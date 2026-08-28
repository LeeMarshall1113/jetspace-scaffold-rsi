# jetspace-scaffold-rsi

Research on **scaffold-level recursive self-improvement**: loops that improve an agent's
scaffolding — prompts, memory, skills, control flow, curation policy — rather than its weights.

Opened 2026-08-27. Field map current through arXiv 2608.

> **Status (2026-08-28).** The original four-claim program is superseded. Occupancy sweeps
> falsified or found published work occupying C1, most of C2, C3's strong form, half of C4, and
> a later big-model-teaches-small pivot. What survived is a single short measurement paper —
> see `docs/PAPER-PLAN.md`. `docs/REVISIONS.md` records what died and why. The durable assets
> are the Q2 results and the measurement instrument, not the original claims.

---

## Thesis

Scaffold-level RSI results are reported against **seed-relative, single-axis ceilings**. Nobody
has built the composite ceiling — best-of-N sampling *and* maximum reasoning effort *and* a strong
human harness *and* compute matching, together — so it is not currently known which published
gains survive it.

This is a narrower claim than "scaffolds only recover slack," which is **false**: three papers
report evolved scaffolds crossing a ceiling ([CyberEvolver](https://arxiv.org/abs/2605.26195),
[RHI](https://arxiv.org/abs/2607.15524), [HGM](https://arxiv.org/abs/2510.21614)). But each
ceiling is weak in a specific way, and one has a documented flaw — see
[docs/PROGRAM.md](docs/PROGRAM.md) C1.

The field already has a name for the underlying distinction: the **elicitation gap** (METR).
[2606.08529](https://arxiv.org/abs/2606.08529) measures 28 points of it *within a single model*
and concludes that "capability numbers produced under a single scaffold are scaffold-conditional
estimates." That vocabulary is standard; use it.

## Program

Ordered by contribution, not dependency. This is one paper, not four.

| | Claim | Status |
|---|---|---|
| **C2** | An agent that **rewrites its own scaffold within a single run** beats the composite ceiling, where the required knowledge is absent from the weights by construction | **headline** — open, clock running |
| **C3** | Learned-context entries carrying a **per-backbone attested effect size**, gated at read time, eliminate negative transfer | mechanism — open |
| **C1** | The composite slack-free ceiling, and which published gains survive it | control condition, not the contribution |
| **C4** | **Clade metaproductivity applied to non-code artifacts** — score a memory entry by the lineage it enables | stretch goal — half of the original claim is occupied |

Protocols, kill conditions and prior art in [docs/PROGRAM.md](docs/PROGRAM.md).

## Testbeds

C2 needs an environment where the required knowledge is absent **by construction**, not by
argument. That requirement eliminates almost everything.

| | Role | Why |
|---|---|---|
| **[NEURONBENCH](https://github.com/murphyk/neuronbench)** | primary | Six mystery neurons whose membrane mechanisms were "designed in order to prevent the LLM from simply recalling the model from memory." Engineered against exactly this failure mode. MIT, active. Limit: only six worlds, and SOTA is already published. |
| **[DiscoverPhysics](https://github.com/SampsonML/DiscoverPhysics)** + a procedural force-law generator | scalable second | 22 non-canonical worlds, half held out; authors concede they are "deliberately curated rather than genuinely novel." **But the simulator accepts arbitrary force laws** — adding a procedural generator is small, well-defined work and yields a genuinely by-construction testbed. |
| **[BoxingGym](https://arxiv.org/abs/2501.01540)** | negative control | Where C1 should hold trivially. See below. |
| **[EvoAgentBench](https://arxiv.org/pdf/2607.05202)** | C3/C4 measurement | Deferred — it is a GPU-infrastructure project, not an API bill. See [docs/OPEN-QUESTIONS.md](docs/OPEN-QUESTIONS.md) Q3. |

**Why BoxingGym is a negative control and not the testbed.** Its structure is fixed, hardcoded
and textbook-nameable in all ten environments; only 3–6 continuous parameters are redrawn per
instance, from narrow priors centred on published fitted values, and with `include_prior=true`
the domain is named outright in the prompt. The harness already ships the prior-only ablation
(`Error@0`), and it settles the question: **six of thirteen goals get *worse* with ten
experiments**, three more move by ≤0.04σ. That is not a window in which a ceiling crossing can
be demonstrated — but it is a clean demonstration of prior substitution saturating a measurement,
which is worth publishing as a control.

## Why this angle

Everything in the RSI literature is measured on SWE-bench, Polyglot, AppWorld, GAIA,
WebWalkerQA, LiveCodeBench — static distributions, contamination risk, large engineering slack.
The defensible position is not the mechanism, it is the **measurement**: a composite ceiling in
an environment where the knowledge is absent by construction, which nobody has built.

## Layout

```
docs/         thesis, field map, program, open questions, revision log
research/     paper notes; PDFs gitignored
harness/      scaffold + attested-context implementation
experiments/  run configs and results
```

## Status

| | |
|---|---|
| Phase | literature complete, program revised, nothing built |
| Base | fork [`metauto-ai/HGM`](https://github.com/metauto-ai/HGM) — Apache-2.0, already implements clade metaproductivity, which C4 extends |
| Blocking | Q2 (are per-entry effect sizes model-conditional?) — cheap, needs no infrastructure, decides whether C3 is a mechanism |
| Deferred | Q3 (compute for C3/C4 measurement) |

## Reading

Start with [docs/LITERATURE.md](docs/LITERATURE.md) — the lineage, the results that bound the
design, and the claim map. Reading order at the bottom.

---

## A note on this README

This README — and the files under `docs/` — were drafted by an AI assistant (Claude), and will
stay that way until a human wants to rewrite them. The research direction, the constraints, and
the calls about what to pursue are the maintainer's. The prose and the literature sweep are not.

Saying so plainly seems better than letting you work it out from the em-dashes. It is also
load-bearing: an earlier revision of this file asserted that Model Discovery Agent was
state-of-the-art on BoxingGym. It is not, and never touched that benchmark. The error came from
an unverified search summary. `docs/REVISIONS.md` logs it. Treat unsourced claims here as
provisional and check the arXiv IDs.

**If you'd like to rewrite any of it in your own voice, please do — that would be genuinely
welcome.** A PR or an issue is plenty; no need to ask first. The parts most worth a human pass
are the thesis framing above and the claim map in `docs/LITERATURE.md`, where the judgement
calls are load-bearing and deserve someone willing to argue with them.

## License

[MIT](LICENSE). Contributions are accepted under the same terms.
