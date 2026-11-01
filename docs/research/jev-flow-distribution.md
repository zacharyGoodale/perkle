# First-question flow response distributions

This is an offline analysis of the saved selected full-context run: `jev-confirmation-winner.json`, model `jev-1.14.0`. No new API calls or prompt changes were made. Counts are transaction-weighted, not independent descriptor families.

The primary positive cohort contains the 140 clear real credits for the evaluated auto-detection benefits, spanning 17 descriptor families. The 289-real-transaction cohort includes those credits, other issuer credits, payments, and merchant credits of unresolved origin. The full 469-case bench additionally includes 180 synthetic stress cases.

## Raw winning response

| Flow label | Clear in-scope benefit credits | All real negative transactions | Full bench, including synthetic |
| --- | ---: | ---: | ---: |
| Other credit | 132 (94.3%) | 201 (69.6%) | 337 (71.9%) |
| Card payment | 8 (5.7%) | 86 (29.8%) | 94 (20.0%) |
| Refund / return / reversal | 0 | 0 | 28 (6.0%) |
| Split repayment | 0 | 1 (0.3%) | 3 (0.6%) |
| Balance redistribution | 0 | 1 (0.3%) | 7 (1.5%) |
| Total | 140 | 289 | 469 |

All eight misclassified clear credits were card-payment predictions: six of the 14 Dunkin credits whose original description says `AMEX DUNKIN' CREDIT`, and both `Shop Saks with Platinum Credit` records. This is a repeatable family-level weakness, not a single Saks anomaly. All other 15 clear-positive descriptor families had `other_credit` as the winning flow label throughout.

There are also 28 explicit `Platinum Walmart+ Credit` records outside the evaluated auto-benefit positive cohort. Every one was labeled `other_credit`. Including these yields 168 named issuer credits: 160 other-credit predictions (95.2%) and the same eight card-payment mistakes (4.8%).

## Combined exclusion score

The policy sums the four excluded-flow choice scores and rejects at 0.80. That score is not a calibrated probability of origin.

| Score band | Clear benefit credits (140) | All real negatives (289) | Full bench (469) |
| --- | ---: | ---: | ---: |
| Below 0.10 | 119 | 139 | 242 |
| 0.10 to below 0.50 | 12 | 61 | 93 |
| 0.50 to below 0.80 | 9 | 14 | 19 |
| At least 0.80 | 0 | 75 | 115 |

For the 140 clear credits, the median exclusion score is **0.01**, mean **0.073**, and maximum **0.62**. The two difficult Saks records score 0.51 and 0.53; Dunkin spans 0.30–0.62. A 0.50 sum-score gate would incorrectly suppress nine clear credits; the frozen 0.80 gate suppresses none, including none of the 28 additional Walmart credits.

## Known exclusion events and limits

The real history has 77 explicitly worded card payments. Jev labels 73 as card payments and all 73 exceed the rejection threshold. The remaining four say `MOBILE PAYMENT - THANK YOU` but are labeled `other_credit`, with exclusion scores 0.33–0.40, and pass the flow gate. The second benefit-choice question produces no matching benefit for them, so the combined recommendation remains a withhold.

The explicitly named split repayment and the redistribution with an offsetting debit are correctly labeled and rejected, scoring 0.93 and 0.99 respectively. Thus the first gate alone catches **75/79** of these clearly identified real exclusion events (94.9%) and rejects none of the named issuer credits. This does not establish exclusion recall for merchant refunds with opaque descriptions.

No real transaction is labeled refund/return/reversal. That must not be interpreted as no real refunds: the known merchant-credit examples often lack refund wording, and their origin is not independently confirmed. The first question is deliberately an affirmative-evidence filter, not a general determination that a credit really came from an issuer rather than a merchant.

The flow question is useful as a conservative veto with separately measured errors. Its raw category should not be trusted as a complete classification. Overall notification correctness depends on both stages and the thresholds; it does not mean each intermediate classifier is correct.

Private cohort details and exact scores are in `backend/data/jev-hillclimb/flow-distribution-analysis.json`. The recommendations and prior full-context results remain unchanged.

## Offline gate ablation

Replaying the frozen winning scores without new model calls yields:

| Decision policy | Notifications | Unsupported top suggestions | Missed eligible transactions | Changes among 289 real transactions |
| --- | ---: | ---: | ---: | ---: |
| Frozen combined exclusion gate | 290 | 0 | 0 | 0 |
| Subtract refund/return/reversal score from exclusion gate | 311 | 21 | 0 | 0 |
| Disable entire exclusion gate | 313 | 23 | 0 | 0 |

All 21 additional suggestions after removing the refund contribution are synthetic explicit-refund/reversal cases; all 23 after removing the whole gate are synthetic. This demonstrates a benefit on constructed affirmative-evidence cases, not measured sensitivity to opaque real merchant refunds. The highest refund/return/reversal score among the 140 clear real benefit credits is 0.08, and none is suppressed by the current combined 0.80 gate.

This is a score-level ablation: the original flow question remains in the saved requests, and benefit-choice scores are held fixed. It does not measure how removing that question from the prompt would change Jev's remaining answers. Private changes are saved in `backend/data/jev-hillclimb/flow-gate-ablation.json`.
