# Cap evidence and Luna fallback experiment

The risk research is in [benefit-refund-risk.md](benefit-refund-risk.md). This note records the local amount analysis and the prepared fallback experiment. No Luna classification results were obtained.

## Amount fit in the existing fixture

Using the frozen real evidence suite and each candidate benefit's **current configured period cap**:

| Provisional label | Exact cap match | Other amount |
| --- | ---: | ---: |
| Match | 51 | 89 |
| No-match | 14 | 2,108 |
| Unresolved | 0 | 32 |

Equality is calculated in decimal cents. This is a descriptive feature analysis across 2,294 candidate pairs, not a population likelihood or a threshold validation. The 14 non-match collisions include merchant credits, payments, an internal adjustment, and credits for other benefits with the same cap. Therefore equal amount is useful supporting context, not a sufficient matching rule. Lack of equality cannot reject a match: 89 of the 140 clear positives differ from the current cap.

Historical correctness is a separate limitation: the 2024–2026 history crosses benefit changes, and some configured limits are outdated. Before relying on cap features, version issuer terms by effective date and calculate full versus remaining period allowance in ordinary code. This experiment marks current-cap hints as historically unverified and instructs the fallback not to penalize mismatches.

## Prepared cascade

`backend/scripts/jev_luna_cascade.py` selects the previously frozen Jev review transactions that have no automatic match: **101 real transactions and 11 synthetic stress transactions**. It asks Luna only about candidate benefits routed to review. Jev's auto/hide results remain unchanged.

Each request supplies the same transaction and related-purchase context, benefit definitions, and cautiously labeled amount-fit hints. It omits expected labels and Jev probabilities to reduce anchoring. The requested output is a structured decision, evidence type, an exact source-description quote, and a short reason. It does not pretend a generated self-confidence number is calibrated like a model probability.

The proposed promotion gate requires a `match`, an explicit-benefit evidence classification, and a source-grounded quote. Merchant-only or unsupported matching proposals stay in review. This is an experimental guard, not independent proof that the quote identifies the benefit; evaluation against reviewed labels is still necessary. Non-match decisions are also evaluated for wrongly hidden credits.

API model: **`gpt-6-luna`**, Responses API, low reasoning effort, strict JSON schema, `store: false`, default service tier, 4,096 maximum output tokens. The script defaults to a conservative **$0.50 per-run cap**, caches exact requests, records usage and latency, and does not automatically retry failures. Official model documentation lists $0.10/M input, $0.01/M cached input, and $0.50/M output; costs would be estimated from returned usage at those rates. [Model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna), [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

## Execution status

The first single-request API probe and a single-request retry after resuming both returned **HTTP429 `credit_balance_exhausted`**. There are **zero successful API classifications**, and no API quality, cost, or latency result to report. The key was read from the user's `OPEN_API_KEY` environment entry; no key value was printed or saved.

A separately labeled qualitative Luna Codex-agent spot-check was prepared with eight cases and 38 candidate judgments, but that agent also failed with **workspace out of credits**. It produced no answer file. This is not a fallback result and is not substituted for the API benchmark.

Private amount-feature examples, prepared qualitative requests, and blocker evidence are in the Git-ignored `backend/data/jev-luna-cascade/` directory. The code is ready to execute after API credit becomes available:

```sh
backend/.venv/bin/python backend/scripts/jev_luna_cascade.py run --max-usd 0.50
backend/.venv/bin/python backend/scripts/jev_luna_cascade.py report
```

Five offline checks pass, including request exclusion of labels/Jev scores, the quote-grounding promotion gate, and the pre-existing Jev context/threshold/cache checks. No production or application behavior changed.
