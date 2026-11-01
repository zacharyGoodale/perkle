# Independent rubric judgment

**Vote: B. Ranking: B > C > A.** Identity of the writers played no role.

| Draft | Clarity / decision order | Observable evidence | Product policy | Avoid category hallucination | Brevity | Total |
|---|---:|---:|---:|---:|---:|---:|
| B | 5 | 5 | 4 | 5 | 4 | 23/25 |
| C | 4 | 5 | 3 | 5 | 4 | 21/25 |
| A | 4 | 4 | 2 | 4 | 5 | 19/25 |

B best preserves the intended merchant-fit policy, explicitly includes broad coverage and nonexhaustive examples, and avoids the other drafts' mandatory abstention for equally fitting benefits. Its strongest weakness is that it never positively instructs the model to select the best candidate when several fit. Its rationale also says the benefit question comes “then,” which can be misread as making benefit classification conditional on flow; the API must keep those questions independent.

C provides useful concrete distinctions: named Saks/Dunkin credits are not payments, and generic airline credits may suggest incidental benefits. However, “if tied, none” explicitly contradicts the requested selection policy. “Original ... outranks” all other fields could also suppress genuinely explicit structured refund evidence; field precedence should aid merchant interpretation, not erase flow evidence. Its cap formulation adds implementation detail the weaker model does not need.

A has the most consequential problems: “explicitly covered” encourages treating illustrative merchant lists as closed, and “indistinguishable ... none” violates the multiple-valid-benefit rule. Its card-payment-first flow priority can misclassify a phrase such as “refund of payment.” All drafts would benefit from explicitly preserving existing thresholds outside the model's evidence rules.

## Compact synthesis (216 words)

Use only this transaction and supplied benefit definitions. Prefer original bank description/name; use merchant and counterparty fields to identify the merchant. Do not infer history, purchases, enrollment, remaining allowance, or credit origin.

Answer both existing questions independently.

**Flow:** Read the full phrase. Explicit refund/return/reversal wording or a supplied structured refund code → `refund_return_reversal`; explicit payment-to-card → `card_payment`; explicit shared-expense repayment → `split_repayment`; explicit internal balance movement → `balance_redistribution`; otherwise `other_credit`. “Refund of payment” is a refund. Named Saks/Dunkin benefit credits are not card payments. Negative amounts and generic “credit” or “adjustment” establish no excluded flow.

**Benefit:** Return the best one candidate slug or `none`:

1. An explicitly named credit program selects its matching roster benefit. If absent, choose `none`.
2. Otherwise require merchant fit to documented coverage. Broad coverage includes stated merchant kinds; examples and “etc.” are nonexhaustive. Shared category alone does not connect Fandango to StubHub, or Google Services to digital benefits.
3. Unknown origin or fee subtype is acceptable when merchant fits: generic airline credit can suggest airline incidental coverage.
4. A supplied verified cap match strengthens existing fit, never creates it; partial credits remain possible.
5. If several fit, choose best; if none fits, choose `none`.

Preserve existing conservative 0.8 flow veto and 0.25 suggestion threshold. Suggestions require confirmation; never automatically record usage.
