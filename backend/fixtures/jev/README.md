# Published confirmation benchmark

`fixture.json` is a pseudonymized replay dataset: 289 real-derived negative
transactions and 180 constructed cases. The `suite` values `synthetic`, `fresh`,
`final`, and `unseen` distinguish historical constructed cohorts; none is a new
holdout now. Labels are provisional agent judgments under the user-confirmation
policy, not independently verified issuer-credit origins.

Privacy transformations replace source case/family identifiers, named people,
niche merchants, geographic strings, store numbers and booking/reference numbers.
Invented analogous merchants are substituted consistently in descriptions,
benefit names, coverage notes and label keys. Geographic enrichment retains field
presence and nullness with example values. Original descriptions retain their
program, merchant-category, payment, refund, reversal and adjustment meaning.
Generic public brands and explicit credit program wording remain.

Every posting day changes while retaining its month and year. Day rotation stays
on the original side of the known July 25, 2024 and September 18, 2025 benefit
change boundaries. Amounts, card product, category codes, categorical enrichment
and bank event codes remain to preserve full-cap, partial-credit and metadata
stress cases. Consequently this is obfuscation, **not an anonymity guarantee**:
amounts, month/year, repeated descriptors and public brands retain some pattern
recognition risk. Raw sources and the reversible export audit are excluded.

Only the target transaction is published. Related purchase history, raw Plaid
identifiers, account identifiers, detection patterns and private label rationale
are absent. The original history-retrieval experiments remain documented, but
cannot be replayed using this deliberately smaller publication fixture.

From the repository root, using the existing backend environment:

```sh
backend/.venv/bin/python backend/scripts/jev_public_bench.py run
backend/.venv/bin/python backend/scripts/jev_public_bench.py report
backend/.venv/bin/python backend/scripts/jev_public_bench.py publish
```

`run` reads `TYPESAFE_API_KEY` from the environment or ignored root `.env`, makes
paid calls for uncached requests and preserves ignored response caches under
`backend/data/jev-public-bench`. It uses the frozen selected single-transaction
prompt, benefit threshold 0.25, exclusion threshold 0.8 and label policy V2.
`report` is offline; `publish` writes numerical results and responses to
`docs/research/jev-final-baseline-results.json` after a complete run. The API does
not receive expected labels. The output is one benefit suggestion requiring user
confirmation, or no suggestion; it never records benefit usage.

See [research index](../../../docs/research/README.md) for the complete experiment
history, prompt alternatives, limitations, costs and final publication results.
