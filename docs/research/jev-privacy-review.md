# Publication privacy review

**Result: no blocking identifying-data finding in the reviewed publication bundle.** This is an independent review of the 61 staged files in the publication checkout before this report was added, including the 469-case fixture, scripts, historical notes/prompts, and final baseline results. The staged blobs matched their working-tree files during review.

## Checks performed

- Inspected all distinct transaction names, original descriptions, merchant names, locations, and counterparty entries in the public fixture. Sensitive local merchants and geographic details use replacements; retained unmodified descriptions are generic program/payment wording. Generic national brands remain intentionally available for benefit-coverage reasoning.
- Confirmed case and descriptor-group identifiers are publication pseudonyms. Account, user, Plaid item, transaction, merchant-entity, and source-provenance identifiers are absent from exported transaction records. No related purchase history or private identity mapping is published.
- Compared the exact staged text against 1,965 distinct identity-token values collected from the private source snapshot: **zero matches**. This includes long source account, transaction/external, pending-transaction, and merchant-entity identifiers.
- Scanned staged text for personal local paths/names, original home-location terms, credential formats, authorization tokens, and deployed AWS resource identifiers: **zero findings**. Environment-variable names and synthetic test placeholders are not credential values.
- Confirmed all 469 published transaction date days differ from the private fixture. Calendar months/years and monetary amounts are retained intentionally; numeric store/ticket references are replaced.
- Inspected the final results envelope and all response-key shapes. The 466 response entries contain request-content hashes, model answers/category scores, token usage, and elapsed timing. They contain no API customer/user identifiers, raw request bodies, authorization headers, or source account/transaction identifiers. Pair/recommendation rows reference only public case/group identifiers and benefit labels.

## Scope and residual risk

The source data, `.env`, exporter and substitution mapping, raw snapshots, and private response caches remain outside the staged publication. Unrelated untracked workspace files were not approved by this review.

This bundle is **pseudonymized, not anonymous**. Exact amounts, calendar month/year, public merchant/program brands, benefit roster, and repeated-event patterns remain because they support the experiment's meaning. Someone with external knowledge could potentially link those features to a person. Mixing constructed examples with real-derived cases does not eliminate that risk. This review supports the user's requested obfuscated research publication; it does not certify irreversible anonymization.

The privacy review does not establish semantic equivalence or model quality. See the [meaning review](jev-meaning-review.md) and [final baseline report](jev-final-baseline.md) for those checks.
