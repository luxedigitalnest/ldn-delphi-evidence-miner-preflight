"""Offline-only tests. Synthetic fixtures are never competition submissions."""
import copy
import unittest
from datetime import datetime, timedelta, timezone
from evidence_preflight import EvidenceError, evidence_key, public_url, validate

NOW = datetime(2026, 11, 22, 14, 0, tzinfo=timezone.utc)
def make():
    return {
        "market_id":"synthetic_test_market_001",
        "side":"YES",
        "fact":"The fictional event notice explicitly includes a stated date and scope that could influence this test-only market.",
        "why_novel":"An independent dated primary document gives a new scope not included in earlier summaries.",
        "human_reviewed":True,
        "evidence_cutoff":"2026-11-30T17:00:00Z",
        "sources":[{
            "url":"https://official-project.org/press/release",
            "title":"Synthetic source title for automated tests",
            "supporting_excerpt":"This synthetic claim is explicitly only a validation fixture.",
            "checked_at":"2026-11-22T13:00:00Z",
            "publicly_accessible":True
        }],
        "attachments":[]
    }

class GuardTests(unittest.TestCase):
    def yes(self, r=None, ledger=None):
        return validate(r or make(), ledger, now=NOW)
    def bad(self, r):
        with self.assertRaises(EvidenceError):
            self.yes(r)
    def test_valid_preflight_not_submitted(self):
        r=self.yes()
        self.assertEqual(r["status"],"PREFLIGHT_ONLY_NOT_SUBMITTED")
    def test_stable_key_ignores_punctuation(self):
        a=make();b=copy.deepcopy(a);b["fact"]=a["fact"].replace("notice", "notice,")
        self.assertEqual(evidence_key(a),evidence_key(b))
    def test_different_fact_different_key(self):
        a=make();b=copy.deepcopy(a);b["fact"]+=" New independent fact."
        self.assertNotEqual(evidence_key(a),evidence_key(b))
    def test_no_human_review(self):
        a=make();a["human_reviewed"]=False;self.bad(a)
    def test_missing_market(self):
        a=make();a["market_id"]="";self.bad(a)
    def test_unknown_side(self):
        a=make();a["side"]="MAYBE";self.bad(a)
    def test_short_fact(self):
        a=make();a["fact"]="A claim";self.bad(a)
    def test_expired_cutoff(self):
        a=make();a["evidence_cutoff"]="2026-11-20T17:00:00Z";self.bad(a)
    def test_future_source_visit(self):
        a=make();a["sources"][0]["checked_at"]="2026-12-01T00:00:00Z";self.bad(a)
    def test_unverified_source(self):
        a=make();a["sources"][0]["publicly_accessible"]=False;self.bad(a)
    def test_no_placeholder_domain(self):
        a=make();a["sources"][0]["url"]="https://example.com/release";self.bad(a)
    def test_no_private_ip(self):
        a=make();a["sources"][0]["url"]="https://127.0.0.1/release";self.bad(a)
    def test_no_insecure_http(self):
        a=make();a["sources"][0]["url"]="http://official-project.org/release";self.bad(a)
    def test_no_duplicate_source(self):
        a=make();a["sources"].append(copy.deepcopy(a["sources"][0]));self.bad(a)
    def test_too_many_files(self):
        a=make();a["attachments"]=["one.pdf","two.pdf","three.pdf","four.pdf"];self.bad(a)
    def test_attachment_traversal(self):
        a=make();a["attachments"]=["../secret.txt"];self.bad(a)
    def test_duplicate_key_blocked(self):
        a=make();self.assertRaises(EvidenceError,self.yes,a,[{"market_id":a["market_id"],"side":"YES","idempotency_key":evidence_key(a)}])
    def test_three_market_entries_limit(self):
        a=make();ledger=[{"market_id":a["market_id"],"side":"YES","idempotency_key":f"key{i}"} for i in range(3)]
        self.assertRaises(EvidenceError,self.yes,a,ledger)
    def test_opposite_side_cancel_guard(self):
        a=make();self.assertRaises(EvidenceError,self.yes,a,[{"market_id":a["market_id"],"side":"NO","idempotency_key":"prior"}])
    def test_timezone_required(self):
        a=make();a["evidence_cutoff"]="2026-11-30T17:00:00";self.bad(a)

if __name__=="__main__":
    unittest.main(verbosity=2)
