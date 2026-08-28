# v3 instrument — making negative per-entry effects expressible

**Status: partial fix. v2 could produce zero negative effects structurally; v3 produces
some. Coverage is narrower than hoped and the reason is interesting.**

Not yet run at full scale. The four-backbone v2 result in [RESULTS.md](RESULTS.md) stands
on its own; this is a rebuilt instrument for the sign-flip question v2 could not address.

## What was actually wrong with v2

Two independent faults, and the first was misdiagnosed at the time.

**Fault 1 — cross-entry interference, not a floor.** v2's store B held six same-direction
wrong hints. Removing one left the other five, and they carried the same global stance, so
the removed entry's leave-one-out effect read ~0. Concretely: with `w_phone` dropped,
Qwen2.5-Coder-3B still emitted `+31%20(0)%2015%207814226` and every other field still
followed its wrong hint. The entry looked harmless because its neighbours were doing its
job. RESULTS.md called this "store B floors", which was the wrong mechanism.

**Fault 2 — the task design, not the store design.** Every v2 field used an arbitrary
convention no model can guess, so hint-free accuracy was ~0 everywhere. **A wrong hint
cannot damage behaviour that was already wrong.** No arrangement of the store could have
fixed this; it needed different tasks.

A related measurement error came out of the same investigation: the "what the model already
believes" baselines reported in RESULTS.md were measured as `A:loo:c_X`, which still
contains five *other* correct hints. The 3B's phone accuracy is 0.96 in that context and
0.00 with no hints at all. Those numbers describe behaviour-in-context, not a default.

## What v3 changes

1. **Mixed stores.** `M1` and `M2` give each field exactly one hint, with correct/wrong
   alternating and complementary between the two stores. No coherent global stance can form.
2. **A hint-free `none` condition** (distractors only) per store, enabling an ABSOLUTE
   effect — `score(full) − score(none)` — alongside the LOO effect. This is the measure
   that is immune to fault 1.
3. **OBVIOUS vs ARBITRARY fields.** Three fields (`iban`, `zip`, `state`) use transforms a
   model performs unprompted, so hint-free accuracy is high and a wrong hint has something
   to destroy. Three (`dob`, `amount`, `code`) remain arbitrary.

## Evidence it works

**ABS and LOO disagree in sign, and ABS is right.** On the 3B, `w_dob` measured LOO
**+0.33** and ABS **−0.50** — the LOO measure called a harmful entry helpful, exactly the
fault-1 failure. This is the capability v2 lacked entirely.

**Negatives are now produced.** Smoke runs show `w_zip` at −0.88 and `w_state` at −0.38 in
one sample, `w_zip` at −0.10 in another. v2 produced zero, structurally, in 5200
generations across four backbones.

## Why the fix is partial

A wrong entry can only measure negative where **both** conditions hold: the field's
hint-free accuracy is high, *and* the wrong hint actually overrides that default. The
second does not always follow from the first.

`w_iban` measures **+0.00** against a hint-free baseline of **1.00** — the model strips the
spacing regardless of a hint telling it the spacing is significant. **Models resist
implausible instructions about obvious transforms.** That is a real finding rather than an
instrument defect, but it does mean negative-capable entries are scarcer than the design
intended.

Smoke coverage was 2/12 entries negative in one sample and 1/12 in another, at n=8–10.
That variance is itself a warning: coverage must be measured at n=50 before any conclusion
rests on it.

## Honest limits

- **Not validated at scale.** All of the above is n=8–10 on one backbone.
- **Thin coverage means a weak sign-flip test.** If only one or two entries can express a
  negative, "no sign flips across backbones" remains weak evidence — the original
  limitation is reduced, not removed.
- **`state` is unstable**: hint-free 0.38 in one sample, 0.00 in another. It may not belong
  in the OBVIOUS set.
- v2's A/B stores are deliberately **not** retained. Their entry ids referenced fields that
  no longer exist, and keeping the names alive would have run a different experiment under
  an old label. v2 is reproducible at commit `dc15ee7`.

## Coverage check at n=50 — GATE FAILED

Run 2026-08-28, Qwen2.5-Coder-3B, 1296 generations. Pre-registered gate: >=3 of 12 entries
expressing a negative ABS effect. **Result: 1/12.** Not proceeding to E2/E3.

| | |
|---|---|
| entries with negative ABS effect | **1/12** (`w_zip`, -0.20) — needed >=3 |
| LOO/ABS magnitude disagreement >0.05 | 3/12 |
| LOO/ABS **sign** disagreement | 1/12 |

Hint-free baselines came out as designed for two of three OBVIOUS fields — `iban` 1.00,
`zip` 1.00 — so the premise held. `state` did not (0.02); the 3B does not uppercase a
two-letter code unprompted, and it does not belong in the OBVIOUS set.

**The blocking problem is not the baselines, it is that the wrong hints do not bite.**
`w_iban` measures **+0.00 against a hint-free baseline of 1.00**: told the group spacing is
significant, the model strips it anyway. Same at smoke scale, so this is stable.

The two requirements for a measurable negative are in tension:

- the model's unaided default must be **right** (so there is something to destroy), and
- a wrong hint must **override** that default.

A model confident enough to get something right unprompted is generally confident enough to
ignore an instruction contradicting it. That is a finding, not only an obstacle: **models
resist implausible instructions precisely where they are competent.**

### What that implies about the wider claim

Our wrong hints are *implausible* — they contradict a transform the model performs
confidently. Real negative transfer, of the kind 2605.23899 measures at 25% of
extractor-target pairs (47% on ALFWorld), most likely comes from *plausible but wrong*
entries: content the model has no grounds to reject. Those are different mechanisms, and
this instrument only probes the first.

**Any v4 should make wrong entries plausible rather than contradictory** — e.g. a convention
that is correct for a neighbouring field, or right for most records and wrong for a subset.
That is a third instrument rebuild and should not be started without deciding it is worth it.

### What survived

The LOO/ABS disagreement is real and measured: 3 of 12 entries diverge by >0.05, one by
**0.72** (`w_state`: LOO -0.74, ABS -0.02), and `w_dob` disagrees in sign (LOO -0.04, ABS
+0.14). That is direct evidence for non-additivity — claim A of
[PAPER-PLAN.md](../../docs/PAPER-PLAN.md) — independent of whether negatives are expressible.
It is thinner than the plan assumed, and it cannot carry E3, which needs enough
negative-capable entries for independent gating to visibly mis-select.
