# Open questions

Blocking items first. Q1 and Q2 each gate a claim, are cheap to answer, and require building
nothing. Answer both before writing code.

---

## Q1 — Can a strong parametric prior substitute for experimentation on BoxingGym?

**Gates** C2, which is the positive result of the whole program.

C2 rests on the required knowledge being absent from the weights *by construction*. BoxingGym
samples the hidden system's parameters per instance, which makes the parameters absent — but the
model *families* are recognisable (psychophysics, discounting, population dynamics and so on),
and a model with a strong prior over those families might reach a good posterior without doing
much real experimentation. If so, the knowledge was not as absent as claimed, C1's ceiling
swallows C2, and the cleanest environment in the design stops being clean.

**How to answer.** Give a frontier model the environment description and *no experimental access*,
ask for its best parameter estimate, and compare to the estimate after a full experimental budget.
The gap is the headroom C2 has to work in. Do this across all ten environments — the answer will
vary by environment, and the subset with a large gap is the working set.

**Weak prior evidence:** the original paper reports that augmenting an LLM agent with an explicit
statistical model does not reliably improve results, which suggests priors are not doing all the
work. Not the same measurement, though.

**Fallback if negative.** Construct the hidden system from a family the model has no prior over —
randomly generated functional forms, or a composed system whose structure is sampled rather than
named. Costs external validity, buys the absence guarantee back.

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
sizes rather than the mean. The claim needs variance across backbones at the entry level. Cheap
tasks are fine — this is a variance question, not a performance question.

**Status:** unanswered.

---

## Q3 — Does the ceiling protocol survive contact with reviewers?

C1's "slack-free ceiling" is the program's main exposure. An oracle harness is a judgement call
and best-of-N at maximum reasoning effort is a proxy for unbounded effort. Worth drafting the
protocol early and showing it to someone adversarial before spending compute on it — a
pre-registration that does not hold up is cheaper to discover now than after the runs.

**Status:** protocol not drafted.

---

## Q4 — Budget and model access

The design no longer needs local models, which was an artefact of the rejected ARC-AGI-3 testbed.
Both testbeds are inference-heavy and GPU-light: BoxingGym environments are statistical
simulators, and EvoAgentBench is API-driven. The binding constraint is API spend, not the local
box.

Undecided: which backbones to run for C3's cross-model comparison. EvoAgentBench used Qwen3.5-27B,
Qwen3.5-397B and Gemma-4-31B as evaluation backbones — matching them makes the comparison direct
but costs more than picking cheaper models and forfeiting the head-to-head table.

**Status:** undecided.

---

## Q5 — Where does this get submitted?

The four claims do not have to land as one paper. C1 alone is a short, sharp negative result. C1
plus C2 is the full slack-versus-capability story and the strongest single submission. C3 and C4
are a methods paper that stands on its own.

Worth deciding early, because it changes how much of the mechanism has to be built before there
is anything publishable.

**Status:** undecided.
