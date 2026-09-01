"""Section 4 — what does independent per-entry gating cost against oracle selection?

Four selection procedures over the same candidate pool, all measured against the
same held-fixed background and all size-matched, then compared to an oracle subset.

  independent   score each candidate against a FIXED reference, keep if its own
                target field improves. O(n). What SkillGen/SkillOpt do.
  global        identical evaluations, but keep on TOTAL accuracy across all fields
                rather than the target field. Same O(n) cost -- if this recovers most
                of the gap it is the cheap practical recommendation.
  greedy        add the best marginal contributor GIVEN the current store, re-measuring
                each round. O(n*k). Order-dependent by construction.
  oracle        best subset found by random sampling plus hill-climbing. The ceiling.

Selection is sequential for greedy and oracle, so this holds the model resident and
evaluates on demand rather than precomputing a condition list. Every evaluation is
cached to disk by frozenset, because greedy and oracle overlap heavily and a rerun
should cost nothing it has already paid for.

NAMING: this file is `selection.py`, not `select.py`. `select` is a stdlib module,
and a file shadowing it here broke the socket/email/http import chain for every
process whose sys.path included this directory -- which silently killed two queued
GPU jobs before the cause was found. Do not name modules in an experiment directory
after stdlib modules.

Every store is BACKGROUND + selected candidates, padded to a fixed entry count. The
padding is not optional: comparing stores of different length would confound content
with context length (PR #1).
"""

import argparse, json, os, pathlib, random, sys, threading, time

os.environ.setdefault("ROCBLAS_USE_HIPBLASLT", "0")
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "3")

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import store as S                                                    # noqa: E402
from tasks import make_tasks, render_record, parse_output, score, FIELDS  # noqa: E402

SYSTEM = ("You normalise messy data records. Apply the notes you are given, then output "
          f"exactly {len(FIELDS)} lines in the form key=value, with keys "
          f"{', '.join(FIELDS)}, in that order. "
          "Output nothing else -- no explanation, no code fences.")
PROMPT = ("Notes from previous records:\n{notes}\n\n"
          "Normalise this record:\n{record}\n\nOutput the {n} key=value lines now.")

CANDIDATES = [k for k, _ in S.CORRECT] + [k for k, _, _, _ in S.WRONG]
BACKGROUND = [k for k, _ in S.DISTRACTOR[:6]]
TARGET = dict(S.TARGET_FIELD)


class Evaluator:
    """Holds the model resident; caches per-store accuracy by frozenset."""

    def __init__(self, args):
        self.a = args
        self.tasks = make_tasks(args.limit)
        self.cache_path = HERE / "results" / f"cache_{args.tag}.jsonl"
        self.cache_path.parent.mkdir(exist_ok=True)
        self.cache = {}
        if self.cache_path.exists():
            for line in open(self.cache_path, encoding="utf-8"):
                try:
                    r = json.loads(line); self.cache[r["key"]] = r["acc"]
                except Exception:
                    pass
            print(f"[cache] {len(self.cache)} stores already measured")
        self.calls = 0

        if torch.cuda.is_available():
            torch.cuda.set_per_process_memory_fraction(args.mem_frac, 0)
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)
        torch.set_num_threads(3)

        print(f"[load] {args.model}")
        self.tok = AutoTokenizer.from_pretrained(args.model)
        self.tok.padding_side = "left"
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            args.model, dtype=torch.bfloat16, attn_implementation="eager",
            device_map="cuda:0")
        self.model.eval()
        self.model.generation_config.do_sample = False
        for k in ("temperature", "top_p", "top_k"):
            setattr(self.model.generation_config, k, None)

        # Same watchdog rationale as run.py: the preempt flag is read between
        # evaluations, so a wedge inside one would otherwise be invisible.
        self.deadline = [float("inf")]
        threading.Thread(target=self._watchdog, daemon=True).start()

    def _watchdog(self):
        while True:
            time.sleep(5)
            if time.time() > self.deadline[0]:
                print("[watchdog] evaluation overran -- hard exit; cache is on disk",
                      flush=True)
                os._exit(75)

    def _key(self, ids):
        return ",".join(sorted(ids))

    def __call__(self, ids):
        """Per-field accuracy for BACKGROUND + ids, size-matched. Cached."""
        key = self._key(ids)
        if key in self.cache:
            return self.cache[key]
        entries = BACKGROUND + [k for k in CANDIDATES if k in set(ids)]
        totals = {f: 0 for f in FIELDS}
        b = self.a.batch
        for i in range(0, len(self.tasks), b):
            self.deadline[0] = time.time() + self.a.batch_timeout
            chunk = self.tasks[i:i + b]
            prompts = []
            for t in chunk:
                msgs = [{"role": "system", "content": SYSTEM},
                        {"role": "user", "content": PROMPT.format(
                            notes=S.build(entries, pad_to=self.a.pad_to),
                            record=render_record(t["record"]), n=len(FIELDS))}]
                try:
                    prompts.append(self.tok.apply_chat_template(
                        msgs, tokenize=False, add_generation_prompt=True,
                        enable_thinking=False))
                except TypeError:
                    prompts.append(self.tok.apply_chat_template(
                        msgs, tokenize=False, add_generation_prompt=True))
            enc = self.tok(prompts, return_tensors="pt", padding=True).to(self.model.device)
            with torch.inference_mode():
                out = self.model.generate(**enc, max_new_tokens=self.a.max_new,
                                          do_sample=False,
                                          pad_token_id=self.tok.pad_token_id, use_cache=True)
            texts = self.tok.batch_decode(out[:, enc["input_ids"].shape[1]:],
                                          skip_special_tokens=True)
            for t, text in zip(chunk, texts):
                for f, v in score(parse_output(text), t["expected"]).items():
                    totals[f] += v
            self.deadline[0] = float("inf")
        n = len(self.tasks)
        acc = {f: totals[f] / n for f in FIELDS}
        acc["_total"] = sum(acc[f] for f in FIELDS) / len(FIELDS)
        self.cache[key] = acc
        self.calls += 1
        with open(self.cache_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"key": key, "acc": acc}) + "\n")
        return acc


def independent(ev, use_global=False):
    """Score each candidate against the FIXED empty-selection reference."""
    base = ev([])
    kept, deltas = [], {}
    for c in CANDIDATES:
        a = ev([c])
        d = (a["_total"] - base["_total"]) if use_global \
            else (a[TARGET[c]] - base[TARGET[c]])
        deltas[c] = d
        if d > 0:
            kept.append(c)
    return kept, deltas, len(CANDIDATES) + 1


def greedy(ev, rounds):
    """Add the best marginal contributor given the store so far."""
    cur, calls = [], 0
    for _ in range(rounds):
        cur_acc = ev(cur)["_total"]; calls += 1
        best, best_gain = None, 0.0
        for c in CANDIDATES:
            if c in cur:
                continue
            g = ev(cur + [c])["_total"] - cur_acc; calls += 1
            if g > best_gain:
                best, best_gain = c, g
        if best is None:
            break
        cur.append(best)
    return cur, calls


def oracle(ev, samples, seed=0, seeds=()):
    """Best subset found by MULTI-START hill-climbing. The ceiling.

    Single-start from the best random sample was not a ceiling at all: with 12 of 18
    candidates harmful, random subsets are almost always poor, and single-element
    flips from a poor start stall in a local optimum. The first run of this returned
    0.906 against greedy's 0.967 -- an "oracle" losing to a procedure it is supposed
    to bound, which is a bug rather than a finding.

    Now it climbs from several starts: every caller-supplied seed (greedy's store,
    the all-correct store), the empty store, and the best random sample. A ceiling
    that a competing procedure beats means the search is wrong, not that the
    procedure is superhuman.
    """
    rng = random.Random(seed)
    calls = 0
    starts = [list(s) for s in seeds] + [[]]

    best_rand, best_rand_v = [], -1.0
    for _ in range(samples):
        k = rng.randint(1, len(CANDIDATES))
        s = rng.sample(CANDIDATES, k)
        v = ev(s)["_total"]; calls += 1
        if v > best_rand_v:
            best_rand, best_rand_v = s, v
    starts.append(best_rand)

    best, best_v = [], -1.0
    for start in starts:
        cur = list(start)
        cur_v = ev(cur)["_total"]; calls += 1
        improved = True
        while improved:
            improved = False
            for c in CANDIDATES:
                cand = [x for x in cur if x != c] if c in cur else cur + [c]
                v = ev(cand)["_total"]; calls += 1
                if v > cur_v + 1e-9:
                    cur, cur_v, improved = cand, v, True
        if cur_v > best_v:
            best, best_v = cur, cur_v
    return best, best_v, calls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--batch", type=int, default=13)
    ap.add_argument("--max-new", type=int, default=160)
    ap.add_argument("--mem-frac", type=float, default=0.90)
    ap.add_argument("--pad-to", type=int, default=26)
    ap.add_argument("--batch-timeout", type=float, default=600.0)
    ap.add_argument("--greedy-rounds", type=int, default=6)
    ap.add_argument("--oracle-samples", type=int, default=120)
    args = ap.parse_args()

    ev = Evaluator(args)
    t0 = time.time()
    out = {}

    for name, fn in [("independent", lambda: independent(ev, False)),
                     ("global", lambda: independent(ev, True))]:
        kept, deltas, calls = fn()
        acc = ev(kept)
        out[name] = {"store": kept, "acc": acc["_total"], "per_field": acc,
                     "evaluations": calls, "deltas": deltas}
        print(f"[{name}] kept {len(kept)}/{len(CANDIDATES)} -> {acc['_total']:.3f} "
              f"({calls} evaluations)", flush=True)

    g, calls = greedy(ev, args.greedy_rounds)
    acc = ev(g)
    out["greedy"] = {"store": g, "acc": acc["_total"], "per_field": acc,
                     "evaluations": calls}
    print(f"[greedy] kept {len(g)} -> {acc['_total']:.3f} ({calls} evaluations)", flush=True)

    # Reference point the procedures never happen to evaluate: the ground-truth
    # store of every correct entry and nothing else.
    all_correct = [k for k, _ in S.CORRECT]
    out["all_correct_reference"] = {"store": all_correct,
                                    "acc": ev(all_correct)["_total"]}
    print(f"[reference] all 6 correct -> {out['all_correct_reference']['acc']:.3f}",
          flush=True)

    o, ov, calls = oracle(ev, args.oracle_samples, seeds=(g, all_correct))
    out["oracle"] = {"store": o, "acc": ov, "evaluations": calls}
    print(f"[oracle] kept {len(o)} -> {ov:.3f} ({calls} evaluations)", flush=True)

    out["_meta"] = {"candidates": CANDIDATES, "background": BACKGROUND,
                    "tasks": args.limit, "pad_to": args.pad_to,
                    "model": args.model, "unique_stores_measured": len(ev.cache),
                    "minutes": round((time.time() - t0) / 60, 1)}
    p = HERE / "results" / f"section4_{args.tag}.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[done] {ev.calls} new evaluations, {(time.time()-t0)/60:.1f} min -> {p}")


if __name__ == "__main__":
    main()
