# Jev clear rubric arena — judge C

Scores are 0–5 (higher is better).

| Draft | Clarity / decision order | Observable-data grounding | Confirmation / product policy | Avoids category invention | Brevity | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 4 | 3 | 5 | 3 | 5 | 20 |
| B | 4 | 5 | 5 | 5 | 4 | 23 |
| C | 5 | 5 | 5 | 5 | 3 | 23 |

**Rank and vote:** B first, C second, A third. B gives the clearest short operational rubric; C supplies useful explicit precedence and examples, but spends more words and adds a questionable tie rule.

**Specific ambiguities:** A's “explicitly covered” merchant rule can turn broad documented coverage into a closed merchant list; its named-program rule does not specify which text field controls. A and C return `none` on indistinguishable matches, although a valid strongest fit should be selected when evidence differentiates them; a tie alone should not invalidate otherwise valid candidates. B does not explicitly rank original bank text above noisy PFC/MCC/location and leaves flow-label precedence implicit. C's “transfer/balance redistribution” could include a generic transfer; the internal redistribution must be explicit. All three could state more clearly that amount is supporting evidence only when a verified, dated cap hint is supplied and never proves program identity.

## Synthesis

Classify one posted negative transaction using its fields and supplied benefit definitions. Prefer original bank description/name; merchant and counterparty identify the merchant. PFC, MCC, and location do not prove issuer or credit origin. Do not infer history, enrollment, allowances, or purchase details.

Answer the two existing questions independently. **Credit flow:** use `refund_return_reversal` for explicit refund/return/reversal wording or a structured refund code; `card_payment` for explicit payment to the card; `split_repayment` for explicit shared-expense repayment; and `balance_redistribution` for explicit internal balance movement. Otherwise use `other_credit`. Read whole phrases: a refund of a payment is a refund; a named Saks or Dunkin benefit credit is not a card payment. Generic “credit” or “adjustment” proves no excluded flow.

**Benefit:** return one listed slug or `none`. An explicitly named program in original bank text takes precedence over overlapping merchant matches; if it is absent from the roster, return `none`. Otherwise require merchant fit to documented coverage. Broad coverage includes stated merchant kinds and nonexhaustive examples; category alone or an ambiguous service name is insufficient. Unknown credit origin or fee subtype does not defeat a covered merchant. Choose the strongest valid match when several fit. A supplied, verified dated cap match may strengthen an existing fit, never create one; partial amounts can fit. Ignore missing cap hints. Suggest for user confirmation only; never automatically record usage.
