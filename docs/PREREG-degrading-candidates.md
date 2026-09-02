# Pre-registration — does compounding appear when candidate quality degrades?

**Written 2026-09-02, before any data is collected.** Committed prior to the run.
Section 6 falsified the compounding claim under a fixed candidate pool
([SECTION6-RESULT.md](SECTION6-RESULT.md)). This registers one specific reason that
result may not generalise, and the exact conditions under which it would be
overturned or confirmed dead.

## Why this is not a rescue attempt

§6 deliberately held candidate quality constant so that only selection varied. That
choice excluded a mechanism a real self-evolving loop has: **the proposer generates
from its own context**, so once bad entries are in the store, subsequent candidates
are drawn from a worse distribution. Selection error would then feed back into
candidate quality rather than only accumulating in the store.

If that mechanism is what produces compounding, §6 could not have seen it. This test
is written before running, with a decision rule that can fail.

## Hypothesis

**H1 (primary).** Under store-dependent candidate degradation, independent gating's
gap to oracle widens monotonically across generations, rather than the inverted U
observed in §6.

**H0.** The gap follows the same inverted-U shape as §6 (peaks mid-run, partially
recovers). Compounding is absent even under feedback, and the claim is dead.

## Design — three arms

| arm | candidate quality | purpose |
|---|---|---|
| **A** — fixed pool | constant, procedure-independent | §6, already run. Baseline. |
| **B** — scheduled decay | wrong-fraction rises on a fixed schedule, identical for all procedures | **Control.** Isolates "harder candidates" from feedback. |
| **C** — store feedback | wrong-fraction is a function of the wrong entries in *that procedure's own store* | **The test.** Each procedure sees its own candidate stream. |

Arm B is what makes arm C interpretable. If B also widens, the effect is difficulty,
not feedback, and H1 is not supported even if C widens.

### Degradation function (fixed now)

At generation *g*, for a procedure whose store currently holds *w* wrong entries,
each of the *m* candidates offered is drawn wrong with probability

    p_wrong = clip(0.50 + 0.08 * w, 0.50, 0.90)

Arm B uses the same curve driven by generation index instead of store state:
`p_wrong = clip(0.50 + 0.08 * (g - 1), 0.50, 0.90)`, so B and C span the same range.
Baseline 0.50 is chosen to match the current pool composition at the first
generation, where every arm has an empty store and must therefore agree.

Draws are without replacement from the correct and wrong sets. Requires a pool of
at least **12 correct and 30 wrong** entries for 10 generations at m = 3; the current
pool (6 / 12) must be expanded before running, by adding competing-transform variants
in the established style.

### Parameters, fixed now

- 10 generations, 3 candidates per generation
- 5 orderings/seeds per arm (§6 used 3; greedy's 40x order spread makes 3 too few)
- Qwen2.5-Coder-3B, 60 tasks, greedy decoding, all stores size-matched
- Oracle restricted to the offered set at each generation, verified as a subset
  invariant before any number is read

## Primary outcome and decision rule

For each arm, let `gap_g` be independent gating's mean gap to oracle at generation
*g*, averaged over the 5 orderings. Define:

- **peak** = the most negative `gap_g` for g in 3..7
- **final** = `gap_10`

**H1 is supported only if all three hold:**

1. **Arm C is monotone-widening:** `final < peak` — the gap at generation 10 is worse
   than the mid-run peak. (§6 showed the opposite: −0.071 final vs −0.164 peak.)
2. **Arm C widens more than Arm A:** C's `final` is at least 0.05 more negative than
   A's `final`.
3. **Feedback, not difficulty:** C's `final` is at least 0.05 more negative than B's
   `final`.

**If (1) fails, H1 is rejected** and compounding is reported dead in both conditions.
If (1) and (2) hold but (3) fails, the honest report is that degrading candidate
quality widens the gap regardless of feedback — a weaker claim, and it must be
labelled as such rather than presented as compounding.

## Secondary outcomes, declared now

Reported whatever the primary shows, and **not** substitutable for it:

- Greedy's gap trajectory and its order-spread in each arm.
- Wrong entries admitted per generation, per procedure.
- Whether greedy's order-instability (§6: 40x spread at generation 6) grows, shrinks
  or holds under degradation.

## What will NOT count as support

Fixed now, because two prior results in this project looked publishable and were bugs:

- Any single ordering showing widening while the mean does not.
- Widening in a metric other than the one defined above.
- Widening that appears only after excluding a seed, generation, or arm.
- A change to the degradation function, generation count, or `m` after seeing data.
  If the design turns out to be wrong, the run is discarded and re-registered — not
  reinterpreted.

The analysis script is committed alongside this document, before the run, and its
output is what gets reported.

## Compute

10 generations x 3 candidates x 5 orderings x 2 new arms, sharing the existing
1,894-store cache. Estimated 2,500–4,000 new store evaluations at ~13s each: roughly
9–14 GPU-hours, run under broker leases in preemptible chunks. If that proves
unaffordable, the reduction is fewer *orderings*, declared before running, never
fewer generations — generation count is the independent variable.
