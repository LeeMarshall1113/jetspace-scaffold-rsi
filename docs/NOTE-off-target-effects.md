# Context entries have off-target effects, so validating them independently is unsound

**Short methodological note. Draft, 2026-08-29.**
Data: [`experiments/q2_model_conditionality`](../experiments/q2_model_conditionality/).

> **Read the limitations before citing this.** Two are serious: the comparison is not
> size-matched, so part of the effect may be context length rather than content (PR #1);
> and of the two headline numbers, one replicates across backbones and one does not.

---

## Claim

Systems that build inference-time context for a target model validate **each entry
independently**: generate a candidate, load it into the frozen consumer, measure whether it
helps, keep it if so. SkillGen (2605.10999) gates one skill at a time and deprecates
failures. SkillOpt (2605.23904) accepts an edit only if the target's score strictly
improves. Strong-to-weak harness construction (2608.12307) refines one bundled object
against a held-out slice.

That protocol is only sound if an entry's contribution is approximately independent of what
else is loaded. **It is not.** We measure entries that change the model's accuracy on fields
they never mention, in both directions and by large margins, and entries whose measured
value reverses depending on which measurement protocol is used.

## The measurement

A controlled instrument, not a real agent benchmark. 50 record-normalisation tasks, six
fields, each scored by exact match. A store holds twelve entries: six field-hints (one per
field, some correct and some wrong) and six topically-plausible distractors that target no
scored field. Greedy decoding throughout, so every difference is exact rather than a sample
estimate. Qwen2.5-Coder-3B, 28 conditions × 50 tasks = 1296 generations.

Two effect measures per entry, both on the entry's own target field:

- **LOO** = `score(full store) − score(full store minus entry)` — the entry's value *in
  context*, which is what a deployed store cares about.
- **ABS** = `score(full store) − score(distractors only)` — the entry's value against a
  hint-free baseline, closer to what independent validation measures.

If effects were additive these would agree.

## Result 1 — entries move fields they do not mention

Only one entry in each store targets `state`, and only one targets `dob`. Removing that one
entry leaves five hints about *other* fields plus six distractors. Those non-mentioning
entries move the field substantially:

| field | distractors only | other-field hints, no hint for this field | full store |
|---|---|---|---|
| `state` | 0.02 | **0.74** | 0.00 |
| `dob` | 0.48 | **0.00** | 1.00 |

`state` accuracy rises **+0.72** from entries that never refer to it. `dob` accuracy falls
**−0.48** from entries that never refer to it.

### Replication — one of the two holds

Repeating the measurement on further backbones separates the two cases sharply:

| backbone | `state` | `dob` |
|---|---|---|
| Qwen2.5-Coder-3B | **+0.72** | **−0.48** |
| Qwen3.5-4B | −0.14 | **−0.68** |
| Gemma-4-E2B | 0.00 *(floored, uninformative)* | 0.00 *(floored)* |
| Qwen2.5-Coder-7B | pending | pending |

**`dob` replicates** — same direction, comparable magnitude, across two model generations.
Entries that never mention the date field drive its accuracy to zero on both.

**`state` does not.** +0.72 on the 3B and −0.14 on the 4B. It is model-specific, and it was
the larger and more quotable of the two numbers. Gemma sits at 0.00 on both fields, which is
a floor rather than a clean null — uninformative, not contradicting.

So the phenomenon survives a change of model generation on one field and not the other. The
honest reading is that off-target effects are real and can be large, but their sign and
magnitude are model-specific in the same way per-entry value is (see Relation to prior work).
Off-target effects of this size are not a rounding error on an entry's own value — where they
occur they are larger than most of the on-target effects being measured — but *where* they
occur is not predictable from this data.

## Result 2 — measured value depends on the protocol

Because of Result 1, the two measures disagree. Three of twelve entries diverge by more
than 0.05; one disagrees in sign.

| entry | LOO | ABS | gap |
|---|---|---|---|
| `w_state` | **−0.74** | **−0.02** | 0.72 |
| `c_dob` | **+1.00** | **+0.52** | 0.48 |
| `w_dob` | −0.04 | +0.14 | 0.18, **sign** |

An earlier run at smaller n showed the same pattern more starkly, with `w_dob` at LOO
**+0.33** against ABS **−0.50** — a full sign reversal on a wrong entry.

## What this does to independent gating

Take `w_state`, an entry stating a false convention for the `state` field.

- **Evaluated independently** — loaded alone against a hint-free baseline — it moves accuracy
  from 0.02 to 0.00. Effect ≈ **−0.02**. Indistinguishable from noise. A gate that keeps
  entries which do not measurably hurt will **keep it**.
- **Evaluated in the store it will actually be deployed in**, it costs **−0.74**, because the
  other entries would otherwise have carried `state` to 0.74 and this entry blocks them.

The same argument runs in reverse for `c_dob`, which is worth +0.52 alone and +1.00 in
context: independent validation *understates* it by half.

So independent gating both keeps entries that are harmful in situ and misprices entries that
are valuable in situ. The error is not small and it is not centred on zero.

## Why this is not simply fixed by measuring in context

The obvious repair — evaluate each candidate against the current store rather than against
nothing — is what LOO does, and it is better. But it is order-dependent: an entry's measured
value now depends on which entries were admitted before it, so a greedy admission sequence
can reach different stores from the same candidate pool. Correct selection over a candidate
pool of size *n* is a subset-selection problem, not *n* independent decisions, and the
published protocols are solving the latter.

We do not quantify how much performance that leaves on the table. That experiment needs an
instrument with more dynamic range than this one has (see Limitations), and we are not
claiming a number we did not measure.

## Relation to prior work

- **2605.23899** finds 25% of extractor–target pairs produce negative transfer (47% on
  ALFWorld) but diagnoses it post hoc and does not gate. Our result offers one mechanism for
  such negatives that is not about the entry's own content.
- **2608.14036** reports retrieval precision collapsing 29.6% → 3.3% as a skill pool grows.
  That is a *retrieval* failure; ours is a failure that occurs even when the right entry is
  retrieved, because its value is not a property of the entry alone.
- **SkillGen, SkillOpt, 2608.12307** are the protocols this note is about. None measures
  interaction between entries.

Separately, and consistent with prior work: entry value tracks neither model scale,
generation, nor lineage. Across four backbones and 5200 generations, within one family
(3B → 7B) two entries moved in opposite directions, the largest divergence was between two
same-vendor models, and the smallest was across lineages. So there is no metadata shortcut
that avoids measuring against the specific consumer — which makes the cost of correct
selection the operative question.

## Limitations

These are load-bearing, not boilerplate.

1. **The comparison is not size-matched, and this is the most serious limitation.**
   Raised by @jmuslu in PR #1. `distractors only` holds **6** entries and
   `other-field hints, no hint for this field` holds **11**, so the two stores differ
   by five entries of *content* and five of *length*. The instrument had only six
   distractors, so there was no way to hold length constant. The measured +0.72 and
   −0.48 therefore have an alternative explanation we did not rule out: part of the
   effect may be a context-length effect rather than a content effect.

   PR #1 framed this as an interpretability problem. It is worse than that — it is a
   confound in the causal attribution, and it weakens Result 1 specifically. The fix
   is a size-matched control: pad every store to a fixed entry count with filler drawn
   from a pool disjoint from the entries under test. That is built into the v4
   instrument (`experiments/v4_compounding/store.py:build`) and is mandatory there, but
   **the numbers in this note predate it and are not size-matched.**

2. **Result 2 is one backbone.** The LOO/ABS divergence is measured on Qwen2.5-Coder-3B
   only. Result 1 has now been replicated on two further backbones with the mixed outcome
   above; Result 2 has not, and the 7B is still pending.
3. **Synthetic tasks.** Record normalisation with designed hints, not a real agent benchmark.
   The systems criticised here use real benchmarks. This demonstrates a failure mode under
   controlled conditions; it does not establish the magnitude in their settings.
4. **Twelve entries, three disagreements.** Small. The two large cases are clean and
   mechanistically interpretable, but this is a demonstration, not an estimate.
5. **We cannot price the consequence.** The instrument could not express enough negative
   effects to simulate independent gating against an oracle-selected subset — a pre-registered
   coverage gate returned 1 of 12 negative-capable entries against a threshold of 3, and we
   stopped rather than run an underpowered experiment. See
   [INSTRUMENT-V3.md](../experiments/q2_model_conditionality/INSTRUMENT-V3.md).
6. **Wrong entries here are implausible.** They contradict transforms the model performs
   confidently, and models largely ignore them — which is why coverage failed. Real negative
   transfer likely comes from *plausible* but wrong entries. This note's mechanism does not
   depend on that, but its generality to that case is untested.

## What would settle it

In order of value per hour:

1. Replicate Results 1 and 2 on the three other backbones already on disk (~4h).
2. Rebuild the instrument with *plausible* wrong entries — right for most records, wrong for a
   subset — so negative effects are expressible and independent gating can be simulated
   against an oracle subset.
3. Replicate on one real skill benchmark, which is what converts this from a demonstration
   into a claim about the deployed protocols.

## Reproduce

```bash
cd experiments/q2_model_conditionality
python run_loo.py --model <path> --tag v3-<name> --limit 50 --batch 13 --max-new 160
python analyze.py --stores mixed v3-<name>
```

Raw generations for every condition are committed under `results/`.
