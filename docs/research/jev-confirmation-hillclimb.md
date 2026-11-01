# Jev confirmation-notification hill climb

> Historical report. The later decision selects the same prompt with transaction history omitted. Start at [the research index](README.md) and [the public baseline](jev-final-baseline.md) for the current recommendation and obfuscated rerun. Earlier scores below describe their original private fixtures.

The selected configuration produced the correct **single top suggestion or withhold decision for all 469 fixture transactions**, including all 50 newly held-out transactions. Optimization stopped at **$0.956450 estimated cumulative Jev spend**, below the $5 cap, for the accepted one-candidate confirmation product. This does **not** establish nearly perfect independent per-benefit classification: held-out pairwise agreement was only **86%**. That stricter interim target was not achieved and must not be conflated with notification success.

All labels remain provisional agent adjudications, not independently user-confirmed issuer-credit origins. The untouched final set is synthetic. This is evidence for a confirmation-first pilot; it is not a production accuracy guarantee or justification for automatic usage recording. No backend deployment, application behavior, or actual notification changed in this spike.

## Selected call and decision structure

Use one Jev `jev-1.14.0` request for each posted negative transaction, with **two shared choice questions**, independent of how many benefits the card has:

1. Classify the bank-described flow: refund/return/reversal, card payment, split repayment, supported balance redistribution, or other credit.
2. Compare all of the card's candidate benefits in one multiclass question, with a no-connected-benefit choice. Prefer explicitly named program identity over merchant/category overlap; otherwise allow plausible merchant fit and let the user confirm subtype and origin.

The request includes original and cleaned descriptions, amount/date/status/currency, available merchant/category/code/counterparty/location metadata, and related same-account transactions. Benefit choices contain names and coverage notes. It does not send expected labels, detection patterns, previous classifications, account IDs, or user IDs.

The deterministic confirmation policy is:

- Withhold when the sum of the four excluded-flow choice scores is at least **0.80**.
- Otherwise, take the highest-scoring benefit candidate. Offer **only that one candidate**, and only if its choice score is at least **0.25**.
- All suggestions require user confirmation. Withholding does not establish a refund or prove that no benefit credit occurred.

Both thresholds were selected using exposed tuning data and frozen before the last unseen evaluation. A broad range of flow thresholds, 0.65–0.98, gave the same best tuning error count; 0.80 was selected within that range. These scores and their sums are not calibrated probabilities of issuer origin. The no-connected-benefit choice competes with the benefit choices, but the deterministic policy uses the strongest benefit's threshold rather than requiring it to outrank the no-connection choice.

The exact reusable configuration is [jev-confirmation-winner.json](jev-confirmation-winner.json). Configuration hash: `41b4cf584e3d4d8c665224e4877a946245d623363f80275c160172749542da19`.

## Evaluation and limitations

The fixture has 289 real production negatives, 33 source-derived synthetic stress cases, 43 first-challenge cases, 54 second-challenge cases, and 50 final unseen cases: **469 transactions and 2,865 benefit pairs**. Repeated real descriptors are not independent examples; 17 positive descriptor families underpin the 140 clear real credits.

| Transaction outcome | Earlier exposed sets | Final unseen set | Combined |
| --- | ---: | ---: | ---: |
| Transactions evaluated | 419 | 50 | 469 |
| Eligible transactions with an allowed top suggestion | 253/253 | 37/37 | 290/290 |
| Ineligible transactions correctly withheld | 166/166 | 13/13 | 179/179 |
| Wrong emitted top suggestions | 0 | 0 | 0 |
| Transaction decision agreement | 100% | 100% | 100% |

All **140/140 clear real benefit credits** receive a correct top suggestion, including the difficult Saks descriptions and all Dunkin credits. The real-data policy emits 166 suggestions and withholds 123 negatives. The 26 suggestions beyond the clear credits have unresolved origin and are candidates for user confirmation, not newly confirmed benefit credits.

The first descriptor-family validation split retained 56 transactions and 533 pairs, with no family overlap with development. Those families had prior pilot exposure, so this is not an entirely new real-world test. The 43- and 54-case challenges became tuning evidence after failures were inspected. The last 50-case set was authored independently without reading prompts, results, or earlier challenge files. A separate auditor checked its labels; one coverage contradiction was clarified before any API call. Final prompt writers and selection judges did not inspect that set. The frozen configuration was then evaluated once on it without further tuning.

Pairwise diagnostics deliberately remain visible:

| Raw benefit-pair outcome | Earlier exposed sets | Final unseen set | Combined |
| --- | ---: | ---: | ---: |
| Correct positive candidate scores above threshold | 254 | 37 | 291 |
| Wrong secondary candidate scores above threshold | 0 | 1 | 1 |
| Allowed alternatives below threshold | 7 | 13 | 20 |
| Pair agreement | 99.75% | **86%** | 99.27% |

Every missed positive pair is an alternative benefit on a transaction that already receives an allowed top recommendation. The wrong secondary candidate is also on a transaction with a correct, higher-scoring top candidate. Thus these errors do not affect the enforced one-recommendation output. They would matter if the UI displayed every candidate above threshold, attempted to enumerate all plausible benefits, or independently classified every benefit. **Do not use the notification result to claim the original ≥99% unseen pairwise target passed.**

Two independent exit reviewers, one Astra and one Sol, considered stopping defensible for the previously accepted one-candidate product, with that pairwise limitation disclosed. This is a product-mode stopping decision, not a revision of frozen labels to improve scores.

## What the hill climb learned

Independent Astra and Sol writers proposed prompts, and separate Astra/Sol judges ranked them. Several unanimously preferred prompts performed worse, so measured results—not votes—determined the retained configurations. Both the full-context and focused-payload alternatives were tested. Generic Plaid `adjustment` codes and preceding purchases could distract models; removing context also removed useful evidence. The selected configuration retains the context but separates the tasks.

The largest useful structural changes were comparing benefit identities jointly and giving transaction flows concrete category names. Joint comparison fixed a stress case that repeatedly assigned an explicitly named Broad Travel credit to a separate Airfare benefit. Concrete flow categories separated refunds from merchant fit more effectively than an abstract binary exclusion question. The initial flow threshold of 0.50 suppressed legitimate credits; tuning it separately recovered them without surfacing explicit refunds in this fixture.

During the experiment, the user clarified that a generic airline credit should be suggested even when its fee type and origin are unknown. An independent label reviewer froze a prospective V2 overlay with 17 dismissal-to-confirmation changes: seven airline-fee pairs, five Hulu pairs, and five synthetic merchant/subtype pairs. V1 labels and results remain unchanged. The earlier configurations were rescored under V2 rather than attributing policy changes to prompt improvements.

The Hulu audit also exposed incomplete catalog notes: they gave open-ended examples while omitting Hulu. Current Amex terms explicitly include Hulu, supporting its plausibility for confirmation. This is not historical confirmation of those transactions; the fixture spans changing terms. Historical limits and complete dated eligibility descriptions remain unresolved. [Amex digital-entertainment benefit](https://global.americanexpress.com/card-benefits/detail/digital-entertainment/platinum/), [Amex Platinum fact sheet](https://www.americanexpress.com/content/dam/amex/en-us/company/press-kits/platinum-refresh/U-S-Consumer-Platinum-Card-Fact-Sheet.pdf).

## Cost and verification

Cumulative Jev input usage across the hill climb was **22,772,620 tokens**, estimated at **$0.956450** using the bench's researched rate of $0.042/M input tokens. This is Jev API cost only, excluding arena-agent usage. Exact request caches deduplicate billed usage across repeated reports and identical transactions. The runner enforces a shared $5 cap with headroom and reserves budget for attempts without a saved response.

The selected full 469-case configuration used 468 unique requests, 971,715 input tokens, and an estimated **$0.040812**. Median request duration was **91 ms**. For the real production negatives alone: 288 unique requests, 672,119 input tokens, estimated **$0.028229**, or about **$0.10 per 1,000 negative transactions** at this observed payload size. The request count remains one per negative transaction; each request contains two questions.

Eight offline checks pass, including request exclusion of gold labels/patterns, exact cache-cost accounting, uncertain-attempt reservations, related-transaction filtering, the shared flow gate, dynamic criteria and focused views, and the guarantee that a wrong secondary candidate is retained diagnostically but not emitted as a second suggestion. `git diff --check` passes.

Private fixtures, the V1/V2 label overlays, exact responses, all tested candidates, and per-transaction recommendations are in Git-ignored `backend/data/jev-hillclimb/`. The result artifact includes explicit `recommendations` with one benefit or null per transaction, plus all raw `pairs`; no secondary candidates are silently discarded from evaluation.

Reproduce from the existing private fixture/cache:

```sh
backend/.venv/bin/python backend/scripts/jev_hillclimb.py report \
  --prompt docs/research/jev-confirmation-winner.json \
  --threshold 0.25 --label-policy v2
backend/.venv/bin/python -m unittest discover -s backend/scripts -p 'test_*.py'
```

To execute missing requests within the same cumulative budget, use `run` instead of `report` and `--split all`. Existing responses are reused. Do not present the small synthetic holdout as demonstrated ≥99% future population accuracy. A confirmation pilot should collect user-reviewed outcomes before expanding claims or considering automatic recording.

## Follow-up round: lean versus full transaction context

The user requested one more round and an approaches summary. The predeclared comparison retained the selected prompts, V2 labels, 0.25 benefit threshold, and 0.80 flow threshold. It removed PFC/category, MCC, location, and transaction-code fields from both the target and related transactions, retaining original/cleaned names, merchant identity, counterparties, amount/date/status/currency, and relationship/offset flags. No prompt or threshold was tuned after inspecting the result. All 469 cases are replay validation in this follow-up; the former unseen 50 are no longer a fresh holdout.

| Result | Full context | Lean context |
| --- | ---: | ---: |
| Correct transaction decisions | 469/469 | 467/469 |
| Correct top suggestions | 290/290 | 289/290 |
| Wrong emitted suggestions | 0 | 1 |
| Eligible transactions withheld | 0 | 1 |
| Clear real credits found | 140/140 | 140/140 |
| Raw pair agreement | 99.27% | 99.20% |
| Tokens | 971,715 | 884,982 |
| Estimated cost for the fixture | $0.040812 | $0.037169 |

Lean context saved **8.93%** of input tokens but changed two decisions adversely: it suggested the digital-entertainment benefit for a generic Google Services credit that the frozen rubric does not support, and withheld a Nordstrom merchant credit against the fictional Nordstrom benefit that should reach confirmation. These remain provisional-label judgments, not proof of the underlying real credit origins. Because four field groups were removed together, this does not establish which individual field caused either change.

The full-context configuration remains selected. The follow-up cost approximately **$0.037169**, bringing cumulative Jev spend to **$0.993619**, still below the original $5 cap. Eight offline checks and `git diff --check` pass. Detailed comparison and all changed recommendations are saved privately in `backend/data/jev-hillclimb/round-11-comparison.json`. See [the approaches summary](jev-approaches-summary.md) for the consolidated comparison.

## Final single-transaction simplification (round 12)

The existing selected prompt without related transactions reproduced all 469 final decisions, including all 140 known real credits, with 8.78% fewer tokens. A broader evidence rubric plus limited historical amount hints preserved recall but added three unsupported real suggestions and used 24.93% more tokens than the no-history control. Select the no-history control for an initial one-top, confirmation-only approach; the exact template is [jev-confirmation-single-transaction.json](jev-confirmation-single-transaction.json). This supersedes the earlier recommendation to retain related-purchase context. See [experiment details](jev-single-transaction-rubric.md). These are replay results, not a fresh holdout; raw secondary-candidate limitations remain.
