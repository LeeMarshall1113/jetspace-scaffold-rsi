"""Leave-one-out ablation of a context store, across backbones.

For each backbone and each of the 18 store entries, run the task set with the
full store and with that entry removed. Effect of entry i is
score(full) - score(full minus i): positive means the entry helped.

Greedy decoding throughout, so every LOO difference is exact rather than a
sample estimate. That buys far more resolution per GPU-hour than sampling would.

ROCm safety, per the hard lessons in this box's history: bf16 only, eager
attention, math-only SDPA, ROCBLAS_USE_HIPBLASLT=0, capped memory fraction, and
incremental JSONL writes so a crash costs one batch rather than a run.

Usage:
    python run_loo.py --model <path> --tag <name> [--limit N] [--batch 8]
"""

import argparse, json, os, pathlib, sys, time

os.environ.setdefault("ROCBLAS_USE_HIPBLASLT", "0")
os.environ.setdefault("PYTORCH_HIP_ALLOC_CONF", "expandable_segments:True")

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import store as S                                    # noqa: E402
from tasks import make_tasks, render_record, parse_output, score, FIELDS  # noqa: E402

# Derived from FIELDS, never hardcoded. A hardcoded key list silently survived a
# field rename once: the model emitted the old keys it had been told to, three
# fields parsed as <none> in every condition, and the result read as "these fields
# floor" rather than "the prompt is stale".
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

Output the six key=value lines now."""


def build_prompt(tok, store_key, entry_ids, record):
    """Render the chat prompt.

    Reasoning-tuned backbones (Qwen3.5) emit a thinking preamble and will burn
    the whole generation budget before reaching the answer -- that voided an
    entire 1300-generation run. Suppress thinking where the template supports
    it, and fall back cleanly where it does not.
    """
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": PROMPT.format(
            notes=S.render(store_key, entry_ids), record=render_record(record))},
    ]
    try:
        return tok.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def conditions(store_set="ab"):
    """Per store: full, one leave-one-out per entry, and a hint-free baseline.

    The 'none' condition (distractors only) is what makes an *absolute* per-entry
    effect measurable rather than only an effect relative to the rest of the
    store. Without it a wrong entry whose neighbours already produce the same
    behaviour reads as harmless, which is exactly how the v2 instrument missed
    the negative direction.
    """
    for store_key in S.STORE_SETS[store_set]:
        ids = S.ids(store_key)
        yield store_key, f"{store_key}:full", ids
        for k in ids:
            yield store_key, f"{store_key}:loo:{k}", [i for i in ids if i != k]
        yield store_key, f"{store_key}:none", [k for k in ids if S.CLASS_OF[k] == "distractor"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--max-new", type=int, default=128)
    ap.add_argument("--mem-frac", type=float, default=0.90)
    ap.add_argument("--stores", default="mixed", choices=["mixed"],
                    help="mixed = v3 one hint per field (v2 a/b retired, see store.py)")
    args = ap.parse_args()

    outdir = HERE / "results"
    outdir.mkdir(exist_ok=True)
    outpath = outdir / f"raw_{args.tag}.jsonl"

    done = set()
    if outpath.exists():
        with open(outpath, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    done.add((r["condition"], r["task_id"]))
                except Exception:
                    pass
        print(f"[resume] {len(done)} rows already present in {outpath.name}")

    tasks = make_tasks(args.limit)

    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(args.mem_frac, 0)
    torch.backends.cuda.enable_flash_sdp(False)
    torch.backends.cuda.enable_mem_efficient_sdp(False)
    torch.backends.cuda.enable_math_sdp(True)

    print(f"[load] {args.model}")
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16, attn_implementation="eager",
        device_map="cuda:0")
    model.eval()
    model.generation_config.do_sample = False
    model.generation_config.temperature = None
    model.generation_config.top_p = None
    model.generation_config.top_k = None

    work = [(sk, cond, ids, t) for sk, cond, ids in conditions(args.stores) for t in tasks
            if (cond, t["id"]) not in done]
    print(f"[plan] {len(work)} generations remaining "
          f"({len(list(conditions(args.stores)))} conditions x {len(tasks)} tasks)")

    # Cooperative preemption: the broker's lease wrapper touches this file when
    # it wants the lease back. A batch boundary is a clean checkpoint -- every
    # completed generation is already flushed to JSONL, so stopping here costs
    # nothing and the next run resumes from the same place.
    preempt_file = os.environ.get("BROKER_PREEMPT_FILE")

    t0 = time.time()
    written = 0
    with open(outpath, "a", encoding="utf-8") as fout:
        for b0 in range(0, len(work), args.batch):
            if preempt_file and os.path.exists(preempt_file):
                print(f"[preempt] yielding at {written}/{len(work)}; "
                      f"rerun to resume", flush=True)
                break
            chunk = work[b0:b0 + args.batch]
            prompts = [build_prompt(tok, sk, ids, t["record"])
                       for sk, _, ids, t in chunk]
            enc = tok(prompts, return_tensors="pt", padding=True).to(model.device)
            with torch.inference_mode():
                out = model.generate(
                    **enc, max_new_tokens=args.max_new, do_sample=False,
                    pad_token_id=tok.pad_token_id, use_cache=True)
            gen = out[:, enc["input_ids"].shape[1]:]
            texts = tok.batch_decode(gen, skip_special_tokens=True)

            for (_, cond, _, t), text in zip(chunk, texts):
                parsed = parse_output(text)
                fout.write(json.dumps({
                    "condition": cond, "task_id": t["id"],
                    "ambiguous_date": t["ambiguous_date"],
                    "fields": score(parsed, t["expected"]),
                    "raw": text[:600],
                }) + "\n")
                written += 1
            fout.flush()

            elapsed = time.time() - t0
            rate = written / elapsed if elapsed else 0
            eta = (len(work) - written) / rate if rate else 0
            print(f"  {written}/{len(work)}  {rate:.2f} gen/s  eta {eta/60:.1f} min",
                  flush=True)

    print(f"[done] {written} generations in {(time.time()-t0)/60:.1f} min -> {outpath}")


if __name__ == "__main__":
    main()
