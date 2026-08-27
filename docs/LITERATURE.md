# Field map — scaffold-level RSI

Current through arXiv 2608 (August 2026). Every claim here is sourced; unsourced inference is
marked *(inference)*.

---

## 1. What "scaffold RSI" means — five levels

Ordered by what the loop is allowed to mutate. The literature clusters at L1–L3; the
interesting failure lives at L4.

| | Mutable object | Representative work | State |
|---|---|---|---|
| **L0** | Nothing persists past the episode | Reflexion, Self-Refine | solved and bounded |
| **L1** | Prompt / instruction text | Promptbreeder, DSPy/MIPROv2, TextGrad, GEPA, SePO | mature |
| **L2** | Accumulated context, skills, memory | Voyager, ACE, Dynamic Cheatsheet, ReasoningBank, MemSkill, SelfMem | most crowded lane of 2026 |
| **L3** | Agent/harness code and control flow | ADAS, AFlow, SICA, DGM, HGM, MOSS, SIA, RHI, HyperAgents | two ICLR 2026 orals |
| **L4** | The generator/evaluator/curator itself | HGM (partially), Red Queen GM (partially) | **barely occupied** |

GEPA's sample-efficiency result — beating GRPO with ~35x fewer rollouts — is the field's
strongest argument that reflective natural-language optimisation beats RL at this level.

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
      Red Queen GM (2606.26294) ... evaluators co-evolved with agents
      RHI (2607.15524) ............ harness as prompt-level spec of the agent loop
```

**Track B — learned context (memory, skills, playbooks)**

```
2023  Voyager, Reflexion, Promptbreeder
2024  DSPy, TextGrad, Agent Workflow Memory
2025  GEPA (2507.19457) ........... reflective prompt evolution, Pareto genetic
      ACE  (2510.04618) ........... context as incrementally-updated playbook
2026  Portable Agent Memory (2605.11032), memorywire (2606.01138), Engram
      AttriMem (2607.21106) ....... per-entry ablation attribution -> process rewards
      AutoMem  (2608.14621) ....... architecture search over 5x5x6x4 memory configs
```

**The join — EvoAgentBench (2607.05202), July 2026.** First instrument to measure both tracks
on the same axis: does the learned artifact *transfer*? Answer: often negatively.

---

## 3. The three results that bound anything built here

### 3.1 Ceiling — scaffold edits land on hygiene, not reasoning

Across L3, the edits that survive selection are parsing, retries, dispatch, and answer
extraction, and "rarely deliver domain-specific reasoning that the base model could not produce
given any prompt." RHI's own analysis agrees: gains "arise primarily from improved task-specific
context management ... rather than longer reasoning traces." STOP degraded on GPT-3.5 and
Mixtral. Weng's synthesis: "harness improvement enables better deployment of the model but
intelligence is still the core."

**Consequence.** Every headline number in this field is compatible with a scaffold that merely
stops wasting the model's existing competence. Nothing published separates the two. → **C1**

### 3.2 Transfer — learned context has a sign, and nobody ships it

EvoAgentBench: 528 train / 267 test tasks, four domains (web research, algorithmic reasoning,
SWE, knowledge work). Construction backbones (Kimi-K2.5, GLM-5.1, DeepSeek-V3.2) held disjoint
from evaluation backbones (Qwen3.5-27B, Qwen3.5-397B, Gemma-4-31B). Metric is average transfer
gain `Δ_m = mean(r_m(x) − r_0(x))` over the test set.

| Method | Qwen3.5-27B | Qwen3.5-397B | Gemma-4-31B | Notes |
|---|---|---|---|---|
| **Anchor Skill** (hand-curated reference) | **+7.5** | **+10.5** | **+5.8** | positive in every domain |
| Memento | −2.4 | +1.5 | −0.7 | one cell at **−36.3** |
| GEPA | +1.2 | +3.5 | +5.7 | still has negative cells |
| ReasoningBank | +0.4 | — | +3.6 | six negative per-domain cells |

> Every automatic method exhibits negative transfer in at least one scaffold–backbone–domain
> setting.

Meanwhile the portability protocols verify that memory moved *faithfully* and never check
whether it *helped*. Portable Agent Memory's five-component model `M = (E,S,P,W,I)` —
episodic, semantic, procedural, working, identity — with Merkle-DAG provenance and
capability-scoped disclosure reports a Transfer Continuity Score of 0.83–0.92 vs 0.28–0.45
baseline. TCS measures **behavioural continuity, not task performance**, on a pilot of N=50.
The paper does not mention pruning, retirement, quality attestation, or effect size.

**Consequence.** Entry value is conditional on backbone and domain and can be sharply negative.
Portability without attestation is a mechanism for exporting negative transfer. → **C3**

### 3.3 Selection — a branch's score barely predicts what it produces

HGM names this the **Metaproductivity-Performance Mismatch**: an agent's benchmark score
correlates weakly with its potential to generate better descendants. High scorers become
evolutionary dead ends; mediocre ones found successful lineages. HGM's fix — Clade
Metaproductivity (CMP), aggregating descendants' performance to decide which subtrees to
expand — reaches human-level coding-agent performance at far fewer CPU-hours than DGM.

**Consequence.** Greedy hill-climbing on any scaffold artifact is mis-specified. Applied only to
*code* lineages so far. Nobody has asked what the clade of a *memory entry* is. → **C4**

---

## 4. Claim map — occupied vs open

### Claimed — do not re-derive

| Territory | Held by | Note |
|---|---|---|
| Agent code self-rewriting | DGM, HGM, SICA, MOSS, SIA, HyperAgents | two ICLR orals; entering means competing on their benchmarks |
| Memory architecture search | **AutoMem (2608.14621)** | 5 encoders x 5 stores x 6 retrievers x 4 managers; +2.8 pts, −14.3% tokens; landed this month |
| Per-entry credit assignment | AttriMem, TreeMem, Memory-R2 | ContextCite ablation -> process rewards under GRPO |
| Memory portability as transport | Portable Agent Memory, memorywire, Engram | solved as plumbing; cross-runtime interop demonstrated |
| Prompt/harness spec evolution | GEPA, SePO, RHI, Self-Harness, Meta-Harness, AHE | |

### Contested

| Territory | Held by | Why still open |
|---|---|---|
| Evaluator co-evolution | Red Queen GM (2606.26294) | names its own unsolved problems: convergence stability, evaluator corruption by the agents it scores, scaling past toy domains |

### Open — the four gaps that survive scrutiny

1. **Utility under transfer.** Attribution measures utility inside one system; portability moves
   bytes across systems. Nothing measures or optimises an entry's effect size *conditioned on
   the target model*, despite EvoAgentBench proving the sign flips. → C3
2. **Curation as the RSI target.** Largest measured headroom in the field: hand-curated +10.5
   and always positive vs automatic methods going negative on the same tasks. Everyone optimises
   artifact *content*; nobody optimises the curator and router that decide what loads. → C4
3. **Entry retirement.** AttriMem explicitly does not address it. PAM does not mention it.
   Accumulation is universal; principled forgetting has one governance-primitive paper
   (2604.12007) and no integration with any RSI loop.
4. **Environments where the knowledge is provably absent.** Everything above is measured on
   SWE-bench, Polyglot, AppWorld, GAIA, WebWalkerQA, LiveCodeBench — all of which the base model
   could in principle solve given a good enough prompt. No scaffold-RSI paper works in a setting
   where the required knowledge is absent from the weights *by construction*, so no result can
   distinguish slack recovery from capability creation. → C1/C2, and the reason the ceiling
   question is still open.

---

## 5. Testbeds

Two benchmarks, split by which claim they serve. The requirements are different enough that one
benchmark would do both jobs badly.

### 5.1 C1 / C2 — BoxingGym (2501.01540, NeurIPS 2025)

Ten environments for **automated experimental design and model discovery**. The agent proposes a
model of a hidden system, designs experiments to test it, observes outcomes, and revises.
Evaluation is two-part: standard prediction error, plus an explanation-based metric that asks
whether *another* agent can predict reliably given the first agent's stated model.

Why this is the right shape for the ceiling claim:

| C2 requires | BoxingGym provides |
|---|---|
| knowledge provably absent from weights | hidden-system parameters sampled per instance — absent by construction |
| contamination-free | resample the instance; no argument from novelty required |
| write–use–validate inside one run | propose → experiment → compare → revise *is* the task loop |
| efficiency signal before success signal | data-efficiency (experiments to convergence) |
| a published bar | GPT-4o struggles on both axes; Model Discovery Agent (2608.09696, Aug 2026) is current SOTA |

Two findings from the original paper that matter here. First, GPT-4o struggles with *both*
experimental design and model discovery — so there is real headroom, not a saturated benchmark.
Second, **augmenting the agent with an explicit statistical model does not reliably help** —
which is a direct precedent for C1's shape: adding machinery to the scaffold did not convert
into capability.

The explanation-based metric is a happy accident. It already measures whether a learned artifact
survives handoff to a different agent, which is the question C3 asks. *(inference)*

### 5.2 C3 / C4 — EvoAgentBench (2607.05202)

The transfer and curation claims need task volume, multiple backbones, and a published table to
compare against. EvoAgentBench is purpose-built for all three: 528 train / 267 test tasks across
four domains, construction backbones held disjoint from evaluation backbones, and per-cell
transfer gains already published for Memento, GEPA, ReasoningBank and the hand-curated Anchor
Skill reference (§3.2 above). C4's target — the Anchor Skill gap — is a number in their table.

### 5.3 Rejected, with reasons

| Candidate | Why not |
|---|---|
| **ARC-AGI-3** | Competition-shaped rather than experiment-shaped; the Kaggle track forbids internet at eval, forcing a local-model regime that constrains the design for reasons unrelated to the science. Contamination argument ("the private games are novel") is weaker than "we resampled the instance." |
| **Agent Island** (2605.04312) | Contamination- and saturation-resistant by construction, but adversarial and winner-take-all — the ceiling C1 measures against is not a fixed object when opponents adapt. |
| **SWE-bench / GAIA / AppWorld** | The default choices in this literature, and precisely the ones whose slack makes C1 unanswerable. |
| **NetHack / TextWorld** | Semantics are heavily represented in pretraining corpora; "knowledge absent from weights" fails. |

---

## 6. Reading order

| arXiv | Paper | Why | Priority |
|---|---|---|---|
| 2607.05202 | EvoAgentBench | negative-transfer numbers motivating C3/C4 — read the per-cell table, not the abstract | first |
| 2607.15524 | Recursive Harness Self-Improvement | closest existing work to "scaffold RSI"; its own ablation supports C1 | first |
| 2510.21614 | Huxley-Godel Machine | metaproductivity mismatch + clade metric — the correction C4 borrows | first |
| — | Weng, *Harness Engineering for Self-Improvement* (2026-07-04) | best synthesis of the bottleneck list; the observability taxonomy (component / experience / decision) is directly reusable | first |
| 2607.21106 | AttriMem | attribution machinery C3 extends; cross-model drops 2.07 / 1.25 / 2.31 test kill-condition #2 | second |
| 2608.14621 | AutoMem | newest occupier of the memory-architecture lane; read to avoid re-deriving | second |
| 2605.11032 | Portable Agent Memory | transport layer to build the attested format on; its evaluation is where the gap is | second |
| 2505.22954 | Darwin Godel Machine | origin of the modern field; the reward-hacking appendix matters more than the headline | second |
| 2606.26294 | Red Queen Godel Machine | evaluator drift — relevant once an intra-episodic validator joins the loop | third |
| 2607.13104 | Self-Improvements in Modern Agentic Systems | the theta-vs-Sigma taxonomy and a citable related-work map; §9 for open-problem framing | third |

Also worth having: *Externalization in LLM Agents* (2604.08224) unifies memory / skills /
protocols / harness engineering; *From Question Answering to Task Completion* (2606.20683) is a
harness-design survey; *When to Forget* (2604.12007) is the only forgetting primitive.

---

## 7. Motivating source outside the literature

Iury Souza, *Memory Portability: Owning Your AI Context* —
<https://iurysouza.dev/memory-portability-owning-your-ai-context/>

Argues accumulated context is the stickiest form of vendor lock-in and sketches a local-first,
owned memory store. The engineering conclusion this repo takes from it is narrower than the
political one: if learned context is going to be portable, **portability has to carry
attestation**, or what gets exported is negative transfer. That is C3.
