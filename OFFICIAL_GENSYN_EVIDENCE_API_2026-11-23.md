# Official Gensyn / Delphi Evidence API integration checkpoint — 23 Nov 2026

Status: **PUBLIC DOCUMENTATION REVIEWED; ACCOUNT AND API NOT YET VERIFIED; NO SUBMISSIONS MADE.**
This is an integration plan and evidence-safety checklist, not an operational live submission.
Official docs may change. Recheck before the first real attempt.

## Important correction to the earlier preflight README

The organizer has now published the official competition guide and SDK details *before* the Nov 25 start.
The 2026 **Evidence Mining** competition runs on **Delphi Mainnet** (not Delphi testnet or the previous trading competition).
For **evidence-only submissions** the official organizer says a **Mainnet API key is sufficient**: **no private key, no wallet signer, no ETH, and no USDC** are required. Trading examples and faucet scripts in the general SDK are **not** required for Evidence Mining; do not use them.

Primary references:
- https://github.com/gensyn-ai/gensyn-delphi-skills/blob/main/reference/competition.md (v1.0, Nov19)
- https://github.com/gensyn-ai/gensyn-delphi-skills/blob/main/reference/evidence-api.md
- https://github.com/gensyn-ai/gensyn-delphi-sdk (EvidenceClient >=2.4.0)
- https://dorahacks.io/hackathon/delphi-agent-competition2/detail
- https://competition.delphi.fyi/markets
- https://competition.delphi.fyi/markets.json

## Organizer calendar

- Registration opened **2026-11-16 17:00 UTC**.
- Evidence competition opens **2026-11-25 17:00 UTC**.
- Entries close **2026-12-11 17:00 UTC**.
- Winners planned **2026-12-16**, subject to settlement and integrity review.
- Prize eligibility: **at least 10 judged submissions across 3+ actual competition markets**. This minimum does not guarantee any payout.
- Standard account tier: up to **3 submissions per market**; server limits and evidence cutoffs govern actual availability.

## Outstanding owner prerequisites (group together)

1. The owner must have a genuine **Mainnet Delphi** account at https://app.delphi.fyi/ and confirm the public wallet address actually associated with that Delphi account. Do **not** create duplicate accounts or infer this from an EVM address shown elsewhere.
2. Confirm DoraHacks registration uses the **same public wallet**. Existing DoraHacks competition registration alone does not prove that Delphi account linkage is correct.
3. Owner generates a **Mainnet** API key at https://api-access.delphi.fyi/ for that wallet and stores it locally in a private `.env` as `DELPHI_API_ACCESS_KEY`. Neither key nor `.env` contents should be pasted into chat, read into model context, committed to GitHub, logged, or sent elsewhere. A testnet key is rejected for this competition.
4. Owner personally reviews the current Evidence API terms at the URL returned by `GET /v1/terms`. **Do not accept those terms on the owner's behalf without explicit informed approval.**

Note: The existing 20 offline Python preflight tests and original evidence fixtures remain helpful but do **not** confirm any account, eligibility, market access, or paid submission.

## Safe technical preparation (before the opening)

- Check published SDK major/minor version and evidence-specific docs. Keep the original offline tests; never run trading or private-key scripts as a substitute for the Evidence API.
- Official evidence API base URL: `https://delphi.fyi/v1`. The OpenAPI document at `https://delphi.fyi/v1/openapi.json` is authoritative over narrative docs.
- The SDK's `EvidenceClient` handles `GET /v1/terms`, `GET /v1/limits`, `GET /v1/submissions`, `GET /v1/markets/{market}/entry-state`, `POST /v1/submissions`, and result lookup; actual calls need the owner's Mainnet key.
- When a verified key becomes available, perform **read-only** `terms`, `limits`, and `list` diagnostics first. A `401` points to a key issue, `403 wallet_mismatch` to an identity mismatch. Never bypass either.
- Before submitting, read the organizer's real market list and match `marketAddress` to the specific claim and evidence cutoff. Run the existing offline `evidence_preflight.py`, and independently verify each referenced primary source for relevance and novelty.
- Check the account's existing `GET /v1/submissions?market=<address>` and shared local ledger to avoid repeats; the organizer says duplicate/rejected entries consume per-market slots.
- Only after terms are explicitly accepted by the owner, send one *real* research evidence package to its verified market. Use the SDK's idempotency key, check receipt and verdict, preserve request ID and link to primary evidence.
- Treat `accepted`, `judged`, `paid`, and `prize eligible` as distinct statuses. A judged submission can earn zero. Never claim a cash result until the payment is actually verified.

## Current blockers as of Nov 23

- Delphi site Privy Sign In was previously non-responsive in authenticated Opera/Chrome despite 200 session responses; public Delphi wallet-account identity has **not** been confirmed.
- Mainnet Evidence API key and owner acceptance of Terms have **not** been verified.
- Competition markets open on **Nov 25**; there are no verified real market-specific submissions.
- No on-chain trading, wallet signing, USDC income, or prizes from this preparatory work.

## No-secret handling

The official organizer instructions say **evidence-only work does not require a wallet private key**. Do not generate, copy, import or request one for this workflow. If a third-party guide asks for `WALLET_PRIVATE_KEY` or deposits for Evidence Mining, compare it against the organizer's competition-specific reference above before doing anything.
