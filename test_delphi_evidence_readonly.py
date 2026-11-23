"""Offline mocked tests: must never make any network request."""
import io
import json
import unittest
from email.message import Message
from urllib.error import HTTPError
from delphi_evidence_readonly import EvidenceReadOnly, EvidenceApiError, NoRedirect, API_BASE

ADDRESS = "0x" + "a" * 40


class FakeResponse:
    def __init__(self, data=None, headers=None):
        self.buf = io.BytesIO(json.dumps(data or {}).encode())
        self.headers = Message()
        for k, v in (headers or {}).items():
            self.headers[k] = v

    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n=-1): return self.buf.read(n)


class Tests(unittest.TestCase):
    def make(self, response=None):
        calls=[]
        def transport(req, timeout):
            calls.append((req, timeout))
            return response or FakeResponse({"ok": True}, {"X-Request-Id": "req-test", "RateLimit-Remaining": "4"})
        return EvidenceReadOnly("TEST-SECRET-NEVER-LOGGED", transport), calls

    def test_no_key_fails_without_request(self):
        with self.assertRaisesRegex(ValueError, "Missing DELPHI"):
            EvidenceReadOnly("")

    def test_header_injection_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid API key"):
            EvidenceReadOnly("dummy\r\nX-Bad: yes")

    def test_get_terms_only(self):
        client,calls=self.make(); out=client.terms()
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][0].get_method(),"GET")
        self.assertEqual(calls[0][0].full_url,API_BASE+"/terms")
        self.assertEqual(calls[0][0].get_header("Authorization"),"Bearer TEST-SECRET-NEVER-LOGGED")
        self.assertEqual(out["meta"]["request_id"],"req-test")
        self.assertEqual(out["meta"]["rate_limit_remaining"],"4")

    def test_get_limits(self):
        c,calls=self.make(); c.limits();self.assertEqual(calls[0][0].full_url,API_BASE+"/limits")

    def test_list_submissions_with_valid_filters(self):
        c,calls=self.make(); c.submissions(market=ADDRESS,agent_id="ldn-evidence-miner",limit=3)
        url=calls[0][0].full_url
        self.assertIn("/submissions?",url)
        self.assertIn("market=0x",url)
        self.assertIn("agentId=ldn-evidence-miner",url)
        self.assertIn("limit=3",url)

    def test_entry_state_with_valid_address(self):
        c,calls=self.make(); c.entry_state(ADDRESS)
        self.assertEqual(calls[0][0].full_url,API_BASE+"/markets/"+ADDRESS+"/entry-state")

    def test_invalid_addresses_never_contact_network(self):
        c,calls=self.make()
        for bad in ("", "../../terms", "0x123", "0x"+"z"*40, "https://evil.test"):
            with self.assertRaises(ValueError):c.entry_state(bad)
        self.assertEqual(calls,[])

    def test_invalid_limit_never_contact_network(self):
        c,calls=self.make()
        with self.assertRaises(ValueError):c.submissions(limit=0)
        self.assertEqual(calls,[])

    def test_invalid_agent_header_filter_never_contact_network(self):
        c,calls=self.make()
        with self.assertRaises(ValueError):c.submissions(agent_id="bad\nvalue")
        self.assertEqual(calls,[])

    def test_unauthorized_error_redacts_server_text_and_key(self):
        body=io.BytesIO(json.dumps({"error":{"code":"unauthorized", "message":"Bearer TEST-SECRET-NEVER-LOGGED"}}).encode())
        hdr=Message();hdr["X-Request-Id"]="req-401"
        def transport(req,timeout):raise HTTPError(req.full_url,401,"Bearer TEST-SECRET-NEVER-LOGGED",hdr,body)
        c=EvidenceReadOnly("TEST-SECRET-NEVER-LOGGED",transport)
        with self.assertRaises(EvidenceApiError) as err:c.limits()
        s=str(err.exception)
        self.assertIn("unauthorized",s);self.assertIn("req-401",s)
        self.assertNotIn("TEST-SECRET",s)

    def test_rate_limit_preserves_retry_header_without_retry(self):
        body=io.BytesIO(json.dumps({"error":{"code":"rate_limited"}}).encode())
        hdr=Message();hdr["Retry-After"]="120"
        count=[]
        def transport(req,timeout):count.append(1);raise HTTPError(req.full_url,429,"rate limited",hdr,body)
        c=EvidenceReadOnly("dummy",transport)
        with self.assertRaises(EvidenceApiError) as err:c.limits()
        self.assertEqual(len(count),1)
        self.assertEqual(err.exception.retry_after,"120")

    def test_redirect_fail_closed(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,"moved",{},"https://other-domain.test"))

    def test_no_post_or_terms_acceptance_method(self):
        c,_=self.make()
        self.assertFalse(hasattr(c,"submit"))
        self.assertFalse(hasattr(c,"accept_terms"))
        self.assertFalse(hasattr(c,"trade"))


if __name__ == "__main__": unittest.main(verbosity=2)
