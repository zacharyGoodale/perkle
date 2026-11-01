# Richer evidence, decision thresholds, and refund stress cases

Experiment date: October 30, 2026. This is a bench experiment; application matching and ledger state were not changed.

## What changed

The new `evidence` prompt includes original bank description alongside cleaned name, amount/currency/date, pending status, merchant name, counterparties with confidence, location, MCC, transaction code, payment channel, and personal-finance category with confidence/version. Up to five related positive transactions from the same account and preceding 90 days supply purchase context. Merchant identity or exact name selects candidates; the literal balance redistribution also gets its same-day offsetting debit. Account IDs, user IDs, source IDs, expected labels, and synthetic-suite markers are not sent to Jev.

The revised rubric:

- Accept equivalent or reordered explicit issuer-benefit wording; exact name matching is unnecessary. Original description takes precedence over cleaned name.
- A merchant refund/return/reversal, payment/autopay, split reimbursement, another benefit, or identified internal balance redistribution is a non-match.
- Reserve insufficient evidence for merchant-only credits or opaque adjustments whose origin remains unresolved. Missing merchant metadata or enrollment confirmation does not negate explicit benefit-credit wording.
- A prior purchase match is supporting context: both refunds and issuer benefit reimbursements can match purchases. A `purchase` transaction code, `other` channel, or missing bank counterparty does not disqualify a credit.

All questions still run independently in one request per transaction and use the card's candidate benefit definitions. This tests the combined prompt/context change, not an isolated causal effect of any single field.

## Frozen fixtures

The real suite has 289 negative transactions and 2,294 transaction-benefit pairs. Prior fixtures remain untouched. Before this run, 14 Dunkin labels were changed from unresolved to match using explicit original bank descriptions, and the literal redistribution's three candidate labels became no-match using its offsetting debit. This gives **140 clear positive pairs**, 2,122 no-match pairs, and 32 unresolved pairs. All remain agent-adjudicated, not independently user-reviewed gold.

The separate synthetic suite has **33 cases** derived from 11 actual merchant credits spanning nine merchants, including the three Nordstrom credits. Each source is tested three ways against a fictional shopping-credit benefit added only to that case's candidate list:

1. Actual source descriptor/context: fictional benefit must not auto-record; actual refund origin is not assumed proven. The target gold label is unresolved.
2. Explicit merchant-refund description: target no-match.
3. Explicit issuer-benefit-credit description: target match, preserving purchase context to test overreliance on refund pairing.

Synthetic scenarios are sanity checks, not independent real-world accuracy evidence. Their invented merchant-credit definitions explicitly exclude refunds and adjustments. They do not affect real-case candidates or results.

## Predeclared decision policy

- Auto-record when `P(match) >= 0.90`.
- Hide when `P(no_match) >= 0.90`.
- Review otherwise, preserving uncertainty as a review outcome.

These probabilities describe the model's chosen label distribution. The thresholds have not been calibrated against independently reviewed production outcomes; 90% is an experimental boundary, not a demonstrated 90% correctness guarantee. The separate entropy-style `confidence` field is not used as match probability.

## Results

| Real-data result at the predeclared thresholds | Count |
| --- | ---: |
| Clear positive pairs auto-recorded | 113/140 (80.7%) |
| Clear positive pairs sent to review | 27/140 |
| Clear positive pairs hidden | 0 |
| Non-match/unresolved pairs auto-recorded | 0 |
| Unresolved pairs sent to review | 32/32 |
| No-match pairs sent to review | 837/2,122 |

At transaction level, 113 auto-record, 101 need review without an auto-match, and 75 are hidden. Grouping prioritizes auto-record when a transaction has one; it does not count its unrelated candidate reviews as separate transaction alerts. All 27 reviewed clear credits have the correct benefit ranked first by match probability. Only 17 distinct positive descriptor families underpin the 140 positives; 11 have at least one automatic match. Repetitions are not independent examples.

The Saks variant still goes to review with match probabilities 0.20–0.23; the richer rubric did **not** fix its recognition failure. Chase dining reaches 0.86–0.89 and goes to review. All 14 Dunkin credits reach review rather than being hidden, but none reaches the 0.90 auto threshold. The balance redistribution is confidently hidden for all candidate benefits.

For the hypothetical target benefits, all **11 actual merchant-credit cases went to review**, all **11 explicit refund variants were hidden**, and all **11 explicit issuer-credit variants auto-recorded**. There were no unsupported automatic matches elsewhere in the synthetic candidate questions either. This includes the fictional Nordstrom credit, and the other merchant stress cases.

Raw winning labels are less safe than the decision policy: on real data there were **28 known no-match pairs labeled match** plus one match on unresolved evidence; all remained below the auto threshold. Thus the result depends on gating, not on treating every winning `match` label as an automatic action.

## Review burden and a post-hoc diagnostic

Requiring 90% no-match probability to hide a candidate is noisy: 837 clearly unrelated candidate pairs stay in review. It protects recall but needs further product testing.

Using cached probabilities, an alternative diagnostic policy retains the same 90% auto threshold, reviews when `P(match) >= 0.10` **or** `P(insufficient_evidence) >= 0.50`, and hides the rest. It yields 113 auto-recorded transactions, **53 review transactions**, and 123 hidden transactions. All 140 clear positive pairs still auto-record or review, but **10 unresolved pairs are hidden**. This is a real uncertainty tradeoff, not a validated improvement. The lower gate was examined after seeing results and needs a separate evaluation set.

No policy or prompt was changed and rerun to optimize the reported model outputs. The alternative policy analysis uses the same cached probabilities. A grid of conservative thresholds 0.80, 0.90, 0.95, and 0.99 is saved privately; none is selected as a production threshold.

## Cost, checks, and reproduction

Model `jev-1.14.0`; 321 unique requests for 322 cases, 1,131,996 billed input tokens, estimated charge **$0.047544** at the researched rate. One identical request was reused. Median unique-request duration was **108 ms**, maximum **301 ms**. No automatic retries.

Four offline checks pass: expected-label/pattern exclusion, cached-cost deduplication, threshold/uncertainty behavior and case-local candidate isolation, and same-account/prior-date context filtering.

Source scripts:

- `backend/scripts/jev_bench.py`: prompt, request execution, cache, raw results and decision policy.
- `backend/scripts/jev_evidence_experiment.py`: frozen enriched fixture, separate synthetic cases and policy summaries.

Private fixture/results and exact response caches are in Git-ignored `backend/data/jev-evidence-experiment/`. Existing experiments remain unchanged.

```sh
backend/.venv/bin/python -m unittest discover -s backend/scripts -p 'test_*.py'
backend/.venv/bin/python backend/scripts/jev_evidence_experiment.py summarize
```

To fill missing cached requests for this frozen fixture (paid):

```sh
backend/.venv/bin/python backend/scripts/jev_bench.py run \
  --data-dir backend/data/jev-evidence-experiment \
  --prompt evidence --max-cases 400 --max-usd 0.25
```

The next product implementation should group review suggestions by transaction and allow manual correction in both directions. Those UI and ledger changes are not part of this bench. Independently review labels and validate thresholds on new cases before relying on automatic recording.
