# Candidate C: short decision order

## Rubric

Classify one posted negative transaction. Original bank description/name outranks merchant, counterparty, PFC, MCC, and location. PFC/MCC cannot prove issuer origin. No history or purchase data exists.

**1. Credit type:** Explicit refund/return/reversal or structured refund code → refund_return_reversal. Read the full phrase: “refund of payment” is a refund. Explicit card payment/autopay → card_payment; shared-expense repayment → split_repayment; transfer/balance redistribution → balance_redistribution. Otherwise other_credit. Neither generic “credit/adjustment” nor merchant identity proves refund. Named benefit credits (“AMEX DUNKIN CREDIT,” “Shop Saks with Platinum Credit”) are not card payments.

**2. Benefit:** Choose one roster benefit or none, only for product confirmation. Match an explicitly named program in original bank text first. If absent from roster, return none, even when another benefit covers a similar service. Without a program name, require merchant fit to stated coverage; shared category or similar service is insufficient. Coverage can be broad; examples and “etc.” are nonexhaustive. Unknown origin or fee subtype remains eligible when merchant fits (generic airline credit for airline incidental benefit). If several fit, choose clearest; if tied, none. Verified, code-computed exact full-cap match with known cap version strengthens an existing program/merchant match, never creates one. Ignore absent cap data; partial credits remain eligible.

## Rationale

The order makes the bank's own words decisive and keeps category guesses from turning a movie, restaurant, or digital-service credit into an unrelated benefit. It leaves uncertain but covered merchants for confirmation without claiming automatic usage. Its weakness is that equally strong benefits still require abstention, and it cannot verify the underlying purchase from one transaction.
