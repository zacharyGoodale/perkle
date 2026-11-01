"""Run/report the published pseudonymized confirmation bench with ignored API caches."""
import argparse
import json
import re

import jev_bench as bench
import jev_hillclimb as hill

FIXTURE = bench.ROOT / "backend/fixtures/jev/fixture.json"
PROMPT = bench.ROOT / "docs/research/jev-confirmation-single-transaction.json"
OUTPUT = bench.ROOT / "backend/data/jev-public-bench"
PUBLISHED = bench.ROOT / "docs/research/jev-final-baseline-results.json"


def fixtures():
    data = json.loads(FIXTURE.read_text())
    assert data["label_policy"] == "v2"
    for case in data["cases"]:
        assert set(case["suggestion_expected"]) == {b["slug"] for b in bench.benefits_for(case, data["cards"])}
        assert "related_transactions" not in case
    return data["cards"], data["cases"]


def request_hashes():
    cards, cases = fixtures()
    prompt = json.loads(PROMPT.read_text())
    return {bench.digest(hill.request(case, cards, prompt)) for case in cases}


def restore_published():
    """Allow a clean checkout to recompute the report without API credentials."""
    result = json.loads(PUBLISHED.read_text())
    _, cases = fixtures()
    assert result["fixture_hash"] == bench.digest(json.loads(FIXTURE.read_text())), "Published fixture differs"
    assert result["evaluation_fixture_hash"] == bench.digest(cases), "Published evaluation differs"
    assert result["prompt_hash"] == bench.digest(json.loads(PROMPT.read_text())), "Published prompt differs"
    assert result["label_policy"] == "v2" and result["threshold"] == .25
    expected = request_hashes()
    entries = result["responses"]
    hashes = [entry["request_hash"] for entry in entries]
    assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes), "Invalid response hash"
    assert len(hashes) == len(set(hashes)) and set(hashes) == expected, "Response hashes differ from current requests"
    for entry in entries:
        bench.save(OUTPUT / "responses" / (entry["request_hash"] + ".json"),
                   {"response": entry["response"], "seconds": entry["seconds"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "report", "publish"])
    args = parser.parse_args()
    previous_spent = hill.spent()
    hill.OUT = OUTPUT
    public_spent = hill.spent
    hill.spent = lambda: previous_spent + public_spent()
    hill.fixtures = fixtures
    hill.POLICY = "v2"
    if args.command == "run":
        hill.run(PROMPT, "all", .25)
    elif args.command == "report":
        restore_published()
        hill.report(PROMPT, .25)
    else:
        source = OUTPUT / f"results-{PROMPT.stem}-t250-v2.json"
        result = json.loads(source.read_text())
        assert not result["pending_cases"] and result["summary"]["all"]["complete"]
        result["fixture_hash"] = bench.digest(json.loads(FIXTURE.read_text()))
        result["provenance"] = "Paid rerun of pseudonymized replay fixture; no new holdout, labels remain provisional."
        result.pop("cumulative_spend", None)
        # Answers contain only public fixture IDs, chosen categories and numerical scores.
        result["responses"] = [{"request_hash": digest,
                                **json.loads((OUTPUT / "responses" / (digest + ".json")).read_text())}
                               for digest in sorted(request_hashes())]
        bench.save(PUBLISHED, result)
        print("Published docs/research/jev-final-baseline-results.json with scores and response usage; raw requests/caches remain ignored.")


if __name__ == "__main__":
    main()
