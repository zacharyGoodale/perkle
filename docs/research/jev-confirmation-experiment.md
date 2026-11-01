# Narrow refund exclusions and confirmation suggestions

This run compares the frozen `evidence` prompt with a new `confirmation` prompt on exactly the same 289 real negative transactions and 33 synthetic stress cases. The fixture hash and provisional labels are unchanged. No application behavior changed and no notifications were sent.

The new prompt permits plausible merchant/program matches for user confirmation. It requires affirmative refund/return/reversal or payment wording, or identified balance redistribution supported by an offsetting debit, to reject on those grounds. A matching prior purchase, missing issuer identity, purchase transaction code, or generic adjustment wording alone cannot establish a refund. Insufficient evidence now means missing merchant/program connection or genuinely conflicting affirmative signals, rather than merely a hypothetical refund.

This tests the combined wording change, including a more permissive match definition; it does not isolate the causal effect of the refund sentence alone. The same rich transaction fields and prior-purchase context are supplied. Current/historical cap arithmetic remains excluded because historical benefit limits are not yet verified. Labels and detection patterns are not supplied to Jev.

Before the paid run, the confirmation suggestion threshold was set to `P(match) >= 0.50`, with `0.20` as an inclusive comparison. These are uncalibrated experimental thresholds, not correctness guarantees. Neither policy automatically records benefit use. The previous prompt is evaluated at these same thresholds for comparison; its older auto-record/review policy is not the comparator.

| Real transaction results | Previous, 0.50 | New, 0.50 | Previous, 0.20 | New, 0.20 |
| --- | ---: | ---: | ---: | ---: |
| Correct benefit suggestions / 140 clear credits | 134 | 139 | 140 | 140 |
| Transactions with any suggestion / 289 | 134 | 147 | 146 | 154 |
| Highest-ranked suggestions labeled clear match | 134 | 139 | 140 | 140 |
| Highest-ranked suggestions with unresolved origin | 0 | 8 | 6 | 14 |
| Highest-ranked suggestions labeled known non-match | 0 | 0 | 0 | 0 |
| Positive descriptor families reached / 17 | 16 | 17 | 17 | 17 |

Notifications are grouped by transaction; the highest-match-probability benefit is the top suggestion. Ranking was analyzed after the run, not separately validated as a production policy. At 0.50 the new prompt also suggests seven wrong benefit candidates, all Amex Resy credits matched to the separate dining benefit. Each transaction has a higher-ranked correct Resy suggestion. Showing every qualifying candidate would therefore surface seven known mistakes; the top-suggestion result must not be described as absence of wrong candidate predictions.

The eight unresolved top suggestions are five New York Times, two Equinox, and one CLEAR credits. They are not proven refunds or proven benefit credits. User confirmation is needed. Repeated descriptions and one user's history limit independence and generalization; all gold labels remain agent-adjudicated rather than independently user-reviewed.

All 14 Dunkin credits qualify at 0.50 (match probability 0.53–0.96), and Chase dining credits reach approximately 0.82–0.83. The two `Shop Saks with Platinum Credit` records rise from approximately 0.20–0.23 to 0.43 and 0.50. One remains below the primary threshold. The prompt improves this recognition failure but does not completely solve it.

For the synthetic target benefits, both prompts at 0.50 hide all 11 explicit refunds, suggest all 11 explicit issuer credits, and withhold all 11 actual merchant-only credits under invented benefits. At 0.20 the new prompt suggests six of the 11 merchant-only cases, whereas the old prompt suggests none. Those six have unresolved origin, not independently proven refund labels. These synthetic results test prompt behavior, not real-world refund frequency or accuracy.

The result supports a confirmation-first pilot with one ranked benefit suggestion per transaction. It does not justify automatic recording. The previous prompt at 0.20 also captures every clear credit with fewer unresolved suggestions than the new prompt at either tested setting, so the new prompt is not an unqualified improvement. Threshold and wording need evaluation on fresh user-reviewed examples before choosing a production policy. Manual rejection/addition and notification batching remain product work.

Model `jev-1.14.0`: 321 unique requests for 322 cases, 1,387,896 billed input tokens, estimated cost **$0.058292**, median latency **105 ms**, maximum **456 ms**. Five offline checks pass. Initial sandbox network failure sent no successful requests; the authorized network-enabled run completed. Existing evidence results remain untouched.

Private requests, responses, fixtures, and comparison metrics are in Git-ignored `backend/data/jev-evidence-experiment/`. Reproduce with:

```sh
backend/.venv/bin/python backend/scripts/jev_bench.py run \
  --data-dir backend/data/jev-evidence-experiment --prompt confirmation \
  --max-cases 400 --max-usd 0.25
backend/.venv/bin/python backend/scripts/jev_confirmation_report.py
backend/.venv/bin/python -m unittest discover -s backend/scripts -p 'test_*.py'
```
