# Clear rubric for a single credit

## Rubric (use the two existing choice questions)

Prefer the original bank description. Use this transaction and listed benefits. Do not infer history, enrollment, allowance, or credit origin.

**Flow:** Choose `refund_return_reversal` for explicit refund, return, or reversal wording, or a refund code. Choose `card_payment` for explicit card-payment wording; benefit credits are not payments. Choose `split_repayment` for explicit shared-expense repayment. Choose `balance_redistribution` for explicit internal balance transfer. Otherwise choose `other_credit`. Generic “credit” or “adjustment” does not establish an excluded flow.

**Benefit:** Return one slug or `none`. If the transaction names a credit program, choose its listed benefit, even when several cover the merchant. If the named program is absent, choose `none`. Otherwise choose a benefit only when the merchant fits documented coverage. Broad coverage includes its stated kinds of merchants; an “etc.” list need not name every merchant. A merely related category or ambiguous service name is insufficient. Unknown fee type or credit origin does not prevent a merchant-fit suggestion. If none fits, choose `none`. An exact amount matching a supplied, verified dated cap strengthens an existing fit; partial amounts may also fit. Without a verified cap hint, ignore amount. Do not calculate caps.

Suggest only for user confirmation; do not treat the choice as proof or recorded usage.

## Rationale

The flow question filters transactions whose own wording identifies a different purpose. The benefit question then gives the model one short path: explicit program, documented merchant coverage, or none. This should reduce broad category guesses while retaining merchant-only suggestions for confirmation. It cannot determine whether an ambiguous merchant credit was a benefit or a refund; that uncertainty belongs in the user confirmation step. Amounts serve as supporting evidence only when code supplies a verified dated cap.
