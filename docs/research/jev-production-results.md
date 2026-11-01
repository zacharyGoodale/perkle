# Production Jev bench results — October 30, 2026

**Verdict: promising modest improvement over the current patterns, with important misses and unresolved ambiguity.** This supports a further controlled test, not automatic production replacement.

Evaluated the [production provisional golden set](jev-production-golden-set.md): 289 negative transactions, 53 card/descriptor families, 21 candidate automatic benefits, and 2,294 transaction-benefit judgments. Model `jev-1.14.0`, `descriptor` prompt, no probability gate. No prompts or labels were adjusted after seeing these results.

## Main comparison

| Metric | Jev | Current catalog patterns |
| --- | ---: | ---: |
| Clear credit transactions found | 122/126 (96.8%) | 119/126 (94.4%) |
| Clear credits missed or abstained on | 4 | 7 |
| Automatic matches on ambiguous evidence | 1 | 4 |
| Matches contradicting clear no-match labels | 0 | 0 |
| Positive descriptor families found | 14/16 (87.5%) | 13/16 (81.3%) |
| Ambiguous descriptor families marked as matches | 1 | 1 |

The four pattern matches on ambiguous evidence are repetitions of one descriptor family. Neither method's ambiguous matches are proven incorrect in the real world; the evidence does not support auto-marking them. Counting them as errors yields a supported-match fraction of 99.2% for Jev and 96.7% for patterns on the repeated-transaction dataset, but only 93.3% and 92.9% on distinct families. These are not independently verified production precision estimates.

Among descriptor families not seen in the small pilot, Jev found **9/10** clear positive families, versus **8/10** for patterns. Jev additionally matched one ambiguous new family; patterns matched none. This is a novelty slice, not a randomly held-out or user-reviewed test set.

## Where results differed

- Jev recovered four Platinum airline reimbursements and one Chase The Edit credit that the current patterns missed.
- Jev missed two Chase dining credits that the patterns found.
- Both methods missed two Saks credits using a different descriptor from the better-known variant.
- Jev matched one merchant-only CLEAR credit at **0.61 match probability**. The provisional label is insufficient evidence: a merchant refund and an issuer reimbursement cannot be distinguished from the saved fields.
- The broader iOS Equinox pattern marked four ambiguous merchant credits; Jev did not automatically match those.

Thus Jev recovered five additional clear transactions while losing two relative to patterns, for a net gain of three. The current matcher is already strong on explicit recurring descriptors.

## Per-benefit clear positives

| Card | Benefit | Jev found | Patterns found |
| --- | --- | ---: | ---: |
| Gold | Dining | 23/23 | 23/23 |
| Gold | Resy | 7/7 | 7/7 |
| Platinum | Uber One | 13/13 | 13/13 |
| Platinum | Resy | 5/5 | 5/5 |
| Platinum | Hotel | 4/4 | 4/4 |
| Platinum | Saks | 2/4 | 2/4 |
| Platinum | Digital entertainment | 47/47 | 47/47 |
| Platinum | Airline fee | 4/4 | 0/4 |
| Platinum | CLEAR | 1/1 | 1/1 |
| Platinum | Lululemon | 5/5 | 5/5 |
| Platinum | Oura | 1/1 | 1/1 |
| Chase | Travel | 6/6 | 6/6 |
| Chase | Dining | 0/2 | 2/2 |
| Chase | The Edit | 1/1 | 0/1 |
| Chase | StubHub | 3/3 | 3/3 |

Six benefits still have no explicit positive evidence in this dataset: Venture X Global Entry, Gold Dunkin, Platinum Equinox and Global Entry, Chase Select Hotels and Global Entry. They were included as candidates, but positive recall cannot be established for them.

## Probability gates: diagnostic only

Reusing cached probabilities, without more model calls:

| Required match probability | Clear credits retained | Unsupported matches |
| --- | ---: | ---: |
| Raw winning choice | 122/126 | 1 |
| At least 0.90 | 106/126 (84.1%) | 0 |
| At least 0.99 | 76/126 (60.3%) | 0 |

The 0.90 gate was previously considered in the pilot. Neither gate has been validated on independent labels or a separate threshold-tuning split. A high gate reduces unsupported decisions here at a substantial recall cost; a model probability is not proof that a credit qualifies or settled.

## Cost and latency

The model state includes card, descriptor, and credit direction, without date or amount. Therefore repeated identical descriptions on the same card produce identical requests and reuse cached responses.

- **53 unique API requests** cover all 289 transactions; 236 cases reuse those exact responses.
- **75,376 billed input tokens**, estimated charge **$0.003166** at the researched $0.042/million input price; no retries.
- Unique-request median **91 ms**, p95 **140 ms**, maximum **379 ms**, observed serially from this client.
- Without exact-request reuse, the same 289-case payloads would total 419,206 input tokens, approximately **$0.01761**. This is a counterfactual estimate, not additional spending.

The run initially exposed a report-accounting issue: cached responses were counted once per transaction when summing token cost. The report now counts each request hash once, while keeping transaction-weighted detection metrics. An offline regression check covers duplicate-cache accounting. No additional API calls were needed for that correction.

## Limits and next decision

Labels are still provisional agent adjudications. Only 16 positive descriptor families support the headline recall, and recurring credits heavily weight transaction metrics. Production omits pending/posted status. The classifier identifies credit descriptors, not settled credits or purchase eligibility. The pattern baseline uses the current iOS catalog, not the earlier Python catalog, and does not run accounting or period logic.

The useful next step is to review ambiguous labels and the missed Chase/Saks families, freeze a revised rubric, and evaluate genuinely new labeled descriptors. The current evidence supports a confidence-gated suggestion or shadow mode experiment; it does not establish safe automatic ledger updates. The application remains unchanged.

Private detailed results: `backend/data/jev-production/results-descriptor.json` and `analysis-descriptor.json`, with raw response caches alongside them. Offline reproduction:

```sh
backend/.venv/bin/python backend/scripts/jev_bench.py report \
  --data-dir backend/data/jev-production --prompt descriptor
backend/.venv/bin/python -m unittest discover -s backend/scripts -p 'test_*.py'
```
