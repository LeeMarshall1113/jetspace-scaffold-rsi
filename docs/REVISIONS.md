# Revision log

The program was substantially revised on 2026-08-27, the day it opened, after a five-agent
literature sweep. This file records what was wrong and what replaced it, so that anyone reading an
earlier commit — or an earlier version of the reasoning — knows which parts did not survive.

---

## Factual error

**Claimed:** Model Discovery Agent (2608.09696) is state-of-the-art on BoxingGym.

**Actually:** MDA never touches BoxingGym. The string does not appear in the paper. Its benchmarks
are FORCEBENCH, CHEMBENCH and NEURONBENCH.

**Cause:** an unverified web-search summary, written into the README as a sourced fact. It was
live on a public repo for several hours. Nothing else in the program depended on it, but it was
used to argue BoxingGym had "a published bar to clear," which it did not.

---

## Falsified claim

**Claimed (original C1, the headline):** no published work separates slack recovery from
capability creation; every measured scaffold-RSI gain is consistent with recovering engineering
slack.

**Actually:** false. Three papers report evolved scaffolds crossing a ceiling —
CyberEvolver (2605.26195) beats seed pass@16 by 13.6% with 17.5% fewer tokens and argues the point
explicitly; RHI (2607.15524) beats the maximum-reasoning-effort setting at up to 60% lower cost;
HGM (2510.21614) beats SWE-agent on a matched budget. RHI was already in this repo's reading list,
cited as *supporting* the claim on the strength of its ablation, while its headline result
contradicts it.

**Replaced by:** the narrower and better-armed claim that published ceilings are seed-relative and
single-axis, that no one has built the composite, and that CyberEvolver's specifically rests on a
pass@k saturation assumption with published evidence against it in the regime applied. See
[PROGRAM.md](PROGRAM.md) C1.

**Also:** the underlying distinction already has a standard name — the **elicitation gap** (METR;
quantified at 28 points within one model by 2606.08529). The program was reinventing vocabulary.

---

## Testbed replaced

**Claimed:** BoxingGym satisfies "knowledge absent from the weights by construction."

**Actually:** it does not. Structure is fixed, hardcoded and textbook-nameable in all ten
environments; only 3–6 continuous parameters are redrawn per instance, from narrow priors centred
on published fitted values. With `include_prior=true` the domain is named in the prompt. The
harness ships the prior-only ablation (`Error@0`) and it settles the matter: six of thirteen goals
get *worse* with ten experiments, three more move by ≤0.04σ.

**Replaced by:** NEURONBENCH (primary), DiscoverPhysics plus a procedural force-law generator
(scalable second). BoxingGym is retained as a **negative control** — the environment where C1
should hold trivially and where prior substitution demonstrably saturates the measurement.

---

## Claim narrowed

**Claimed (original C2):** intra-episodic scaffold adaptation is an unoccupied operating point.

**Actually:** partially occupied. Model Discovery Agent already does hypothesis → act → validate →
revise inside a single run. What it does not do is let the agent rewrite the accumulator — its
meta-controller is a fixed, hand-built Bayesian design.

**Replaced by:** C2 restricted to **scaffold self-modification at intra-run timescale**.

---

## Claim halved

**Claimed (original C4):** nobody targets the curator/router as the RSI optimisation target.

**Actually:** MEGA (2608.10504) evolves curation strategies; ERSkill (2608.12720) names the gap
and co-evolves router with skill set.

**Retained:** clade metaproductivity applied to non-code artifacts — zero hits across every
search.

---

## Target restated

**Claimed:** EvoAgentBench's Anchor Skill is a hand-curated reference whose +5.8 / +7.5 / +10.5
represents closable headroom.

**Actually:** wrong twice. Anchor is not hand-curated — LLM extraction (Claude Sonnet 4.6),
three-judge canonicalisation, human arbitration only on non-unanimous pairs. And its routing is an
**oracle**: it retrieves by curator-side Ability labels computed offline using the test task's own
ground-truth answer and traces. The paper states three times that it "is not a deployable method."

**Replaced by:** target the routing-attributable portion of the gap. The premise is unaffected and
arguably strengthened — the paper's own §4.2 subhead is "The gap implicates method-side extraction
and routing," and it stops there.

---

## Dependencies that do not exist

**Claimed:** Portable Agent Memory (2605.11032) is the transport layer to build the attested
format on; Engram is a portability protocol alongside it and memorywire.

**Actually:** PAM's paper claims a Python SDK with 54 passing tests; no repository is linked
anywhere in the abstract or full text, and the similarly-named GitHub project is unrelated. Design
ideas only. "Engram" is not a standard — it is a name shared by six or more unrelated projects
with no common spec. AttriMem's code is likewise unreleased ("upon acceptance").

---

## Cost model wrong

**Claimed:** both testbeds are inference-heavy and GPU-light; EvoAgentBench is API-driven.

**Actually:** EvoAgentBench is a GPU-infrastructure project. Backbones are open-weight and
self-hosted via vLLM — the repo ships a config pointing at Qwen3.5-397B-A17B-GPTQ-Int4. SWE-bench
Verified needs per-instance Docker images; BrowseComp-Plus needs a FAISS-served corpus. Scope is
roughly 24,000 agent rollouts for evaluation plus ~9,500 for evolution-state construction. The
smallest evaluation backbone is 27B.

**Consequence:** C3/C4's measurement is out of reach on the available hardware and is deferred.
See [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) Q3.
