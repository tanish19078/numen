# Numen 3-Cluster Agentic Architecture & Integration Spec

> Clear architectural map explaining what runs live today in `backend/app/`, how the three agent clusters interact over A2A & MCP, and how external issuing rails plug in cleanly.

---

## 1. The Three Clusters

### Cluster 1 — Edge Commerce Cluster (Untrusted Surface)
- **Role:** Autonomous coding, cloud ops, procurement, and research agents (or external MCP clients such as Claude Desktop, Cursor, Google ADK, LangGraph) browsing vendor pages and constructing checkout intents.
- **Constraint:** Holds **zero raw PANs** and cannot debit the operating treasury vault. Discovers Numen at `GET /.well-known/agent.json` and requests spend credentials via `POST /mcp` (`tools/call -> request_scoped_card`).

### Cluster 2 — Verification & Consensus Quorum Cluster (`backend/app/agents/`)
- **Smart Router (`gemini_router.py`):** Sends whitelisted infrastructure requests with clean DOM to `gemini-2.5-flash` (0x counterfactual overhead) and escalates untrusted HTML, dense checkout clauses (`>120 chars`), or unfamiliar domains to `gemini-2.5-pro`.
- **4 Specialist Verifier Agents (Consensus Quorum via typed `A2AMessage` envelopes):**
  1. **`BudgetController`** ([`budget_controller.py`](../backend/app/agents/budget_controller.py)): Verifies daily sub-account allowance, MCC allowlist, and the `3x / 60s` identical-request retry-loop circuit breaker.
  2. **`CaMeL.CapabilityGuard`** ([`camel_capabilities.py`](../backend/app/agents/camel_capabilities.py)): Enforces Google DeepMind CaMeL (`arXiv:2503.18813`) provenance isolation between privileged human mandates and quarantined DOM inputs.
  3. **`AttriGuard.Firewall`** ([`attriguard.py`](../backend/app/agents/attriguard.py)): Dual Tool Sanitizer (`arXiv:2510.05244`) strips hidden CSS (`opacity:0`, `display:none`, zero-width glyphs) and runs counterfactual `World A vs World B` attribution (`arXiv:2603.10749`). Drift `>= 0.25` triggers a hard veto and pauses the agent.
  4. **`FinePrint.Auditor`** ([`fineprint_auditor.py`](../backend/app/agents/fineprint_auditor.py)): Extracts hidden annual lock-in liabilities (e.g., `₹99 trial -> ₹36,000/yr`) and 1-character homoglyph domain spoofs (`runp0d.io`).

### Cluster 3 — Zero-LLM Deterministic Custody Cluster (`backend/app/`)
- **Strict Air-Gap:** No probabilistic LLM call inside Cluster 3.
- **AP2 Signer (`crypto_ap2.py`):** Signs and verifies `IntentMandate -> CartMandate -> PaymentMandate` chains using canonical `SHA-256` digests and `Ed25519` keys.
- **Card Minter & Shredder (`sandbox_mint.py`):** Mints Luhn-valid Visa PANs locked via `HMAC-SHA256` to exact `±₹0.00` tolerance, exact merchant name, exact MCC, and 60-second TTL; permanently shreds after 1 settlement.
- **ACID Ledger & HITL (`db.py`, `main.py`):** Commits state to `SQLite WAL`, broadcasts real-time events over `GET /api/stream`, and holds grey-zone recurring traps for 1-Tap Passkey resolution (`POST /api/passkeys/{id}/resolve`).

---

## 2. Live API, MCP & A2A Contract

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/.well-known/agent.json` | `GET` | A2A Discovery Card listing all 3 clusters, protocols (`A2A/0.2`, `MCP/2025-03-26`, `AP2/Ed25519`), and endpoints |
| `/mcp` | `POST` | MCP JSON-RPC 2.0 server (`initialize`, `tools/list`, `tools/call`: `request_scoped_card`, `get_agent_allowance`, `settle_ephemeral_card`) |
| `/api/spend/evaluate` | `POST` | Runs the 3-cluster quorum verification pipeline & mints 60s card (or returns `BLOCKED` / `PASSKEY_REQUIRED`) |
| `/api/cards/{id}/charge` | `POST` | Simulates merchant charge; enforces exact `±₹0.00` lock & single-use shredding |
| `/api/passkeys/{id}/resolve` | `POST` | Resolves pending Founder Passkey escalation (`approve` or `deny`) |
| `/api/mandates/{id}/verify-tamper` | `POST` | Live cryptographic proof rejecting a `+₹1` tampered mandate |
| `/api/benchmarks/run` | `POST` | Executes all 240 live red-team + clean checkout test cases |
| `/api/stream` | `GET` | Server-Sent Events (SSE) telemetry stream |

### Connect Claude Desktop / Cursor in 30 Seconds
```json
{
  "mcpServers": {
    "numen-treasury": {
      "url": "http://127.0.0.1:8000/mcp",
      "transport": "http"
    }
  }
}
```

---

## 3. Honest Component Boundary: Live Now vs. Production Adapters

| Layer | Running Live in This Repo Today | Drop-In Production Adapter |
| :--- | :--- | :--- |
| **Agent Discovery & MCP** | Live `/.well-known/agent.json` + `POST /mcp` JSON-RPC 2.0 | Cloud Run + OAuth / Cloud Armor |
| **AP2 Cryptography** | Local `Ed25519` + `SHA-256` chains (`crypto_ap2.py`) | Google Cloud KMS / HSM + WebAuthn |
| **LLM Router** | `Gemini 2.5 Flash/Pro` router + deterministic offline mode | Vertex AI Gemini Enterprise |
| **Card Issuing Rail** | Sandboxed Luhn PAN mint + `±₹0.00` HMAC lock (`sandbox_mint.py`) | Stripe Issuing / Marqeta / RazorpayX JIT |
| **Treasury Ledger** | `SQLite WAL` ACID tables + live SSE (`/api/stream`) | Cloud SQL PostgreSQL / Firestore + Pub/Sub |
