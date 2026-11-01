# Public fixture meaning review

An independent review compared the published single-transaction fixture with the frozen private V2 fixture before the publication rerun. **Pass for the intended confirmation-suggestion task.** This review validates retained case meaning and labels; it does not assert identical model predictions after obfuscation.

## Checks performed

- All **469 cases**, **2,865 candidate-benefit judgments**, and **79 descriptor-family groups** remain represented. Case IDs are new sequential pseudonyms; family mapping is bijective. Splits, suite membership, candidate order, and frozen V2 suggestion labels are preserved.
- Original origin-evidence labels remain unchanged, including **140 explicit real-derived in-scope credits**. Unresolved-origin confirmation candidates remain unresolved; they were not upgraded to verified benefit receipts. Invented-benefit stress cases remain constructed cases.
- Amounts, credit signs, currency presence/values, pending status, card association, transaction codes, payment channel, MCC, and personal-finance category are unchanged. Exact cap matches, partial amounts, and monetary collisions therefore remain available to the model, although the selected prompt supplies no computed cap hints.
- Every posting date has a changed day within its original month and year. The review checked that dates retain their side of the July 25, 2024 and September 18, 2025 benefit-change boundaries. Month and year retain historical context; day-sensitive eligibility is not an evaluated target.
- For every original/name description, the counts of the semantic terms `refund`, `return`, `reversal`, `not`, `no`, `credit`, `payment`, `autopay`, `repayment`, `split`, `redistribution`, `adjustment`, `reimbursement`, and `reimbursed` are unchanged. Changed descriptors were also inspected manually; important negations and explicit program names survive.
- Niche hotel, home-goods, apparel, and dining merchants use analogous invented identities. Associated hypothetical benefit names, notes, and slug/label references change consistently. Generic brands needed for actual benefit recognition remain recognizable. Location and numeric-reference substitutions retain the merchant/event wording rather than adding evidence of a benefit or refund.
- Candidate metadata other than merchant identity text, renamed hypothetical slugs, and removed detection rules remains unchanged. Label keys exactly match each case's candidate roster. Detection patterns and adjudication prose are absent from the published fixture.
- All 469 generated requests use only the target transaction as state. Expected labels, descriptor families, detection rules, and transaction history are not sent. The runner uses the selected single-transaction template, the frozen **0.25** benefit threshold, the **0.80** combined exclusion threshold, and the existing one-top-candidate evaluator.

## Scope and limits

Related purchases were deliberately omitted because the selected approach does not use them. The public fixture cannot reproduce earlier experiments that depended on purchase context; those historical scores refer to private snapshots. Existing family splits are preserved for traceability, but all cases have already been exposed during development and are replay material.

The substitutions retain the distinctions needed by this task, not every possible transaction-analysis use. A different location-specific benefit, day-specific eligibility test, merchant-entity resolver, or purchase-history algorithm would require its own validation. Invented merchants can change a language model's recognition and confidence even when category and label meaning are retained. The paid publication rerun must therefore be reported independently, with any changed decisions and no retrospective label edits.

This review is separate from the [privacy review](jev-privacy-review.md). Preserving semantic meaning does not make the dataset anonymous; see the [research index](README.md) and [final baseline report](jev-final-baseline.md) for publication limitations and rerun results.
