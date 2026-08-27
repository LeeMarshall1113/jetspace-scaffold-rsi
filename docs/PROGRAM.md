# Research program

One paper, four claims, ordered by contribution. C2 is the result; C1 is the control that makes
C2 meaningful; C3 is the mechanism that makes C2 hold across backbones; C4 is a stretch goal that
costs little given the chosen codebase.

Background and citations: [LITERATURE.md](LITERATURE.md). What changed and why:
[REVISIONS.md](REVISIONS.md).

---

## C2 — An agent that rewrites its own scaffold within a single run crosses the ceiling

**Headline claim.** Where the required knowledge is absent from the weights by construction, an
agent that modifies **its own scaffold** inside a single run achieves what no oracle prompt and no
offline-evolved scaffold can.

**The narrowing that matters.** "Within-run adaptation beats offline" is **already demonstrated**.
Model Discovery Agent (2608.09696) does hypothesis → act → validate → revise inside one run: it
expands the hypothesis space when predictive-check error is too high and contracts it when the
posterior concentrates. What MDA does *not* do is let the agent rewrite the accumulator — its
meta-controller is a fixed, hand-built Bayesian design. C2 is therefore specifically about
**scaffold self-modification at intra-run timescale**, not about intra-run adaptation.

**Why it is still open.** Four papers with intra-run-sounding framings were checked word-for-word
and all confirmed inter-episodic only: TTHE (2607.08124), JIT-Agent (2608.25593), HELIX
(2608.13951), Recuris (2608.24876). Every offline method — ACE, GEPA, AutoMem, everything in
EvoAgentBench — assumes a train/test split with many rollouts.

**Clock.** Three independent "test-time" / "just-in-time" / "online" framings landed within three
weeks of 2026-08. This is the fastest-closing window in the program. Prioritise accordingly.

**Protocol.** On NEURONBENCH primarily, DiscoverPhysics-with-procedural-force-laws for scale:

1. Measure the composite ceiling from C1 on the same worlds.
2. Agent maintains a within-run scaffold it may rewrite: hypothesis store, the routine that
   proposes experiments, and the rule that decides what to keep. The environment supplies the
   validation signal; the contribution is that the *machinery* is mutable, not the hypotheses.
3. Compare at matched experiment budgets and matched token budgets.

**Predicted.** True, with the effect on **data-efficiency before final error**. MDA's own framing
supports this — "this gap is one of data efficiency, not capability" — and these benchmarks are
built to measure exactly that.

**Risk.** If the agent's scaffold rewrites converge to something MDA's hand-built controller
already encodes, the result is a rediscovery, not a contribution. Mitigate by reporting *what the
agent wrote*, not just the score.

---

## C3 — Per-backbone attested entries, gated at read time, eliminate negative transfer

**Claim.** Making measured effect size **per backbone** a first-class field of a learned-context
entry, and refusing to load entries whose attestation does not cover the current model, removes
the negative-transfer cells every automatic method exhibits.

**Two motivations; the second is stronger.**

*Capability.* EvoAgentBench's 17 negative cells, worst at −36.3. The structural pattern is the
interesting part: OpenClaw carries **12 of 17 (71%)** despite having 26 tools to Nanobot's 7 —
more scaffold surface correlated with *more* negative transfer. By domain: knowledge work 7/18,
SWE 6/18, algorithmic 3/18, web research 1/18.

*Safety.* Unattested accumulation is exploitable and the damage is not undoable. Skill backdoors
via poisoned trajectories reach 56–89% attack success (2608.03509); trajectory poisoning reaches
91% (2608.05563); individually-safe experiences compose into unsafe behaviour (2608.01759). And
"When Self-Evolution Backfires" (2608.05810) shows bad skill admission is **structurally
irreversible post-hoc**, which makes pre-commit gating necessary rather than merely useful.

Lead with safety. It is the better argument and it is less crowded.

**Mechanism.** The unit of learned context is an object with four fields:

| Field | Contents |
|---|---|
| `content` | the entry — skill, hypothesis, playbook line |
| `provenance` | derivation chain; which runs and which parent entries produced it |
| `attestation[]` | measured effect size **per backbone**, with sample size and CI |
| `retirement` | the condition under which this entry stops being loaded |

**The schema is the easy part.** Confirmed: nothing anywhere combines all three of provenance,
per-backbone effect size, and a retirement condition with read-time gating. Nearest fragments each
miss two — ACE's `helpful=X harmful=Y` counters are global not per-backbone; memorywire has
provenance and a quarantine state machine but no effect measurement; AutoMem measures per-backbone
but at the *architecture* level; AttriMem attributes at write time, not read time, and has no code
released.

**The retirement policy is the research problem.** How much per-backbone evidence justifies
retiring an entry is a bandit / credit-assignment design question, not a library question. That is
where C3's contribution actually lives.

**Steal, do not depend on:** ACE's counter notation; memorywire's quarantine-not-delete state
machine and its thin `MemoryStore` interface over swappable backends. Skip Merkle-DAG provenance
absent a real adversarial threat model.

**Risk.** AttriMem reports learned memory transferring across answer models with drops of only
2.07 / 1.25 / 2.31 points. If effect sizes are model-stable in general, gating buys nothing.
**Test this before building the format** — [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) Q2.

---

## C1 — The composite ceiling, and which published gains survive it

**Demoted from thesis to control condition.** The strong form — "no published work separates slack
recovery from capability creation" — is **falsified**. Three counterexamples:

| Paper | Ceiling crossed | Weakness of that ceiling |
|---|---|---|
| CyberEvolver (2605.26195) | seed pass@16, beaten by 13.6% with 17.5% *fewer* tokens | ceiling is the *seed scaffold's*, not a strong human harness; expert baselines capped at pass@4 |
| RHI (2607.15524) | max-reasoning-effort setting, at up to 60% lower cost | same-family test-time scaling only; no best-of-N; no human oracle harness |
| HGM (2510.21614) | SWE-agent, same backbone, matched budgets | strong human baseline, but not an oracle; no BoN or effort control |

**What survives.** No paper conjoins the four axes: BoN sampling ceiling, maximum reasoning
effort, a strong human harness, and compute matching. The contribution is the composite instrument
plus the replication verdict.

**The concrete target.** CyberEvolver capped its expert baselines at pass@4 on the grounds that
"pass@k saturates beyond k=4 for fixed scaffolds," generalising from its own seed agent's curve
(+1.4% from k=4 to k=16). Pass@(k,T) analysis (2604.14877) shows saturation is **task-dependent**:
on compositional multi-step tasks the gap *widens* at the right tail and curve orderings **flip
near k=4**. CTF and pentest targets are compositional multi-step tasks. The assumption is
unsupported in the regime it was applied to, and the error direction favours their own result.
Their 13.6% margin is not protected against a properly-run expert-scaffold pass@16.

**Best available headroom precedent.** ReCreate (2601.11100) Appendix F: five human-designed
scaffolds, one fixed base model, SWE-bench Lite — union solves 184, best single scaffold 147, so
**37 issues (20% of union) are scaffold-fixable**. Clean construction, non-saturated benchmark,
buried as appendix motivation, nobody has built on it. Use this, not CORE-Bench.

*Do not* use CORE-Bench's "oracle router reaches 100%" as a headroom figure — the benchmark is
near-saturated and headroom is 10.3 pts for Opus 4.5 but 2.6 for GPT-5.4. Its useful result is
different: scaffold outcomes **disagreed on 31% of tasks at near-identical means**, i.e. scaffolds
route the model to different solvable regions rather than being uniformly better or worse. That is
the argument for curation work.

**Estimator hygiene.** "Beyond Pass@k" (2608.14711) finds implementations routinely set n to the
number of unit tests rather than independent rollouts, inflating scores by 0.85–0.97 absolute.
State the estimator explicitly.

**Reusable instrument.** PAST-Bench (2608.04003) — 26 scenarios, 204 episodes, on/off retained
experience — isolates whether a gain is supported by evidence of the intended pathway. Reuse
rather than rebuild.

---

## C4 — Clade metaproductivity for non-code artifacts

**Half the original claim is occupied.** "Optimise the curator/router rather than artifact
content" is taken:
- **MEGA (2608.10504)** evolves "the curation strategies that govern wisdom composition."
- **ERSkill (2608.12720)** states the gap in its own words — "the retrieval mechanisms governing
  this memory are rarely treated as evolvable components" — then co-evolves router and skill set.

**The clean half.** Applying HGM's clade metaproductivity to non-code artifacts returned **zero
hits** across every search. Score a memory entry by the lineage it enables — which later entries
it made possible — rather than its own immediate lift. HGM established that immediate score is a
weak predictor of a lineage's value; greedy accumulation is the default failure mode of every
memory store.

**Why it is cheap here.** The chosen base is a fork of `metauto-ai/HGM`, which *is* the CMP
implementation. Extending it from code lineages to memory lineages reuses the selection machinery.

**Restated target.** The earlier framing — "close the gap to hand-curated Anchor Skill" — was
wrong on two counts, corrected in [REVISIONS.md](REVISIONS.md). Anchor is not hand-curated (LLM
extraction, three-judge canonicalisation, human arbitration only on non-unanimous pairs), and its
routing is an **oracle**: it retrieves by curator-side Ability labels computed offline from the
test task's own ground-truth answer and traces. The paper says so — "Anchor Skill is not a
deployable method." Its +5.8 / +7.5 / +10.5 is an oracle-routing ceiling, definitionally
unreachable by a real router.

The premise survives and is stronger for it: EvoAgentBench §4.2's subhead is literally "The gap
implicates method-side extraction and routing," and the paper stops there. The diagnosis is handed
over; the fix is not taken. Target the **routing-attributable portion** of the gap.

**Quantitative anchor for curation work:** "Demystifying Agent Skills" (2608.14036), 8,135 trials
— retrieval precision collapses from **29.6% to 3.3%** as the skill pool grows.

---

## Dependency order

```
Q2 (model-conditionality) ──gates──> C3
Q1 (testbed novelty)      ──gates──> C2      [BoxingGym answered NO; NEURONBENCH pending]
Q3 (compute)              ──gates──> C3/C4 measurement on EvoAgentBench

C1 ──defines the measuring stick──> C2 ──> C3 ──> C4
```

Q2 first: cheap, no infrastructure, decides whether C3 is a mechanism or a wrapper around C4.

---

## Kill conditions

| # | Condition | Response |
|---|---|---|
| 1 | Composite ceiling attacked as ill-posed | pre-register the protocol; publish the harness; report sensitivity to N and state the pass@N estimator |
| 2 | Effect sizes are model-stable (Q2 negative) | drop C3's gating; the safety argument survives on its own; fold the rest into C4 |
| 3 | NEURONBENCH's six worlds are too few for statistics | DiscoverPhysics + procedural force-law generator becomes primary, not secondary |
| 4 | Agent's scaffold rewrites converge on MDA's hand-built controller | report what the agent wrote; a rediscovery framed honestly is still a result, but it is a weaker one |
| 5 | Someone publishes intra-run scaffold self-modification first | the clock is real — three near-misses in three weeks. This is the reason C2 goes first. |
