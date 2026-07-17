# Rubric Layer (v2) — Graded Qualities

The deterministic layer proves outputs are **well-formed** (`scripts/validate_*.py`); the case layer proves decisions are **correct** (`evals/cases/`). This layer grades what neither can: qualities that exist on a spectrum — is the copy something a human would actually send, is the journey design coherent, is the dossier readable. A rubric score is an **anchored ordinal judgment, not a measurement**: it is honest only when the anchors are concrete, the evidence is quoted, and the judge is independent.

## Protocol (all five hold, or the scores are decoration)

1. **Blind & independent.** The judge never scores output it produced. Use a fresh session — or better, a different model entirely (cross-model judging cuts self-preference bias; the repo's own runs have used an external model as judge).
2. **Evidence or it didn't happen.** Every score below 5 quotes the exact line that cost the point; every 5 quotes the line that earned it. A scorecard without quotes is rejected.
3. **Adversarial posture.** Same anti-inflation rule as `lifecycle-audit` and `copy-reviewer`: the default assumption is that a point is not earned. An all-5 scorecard on a first pass means re-judge, not celebrate.
4. **No invented aggregate.** Dimensions are reported separately. There is no weighted total — a single blended number hides exactly the signal this layer exists to surface.
5. **Two judgments to gate.** A release-gating decision needs two independent scorecards; dimensions disagreeing by ≥ 2 points get re-judged with both sets of evidence side by side.

## Scale anchors (all dimensions)

- **1** — the failure mode named in the dimension is present and typical.
- **3** — competent and rule-compliant, but exhibits the "passes checks, still mediocre" quality the dimension warns about.
- **5** — a practitioner would ship it unchanged; the quoted evidence shows why.

## Copy dimensions (per copy doc / canvas)

| Dim | Question | 1 looks like | 5 looks like |
|---|---|---|---|
| **C1 Intent fidelity** | Does each block deliver its step's intent line — and nothing else? | Copy drifts to a generic pitch; intent line ignored | Every block is the intent line, executed |
| **C2 Naturalness** | Would a human at this brand actually send this sentence? | Template-speak, crammed clauses, hedges ("belki", "neredeyse") | Reads like the brand's best human writer on a good day |
| **C3 Variant distinctness** | Are A/B genuinely different *strategies*? | Synonym swaps wearing different `strategy` labels | The two variants would produce a decision-worthy test result |
| **C4 Claim discipline** | Is every factual/urgency claim variable-backed, every incentive within policy? | Adjective urgency, baked literals, unbacked "most popular" | Every claim traceable; restraint visible where data was missing |
| **C5 Persona precision** | Is this written to the journey's §3 audience? | Addressed to "a user"; segment context invisible | Word choice and framing only make sense for exactly this persona |

## Journey/portfolio dimensions (per portfolio + journey docs)

| Dim | Question | 1 looks like | 5 looks like |
|---|---|---|---|
| **J1 Sequence coherence** | Do steps escalate with a visible logic (channel economics, timing anchors)? | Arbitrary waits, channel order contradicts cost/intrusiveness rules | Every wait/channel choice cites its anchor (decision-trace rule held) |
| **J2 Portfolio balance** | Leak-recovery AND growth, per CLAUDE.md rule 2? | Only fix-the-broken journeys; healthy areas ignored | Mix reflects the funnel's actual shape, stated in the exec summary |
| **J3 Honesty surface** | Are limits (assumptions, blocked depth, activation flag) visible where a stakeholder will look? | Caveats buried or missing; portfolio reads rosier than the data | Assumptions marked inline; the dossier says what can't run and why |
| **J4 Tracking-plan leverage** | Does the plan name what each missing event *unlocks*, ranked by value? | A flat list of "nice to have" events | A data engineer could sequence next quarter's work from it directly |

## Dossier dimensions

| Dim | Question | 1 looks like | 5 looks like |
|---|---|---|---|
| **D1 Standalone readability** | Can a stakeholder who saw nothing else act on it? | Requires opening other files to make sense | One read → correct mental model of the whole run |
| **D2 Proportion** | ~One page, selective detail per the template's rule? | A second copy of the raw outputs | The cut material was cut for a visible reason |

## Scorecard format

```
## Rubric — <project> · <artifact> · judge: <model/session> · date
| Dim | Score | Evidence (quoted) |
|---|---|---|
| C1 | 4 | "..." — intent held in 21/22 blocks; step 3b drifts: "..." |
...
verdict-notes: <the 2-3 findings that should change the next run>
```

Scorecards live in `output/<project>/rubric-<judge>.md` (machine-facing until a human reads them; never auto-acted on — findings route through the normal review process like any external input).

## When to run

Before a release; after any change to lexicons, persuasion/segmentation knowledge, or copy-writer/copy-reviewer agents; and on every real-data run's outputs while the engine is still young — real runs are where the 3-vs-5 gap shows.
