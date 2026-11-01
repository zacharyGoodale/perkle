# Small Jev bench — October 30, 2026

**Verdict:** worth a further controlled experiment, not ready to replace automatic matching. Performance changed substantially with the prompt. This measures identification of posted statement credits, not whether purchases qualify for benefits.

## Scope and provenance

Read-only extraction from the existing local backend database, using records marked `source=plaid`. No live Plaid refresh was performed. The snapshot dates run from December 2025 through March 2026.

The bench contains **19 actual transaction cases**, selected from 121 card-mapped transactions: one representative per credit descriptor/card/status (11), plus four deterministically sampled purchases per card (8). Seven unmapped transactions were excluded. Repeated descriptors are not counted as independent evidence. This deliberately enriched selection does not estimate production traffic accuracy.

There are **174 transaction-benefit judgments**, covering the configured automatic benefits on the two cards. Labels were frozen before API calls: six explicit benefit-credit matches, two ambiguous target-benefit pairs, and other pairs labeled no-match. These are **provisional agent-adjudicated labels**, not independently human-reviewed gold. Neither stored assignments nor regex results were used as truth. Benefit names are interpreted as descriptor identification; current amounts and historical eligibility are not evaluated.

Private fixture, annotation evidence, response cache, and detailed results are under `backend/data/jev-bench/`, already ignored by Git. They contain transaction information; the public source and this note contain no raw transaction records. Requests omit account numbers/masks, user IDs, Plaid credentials, and existing benefit assignments.

## Measured results

Pinned model: `jev-1.14.0`. Each request asks an independent three-way Choice question per automatic benefit on the transaction's card. No confidence threshold was applied; these are raw winning choices.

| Method | Clear credits found | Matches on ambiguous evidence | Known false matches | Median request time | Input tokens | Estimated charge |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Existing descriptor patterns | 5/6 | 0 | 0 | — | — | $0 |
| Jev with longer instructions + benefit notes | 2/6 | 0 | 0 | 93 ms | 46,056 | $0.001934 |
| Jev with compact descriptor rubric | 6/6 | 1 | 0 | 94 ms | 29,670 | $0.001246 |

Total: **38 requests, 75,726 input tokens, approximately $0.003180** at the researched $0.042/million input-token price. Timing is client-observed serial request duration; this is not a load test. There were no automatic retries. The regex comparison isolates current per-benefit substring matching; it does not rerun the production detector's period filtering or accounting writes.

The longer version abstained even on several explicit named credits. The compact version recovered the reimbursement descriptor missed by the patterns, but overclaimed one merchant-only credit at **0.52 match probability** (confidence 0.28). The available data cannot establish whether that ambiguous record was actually an issuer benefit or a refund; this is an unsupported automatic decision, not a proven incorrect real-world benefit assignment.

For context, the compact version's six clear positive probabilities were 0.92, 0.99, 1.00, 0.54, 0.97, and 0.97. A post-hoc 0.90 gate would retain five and reject the unsupported match. This is diagnostic only: no threshold was validated on a holdout.

The shorter variant was designed after inspecting the first run. It also removes amount/date/category fields and benefit notes, so the experiment does not isolate which change caused the improvement. Both variants use the same development cases; there is **no independent test set**, and only six clear positives. Aggregate pair accuracy is dominated by unrelated benefits and should not drive the decision.

## Reproduce

From the repository root, using the existing backend environment:

```sh
backend/.venv/bin/python -m unittest discover -s backend/scripts -p 'test_*.py'
backend/.venv/bin/python backend/scripts/jev_bench.py report --prompt contextual
backend/.venv/bin/python backend/scripts/jev_bench.py report --prompt compact
```

The reports are offline and use cached responses. To issue missing requests:

```sh
backend/.venv/bin/python backend/scripts/jev_bench.py run --prompt compact --max-usd 0.10
```

The script reads `TYPESAFE_API_KEY` from the environment or root `.env`. Responses are cached by exact request content/model. Cached requests are reused; edited transaction fields or prompts generate new requests. The per-invocation budget check reserves a conservative estimate before each call and records returned billable usage; it is not a provider-enforced account spending limit. At most 40 fixture cases are allowed, and calls are not retried automatically. Requests go directly to the official `https://api.typesafe.ai/v1/systemone` endpoint.

On a new checkout, `prepare` creates an unlabeled fixture in the ignored directory; review and fill each case's `expected` map and `label_evidence` before `run`. Every candidate benefit needs `match`, `no_match`, or `insufficient_evidence`. `reviewed_by_user` defaults to false. `prepare` refuses to overwrite an existing fixture. It currently supports this repository's local SQLite snapshot, not encrypted or remote database access.

## Next expansion, if desired

First review the 19 labels, especially ambiguous records. Then freeze the compact rubric and evaluate new, independently labeled descriptors, including explicit refunds and generic credits, before tuning a probability gate on a separate development split. Preserve both original Plaid descriptions and merchant names if pursuing merchant-only cases. A classifier cannot recover discarded source evidence. Application tracking remains unchanged by this spike.
