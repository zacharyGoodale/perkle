# Blinded prompt arena candidates

Task: classify negative posted Plaid transactions against candidate benefit credits for user confirmation, never automatic usage recording. Inputs include original bank description, cleaned name, merchant/category/code/counterparties, same-card purchase context, and benefit name/notes. Caps are not historically verified. Label scores are not calibrated probabilities of origin. No transaction benchmark has been run on these proposals.

## Candidate X

Three outcomes: `benefit_identified`, `merchant_fit`, `no_match`. Both first outcomes offer confirmation.

Classify each candidate independently. Decide whether to offer user confirmation; do not determine that origin is proven. Return benefit ID, outcome, and one concise evidence-based reason.

The original bank description takes precedence over cleaned names and enrichment when they disagree. Enrichment may supply missing merchant identity but must not erase explicit bank wording. Distinguish whether the transaction connects to this merchant/program from whether affirmative evidence identifies a different origin. An unresolved origin does not negate a positive connection. A negative amount alone establishes neither.

Apply in order:

1. `no_match` if affirmative evidence identifies a merchant refund/return/reversal, payment/autopay, split reimbursement, balance redistribution supported by redistribution wording and a corresponding offsetting debit, or a different named benefit/program. Read ordinary meaning in context. The word credit alone identifies neither refund nor issuer benefit. Equal purchase or offsetting amount alone does not establish exclusion. A specifically named different benefit is no_match even if its merchant/category overlaps this candidate; do not spread its credit across broader separate benefits.
2. Otherwise `benefit_identified` if bank description explicitly identifies the target benefit or issuer credit program. This is sufficient without extra corroboration.
3. Otherwise `merchant_fit` if description or reliable merchant identity positively connects to the target's named merchant/program, or eligibility expressly described in its notes. Generic category overlap is insufficient when a particular merchant/program is required. Credit may still be a refund or adjustment; user confirmation resolves that uncertainty.
4. Otherwise `no_match`: absence of positive connection makes it ineligible for this suggestion without proving its origin.

Do not reject positive fit for hypothetical refunds, prior matching purchases, purchase code, missing issuer identity, or generic adjustment wording without affirmative contrary evidence. Do not infer eligibility from amount alone; do not apply caps, assumed refund rates, or unstated rules.

Expected: explicit Saks/Dunkin → benefit_identified; generic matching NYT/Equinox/CLEAR/Nordstrom → merchant_fit; explicit refund, paired redistribution, unrelated generic adjustment, or explicit Resy against separate dining → no_match.

## Candidate Y

Binary `suggest`/`dismiss` plus orthogonal `semantic_fit` and `origin_signal` (`target_credit`, `unclear`, `non_target`).

Classify possible use of each candidate benefit credit. Recommend only whether to ask confirmation. Evaluate every candidate independently; do not force one winner or treat scores as calibrated origin probabilities. Return JSON results in candidate order, each containing benefit_id, decision, semantic_fit, origin_signal, reason.

Original bank description is primary; other fields clarify but must not override its explicit wording. Prior purchases are context only.

First decide semantic fit: description explicitly identifies this benefit/program/issuer benefit credit OR merchant/program plus benefit notes make this particular benefit a plausible source. Exact benefit wording is sufficient. Merchant fit can suffice for confirmation even if origin is unclear. Generic adjustment with no identifiable merchant/program has no fit. Explicit different benefit/program does not fit merely because its merchant could also qualify.

Separately assess origin signal: target_credit if description affirmatively identifies its benefit/program as a credit; non_target if transaction affirmatively identifies refund, return, reversal, payment/autopay, split reimbursement, another benefit/program, or balance redistribution (including a linked offsetting debit); otherwise unclear. Read in context: hypothetical refund or matching purchase/amount does not establish refund. Purchase code, missing bank identity, generic adjustment alone do not establish non_target. Do not use unverified historical cap as gate.

Decision is suggest iff semantic fit is true and origin_signal is not non_target; otherwise dismiss.

Expected: explicit Saks/Dunkin → suggest/target_credit; generic matching merchants → suggest/unclear; anonymous adjustment → dismiss/unclear; paired redistribution or explicit refund → dismiss/non_target; explicit Resy → suggest/target_credit for Resy and dismiss/non_target for separate dining.

## Candidate Z

Three outcomes `suggest`, `exclude`, `unresolved_identity` plus boolean `origin_uncertain` and concise reason. Classify one transaction against one target for confirmation, never recording. origin_uncertain does not turn a semantic suggest into unresolved_identity.

Original bank wording takes precedence over cleaned/inferred merchant. Metadata and prior purchases support. Purchase code, absent bank identity, prior matching purchase, generic adjustment alone cannot prove refund or reject candidate. Hypothetical refunds are not affirmative evidence. Do not apply caps until historical usage verified.

Apply in order:

1. Explicit target issuer benefit/program → suggest unless stronger transaction-specific evidence proves reversal or excluded flow. Explicit different benefit → exclude even if related (Resy versus separate dining).
2. Otherwise exclude only for transaction-specific affirmative return/refund/reversal, payment/autopay, split, different benefit, unrelated merchant/program, or balance redistribution paired with offsetting debit. Explain observed evidence, not a possibility.
3. Otherwise suggest when named merchant/program in original description or reliable merchant fields plausibly fits target name/notes. Origin may be uncertain; set origin_uncertain true. Generic credit at covered merchant can be suggested without issuer wording.
4. unresolved_identity only when reliable merchant/program identity is insufficient to establish target connection AND no affirmative exclusion. Not for unrelated merchants or matching merchants whose credit origin is unverified.

Evaluate candidates independently. Do not infer target from amount/cap. Labels are decisions, not calibrated origin probabilities.

Expected: explicit Saks/Dunkin → suggest; generic matching NYT/Equinox/CLEAR/Nordstrom → suggest, origin_uncertain true; explicit refund or paired redistribution → exclude; anonymous Generic Adjustment → unresolved_identity; explicit Resy against separate dining → exclude.

## Shared judging brief

Score each candidate 1–5 on semantic clarity, meaningful uncertainty handling, benefit-specificity safety, compatibility with Jev's existing per-benefit choice questions, and simplicity. Rank all three and cast one winner vote. Identify the biggest flaw in the winner and a minimal repair. Do not claim benchmark accuracy or assume extra boolean/structured fields are supported by the existing choice API. Cases should include explicit benefit text, merchant-only plausible origins, unrelated merchant, anonymous adjustment, explicit refunds/reversals including wording that also names target, overlapping benefits, and same-amount prior purchases. Judges must independently assess; writer identities/models are withheld.
