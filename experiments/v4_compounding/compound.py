"""Section 6 — does selection error compound across self-improvement generations?

Self-evolving agents do not select once. ACE curates its playbook each round, MEGA
evolves its curation strategies, ERSkill co-evolves router and skills, SkillGen gates
and deprecates. Every generation admits new candidates into a store that already
exists, using per-entry evaluation.

THE CLAIM. Independent gating evaluates each candidate against a FIXED reference
while the deployed store grows around it. The conditions under which an entry is
validated therefore drift monotonically from the conditions under which it is used,
so the gap to oracle selection should WIDEN with generation count. Interaction-aware
selection re-measures against the current store and should not diverge.

THE FALSIFICATION. A flat gap means the error is one-shot and does not accumulate.
That is a real result and a much smaller paper, and it gets reported either way.

DESIGN. Candidates are drawn from a fixed pool in batches, so generation quality is
held constant and only selection varies. LLM-generated candidates would confound the
claim with proposer variance; that is deliberately excluded. Several batch orderings
are run because greedy is order-dependent by construction, and how much that matters
is itself a measurement.

Every store is size-matched. Every evaluation is cached by store contents and shared
with section 4's cache, so overlapping stores cost nothing.
"""

import argparse, json, pathlib, random, sys, time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import store as S                       # noqa: E402
from selection import Evaluator, CANDIDATES, TARGET, oracle   # noqa: E402


def run_generation_loop(ev, order, batch, generations):
    """One ordering. Returns per-generation trajectories for each procedure."""
    indep, grdy = [], []
    offered = []
    rows = []

    for g in range(generations):
        newly = order[g * batch:(g + 1) * batch]
        if not newly:
            break
        offered += newly

        # INDEPENDENT: each candidate scored against the FIXED empty reference,
        # regardless of how large the deployed store has grown. This is the
        # mechanism under test, not a strawman -- it is what O(n) per-entry
        # validation means once a store persists across rounds.
        base_fixed = ev([])["_total"]
        for c in newly:
            if ev([c])["_total"] - base_fixed > 0:
                indep.append(c)

        # GREEDY: each candidate scored against the store as it actually stands.
        for c in newly:
            cur = ev(grdy)["_total"]
            if ev(grdy + [c])["_total"] - cur > 0:
                grdy.append(c)

        # ORACLE over everything offered so far.
        # Oracle chooses only from what has been offered by this generation.
        orc, orc_v, _ = oracle(ev, samples=0, seeds=(grdy, indep, offered),
                               pool=offered)

        a_i, a_g = ev(indep)["_total"], ev(grdy)["_total"]
        rows.append({
            "generation": g + 1, "offered": len(offered),
            "independent_acc": a_i, "greedy_acc": a_g, "oracle_acc": orc_v,
            "independent_gap": a_i - orc_v, "greedy_gap": a_g - orc_v,
            "independent_store": list(indep), "greedy_store": list(grdy),
            "oracle_store": list(orc),
            "independent_wrong_admitted": sum(
                1 for c in indep if S.CLASS_OF[c] == "wrong"),
            "greedy_wrong_admitted": sum(
                1 for c in grdy if S.CLASS_OF[c] == "wrong"),
        })
        print(f"  gen {g+1}: offered {len(offered):2d} | "
              f"indep {a_i:.3f} (gap {a_i-orc_v:+.3f}, {rows[-1]['independent_wrong_admitted']} wrong) | "
              f"greedy {a_g:.3f} (gap {a_g-orc_v:+.3f}) | oracle {orc_v:.3f}", flush=True)
    return rows


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
    ap.add_argument("--gen-batch", type=int, default=3,
                    help="candidates offered per generation")
    ap.add_argument("--generations", type=int, default=6)
    ap.add_argument("--orderings", type=int, default=3,
                    help="distinct batch orderings; greedy is order-dependent")
    args = ap.parse_args()

    ev = Evaluator(args)
    out = {"orderings": [], "_meta": {
        "gen_batch": args.gen_batch, "generations": args.generations,
        "pool": CANDIDATES, "model": args.model, "tasks": args.limit}}

    t0 = time.time()
    for seed in range(args.orderings):
        order = list(CANDIDATES)
        random.Random(1000 + seed).shuffle(order)
        print(f"[ordering {seed}] {order}", flush=True)
        out["orderings"].append({"seed": seed, "order": order,
                                 "rows": run_generation_loop(
                                     ev, order, args.gen_batch, args.generations)})

    out["_meta"]["unique_stores"] = len(ev.cache)
    out["_meta"]["minutes"] = round((time.time() - t0) / 60, 1)
    p = HERE / "results" / f"section6_{args.tag}.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[done] {ev.calls} new evaluations, {(time.time()-t0)/60:.1f} min -> {p}")


if __name__ == "__main__":
    main()
