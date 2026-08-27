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

## Testbed

**ARC-AGI-3.** The only mainstream benchmark whose properties match what C1–C2 need: no
natural-language instructions, uncontaminated private games, and a scoring metric that is
skill-acquisition *efficiency* (levels completed, total actions as tiebreaker) — exactly the
quantity C2 predicts moves first.

Load-bearing constraint: **no internet during Kaggle evaluation.** API models cannot be relied
on. The competition track is a local-model regime, which makes C1's effect larger and puts it
in direct tension with STOP's negative result. Resolving that tension cleanly is a paper.

Existing assets: ARC-AGI-3 harness in `../Arc-Prize`, ARC-AGI-2 campaign in `../arc-agi-2`.

## Why this angle

Everything in the RSI literature is measured on SWE-bench, Polyglot, AppWorld, GAIA,
WebWalkerQA, LiveCodeBench — static distributions, contamination risk, large engineering slack.
**No scaffold-RSI paper uses an interactive-novelty environment.** That is the defensible
position here: the idea is contestable, the testbed is not.

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
| Blocking | per-game action budget unverified (gates C2); workspace/compute plan undecided |
| Next | verify action budget permits a write–use–validate cycle inside one run |

## Calendar

- **2026-09-30** — ARC-AGI-3 Milestone #2. $25K / $10K / $2.5K. Open-sourcing required for
  eligibility. Overlaps the ARC-AGI-2 entry window (10-26 entry, 11-02 final). Scheduling
  decision, not a free addition.

## Reading

Start with [docs/LITERATURE.md](docs/LITERATURE.md). Ten papers in argument order at the bottom.

Field map as a rendered page: https://claude.ai/code/artifact/c8faf4bb-507f-487f-a163-048c26310e3a
