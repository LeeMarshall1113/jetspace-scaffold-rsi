# jetspace-scaffold-rsi

Does the way self-evolving agents decide **what context to keep** accumulate error across
generations? An entry's value is a property of the store rather than the entry, and these
systems evaluate entries one at a time — so the selection error is made every generation, and
should compound silently.

Target: [docs/PAPER-PLAN.md](docs/PAPER-PLAN.md). Measured so far: the mechanism below.

Opened 2026-08-27.

---

## The result

**Context entries change a model's accuracy on fields they never mention.**

Remove the only entry targeting a field, leaving five hints about *other* fields plus six
topically-irrelevant distractors. Those non-mentioning entries still move it, hard:

| field | no hints | other-field hints only | full store |
|---|---|---|---|
| `state` | 0.02 | **0.74** | 0.00 |
| `dob` | 0.48 | **0.00** | 1.00 |

**+0.72** and **−0.48** from entries with no reference to the field — larger than most of the
on-target effects being measured.

This makes independent per-entry validation unsound, and that is the protocol published
systems use. SkillGen (2605.10999) gates one skill at a time; SkillOpt (2605.23904) accepts
an edit only on a strict score improvement; strong-to-weak harness construction (2608.12307)
refines one bundled object. Concretely: an entry stating a false convention measures **−0.02**
evaluated alone — indistinguishable from noise, so a gate keeps it — and costs **−0.74** in
the store it actually deploys into, because the other entries would have carried that field
and it blocks them. The error runs both ways: another entry is worth +0.52 alone and +1.00 in
context.

Write-up: **[docs/NOTE-off-target-effects.md](docs/NOTE-off-target-effects.md)**.
Limitations there are load-bearing and worth reading before citing anything.

## Status

| | |
|---|---|
| Result | measured on Qwen2.5-Coder-3B; replication on three further backbones **in progress** |
| Data | 6,700+ committed generations, four backbones, two lineages, all greedy (exact, not sampled) |
| Instrument | v3, working, with a known ceiling — see [INSTRUMENT-V3.md](experiments/q2_model_conditionality/INSTRUMENT-V3.md) |
| Not claimed | how much performance independent gating costs, or whether that cost compounds across generations. A pre-registered coverage gate failed 1/12 against a threshold of 3, so the experiments that would measure both are underpowered until the instrument is rebuilt. |

## Layout

```
docs/
  NOTE-off-target-effects.md   the result
  PAPER-PLAN.md                fuller plan; its headline experiment is gated out
  REVISIONS.md                 what was wrong and what replaced it
  LITERATURE.md                field map through arXiv 2608
  PROGRAM.md                   superseded four-claim programme, kept for the record
experiments/q2_model_conditionality/
  RESULTS.md                   four-backbone entry-value measurements
  INSTRUMENT-V3.md             instrument design, three rebuilds, and what still fails
  results/                     raw generations for every condition
```

## History

This began as a four-claim programme on scaffold-level recursive self-improvement. Occupancy
sweeps falsified or found published work occupying all of it — the composite-ceiling claim,
most of the intra-run claim, the strong form of the attestation claim, half the curation
claim, and a later big-model-teaches-small pivot. [REVISIONS.md](docs/REVISIONS.md) records
each one and what killed it, including a factual error of ours that was briefly live here.

The durable output turned out to be the measurement apparatus and the data, not the original
claims. That is why the repo is organised around a result rather than a plan.

## Reading order

1. [docs/NOTE-off-target-effects.md](docs/NOTE-off-target-effects.md) — the result and its limits
2. [experiments/.../RESULTS.md](experiments/q2_model_conditionality/RESULTS.md) — entry value across four backbones: it tracks neither scale, generation, nor lineage
3. [experiments/.../INSTRUMENT-V3.md](experiments/q2_model_conditionality/INSTRUMENT-V3.md) — why three instrument rebuilds, and what the current one still cannot express
4. [docs/LITERATURE.md](docs/LITERATURE.md) — field map, if you want the surrounding work

## Reproduce

```bash
cd experiments/q2_model_conditionality
python run_loo.py --model <path> --tag v3-<name> --limit 50 --batch 13 --max-new 160
python analyze.py --stores mixed v3-<name>
```

Greedy decoding throughout, so every difference is exact rather than a sample estimate. Raw
generations for every condition are committed under `results/`.

---

## A note on this README

This README — and the files under `docs/` — were drafted by an AI assistant (Claude), and will
stay that way until a human wants to rewrite them. The research direction, the constraints, and
the calls about what to pursue are the maintainer's. The prose and the literature sweep are not.

Saying so plainly seems better than letting you work it out from the em-dashes. It is also
load-bearing: an earlier revision of this file asserted that Model Discovery Agent was
state-of-the-art on BoxingGym. It is not, and never touched that benchmark. The error came from
an unverified search summary. [REVISIONS.md](docs/REVISIONS.md) logs it. Treat unsourced claims
here as provisional and check the arXiv IDs.

**If you'd like to rewrite any of it in your own voice, please do — that would be genuinely
welcome.** A PR or an issue is plenty; no need to ask first. The parts most worth a human pass
are the result framing above and the limitations in the note, where the judgement calls are
load-bearing and deserve someone willing to argue with them.

## License

[MIT](LICENSE). Contributions are accepted under the same terms.
