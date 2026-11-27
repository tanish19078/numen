# Numen — The AP2-Native Neobank & Spend Firewall for AI Agents

> **Programmable Corporate Banking Built on a 3-Cluster Agentic Quorum.**  
> Verify **why** an AI agent wants to spend before a single rupee moves — combining **Google Cloud AP2 Cryptographic Mandates (`Ed25519`)**, **DeepMind `CaMeL` (`arXiv:2503.18813`)**, **Dual Tool Firewalls (`arXiv:2510.05244`)**, **USENIX `AttriGuard` (`arXiv:2603.10749`)**, and **60-Second Exact-Rupee Virtual Cards**.
>
> **Start here to learn & discuss with peers:** [**Complete Pitch, Pre/Post Flow & Visual Architecture Guide (`docs/NUMEN_PITCH_AND_GUIDE.md`)**](docs/NUMEN_PITCH_AND_GUIDE.md)

---

## 1. Why Static Corporate Cards Break for AI Agents

Unshielded frontier agents in the **`AgentDojo` Banking Suite (`arXiv:2406.13352`)** suffer **55.0% targeted attack success (`79/144` attack paths on `gpt-4o-2024-08-06`; `47.7%` overall / `33.9%` on `Claude 3.5 Sonnet`)**. Static `₹10,000` spend caps fail because attacks happen **below** the limit:

1. **Sub-Limit Indirect Prompt Injections:** Hidden CSS (`opacity:0`) redirects `Procurement-Agent` to buy `₹4,200` gift vouchers under a `₹10,000` limit.
2. **Dark-Pattern Annual Lock-Ins:** A `₹99` trial hides Clause 14.3 non-cancellable `₹36,000/yr` auto-renewal onto a reusable PAN.
3. **Homoglyph Domains & Retry Loops:** Billing spoofs (`runp0d.io`) or gateway timeout loops (`3x/60s`) drain funds autonomously.

---

## 2. 3-Cluster Agentic Architecture ([Full Spec](docs/AGENTIC_CLUSTER_ARCHITECTURE.md))

1. **Cluster 1 — Edge Commerce Agents:** External agents discover Numen (`GET /.well-known/agent.json`) and request credentials via MCP (`POST /mcp -> request_scoped_card`). Zero raw PAN custody at the edge.
2. **Cluster 2 — Verification & Consensus Quorum (`backend/app/agents/`):** `Gemini 2.5` Smart Router (`Flash` fast-path vs. `Pro` deep reasoning) coordinates 4 independent verifier votes (`Budget & 3x/60s Loop`, `CaMeL Provenance`, `AttriGuard World A vs B Drift`, `FinePrint & Homoglyph`).
3. **Cluster 3 — Zero-LLM Deterministic Custody (`backend/app/`):** Signs `Ed25519` AP2 mandates, mints 60-second `HMAC-SHA256` locked Luhn Visa PANs (`±₹0.00`), commits to `SQLite WAL`, and permanently shreds each PAN after 1 settlement.

---

## 3. Clean Repository Map

```text
numen/
├── .agents/skills/                   # Workspace Craft Skills (frontend-design, pitch-deck-design, system-integration-clarity)
├── DESIGN.md                         # Canonical visual tokens shared across Web UI, PPTX & HTML Keynote
├── docs/
│   ├── NUMEN_PITCH_AND_GUIDE.md      # Single-file Pitch, Pre/Post Flow, A2A+AP2 Builds & Visual Mermaid Diagrams
│   ├── NUMEN_MASTER_DECK_BRIEF.md    # Master PS, verified research metrics, 3-cluster thesis & 9-slide brief
│   ├── AGENTIC_CLUSTER_ARCHITECTURE.md # 3-cluster topology, MCP/A2A contracts & Live vs Production Adapters
│   └── DEMO_RUNBOOK.md               # Live 3-act demo walkthrough
├── deck/
│   ├── Numen_Pitch_Deck.pptx         # 9-slide editorial pitch deck (bounds-audited)
│   └── Numen_Keynote_Live.html       # Fixed 1920x1080 interactive stage keynote
├── backend/
│   ├── app/                          # FastAPI, A2A Agent Card, MCP server, 4-voter firewall, Ed25519 & Luhn mint
│   └── tests/test_numen_core.py      # 10/10 unit, crypto, firewall, MCP, A2A & benchmark verification tests
└── frontend/                         # Calm editorial Neobank Treasury Console (React + Vite + Tailwind)
```

---

## 4. Quickstart & Verification

```powershell
# Backend tests (10/10 passing) & live unified server
cd backend
.\.venv\Scripts\python.exe -m pytest -v tests\test_numen_core.py
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000

# Rebuild React SPA (served automatically at http://127.0.0.1:8000)
cd ..\frontend
npm run build

# Rebuild & audit 9-slide Pitch Deck
cd ..
python scripts\build_pitch_deck.py
```
