# Paper plan — validation-gated skill selection is unsound at scale

**Scope: one short paper, not a research programme.** Written 2026-08-28 after a
three-agent occupancy sweep killed the broader theses. What survived is narrow, real, and
has a closing window. [REVISIONS.md](REVISIONS.md) records what died and why.

---

## The claim

Published systems that build inference-time context for a target model validate **each entry
independently**: generate a candidate, run it against the frozen consumer, keep it if it
helps. SkillGen gates one skill at a time; SkillOpt optimises a single document; the
strong-to-weak harness work ships one bundled object scored end to end.

**That protocol is unsound, for two measurable reasons that compound.**

- **A — Effects are non-additive.** An entry's measured value depends on which other entries
  are present, sometimes to the point of sign reversal. Independent validation therefore
  keeps entries that hurt in situ and discards entries that only help in company.
- **B — Value is not predictable from model metadata.** It tracks neither scale, generation,
  nor lineage, so there is no shortcut that avoids measuring against the specific consumer.

**C — The consequence.** Because you cannot infer entry value (B) *and* cannot measure it
independently (A), the verification cost of a correctly-selected multi-entry store is far
worse than the O(n) that published protocols assume. That is the contribution: not a new
mechanism, but a bound on what the existing ones can deliver.

## Why this is open

The occupancy sweep found the mechanism thoroughly taken and this specific gap consistently
left:

| Work | Does | Leaves |
|---|---|---|
| SkillGen (2605.10999) | per-artifact validation against 8 consumers, deprecation of failures | gates entries **independently**; no interaction measurement |
| SkillOpt (2605.23904) | candidate evaluated on frozen target, strict-improvement gate | optimises a **single document**, not a library |
| Strong-to-weak harnesses (2608.12307) | strong builder, frozen weak target, iterative refinement | **one bundled object**, end-to-end score, no memory component |
| Skill consumption (2605.23899) | 5 extractors × 6 targets; finds 25% of pairs Δ<0 (47% on ALFWorld) | diagnoses post hoc, does not gate; no interaction analysis |
| Demystifying Agent Skills (2608.14036) | retrieval precision collapses 29.6% → 3.3% as pool grows | measures retrieval, not per-entry value interaction |

Two independent agents reached this gap from different directions. Nobody measures what
happens when entries are selected **together**.

## Evidence already in hand

From the committed Q2 runs, before this was known to be the gap:

- **Non-additivity, direct.** `w_dob` measures **LOO +0.33 and ABS −0.50** on the same entry
  and backbone — the two protocols disagree on whether to keep it.
- **Interference, mechanistic.** In the v2 store, removing `w_phone` changed nothing: the 3B
  still emitted `+31%20(0)%2015%207814226` because five neighbouring entries carried the same
  stance. The entry read as harmless while being harmful.
- **B is established.** Four backbones, 5200 generations, two lineages: entry value tracks
  neither scale (within Qwen2.5-Coder 3B→7B, `c_dob` and `c_phone` move in opposite
  directions), nor generation (largest divergence 0.960 is Qwen-vs-Qwen), nor lineage
  (smallest divergence 0.260 is Qwen-vs-Gemma). See [RESULTS.md](../experiments/q2_model_conditionality/RESULTS.md).

## Experiments

The v3 instrument ([INSTRUMENT-V3.md](../experiments/q2_model_conditionality/INSTRUMENT-V3.md))
already produces the LOO and ABS measures. Costs assume ~3 gen/s on the 3B, batch 13.

| | Experiment | Measures | Conditions | Cost |
|---|---|---|---|---|
| **E1** | LOO vs ABS disagreement | rate of magnitude and **sign** disagreement per entry | already collected | done |
| **E2** | Pairwise interaction | `effect(A∪B) − effect(A) − effect(B)`; super/sub-additivity | 66 pairs × 50 tasks | ~20 min/model |
| **E3** | **Selection error** | performance of an independently-gated store vs full store vs best-found subset | ~200 sampled subsets × 50 tasks | ~60 min/model |
| **E4** | Size sweep | claim B within one family, size as the isolated variable | 4 sizes × 28 conditions × 50 | ~2 h total |
| **E5** | Cross-family control | already have Gemma-4-E2B, Qwen3.5-4B | collected | done |

**E3 is the money experiment.** It converts a methodological objection into a number: *how
much performance does independent gating leave on the table?* Everything else is supporting.

**E4 fills a gap A3 confirmed is unfilled** — no published work runs a controlled sweep with
4+ sizes in one family isolating scale. Qwen2.5-Coder ships 0.5B / 1.5B / 3B / 7B, all of
which fit the 17.1 GB card. We already hold 3B and 7B; 0.5B and 1.5B are small downloads.
14B and above do not fit and are out of scope.

## What kills this

1. **External validity — the biggest risk by far.** The instrument is synthetic
   record-normalisation. SkillGen and SkillOpt use real agent benchmarks. A critique of their
   protocol measured only on designed toy tasks is weak, and a reviewer will say so first.
   **Mitigation: E1 and E3 must be replicated on at least one real skill benchmark**, even at
   reduced scale. If that replication is not affordable, the paper should be framed as a
   controlled demonstration of a failure mode rather than a general claim about their systems.
2. **The effect may be small in realistic stores.** Our v2 interference was dramatic partly
   because six same-direction entries formed a coherent stance — an artefact of that design.
   Real stores are more heterogeneous, which may suppress the effect. E2 must report effect
   size honestly, including if it is negligible.
3. **Someone publishes interaction effects first.** Six directions died to this in one day.
   The window is weeks.
4. **The instrument still cannot express many negatives.** Only 1–2 of 12 entries produced
   negative effects at n=8–10 smoke scale, with sample-to-sample disagreement. **The queued
   coverage check at n=50 gates this whole plan** — below three negative-capable entries,
   E2 and E3 lack the dynamic range to say anything, and the plan should not proceed.

## Order of work

1. **Coverage check** (queued, `jetspace-scaffold-rsi-32`). Gate: ≥3 entries express
   negatives at n=50. **If this fails, stop and reconsider — do not proceed to E2.**
2. **E2** on the 3B. Cheap, and tells us whether interaction is large enough to matter.
3. **E3** on the 3B. The headline number.
4. **E4** — download 0.5B and 1.5B, run the sweep.
5. **Real-benchmark replication** of E1/E3. Scope depends on what is affordable; decide after
   E3 gives us an effect size worth defending.
6. E2/E3 on a second backbone for robustness.

Steps 1–4 are days of local compute under broker leases. Step 5 is the one with real cost and
the one that determines whether this is a workshop note or a short conference paper.

## Framing notes

- **Never use "distillation" unqualified.** Context distillation (2209.15189) absorbs context
  *into weights*; 2602.21103 uses the same word for the opposite. The term is unusable.
- **Pre-empt weak-to-strong generalisation in the first paragraph.** Reversed in both
  direction and product, but it is the largest adjacent subfield and will be the reflexive
  first objection.
- Use existing vocabulary: *validation-gated selection*, *optimizer/target model*,
  *extractor/consumer*, *negative transfer*, *inference-time intervention*. Do not coin.
- Anchor the economics on Davidson et al. (2312.07413, compute-equivalent gain 5–20× at <1%
  of retraining cost) — it is the only claim here with years of stress-testing behind it.
- **Primary-source everything.** A3 caught a search summary attributing fabricated per-size
  statistics to a real paper, and this repo already carries one error of exactly that kind
  (see REVISIONS.md). No number enters the paper from a secondary summary.

## Relationship to the existing program

This supersedes [PROGRAM.md](PROGRAM.md) as the active plan. C1, C2 and the strong form of C3
were falsified or occupied; C4's clean half survives but is not on this critical path. The
Q2 results and the v3 instrument are the assets this paper is built from — the program's
value turned out to be the measurement apparatus, not its claims.
