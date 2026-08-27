# Open questions

Q2 first: cheap, needs no infrastructure, and decides whether C3 is a mechanism or a wrapper.

---

## Q1 — Is the required knowledge absent by construction? (per testbed)

**Gates** C2.

**BoxingGym: ANSWERED, NO.** Structure fixed and textbook-nameable across all ten environments;
only 3–6 continuous parameters redrawn per instance from narrow priors centred on published fitted
values. The harness ships the prior-only ablation (`Error@0`) and it settles it — six of thirteen
goals get *worse* with ten experiments, three more move by ≤0.04σ. Dugongs beats the normalisation
baseline at zero observations. Retained as a negative control instead.

**NEURONBENCH: PENDING, promising.** Its six mystery neurons use membrane mechanisms "designed in
order to prevent the LLM from simply recalling the model from memory" — the authors built it
against exactly this failure mode. Still needs the same prior-only measurement run against it
before trusting the property. Open sub-question: are six worlds enough for statistics?

**DiscoverPhysics: PENDING, needs work.** Authors concede the 22 worlds are "deliberately curated
rather than genuinely novel." But the simulator accepts arbitrary force laws, so a procedural
generator would make the property hold by construction. Scope that work.

**Method for any new testbed:** give a frontier model the environment description with no
experimental access, ask for its best estimate, compare to the full-budget estimate. The gap is
the headroom C2 has to work in. Do it per environment — the answer varies, and the subset with a
large gap is the working set.

---

## Q2 — Are per-entry effect sizes actually model-conditional?

**Gates** C3, specifically whether read-time gating buys anything.

*For:* EvoAgentBench — 17 negative cells, worst −36.3, across backbones held disjoint from the
construction backbones. And the structural pattern: OpenClaw carries 12 of 17 (71%) despite having
26 tools to Nanobot's 7.

*Against:* AttriMem — learned memory transferred across answer models with drops of only
2.07 / 1.25 / 2.31 points.

Not obviously contradictory (AttriMem measures aggregate accuracy on QA-shaped benchmarks;
EvoAgentBench measures per-domain transfer on long-horizon agentic tasks), but the resolution
decides whether C3 has a mechanism.

**How to answer.** Build a small context store on one backbone, evaluate it entry-by-entry on two
others via leave-one-out ablation, and look at the *distribution* of per-entry effect sizes rather
than the mean. The claim needs variance across backbones at the entry level. Cheap tasks are fine
— this is a variance question, not a performance question.

**Note:** AttriMem's code is unreleased ("upon acceptance"), so their attribution machinery cannot
be reused. Leave-one-out is sufficient for a variance question.

**Status:** unanswered. Do this first.

---

## Q3 — Compute for the C3/C4 measurement

**Deferred, by recommendation.**

EvoAgentBench is a GPU-infrastructure project: open-weight backbones self-hosted via vLLM (repo
ships a Qwen3.5-397B-A17B-GPTQ-Int4 config), per-instance Docker images for SWE-bench Verified, a
FAISS-served corpus for BrowseComp-Plus. Roughly 24,000 agent rollouts for evaluation plus ~9,500
for evolution-state construction. Smallest evaluation backbone is 27B — out of reach on a 16GB
card.

Partial relief: the paper's published numbers are static and citable, so a new method needs only
its own runs; Memento / ReasoningBank / GEPA / Anchor need not be rerun. A clean baseline still
wants a Vanilla rerun.

Harder blocker: **the curator was never released.** Full repo tree search returns zero hits for
"ability", "graph", "anchor", "memento", "reasoningbank", "gepa". The extraction, canonicalisation
and graph-construction pipeline — and Anchor's routing labels — are absent. Rebuilding it is its
own sub-project, and any "gap recovered" claim would be against that reconstruction unless it is
first validated against the published Anchor numbers.

**Recommendation:** do C2 on NEURONBENCH first. Rent hardware only once there is a result worth
measuring transfer on.

**Trap:** the HF dataset card describes five domains including a phantom "OmniMath" split absent
from both the paper and the repo, and its default `configs:` block points at that unused split.
GitHub is authoritative.

---

## Q4 — Does the composite ceiling protocol survive review?

C1's exposure. An oracle harness is a judgement call; best-of-N at maximum reasoning effort is a
proxy for unbounded effort. Draft the protocol early and show it to someone adversarial before
spending compute. Pre-register it.

State the pass@N estimator explicitly — "Beyond Pass@k" (2608.14711) finds implementations
routinely set n to the number of unit tests rather than independent rollouts, inflating scores by
0.85–0.97 absolute.

**Status:** protocol not drafted.

---

## Q5 — Where does this get submitted?

C1 alone is a short negative-result / replication paper. C1+C2 is the full story and the strongest
single submission. C3 is a methods paper that stands alone, and its safety framing may suit a
different venue than its capability framing.

Decide early — it changes how much mechanism must be built before there is anything publishable.

**Status:** undecided.
