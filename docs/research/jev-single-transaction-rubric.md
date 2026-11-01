# Single-transaction rubric: final simplification experiment

The user approved a final experiment removing related purchases and comparing a signal rubric before selecting an initial confirmation-only solution. No production changes or notifications are authorized by bench recommendations.

## Frozen comparison

Both new arms use the same 469 frozen cases, V2 labels, one-top recommendation policy, benefit threshold 0.25, and combined exclusion threshold 0.80. Real transactions and synthetic stress cases are reported separately. Earlier validation and challenge cases have been exposed in prior rounds; these results are replay performance, not a fresh holdout or population accuracy estimate.

- Reference: selected full-context `prompt-10-final.json`, including related purchases.
- Control: `prompt-12-no-history-control.json`, identical reference instructions but `related_transactions` omitted entirely.
- Rubric: `prompt-12-rubric-no-history.json`, no transaction history; explicit ordered evidence rubric, original description precedence, conservative structured-refund evidence, and posting-date-versioned amount hints. Explicit redistribution wording can identify a balance movement without retrieving offsetting debits. Generic adjustments do not suffice.

The rubric is an intentional combined prompt/metadata experiment; its comparison to the no-history control does not isolate the marginal effect of amount hints from the wording changes. No thresholds or golden labels will be tuned after observing this round.

## Amount scope and limitations

Only explicitly supported USD cap versions are supplied; all other candidates receive `cap_version_known: false`. Cap selection uses the credit posting date because original purchase date is unavailable; it is supporting evidence, not verified historical eligibility. Remaining allowance is always unknown. Currency is checked and equality uses decimal arithmetic. No golden labels or string-matching detection patterns enter requests.

The small cap catalog covers Gold dining ($10/month), Resy ($50/semiannual), and Dunkin ($7/month) for the bounded August 2024–June 2026 window, Platinum Saks ($50/semiannual) for 2024–2025, and Platinum Resy ($100/quarter) from October 2025 through this experiment's date. Boundary exclusions deliberately avoid launch periods and later changes; they do not assert that the benefits were absent outside these windows. Other cap versions, including digital entertainment's historical change, remain unknown rather than using stale configuration values.

Sources: [Amex Gold launch announcement](https://www.americanexpress.com/en-us/newsroom/articles/products-and-services/american-express--updates-u-s--consumer-gold-card-with-new-benef.html), [issuer announcement reproduced on WebWire](https://www.webwire.com/ViewPressRel.asp?aId=324706), [issuer Saks announcement reproduced on WebWire](https://www.webwire.com/ViewPressRel.asp?aId=225833), [Resy September 2025 announcement](https://blog.resy.com/newsroom/new-resy-benefits-are-added-to-american-express-u-s-consumer-and-business-platinum-cards/).

Exact amount supports an existing merchant/program connection; it cannot create one or override an explicitly different program. Partial credits are allowed. Missing metadata, unknown origin and generic adjustments do not veto plausible suggestions. Final selection always requires user confirmation before usage is recorded.

The reproducible rubric template is `docs/research/jev-single-transaction-rubric.json`. Private responses and per-case results remain under ignored `backend/data/jev-hillclimb/`.

## Results and selection

| Arm | Known real credits recovered | Correct real decisions | Correct constructed decisions | Correct total decisions | Unsupported top suggestions | Input tokens | Run cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Prior full-context reference | 140/140 | 289/289 | 180/180 | 469/469 | 0 | 971,715 | $0.040812 |
| Existing prompt, no history | 140/140 | 289/289 | 180/180 | 469/469 | 0 | 886,377 | $0.037228 |
| Added rubric and limited cap hints, no history | 140/140 | 286/289 | 180/180 | 466/469 | 3 | 1,107,342 | $0.046508 |

No-history control emits exactly the same benefit/null recommendation as the full-context reference for every case: 166 suggestions among 289 real negative transactions, and 124 among 180 constructed cases. It uses 8.78% fewer tokens than the reference. Removing history allows additional identical requests to share a cache entry: both new runs have 466 distinct requests for 469 cases, compared with 468 for the reference.

The rubric's three additional, unsupported real suggestions are Shake Shack → Gold dining, Fandango → StubHub/viagogo, and generic Google Services → digital entertainment. Their benefit scores are 0.47, 0.27, and 0.28 respectively; all pass the frozen exclusion threshold. These are unsupported benefit connections under the frozen suggestion rubric, not independently proven merchant refunds. The rubric uses 24.93% more input tokens than the no-history control. Because wording, amount hints and redistribution evidence wording changed together, this does not establish that amount matching itself caused the errors.

**Select the existing prompt without transaction history as the initial confirmation-only approach.** The exact template is `jev-confirmation-single-transaction.json`. Keep the rubric variant as an experiment, not a selected winner. No cap-hint lookup or related-purchase retrieval is required by the selected request. No production deployment was performed.

The selected variant retains the reference's raw per-benefit limitations: 291 true-positive pairs, one unsupported secondary pair, and 20 omitted valid alternative pairs out of 2,865. Only one top candidate may be shown; this is not exhaustive benefit classification. All 140 clear real credits are recovered. The 26 additional real suggestions have unresolved origin and require user confirmation; their inclusion is not proof they are issuer benefits.

Amount coverage in the rubric arm: 237 real transactions have at least one verified candidate cap hint; the correct benefit has a hint for 43/140 clear credits, with exact full-cap equality in 34. Candidate coverage is not ground-truth leakage: hints depend only on card, named benefit, posting date, currency and amount, never expected labels.

The two new runs cost an estimated $0.083736 in billed input tokens. Total recorded hill-climb usage is approximately $1.07736, plus $0.001615 conservatively retained for two initial network-unavailable attempts. Those failed attempts were retained as separate reservations before one network-enabled attempt per arm. Nine offline tests pass, covering currency/date boundaries, decimal amount equality, no-history request construction and the existing recommendation/budget behavior.
