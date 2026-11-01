# Jev spike: approaches and tradeoffs

> Historical report. The later decision selects the same prompt with transaction history omitted. Start at [the research index](README.md) and [the public baseline](jev-final-baseline.md) for the current recommendation and obfuscated rerun. Earlier scores below describe their original private fixtures.

The selected design is **one API request per negative posted transaction, with a shared concrete flow question and a joint benefit-choice question, emitting only one top confirmation suggestion**. The latest replay ablation did not improve it: dropping category, MCC, location, and transaction codes saved 8.93% of tokens but introduced an unsupported suggestion and a missed suggestion. Keep the full context. Cumulative Jev spend after this round is approximately $0.993619.

## Approach comparison

Earlier figures use different fixtures and label policies; they are not one continuous head-to-head accuracy ranking. Restoring original Plaid descriptions established 14 additional clear Dunkin credits, taking the clear-real-credit denominator from 126 to 140. The later V2 policy treats plausible merchant fit with unknown fee type/origin as confirmation-eligible. Old labels and results remain preserved.

| Approach | What we observed | Benefit | Tradeoff |
| --- | --- | --- | --- |
| Existing card-specific string patterns | Found 119/126 clear credits on the early production fixture. | Free, fast, transparent for established wording. | Per-card upkeep and descriptor-variant misses. |
| Compact descriptor-only Jev | Found 122/126 on that same fixture; 53 distinct requests covered 289 transactions through exact-request caching. | Semantic matching recovers some wording variants cheaply. | Still missed Saks/Chase dining variants; cannot recover fields discarded upstream. |
| Rich metadata plus three-way match/no-match/insufficient-evidence | At the predeclared 0.90 gate, 113/140 clear credits auto-record candidates, 27 review, none hidden; 101 transactions required review without an auto-match. | Conservative separation of uncertain cases; original descriptions revealed Dunkin. | Noisy review queue and a vague third class; unsupported for production automatic recording. |
| Tighter refund wording for confirmation, still independent per-benefit questions | At 0.50, 139/140 clear credits surfaced, plus eight unresolved top suggestions. | Lets a human resolve origin instead of withholding plausible matches. | Seven wrong secondary Resy/dining candidates and borderline Saks scores. |
| Binary suggest/dismiss, candidate rosters, and stronger scope wording | Some variants improved recall; others regressed. The later V2 binary candidate at 0.25 emitted 250 correct top suggestions, one wrong top, and missed two eligible transactions in the 419-case exposed set. | Directly matches the confirmation action; roster helps distinguish separate programs. | Independent questions can all favor overlapping benefits; longer instructions did not reliably help. |
| Shared abstract binary flow check plus joint benefit choice | Joint comparison fixed the named Broad Travel versus Airfare error. Abstract flow labels gave obvious refunds weak exclusion scores. | Fewer repeated questions and direct competition among benefit identities. | Flow classification was too weak despite sensible-looking wording. |
| Shared five-way concrete flow plus joint benefit choice — selected | 140/140 clear real credits found; all 469 top-suggestion/withhold decisions correct, including the then-unseen 50. | Separates bank-described flow from merchant fit; cheap, one top candidate per transaction. | Not exhaustive per-benefit matching: unseen pair agreement was 86%, with unselected alternatives and one wrong secondary candidate. Requires confirmation. |
| Focused/lean context ablations | Earlier focused variants were mixed; the latest controlled comparison gave 467/469 correct decisions versus full context's 469/469, for 8.93% fewer tokens. | Smaller requests, less noisy metadata, potentially lower cost. | Loses useful signals too; current evidence favors retaining full context. |
| Jev-to-Luna escalation — attempted, not evaluated | Prepared review-case fallback, but API probes returned exhausted-credit errors; zero successful Luna classifications. | Could in principle help recognition failures. | No measured evidence of benefit; cannot resolve absent origin evidence by itself. |

Per-benefit questions were already batched into one API request per transaction. The selected structure reduces question count and repeated instructions, rather than changing from multiple HTTP requests per transaction to one.

## Considered but not independently validated

The initial arena compared explicit-benefit/merchant-fit/no-suggestion labels, binary suggestion decisions with separate origin fields, and a narrow unresolved-identity class. A synthesis favored binary decisions for the then-current independent-question interface. These qualitative votes guided experiments; they were not accuracy evidence. The final architecture later separated flow from benefit identity after measured failures.

Exact allowance fit was analyzed as a possible feature: 51/140 clear credits equaled the current configured cap, but so did 14 wrong transaction-benefit pairs. It was not promoted to a hard rule or validated prompt feature because historical limits were not versioned. No food-first/category-first cascade was benchmarked.

All performance figures concern frozen, largely agent-adjudicated fixtures. The top-suggestion success supports a confirmation pilot, not a guarantee of future accuracy or automatic ledger updates. No production behavior changed.

Details: [early production results](jev-production-results.md), [rich-context experiment](jev-evidence-threshold-experiment.md), [tight-refund experiment](jev-confirmation-experiment.md), [hill-climb and latest comparison](jev-confirmation-hillclimb.md), [exact selected configuration](jev-confirmation-winner.json).

## Final single-transaction simplification (round 12)

The existing selected prompt without related transactions reproduced all 469 final decisions, including all 140 known real credits, with 8.78% fewer tokens. A broader evidence rubric plus limited historical amount hints preserved recall but added three unsupported real suggestions and used 24.93% more tokens than the no-history control. Select the no-history control for an initial one-top, confirmation-only approach; the exact template is [jev-confirmation-single-transaction.json](jev-confirmation-single-transaction.json). This supersedes the earlier recommendation to retain related-purchase context. See [experiment details](jev-single-transaction-rubric.md). These are replay results, not a fresh holdout; raw secondary-candidate limitations remain.
