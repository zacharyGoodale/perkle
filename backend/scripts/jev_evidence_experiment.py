"""Prepare and summarize the private richer-context and hypothetical-benefit bench."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import date
from decimal import Decimal
from pathlib import Path
import json

import jev_bench as bench

OUT = bench.ROOT / "backend/data/jev-evidence-experiment"
SOURCE = bench.ROOT / "backend/data/jev-enriched-production"
OLD = bench.ROOT / "backend/data/jev-production"
FIELDS = ("name", "original_description", "amount", "date", "pending", "iso_currency_code",
          "merchant_name", "merchant_category_code", "personal_finance_category", "location",
          "transaction_code", "payment_channel")


def view(row):
    result = {k: row.get(k) for k in FIELDS}
    result["counterparties"] = [{k: c.get(k) for k in ("name", "type", "confidence_level")}
                                for c in row.get("counterparties", [])]
    return result


def context(target, rows):
    related = []
    for row in rows:
        if row["account_id"] != target["account_id"] or row["amount"] <= 0:
            continue
        days = (date.fromisoformat(target["date"]) - date.fromisoformat(row["date"])).days
        if not 0 <= days <= 90:
            continue
        same_merchant = (bool(target.get("merchant_entity_id")) and
                         target["merchant_entity_id"] == row.get("merchant_entity_id")) or target["name"].casefold() == row["name"].casefold()
        adjustment_pair = days == 0 and "ADJ" in target["name"] and "ADJ" in row["name"]
        if same_merchant or adjustment_pair:
            exact = Decimal(str(row["amount"])) == -Decimal(str(target["amount"]))
            related.append((not exact, days, {**view(row), "same_account": True,
                                            "same_merchant_identity": bool(same_merchant),
                                            "days_before_credit": days, "equal_opposite_amount": exact}))
    return [r[2] for r in sorted(related, key=lambda x: (x[0], x[1]))[:5]]


def prepare():
    if (OUT / "fixture.json").exists():
        raise SystemExit("Preserving existing frozen experiment fixture.")
    original = json.loads((OLD / "fixture.json").read_text())
    rows = json.loads((SOURCE / "transactions.json").read_text())
    source = {r["external_id"]: r for r in rows}
    mapping = {r["id"]: r["source_external_id"] for r in json.loads((OLD / "negative-transactions.json").read_text())}
    cases = []
    for old in original["cases"]:
        row = source[mapping[old["id"]]]
        c = deepcopy(old)
        c.update(transaction={**view(row), "card": old["transaction"]["card"]},
                 related_transactions=context(row, rows), suite="real", source_status_known=True)
        if row.get("original_description") == "AMEX DUNKIN' CREDIT" and c["transaction"]["card"] == "amex-gold":
            c["expected"]["dunkin-credit"] = "match"
            c["label_evidence"] = "Updated from unknown: raw bank description explicitly names Amex Dunkin credit."
        if row["name"] == "ADJ REDIST PURCHASE BAL":
            assert any(r["equal_opposite_amount"] and "ADJ" in r["name"] for r in c["related_transactions"])
            c["expected"] = dict.fromkeys(c["expected"], "no_match")
            c["label_evidence"] = "Balance redistribution wording plus equal opposite same-day adjustment on same account."
        cases.append(c)
    # Actual merchant credits remain ambiguous; invented benefits never enter real candidates.
    targets = {"Nordstrom": "Nordstrom", "Nordstrom Direct": "Nordstrom",
               "UNIQLO Pearl District": "Uniqlo", "JUNIPERAPPAREL* ********": "Juniper Apparel",
               "SP WILLOW HOME": "Willow Home", "CVS": "CVS", "Popeyes": "Popeyes",
               "Alaska Airlines": "Alaska Airlines", "FSP*MAPLE & SHORE INN": "Maple & Shore Inn",
               "Fandango": "Fandango"}
    synthetic = []
    for real in cases:
        merchant = targets.get(real["transaction"]["name"])
        if not merchant:
            continue
        slug = "hypothetical-" + merchant.lower().replace(" ", "-").replace("&", "and")
        benefit = {"slug": slug, "name": merchant + " Shopping Statement Credit", "tracking_mode": "auto",
                   "notes": f"Issuer statement credit reimbursing eligible {merchant} purchases. Merchant refunds, returns and balance adjustments are excluded.", "detection_rules": {"credit_patterns": []}}
        for variant in ("actual_merchant_credit", "explicit_refund", "explicit_issuer_credit"):
            c = deepcopy(real)
            c.update(id=real["id"] + "-" + variant, suite="synthetic", synthetic_variant=variant,
                     stress_target=slug, parent_case_id=real["id"], candidate_benefits=original["cards"][real["transaction"]["card"]] + [benefit])
            c["expected"] = dict.fromkeys([b["slug"] for b in c["candidate_benefits"]], "no_match")
            if variant == "actual_merchant_credit":
                c["expected"].update(real["expected"])
                c["expected"][slug] = "insufficient_evidence"
                c["label_evidence"] = "Real merchant credit plus invented benefit; origin not independently proven. Stress criterion: must not auto-record hypothetical benefit."
            elif variant == "explicit_refund":
                c["transaction"]["original_description"] = "MERCHANT REFUND OF PRIOR PURCHASE: " + merchant
                c["label_evidence"] = "Synthetic explicit merchant refund; fictional benefit must not match."
            else:
                issuer = {"amex-platinum": "American Express", "amex-gold": "American Express", "venture-x": "Capital One", "chase-sapphire-reserve": "Chase"}[c["transaction"]["card"]]
                c["transaction"]["name"] = c["transaction"]["original_description"] = issuer + " " + benefit["name"]
                c["expected"][slug] = "match"
                c["label_evidence"] = "Synthetic explicit issuer credit for fictional benefit; keeps purchase context to test refund overreach."
            synthetic.append(c)
    fixture = {**original, "task": "credit_evidence", "source": "Frozen enriched production snapshot; independently marked synthetic stress suite",
               "label_status": "provisional agent labels; two evidence-based corrections; user review pending",
               "cases": cases + synthetic, "threshold_policy": {"auto_match_probability": .9, "hide_no_match_probability": .9}}
    bench.save(OUT / "fixture.json", fixture)
    print(f"Prepared {len(cases)} real and {len(synthetic)} synthetic cases; no model calls.")


def summarize():
    fixture = json.loads((OUT / "fixture.json").read_text())
    results = json.loads((OUT / "results-evidence.json").read_text())
    cases = {c["id"]: c for c in fixture["cases"]}
    summaries = {}
    for suite in ("real", "synthetic"):
        pairs = [p for p in results["pairs"] if cases[p["case_id"]]["suite"] == suite]
        if suite == "synthetic":
            pairs = [p for p in pairs if p["benefit"] == cases[p["case_id"]]["stress_target"]]
        def counts(ps, threshold):
            return dict(Counter(("gold=" + p["expected"] + ",action=" + bench.action_for(p["probabilities"], threshold)) for p in ps))
        groups = {}
        for p in pairs:
            groups.setdefault((cases[p["case_id"]]["descriptor_group"], p["benefit"]), []).append(p)
        summaries[suite] = {"pairs": len(pairs), "thresholds": {str(t): counts(pairs, t) for t in (.8, .9, .95, .99)}}
        if suite == "real":
            summaries[suite]["families_at_90"] = [
                {"group": g, "benefit": b, "expected": ps[0]["expected"],
                 "actions": dict(Counter(bench.action_for(p["probabilities"]) for p in ps))} for (g, b), ps in groups.items()]
    summaries["synthetic_targets"] = [
        {**p, "variant": cases[p["case_id"]]["synthetic_variant"], "source_name": cases[p["case_id"]]["transaction"]["name"]}
        for p in results["pairs"] if cases[p["case_id"]]["suite"] == "synthetic" and p["benefit"] == cases[p["case_id"]]["stress_target"]]
    # Post-hoc diagnostic, separate from the predeclared conservative policy.
    real = [p for p in results["pairs"] if cases[p["case_id"]]["suite"] == "real"]
    comparisons = {}
    for name, floor in (("predeclared_no_match_90", None), ("diagnostic_match_10_or_uncertain_50", .10)):
        grouped = {}
        for p in real:
            grouped.setdefault(p["case_id"], []).append(p)
        comparisons[name] = {
            "pair_actions": dict(Counter("gold=" + p["expected"] + ",action=" + bench.action_for(p["probabilities"], review_floor=floor) for p in real)),
            "transaction_actions": dict(Counter(
                "auto_record" if any(bench.action_for(p["probabilities"], review_floor=floor) == "auto_record" for p in ps)
                else "review" if any(bench.action_for(p["probabilities"], review_floor=floor) == "review" for p in ps)
                else "hide" for ps in grouped.values()))}
    summaries["policy_comparison"] = comparisons
    bench.save(OUT / "decision-summary.json", summaries)
    print(json.dumps({k: {a: b for a, b in v.items() if a != "families_at_90"} for k, v in summaries.items() if k != "synthetic_targets"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "summarize"])
    args = parser.parse_args()
    prepare() if args.command == "prepare" else summarize()
