# Paper plan — interaction-aware selection for inference-time context

**Target: full paper.** Revised 2026-08-29, replacing the short-note scope.
Prior version's plan is in git history; what was measured under it is in
[NOTE-off-target-effects.md](NOTE-off-target-effects.md) and stands as motivation.

---

## Why the previous scope was a workshop note

It observed a failure mode. Observations are workshop-shaped however many backbones they run
on, because the reader's next question — *so what should I do instead?* — has no answer in
them. A full paper needs the critique as motivation and a **method** as the contribution.

## The paper

**Claim.** Selecting inference-time context entries independently is unsound because entry
effects interact; interaction-aware selection recovers a measurable fraction of the gap to
oracle selection, at a verification cost that can be characterised rather than assumed.

**Structure.**

| § | Content | Built? |
|---|---|---|
| 1–2 | Motivation; published protocols gate independently (SkillGen 2605.10999, SkillOpt 2605.23904, strong-to-weak harnesses 2608.12307) | related work done, three occupancy sweeps |
| 3 | **Entries have off-target effects** — they change accuracy on fields they never mention | **measured**, partially replicated |
| 4 | **The cost of independence** — independent gating vs oracle subset | **not built** (E3) |
| 5 | **Interaction-aware selection** — the method | **not built** |
| 6 | Evaluation across backbones and on a real benchmark | **not built** |
| 7 | Verification-cost analysis: quality per evaluation budget | **not built** |

Sections 4–7 are the paper. Section 3 is the setup.

## The method (§5) — the actual contribution

Three selection procedures, evaluated against each other and against an oracle:

1. **Independent gating** (the baseline, what published systems do). Each candidate scored
   against a fixed reference context; keep if it helps. O(n) evaluations.
2. **Greedy forward selection with re-measurement.** Add the entry with the best marginal
   contribution *given the store so far*; repeat. O(n²) evaluations. Accounts for interaction
   but is order-dependent — that dependence is itself worth measuring.
3. **Global-effect scoring.** Score each entry by its effect on *total* task performance
   rather than on its target field. Cheap — same O(n) as independent gating — and our data
   says it would catch the specific failure we measured. If it recovers most of the gap, that
   is the practical recommendation and it costs adopters almost nothing.

**A negative result worth reporting either way:** if entry effects are not submodular — and
our superadditive cases suggest they are not — then greedy selection has no approximation
guarantee here, and the field should stop assuming one.

**Oracle** = best subset found by exhaustive search where *n* permits, sampled search
otherwise. This is the ceiling all three are measured against.

## Blockers, in dependency order

**B1 — the instrument cannot express enough negatives.** A pre-registered coverage gate
returned 1/12 negative-capable entries against a threshold of 3. Without negatives,
independent gating cannot visibly mis-select and §4 has nothing to measure.

*Cause, diagnosed:* our wrong entries are **implausible** — they contradict transforms the
model performs confidently, and models largely ignore them (`w_iban`: +0.00 against a
hint-free baseline of 1.00). *Fix:* v4 entries must be **plausible but wrong** — correct for
most records and wrong for a subset, or correct for a neighbouring field. The model has no
grounds to reject them, so they bite.

**B2 — synthetic tasks only.** The systems criticised use real agent benchmarks. Section 6
needs at least one real skill/memory benchmark or the paper is a controlled demonstration
making claims about deployed systems. This is the single largest external-validity risk and
the reviewers' first objection.

**B3 — scale.** 12 entries is enough to demonstrate, not enough to characterise a selection
procedure. §5–7 need a candidate pool large enough for the O(n) vs O(n²) distinction to
matter — 40+ entries.

## Critical path

| | Work | Estimate | Depends on |
|---|---|---|---|
| 1 | **v4 instrument**: plausible-wrong entries, 40+ candidate pool, coverage re-gated | 2–3 days | — |
| 2 | **§4**: independent gating vs oracle, quantified | 2 days compute + analysis | 1 |
| 3 | **§5**: implement all three selection procedures | 2–3 days | 1 |
| 4 | **§6**: cross-backbone evaluation (4 models on disk) | ~1 day compute | 3 |
| 5 | **§6 real benchmark**: port the measurement | 4–7 days, **largest unknown** | 3 |
| 6 | **§7**: cost curves | 1 day | 2–4 |
| 7 | Writing | 1–2 weeks, overlappable from step 2 | — |

**Realistic: 3–4 weeks to a submission-ready draft**, assuming the real-benchmark port
behaves. Steps 1–4 and 6 are local compute under broker leases and are well understood. Step
5 is the one that could double the estimate.

Writing can start at step 2 — sections 1–3 depend on nothing that follows.

## Decisions needed

1. **Compute envelope.** Steps 1–4 fit the local box. Step 5 may not: a real agent benchmark
   with a multi-entry store is the setting where EvoAgentBench needed self-hosted 27B+ models.
   If local-only is a hard constraint, §6 should target the smallest viable real benchmark
   rather than a headline one, and the paper should say so.
2. **Venue and deadline**, which set how much of step 5 is affordable.

## Standing risk

Six directions died to occupancy sweeps in one day. A 3–4 week build carries real scoop risk
in a field publishing monthly, and the mechanism space here is demonstrably crowded. Two
mitigations: the method (§5) is a smaller target than the mechanism, and posting §3 as a
preprint early timestamps the measurement independently of the method.

## What is already done and does not need redoing

- Related work: three occupancy sweeps, ~30 papers checked against primary sources.
- Framing hazards: never write "distillation" unqualified (2209.15189 means the opposite of
  what we mean; 2602.21103 means the opposite of *that*); pre-empt weak-to-strong
  generalisation in the first paragraph.
- §3 measurement, partially. Replication status is honest in
  [NOTE-off-target-effects.md](NOTE-off-target-effects.md): `dob` spillover holds on two
  backbones, `state` is model-specific, Gemma is floored.
- Metadata shortcut foreclosed: entry value tracks neither scale, generation nor lineage
  across 4 backbones and 5200 generations, so measurement cannot be replaced by a heuristic.
- The instrument, the broker-leased runner, and 6,700+ committed generations.
