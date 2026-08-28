"""Q2 analysis: is a learned-context entry's effect size model-conditional?

For each backbone and each entry, the leave-one-out effect is

    effect(entry) = score(store without entry) - score(full store)

measured on the entry's TARGET FIELD (its global effect is also reported).
Positive means removing the entry helped, i.e. the entry was harmful. We negate
so that positive = the entry helped, matching how a memory system would score it.

The question is not whether the models recover the designed ground truth. It is
whether the *measured* effect per entry agrees across backbones. Three summaries:

  sign agreement   fraction of entries where all backbones agree on the sign
  rank correlation Spearman rho between backbones over per-entry effects
  max divergence   largest |effect_i - effect_j| for any entry

If effects are model-stable, read-time gating on a per-backbone attestation buys
nothing and C3 collapses into C4. If signs flip, C3 has a mechanism.
"""

import json, pathlib, sys, itertools, statistics

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import store as S                                    # noqa: E402
from tasks import FIELDS                             # noqa: E402

RESULTS = HERE / "results"


def load(tag):
    rows = [json.loads(l) for l in open(RESULTS / f"raw_{tag}.jsonl", encoding="utf-8")]
    by = {}
    for r in rows:
        by.setdefault(r["condition"], {})[r["task_id"]] = r["fields"]
    return by


def mean_field(cond_rows, field):
    vals = [f[field] for f in cond_rows.values()]
    return sum(vals) / len(vals) if vals else float("nan")


def mean_all(cond_rows):
    vals = [sum(f.values()) / len(FIELDS) for f in cond_rows.values()]
    return sum(vals) / len(vals) if vals else float("nan")


def effects(by):
    """entry -> (targeted effect, global effect). Positive = entry helped."""
    out = {}
    for sk in ("A", "B"):
        full = by.get(f"{sk}:full")
        if not full:
            continue
        for eid in S.ids(sk):
            loo = by.get(f"{sk}:loo:{eid}")
            if not loo:
                continue
            tf = S.TARGET_FIELD.get(eid)
            if tf:
                targeted = mean_field(full, tf) - mean_field(loo, tf)
            else:  # distractor: average over all fields
                targeted = mean_all(full) - mean_all(loo)
            out[eid] = (targeted, mean_all(full) - mean_all(loo))
    return out


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def sign(x, eps=0.02):
    return 0 if abs(x) < eps else (1 if x > 0 else -1)


def main(tags):
    per = {}
    for t in tags:
        try:
            per[t] = effects(load(t))
        except FileNotFoundError:
            print(f"[skip] no results for {t}")
    if len(per) < 2:
        print("need at least two backbones"); return

    entries = [e for e in S.CLASS_OF if all(e in per[t] for t in per)]
    tags = list(per)

    print("=" * 78)
    print("PER-ENTRY TARGETED EFFECT  (positive = entry helped that backbone)")
    print("=" * 78)
    hdr = f"{'entry':12s} {'class':11s}" + "".join(f"{t:>14s}" for t in tags) + "   flip"
    print(hdr); print("-" * len(hdr))
    flips = []
    for e in entries:
        vals = [per[t][e][0] for t in tags]
        signs = {sign(v) for v in vals}
        nz = {s for s in signs if s != 0}
        flip = len(nz) > 1
        if flip:
            flips.append(e)
        print(f"{e:12s} {S.CLASS_OF[e]:11s}"
              + "".join(f"{v:+14.3f}" for v in vals)
              + ("   YES" if flip else ""))

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    agree = sum(1 for e in entries
                if len({sign(per[t][e][0]) for t in tags} - {0}) <= 1)
    print(f"sign agreement           {agree}/{len(entries)} entries "
          f"({100*agree/len(entries):.0f}%)")
    if flips:
        print(f"sign flips               {', '.join(flips)}")

    print()
    for a, b in itertools.combinations(tags, 2):
        xs = [per[a][e][0] for e in entries]
        ys = [per[b][e][0] for e in entries]
        rho = spearman(xs, ys)
        maxdiv = max(abs(x - y) for x, y in zip(xs, ys))
        worst = entries[max(range(len(xs)), key=lambda i: abs(xs[i] - ys[i]))]
        print(f"{a:14s} vs {b:14s}  spearman {rho:+.3f}   "
              f"max divergence {maxdiv:.3f} ({worst})")

    print()
    print("by class, mean targeted effect:")
    for cls in ("correct", "wrong", "distractor"):
        es = [e for e in entries if S.CLASS_OF[e] == cls]
        if not es:
            continue
        line = "".join(f"{statistics.mean(per[t][e][0] for e in es):+14.3f}" for t in tags)
        print(f"  {cls:11s}" + line)


if __name__ == "__main__":
    main(sys.argv[1:] or ["qwen25c-3b", "qwen35-4b", "qwen25c-7b"])
