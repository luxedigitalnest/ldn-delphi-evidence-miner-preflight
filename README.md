# LDN Evidence Miner — Gensyn / Delphi offline preflight

**Status: a genuine pre-submission validation module only. No live agent submissions, earned USDC, API credentials, wallet keys, or real market evidence are claimed.**

This module implements strict preflight checks based on the organiser's live [Agent Arena Competition: Evidence Mining](https://dorahacks.io/hackathon/delphi-agent-competition2/detail) rules before the Delphi API and market guide are released **25 November 2026 at 17:00 UTC**.

The official competition rewards credible, novel, dated public evidence. It allows **up to three API submissions per agent per market** and **three files per submission**. The API supports an **Idempotency-Key** to retry a timed-out request after checking `GET /v1/submissions`. Prize eligibility requires at least **10 judged submissions across 3+ markets**; sending arbitrary notes does not qualify.

## Functional safety gates

- Candidate market IDs must come from the official market list once it opens; the unit test ID is explicitly synthetic.
- Each candidate has a one-sided specific factual claim, checked public HTTPS source links, source titles, dated excerpts, an explicit evidence cutoff, a novelty explanation and human-reviewed confirmation.
- Rejects private/local/synthetic source domains, future timestamps, unverifiable citations, path traversal, too many file attachments and exact duplicate substantive fact keys.
- Blocks opposite-sided submissions to one market (because the competition says they cancel), plus fourth submissions.
- Computes a **stable idempotency key for the specific fact**. This helps preserve the same key if a future official API POST times out.
- **This tool never sends HTTP requests, creates wallets, trades, fetches protected content or submits competition entries**. Source review checkboxes are user assertions, not automated truth verification. The actual final research agent must independently retrieve and verify the real evidence.

## Run
```text
python -m unittest -v test_evidence_preflight.py
python evidence_preflight.py YOUR_REAL_EVIDENCE.json --ledger genuine_receipts.json --evidence-dir evidence
```
Do not submit a synthetic fixture. The organiser will publish the actual API key instructions, endpoint/payload and official starter agent on 25 November. Only then implement a documented API adapter with explicit consent, safe receipt checks, proper account verification and rate-limit handling.

## Honest blockers as of 22 Nov 2026

1. Delphi Google/Privy authentication is inconsistent: site still says SIGN IN, console warns `Attempted to log in, but user is already logged in`. No confirmed wallet address. DoraHacks registration must use the same genuine Delphi wallet, not an invented one.
2. No competition API keys/market list until 25 November.
3. No human-reviewed market facts, no API requests, no judged submissions and no cash payout verified.

Licensed Apache-2.0; intended for the existing LuxeDigitalNest Crypto project.
