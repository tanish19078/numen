---
name: system-integration-clarity
description: >-
  Enforces 100% architectural and integration honesty across docs, UI, and pitch decks:
  plain-English product definition, real end-to-end protocol contracts, and explicit Live Today
  vs. Production Adapter boundaries.
---

# System & Integration Clarity Standard

Use this skill whenever documenting, presenting, or exposing agent-payment architecture.

## Four Required Artifacts & Guarantees

1. **Plain-English One-Sentence Definition**
   - Avoid stacked buzzwords. Lead with what the product does physically:
     *"Numen is a programmable corporate bank layer that verifies why an AI agent wants to buy something—before minting a single-use, exact-rupee 60-second virtual card."*

2. **Exact End-to-End Integration Sequence**
   Must trace all 6 physical hops without gaps:
   1. **Human / CFO** funds treasury & signs a cryptographic `IntentMandate` (`Ed25519`).
   2. **External AI Agent** discovers capabilities (`GET /.well-known/agent.json`) and requests spend via `POST /mcp` (`request_scoped_card`).
   3. **Router & Mandate Gate** verifies `Ed25519`, checks daily balance + 3x/60s retry-loop lock, and routes to Gemini 2.5 Flash or Pro.
   4. **Causal Firewall** isolates control intent vs untrusted DOM (`CaMeL`), scores counterfactual `World A vs B` drift (`AttriGuard`), and checks fine-print traps / lookalike domains (`FinePrintAuditor`).
   5. **Issuer Mint / Passkey** mints an HMAC-locked 60s Luhn virtual PAN + `PaymentMandate` (or triggers 1-Tap Passkey HITL hold).
   6. **Merchant Settlement** validates exact rupee (`±₹0.00`), merchant, and MCC, settles in SQLite WAL, and permanently shreds the PAN.

3. **Strict Honesty Split (Live Now vs. Production Adapters)**
   Every architecture doc, integration screen, and investor slide must explicitly separate:
   - **Running Live in Repo Today**: FastAPI + React SPA, SQLite WAL ledger, local Ed25519 cryptography, MCP JSON-RPC 2.0 (`POST /mcp`), A2A Agent Card (`GET /.well-known/agent.json`), deterministic AttriGuard/CaMeL/FinePrint + optional live `GEMINI_API_KEY`, sandboxed Luhn PAN + HMAC mint engine.
   - **Pluggable Production Adapters**: Stripe Issuing / Marqeta / RazorpayX real PAN rails, Google Cloud KMS / HSM signing, Vertex AI Gemini Enterprise, Cloud Run + Firestore/Postgres.

4. **Copy-Pasteable Developer Contract**
   Every integration view must expose working `POST /mcp` JSON-RPC examples and Claude Desktop / Cursor MCP config snippets matching actual backend routes.
