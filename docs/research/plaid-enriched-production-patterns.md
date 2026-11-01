# Refreshed production Plaid evidence — October 30, 2026

## Deployment and refresh

Backend commit **`31e132a32e65a175a20bf2b36cbc1a7f783d8143`** preserves Plaid's optional transaction fields through parsing, client responses, and DynamoDB persistence, and enables `options.include_original_description` for sync. Optional metadata is retained verbatim, including nulls and false values. All **70 Rust tests** passed. The production Lambda deployment completed, its downloaded binary matched the tested build, and its health check passed.

The original backend checkout was fast-forwarded to the commit on `feat/missed-credit-suggestions`; existing staged and unstaged user patches remained byte-identical. No push or main-branch change was performed. The standard SAM deployment also activated previously committed detection-miss table/API/IAM wiring from baseline HEAD, beyond the metadata patch. No resource deletions or replacements occurred.

A metadata-only historical backfill requested full Plaid transactions with original descriptions and conditionally updated existing production records. All **1,565 transactions**, including **289 negatives**, were updated with **zero conditional skips**. Readback verified unchanged transaction core fields, row counts, and sync cursors. No old negative transaction lacked metadata. Root separately verified every exported metadata map against the retrieved Plaid metadata.

Private evidence, source responses, normalized readback, and scripts live in the Git-ignored `backend/data/jev-enriched-production/` directory. The earlier dataset and Jev results remain frozen. No new Jev calls were made for this work.

## Actual field coverage on negative transactions

| Card | Negatives | Raw description | Non-null transaction code | Nonempty counterparties | Non-null MCC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Amex Platinum | 171 | 171 | 31 | 26 | 0 |
| Amex Gold | 80 | 80 | 11 | 48 | 0 |
| Chase Sapphire Reserve | 27 | 27 | 0 | 0 | 4 |
| Venture X | 11 | 11 | 6 | 9 | 3 |
| Total | 289 | 289 | 48 | 83 | 7 |

All 289 negatives have pending state, category, payment channel, and currency. All are **non-pending** in the retrieved response. Raw bank descriptions differ substantively from stored Plaid names on **61/289** negatives, including **24/44** previously ambiguous cases. Counts compare case-folded, trimmed strings.

## Useful discovery: merchant cleanup removed benefit wording

All **14 Gold Dunkin cases** that previously had merchant-only Plaid names have raw bank descriptions explicitly naming the Amex Dunkin credit. Their counterparties include both Dunkin as a merchant and American Express as a financial institution. This supplies direct descriptor evidence for the previously missing Gold Dunkin positive coverage.

This is the strongest concrete reason to preserve both `name` and `original_description`: merchant cleanup can remove exactly the issuer-benefit language the classifier needs. Prefer the original description as a primary input; provide the cleaned name alongside it. The old provisional labels remain unchanged for reproducibility; a future label version can resolve these 14 cases using the new evidence.

## Fields that do not provide a universal shortcut

**Transaction codes are sparse and do not reliably separate these credits.** Of 289 negatives, 241 have no code; 34 say `purchase`, 12 `payment`, and two `adjustment`. None says `refund`. Among the 126 already explicit benefit-credit examples, **24 say `purchase`**. The two `adjustment` records are merchant credits on Venture X, not autopay records (corrected after row-level review). A `purchase` code must not override a negative amount and explicit credit wording.

**Counterparties are supporting context.** Most previously explicit benefit credits lack financial-institution counterparties, and payments can have them. Chase returned no counterparties for any of its 27 negatives. A bank identity can strengthen a named credit interpretation but cannot be required or treated as proof of a benefit. As the [prior research](plaid-credit-signals.md) explains, these identities are extracted by Plaid from descriptions, not an independent issuer-origin audit trail.

**MCCs are too sparse to route benefit credits reliably.** Only seven negatives have MCCs, and none of the 126 previously explicit benefit examples does. They are useful merchant-category evidence when available, not an issuer-credit flag.

**Categories describe inconsistent aspects of credits.** Chase dining credits are categorized as incoming transfers; Chase travel credits fall under other; Platinum Resy credits also fall under other. Some digital entertainment credits fall under video games. Filtering to dining/travel/entertainment categories before considering benefits would discard valid named credits. Category confidence is not proof of benefit eligibility or origin.

**Inter-bank payment metadata adds nothing to these negatives.** None of the 289 negative records has meaningful `payment_meta` values.

## What remains unresolved

For the missed Saks variant and Chase dining examples, the original descriptions retain the same explicit credit wording already present in their Plaid names. Neither has a transaction code, merchant identity, MCC, or counterparty identifying the issuer. These remain prompt/model recognition failures rather than failures caused by discarded raw descriptions.

The Equinox merchant-only credits, merchant-only CLEAR cases, generic balance adjustment, and several merchant refunds/credits still lack explicit issuer-benefit wording. Richer metadata does not justify relabeling all of these as benefits. Uncertainty remains useful for genuinely underspecified records, while explicit issuer-credit wording should be accepted as descriptor evidence.

## Recommended next Jev comparison

Keep `amount < 0` and actual-card selection as deterministic candidate filters. Compare the same frozen cases with original description plus cleaned name, and optionally counterparties/categories/codes as supporting context. Do not hard-gate on MCC, category, transaction code, or bank-counterparty presence. Score an updated, evidence-versioned label set separately from the old benchmark, especially for the 14 newly resolved Dunkin cases. No richer-input accuracy result has been measured yet.

## Follow-up: purchase context for refund candidates

Row-level review found merchant credits matching earlier purchases, including an exact reversal and a credit equaling the sum of two earlier purchases on the same account. A separate literal balance-adjustment credit has an equal same-day debit on the same account, strongly suggesting an internal balance redistribution. These are contextual signals rather than universal field flags.

For this review, the 289 negatives were provisionally grouped into 168 explicitly named benefit credits (including the out-of-catalog Walmart benefit), 77 card payments, one split reimbursement, one literal balance adjustment, and 42 remaining merchant credits of unresolved origin. These are descriptive review cohorts, not independently confirmed refund labels. Both merchant refunds/candidates and explicit benefit credits can have `purchase` codes, merchant counterparties, or no enrichment at all. All have payment channel `other`.

Six of the 42 unresolved merchant credits have a same-account, same-merchant, exact-amount prior purchase within 30 days; so do 42 of the 168 explicit benefit credits. Matching checks use merchant entity ID or an exact normalized descriptor, a nonnegative day difference, and cent-exact amount equality. A same-amount purchase match is therefore useful review context but cannot by itself establish a refund. Private examples and full Saks/Nordstrom payloads are saved alongside the refreshed snapshot.
