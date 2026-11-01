"""Compare frozen prompts as confirmation suggestions, never automatic recording."""
from collections import Counter
import json

import jev_bench as bench


def summarize():
    data = bench.ROOT / "backend/data/jev-evidence-experiment"
    cases = {c["id"]: c for c in json.loads((data / "fixture.json").read_text())["cases"]}
    output = {}
    for prompt in ("evidence", "confirmation"):
        result = json.loads((data / f"results-{prompt}.json").read_text())
        policies = {}
        for threshold in (.5, .2):
            real = [p for p in result["pairs"] if cases[p["case_id"]]["suite"] == "real"]
            suggested = [p for p in real if p["probabilities"]["match"] >= threshold]
            by_case = {}
            for p in suggested:
                by_case.setdefault(p["case_id"], []).append(p)
            top = [max(ps, key=lambda p: p["probabilities"]["match"]) for ps in by_case.values()]
            synthetic = [p for p in result["pairs"] if cases[p["case_id"]]["suite"] == "synthetic"
                         and p["benefit"] == cases[p["case_id"]]["stress_target"]]
            families = {(cases[p["case_id"]]["descriptor_group"], p["benefit"]) for p in real if p["expected"] == "match"}
            found_families = {(cases[p["case_id"]]["descriptor_group"], p["benefit"]) for p in suggested if p["expected"] == "match"}
            policies[str(threshold)] = {
                "suggested_pairs_by_gold": dict(Counter(p["expected"] for p in suggested)),
                "notifications": len(by_case),
                "top_suggestion_by_gold": dict(Counter(p["expected"] for p in top)),
                "positive_families_found": len(found_families), "positive_families_total": len(families),
                "synthetic_targets": dict(Counter(cases[p["case_id"]]["synthetic_variant"] + ":" +
                    ("suggest" if p["probabilities"]["match"] >= threshold else "hide") for p in synthetic)),
            }
        output[prompt] = {"usage": result["summary"], "policies": policies}
    bench.save(data / "confirmation-comparison.json", output)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    summarize()
