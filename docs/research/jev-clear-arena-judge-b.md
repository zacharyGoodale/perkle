# Independent judge B: Jev clear-rubric arena

## Vote

**C > B > A.** C gives the clearest evidence hierarchy and guards against mistaking PFC/MCC for issuer origin. B is compact and preserves broad documented coverage. A is concise but makes coverage too literal and abstains when multiple candidates are indistinguishable, even though the product needs one best suggestion.

| Candidate | Clarity / decision order | Observable-data grounding | Product-policy preservation | Avoids category hallucinations | Brevity | Total |
|---|---:|---:|---:|---:|---:|---:|
| A | 4 | 4 | 3 | 3 | 5 | 19/25 |
| B | 4 | 4 | 4 | 4 | 4 | 20/25 |
| C | 5 | 5 | 4 | 5 | 4 | 23/25 |

## Ambiguities and corrections

- All three omit the existing underlying gate at **0.8** and benefit threshold at **0.25**; the rubric must leave both unchanged.
- A's “explicitly covered” language could reject broad travel coverage or nonexhaustive examples. C and B handle these better.
- A and C say to return `none` for an indistinguishable tie. Choose the best supported slug when several are valid; do not abstain solely because alternatives exist.
- C should explicitly say merchant/counterparty names may identify the merchant, while noisy PFC/MCC/location are context only. Its program-name priority should not imply that a noisy category field proves program identity.
- “Refund of payment” should be read as a refund, while an explicit card payment is still excluded. Generic “credit” or “adjustment” is neither.

## Synthesized rubric

Classify one posted negative transaction using its original bank name/description and benefit roster. Original bank text outranks cleaned names; merchant and counterparty names identify the merchant. PFC, MCC, and location are context, not origin proof. Do not infer history, enrollment, remaining allowance, purchase subtype, or issuer origin.

Answer two questions. **Flow:** Select `refund_return_reversal` for explicit refund/return/reversal wording or structured refund code; read the full phrase. Select `card_payment` for explicit card-payment/autopay wording, `split_repayment` for explicit shared-expense repayment, and `balance_redistribution` for explicit internal redistribution. Otherwise select `other_credit`. Generic “credit” or “adjustment” proves no exclusion. Saks or Dunkin benefit credits are not card payments.

**Benefit:** Return one best slug or `none`. A named program takes priority; if absent from the roster, return `none`. Otherwise require merchant fit to documented coverage. Broad travel includes stated merchant kinds; examples and “etc.” are nonexhaustive. Category alone cannot establish fit: Fandango is not StubHub; generic Google Services is not an identified eligible provider. Unknown origin or fee subtype does not block a covered merchant, including generic airline credit for an airline incidental benefit. A supplied verified dated cap match only strengthens fit; partial credits can fit. Never calculate caps. Keep the underlying 0.8 gate and benefit 0.25 threshold. Suggest for user confirmation; never record usage automatically.

## Strongest remaining weakness

A single credit can identify a covered merchant without proving the underlying purchase or credit origin. The suggestion may be wrong; user confirmation is the necessary final check.
