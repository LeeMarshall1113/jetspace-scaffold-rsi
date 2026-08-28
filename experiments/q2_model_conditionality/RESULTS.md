# Q2 — are per-entry effect sizes model-conditional?

**Run 2026-08-27/28. Three backbones: Qwen2.5-Coder-3B, Qwen2.5-Coder-7B, Qwen3.5-4B.
1300 greedy generations each (26 conditions x 50 tasks), 3900 total.**

## Verdict

**Signs are stable. Magnitudes are strongly conditional, and the conditionality is
idiosyncratic per model — it does not track scale or family.**

C3's strong form is not supported. A weaker form is, and the 7B run made its case
substantially stronger than the two-backbone result did.

| | |
|---|---|
| sign agreement | **18/18 entries (100%)** across all three backbones |
| Spearman rho | 3B/7B **+0.984** · 3B/4B **+0.924** · 7B/4B **+0.901** |
| max divergence | **0.960** (`c_dob`, 7B vs 4B) |

## Per-entry targeted effect (positive = entry helped)

| entry | class | Qwen2.5-Coder-3B | Qwen2.5-Coder-7B | Qwen3.5-4B |
|---|---|---|---|---|
| c_name | correct | +0.780 | +0.960 | +0.980 |
| **c_dob** | correct | **+0.660** | **+0.040** | **+1.000** |
| **c_phone** | correct | **+0.020** | **+0.360** | **+0.860** |
| c_amount | correct | +0.860 | +1.000 | +1.000 |
| c_weight | correct | +0.980 | +1.000 | +1.000 |
| c_code | correct | +0.980 | +0.960 | +1.000 |
| w_dob | wrong | +0.520 | +0.500 | +0.640 |
| w_name | wrong | −0.020 | −0.040 | +0.000 |
| w_phone / w_amount / w_weight / w_code | wrong | +0.000 | +0.000 | +0.000 |
| all six distractors | distractor | +0.000 | +0.000 | +0.000 / +0.003 |

## The result the 7B was run for

The 7B is same-family-different-scale to the 3B, so it separates *scale-tracking* divergence
from *idiosyncratic* divergence. Baseline accuracy on the target field **without** the hint:

| entry | 3B | 7B | 4B | reading |
|---|---|---|---|---|
| `c_dob` (dates are day-first) | 0.32 | **0.96** | **0.00** | 7B already reads day-first; 4B is confidently month-first |
| `c_phone` (drop the `(0)` prefix) | **0.96** | 0.64 | **0.14** | 3B already strips it; 4B never does |

Within one family, 3B to 7B, the two entries move in **opposite directions**:

- `c_dob` baseline 0.32 → 0.96. The larger model needs the hint *less* (+0.66 → +0.04).
- `c_phone` baseline 0.96 → 0.64. The larger model needs the hint *more* (+0.02 → +0.36).

So an entry's value is not a function of model scale, and not a function of family. It is a
function of **what that specific model already happens to believe about the data convention**,
which is not predictable from any metadata you have before measuring. That is the strongest
available argument for attestation being a measurement rather than a heuristic: you cannot
substitute a rule like "larger models need fewer hints", because the direction reverses
entry by entry within a single family.

## Methodological note: correlation is the wrong summary here

Spearman between 3B and 7B is **+0.984**, which reads as "effects are stable." But `c_dob`
diverges by 0.62 between exactly those two backbones. The correlation is inflated by twelve
entries sitting at ~0 (four floored wrong entries plus six distractors plus two near-zero).
**Report per-entry divergence, not rank correlation** — the aggregate statistic hides the
phenomenon it is being used to measure.

## What this means for C3

**Not supported: "gating eliminates negative transfer."** Requires a sign flip; zero of
eighteen entries flipped, across three backbones.

**Supported and now well-evidenced: entry value is backbone-specific and unpredictable
in advance.** Same entry, same task, values spanning 0.02 → 0.86 (`c_phone`) and 0.04 → 1.00
(`c_dob`). A relevance-ranked store loads both for every model; an attestation-gated store
knows `c_dob` is dead weight for the 7B and load-bearing for the 4B.

This is a precision and context-budget argument, and it connects to a measured number in the
literature: retrieval precision collapses from 29.6% to 3.3% as the skill pool grows
(2608.14036). C3's safety leg — poisoning, structurally irreversible admission (2608.05810) —
is untouched by this result and remains its stronger motivation.

## Limitations — load-bearing, not boilerplate

1. **The instrument probably cannot produce sign flips.** Store B floors: with a wrong hint
   in play the models sit at ~0 on the target field, so removing it cannot show recovery. Four
   of six wrong entries measured exactly 0.000 on all three backbones. The one wrong entry with
   genuine two-sided range (`w_dob`, +0.50 to +0.64 — half the dates are unambiguous by
   construction) agreed in sign everywhere. **Absence of sign flips here is weak evidence.**
2. **All three backbones are Qwen.** The 4B is a different generation, not a different lineage.
   A genuinely distant family (Gemma, Llama, Mistral) is still the missing condition — and the
   same weakness applies to AttriMem's cross-model stability result.
3. **Ground truth is designed clean.** Entries are unambiguously correct, wrong, or irrelevant.
   Real stores hold *conditionally* correct entries — right for some inputs, wrong for others —
   which is the most plausible source of genuine sign flips.
4. **Fifty record-normalisation tasks is a thin setting** next to EvoAgentBench's four
   long-horizon agentic domains, where the −36.3 cell was observed.

## Next measurement, in priority order

1. **A non-Qwen backbone.** The condition this whole run is missing.
2. **An instrument with two-sided range on wrong entries** — tasks where a wrong hint degrades
   from a non-floored baseline, so a sign flip is at least expressible.
3. Conditionally-correct entries, to probe the mechanism limitation (3) names.

## Reproduce

```bash
python run_loo.py --model <path> --tag <name> --limit 50 --batch 8 --max-new 160
python analyze.py qwen25c-3b qwen25c-7b qwen35-4b
```

Greedy decoding throughout, so every leave-one-out difference is exact rather than a sample
estimate. Reasoning-tuned backbones need `enable_thinking=False` — see `run_loo.py`. The 7B
needs `--batch 2 --mem-frac 0.92`; larger batches risk the documented VRAM/commit crash mode
on a 17.1 GB card.
