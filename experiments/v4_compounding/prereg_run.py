"""Pre-registered degradation test — arms B and C.

Design, degradation function, generation count, seed count and decision rule are
fixed in docs/PREREG-degrading-candidates.md, committed before this ran. Nothing
here may be changed after seeing data; if the design is wrong the run is discarded
and re-registered.

  arm B  scheduled decay   p_wrong = clip(0.50 + 0.08*(g-1), 0.50, 0.90)
                           identical stream for every procedure. CONTROL.
  arm C  store feedback    p_wrong = clip(0.50 + 0.08*w, 0.50, 0.90) where w is the
                           wrong-entry count in THAT procedure's own store, so each
                           procedure sees its own stream. THE TEST.

Arm B is what makes C interpretable: if difficulty alone widens the gap, feedback is
not demonstrated.

The oracle is scoped to what a procedure was actually offered, and that is asserted
at runtime rather than checked afterwards -- an unscoped oracle silently produced a
clean, plausible, wrong trend once already.
"""

import argparse, json, pathlib, random, sys, time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import pool_ext as P                                  # noqa: E402
from selection import Evaluator, oracle               # noqa: E402
import selection                                      # noqa: E402


def p_wrong(g, w, arm):
    """Fixed by pre-registration. Do not tune."""
    x = (g - 1) if arm == "B" else w
    return min(0.90, max(0.50, 0.50 + 0.08 * x))


class Stream:
    """Draws candidates without replacement from the extended pool."""

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.correct = list(P.CORRECT_IDS); self.rng.shuffle(self.correct)
        self.wrong = list(P.WRONG_IDS); self.rng.shuffle(self.wrong)

    def draw(self, m, p):
        out = []
        for _ in range(m):
            want_wrong = self.rng.random() < p
            src = self.wrong if (want_wrong and self.wrong) else self.correct
            if not src:
                src = self.wrong or self.correct
            if not src:
                break
            out.append(src.pop())
        return out


def run_arm(ev, arm, seed, gens, m):
    """One arm, one seed. Each procedure carries its own stream in arm C."""
    procs = {"independent": {"store": [], "offered": [], "stream": Stream(seed)},
             "greedy": {"store": [], "offered": [], "stream": Stream(seed)}}
    shared = Stream(seed)
    rows = []

    for g in range(1, gens + 1):
        if arm == "B":
            batch = shared.draw(m, p_wrong(g, 0, "B"))
            batches = {k: batch for k in procs}
        else:
            batches = {}
            for k, st in procs.items():
                w = sum(1 for c in st["store"] if P.CLASS_OF[c] == "wrong")
                batches[k] = st["stream"].draw(m, p_wrong(g, w, "C"))

        row = {"generation": g, "arm": arm, "seed": seed}
        for k, st in procs.items():
            newly = batches[k]
            st["offered"] += newly
            if k == "independent":
                base = ev([])["_total"]
                for c in newly:
                    if ev([c])["_total"] - base > 0:
                        st["store"].append(c)
            else:
                for c in newly:
                    cur = ev(st["store"])["_total"]
                    if ev(st["store"] + [c])["_total"] - cur > 0:
                        st["store"].append(c)

            orc, orc_v, _ = oracle(ev, samples=0,
                                   seeds=(st["store"], st["offered"]),
                                   pool=st["offered"])
            assert set(orc) <= set(st["offered"]), \
                f"oracle leaked unoffered candidates in arm {arm} gen {g} ({k})"
            acc = ev(st["store"])["_total"]
            row[f"{k}_acc"] = acc
            row[f"{k}_oracle"] = orc_v
            row[f"{k}_gap"] = acc - orc_v
            row[f"{k}_offered"] = len(st["offered"])
            row[f"{k}_wrong_admitted"] = sum(
                1 for c in st["store"] if P.CLASS_OF[c] == "wrong")
            row[f"{k}_wrong_offered"] = sum(
                1 for c in st["offered"] if P.CLASS_OF[c] == "wrong")
            row[f"{k}_store"] = list(st["store"])
        rows.append(row)
        print(f"  [{arm} s{seed}] gen {g:2d} | indep gap {row['independent_gap']:+.3f} "
              f"({row['independent_wrong_admitted']}w of {row['independent_wrong_offered']} offered) "
              f"| greedy gap {row['greedy_gap']:+.3f} "
              f"({row['greedy_wrong_admitted']}w)", flush=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--batch", type=int, default=13)
    ap.add_argument("--max-new", type=int, default=160)
    ap.add_argument("--mem-frac", type=float, default=0.90)
    ap.add_argument("--pad-to", type=int, default=36)
    ap.add_argument("--batch-timeout", type=float, default=600.0)
    ap.add_argument("--generations", type=int, default=10)
    ap.add_argument("--gen-batch", type=int, default=3)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--arms", default="B,C")
    args = ap.parse_args()

    # Route the shared Evaluator at the extended pool.
    selection.CANDIDATES = P.POOL
    selection.BACKGROUND = P.BACKGROUND
    selection.S = P

    ev = Evaluator(args)
    out = {"arms": {}, "_meta": {
        "generations": args.generations, "gen_batch": args.gen_batch,
        "seeds": args.seeds, "pool_correct": len(P.CORRECT_IDS),
        "pool_wrong": len(P.WRONG_IDS), "model": args.model,
        "prereg": "docs/PREREG-degrading-candidates.md"}}

    t0 = time.time()
    for arm in args.arms.split(","):
        out["arms"][arm] = []
        for seed in range(args.seeds):
            out["arms"][arm].append(
                {"seed": seed,
                 "rows": run_arm(ev, arm, seed, args.generations, args.gen_batch)})
            p = HERE / "results" / f"prereg_{args.tag}.json"
            out["_meta"]["minutes"] = round((time.time() - t0) / 60, 1)
            p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[done] {ev.calls} new evaluations, {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
