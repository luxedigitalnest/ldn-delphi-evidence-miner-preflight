# Live-API integration checklist (not yet implemented)

**Date checked: 22 November 2026.** This repository is an offline evidence-validation preflight and is NOT an active Gensyn/Delphi mining bot.

When the organizer releases competition markets and API on November 25 at 17:00 UTC:

1. Open only the official Delphi competition site and read current live API documentation. Record actual API host, available market identifiers, question/side semantics, access scopes, exact payload schema, idempotency and rate limits. Never guess endpoints from the offline preflight fields.
2. Verify the **existing** authenticated Delphi wallet public address and that the same address is used on the existing DoraHacks event registration. Do not create a second wallet or expose seed phrases.
3. Retrieve any API key through official account authorization. Store it only in the owner's secure local environment/secret store, never this public repository, screenshots, chat logs or URL.
4. Collect dated primary-source evidence for a small number of real markets. The local human_reviewed field must be set after genuine verification: title, original source, quotes/paraphrase, cutoff and actual claim implications.
5. First make a **read-only** API request to enumerate real markets; inspect API response and client logs for status codes, schema and rate limiting. Only then add an authenticated API adapter with a deliberately gated first real POST.
6. Use the official Idempotency-Key header (if still supported) and check existing remote receipts before any retry. Ledger entries represent **actual** accepted submissions only, never synthetic local checks. At most three submissions per market and never contradictory sides in the same market.
7. Inspect published judge scores, evidence status, API request IDs and eligibility. Ten judged across three markets is a minimum, not an automatic prize. Do not claim rewards until the actual account records them.

The offline checker uses deliberately synthetic fixture markets and no network access. Run python -m unittest -v test_evidence_preflight.py without tokens, private data, wallets or internet.

**Stop conditions:** authentication mismatch; app requires identity checks; wallets or contracts request real funds; API says pause/rate-limit; uncertain source interpretation; missing owner consent for a trade or signing; contradictory market direction.
