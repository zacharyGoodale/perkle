"""Offline checks: no real transactions, network requests, or API key required."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import jev_bench as bench
import jev_evidence_experiment as experiment
import jev_luna_cascade as luna
import jev_hillclimb as hill


class BenchTest(unittest.TestCase):
    def test_single_transaction_amount_context_respects_version_and_currency(self):
        case = {"transaction": {"card": "test", "name": "Credit", "amount": -7.0,
                                "date": "2025-02-01", "iso_currency_code": "USD"},
                "related_transactions": [{"name": "Must not be sent"}]}
        cards = {"test": [{"slug": "benefit", "name": "Example", "detection_rules": {"credit_patterns": ["SECRET"]}}]}
        spec = {"instructions": "Evaluate", "criteria": hill.CHOICES, "include_related_transactions": False,
                "amount_rules": [{"card": "test", "benefit": "benefit", "start": "2025-01-01",
                                  "end": "2025-12-31", "cap_usd": 7, "period": "monthly"}]}
        body = hill.request(case, cards, spec)
        self.assertNotIn("related_transactions", body["state"])
        self.assertNotIn("SECRET", json.dumps(body))
        hints = body["state"]["benefit_amount_context"]["benefit"]
        self.assertTrue(hints["exact_full_cap_match"])
        self.assertFalse(hints["remaining_allowance_known"])
        for key, value in (("date", "2024-12-31"), ("iso_currency_code", "EUR")):
            changed = {**case, "transaction": {**case["transaction"], key: value}}
            self.assertEqual(hill.request(changed, cards, spec)["state"]["benefit_amount_context"]["benefit"],
                             {"cap_version_known": False})

    def test_shared_flow_gate_overrides_benefit_score(self):
        case = {"id": "test", "transaction": {"card": "test", "name": "MERCHANT REFUND", "amount": -5},
                "suggestion_expected": {"benefit": "do_not_suggest"}, "suite": "real", "split": "dev",
                "descriptor_group": "refund", "expected": {"benefit": "no_match"}}
        cards = {"test": [{"slug": "benefit", "name": "Example", "notes": "Terms"}]}
        spec = {"flow_instructions": "Flow", "flow_criteria": {"excluded_flow": "Refund", "no_affirmative_exclusion": "Other"},
                "benefit_instructions": "Benefit", "benefit_criterion": "{benefit_name}: {benefit_notes}", "none_criterion": "Unrelated"}
        body = hill.request(case, cards, spec)
        self.assertEqual(body["questions"]["__benefit"]["criteria"], {"benefit": "Example: Terms", "__none": "Unrelated"})
        response = {"usage": {"input_tokens": 100}, "answers": {
            "__flow": {"probabilities": {"excluded_flow": .9, "no_affirmative_exclusion": .1}},
            "__benefit": {"probabilities": {"benefit": .95, "__none": .05}}}}
        with tempfile.TemporaryDirectory() as directory, patch.object(hill, "OUT", Path(directory)), patch.object(hill, "fixtures", return_value=(cards, [case])):
            path = hill.OUT / "prompt.json"
            bench.save(path, spec)
            bench.save(hill.OUT / "responses" / (bench.digest(body) + ".json"), {"response": response, "seconds": .1})
            with contextlib.redirect_stdout(io.StringIO()):
                hill.report(path)
            result = json.loads((hill.OUT / "results-prompt.json").read_text())
        self.assertEqual(result["pairs"][0]["predicted"], "do_not_suggest")
        self.assertEqual(result["summary"]["dev"]["fp"], 0)
        self.assertIsNone(result["recommendations"][0]["benefit"])

    def test_only_top_candidate_is_emitted_and_secondary_error_stays_visible(self):
        case = {"id": "test", "transaction": {"card": "test", "name": "Credit", "amount": -5},
                "suggestion_expected": {"right": "suggest_confirmation", "wrong": "do_not_suggest"},
                "suite": "fresh", "split": "fresh", "descriptor_group": "overlap"}
        cards = {"test": [{"slug": "right", "name": "Right"}, {"slug": "wrong", "name": "Wrong"}]}
        spec = {"flow_instructions": "Flow", "flow_criteria": {"refund": "Refund", "other": "Other"},
                "flow_non_excluded_choice": "other", "flow_reject_threshold": .8,
                "benefit_instructions": "Benefit", "benefit_criterion": "{benefit_name}", "none_criterion": "Unrelated"}
        body = hill.request(case, cards, spec)
        response = {"usage": {"input_tokens": 100}, "answers": {
            "__flow": {"probabilities": {"refund": .1, "other": .9}},
            "__benefit": {"probabilities": {"right": .6, "wrong": .3, "__none": .1}}}}
        with tempfile.TemporaryDirectory() as directory, patch.object(hill, "OUT", Path(directory)), patch.object(hill, "fixtures", return_value=(cards, [case])):
            path = hill.OUT / "prompt.json"
            bench.save(path, spec)
            bench.save(hill.OUT / "responses" / (bench.digest(body) + ".json"), {"response": response, "seconds": .1})
            with contextlib.redirect_stdout(io.StringIO()):
                hill.report(path, .25)
            result = json.loads((hill.OUT / "results-prompt-t250.json").read_text())
        self.assertEqual(len(result["recommendations"]), 1)
        self.assertEqual(result["recommendations"][0]["benefit"], "right")
        self.assertEqual(result["summary"]["fresh"]["fp"], 1)
        self.assertEqual(result["summary"]["fresh"]["wrong_top_suggestions"], 0)

    def test_hillclimb_requests_and_cumulative_budget(self):
        case = {"transaction": {"card": "test", "name": "Credit", "amount": -5},
                "expected_suggestion": {"benefit": "suggest_confirmation"}}
        cards = {"test": [{"slug": "benefit", "name": "Example", "notes": "Terms",
                           "detection_rules": {"credit_patterns": ["SECRET"]}}]}
        body = hill.request(case, cards, "Evaluate {benefit_name}: {benefit_notes}")
        self.assertEqual(body["questions"]["benefit"]["instructions"], "Evaluate Example: Terms")
        self.assertNotIn("SECRET", json.dumps(body))
        self.assertNotIn("expected_suggestion", json.dumps(body))
        roster = hill.request(case, cards, {"instructions": "{benefit_name}", "criteria": hill.CHOICES,
                                           "include_candidate_roster": True})
        self.assertEqual(roster["state"]["candidate_benefits"], [{"name": "Example", "notes": "Terms"}])
        self.assertNotIn("SECRET", json.dumps(roster))
        focused = hill.request(case, cards, {"instructions": "{benefit_name}",
            "criteria": {"suggest_confirmation": "Confirm {benefit_name}: {benefit_notes}",
                         "do_not_suggest": "Other than {benefit_name}"},
            "include_candidate_roster": True, "candidate_roster_names_only": True,
            "transaction_fields": ["card", "name"], "include_related_transactions": False})
        self.assertEqual(focused["questions"]["benefit"]["criteria"]["suggest_confirmation"], "Confirm Example: Terms")
        self.assertEqual(focused["state"]["transaction"], {"card": "test", "name": "Credit"})
        self.assertEqual(focused["state"]["candidate_benefits"], ["Example"])
        self.assertNotIn("related_transactions", focused["state"])
        case["related_transactions"] = [{"name": "Offsetting debit", "same_account": True,
                                         "amount": 5, "personal_finance_category": {"primary": "OTHER"}}]
        lean = hill.request(case, cards, {"instructions": "{benefit_name}", "criteria": hill.CHOICES,
                            "related_transaction_fields": ["name", "same_account", "amount"]})
        self.assertEqual(lean["state"]["related_transactions"], [{"name": "Offsetting debit", "same_account": True, "amount": 5}])
        with tempfile.TemporaryDirectory() as directory, patch.object(hill, "OUT", Path(directory)):
            bench.save(hill.OUT / "responses/a.json", {"response": {"usage": {"input_tokens": 100}}})
            bench.save(hill.OUT / "responses/b.json", {"response": {"usage": {"input_tokens": 200}}})
            self.assertAlmostEqual(hill.spent(), 300 * bench.RATE)
            bench.save(hill.OUT / "pending/lost.json", {"reserved_usd": .001})
            bench.save(hill.OUT / "pending/a.json", {"reserved_usd": .001})
            self.assertAlmostEqual(hill.spent(), 300 * bench.RATE + .001)

    def test_request_excludes_labels_and_detection_patterns(self):
        case = {"id": "test", "transaction": {"card": "test", "name": "Example credit", "amount": -5,
                                "status": "posted"}, "expected": {"example": "match"}}
        cards = {"test": [{"slug": "example", "name": "Example Benefit",
                           "detection_rules": {"credit_patterns": ["SECRET_PATTERN"]}}]}
        for prompt in ("contextual", "compact", "descriptor", "evidence", "confirmation"):
            request = bench.request_for(case, cards, prompt)
            self.assertEqual(set(request["questions"]), {"example"})
            self.assertNotIn("SECRET_PATTERN", json.dumps(request))
            self.assertNotIn("expected", json.dumps(request))
        self.assertNotIn('"status"', json.dumps(bench.request_for(case, cards, "descriptor")["state"]))
        self.assertEqual(bench.expected_for(case, cards["test"]), {"example": "match"})
        case["expected"] = {}
        with self.assertRaises(ValueError):
            bench.expected_for(case, cards["test"])

    def test_metrics_count_missed_and_false_matches(self):
        benefits = [{"slug": "yes", "name": "Yes"}, {"slug": "no", "name": "No"}]
        case = {"id": "test", "transaction": {"card": "test", "name": "credit", "amount": -5},
                "expected": {"yes": "match", "no": "no_match"}, "reviewed_by_user": False}
        fixture = {"cards": {"test": benefits}, "cases": [case, {**case, "id": "repeat"}]}
        response = {"usage": {"input_tokens": 100}, "answers": {
            "yes": {"choice": "insufficient_evidence", "confidence": 1, "probabilities": {"match": 0, "no_match": 0, "insufficient_evidence": 1}},
            "no": {"choice": "match", "confidence": 1, "probabilities": {"match": 1, "no_match": 0, "insufficient_evidence": 0}}}}
        with tempfile.TemporaryDirectory() as directory, patch.object(bench, "DATA", Path(directory)):
            body = bench.request_for(case, fixture["cards"])
            bench.save(bench.DATA / "responses" / f"{bench.digest(body)}.json",
                       {"response": response, "seconds": 0.1})
            with contextlib.redirect_stdout(io.StringIO()):
                bench.report(fixture)
            result = json.loads((bench.DATA / "results-contextual.json").read_text())["summary"]
        self.assertEqual(result["jev"]["unsupported_matches"], 2)
        self.assertEqual(result["jev"]["missed_matches"], 2)
        self.assertEqual(result["jev"]["recall"], 0)
        self.assertEqual(result["unique_requests"], 1)
        self.assertAlmostEqual(result["cost_usd"], 100 * bench.RATE)

    def test_thresholds_preserve_uncertainty_and_case_candidates(self):
        self.assertEqual(bench.action_for({"match": .01, "no_match": .01, "insufficient_evidence": .98}), "review")
        self.assertEqual(bench.action_for({"match": .90, "no_match": .05, "insufficient_evidence": .05}), "auto_record")
        self.assertEqual(bench.action_for({"match": .05, "no_match": .90, "insufficient_evidence": .05}), "hide")
        self.assertEqual(bench.action_for({"match": .01, "no_match": .01, "insufficient_evidence": .98}, review_floor=.1), "review")
        self.assertEqual(bench.action_for({"match": .01, "no_match": .89, "insufficient_evidence": .1}, review_floor=.1), "hide")
        cards = {"test": [{"slug": "real", "name": "Real"}]}
        case = {"transaction": {"card": "test", "name": "credit", "amount": -5},
                "candidate_benefits": [{"slug": "fake", "name": "Fake"}]}
        self.assertEqual(set(bench.request_for(case, cards, "evidence")["questions"]), {"fake"})
        self.assertEqual(bench.benefits_for(case, {}), case["candidate_benefits"])
        del case["candidate_benefits"]
        self.assertEqual(set(bench.request_for(case, cards, "evidence")["questions"]), {"real"})

    def test_context_uses_only_prior_transactions_on_same_account(self):
        credit = {"account_id": "one", "name": "Store", "merchant_entity_id": "merchant",
                  "date": "2026-10-10", "amount": -50}
        purchase = {**credit, "date": "2026-10-01", "amount": 50}
        context = experiment.context(credit, [purchase, {**purchase, "account_id": "two"},
                                               {**purchase, "date": "2026-10-11"}])
        self.assertEqual(len(context), 1)
        self.assertEqual(context[0]["days_before_credit"], 9)
        self.assertTrue(context[0]["equal_opposite_amount"])
        self.assertNotIn("account_id", context[0])

    def test_luna_promotion_requires_grounded_explicit_evidence(self):
        txn = {"name": "Shop Saks with Platinum Credit", "amount": -50}
        answer = {"decision": "match", "basis": "explicit_benefit_description",
                  "evidence_quote": "Shop Saks with Platinum Credit", "reason": "Named benefit credit"}
        self.assertEqual(luna.cascade_action(answer, txn), "auto_record")
        self.assertEqual(luna.cascade_action({**answer, "evidence_quote": "Invented issuer confirmation"}, txn), "review")
        self.assertEqual(luna.cascade_action({**answer, "basis": "merchant_context_only"}, txn), "review")
        case = {"transaction": {**txn, "card": "test"}, "expected": {"saks": "match"}}
        request = luna.request_for(case, [{"slug": "saks", "name": "Saks", "value": 50}])
        payload = json.loads(request["input"])
        self.assertTrue(payload["candidate_benefits"][0]["equals_configured_cap"])
        self.assertNotIn("expected", payload)
        self.assertNotIn("jev_probabilities", payload)
        self.assertFalse(request["store"])


if __name__ == "__main__":
    unittest.main()
