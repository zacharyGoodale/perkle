# Production credit dataset — October 30, 2026

Built a larger **provisional golden set** from actual production transactions, using the user's `amount < 0` candidate rule. No Jev requests were made during this expansion and no production state was changed.

The subsequent evaluation is recorded in [production bench results](jev-production-results.md).

## Source and scope

The production service is the Rust Lambda backend in the sibling `perkle-ios` repository, backed by DynamoDB. Its transaction endpoint is a mutating Plaid sync operation, not a read-only export. The delegated agent inspected the deployed configuration and performed a **read-only, user-scoped, paginated production DynamoDB query** instead of invoking that sync route. This is a production backend snapshot, not a fresh Plaid sync or a Lambda invocation. Private provenance records the exact tables, production environment, user-scope basis, hashes, and retrieval time.

The export contains **1,565 transactions**, dating from June 12, 2024 through October 30, 2026. **289 are negative (18.47%)**. All negatives map to the four requested cards using the iOS catalog's account patterns. Stored Plaid `name` values are preserved. These are not the bank's raw `original_description` field; production did not request or retain that field. The export's `raw_description` is a copy of stored `name`, not additional source evidence.

The user explicitly identified Venture X, Amex Gold, Amex Platinum, and Chase. A read-only check of the local iOS simulator's persistent portfolio corroborated those four active cards and no hidden overrides. This is not verification of a live device's CloudKit state. The candidate catalog is snapshotted from the current sibling iOS JSON resources, with source hashes; it contains **21 automatic benefits**. Manual and information-only benefits are excluded. The catalog is configuration evidence, not independent verification of issuer terms.

## Dataset and labels

| Card | Negative transactions | Auto benefits | Benefits with explicit positive descriptors |
| --- | ---: | ---: | ---: |
| Venture X | 11 | 1 | 0 |
| Amex Gold | 80 | 3 | 2 |
| Amex Platinum | 171 | 11 | 9 |
| Chase Sapphire Reserve | 27 | 6 | 4 |
| Total | 289 | 21 | 15 |

There are **53 distinct card/descriptor families**, not 289 independent descriptions. The fixture contains **2,294 candidate transaction-benefit pairs**: 126 `match`, 2,119 `no_match`, and 49 `insufficient_evidence`. There are 126 transactions with explicit benefit descriptors, 44 transactions with at least one ambiguous candidate, and 119 with no candidate match.

Labels were independently adjudicated by the coding agent from descriptor evidence, not copied from regex matches, stored benefit assignments, or Jev predictions. They remain **provisional until user review**. Each case includes evidence, a descriptor group, and `reviewed_by_user: false`. A match identifies an issuer-credit descriptor; it does not prove eligibility under historical terms or a settled ledger event.

Ten descriptor families overlap the first pilot. Each case records `previously_seen_in_pilot`; any future split should keep families together and distinguish new descriptors from pilot overlap. No accuracy claim or new holdout result is made here.

## Positive coverage

| Card | Explicit positive coverage | Remaining gaps |
| --- | --- | --- |
| Venture X | None | Global Entry: no observed positive |
| Amex Gold | Dining; Resy | Dunkin: merchant-only evidence, ambiguous |
| Amex Platinum | Uber One; Resy; hotel; Saks; digital entertainment; airline fee; CLEAR; Lululemon; Oura | Equinox: merchant-only evidence, ambiguous. Global Entry: no observed positive |
| Chase Sapphire Reserve | Travel; dining; The Edit; StubHub | Select Hotels: ambiguous hotel evidence only. Global Entry: no observed positive |

All 21 benefits are included as candidate labels even where positive coverage is missing. No synthetic examples were used to conceal gaps. Merchant-only credits can be refunds or benefit credits; recognizable merchants, recurring amounts, or existing broad patterns alone do not settle that distinction. Benefits outside the configured candidate catalog are not forced into an unrelated benefit.

## Important source limitation

Production persists descriptions and amounts but **does not retain pending/posted status or categories**. These fields remain null. The expanded task is therefore **issuer benefit-credit descriptor identification**, not proof that a credit posted. The bench has a separate `descriptor` prompt and refuses the earlier posted-credit prompts for this fixture. Pending/posted verification requires additional upstream evidence before using these results to update actual benefit usage.

## Private artifacts and verification

All transaction artifacts are under the existing Git-ignored directory `backend/data/jev-production/`:

- `fixture.json`: complete provisional labels and case evidence.
- `adjudicated-groups.json`: descriptor-family labels and supporting rationale.
- `coverage.json`: per-benefit positive/negative/ambiguous counts and coverage gaps.
- `raw-transactions.json`, `negative-transactions.json`, `descriptor-groups.json`: source snapshot and normalized records.
- `card-scope.json`, `ios-catalog.json`, `provenance.json`, `linked-items.json`: scope and source evidence.
- `pull_snapshot.py`: read-only export procedure used by the delegated agent.

Validated 289 distinct case IDs, strictly negative amounts, unknown status preservation, complete per-card labels, and matching model-question keys. The offline bench checks pass. No sensitive rows or credentials are included in tracked documentation.

The existing small fixture and its cached responses remain intact. The bench now accepts a separate dataset directory and explicit case ceiling. To evaluate this expanded fixture later:

```sh
backend/.venv/bin/python backend/scripts/jev_bench.py run \
  --data-dir backend/data/jev-production \
  --prompt descriptor --max-cases 400 --max-usd 0.10
```

That command makes paid requests for uncached cases; it was **not run** as part of building this dataset. Labels should be reviewed before treating the resulting agreement as validated accuracy. The explicit dollar cap is a conservative local preflight check, not a provider-enforced account budget.
