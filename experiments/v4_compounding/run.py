"""v4 runner: evaluate named store configurations against the task set.

Takes an explicit list of (name, entry_ids) conditions rather than deriving them,
because §4 (single-shot selection) and §6 (the compounding loop) need different
condition sets from the same machinery.

EVERY CONDITION IS SIZE-MATCHED. `--pad-to` fixes the entry count across all
stores in a run, with filler drawn from a pool kept separate from the entries
under test. This is not optional: without it a comparison between stores of
different length confounds content with context length, which is the confound
PR #1 identified in the v3 headline.

ROCm safety per this box's history: bf16, eager attention, math-only SDPA,
ROCBLAS_USE_HIPBLASLT=0, capped memory fraction, incremental JSONL writes.
Greedy decoding, so every difference between conditions is exact.
"""

import argparse, json, os, pathlib, sys, threading, time

os.environ.setdefault("ROCBLAS_USE_HIPBLASLT", "0")
# 8 physical / 16 logical cores are shared with other agents on this box; one
# session starving the machine with 13 of 16 threads is a documented incident.
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "3")

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import store as S                                                    # noqa: E402
from tasks import make_tasks, render_record, parse_output, score, FIELDS  # noqa: E402

SYSTEM = (
    "You normalise messy data records. Apply the notes you are given, then output "
    f"exactly {len(FIELDS)} lines in the form key=value, with keys "
    f"{', '.join(FIELDS)}, in that order. "
    "Output nothing else -- no explanation, no code fences."
)
PROMPT = """Notes from previous records:
{notes}

Normalise this record:
{record}

Output the {n} key=value lines now."""

CORRECT_IDS = [k for k, _ in S.CORRECT]


def smoke_conditions():
    """Does a plausible-wrong entry added to a correct store actually cost accuracy?

    That premise is what v3 failed on, so it is tested before anything is built on
    top of it. Base is the six correct entries; each variant adds one wrong entry.
    All padded to the same length.
    """
    yield "base", list(CORRECT_IDS)
    for k, _, _, _ in S.WRONG:
        yield f"base+{k}", CORRECT_IDS + [k]


def build_prompt(tok, entry_ids, record, pad_to):
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": PROMPT.format(
            notes=S.build(entry_ids, pad_to=pad_to),
            record=render_record(record), n=len(FIELDS))},
    ]
    try:
        return tok.apply_chat_template(msgs, tokenize=False,
                                       add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--batch", type=int, default=13)
    ap.add_argument("--max-new", type=int, default=160)
    ap.add_argument("--mem-frac", type=float, default=0.90)
    ap.add_argument("--pad-to", type=int, default=18,
                    help="entry count every store is padded to; keeps length constant")
    ap.add_argument("--conditions", default="smoke", choices=["smoke"])
    ap.add_argument("--batch-timeout", type=float, default=600.0,
                    help="hard-exit if one batch exceeds this many seconds")
    args = ap.parse_args()

    outdir = HERE / "results"; outdir.mkdir(exist_ok=True)
    outpath = outdir / f"raw_{args.tag}.jsonl"

    done = set()
    if outpath.exists():
        for line in open(outpath, encoding="utf-8"):
            try:
                r = json.loads(line); done.add((r["condition"], r["task_id"]))
            except Exception:
                pass
        print(f"[resume] {len(done)} rows present")

    tasks = make_tasks(args.limit)
    conds = list(smoke_conditions())

    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(args.mem_frac, 0)
    torch.backends.cuda.enable_flash_sdp(False)
    torch.backends.cuda.enable_mem_efficient_sdp(False)
    torch.backends.cuda.enable_math_sdp(True)

    torch.set_num_threads(3)

    print(f"[load] {args.model}")
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16, attn_implementation="eager", device_map="cuda:0")
    model.eval()
    model.generation_config.do_sample = False
    for k in ("temperature", "top_p", "top_k"):
        setattr(model.generation_config, k, None)

    work = [(c, ids, t) for c, ids in conds for t in tasks if (c, t["id"]) not in done]
    print(f"[plan] {len(work)} generations ({len(conds)} conditions x {len(tasks)} tasks, "
          f"all padded to {args.pad_to} entries)")

    preempt = os.environ.get("BROKER_PREEMPT_FILE")

    # WATCHDOG. The preempt flag is only read at batch boundaries, so a job that
    # wedges INSIDE a batch never sees it -- a cooperative design that stops being
    # cooperative exactly when it matters. That happened: a run whose lease expired
    # spent 21.7 CPU-hours inside one generate() call after losing its GPU context
    # and falling back to host compute, holding 18 GB and producing nothing.
    #
    # Every completed generation is already flushed, so a hard exit costs at most
    # one batch and the run resumes in place. os._exit is deliberate: a wedged
    # ROCm call will not unwind, so raising in a thread would not free anything.
    deadline = [float("inf")]

    def _watchdog():
        while True:
            time.sleep(5)
            if time.time() > deadline[0]:
                print(f"[watchdog] batch exceeded {args.batch_timeout:.0f}s -- "
                      f"hard exit; rerun to resume", flush=True)
                os._exit(75)

    threading.Thread(target=_watchdog, daemon=True).start()

    t0, written = time.time(), 0
    with open(outpath, "a", encoding="utf-8") as fout:
        for b0 in range(0, len(work), args.batch):
            if preempt and os.path.exists(preempt):
                print(f"[preempt] yielding at {written}/{len(work)}", flush=True); break
            deadline[0] = time.time() + args.batch_timeout
            chunk = work[b0:b0 + args.batch]
            prompts = [build_prompt(tok, ids, t["record"], args.pad_to)
                       for _, ids, t in chunk]
            enc = tok(prompts, return_tensors="pt", padding=True).to(model.device)
            with torch.inference_mode():
                out = model.generate(**enc, max_new_tokens=args.max_new, do_sample=False,
                                     pad_token_id=tok.pad_token_id, use_cache=True)
            texts = tok.batch_decode(out[:, enc["input_ids"].shape[1]:],
                                     skip_special_tokens=True)
            for (c, _, t), text in zip(chunk, texts):
                fout.write(json.dumps({
                    "condition": c, "task_id": t["id"], "subsets": t["subsets"],
                    "fields": score(parse_output(text), t["expected"]),
                    "raw": text[:600]}) + "\n")
                written += 1
            fout.flush()
            deadline[0] = float("inf")          # clear between batches
            el = time.time() - t0
            print(f"  {written}/{len(work)}  {written/el:.2f} gen/s  "
                  f"eta {(len(work)-written)/(written/el)/60:.1f} min", flush=True)

    print(f"[done] {written} in {(time.time()-t0)/60:.1f} min -> {outpath}")


if __name__ == "__main__":
    main()
