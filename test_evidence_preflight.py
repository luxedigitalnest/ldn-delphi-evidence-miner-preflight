"""Offline-only tests. Synthetic fixtures are never competition submissions."""
import copy
import unittest
import tempfile
from pathlib import Path
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

    def test_review_flag_must_be_boolean_true(self):
        for value in ("false", "true", 1):
            with self.subTest(value=value):
                a=make(); a["human_reviewed"]=value; self.bad(a)
    def test_access_flag_must_be_boolean_true(self):
        a=make(); a["sources"][0]["publicly_accessible"]="false"; self.bad(a)
    def test_address_alias_shares_key_and_market_limit(self):
        a=make(); a["market_id"]="0x"+"aB"*20
        b=copy.deepcopy(a); b["market_id"]=a["market_id"].lower()
        self.assertEqual(evidence_key(a),evidence_key(b))
        ledger=[{"market_id":b["market_id"],"side":"YES","idempotency_key":f"other{i}"} for i in range(3)]
        self.assertRaises(EvidenceError,self.yes,a,ledger)
    def test_address_alias_blocks_opposite_side(self):
        a=make(); a["market_id"]="0x"+"Ab"*20
        self.assertRaises(EvidenceError,self.yes,a,[{"market_id":a["market_id"].lower(),"side":"no","idempotency_key":"prior"}])
    def test_invalid_ledger_rejected(self):
        for ledger in ({}, ["not an object"]):
            self.assertRaises(EvidenceError,self.yes,make(),ledger)
    def test_attachment_requires_verified_directory(self):
        a=make(); a["attachments"]=["file.txt"]; self.bad(a)
    def test_existing_attachment_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,"file.txt").write_text("synthetic",encoding="utf-8")
            a=make(); a["attachments"]=["file.txt"]
            result=validate(a,now=NOW,evidence_dir=tmp)
            self.assertEqual(result["attachment_count"],1)
    def test_attachment_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            target=Path(outside,"outside.txt"); target.write_text("synthetic",encoding="utf-8")
            try:
                Path(root,"link.txt").symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink not available on this host")
            a=make(); a["attachments"]=["link.txt"]
            with self.assertRaises(EvidenceError):
                validate(a,now=NOW,evidence_dir=root)
    def test_duplicate_attachment_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,"file.txt").write_text("synthetic",encoding="utf-8")
            a=make(); a["attachments"]=["file.txt","./file.txt"]
            with self.assertRaises(EvidenceError):
                validate(a,now=NOW,evidence_dir=tmp)
    def test_windows_attachment_path_rejected(self):
        a=make(); a["attachments"]=["C:/private/file.txt"]; self.bad(a)

    def test_nonstring_market_ids_rejected(self):
        for value in (None, True, 123):
            with self.subTest(value=value):
                a=make(); a["market_id"]=value; self.bad(a)
    def test_nonstring_candidate_evidence_rejected(self):
        for field in ("side", "fact", "why_novel"):
            with self.subTest(field=field):
                a=make(); a[field]=["a sufficiently long but non-text field"]*3; self.bad(a)
    def test_nonstring_source_evidence_rejected(self):
        for field in ("title", "supporting_excerpt"):
            with self.subTest(field=field):
                a=make(); a["sources"][0][field]={"fake":"not a source excerpt or title"}; self.bad(a)
    def test_malformed_url_fails_closed(self):
        for url in ("https://[broken", "https://official-project.org:99999/release", "https://official-project.org:bad/release"):
            with self.subTest(url=url):
                a=make(); a["sources"][0]["url"]=url; self.bad(a)
    def test_incomplete_receipt_row_fails_closed(self):
        for row in ({}, {"market_id":"other", "side":"YES"}, {"market_id":"other", "side":"invalid", "idempotency_key":"key"}):
            with self.subTest(row=row):
                self.assertRaises(EvidenceError,self.yes,make(),[row])

if __name__=="__main__":
    unittest.main(verbosity=2)
