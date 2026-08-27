# Research program

Four falsifiable claims on one experimental spine. Each stands alone as a publishable finding,
including if it comes out negative. Ordering is dependency, not priority: C1 defines the
measuring stick everything else is scored against.

Background and citations: [LITERATURE.md](LITERATURE.md).

---

## C1 — Offline scaffold evolution cannot beat its own model's slack-free ceiling

**Claim.** For a fixed base model, no amount of offline scaffold evolution exceeds what that
model achieves under an oracle harness at unbounded reasoning effort.

**Why it matters.** If true, the field's headline numbers — DGM's 20→50% on SWE-bench included —
are slack recovery, not capability creation. Nobody has run this comparison. Saying so with a
clean measurement is itself the contribution, and it reframes every result that follows.

**Protocol.**

1. Define the ceiling operationally and *publish the definition before running it*:
   same base model, best-of-N at maximum reasoning effort, human-written oracle harness,
   no learned artifact, N chosen so the curve has visibly flattened.
2. Run offline scaffold evolution against the same model to budget exhaustion.
3. Compare on held-out tasks. Report the gap with confidence intervals, not point estimates.

Run this on both testbeds. BoxingGym gives the clean version (C2 needs the same ceiling on the
same environments); EvoAgentBench gives the version that is directly comparable to published
numbers.

**Predicted.** True.

**Kills.** The implicit claim that L3 evolution creates capability.

**Risk.** "Slack-free ceiling" is the reviewer's target and it is not a well-defined object —
an oracle harness is a judgement call and best-of-N at max effort is a proxy. Pre-register the
exact protocol or C1 becomes arguable rather than measured. This is the single largest threat
to the program.

---

## C2 — Intra-episodic scaffold adaptation crosses the ceiling

**Claim.** When the required knowledge is absent from the weights by construction, an artifact
written, used and validated *inside a single run* achieves what no oracle prompt can.

**Why it matters.** This is the positive result that separates the two regimes and locates where
scaffold RSI is not slack. Nobody works at this timescale: ACE, GEPA, AutoMem and every method
in EvoAgentBench assume a train/test split with many rollouts. Intra-episodic write–use–validate
is an unoccupied operating point.

**Protocol.** On BoxingGym, with instances resampled so the hidden system's parameters cannot
have been seen:

1. Same ceiling measurement as C1, on the same environments.
2. Agent maintains a within-run artifact store: writes hypotheses about the hidden system, designs
   experiments against them, validates predictions against observed outcomes, revises. The
   environment's own loop already has this shape, so the scaffold contribution is the *store and
   its curation*, not the loop.
3. Compare against the C1 ceiling at matched experiment budgets.

**Predicted.** True, with the effect appearing on **data-efficiency before final prediction
error** — fewer experiments to reach the same posterior is where an early signal should show up.

**Establishes.** The boundary condition under which scaffold RSI is not slack recovery.

**Risk.** BoxingGym's environments are drawn from recognisable model families, so a strong
parametric prior could substitute for genuine experimentation — which would mean the knowledge
was not as absent as claimed and C1's ceiling swallows C2. **Verify before building anything** —
see [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) Q1. The original paper's finding that an explicit
statistical model does not reliably help is weak evidence the risk is manageable, but it is not
the same measurement.

---

## C3 — Attested entries transfer positively; unattested ones reproduce the negative cells

**Claim.** Making per-backbone effect size a first-class field of a context entry, and gating on
it at read time, eliminates the negative-transfer cells that every automatic method in
EvoAgentBench exhibits.

**Why it matters.** This is the join nobody has made. Attribution methods (AttriMem, TreeMem,
Memory-R2) have the measurement but stay inside one system. Portability protocols (PAM,
memorywire, Engram) have the transport but never check utility — PAM's headline metric is
behavioural continuity on N=50 and the paper does not mention effect size at all. Portability
without attestation exports negative transfer.

**Mechanism.** The unit of learned context becomes an object with four fields:

| Field | Contents |
|---|---|
| `content` | the entry itself — skill, hypothesis, playbook line |
| `provenance` | derivation chain; which runs and which parent entries produced it |
| `attestation[]` | measured effect size **per backbone**, with sample size and CI |
| `retirement` | the condition under which this entry stops being loaded |

Read-time gate: refuse to load an entry whose attestation does not cover the current backbone.
Transport can reuse PAM's five-component model and Merkle-DAG provenance rather than reinventing
it — the gap is in the evaluation layer, not the plumbing.

**Protocol.** Measure negative-cell rate, gated vs ungated, across ≥3 backbones on the same task
set. The claim is specifically about the *rate of negative cells*, not mean gain — mean gain can
improve while the tail stays broken, and the tail is the failure mode that matters.

**This is the mechanism contribution.** It is also where the memory-portability thread enters.

**Risk.** AttriMem already reports learned memory transferring across answer models with drops
of only 2.07 / 1.25 / 2.31 points. If effect sizes are model-stable in general, gating buys
nothing and the contribution collapses into C4. **Test this second, on cheap tasks, before
building the format** — see [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) Q2.

---

## C4 — Optimising the curator closes most of the hand-curation gap

**Claim.** Targeting the RSI loop at the router and retirement policy — rather than at artifact
content — recovers a substantial fraction of the gap between hand-curated and automatic context.

**Why it matters.** There is a ready-made number to close. On EvoAgentBench, hand-curated
Anchor Skill scores +5.8 / +7.5 / +10.5 and is positive in every domain; every automatic method
has negative cells. That gap is the largest measured headroom in the field, and it is a
*curation* gap, not a content gap. This is L4 on the ladder — the loop mutating the thing that
generates, evaluates and retires artifacts, not the artifacts.

**Borrowed correction.** Score an entry by the clade it enables — which later entries it made
possible — not by its own immediate lift. HGM established that immediate score is a weak
predictor of a lineage's value, and greedy accumulation is the default failure mode every memory
store ships with. Clade metaproductivity has only ever been applied to code lineages; applying
it to non-code artifacts is novel.

**Protocol.** Fraction of the Anchor Skill gap recovered, on the same tasks and backbones.

**Novel.** Clade metaproductivity for non-code artifacts; curator-as-RSI-target.

---

## Dependency order

```
Q1 (prior substitution) ──gates──> C2
Q2 (model-conditionality) ──gates──> C3

C1 ──defines the measuring stick──> C2
                                     │
C3 ──mechanism──> C4 ────────────────┘
```

Run Q1 and Q2 first. Both are cheap, both can kill a claim, and neither requires building
anything. Do not write the attested-context format until Q2 comes back.

---

## Kill conditions

| # | Condition | Response |
|---|---|---|
| 1 | The ceiling definition gets attacked as ill-posed | pre-register the protocol; publish the oracle harness; report sensitivity to N |
| 2 | Attestations turn out model-stable (Q2 negative) | drop C3's gating; fold the remaining contribution into C4 |
| 3 | A parametric prior substitutes for experimentation (Q1 negative) | BoxingGym's knowledge is not absent enough; move C1/C2 to a construction where the hidden system is sampled from a family the model has no prior over |
| 4 | Someone publishes the join first | lead with the measurement, not the idea — see below |

**On #4.** Both flanks move monthly; AutoMem landed in August. The defensible position is not
the mechanism, it is the measurement: nobody has run a scaffold-RSI experiment in a setting where
the required knowledge is absent from the weights by construction, so nobody can currently say
whether any of it creates capability. Frame the contribution as *the first measurement that
separates slack recovery from capability creation*, with the attested-context format as what that
measurement required rather than as the headline.
