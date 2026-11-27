# Numen — Layer-2 Agentic Spend Control & AP2 Issuing Backend

> **Programmable pre-authorization firewall and single-use virtual card issuer for AI agents.**  
> Isolates untrusted edge browsing from deterministic custody via **Google AP2 (`Ed25519`) 3-link mandate chains**, **CaMeL + AttriGuard causal verification**, **NFKC/HTML-entity DOM sanitization**, **atomic compare-and-swap double-entry settlement**, and **pluggable JIT card issuing adapters (`Sandbox` + `Stripe Issuing`)**.

---

## Documentation

1. **[Architecture Specification (`docs/ARCHITECTURE.md`)](docs/ARCHITECTURE.md)** — 3-Cluster topology, AP2 3-link cryptographic chain, double-entry paise ledger, hash-chained audit log, issuing adapters, MCP, A2A, and Stripe JIT webhooks.
2. **[Planned Solution & Threat Model (`docs/SOLUTION.md`)](docs/SOLUTION.md)** — Layer-2 problem statements, defense invariants (`CaMeL`, `AttriGuard`, `Dual Tool Firewalls`), evasion hardening, and production roadmap.

---

## Repository Structure

```text
numen/
├── .agents/skills/                   # Workspace engineering & UI standards
├── docs/
│   ├── ARCHITECTURE.md               # Technical topology, storage & protocol contracts
│   └── SOLUTION.md                   # Threat model, hardened defenses & roadmap
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI REST, SSE, MCP, A2A & Stripe JIT webhook
│   │   ├── config.py                 # Environment & signing/webhook settings
│   │   ├── models.py                 # Pydantic v2 schemas
│   │   ├── crypto_ap2.py             # SignerBackend, Ed25519 signing, expiry & 3-link chain verifier
│   │   ├── db.py                     # SQLite WAL atomic CAS, double-entry paise ledger, idempotency & audit chain
│   │   ├── gemini_router.py          # Gemini 2.5 Flash / Pro smart router
│   │   ├── mcp_server.py             # MCP JSON-RPC 2.0 server
│   │   ├── sandbox_mint.py           # Backwards-compatible wrapper delegating to issuers.sandbox
│   │   ├── scenarios.py              # Demo scenarios & 240-case verification suite
│   │   ├── issuers/                  # Pluggable IssuingAdapter, Sandbox & Stripe Issuing JIT adapter
│   │   └── agents/                   # Orchestrator, Budget/Loop, CaMeL, AttriGuard, FinePrint & A2A bus
│   └── tests/test_numen_core.py      # 15/15 unit, crypto, ledger, firewall, issuer, MCP & A2A tests
└── .env.example                      # Environment config template
```

---

## Quickstart & Testing

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v tests\test_numen_core.py
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
```

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.
