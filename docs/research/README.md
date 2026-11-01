# Jev benefit-credit classification research

Start here for the spike's conclusion, experiment history, and artifact index. The individual notes preserve decisions as they happened; their original recommendations can be superseded by later experiments. This index states the current choice.

## Current decision

Keep the **single-transaction confirmation approach** in [the exact selected prompt](jev-confirmation-single-transaction.json). For each posted negative transaction, send one Jev request containing two shared Choice questions: the transaction's described credit type, and its best-fitting benefit from the card's benefit roster. Supply available original description and transaction metadata; omit related transaction history. No category-first pipeline, purchase matching, amount-cap inference, or fallback model is required.

Ordinary code withholds a suggestion if the combined excluded-flow score is at least 0.80. Otherwise, it selects the strongest benefit candidate and suggests that one benefit when its score is at least 0.25. These scores are relative model outputs, **not calibrated probabilities that an issuer paid a benefit**. Every suggestion needs user confirmation before usage is recorded. Users should also be able to remove a mistaken match or add a missed transaction. Those UI paths are product requirements, not implemented by this research bench.

Explicit program identity takes priority over overlapping merchant or category meaning. When a covered merchant is identifiable, unknown origin, enrollment, or fee subtype can be resolved by the user. Generic adjustment wording, equal amounts, or a matching prior purchase do not prove a refund. Clear payment, refund/reversal, shared-expense repayment, or supported balance redistribution can justify withholding. The selected no-history configuration cannot establish an offsetting-purchase relationship and should not invent one.

The final obfuscated publication run recovered **140/140** known credits and agreed with **467/469** transaction decisions, with one unsupported top suggestion and one missed unresolved-origin candidate. See [the final report](jev-final-baseline.md) for both errors, exact scores, and reproducible evidence.

## What the evidence supports

The source snapshot supplied 289 real negative transactions. The final fixture combines those with 180 constructed cases, for 469 transactions and 2,865 transaction-benefit pairs. There are 140 clear in-scope real credits from only 17 positive descriptor families. Another 26 real-history suggestions are unresolved-origin, policy-positive confirmation candidates; they are not verified issuer credits. Labels are provisional agent adjudications rather than independently user-confirmed issuer outcomes.

On the original private fixture, the selected no-history baseline recovered 140/140 clear real credits and produced an allowed top suggestion or correct withholding decision for 469/469 transactions. Its raw pair diagnostics remained imperfect: 291 positive pairs above threshold, one unsupported secondary candidate, and 20 allowed alternatives below threshold. On the last 50-case synthetic set, the earlier full-context winner had 100% one-top decision agreement but only 86% pair agreement. The fixture has since been exposed during prompt development. Replays do not restore holdout status.

The strongest simplification was removing history: it preserved all final decisions while reducing input tokens by 8.78%. More elaborate evidence wording and historical amount hints added three unsupported real suggestions. A later clarity arena produced a shorter rubric that used 28.76% fewer tokens than the selected baseline, but missed seven desired confirmation suggestions. Retain that candidate as research rather than promoting it.

The original no-history run used 886,377 input tokens across 466 distinct requests, costing an estimated $0.03723 at the recorded Jev rate of $0.042 per million input tokens. Actual-history payloads implied about $0.089 per 1,000 negative transactions. Cumulative recorded hill-climb and follow-up usage before the publication rerun was about $1.10549 including retained uncertain-attempt reservations. These figures exclude arena-agent usage, infrastructure, annotation, and future pricing changes. Use the publication rerun's results for claims about the obfuscated fixture; do not transplant these original-data metrics to it.

This supports a small confirmation pilot. It does not establish general population accuracy, reliable exhaustive benefit enumeration, or safe automatic usage recording. No model-powered production detector or notification flow was deployed by the spike. A separate backend metadata-preservation change was deployed so the analysis could inspect fields previously discarded upstream.

## Publication bundle and reproduction

The [final baseline report](jev-final-baseline.md) records the rerun on the obfuscated fixture and the privacy and meaning reviews. Its [machine-readable results](jev-final-baseline-results.json) are the authoritative publication-run output. The [public fixture](../../backend/fixtures/jev/fixture.json) contains the 469 single-transaction cases, candidate coverage, and frozen suggestion labels. Use the [public runner](../../backend/scripts/jev_public_bench.py) for this bundle rather than historical commands requiring private snapshots:

```sh
backend/.venv/bin/python backend/scripts/jev_public_bench.py run
backend/.venv/bin/python backend/scripts/jev_public_bench.py report
backend/.venv/bin/python backend/scripts/jev_public_bench.py publish
```

The runner offers `run`, `report`, and `publish`; caches stay in ignored `backend/data/jev-public-bench/`. For a fresh Python environment install `python-dotenv` and `PyYAML` (or use the existing backend environment). Running missing requests requires a `TYPESAFE_API_KEY`; reporting saved results does not justify substituting old private-fixture responses. Expected labels are evaluation inputs and must not be sent in model requests. Retain the selected prompt and frozen thresholds for this publication rerun rather than tuning after inspecting changed cases.

Publication transforms account and transaction identifiers, location details, and niche or sensitive merchant identities while preserving the relevant merchant class, descriptor meaning, and within-fixture relationships. Generic brands needed to evaluate real benefit coverage can remain. Exact amounts and calendar month/year are retained; each date’s day is shifted within its month and known historical benefit regime; this is **pseudonymization, not a guarantee of anonymity**. The mixture of real-derived and constructed examples does not itself remove privacy risk. Keep any transformation mapping, raw source payload, credentials, and private cache out of Git. Do not combine this bundle with outside records to identify the source person.

## Read by question

| Question | Read |
| --- | --- |
| What did we try, and what were the tradeoffs? | [Approaches summary](jev-approaches-summary.md) |
| What exact request should an initial pilot use? | [Selected single-transaction JSON](jev-confirmation-single-transaction.json), [no-history comparison](jev-single-transaction-rubric.md) |
| How did prompt optimization and thresholds evolve? | [Hill-climb record](jev-confirmation-hillclimb.md) |
| Can Plaid distinguish refunds from benefit credits? | [Refund/credit signal research](plaid-refund-credit-signals.md), [observed enriched-data patterns](plaid-enriched-production-patterns.md), [gate distributions](jev-flow-distribution.md) |
| Which fields were useful or unavailable? | [Plaid field research](plaid-credit-signals.md), [enriched-data observations](plaid-enriched-production-patterns.md) |
| Are Plaid Insights or Enrich useful, and what do they cost? | [Insights investigation](plaid-insights.md) |
| How strong is benefit amount as evidence? | [Amount analysis and fallback preparation](jev-luna-cascade.md), [dated-cap rubric experiment](jev-single-transaction-rubric.md) |
| Did a smarter-model cascade work? | [Luna experiment](jev-luna-cascade.md): zero successful classifications because of exhausted API credit; no quality conclusion |
| How common are refunds in these benefit categories? | [Benefit/refund risk research](benefit-refund-risk.md): category reasoning, not a measured personal or population refund rate |
| Did clearer instructions improve results? | [Clear-rubric arena and benchmark](jev-clear-rubric-arena.md): shorter, but seven missed suggestions |

## Review records

- [Independent meaning review](jev-meaning-review.md): label, signal, candidate, and historical-regime preservation checks.
- [Independent privacy review](jev-privacy-review.md): final publication scope and residual privacy limits.

## Complete artifact index

### Initial research and pilots

- [Initial API/design research](jev-benefit-classification.md): vendor API facts, request structures, category-cascade alternatives, cost assumptions, and original evaluation proposal. Its three-way classification and independent-benefit recommendation are historical.
- [Small pilot](jev-small-bench.md): first limited fixtures and feasibility checks.
- [Production golden-set construction](jev-production-golden-set.md): source coverage, label construction, real versus constructed examples, and limitations.
- [Early production results](jev-production-results.md): descriptor-based Jev and string-pattern comparison before original-description enrichment expanded the clear-positive cohort.
- [Plaid credit-signal research](plaid-credit-signals.md): optional schema fields and their limits.
- [Enriched production patterns](plaid-enriched-production-patterns.md): observed signal quality after preserving metadata.
- [Plaid Insights research](plaid-insights.md): product distinctions, overlap, access, and unavailable public numeric prices.

### Evidence, confirmation, and risk

- [Rich-context threshold experiment](jev-evidence-threshold-experiment.md): three-way labels, review queues, context, and thresholds.
- [Tight-refund confirmation experiment](jev-confirmation-experiment.md): moving from proof of origin toward confirmation suggestions.
- [Refund risk by benefit](benefit-refund-risk.md): merchant/category considerations and limits of available frequency evidence.
- [Amount and Luna cascade](jev-luna-cascade.md): exact-cap collisions, historical-cap problems, prepared fallback, and unsuccessful API probes.
- [Refund/credit signal research](plaid-refund-credit-signals.md): authoritative documentation, missing provenance, transaction-code coverage, and conservative exclusion implications.
- [Flow distributions and gate ablations](jev-flow-distribution.md): real versus constructed exclusions and why no observed real refund effect does not establish that the gate is unnecessary.

### Prompt arenas and hill climbing

- [Initial arena candidate prompts](jev-prompt-arena-candidates.md).
- [Initial arena votes/results](jev-prompt-arena-results.md).
- [Initial arena synthesis](jev-prompt-arena-synthesis.md) and [synthesis ballot](jev-prompt-arena-synthesis-ballot.md).
- [Hill-climb experiments and exit conditions](jev-confirmation-hillclimb.md): architecture changes, prospective V2 label-policy changes, thresholds, validation history, costs, and limitations.
- [Full-context winner JSON](jev-confirmation-winner.json): earlier retained configuration, before removing history.
- [Approaches summary](jev-approaches-summary.md): compact comparison across the spike; its final single-transaction update supersedes the opening full-history recommendation.
- [No-history and amount-rubric comparison](jev-single-transaction-rubric.md).
- [Selected single-transaction JSON](jev-confirmation-single-transaction.json).
- [Rejected broader amount/evidence rubric JSON](jev-single-transaction-rubric.json).
- [Clear-rubric arena and benchmark](jev-clear-rubric-arena.md).
- Clear-arena writer drafts: [A](jev-clear-arena-writer-a.md), [B](jev-clear-arena-writer-b.md), [C](jev-clear-arena-writer-c.md).
- Clear-arena independent judgments: [A](jev-clear-arena-judge-a.md), [B](jev-clear-arena-judge-b.md), [C](jev-clear-arena-judge-c.md).
- [Rejected clear-arena synthesis JSON](jev-clear-arena-synthesis.json): unanimous qualitative approval did not prevent benchmark regressions.

### Bench implementation

- [Initial bench and shared helpers](../../backend/scripts/jev_bench.py).
- [Evidence fixtures and context experiment](../../backend/scripts/jev_evidence_experiment.py).
- [Budgeted hill-climb runner and reports](../../backend/scripts/jev_hillclimb.py).
- [Earlier confirmation report](../../backend/scripts/jev_confirmation_report.py).
- [Prepared Luna fallback](../../backend/scripts/jev_luna_cascade.py).
- [Offline checks](../../backend/scripts/test_jev_bench.py).

Some historical commands refer to private, Git-ignored local snapshots and caches. They document provenance and are not standalone reproduction instructions from a clean checkout. Raw Plaid payloads, access tokens, private identifier mappings, and original response caches should remain private. The publication bundle uses a separate obfuscated fixture and its own rerun; that material must be assessed separately for privacy and meaning preservation.

## Findings to carry into future work

1. Preserve original bank descriptions. Cleaned merchant labels hid clear benefit wording in this snapshot; enrichment cannot restore discarded evidence reliably.
2. Compare benefits jointly. Independent questions can favor overlapping benefits; one-top output is part of the evaluated product contract.
3. Separate semantic fit from origin. A plausible covered merchant can merit confirmation even when Plaid cannot prove who originated its credit.
4. Avoid hard refund inference from purchase pairing. An issuer reimbursement may equal a prior purchase too. Plaid does not document a universal issuer-benefit flag or original-purchase link for arbitrary card refunds.
5. Version benefit rules before using amounts. Current caps can be wrong for historical dates; equality supports an existing match, and partial credits remain valid possibilities.
6. Let measured results outrank prompt votes. Shorter or more explicit-looking rubrics changed behavior adversely; qualitative clarity is not equivalence.
7. Keep refund and synthetic limitations visible. Sparse real refund evidence and repeated descriptors cannot establish future false-positive rates. Collect user-reviewed outcomes across people, issuers, and changing terms before stronger claims.

## Exact historical prompts

The [prompt archive](jev-prompt-archive/README.md) preserves all 16 hill-climb configurations, including rejected rubrics. Earlier descriptor and evidence prompt builders remain in the archived bench scripts. Their historical commands require ignored private snapshots; the public baseline runner uses the standalone published fixture.
