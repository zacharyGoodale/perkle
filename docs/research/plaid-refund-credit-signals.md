# Distinguishing refunds from issuer benefit credits

Researched October 31, 2026. Primary sources checked: current Plaid Transactions documentation and official OpenAPI schema, Plaid transaction-state and Transfer documentation, and Stripe's first-party refund documentation. No production requests, paid model calls, or application changes.

## Finding

There is no documented universal issuer-benefit flag or general refund-to-original-purchase link in Plaid Transactions. This is an inference from the reviewed public transaction schema, not a claim about private issuer/network data. The available evidence supports a conservative explicit-evidence veto rather than trying to infer refund origin from an otherwise plausible merchant credit. [Official Plaid schema](https://github.com/plaid/plaid-openapi/blob/master/2020-09-14.yml)

## What can actually distinguish them?

| Signal | Documented meaning | Treatment for Perkle |
| --- | --- | --- |
| `transaction_code = refund` | Merchant credit/return; populated in Europe and certain US institutions. | Strong structured clue when present; coverage is incomplete and Plaid does not promise perfect classification. |
| `transaction_code = adjustment` | Bank adjustment. | Does not establish a merchant return; never reject a plausible benefit merely for this code. |
| `original_description` | Institution-provided description, requested explicitly. | Preserve explicit refund/return wording and explicit issuer-program wording. |
| `counterparties` | Extracted from the raw description. | Bank or merchant identity is supporting evidence, not independent proof of who originated the credit. |

These definitions and availability limits come from the [Transactions API reference](https://plaid.com/docs/api/products/transactions/). A deterministic rule reading an explicit code is more transparent than an inferred origin label, but is still limited by the correctness of its input.

Amount sign only identifies money direction: payments and refunds can both be negative. Merchant entity IDs identify a broader merchant, not a particular purchase or its reversal. MCC describes merchant activity; personal-finance categories describe inferred intent. Payment channel describes how the payment occurred. Inter-bank `payment_meta` is not a general card-network provenance record. Neither these fields nor their combinations document a guaranteed distinction between an issuer reimbursement and merchant refund. [Official schema: Transaction, TransactionCode, PersonalFinanceCategory, PaymentMeta](https://github.com/plaid/plaid-openapi/blob/master/2020-09-14.yml)

## Pending links and removals are not refund links

Plaid's `pending_transaction_id` matches a posted transaction to its preceding pending record when possible. A pending record normally appears in `removed` when its posted replacement appears in `added`; authorization holds can also disappear without posting. Posted transactions can change for refunds or recategorization. Consequently, a removal or modification event alone is not a deterministic refund event. Apply sync changes to keep records accurate, but do not interpret every disappearance as a merchant return. [Plaid transaction states](https://plaid.com/docs/transactions/transactions-data/)

## How systems with authoritative evidence do it

Payment processors can retain an explicit reference to the original payment. Stripe's refund object has `charge` and `payment_intent` references identifying what was refunded. That establishes a relationship rather than guessing from equal amounts and merchant names. [Stripe's official Refund object source](https://github.com/stripe/stripe-php/blob/master/lib/Refund.php)

Stripe also exposes a refund/reversal type and, when available, ARN/STAN/RRN references for tracing refunds. Some reversals remove the original charge without issuing a separate credit. These are processor/issuer workflow details; the examined Plaid Transactions schema does not expose a general equivalent charge-linked refund object. Perkle cannot obtain a third-party merchant's processor records merely by connecting the user's card account. [Stripe refund/reversal and tracing documentation](https://docs.stripe.com/refunds#refund-and-reversal)

Plaid's own Transfer refund APIs do have original `transfer_id` relationships, but those concern ACH transfers initiated through that product. They are not an extra lookup for arbitrary historical card purchases. [Plaid Transfer refunds](https://plaid.com/docs/transfer/refunds/)

## Implications for our actual history

The refreshed snapshot has zero `refund` transaction codes among 289 negative transactions. Merchant/category fields overlap between credits of uncertain origin and named issuer benefits. Six unresolved merchant credits have an exact same-merchant prior purchase within 30 days; so do 42 explicitly named benefit credits. Thus purchase matching cannot be a hard refund rule in this data. A benefit reimbursement is often expected to match the reimbursed purchase. [Local refreshed-data analysis](plaid-enriched-production-patterns.md)

The cached winning bench supplies a useful separation between real evidence and synthetic coverage:

- Current conservative combined gate suppresses **0/140** clear in-scope real credits and **0/168** named issuer credits including Walmart+.
- Removing the refund contribution changes **no real-history suggestions**, but allows **21 additional unsupported suggestions** in synthetic cases with explicit refund/reversal evidence.
- Removing the whole flow gate allows 23 additional unsupported synthetic suggestions. This is not a measured real-world refund false-positive rate.

These are offline ablations of existing responses, with no new model calls. See [gate distribution and ablation](jev-flow-distribution.md).

## Recommendation

Keep an explicit refund check, but do not ask it to resolve unsupported origin ambiguity. Suppress a plausible benefit suggestion only for clear affirmative evidence, such as unambiguous merchant-return wording or a meaningful explicit refund code. Avoid a broad substring rule for “return,” “credit,” “reversal,” or “adjustment”: those words can have other meanings, including benefit-credit reversals or product descriptions. Conflicting explicit benefit and refund evidence merits review rather than an automatic rule claiming certainty.

For merchant-only credits, missing metadata, or same-amount prior purchases, continue to the benefit question and ask the user to confirm origin. Exact benefit amounts and recurrence can strengthen a suggestion, but cannot prove issuer origin. Evaluate any deterministic replacement against the existing explicit-refund synthetic cases before changing the winning prompt; current ablation does not establish that removing the veto is harmless outside this user's sparse real refund evidence.
