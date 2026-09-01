# Section 4 — what independent per-entry gating costs

Qwen2.5-Coder-3B, 60 tasks, 18-candidate pool, 211 unique stores measured, all
size-matched to 26 entries. Greedy decoding, so every comparison is exact.

## Result

| procedure | acc | gap to oracle | evaluations | store |
|---|---|---|---|---|
| **independent** (what published systems do) | 0.897 | **−0.069** | 19 | 4 correct + **3 wrong** |
| **global-effect** scoring | 0.897 | **−0.069** | 19 | identical |
| **greedy** + re-measurement | **0.967** | 0.000 | 85 | 4 correct |
| all 6 correct entries | 0.897 | **−0.069** | — | 6 correct |
| **oracle** (best found) | **0.967** | — | 232 | 4 correct |

## Three findings

**1. Independent gating costs 0.069 and admits harmful entries.** It keeps
`p_code_ad`, `p_phone_dash` and `p_ref_early` — three entries that hurt in situ —
and omits nothing it should have kept. The failure is one-directional here: it
over-admits rather than under-admits.

**2. Global-effect scoring does not help.** It produced a byte-identical store.
Scoring on total accuracy rather than target-field accuracy was the cheap fix
worth hoping for — same O(n) cost, no protocol change — and it recovers none of
the gap. The O(n·k) cost of re-measurement looks unavoidable rather than optional.

**3. The strongest result: a store of *only correct entries* is worse than a subset
of them.** All six correct entries score 0.897; the four-entry oracle scores 0.967.
Adding `c_iban` and `c_zip` — both individually correct, both describing their field
accurately — costs 0.069.

That third finding is the sharpest form of the paper's claim. Independent gating can
be defended as a heuristic that admits the occasional bad entry. It cannot be
defended against a case where **every entry is correct and the store is still
suboptimal**, because no per-entry criterion of any kind distinguishes the six-entry
store from the four-entry one. Entry correctness is not the property selection
should be optimising, and per-entry evaluation cannot see the property that matters.

## Caveat on the oracle

The first run's oracle returned 0.906 — below greedy's 0.967 — because single-start
hill-climbing from the best random sample stalls when 12 of 18 candidates are
harmful. A ceiling that loses to a procedure it bounds is a bug. Fixed to multi-start
seeded with greedy's store and the all-correct store; it now converges to greedy's
store, which is also the best of all 211 stores measured.

The oracle is therefore "best found", not proven optimal. 2^18 is 262,144 subsets and
exhaustive search is not affordable at ~13s per store. Greedy reaching the same store
is weak evidence it is optimal, not proof.

## Limitations

- One backbone. §7 replicates across the other three.
- The candidate pool is 18; real stores are larger, and the O(n) vs O(n·k) distinction
  matters more as n grows.
- Synthetic tasks. Unchanged from the note: this demonstrates a failure mode under
  controlled conditions.
- `c_iban` and `c_zip` are excluded because those fields are already near-perfect
  without a hint, so their entries add context cost without benefit. Whether the same
  holds where every field genuinely needs its entry is untested.
