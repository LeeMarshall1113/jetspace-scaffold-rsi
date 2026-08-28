"""Q2 analysis: is a learned-context entry's effect size model-conditional?

Two effect measures per entry, both on its target field:

  LOO       score(full) - score(full minus entry)
  ABSOLUTE  score(full) - score(distractors only)

Positive means the entry helped. In a MIXED store each field carries exactly one
hint, so removing it should be equivalent to having none -- LOO and ABSOLUTE
should agree, and any gap between them is residual cross-entry interference.
That gap is the thing the v2 instrument could not see: with six same-direction
wrong hints, removing one left the others doing its job, so LOO read ~0 while the
entry was in fact strongly harmful. ABSOLUTE is immune to that.

The question is not whether models recover the designed ground truth. It is
whether the measured effect per entry agrees across backbones.

Usage:  python analyze.py [--stores ab|mixed] tag [tag ...]
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


def mean_field(rows, field):
    v = [f[field] for f in rows.values()]
    return sum(v) / len(v) if v else float("nan")


def mean_all(rows):
    v = [sum(f.values()) / len(FIELDS) for f in rows.values()]
    return sum(v) / len(v) if v else float("nan")


def effects(by, store_set):
    """entry -> (loo_effect, absolute_effect) on its target field."""
    out = {}
    for sk in S.STORE_SETS[store_set]:
        full, none = by.get(f"{sk}:full"), by.get(f"{sk}:none")
        if not full:
            continue
        for eid in S.ids(sk):
            loo = by.get(f"{sk}:loo:{eid}")
            if not loo:
                continue
            tf = S.TARGET_FIELD.get(eid)
            if tf:
                l = mean_field(full, tf) - mean_field(loo, tf)
                a = (mean_field(full, tf) - mean_field(none, tf)) if none else float("nan")
            else:
                l = mean_all(full) - mean_all(loo)
                a = (mean_all(full) - mean_all(none)) if none else float("nan")
            out[eid] = (l, a)
    return out


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v); i = 0
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
    return 0 if abs(x) < eps or x != x else (1 if x > 0 else -1)


def main(argv):
    store_set = "ab"
    if argv and argv[0] == "--stores":
        store_set = argv[1]; argv = argv[2:]
    tags = argv or ["qwen25c-3b", "qwen25c-7b", "qwen35-4b", "gemma4-e2b"]

    per = {}
    for t in tags:
        try:
            e = effects(load(t), store_set)
            if e:
                per[t] = e
            else:
                print(f"[skip] {t}: no {store_set} conditions present")
        except FileNotFoundError:
            print(f"[skip] {t}: no results file")
    if len(per) < 2:
        print("need at least two backbones"); return
    tags = list(per)
    entries = [e for e in S.CLASS_OF if all(e in per[t] for t in tags)]

    use_abs = all(per[t][e][1] == per[t][e][1] for t in tags for e in entries)
    idx = 1 if use_abs else 0
    label = "ABSOLUTE (vs hint-free)" if use_abs else "LOO"

    print("=" * 86)
    print(f"PER-ENTRY EFFECT ON TARGET FIELD -- {label}   (positive = entry helped)")
    print("=" * 86)
    hdr = f"{'entry':11s} {'class':11s}" + "".join(f"{t:>14s}" for t in tags) + "   flip"
    print(hdr); print("-" * len(hdr))
    flips = []
    for e in entries:
        vals = [per[t][e][idx] for t in tags]
        nz = {sign(v) for v in vals} - {0}
        flip = len(nz) > 1
        if flip:
            flips.append(e)
        print(f"{e:11s} {S.CLASS_OF[e]:11s}" + "".join(f"{v:+14.3f}" for v in vals)
              + ("   YES" if flip else ""))

    if use_abs:
        print()
        print("interference check -- |ABSOLUTE - LOO| per entry (large = neighbours "
              "masked this entry)")
        worst = []
        for e in entries:
            g = max(abs(per[t][e][1] - per[t][e][0]) for t in tags)
            worst.append((g, e))
        worst.sort(reverse=True)
        for g, e in worst[:5]:
            print(f"    {e:11s} {S.CLASS_OF[e]:11s} max gap {g:.3f}")

    print()
    print("=" * 86)
    print("SUMMARY")
    print("=" * 86)
    agree = sum(1 for e in entries if len({sign(per[t][e][idx]) for t in tags} - {0}) <= 1)
    print(f"sign agreement           {agree}/{len(entries)} entries "
          f"({100*agree/len(entries):.0f}%)")
    print(f"sign flips               {', '.join(flips) if flips else 'none'}")

    neg = [e for e in entries
           if any(sign(per[t][e][idx]) < 0 for t in tags)]
    print(f"entries harmful somewhere {len(neg)}/{len(entries)}"
          + (f"  ({', '.join(neg)})" if neg else ""))

    print()
    for a, b in itertools.combinations(tags, 2):
        xs = [per[a][e][idx] for e in entries]
        ys = [per[b][e][idx] for e in entries]
        md = max(abs(x - y) for x, y in zip(xs, ys))
        w = entries[max(range(len(xs)), key=lambda i: abs(xs[i] - ys[i]))]
        print(f"{a:14s} vs {b:14s}  spearman {spearman(xs, ys):+.3f}   "
              f"max divergence {md:.3f} ({w})")

    print()
    print("by class, mean effect:")
    for cls in ("correct", "wrong", "distractor"):
        es = [e for e in entries if S.CLASS_OF[e] == cls]
        if es:
            print(f"  {cls:11s}" + "".join(
                f"{statistics.mean(per[t][e][idx] for e in es):+14.3f}" for t in tags))


if __name__ == "__main__":
    main(sys.argv[1:])
