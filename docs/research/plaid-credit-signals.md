# Plaid signals for issuer credits versus refunds

Researched October 30, 2026 against Plaid's current documentation and official API schema. No production requests, model calls, or application changes were made.

## Finding

**Plaid exposes useful additional evidence, but its documented Transactions object has no guaranteed US-card field that means “this is an issuer benefit statement credit.”** A named benefit descriptor can be strong evidence on its own. “Generic adjustment” was our benchmark rubric wording, not a field read from Plaid. The rubric should not demand additional issuer provenance when the descriptor already explicitly identifies the benefit.

That conclusion is an interpretation of the documented [Transactions response](https://plaid.com/docs/api/products/transactions/#transactionssync) and [official schema](https://github.com/plaid/plaid-openapi/blob/master/2020-09-14.yml), not a claim that every institution returns identical data.

## Fields worth preserving

| Field | Documented meaning and coverage | Implication for Perkle |
| --- | --- | --- |
| `original_description` | Institution's unparsed description; request with `options.include_original_description: true` on sync/get. | Best next field to inspect for lost issuer-credit/refund wording. Keep it alongside other names. |
| `transaction_code` | `refund` denotes merchant credit/return; `adjustment` denotes bank adjustment. Available for European and certain US institutions; otherwise null. | Potentially useful distinction, but no published guarantee for our specific US issuers. `adjustment` does not identify a benefit or exclude other adjustments. |
| `merchant_category_code` | Nullable, beta MCC field; primarily card transactions, institution-dependent coverage, values can change. | Categorizes merchant business; does not by itself establish issuer origin. |

These definitions and availability qualifications come from the [Transactions API reference](https://plaid.com/docs/api/products/transactions/). There is no documented benefit-credit transaction code in its enum. Actual population on our linked items has not been tested.

| Additional field | What it adds | Limit |
| --- | --- | --- |
| `counterparties[]` | Names, stable entity IDs, types including `financial_institution` and `merchant`, and confidence. | Extracted from description; confidence concerns involvement, not proof of who originated a credit. |
| `merchant_name`, `merchant_entity_id` | Enriched merchant identity; entity ID groups the broader merchant across locations. | Merchant recognition is not a benefit/refund distinction. |
| `personal_finance_category` | Primary/detailed intent classification, confidence, taxonomy version. | Intent inference is supporting evidence, not verified issuer provenance. |
| `payment_channel` | Online/in-store/other channel; replaces deprecated `transaction_type`. | `other` is not a benefit-credit flag. |
| `payment_meta` | Inter-bank transfer metadata, potentially payer/payee/reason. | Not guaranteed; fields are null for non-inter-bank transactions. Not a general card-credit originator record. |

The [official OpenAPI schema](https://github.com/plaid/plaid-openapi/blob/master/2020-09-14.yml) defines these fields. Plaid's enriched identities and categories are useful model inputs, but treating two description-derived classifications as independent confirmation would overstate the evidence.

`pending` and `pending_transaction_id` support settlement and deduplication. A pending record can be removed and replaced by a posted record with a different transaction ID. The latter field links pending to posted where matched; it is not a general link from refund or benefit credit to the original purchase. Some institutions, including Capital One, do not provide pending records. [Transaction states](https://plaid.com/docs/transactions/transactions-data/)

## What our integration retains

Read-only source inspection found the production Rust parser's `RawTxn` only includes transaction ID, account ID, date, `name`, and amount. The projection persists those with account context and ingestion time. The sync request does not enable original descriptions.

Sources: `perkle-ios/backend/src/plaid/plaid_client.rs` and `perkle-ios/backend/src/main.rs`.

Consequently, the existing production snapshot cannot tell us whether transaction codes, counterparties, MCCs, or original descriptions would have helped: they were discarded or never requested. A correction to earlier spike notes: stored Plaid **`name` is not `original_description`**. The normalized dataset's `raw_description` field copied stored `name`; its label does not establish that it contains the original institution string.

## Enrich is not an issuer audit trail

Plaid Enrich accepts locally held descriptions and returns merchant/counterparty/category enrichments. Its counterparty identities are also description-derived. It can help classify records, but cannot reconstruct a missing independent issuer-origin record from the same description. Its documented purpose is enriching data from one's own banking products or non-Plaid sources; first preserve the standard Transactions fields already available rather than adding this product to the spike. [Enrich API](https://plaid.com/docs/api/products/enrich/)

## Recommended next experiment

1. Inspect fresh full responses for a small set of explicit benefit credits, merchant-only credits, and explicit refunds across the linked issuers. Enable original descriptions; measure field population per institution. Do not assume optional fields are present because they exist in the schema.
2. Preserve both institution and enriched descriptions, transaction code, counterparties with confidence, categories with version/confidence, MCC, amount/currency, and pending relationships. The schema can be expanded without making these fields mandatory.
3. Compare the same frozen cases using descriptor-only and enriched inputs. Distinguish institution-supplied fields from Plaid's inferred annotations.
4. Retain an uncertainty outcome for genuinely underspecified records, but narrow its rubric: explicit benefit-credit wording should count as evidence; merchant-only credits and opaque adjustments can remain unresolved. Alternatively separate “which benefit does the descriptor refer to?” from “does the available evidence establish a received benefit credit?” and combine in code.

The Saks miss does not establish that an uncertainty option is inherently harmful. It establishes that the current prompt/model did not consistently use explicit descriptor evidence. Removing the option may force more matches while concealing uncertain merchant credits; that is a hypothesis to test, not a reliability improvement to assume.
