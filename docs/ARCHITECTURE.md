# Numen Architecture Specification

## 1. Architectural Thesis: Deterministic Safety Around Probabilistic Reasoning

Financial systems cannot execute ledger mutations or issue card PANs directly from raw LLM token output. Numen separates **semantic inspection** from **cryptographic execution** across four strict boundaries inside **Google Gemini Enterprise**:

1. **Boundary 1 — MCP Payment Interface (`mcp_server.py`):** External autonomous agents never hold raw card credentials. They invoke `request_scoped_card` over Model Context Protocol (`POST /mcp`), passing their structured cart, reasoning trace, and any untrusted external observations (webpage DOM, invoice PDF text, checkout terms).
2. **Boundary 2 — Gemini Smart Model Router (`gemini_router.py`):** Routes low-risk, whitelisted infrastructure calls with empty untrusted DOM to **`gemini-2.5-flash`** (~185 ms target latency), while escalating requests carrying untrusted HTML, long T&Cs, or unfamiliar merchants to **`gemini-2.5-pro`** for deep causal and multimodal inspection.
3. **Boundary 3 — ADK + A2A Specialist Committee (`agents/`):** Three specialized agents exchange typed `A2AMessage` envelopes streamed in real time over Server-Sent Events (`/api/stream`):
   - `BudgetControllerAgent`: Allowance, MCC allowlist, and duplicate retry-loop circuit breaker.
   - `AttriGuardAgent`: Dual DOM Sanitizer + Counterfactual Causal Drift verifier.
   - `FinePrintAuditorAgent`: Hidden recurring lock-in clause parser + lookalike domain detector.
4. **Boundary 4 — Python Agent Sandbox & ACID Ledger (`sandbox_mint.py`, `crypto_ap2.py`, `db.py`):** All Ed25519 signature verification, Luhn PAN generation, HMAC-SHA256 scope binding, 60-second TTL checks, exact-rupee settlement validation, and atomic SQLite `WAL` mutations execute deterministically in Python—never via LLM arithmetic.

---

## 2. End-to-End System Topology

```mermaid
flowchart LR
    Agent["Autonomous AI Agent (DevOps / Procurement / Travel)"] -->|"MCP tools/call: request_scoped_card"| MCP["Numen MCP Server (/mcp)"]
    MCP --> Router["Gemini Enterprise Smart Router"]
    Router -->|"Fast-Path (<200ms)"| Flash["Gemini 2.5 Flash"]
    Router -->|"Deep Inspection"| Pro["Gemini 2.5 Pro"]
    Flash --> Orch["ADK Orchestrator (A2A Mesh)"]
    Pro --> Orch
    Orch -->|"Hop 1: Ed25519 Verify"| AP2["AP2 Mandate Verifier"]
    Orch -->|"Hop 2: Allowance & Loop Check"| Budget["Budget Controller Agent"]
    Orch -->|"Hop 3: World A vs World B"| Attri["AttriGuard Firewall Agent"]
    Orch -->|"Hop 4: T&Cs & Lookalike Check"| Fine["Fine-Print Auditor Agent"]
    Fine -->|"Trap Detected"| Passkey["1-Tap Founder Passkey Gate"]
    Attri -->|"Drift >= 0.25"| Block["Block Mint & Pause Agent"]
    Orch -->|"All Gates PASS"| Sandbox["Python Agent Sandbox (Luhn + HMAC + 60s TTL)"]
    Sandbox --> Ledger["ACID Ledger (SQLite WAL / Cloud Firestore)"]
    Orch -.->|"Live A2A Telemetry"| SSE["SSE Stream (/api/stream) -> Glass-Box UI"]
```

---

## 3. Request Evaluation Sequence

```mermaid
sequenceDiagram
    participant A as "External AI Agent"
    participant O as "ADK Orchestrator"
    participant B as "Budget Controller"
    participant G as "AttriGuard (arXiv:2603.10749)"
    participant F as "FinePrint Auditor"
    participant S as "Python Sandbox Mint"

    A->>O: "request_scoped_card(cart, reasoning, untrusted_dom, terms)"
    O->>O: "Verify Human Ed25519 IntentMandate signature"
    O->>B: "A2A: check_allowance_and_velocity()"
    B-->>O: "PASS (Remaining INR 25,000 | Loop count = 1)"
    O->>G: "A2A: counterfactual_causal_check(mandate, dom, reasoning)"
    alt "Drift >= 0.25 (Prompt Injection Hijack)"
        G-->>O: "BLOCK (Drift=0.94, poisoned CSS span extracted)"
        O-->>A: "403 MINT_BLOCKED + Pause Compromised Agent"
    else "Drift < 0.25 (Aligned with Human Mandate)"
        G-->>O: "PASS (Drift=0.02)"
        O->>F: "A2A: inspect_terms_and_domain()"
        alt "Hidden Annual Auto-Debit Found"
            F-->>O: "PASSKEY_REQUIRED (Hidden INR 36,000/yr Clause 14.3)"
            O-->>A: "202 AWAITING_FOUNDER_PASSKEY"
        else "Clean Terms & Verified Domain"
            F-->>O: "PASS"
            O->>S: "Sign CartMandate + Mint 60s Luhn Card + Sign PaymentMandate"
            S-->>O: "VirtualCard(*9104, exact_lock=INR 3400, ttl=60s)"
            O-->>A: "200 MINTED (PAN + CVV + AP2 PaymentMandate)"
        end
    end
```

---

## 4. Google Cloud & Gemini Enterprise Service Mapping

| Layer | Local Prototype Implementation | Production Google Cloud / Gemini Enterprise Target |
| :--- | :--- | :--- |
| **Agent Orchestration** | `agents/orchestrator.py` + `agents/a2a.py` | **Gemini Enterprise ADK** + **Agent2Agent (A2A) Protocol** |
| **Model Routing** | `gemini_router.py` (`google-genai`) | **Gemini Enterprise Gateway** (`gemini-2.5-flash` / `gemini-2.5-pro`) + Spend Caps |
| **Deterministic Execution** | `sandbox_mint.py` + `crypto_ap2.py` | **Gemini Agent Sandbox** (isolated ephemeral Ubuntu Python runtime) |
| **Policy & T&C Knowledge** | `fineprint_auditor.py` rule & regex engine | **Vertex AI RAG Engine** (Visa CE3.0 / RBI / SaaS Dark-Pattern Corpus) |
| **Cryptographic Keys** | Local Ed25519 + HMAC-SHA256 | **Google Cloud KMS** (HSM-backed signing keys) |
| **Transactional Ledger** | SQLite `WAL` mode (`db.py`) | **Cloud Firestore** (ACID transactions) + **BigQuery** (audit analytics) |
| **Compute Hosting** | Single-process FastAPI + built React SPA | **Google Cloud Run** (autoscaling containers) |

---

## 5. Failure-Mode & Invariant Guarantees

1. **Tampered Mandate Rejection:** Any 1-byte modification to an `IntentMandate` (e.g., raising `daily_limit_inr` or adding `"GIFTCARD"` to `allowed_mccs`) fails Ed25519 verification before any agent runs.
2. **Zero Post-Settlement Subscription Bleed:** As soon as a valid charge settles on a `VirtualCard`, its status transitions atomically to `SHREDDED`. Any subsequent recurring charge attempt against the same PAN is rejected with `CARD_SHREDDED`.
3. **Zero Overcharge Tolerance:** Merchant settlements verify `round(charge_amount_inr, 2) == round(card.exact_amount_inr, 2)`. Even a `+₹1.00` discrepancy is rejected with `AMOUNT_MISMATCH`.
4. **Fail-Closed Circuit Breaker:** Three identical `(agent_id, merchant_name, amount_inr)` requests within 60 seconds automatically transition the agent's status to `PAUSED`.
