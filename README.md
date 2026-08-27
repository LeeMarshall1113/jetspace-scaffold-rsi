# jetspace-scaffold-rsi

Research on **scaffold-level recursive self-improvement**: loops that improve an agent's
scaffolding — prompts, memory, skills, control flow, curation policy — rather than its weights.

Opened 2026-08-27. Field map current through arXiv 2608.

---

## Thesis

The field has two ICLR 2026 orals, a dedicated benchmark, and a dense literature. It does not
have a single demonstration that a self-improving scaffold produced **capability the base model
did not already have**. Every measured gain to date is consistent with recovering engineering
slack.

Supporting evidence, three independent sources:

- Scaffold edits that survive selection concentrate on parsing, retries, dispatch and answer
  extraction, and "rarely deliver domain-specific reasoning that the base model could not
  produce given any prompt."
- RHI's own ablation: gains "arise primarily from improved task-specific context management
  ... rather than longer reasoning traces."
- STOP degraded outright on weaker models (GPT-3.5, Mixtral).

No published experiment separates slack-recovery from capability-creation. That experiment is
the spine of this repo.

## Program

Four falsifiable claims. Each stands alone as a publishable finding, including negative.

| | Claim | Predicted |
|---|---|---|
| **C1** | Offline scaffold evolution cannot beat its own model's slack-free ceiling | true |
| **C2** | Intra-episodic scaffold adaptation crosses it, because the knowledge is genuinely absent | true |
| **C3** | Entries carrying a per-backbone attested effect size transfer positively; unattested ones reproduce EvoAgentBench's negative cells | mechanism contribution |
| **C4** | Optimising the curator closes most of the hand-curation gap | measurable headroom |

Full protocols, kill conditions and prior art in [docs/PROGRAM.md](docs/PROGRAM.md).

## Testbeds

Two benchmarks, each doing the job it is actually suited for.

**C1 / C2 — [BoxingGym](https://arxiv.org/abs/2501.01540)** (NeurIPS 2025). Ten environments for
automated experimental design and model discovery. The agent proposes a model of a hidden
system, designs experiments, observes outcomes, and revises.

Why it fits, point by point against what C2 needs:

| Requirement | How BoxingGym satisfies it |
|---|---|
| Required knowledge genuinely absent from weights | the hidden system's parameters are sampled per instance — absent by construction, not by argument |
| Contamination-free | re-randomise the instance; no appeal to "these games are novel" needed |
| Write–use–validate fits inside one run | native to the environment — propose, experiment, compare, revise *is* the task loop |
| Efficiency metric that moves before success | data-efficiency, i.e. experiments-to-convergence, which is exactly C2's predicted early signal |
| A published bar to clear | GPT-4o struggles (original paper); [Model Discovery Agent](https://arxiv.org/abs/2608.09696) (2608.09696) is Aug 2026 SOTA |

One free property worth noting: BoxingGym's discovery metric asks whether *another* agent can
predict correctly from your agent's explanation. That is C3's transfer question already built
into the benchmark.

**C3 / C4 — [EvoAgentBench](https://arxiv.org/pdf/2607.05202)** (2607.05202). The transfer and
curation claims need task volume, multiple backbones, and a published comparison table — all
three are what this benchmark exists to provide. Report on their axis and compare directly
against their per-cell numbers, including the Anchor Skill gap C4 is trying to close.

Rejected: ARC-AGI-3 (competition-shaped, offline-model constraint, and the contamination
argument is weaker than "we resampled the instance"); Agent Island (adversarial and
winner-take-all, so the fixed ceiling C1 needs does not exist).

## Why this angle

Everything in the RSI literature is measured on SWE-bench, Polyglot, AppWorld, GAIA,
WebWalkerQA, LiveCodeBench — static distributions, contamination risk, large engineering slack.
**No scaffold-RSI paper works in a setting where the required knowledge is provably absent from
the model.** That is the opening: the mechanism is contestable, the measurement is not.

## Layout

```
docs/         thesis, field map, program, open questions
research/     paper notes; PDFs gitignored
harness/      scaffold + attested-context implementation
experiments/  run configs and results
```

## Status

| | |
|---|---|
| Phase | literature complete, program drafted, nothing built |
| Blocking | Q1 — can a strong model prior substitute for experimentation on BoxingGym? (gates C2) · Q2 — are per-entry effect sizes actually model-conditional? (gates C3) |
| Next | Q1 and Q2. Both cheap, both can kill a claim, neither needs code written first. |

## Reading

Start with [docs/LITERATURE.md](docs/LITERATURE.md). Ten papers in argument order at the bottom.

Field map as a rendered page: https://claude.ai/code/artifact/c8faf4bb-507f-487f-a163-048c26310e3a

---

## A note on this README

This README — and the files under `docs/` — were drafted by an AI assistant (Claude), and will
stay that way until a human wants to rewrite them. The research direction, the constraints, and
the calls about what to pursue are the maintainer's. The prose and the literature sweep are not.

Saying so plainly seems better than letting you work it out from the em-dashes.

**If you'd like to rewrite any of it in your own voice, please do — that would be genuinely
welcome.** A PR or an issue is plenty; no need to ask first. The parts most worth a human pass
are the thesis framing above and the claim map in `docs/LITERATURE.md`, where the judgement
calls are load-bearing and deserve someone willing to argue with them.
