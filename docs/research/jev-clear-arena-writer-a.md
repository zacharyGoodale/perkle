# Jev: single-transaction rubric

Use only this transaction and supplied benefit definitions. Prefer original description/name; use merchant and counterparty names to identify the merchant.

## 1. Credit flow

Choose the first supported label:

1. `card_payment`: explicit payment-to-card wording, such as “AUTOPAY PAYMENT THANK YOU.” A card or program name plus “credit” is insufficient.
2. `balance_redistribution`: explicit balance redistribution or internal movement.
3. `refund_return_reversal`: explicit refund, return, or reversal wording, or a structured refund code.
4. `split_repayment`: explicit repayment of a shared expense.
5. `other_credit`: otherwise. A negative amount or generic adjustment proves none of the above.

## 2. Benefit suggestion

Return one candidate slug or `none`:

1. If text names a benefit program, choose only its matching candidate; otherwise `none`.
2. Otherwise, choose a candidate only when the identified merchant is explicitly covered by its definition. Merchant category, MCC, location, and amount alone cannot establish coverage.
3. Unknown purchase/fee subtype or credit origin does not disqualify a covered merchant. Do not assume either is known.
4. A supplied, verified exact cap match strengthens a match; it cannot create one. Partial amounts remain possible.
5. If multiple candidates remain indistinguishable, return `none`.

Suggestions require user confirmation. Never automatically record usage.

## Rationale

The ordered rules separate credit-flow evidence from benefit eligibility. Explicit merchant coverage blocks category-based substitutions without hardcoding merchants. Strongest weakness: merchant-only matches can still suggest unrelated credits or ineligible purchase subtypes. Confirmation handles that uncertainty; this classifier cannot resolve it from the allowed data.
