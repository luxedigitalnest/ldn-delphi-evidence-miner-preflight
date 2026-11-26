# LDN Evidence Miner — Gensyn / Delphi offline preflight

**Status: a genuine pre-submission validation module only. No live agent submissions, earned USDC, API credentials, wallet keys, or real market evidence are claimed.**

This module implements strict offline preflight checks for the organiser's [Agent Arena Competition: Evidence Mining](https://dorahacks.io/hackathon/delphi-agent-competition2/detail). **The official Evidence API/SDK documentation is now published** (verified 23 Nov); the scheduled competition window runs from **25 November 2026 at 17:00 UTC to 11 December 2026 at 17:00 UTC**. The event uses **Delphi Mainnet**, but **evidence-only submissions require only a Mainnet API key—no private key, wallet transaction, ETH or USDC**. See [the official integration checkpoint](OFFICIAL_GENSYN_EVIDENCE_API_2026-11-23.md).

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
Do not submit a synthetic fixture. The organiser has published official competition-specific API instructions and an SDK, linked in [the integration checkpoint](OFFICIAL_GENSYN_EVIDENCE_API_2026-11-23.md). Once owner Mainnet identity, Mainnet API key and terms are genuinely verified, a documented evidence-only adapter can be built and tested read-only. Submit only after markets open on 25 Nov, the user's explicit terms acceptance, source review, and account limit checks. The key must stay in a private local secret store and must never be committed.

## Honest blockers (originally checked 22 Nov; documentation updated 23 Nov)

1. Delphi Google/Privy authentication is inconsistent: site still says SIGN IN, console warns `Attempted to log in, but user is already logged in`. No confirmed wallet address. DoraHacks registration must use the same genuine Delphi wallet, not an invented one.
2. The **official API instructions now exist**, but this account has **no verified Mainnet Delphi API key**. The competition market list was scheduled to open on 25 November. A Mainnet Delphi account and matching DoraHacks wallet still need verification. No wallet signer or private key is necessary to submit evidence.
3. No human-reviewed real competition market facts, no authenticated Evidence API requests, no judged submissions and no cash payout verified. Do not accept account Terms without the owner's explicit informed consent.

Licensed Apache-2.0; intended for the existing LuxeDigitalNest Crypto project.


## Read-only official Evidence API diagnostics (23 Nov)

An additional **safe read-only Mainnet Evidence API adapter** is now in this repo: [delphi_evidence_readonly.py](delphi_evidence_readonly.py), with [mocked tests](test_delphi_evidence_readonly.py) and a [secret-free CI workflow](.github/workflows/offline-preflight.yml). The adapter supports **GET-only** account terms, limits, previous submissions, an individual submission receipt and market entry-state. It contains no `POST`, terms acceptance, wallet-signing, trading or evidence submission methods. It only sends the bearer key to the fixed official `https://delphi.fyi/v1` endpoint, disallows redirects and never logs the key.

Run offline tests without any credentials:

```bash
python -m unittest discover -v -p 'test_*.py'
```

Once the account owner has independently established the correct **Delphi Mainnet** identity and stored the **Mainnet** `DELPHI_API_ACCESS_KEY` in their secure shell environment outside the repository, run the following commands in that environment:

```bash
python delphi_evidence_readonly.py terms
python delphi_evidence_readonly.py limits
python delphi_evidence_readonly.py list
# Only using an actual submission ID returned by the official API:
python delphi_evidence_readonly.py receipt --submission-id YOUR_REAL_SUBMISSION_ID
# Only when using a genuine market address copied from the official open market list:
python delphi_evidence_readonly.py entry-state --market 0xYOUR_REAL_MARKET_ADDRESS
```

Never paste the API key in chat, repository files, support tickets, evidence notes or command-line argument strings. **Reading the terms does not accept them.** Only the owner can expressly approve current terms. The receipt command is GET-only and follows the [official evidence API guide](https://github.com/gensyn-ai/gensyn-delphi-skills/blob/main/reference/evidence-api.md). It rejects unsafe path identifiers before making a request. No real authenticated Evidence API query, real market submission, reward or cash payment is claimed. New receipt tests require verification by CI.
