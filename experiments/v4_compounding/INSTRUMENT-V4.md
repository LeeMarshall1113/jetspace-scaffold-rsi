# v4 instrument — status

**Premise test PASSED at 7/12 negative-capable entries** (gate: ≥3; v3 managed 1/12).
Qwen2.5-Coder-3B, 60 tasks, 780 generations, all stores size-matched to 18 entries.

## Result

| entry | field | base | +wrong | Δ | on subset |
|---|---|---|---|---|---|
| `p_iban_lower` | iban | 1.00 | 0.15 | **−0.85** | −0.85 |
| `p_amt_round` | amount | 0.95 | 0.15 | **−0.80** | −0.79 |
| `p_zip_pad` | zip | 1.00 | 0.58 | **−0.42** | −0.42 |
| `p_code_dash` | code | 0.87 | 0.58 | **−0.28** | −0.28 |
| `p_amt_comma` | amount | 0.95 | 0.72 | **−0.23** | −0.23 |
| `p_iban_dash` | iban | 1.00 | 0.90 | −0.10 | **−0.20** |
| `p_code_ad` | code | 0.87 | 0.83 | −0.03 | −0.06 |
| `p_dob_slash`, `p_dob_pre70` | dob | 0.98 | 0.98 | +0.00 | +0.00 |
| `p_state_dot`, `p_state_vwl` | state | 1.00 | 1.00 | +0.00 | +0.00 |
| `p_zip_two` | zip | 1.00 | 1.00 | +0.00 | +0.00 |

Ample dynamic range for §4 and §6. Four of six fields respond; effects reach −0.85.

## What still does not work, and it is not random

**`dob` and `state` are immune.** Both sit at 0.98–1.00 with the correct entry and neither
budges for any wrong variant. Two different reasons:

- **`state`** — both its wrong entries propose an *addition* (trailing period, `US-` prefix)
  rather than a competing transform. Consistent with the rule established in the first
  premise test: models ignore add-ons. This is a pool design error, not a property of the
  field, and is fixable.
- **`dob`** — `p_dob_slash` *is* a competing transform (slashes vs hyphens for ISO order) and
  it still fails. The likely reason is that ISO-with-hyphens is an unusually strong canonical
  prior, so instructing slashes contradicts confident behaviour — the v3 failure mode
  resurfacing on one field. Not fixable by rewording; `dob` may simply be unusable as a
  damageable field.

**Conditional entries largely do not bite.** Only 2 of 6 subset-restricted entries register,
both weakly (`p_iban_dash` −0.20 on subset, `p_code_ad` −0.06). The always-applicable
competing transforms are far stronger. Subset attribution therefore rests on two thin
entries — it was a nice-to-have for §6 and should not be leaned on.

## Consequence for the plan

B1 (dynamic range) is cleared. §4 can proceed on the four responsive fields.

Before §6, consider dropping `dob` and `state` from the damageable set rather than carrying
four dead entries through a multi-generation loop, and replacing `p_state_dot`/`p_state_vwl`
with competing transforms since that failure is a design error rather than a finding.
