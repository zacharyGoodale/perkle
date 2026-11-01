"""Budgeted, cached confirmation-prompt experiments on frozen private fixtures."""
import argparse
from collections import Counter
from decimal import Decimal
import json
import os
from pathlib import Path
import statistics
import time
import urllib.error
import urllib.request

from dotenv import dotenv_values
import jev_bench as bench

OUT = bench.ROOT / "backend/data/jev-hillclimb"
POLICY = "v1"
CHOICES = {
    "suggest_confirmation": "Positive target-benefit or merchant/program connection exists, and no affirmative exclusion applies. Ask the user before recording usage.",
    "do_not_suggest": "Affirmative evidence excludes this candidate, OR no identifiable positive connection exists. Do not offer this candidate.",
}


def spent():
    actual = sum(json.loads(p.read_text())["response"]["usage"]["input_tokens"] * bench.RATE
                 for p in (OUT / "responses").glob("*.json"))
    uncertain = sum(json.loads(p.read_text())["reserved_usd"] for p in (OUT / "pending").glob("*.json")
                    if not (OUT / "responses" / p.name).exists())
    return actual + uncertain


def request(case, cards, prompt):
    state = {"transaction": case["transaction"], "related_transactions": case.get("related_transactions", [])}
    if isinstance(prompt, dict) and prompt.get("transaction_fields"):
        state["transaction"] = {k: v for k, v in case["transaction"].items() if k in prompt["transaction_fields"]}
    if isinstance(prompt, dict) and prompt.get("include_related_transactions") is False:
        state.pop("related_transactions")
    if isinstance(prompt, dict) and prompt.get("amount_rules"):
        txn = case["transaction"]
        known_names = {b["slug"]: b["name"] for b in cards.get(txn["card"], [])}
        amounts = {}
        for b in bench.benefits_for(case, cards):
            rules = [r for r in prompt["amount_rules"] if r["card"] == txn["card"]
                     and txn.get("iso_currency_code") == "USD"
                     and r["benefit"] == b["slug"] and known_names.get(b["slug"]) == b["name"]
                     and r["start"] <= txn.get("date", "") <= r["end"]]
            assert len(rules) <= 1
            amounts[b["slug"]] = {"cap_version_known": bool(rules)}
            if rules:
                rule = rules[0]
                credit = abs(Decimal(str(txn["amount"])))
                cap = Decimal(str(rule["cap_usd"]))
                amounts[b["slug"]].update(period_cap_usd=rule["cap_usd"], period=rule["period"],
                    exact_full_cap_match=credit == cap, at_or_below_full_cap=credit <= cap,
                    remaining_allowance_known=False)
        state["benefit_amount_context"] = amounts
    if isinstance(prompt, dict) and prompt.get("related_transaction_fields") and "related_transactions" in state:
        state["related_transactions"] = [{k: v for k, v in row.items() if k in prompt["related_transaction_fields"]}
                                         for row in state["related_transactions"]]
    if isinstance(prompt, dict) and prompt.get("include_candidate_roster"):
        state["candidate_benefits"] = [{"name": b["name"], "notes": b.get("notes", "")} for b in bench.benefits_for(case, cards)]
        if prompt.get("candidate_roster_names_only"):
            state["candidate_benefits"] = [b["name"] for b in bench.benefits_for(case, cards)]
    if isinstance(prompt, dict) and "flow_criteria" in prompt:
        criteria = {b["slug"]: prompt["benefit_criterion"].replace("{benefit_name}", b["name"]).replace("{benefit_notes}", b.get("notes", ""))
                    for b in bench.benefits_for(case, cards)}
        assert "__none" not in criteria
        criteria["__none"] = prompt["none_criterion"]
        return {"model": bench.MODEL, "state": state, "questions": {
            "__flow": {"type": "choice", "instructions": prompt["flow_instructions"], "criteria": prompt["flow_criteria"]},
            "__benefit": {"type": "choice", "instructions": prompt["benefit_instructions"], "criteria": criteria}}}
    instructions = prompt["instructions"] if isinstance(prompt, dict) else prompt
    criteria = prompt["criteria"] if isinstance(prompt, dict) else CHOICES
    assert set(criteria) == set(CHOICES)
    return {"model": bench.MODEL,
            "state": state,
            "questions": {b["slug"]: {"type": "choice", "instructions": instructions.replace("{benefit_name}", b["name"]).replace("{benefit_notes}", b.get("notes", "")),
                                       "criteria": {label: text.replace("{benefit_name}", b["name"]).replace("{benefit_notes}", b.get("notes", "")) for label, text in criteria.items()}}
                          for b in bench.benefits_for(case, cards)}}


def fixtures():
    base = json.loads((bench.ROOT / "backend/data/jev-evidence-experiment/fixture.json").read_text())
    labels = json.loads((OUT / "suggestion-labels.json").read_text())
    # Label/split format is deliberately explicit and verified before any paid run.
    cases = []
    for c in base["cases"]:
        row = {**c, "suggestion_expected": {}, "split": labels["splits"][c["id"]]}
        for slug, old in c["expected"].items():
            row["suggestion_expected"][slug] = ("suggest_confirmation" if old == "match" else "do_not_suggest") if old != "insufficient_evidence" else labels["overrides"][c["id"]][slug]["label"]
        cases.append(row)
    for filename, split in (("fresh-challenge.json", "fresh"), ("final-challenge.json", "final"),
                            ("unseen-v2-challenge.json", "unseen")):
        path = OUT / filename
        if not path.exists():
            continue
        for c in json.loads(path.read_text())["cases"]:
            cases.append({**c, "id": c.get("id", c.get("case_id")), "split": split,
                          "suggestion_expected": c["expected_suggestion"]})
    if POLICY == "v2":
        index = {c["id"]: c for c in cases}
        for change in json.loads((OUT / "policy-v2.json").read_text())["changes"]:
            c = index[change["case_id"]]
            assert c["suggestion_expected"][change["benefit"]] == change["from"]
            c["suggestion_expected"][change["benefit"]] = change["to"]
    families = {}
    for c in cases:
        assert set(c["suggestion_expected"]) == {b["slug"] for b in bench.benefits_for(c, base["cards"])}
        assert set(c["suggestion_expected"].values()) <= set(CHOICES)
        if c["split"] in ("dev", "validation"):
            assert families.setdefault(c["descriptor_group"], c["split"]) == c["split"]
    return base["cards"], cases


def run(prompt_path, split, threshold=.5):
    cards, cases = fixtures()
    prompt = json.loads(prompt_path.read_text()) if prompt_path.suffix == ".json" else prompt_path.read_text()
    key = os.getenv("TYPESAFE_API_KEY") or dotenv_values(bench.ROOT / ".env").get("TYPESAFE_API_KEY")
    if not key:
        raise SystemExit("Missing TYPESAFE_API_KEY")
    for i, c in enumerate(cases):
        if split == "tuning" and c["split"] == "unseen":
            continue
        if split not in ("all", "tuning") and c["split"] != split:
            continue
        body = request(c, cards, prompt)
        cache = OUT / "responses" / f"{bench.digest(body)}.json"
        if cache.exists():
            continue
        payload = json.dumps(body).encode()
        reserve = (len(payload) + 8192) * bench.RATE
        if spent() + reserve > 4.99:
            raise SystemExit("$5 experiment cap reached; cache preserved")
        pending = OUT / "pending" / cache.name
        if pending.exists():
            raise SystemExit("Unresolved prior attempt; preserve its budget reservation instead of retrying")
        bench.save(pending, {"reserved_usd": reserve})
        req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=payload,
              headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            raise SystemExit(f"TypeSafe HTTP {exc.code}; no retry") from None
        except urllib.error.URLError:
            raise SystemExit("Network unavailable; no retry") from None
        bench.save(cache, {"response": result, "seconds": time.monotonic() - start})
        pending.unlink()
        if i % 25 == 0:
            print(f"Case {i + 1}; cumulative new Jev spend ${spent():.6f}", flush=True)
    report(prompt_path, threshold)


def report(prompt_path, threshold=.5):
    cards, cases = fixtures()
    prompt = json.loads(prompt_path.read_text()) if prompt_path.suffix == ".json" else prompt_path.read_text()
    pairs, pending, counted, tokens, timings = [], 0, set(), 0, []
    for c in cases:
        body = request(c, cards, prompt)
        digest = bench.digest(body)
        path = OUT / "responses" / f"{digest}.json"
        if not path.exists():
            pending += 1
            continue
        cache = json.loads(path.read_text())
        response = cache["response"]
        multiclass = isinstance(prompt, dict) and "flow_criteria" in prompt
        assert set(response["answers"]) == ({"__flow", "__benefit"} if multiclass else set(c["suggestion_expected"]))
        if digest not in counted:
            counted.add(digest)
            tokens += response["usage"]["input_tokens"]
            timings.append(cache["seconds"])
        for slug, gold in c["suggestion_expected"].items():
            p_excluded = 0
            if multiclass:
                a = response["answers"]["__benefit"]
                assert set(a["probabilities"]) == set(c["suggestion_expected"]) | {"__none"}
                p_suggest = a["probabilities"][slug]
                flow_probs = response["answers"]["__flow"]["probabilities"]
                assert set(flow_probs) == set(prompt["flow_criteria"])
                kept_choice = prompt.get("flow_non_excluded_choice", "no_affirmative_exclusion")
                p_excluded = sum(v for k, v in flow_probs.items() if k != kept_choice)
            else:
                a = response["answers"][slug]
                assert set(a["probabilities"]) == set(CHOICES)
                p_suggest = a["probabilities"]["suggest_confirmation"]
            flow_threshold = prompt.get("flow_reject_threshold", .5) if isinstance(prompt, dict) else .5
            predicted = "suggest_confirmation" if p_suggest >= threshold and p_excluded < flow_threshold else "do_not_suggest"
            pairs.append({"case_id": c["id"], "split": c["split"], "suite": c["suite"], "benefit": slug,
                          "expected": gold, "predicted": predicted, "p_suggest": p_suggest, "p_excluded": p_excluded,
                          "origin_label": c.get("expected", {}).get(slug), "descriptor_group": c["descriptor_group"]})
    grouped_cases = {}
    for p in pairs:
        grouped_cases.setdefault(p["case_id"], []).append(p)
    recommendations = []
    for case_id, group in grouped_cases.items():
        eligible = [p for p in group if p["predicted"] == "suggest_confirmation"]
        top = max(eligible, key=lambda p: p["p_suggest"]) if eligible else None
        allowed = [p["benefit"] for p in group if p["expected"] == "suggest_confirmation"]
        recommendations.append({"case_id": case_id, "split": group[0]["split"], "suite": group[0]["suite"],
            "benefit": top["benefit"] if top else None, "requires_user_confirmation": bool(top),
            "allowed_by_frozen_rubric": allowed,
            "correct_for_frozen_rubric": top["benefit"] in allowed if top else not allowed})
    summaries = {}
    for split in ("dev", "validation", "fresh", "final", "unseen", "all"):
        ps = [p for p in pairs if split == "all" or p["split"] == split]
        expected_cases = [c for c in cases if split == "all" or c["split"] == split]
        completed_cases = {p["case_id"] for p in ps}
        positives = sum(p["expected"] == "suggest_confirmation" for p in ps)
        tp = sum(p["expected"] == p["predicted"] == "suggest_confirmation" for p in ps)
        fp = sum(p["expected"] != p["predicted"] == "suggest_confirmation" for p in ps)
        correct = sum(p["expected"] == p["predicted"] for p in ps)
        clear = [p for p in ps if p["origin_label"] == "match" and p["suite"] == "real"]
        grouped = {}
        for p in ps:
            grouped.setdefault(p["case_id"], []).append(p)
        eligible_transactions = sum(any(p["expected"] == "suggest_confirmation" for p in group) for group in grouped.values())
        top = [max((p for p in group if p["predicted"] == "suggest_confirmation"), key=lambda p: p["p_suggest"])
               for group in grouped.values() if any(p["predicted"] == "suggest_confirmation" for p in group)]
        decisions = [r for r in recommendations if split == "all" or r["split"] == split]
        summaries[split] = {"expected_cases": len(expected_cases), "completed_cases": len(completed_cases),
                            "complete": len(completed_cases) == len(expected_cases),
                            "pairs": len(ps), "positives": positives, "tp": tp, "fp": fp, "fn": positives - tp,
                            "suggestion_recall": tp / positives if positives else None,
                            "agreement": correct / len(ps) if ps else None,
                            "eligible_transactions": eligible_transactions, "notifications": len(top),
                            "correct_top_suggestions": sum(p["expected"] == "suggest_confirmation" for p in top),
                            "wrong_top_suggestions": sum(p["expected"] == "do_not_suggest" for p in top),
                            "notification_recall": sum(p["expected"] == "suggest_confirmation" for p in top) / eligible_transactions if eligible_transactions else None,
                            "transaction_decision_agreement": sum(r["correct_for_frozen_rubric"] for r in decisions) / len(decisions) if decisions else None,
                            "clear_credit_recall": sum(p["predicted"] == "suggest_confirmation" for p in clear) / len(clear) if clear else None,
                            "real_wrong_benefit_suggestions": sum(p["origin_label"] == "no_match" and p["expected"] == "do_not_suggest" and p["predicted"] == "suggest_confirmation" and p["suite"] == "real" for p in ps)}
    result = {"prompt_hash": bench.digest(prompt), "evaluation_fixture_hash": bench.digest(cases), "label_policy": POLICY,
              "threshold": threshold, "pending_cases": pending, "unique_requests": len(counted),
              "tokens": tokens, "cost_usd": tokens * bench.RATE, "cumulative_spend": spent(),
              "median_seconds": statistics.median(timings) if timings else None, "summary": summaries, "pairs": pairs,
              "recommendations": recommendations}
    suffix = "" if threshold == .5 else f"-t{round(threshold * 1000):03d}"
    if POLICY != "v1":
        suffix += "-" + POLICY
    bench.save(OUT / f"results-{prompt_path.stem}{suffix}.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("pairs", "recommendations")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "report"])
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--split", choices=["dev", "validation", "fresh", "final", "unseen", "tuning", "all"], default="dev")
    parser.add_argument("--threshold", type=float, default=.5)
    parser.add_argument("--label-policy", choices=["v1", "v2"], default="v1")
    args = parser.parse_args()
    POLICY = args.label_policy
    if not 0 < args.threshold < 1:
        parser.error("threshold must be between 0 and 1")
    run(args.prompt, args.split, args.threshold) if args.command == "run" else report(args.prompt, args.threshold)
