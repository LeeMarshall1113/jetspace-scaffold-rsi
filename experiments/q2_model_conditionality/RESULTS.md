# Q2 — are per-entry effect sizes model-conditional?

**Run 2026-08-27/28. Four backbones: Qwen2.5-Coder-3B, Qwen2.5-Coder-7B, Qwen3.5-4B,
Gemma-4-E2B. 1300 greedy generations each (26 conditions x 50 tasks), 5200 total.**

## Verdict

**Signs are stable, including across a lineage change. Magnitudes are strongly conditional,
and the conditionality is idiosyncratic — it tracks neither scale, generation, nor lineage.**

C3's strong form is not supported. The weaker form is, and is now the better-evidenced of the
two because the cross-lineage backbone did not rescue the strong form.

| | |
|---|---|
| sign agreement | **18/18 entries (100%)** across all four backbones |
| max divergence | **0.960** (`c_dob`, Qwen2.5-Coder-7B vs Qwen3.5-4B) |

## Per-entry targeted effect (positive = entry helped)

| entry | class | Qwen2.5-C-3B | Qwen2.5-C-7B | Qwen3.5-4B | Gemma-4-E2B |
|---|---|---|---|---|---|
| c_name | correct | +0.780 | +0.960 | +0.980 | +1.000 |
| **c_dob** | correct | **+0.660** | **+0.040** | **+1.000** | **+0.740** |
| **c_phone** | correct | **+0.020** | **+0.360** | **+0.860** | **+0.900** |
| c_amount | correct | +0.860 | +1.000 | +1.000 | +0.980 |
| c_weight | correct | +0.980 | +1.000 | +1.000 | +1.000 |
| c_code | correct | +0.980 | +0.960 | +1.000 | +1.000 |
| w_dob | wrong | +0.520 | +0.500 | +0.640 | +0.520 |
| w_name | wrong | −0.020 | −0.040 | +0.000 | +0.000 |
| w_phone / w_amount / w_weight / w_code | wrong | +0.000 | +0.000 | +0.000 | +0.000 |
| six distractors | distractor | +0.000 | +0.000 | ≤+0.003 | ≤+0.007 |

## The core finding: lineage does not predict entry value

Accuracy on the target field **without** the hint — i.e. what each model already believes:

| backbone | `dob` (day-first?) | `phone` (drop `(0)`?) |
|---|---|---|
| Qwen2.5-Coder-3B | 0.32 | **0.96** |
| Qwen2.5-Coder-7B | **0.96** | 0.64 |
| Qwen3.5-4B | **0.00** | **0.14** |
| Gemma-4-E2B | 0.26 | **0.10** |

Three independent ways the divergence fails to follow any predictable axis:

1. **Not scale.** Within one family (Qwen2.5-Coder, 3B → 7B) the two entries move in *opposite*
   directions: `c_dob` +0.66 → +0.04 (larger model needs it less), `c_phone` +0.02 → +0.36
   (larger model needs it more).
2. **Not generation.** The largest divergence in the whole matrix, 0.960 on `c_dob`, is between
   two Qwen models (2.5-Coder-7B vs 3.5-4B).
3. **Not lineage.** The *smallest* max divergence, 0.260, is between Qwen3.5-4B and Gemma-4-E2B —
   two different lineages. The cross-lineage pair agrees more closely than the same-vendor
   cross-generation pair does.

An entry's value is a function of what that specific checkpoint happens to believe about a data
convention. Nothing in the model card predicts it. **That is the argument for attestation being
a measurement rather than a heuristic**: there is no rule of the form "larger models need fewer
hints" or "same-family models share entry values" that survives this table.

## Methodological note: correlation is the wrong summary

Spearman between the 3B and 7B is **+0.984**, which reads as "effects are stable" — while
`c_dob` diverges 0.62 between exactly those two. The correlation is inflated by twelve entries
sitting at ~0 (four floored wrong entries, six distractors, two near-zero). **Report per-entry
divergence, not rank correlation.** The aggregate statistic hides the phenomenon it is being
used to measure.

## What this means for C3

**Not supported: "gating eliminates negative transfer."** Requires a sign flip. Zero of eighteen
entries flipped across four backbones spanning two lineages, three generations and 2B–7B scale.
Adding the non-Qwen backbone was the strongest available chance to falsify this and it did not.

**Supported: entry value is backbone-specific and unpredictable in advance.** Same entry, same
task: 0.02 → 0.90 (`c_phone`), 0.04 → 1.00 (`c_dob`). A relevance-ranked store loads both for
every model; an attestation-gated store knows `c_dob` is dead weight for the 7B and load-bearing
for the 4B.

This is a precision and context-budget argument, connecting to a measured number in the
literature: retrieval precision collapses 29.6% → 3.3% as the skill pool grows (2608.14036).
C3's safety leg — poisoning, structurally irreversible admission (2608.05810) — is untouched by
this result and remains its stronger motivation.

## Limitations — load-bearing, not boilerplate

1. **The instrument probably cannot produce sign flips.** Store B floors: with a wrong hint in
   play the models sit at ~0 on the target field, so removing it cannot show recovery. Four of
   six wrong entries measured exactly 0.000 on all four backbones. The one wrong entry with
   genuine two-sided range (`w_dob`, +0.50 to +0.64) agreed in sign everywhere. **Absence of
   sign flips is weak evidence given the instrument cannot easily express one.**
2. **Ground truth is designed clean.** Entries are unambiguously correct, wrong, or irrelevant.
   Real stores hold *conditionally* correct entries — right for some inputs, wrong for others —
   which is the most plausible source of genuine sign flips.
3. **Fifty record-normalisation tasks is a thin setting** next to EvoAgentBench's four
   long-horizon agentic domains, where the −36.3 cell was observed.
4. Gemma-4-E2B is a nested/MatFormer 2B; whether E4B or a dense non-Qwen model behaves the same
   is untested.

## Next measurement

Limitation 1 is now the binding one, and it is a design problem rather than a coverage problem —
a fifth backbone will not fix it. **The next instrument needs two-sided range on wrong entries:
tasks where a wrong hint degrades from a non-floored baseline, so a sign flip is expressible at
all.** Only then does "no sign flips" become strong evidence.

## Reproduce

```bash
python run_loo.py --model <path> --tag <name> --limit 50 --batch 8 --max-new 160
python analyze.py qwen25c-3b qwen25c-7b qwen35-4b gemma4-e2b
```

Greedy decoding throughout, so every leave-one-out difference is exact rather than a sample
estimate. Notes: reasoning-tuned backbones need `enable_thinking=False`; Gemma ships its chat
template as a standalone `chat_template.jinja` that a `*.json` allow-list will silently miss,
producing an empty template rather than an error; the 7B needs `--batch 2 --mem-frac 0.92` on a
17.1 GB card.

## Cost

| backbone | weights | batch | wall clock |
|---|---|---|---|
| Qwen2.5-Coder-3B | 5.8 GB | 13 | ~13 min |
| Qwen3.5-4B | 8.8 GB | 8 | ~110 min |
| Qwen2.5-Coder-7B | 15 GB | 2 | 133 min |
| Gemma-4-E2B | 10.2 GB | 8 | **7.2 min** |
