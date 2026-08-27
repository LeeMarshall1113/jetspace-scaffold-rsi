# Open questions

Blocking items first. Q1 and Q2 each gate a claim, are cheap to answer, and require building
nothing. Answer both before writing code.

---

## Q1 — Does the per-game action budget permit a write–use–validate cycle inside one run?

**Gates** C2, which is the positive result of the whole program.

C2 requires the agent to write a hypothesis about game mechanics, act on it, observe the
transition, and revise — all within a single run's action budget. If the budget is tight enough
that this cycle costs a meaningful fraction of the run, intra-episodic adaptation cannot express
itself and the claim has no room.

**How to answer.** Read the ARC-AGI-3 action cap per game from the competition docs, then
instrument the existing `../Arc-Prize` harness to count the minimum actions a single
write–use–validate cycle costs on `ft09` / `ls20` / `vc33`. Compare.

**Status:** unanswered.

---

## Q2 — Are per-entry effect sizes actually model-conditional?

**Gates** C3, and specifically whether read-time gating buys anything.

The case *for* model-conditionality is EvoAgentBench: every automatic method has at least one
negative transfer cell, with Memento hitting −36.3, across backbones held disjoint from the
construction backbones. The case *against* is AttriMem: learned memory transferred across answer
models with drops of only 2.07 / 1.25 / 2.31 points.

These are not obviously contradictory — AttriMem measures aggregate accuracy on QA-shaped
benchmarks, EvoAgentBench measures per-domain transfer gain on long-horizon agentic tasks — but
the resolution determines whether C3 has a mechanism or is a wrapper around C4.

**How to answer.** Take a small context store built on one backbone, evaluate it entry-by-entry
on two others via leave-one-out ablation, and look at the *distribution* of per-entry effect
sizes rather than the mean. The claim needs variance across backbones at the entry level.
Cheap tasks are fine — this is a variance question, not a performance question.

**Status:** unanswered.

---

## Q3 — Workspace and compute plan

Related work lives in two sibling repos:

- `../Arc-Prize` — existing ARC-AGI-3 system and harness. The asset this program is built on.
- `../arc-agi-2` — ARC-AGI-2 Kaggle campaign, active.

Undecided: whether the ARC-AGI-3 harness work happens here or in `Arc-Prize`, and how compute is
split. The local box is an RX 9070 XT (16GB, gfx1201, ROCm) with known constraints from the
ARC-AGI-2 campaign; Kaggle GPU quota is shared at 30h/week.

Note the shape of the cost differs from the ARC-AGI-2 campaign: scaffold-RSI experiments are
inference-heavy rather than training-heavy, which fits the available hardware better — but the
Kaggle track's offline constraint means the base model must run locally, which puts a hard
ceiling on model size.

**Status:** undecided.

---

## Q4 — Scheduling against the ARC-AGI-2 campaign

ARC-AGI-3 Milestone #2 is **2026-09-30** ($25K / $10K / $2.5K, open-sourcing required for
eligibility). The ARC-AGI-2 entry window is 10-26 / final 11-02, with the ARC Prize paper track
due 11-08.

These overlap. Committing to a Milestone #2 submission is a real trade against ARC-AGI-2
preparation, not an addition to it.

**Status:** undecided.

---

## Q5 — Does the ceiling protocol survive contact with reviewers?

C1's "slack-free ceiling" is the program's main exposure. An oracle harness is a judgement call
and best-of-N at maximum reasoning effort is a proxy for unbounded effort. Worth drafting the
protocol early and showing it to someone adversarial before spending compute on it — a
pre-registration that does not hold up is cheaper to discover now than after the runs.

**Status:** protocol not drafted.
