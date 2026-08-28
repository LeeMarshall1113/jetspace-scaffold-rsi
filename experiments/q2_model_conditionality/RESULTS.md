# Q2 — are per-entry effect sizes model-conditional?

**Run 2026-08-27. Backbones: Qwen2.5-Coder-3B, Qwen3.5-4B. 1300 greedy generations each
(26 conditions x 50 tasks). Qwen2.5-Coder-7B not run.**

## Verdict

**Signs are stable. Magnitudes are not.** C3's strong form is not supported by this
instrument; a weaker, still-useful form is.

| | |
|---|---|
| sign agreement | **18/18 entries (100%)** — no entry helps one backbone and hurts the other |
| Spearman rho | **+0.924** |
| max divergence | **0.840** on `c_phone` |

## Per-entry targeted effect (positive = entry helped)

| entry | class | Qwen2.5-Coder-3B | Qwen3.5-4B |
|---|---|---|---|
| c_name | correct | +0.780 | +0.980 |
| c_dob | correct | +0.660 | +1.000 |
| **c_phone** | correct | **+0.020** | **+0.860** |
| c_amount | correct | +0.860 | +1.000 |
| c_weight | correct | +0.980 | +1.000 |
| c_code | correct | +0.980 | +1.000 |
| w_dob | wrong | +0.520 | +0.640 |
| w_name | wrong | −0.020 | +0.000 |
| w_phone / w_amount / w_weight / w_code | wrong | +0.000 | +0.000 |
| all six distractors | distractor | +0.000 | +0.000 / +0.003 |

Class means: correct +0.713 / +0.973 · wrong +0.083 / +0.107 · distractor +0.000 / +0.001

## What this means for C3

**Not supported: "gating eliminates negative transfer."** Negative transfer requires an
entry whose sign flips across backbones. Zero of eighteen did.

**Supported: entry value is strongly backbone-dependent in magnitude.** `c_phone` is worth
+0.86 to the 4B and **+0.02 to the 3B** — the 3B already strips the `(0)` trunk prefix
unprompted (phone accuracy 0.98 without the hint), so that entry is pure dead weight for it.
Same entry, same task, 43x difference in value.

That reframes C3 from a correctness argument to a **precision and context-budget** argument,
which connects to a measured number already in the literature: "Demystifying Agent Skills"
(2608.14036) reports retrieval precision collapsing from 29.6% to 3.3% as the skill pool
grows. Dropping entries that are dead weight *for the current backbone* attacks that directly.
A relevance-ranked store loads `c_phone` for both models; an attestation-gated store knows it
is worthless to one of them.

## Limitations — these are load-bearing, not boilerplate

1. **The instrument probably cannot produce sign flips.** Store B floors: with a wrong hint
   in play the models sit at ~0 on the target field, so removing it cannot show a recovery.
   Four of six wrong entries measured exactly 0.000 on both backbones for this reason. The one
   wrong entry with genuine two-sided range (`w_dob`, +0.52 / +0.64 — half the dates are
   unambiguous by construction) agreed in sign. **A sign flip may simply be unmeasurable here.**
2. **Both backbones are Qwen.** "Cross-family" overstates it — Qwen2.5-Coder and Qwen3.5 are
   one lineage. AttriMem's cross-model stability result has the same weakness. A genuinely
   distant family (Gemma, Llama) is the missing condition.
3. **Ground truth is designed.** Entries are cleanly correct, wrong, or irrelevant. Real memory
   stores contain entries that are *conditionally* correct — right for some inputs, wrong for
   others — which is where sign flips would plausibly come from. This design may exclude the
   phenomenon by construction.
4. **EvoAgentBench's negative cells came from long-horizon agentic tasks across four domains.**
   Fifty record-normalisation tasks is a much thinner setting. Absence of sign flips here is
   weak evidence about their absence there.

## Consequence for the program

- C3 is **not dead**, but its headline must change: from eliminating negative transfer to
  pruning backbone-specific dead weight. The safety motivation (poisoning, irreversible
  admission) is untouched by this result and is now the stronger of C3's two legs.
- The measured 0.84 spread is a real finding and is the number to build on.
- **Next measurement, in priority order:** (a) Qwen2.5-Coder-7B, which is same-family-different-
  scale and tells us whether `c_phone`-style divergence tracks scale or is idiosyncratic;
  (b) a non-Qwen backbone, which is the condition this run is actually missing; (c) an
  instrument with two-sided range on wrong entries, i.e. tasks where a wrong hint degrades from
  a non-floored baseline.

## Reproduce

```bash
python run_loo.py --model <path> --tag <name> --limit 50 --batch 8 --max-new 160
python analyze.py qwen25c-3b qwen35-4b
```

Greedy decoding throughout, so every leave-one-out difference is exact rather than a sample
estimate. Reasoning-tuned backbones need `enable_thinking=False`; see the note in `run_loo.py`.
