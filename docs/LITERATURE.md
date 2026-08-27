# Field map — scaffold-level RSI

Current through arXiv 2608 (August 2026). Sourced throughout; unverified inference is marked
*(inference)*. Claims that did not survive checking are in [REVISIONS.md](REVISIONS.md).

---

## 1. What "scaffold RSI" means — five levels

Ordered by what the loop is allowed to mutate.

| | Mutable object | Representative work | State |
|---|---|---|---|
| **L0** | nothing persists past the episode | Reflexion, Self-Refine | solved and bounded |
| **L1** | prompt / instruction text | Promptbreeder, DSPy/MIPROv2, TextGrad, GEPA, SePO | mature |
| **L2** | accumulated context, skills, memory | Voyager, ACE, Dynamic Cheatsheet, ReasoningBank, MemSkill, SelfMem | most crowded lane of 2026 |
| **L3** | agent/harness code and control flow | ADAS, AFlow, SICA, DGM, HGM, MOSS, SIA, RHI, HyperAgents | two ICLR 2026 orals |
| **L4** | the generator / evaluator / curator itself | MEGA, ERSkill, HGM (selection), Red Queen GM (evaluators) | occupied since mid-2026 |

The **timescale** axis is orthogonal and thinner: everything above is offline or inter-episodic.
Intra-run scaffold self-modification is the gap — see §5.

---

## 2. Lineage — two tracks converging mid-2026

**Track A — self-modifying agents (code, control flow)**

```
2003  Godel Machine ............... provably optimal self-rewriting; needs proof search; never ran
2023  STOP ........................ self-taught optimizer; DEGRADED under weaker models
2024  ADAS, AFlow ................. agents invented in code space; MCTS over workflow graphs
2025  DGM (2505.22954) ............ open-ended archive of self-rewriting agents
      HGM (2510.21614) ............ clade-level selection; metaproductivity != performance
2026  MOSS (2605.22794) ........... source-level rewriting on minimal scaffolds
      SIA (2605.27276) ............ harness + weight updates jointly
      CyberEvolver (2605.26195) ... beats seed pass@16 with fewer tokens
      Red Queen GM (2606.26294) ... evaluators co-evolved with agents
      RHI (2607.15524) ............ harness as prompt-level spec of the agent loop
```

**Track B — learned context (memory, skills, playbooks)**

```
2023  Voyager, Reflexion, Promptbreeder
2024  DSPy, TextGrad, Agent Workflow Memory
2025  GEPA (2507.19457) ........... reflective prompt evolution, Pareto genetic
      ACE  (2510.04618) ........... context as incrementally-updated playbook
2026  AttriMem (2607.21106) ....... per-entry ablation attribution -> process rewards
      MEGA (2608.10504) ........... evolves the curation strategies themselves
      ERSkill (2608.12720) ........ co-evolves retrieval router with skill set
      AutoMem  (2608.14621) ....... architecture search over 5x5x6x4 memory configs
```

**The instrument — EvoAgentBench (2607.05202), July 2026.** First to measure both tracks on one
axis: does the learned artifact transfer? Often negatively.

---

## 3. Results that bound the design

### 3.1 Scaffolds *do* cross ceilings — but weak ones

The claim that scaffold RSI only recovers slack is **false**. Three counterexamples:

| Paper | Result | Weakness of its ceiling |
|---|---|---|
| CyberEvolver (2605.26195) | beats seed pass@16 by 13.6% using 17.5% *fewer* tokens; argues explicitly that it "solves targets that lie beyond the unchanged scaffold's sampling ceiling" | ceiling is the *seed scaffold's*; expert baselines capped at pass@4 |
| RHI (2607.15524) | evolved harness on a low-effort agent beats the same model at max reasoning effort, up to 60% cheaper | same-family test-time scaling only; no BoN; no human oracle harness |
| HGM (2510.21614) | evolved agent beats SWE-agent, same backbone, matched budgets | strong human baseline, not an oracle; no BoN or effort control |

**The standard vocabulary is "elicitation gap"** (METR). 2606.08529 measures 28 points of it
within a single model and concludes capability numbers are "scaffold-conditional estimates." Also
relevant methodologically: 2604.02460 (single-agent beats multi-agent at equal thinking-token
budgets — "many reported advantages of MAS are better explained by unaccounted computation"),
2606.31511 (placebo-controlled decomposition), 2607.26117 (blind resampling beats self-repair at
2.5–5.5× fewer tokens).

**The exploitable flaw.** CyberEvolver justified its pass@4 cap with "pass@k saturates beyond k=4
for fixed scaffolds," generalising from its own seed agent's curve (+1.4%, k=4→16). Pass@(k,T)
analysis (2604.14877) shows saturation is task-dependent: on compositional multi-step tasks the
gap *widens* at the right tail and orderings **flip near k=4** (pass@(64,5): RL 0.81, base 0.77).
CTF targets are compositional multi-step tasks. Supporting: Kevin (2507.11948), R2E-Gym
(2504.07164).

**Best headroom precedent — ReCreate (2601.11100), Appendix F.** Five human-designed scaffolds,
one fixed base model, SWE-bench Lite: union 184, best single 147, **37 issues (20% of union)
scaffold-fixable**. Clean, non-saturated, under-claimed, unbuilt-upon.

*Do not* use CORE-Bench (2606.26158) "oracle router = 100%" as a headroom number — near-saturated
benchmark, headroom 10.3 pts for Opus 4.5 vs 2.6 for GPT-5.4. Its useful finding is different:
outcomes **disagreed on 31% of tasks at near-identical means** — scaffolds route the model to
different solvable regions.

**Estimator hygiene:** "Beyond Pass@k" (2608.14711) — implementations routinely set n to the
number of unit tests rather than independent rollouts, inflating scores 0.85–0.97 absolute.

### 3.2 Learned context has a sign, and nobody ships it

EvoAgentBench: 528 train / 267 test tasks, four domains, construction backbones (Kimi-K2.5,
GLM-5.1, DeepSeek-V3.2) disjoint from evaluation backbones (Qwen3.5-27B, Qwen3.5-397B,
Gemma-4-31B). Metric `Δ_m = mean(r_m(x) − r_0(x))`.

| Method | Qwen3.5-27B | Qwen3.5-397B | Gemma-4-31B |
|---|---|---|---|
| **Anchor Skill** (oracle routing — see below) | +7.5 | +10.5 | +5.8 |
| Memento | −2.4 | +1.5 | −0.7 |
| ReasoningBank | +3.6 | +2.4 | +0.4 |
| GEPA | +1.2 | +3.5 | +5.7 |

Seventeen negative cells, worst **−36.3**. The structural pattern is the useful part:

- **By scaffold:** OpenClaw carries **12 of 17 (71%)** despite 26 tools to Nanobot's 7. More
  scaffold surface correlated with *more* negative transfer.
- **By domain:** knowledge work 7/18, SWE 6/18, algorithmic 3/18, web research 1/18.
- **By backbone:** Gemma-4-31B worst (7/17), Gemma+OpenClaw the single worst pairing.

*(Domain/scaffold breakdown derived from the per-cell table, not stated by the authors.)*

**Anchor Skill is an oracle on routing.** Content is clean — built exclusively from train-side
cards. But it retrieves by curator-side Ability labels computed offline using the test task's own
ground-truth answer and traces. The paper: "Anchor Skill is not a deployable method." Its numbers
are an oracle-routing ceiling, not a reachable target. The paper's §4.2 subhead — "The gap
implicates method-side extraction and routing" — hands over the diagnosis and stops.

**Caveat on all absolute Δ:** test tasks were preferentially sampled where construction backbones
left headroom, so magnitudes are split-specific, not generic estimates.

### 3.3 Unattested accumulation is exploitable and irreversible

The strongest argument for gating is not capability, it is safety.

- Skill backdoors via poisoned trajectories: **56–89%** attack success (2608.03509)
- Trajectory poisoning in self-evolving skill systems: **91%** (2608.05563)
- Individually-safe experiences composing into unsafe behaviour (2608.01759)
- Indirect bias injection into agent memory (2608.22061)
- **"When Self-Evolution Backfires" (2608.05810)** — capability-contamination phase transition;
  bad skill admission is **structurally irreversible post-hoc**, so pre-commit gating is necessary

### 3.4 Selection — a branch's score barely predicts what it produces

HGM's **Metaproductivity-Performance Mismatch**: benchmark score correlates weakly with a
lineage's potential to generate better descendants. Clade Metaproductivity (CMP) aggregates
descendants' performance to decide which subtrees to expand, reaching human-level coding-agent
performance at far fewer CPU-hours than DGM. Applied only to *code* lineages.

### 3.5 Gains often are not real

- **"Do Agent Optimizers Compound?" (2607.14004)** — GEPA's gains regress on new tasks; only
  regression-controlled optimizers compound.
- **PAST-Bench (2608.04003)** — isolates whether a gain is supported by evidence of the intended
  pathway. 26 scenarios, 204 episodes, on/off conditions. **Reusable instrument.**
- **"On the Fragility of Self-Improving Agents" (2608.18066)** — noise and task-order produce
  illusory gains.
- **"Self-Authored Verification Is Unreliable" (2607.24300)**, **"Phantom Guardrails"
  (2607.13083)** — self-improving harnesses invent fixes for failures that do not exist.
- **"Demystifying Agent Skills" (2608.14036)**, 8,135 trials — skills act as procedural anchors
  (65.7%) not knowledge injection (4.5%); retrieval precision collapses **29.6% → 3.3%** as the
  pool grows.

---

## 4. Claim map

### Claimed — do not re-derive

| Territory | Held by |
|---|---|
| Agent code self-rewriting | DGM, HGM, SICA, MOSS, SIA, HyperAgents |
| Memory architecture search | AutoMem (2608.14621), SelfMem, EvolveMem, MemSkill |
| Per-entry credit assignment | AttriMem, TreeMem, Memory-R2 |
| Prompt/harness spec evolution | GEPA, SePO, RHI, Self-Harness, Meta-Harness, AHE |
| **Curator/router as RSI target** | **MEGA (2608.10504), ERSkill (2608.12720)** |
| Inter-episodic test-time harness adaptation | TTHE (2607.08124), JIT-Agent (2608.25593), HELIX (2608.13951), Recuris (2608.24876) |
| Within-run hypothesis→act→validate→revise | Model Discovery Agent (2608.09696) — but with a **fixed, hand-built** Bayesian meta-controller |

### Contested

| Territory | Held by | Why still open |
|---|---|---|
| Evaluator co-evolution | Red Queen GM (2606.26294) | names its own unsolved problems: convergence stability, evaluator corruption, scaling |

### Open

1. **Intra-run scaffold self-modification.** MDA does within-run adaptation but never lets the
   agent rewrite the accumulator. The four inter-episodic near-misses were quote-checked. → **C2**
2. **Utility under transfer.** Attribution stays inside one system; portability moves bytes without
   checking utility. Nothing conditions effect size on the target model. → **C3**
3. **Entry retirement.** AttriMem explicitly does not address it. One governance-primitive paper
   (2604.12007), no integration with any RSI loop.
4. **Clade metaproductivity for non-code artifacts.** Zero hits across every search. → **C4**
5. **The composite ceiling.** Four axes exist separately; nobody conjoins them. → **C1**

---

## 5. Testbeds

C2 needs knowledge absent **by construction**. That eliminates almost everything.

| | Verdict |
|---|---|
| **NEURONBENCH** ([repo](https://github.com/murphyk/neuronbench), in 2608.09696) | **Primary.** Six mystery neurons with membrane mechanisms "designed in order to prevent the LLM from simply recalling the model from memory." MIT, active. Limit: six worlds; SOTA published. |
| **DiscoverPhysics** (2605.26087, [repo](https://github.com/SampsonML/DiscoverPhysics)) | **Scalable second.** 22 worlds, 11 private; authors concede "deliberately curated rather than genuinely novel." **The simulator accepts arbitrary force laws** — a procedural generator makes the property hold by construction. Best pass@5 ~73%. |
| **BoxingGym** (2501.01540) | **Negative control.** Structure fixed and textbook-nameable; only 3–6 continuous parameters redrawn from narrow priors; domain named in-prompt under `include_prior`. Prior-only ablation (`Error@0`): six of thirteen goals get *worse* with ten experiments, three more move ≤0.04σ. Repo effectively unmaintained (12 stars, single squashed commit, July 2025) and ships broken configs. |
| **Agentic Automata Learning** (2606.16576) | Clean control. Procedurally sampled DFAs; equivalence queries return counterexamples. Thin scaffold, so little to adapt. |
| **EvoAgentBench** (2607.05202) | C3/C4 measurement, **deferred** — GPU-infrastructure project, 27B floor, curator unreleased. |

**Rejected with measurements:** Cybench / NYU CTF — contamination is measured, not hypothetical
(NYU CTF 14.4% vs 6.3% on live unreleased challenges, ~2.3× inflation, 71 cheating instances,
CTFusion 2605.11504). DiscoveryBench — targets are published findings, and its headline 25% is
Reflexion with oracle feedback injected mid-run. ScienceAgentBench — execution feedback only.
Agent Island (2605.04312) — transparent rules, no hidden system. ARC-AGI-3 — competition-shaped,
offline-model constraint; contamination argument weaker than resampling. NetHack / TextWorld —
semantics heavily represented in pretraining.

---

## 6. Implementation

**Base: fork [`metauto-ai/HGM`](https://github.com/metauto-ai/HGM)** — Apache-2.0, built on DGM's
codebase, ICLR 2026 oral, already wired to SWE-bench/Polyglot. It *is* the CMP implementation, so
C4 extends it rather than reimplementing it.

Alternative assembly: [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve)
(MAP-Elites archive with real lineage, benchmark-agnostic evaluator) +
[`gepa-ai/gepa`](https://github.com/gepa-ai/gepa) for prompt mutation + ACE's
Generator/Reflector/Curator pattern. OpenEvolve lacks CMP-style lineage selection.

**Build yourself:** the attested-entry schema. Nothing combines provenance + per-backbone effect
size + retirement condition with read-time gating. The schema is easy; **the retirement policy is
the research problem** — a bandit / credit-assignment design question.

**Steal, do not depend on:** ACE's inline `helpful=X harmful=Y` counters; memorywire's
quarantine-not-delete state machine and its thin `MemoryStore` interface.

**Traps.** `CerebrasResearch/gepa` is a dead fork — use `gepa-ai/gepa`. Letta wants to own the
agent loop and fights control-flow mutation. Zep's useful core is Graphiti; the rest is SaaS.
TextGrad is 13 months stale. DGM/ADAS/SICA are frozen 13–19 months. Two unrelated papers are named
AutoMem (2607.01224 vs 2608.14621). **DGM and HGM execute untrusted model-generated code as normal
operation — sandbox before running either.** Portable Agent Memory (2605.11032) has no locatable
code despite claiming a tested SDK; "Engram" names six or more unrelated projects with no shared
spec; AttriMem's code is unreleased.

---

## 7. Reading order

| arXiv | Paper | Why | Priority |
|---|---|---|---|
| 2605.26195 | CyberEvolver | the ceiling-crossing result to attack; read the pass@4 justification | first |
| 2607.15524 | Recursive Harness Self-Improvement | closest work to "scaffold RSI"; beats max-effort baselines | first |
| 2604.14877 | Pass@(k,T) Analysis | the rebuttal — saturation is task-dependent, orderings flip near k=4 | first |
| 2607.05202 | EvoAgentBench | negative-transfer table; read Appendix B's access matrix for Anchor | first |
| 2510.21614 | Huxley-Godel Machine | CMP, the metric C4 extends; also the codebase to fork | first |
| — | Weng, *Harness Engineering* (2026-07-04) | best bottleneck synthesis; observability taxonomy is reusable | first |
| 2608.09696 | Model Discovery Agent | what C2 must distinguish itself from; ships NEURONBENCH | second |
| 2601.11100 | ReCreate (Appendix F) | the 20% scaffold-fixable headroom figure | second |
| 2608.04003 | PAST-Bench | reusable instrument for "is this gain real" | second |
| 2608.05810 | When Self-Evolution Backfires | irreversibility of bad admission — C3's safety argument | second |
| 2608.14036 | Demystifying Agent Skills | 29.6%→3.3% retrieval collapse; skills as procedural anchors | second |
| 2606.08529 | Scaffold Effects on GAIA | elicitation-gap vocabulary and magnitude | third |
| 2608.10504 / 2608.12720 | MEGA / ERSkill | what occupies C4's first half | third |
| 2607.13104 | Self-Improvements survey | θ-vs-Σ taxonomy, citable related-work map | third |

**Curated lists:** VoltAgent and selfimproving-agent are current but thin. **EvoAgentX's
Awesome-Self-Evolving-Agents and Shichun-Liu's Agent-Memory-Paper-List are stale since ~January
2026** — do not rely on them for currency.

---

## 8. Motivating source outside the literature

Iury Souza, *Memory Portability: Owning Your AI Context* —
<https://iurysouza.dev/memory-portability-owning-your-ai-context/>

Argues accumulated context is the stickiest form of vendor lock-in. The engineering conclusion
taken here is narrower than the political one: if learned context is going to be portable,
**portability has to carry attestation**, or what gets exported is negative transfer — and, per
§3.3, poisoned skills. That is C3.
