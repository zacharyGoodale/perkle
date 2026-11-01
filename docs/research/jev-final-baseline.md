# Final published baseline — October 31, 2026

Keep the simple **single-transaction, one-top-suggestion, confirmation-only** approach. This publication run used the [selected prompt](jev-confirmation-single-transaction.json) unchanged, on the reviewed [obfuscated fixture](../../backend/fixtures/jev/fixture.json). It recovered all 140 explicit real-derived credits and agreed with 467 of 469 frozen transaction decisions. Two changed decisions are retained below; no labels, prompts, thresholds, or aliases were tuned after seeing this run.

## Measured result

| Metric | Published rerun |
| --- | ---: |
| Cases / distinct requests | 469 / 466 |
| Real-derived / constructed cases | 289 / 180 |
| Candidate-benefit judgments | 2,865 |
| Correct top-suggestion or withhold decisions | 467/469 (99.57%) |
| Explicit real-derived credits recovered | 140/140 |
| Confirmation-eligible cases with an allowed top suggestion | 289/290 (99.66%) |
| Unsupported top suggestions | 1 |
| Total suggestions / withheld | 290 / 179 |
| Correct decisions: real-derived / constructed | 287/289 / 180/180 |
| Raw pair true positives / false positives / false negatives | 290 / 2 / 21 |
| Raw pair agreement | 99.20% |
| Input tokens | 886,367 |
| Estimated Jev charge | $0.037227414 |
| Client-observed median serial request duration | 90 ms |

Cost uses the recorded experiment rate of $0.042 per million input tokens; this is not a future price guarantee. Duration is a serial client observation, not a production load test. The charge excludes agent/arena work, annotation, infrastructure, and earlier experiments. Three exact duplicate requests share cached answers; repeated descriptor families are not independent examples.

## The two decision errors

- `case-0272`: the invented restaurant descriptor **OLIVE TABLE DINING LLC PORTLAND**, a $3 credit, received a 0.31 Gold dining score. The frozen label requires withholding because the identified restaurant has no supported connection to the listed dining partners. This is an unsupported suggestion, not evidence about the source transaction’s true origin. The exclusion score was 0.26, so the flow gate did not suppress it.
- `case-0278`: **ASIA MILES LIMITED SINGAPORE SG**, an unresolved-origin airline credit, received a 0.21 airline-fee score, below the fixed 0.25 threshold. The product policy says to suggest this plausible airline relationship and ask the user to confirm origin and fee type. It is not one of the 140 known issuer credits. The exclusion score was 0.04; this was a benefit-score miss rather than a refund veto.

The original private no-history run agreed with 469/469 decisions. These two obfuscated-payload decisions differ. This run changes several identifying fields together and makes fresh model calls, so it cannot isolate merchant aliases, geography, dates, numeric references, or inference variability as the cause. Semantic preservation does not imply identical model confidence. Do not present the original perfect replay score as the public fixture’s result.

One additional unsupported secondary candidate remains in raw pair diagnostics but is not the top suggestion. Multiple acceptable alternatives also fall below threshold. This bench evaluates one best suggestion, not exhaustive detection of every eligible benefit.

## Frozen request and decision policy

For each posted negative transaction, issue one `jev-1.14.0` request with two Choice questions: described credit flow and the best-fitting benefit (plus none). Supply the original/name descriptor, amount, shifted date, and available merchant/category/code/counterparty/location fields. Do not send related purchases, labels, detection rules, past matches, account identifiers, or adjudication text. Unknown origin or fee type alone need not suppress an identifiable covered merchant.

Ordinary code excludes a transaction when the combined refund/reversal, card-payment, shared-repayment, and balance-redistribution score is at least **0.80**. Otherwise emit the highest-scoring benefit at **0.25** or higher. Every suggestion requires user confirmation; these scores are not calibrated issuer-origin probabilities. No application writes, push notifications, or production model deployment were performed.

## Provenance, privacy, and review

The dataset is a pseudonymized replay of 289 source-history negatives plus 180 constructed cases. Origin and suggestion labels remain provisional agent judgments, with frozen V2 confirmation policy. Invented-benefit tests are explicitly constructed; plausible merchant credits are not relabeled as verified issuer benefits. Existing dev/validation/fresh/final/unseen cohort names record their historical roles. All are now exposed replay material, not a fresh holdout or population sample.

The [independent privacy review](jev-privacy-review.md) scans the actual publication files. The [independent meaning review](jev-meaning-review.md) checks preserved labels, candidate relationships, amounts, semantic wording, and historical regimes. Locations, niche merchants, numeric references, people, and source IDs are removed or replaced; dates change within month and known benefit regimes. Exact amounts, month/year, generic brands, and card products remain. This is **pseudonymization, not guaranteed anonymity**. Raw transactions, original-to-public mappings, credentials, purchase history, and private response caches remain outside Git.

## Reproduction and machine-readable evidence

The [published result JSON](jev-final-baseline-results.json) contains per-candidate scores, top decisions, usage, response categories, request hashes, and fixture/prompt hashes. The [fixture guide](../../backend/fixtures/jev/README.md) explains transformations and cohorts. The [public runner](../../backend/scripts/jev_public_bench.py) reuses the existing request builder and evaluator:

```sh
# Offline: verify the committed hashes, restore published responses into ignored cache,
# and recompute the report without API credentials.
python backend/scripts/jev_public_bench.py report

# Paid: send missing requests, then publish a complete run.
python backend/scripts/jev_public_bench.py run
python backend/scripts/jev_public_bench.py publish
```

Use Python 3.12+ with `python-dotenv` and `PyYAML`, or the existing backend environment. A run reads `TYPESAFE_API_KEY` from the environment or ignored root `.env`. Calls are serial, cached by exact request content, budget-reserved before dispatch, and never automatically retried. The historical cumulative experiment cap remains $4.99; a new checkout accounts for locally available caches and reservations, not a provider-enforced account balance.

Validation: all nine offline bench tests passed. A separate checkout of mainline, without the private snapshot or API credentials, restored the published scores and recomputed exactly the same summary, per-candidate diagnostics, and top decisions. Whitespace and local documentation-link checks passed.

See [the research index](README.md) for the complete timeline, sources, rejected rubrics, tradeoffs, and next-step limitations.
