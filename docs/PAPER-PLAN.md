# Paper plan — selection error compounds across self-improvement generations

**Target: full paper.** Revised 2026-08-29. Supersedes the short-note and the
context-selection scopes; both are in git history.

---

## Headline

Self-evolving agents accumulate context artifacts and decide what to keep, every generation.
They decide **independently per entry** — ACE curates its playbook each round, MEGA evolves
its curation strategies, ERSkill co-evolves router and skills, ReasoningBank distils and
prunes, SkillGen gates and deprecates.

But an entry's value is a property of the **store**, not the entry. So the selection error is
not made once. It is made at every generation, it compounds, and it compounds **silently** —
the loop's own validation reports that everything it kept was fine.

**Prediction, and the paper's core claim:** the gap between independent gating and oracle
selection **widens with generation count**, because the fixed reference context that
independent gating evaluates against drifts further from the deployed store as the store
grows. Interaction-aware selection does not diverge, or diverges more slowly.

This is the context-domain analogue of HGM's Metaproductivity-Performance Mismatch: greedy
per-item scoring is the wrong objective, because value is a property of the lineage rather
than the item. HGM established that for *code* lineages. Nobody has established it for
context — and a search for exactly this returned zero hits during the occupancy sweeps.

## Structure

| § | Content | Built? |
|---|---|---|
| 1–2 | Motivation; self-evolving systems gate independently, every generation | related work done — three occupancy sweeps, ~30 papers primary-sourced |
| 3 | **Entries have off-target effects** — they change accuracy on fields they never mention | **measured**, partially replicated |
| 4 | **The single-shot cost** — independent gating vs oracle subset | not built (E3) |
| 5 | **Selection procedures** — four, below | not built |
| 6 | **Compounding** — the loop experiment; does the gap widen? | not built, **the paper** |
| 7 | Cross-backbone evaluation, and one real benchmark | not built |
| 8 | Verification-cost analysis: quality per evaluation budget | not built |

§3–5 are now setup. **§6 is the contribution.**

## The four selection procedures (§5)

1. **Independent gating** — baseline; each candidate scored against a fixed reference context,
   kept if it helps. O(n) per generation. What published systems do.
2. **Greedy forward selection with re-measurement** — add the best marginal contributor *given
   the current store*. O(n²), order-dependent; that dependence is itself a measurement.
3. **Global-effect scoring** — score by effect on *total* task performance, not target-field
   performance. Same O(n) as the baseline, and our §3 data says it catches the failure we
   measured. If it recovers most of the gap it is the practical recommendation, since adopting
   it costs almost nothing.
4. **Lineage scoring** — score an entry by the performance of stores that *descend from*
   including it, not by its immediate marginal gain. The direct HGM/CMP analogue, and the one
   procedure that is native to the loop setting rather than borrowed from single-shot
   selection.

**Negative result worth reporting either way:** if entry effects are not submodular — and our
superadditive cases suggest they are not — greedy has no approximation guarantee here, and the
field should stop assuming one.

## The compounding experiment (§6)

**Protocol.** Fixed candidate pool, drawn in batches, so *generation quality is held constant
and only selection varies*. This is deliberate: the claim is about selection, and
LLM-generated candidates would confound it with proposer variance.

For each selection procedure, for generations *k = 1…N*:

1. Draw a batch of *m* candidates from the pool.
2. Select which to admit, using that procedure. Independent gating evaluates against its
   **fixed reference**; interaction-aware procedures evaluate against the **current store**.
3. The admitted store carries forward and conditions generation *k+1*.
4. Measure: task performance of the resulting store; gap to the oracle subset at that
   generation; count of mis-kept and mis-dropped entries.

**Measured outcome:** performance-vs-generation trajectories, and whether the
independent-gating gap to oracle grows, stays flat, or closes.

**What would falsify the claim:** flat gap across generations. That would mean the error is
one-shot and does not accumulate — a real result, and worth reporting, but a much smaller
paper. Report it either way.

**Why the mechanism should produce divergence:** independent gating's reference context is
fixed while the deployed store grows, so the conditions under which an entry was validated
diverge monotonically from the conditions under which it is used. §3 says that divergence
changes an entry's value by up to 0.72.

## Blockers, in dependency order

**B1 — the instrument cannot express enough negatives.** Coverage gate returned 1/12 against
a threshold of 3. Without negatives, independent gating cannot visibly mis-select and §4 and
§6 have nothing to measure. *Cause:* our wrong entries are **implausible** — they contradict
transforms the model performs confidently and it ignores them (`w_iban`: +0.00 against a
hint-free baseline of 1.00). *Fix:* v4 entries must be **plausible but wrong** — right for
most records and wrong for a subset, or right for a neighbouring field.

**B2 — pool size.** §6 needs a candidate pool large enough for several generations of batched
admission. 12 entries will not do; target 40–60.

**B3 — synthetic tasks only.** The systems criticised use real agent benchmarks. §7 needs at
least one, or the paper is a controlled demonstration making claims about deployed systems.
The reviewers' first objection.

## Critical path

| | Work | Est. | Depends |
|---|---|---|---|
| 1 | **v4 instrument** — plausible-wrong entries, 40–60 pool, coverage re-gated | 3–4 days | — |
| 2 | **§4** single-shot cost, quantified | 2 days | 1 |
| 3 | **§5** implement four procedures | 3 days | 1 |
| 4 | **§6 compounding loop** — the paper | 3–4 days | 2, 3 |
| 5 | **§7** cross-backbone (4 models on disk) | ~1 day | 3 |
| 6 | **§7 real benchmark** | 4–7 days, **largest unknown** | 3 |
| 7 | **§8** cost curves | 1 day | 4 |
| 8 | Writing | 1–2 weeks, overlappable from step 2 | — |

**Realistic: 4–5 weeks to a submission-ready draft.** Steps 1–5 and 7 are local compute under
broker leases and well understood. Step 6 is the one that could extend it.

## Decisions still needed

1. **Compute envelope for step 6.** A real agent benchmark with a multi-entry store is the
   setting where EvoAgentBench required self-hosted 27B+ models. If local-only is a hard
   constraint, target the smallest viable real benchmark and say so in the paper.
2. **Venue and deadline**, which set how much of step 6 is affordable.

## Standing risk

Six directions died to occupancy sweeps in a single day, in a field publishing monthly.
Mitigations: §6 is a narrower target than the mechanism space that keeps getting occupied;
and **preprinting §3 early** timestamps the measurement independently, so if the method is
scooped the measurement is still ours.

## Already done, not to be redone

- Related work: three occupancy sweeps, ~30 papers checked against primary sources.
- Framing hazards: never write "distillation" unqualified (2209.15189 means the opposite of
  our sense; 2602.21103 means the opposite of *that*); pre-empt weak-to-strong generalisation
  in the first paragraph.
- §3, partially — `dob` spillover holds on two backbones, `state` is model-specific, Gemma is
  floored. Status honest in [NOTE-off-target-effects.md](NOTE-off-target-effects.md).
- Metadata shortcut foreclosed: entry value tracks neither scale, generation nor lineage
  across 4 backbones and 5200 generations, so measurement cannot be replaced by a heuristic.
- The instrument, the broker-leased runner, and 6,700+ committed generations.
