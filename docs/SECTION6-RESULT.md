# Section 6 — does selection error compound across generations?

Qwen2.5-Coder-3B, 60 tasks, 18-candidate pool, 3 candidates offered per generation,
6 generations, 3 batch orderings. 1,894 unique stores measured. Every store
size-matched; oracle restricted to the offered set at each generation (verified as
a subset invariant).

## The pre-registered claim is FALSIFIED

The prediction was that independent gating's gap to oracle would **widen
monotonically** with generation count, because entries are validated against a fixed
reference while the deployed store grows around them. It does not.

Mean gap to oracle across three orderings:

| generation | independent | greedy |
|---|---|---|
| 1 | −0.015 | −0.013 |
| 2 | −0.105 | −0.016 |
| 3 | **−0.164** | −0.024 |
| 4 | −0.144 | −0.025 |
| 5 | −0.103 | **−0.062** |
| 6 | −0.071 | −0.057 |

Independent's gap **peaks at generation 3 and then partially recovers**. It is an
inverted U, not a divergence. As more candidates arrive, some of the damage is
offset by correct entries the procedure also admits.

**So error does not compound in the sense claimed.** That is the honest headline and
it makes this a smaller result than intended.

## What does survive, and it is not nothing

**1. Independent is persistently worse, by roughly 3x.** Averaged over generations
2–6: independent −0.117, greedy −0.037. The single-shot §4 result (−0.069) turns out
to be near the *low* end of independent's damage; mid-trajectory it reaches −0.164.
A protocol evaluated only at convergence understates its own cost.

**2. The recommended fix is unstable.** Greedy's generation-6 gap ranges from
**−0.003 to −0.128 across three orderings** — a 40x spread from nothing but the order
candidates arrive in. It also produces three different stores (7, 9 and 7 entries,
differing in content). "Re-measure against the current store" is better on average
and unreliable in any single run, which is a real caveat on the only fix that worked
in §4.

**3. Wrong-entry count is not a quality metric.** Greedy admits *more* wrong entries
than independent at every generation (final: 4/7/4 vs 3/3/3) while scoring better.
It also admits more correct ones, and the wrong entries it takes are less harmful in
the store it has built. Counting bad entries does not measure store quality — which
is the same lesson as §4's finding that an all-correct store is not optimal, arriving
from the opposite direction.

## Honest assessment

The compounding framing was the reason to call this RSI work rather than
context-engineering. That framing is not supported. What is supported is narrower:
per-entry validation is persistently and substantially worse than store-conditioned
validation across repeated selection, and the store-conditioned fix is order-unstable.

Two options follow, and this is a judgement call rather than a measurement:

- **Report it as falsified** and publish the persistent-gap result, dropping the RSI
  framing back to a claim about repeated selection.
- **Test whether compounding appears under conditions this design excluded** — more
  generations, a larger pool, or candidate quality that degrades over rounds (which
  is what a real self-evolving loop does, since it generates from its own outputs).
  The fixed pool was chosen deliberately to isolate selection from proposer variance,
  and that choice may have excluded the mechanism.

The second is not a rescue attempt if it is pre-registered before running. It is
also how the claim could have been wrong in a recoverable way rather than simply
wrong.

## Limitations

- One backbone, one pool, six generations, three orderings.
- The fixed candidate pool excludes proposer degradation, which is a plausible
  compounding mechanism this design cannot see.
- The oracle is best-found, not proven optimal.
- Synthetic tasks throughout.
