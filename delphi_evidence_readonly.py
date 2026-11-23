"""Read-only Delphi Evidence API diagnostics for the 2026 evidence competition.

This tool intentionally implements NO submission, terms acceptance, trading,
wallet signing, or private-key functionality. It makes no request on import.
Mainnet API keys must be stored only in DELPHI_API_ACCESS_KEY outside source.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

API_BASE = "https://delphi.fyi/v1"
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


class NoRedirect(HTTPRedirectHandler):
    """Never forward a bearer key to a redirect destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass
class EvidenceApiError(Exception):
    http_status: int
    code: str
    request_id: Optional[str] = None
    retry_after: Optional[str] = None

    def __str__(self) -> str:
        # Deliberately do not echo response bodies, request headers or secrets.
        parts = [f"Evidence API HTTP {self.http_status}", f"code={self.code}"]
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        if self.retry_after:
            parts.append(f"retry_after={self.retry_after}")
        return " ".join(parts)


class EvidenceReadOnly:
    def __init__(self, api_key: str, transport: Optional[Callable] = None):
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("Missing DELPHI_API_ACCESS_KEY; no request was made")
        if any(c in api_key for c in "\r\n"):
            raise ValueError("Invalid API key header characters; no request was made")
        self._key = api_key.strip()
        # HTTP redirects fail closed; no remote host may receive this key.
        self._transport = transport or build_opener(NoRedirect()).open

    def _get(self, path: str, query: Optional[dict] = None) -> dict:
        if not path.startswith("/") or "?" in path or "#" in path or ".." in path:
            raise ValueError("Invalid API route; no request was made")
        url = API_BASE + path
        if query:
            url += "?" + urlencode(query)
        req = Request(
            url,
            headers={
                "Authorization": "Bearer " + self._key,
                "Accept": "application/json",
                "X-Agent-Id": "ldn-evidence-miner",
                "X-Agent-Harness": "python-stdlib-readonly",
                "X-Agent-Model": "gpt-6",
            },
            method="GET",
        )
        try:
            with self._transport(req, timeout=15) as response:
                content = response.read(2_000_001)
                if len(content) > 2_000_000:
                    raise EvidenceApiError(0, "oversized_response")
                payload = json.loads(content.decode("utf-8"))
                headers = response.headers
                return {
                    "data": payload,
                    "meta": {
                        "request_id": headers.get("X-Request-Id"),
                        "rate_limit_remaining": headers.get("RateLimit-Remaining"),
                        "retry_after": headers.get("Retry-After"),
                    },
                }
        except HTTPError as exc:
            # Only trust the structured error code, never print untrusted body.
            try:
                err = json.loads(exc.read(4096).decode("utf-8"))
                code = str((err.get("error") or {}).get("code", "http_error"))
                if not re.fullmatch(r"[a-zA-Z0-9_\-]{1,64}", code):
                    code = "http_error"
            except (ValueError, UnicodeError, AttributeError):
                code = "http_error"
            raise EvidenceApiError(
                exc.code,
                code,
                exc.headers.get("X-Request-Id") if exc.headers else None,
                exc.headers.get("Retry-After") if exc.headers else None,
            ) from None
        except URLError:
            raise EvidenceApiError(0, "network_error") from None

    def terms(self) -> dict:
        return self._get("/terms")

    def limits(self) -> dict:
        return self._get("/limits")

    def submissions(self, market: Optional[str] = None,
                    agent_id: Optional[str] = None, limit: int = 25) -> dict:
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        query = {"limit": limit}
        if market is not None:
            self._validate_market(market)
            query["market"] = market
        if agent_id is not None:
            if not re.fullmatch(r"[\x20-\x7E]{1,64}", agent_id):
                raise ValueError("agent_id must be 1-64 printable ASCII characters")
            query["agentId"] = agent_id
        return self._get("/submissions", query)

    def entry_state(self, market: str) -> dict:
        self._validate_market(market)
        return self._get(f"/markets/{market}/entry-state")

    @staticmethod
    def _validate_market(market: str) -> None:
        if not isinstance(market, str) or not ADDRESS_RE.fullmatch(market):
            raise ValueError("market must be an official 0x + 40 hex-character address")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("terms", "limits", "list", "entry-state"))
    parser.add_argument("--market", help="marketAddress copied from official list")
    parser.add_argument("--agent-id", help="filter existing submissions by agent ID")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args(argv)
    try:
        client = EvidenceReadOnly(os.environ.get("DELPHI_API_ACCESS_KEY", ""))
        if args.action == "terms":
            result = client.terms()
        elif args.action == "limits":
            result = client.limits()
        elif args.action == "list":
            result = client.submissions(args.market, args.agent_id, args.limit)
        else:
            if not args.market:
                parser.error("entry-state requires --market from official market list")
            result = client.entry_state(args.market)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, EvidenceApiError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
