"""LDN Delphi Evidence Mining: evidence-quality and idempotency preflight only.
No trading, API submissions, wallet signing, scraping, key handling or live claims.
Official API adapter and real market research must wait for 25 Nov 2026.
"""
import argparse
import hashlib
import ipaddress
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from urllib.parse import urlsplit

MIN_FACT_LENGTH = 45
MAX_FILES = 3
MAX_PER_MARKET = 3
ALLOWED_ATTACHMENTS = {".pdf", ".txt", ".csv", ".png", ".jpg", ".jpeg"}

class EvidenceError(ValueError):
    pass

def utc_time(text):
    try:
        result = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("timezone required")
        return result.astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise EvidenceError("Supply a valid timestamp including a UTC offset") from exc

def public_url(text):
    if not isinstance(text, str) or not text.strip():
        raise EvidenceError("Source URL must be a nonempty string")
    try:
        parsed = urlsplit(text)
        host = (parsed.hostname or "").lower().rstrip(".")
        parsed.port  # Reject malformed or out-of-range ports.
    except ValueError as exc:
        raise EvidenceError("Malformed source URL") from exc
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        raise EvidenceError("Source must be a public HTTPS URL without credentials")
    if host in {"localhost", "example.com", "example.org", "example.net"} or host.endswith((".localhost", ".local", ".internal", ".test", ".invalid")):
        raise EvidenceError("Local, synthetic or placeholder sources are not admissible")
    if re.search(r"[^a-z0-9.\-]", host) or "." not in host:
        raise EvidenceError("Invalid source hostname")
    try:
        addr = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        pass
    else:
        if not addr.is_global:
            raise EvidenceError("Private/reserved source address is not admissible")
    return parsed.geturl().split("#", 1)[0]

def canonical_fact(statement):
    return " ".join(re.sub(r"[^\w\s]", " ", statement.lower(), flags=re.UNICODE).split())

def canonical_market(market):
    if not isinstance(market, str):
        raise EvidenceError("Market id must be a string")
    market = market.strip()
    if re.fullmatch(r"0x[0-9a-fA-F]{40}", market):
        return market.lower()
    return market

def evidence_key(record):
    content = [canonical_market(record["market_id"]), canonical_fact(record["fact"])]
    return hashlib.sha256("\n".join(content).encode("utf-8")).hexdigest()

def validate(record, ledger=None, *, now=None, evidence_dir=None):
    """Validate a candidate WITHOUT asserting it is true or sending it anywhere."""
    if ledger is None:
        ledger = []
    if not isinstance(ledger, list) or any(not isinstance(row, dict) for row in ledger):
        raise EvidenceError("Receipt ledger must be a list of structured objects")
    now = now or datetime.now(timezone.utc)
    if not isinstance(record, dict):
        raise EvidenceError("Candidate must be a JSON object")
    market = canonical_market(record.get("market_id", ""))
    if any(not isinstance(record.get(field), str) for field in ("side", "fact", "why_novel")):
        raise EvidenceError("Side, fact and novelty rationale must be strings")
    side = record["side"].upper()
    fact = record["fact"].strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", market):
        raise EvidenceError("Market id must come from the official competition market list")
    if side not in ("YES", "NO"):
        raise EvidenceError("Side must be YES or NO")
    if len(fact) < MIN_FACT_LENGTH or len(fact) > 1500:
        raise EvidenceError("Give one specific, adequately detailed factual claim")
    if record.get("human_reviewed") is not True:
        raise EvidenceError("A human must confirm source faithfulness before submission")
    rationale = str(record.get("why_novel", "")).strip()
    if len(rationale) < 30:
        raise EvidenceError("Explain why this dated evidence is not common knowledge")
    cutoff = utc_time(record.get("evidence_cutoff"))
    if now >= cutoff:
        raise EvidenceError("The market's evidence cutoff has passed")
    sources = record.get("sources")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 8:
        raise EvidenceError("Need 1 to 8 original, checkable public sources")
    urls = set()
    for source in sources:
        if not isinstance(source, dict):
            raise EvidenceError("Source must be a structured reference")
        url = public_url(source.get("url", ""))
        if url in urls:
            raise EvidenceError("Same source URL cited twice")
        urls.add(url)
        if not isinstance(source.get("title"), str) or len(source["title"].strip()) < 8:
            raise EvidenceError("Include actual source title")
        if not isinstance(source.get("supporting_excerpt"), str) or len(source["supporting_excerpt"].strip()) < 20:
            raise EvidenceError("Quote or accurately paraphrase the supporting evidence")
        checked = utc_time(source.get("checked_at"))
        if checked > now:
            raise EvidenceError("Cannot claim to have checked a source in the future")
        if source.get("publicly_accessible") is not True:
            raise EvidenceError("Source accessibility must be independently verified")
    attachments = record.get("attachments", [])
    if not isinstance(attachments, list) or len(attachments) > MAX_FILES:
        raise EvidenceError("Maximum 3 files per submission")
    seen_files = set()
    for item in attachments:
        if not isinstance(item, str):
            raise EvidenceError("Attachment must be a relative supported file")
        path = Path(item)
        win = PureWindowsPath(item)
        if path.is_absolute() or win.drive or win.root or ".." in path.parts or ".." in win.parts or "\\" in item or path.suffix.lower() not in ALLOWED_ATTACHMENTS:
            raise EvidenceError("Attachment must be a relative supported file")
        if not evidence_dir:
            raise EvidenceError("Provide --evidence-dir to verify attachment existence")
        root = Path(evidence_dir).resolve()
        try:
            resolved = (root / path).resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError, RuntimeError) as exc:
            raise EvidenceError("Attachment missing or outside the evidence directory") from exc
        if not resolved.is_file() or resolved in seen_files:
            raise EvidenceError("Attachment must be a distinct verified existing file")
        seen_files.add(resolved)
    for row in ledger:
        if not isinstance(row.get("market_id"), str) or not row["market_id"].strip() or not isinstance(row.get("side"), str) or row["side"].upper() not in ("YES", "NO") or not isinstance(row.get("idempotency_key"), str) or not row["idempotency_key"].strip():
            raise EvidenceError("Receipt ledger entries require market id, side and idempotency key")
    previous = [row for row in ledger if canonical_market(row["market_id"]) == market]
    if any(str(row.get("side", "")).upper() != side for row in previous):
        raise EvidenceError("Conflicting market direction; avoid evidence cancellation")
    key = evidence_key(record)
    if any(row.get("idempotency_key") == key for row in ledger):
        raise EvidenceError("Already recorded: preserve original idempotency key; check receipt")
    if len(previous) >= MAX_PER_MARKET:
        raise EvidenceError("Official 3 submissions per market limit reached")
    return {"market_id": market, "side": side, "idempotency_key": key, "source_count": len(sources), "attachment_count": len(attachments), "status": "PREFLIGHT_ONLY_NOT_SUBMITTED"}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", help="Locally authored real-evidence JSON")
    parser.add_argument("--ledger", help="JSON list of actually submitted/judged receipts")
    parser.add_argument("--evidence-dir", help="Root for verifying attachment paths")
    args = parser.parse_args()
    obj = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8")) if args.ledger else []
    try:
        result = validate(obj, ledger, evidence_dir=args.evidence_dir)
    except EvidenceError as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}))
        sys.exit(2)
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
