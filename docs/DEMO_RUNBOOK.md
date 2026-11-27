# Numen Live Demo Runbook (Neobank Console)

## Pre-Flight (Before Presenting)
1. Open **`http://127.0.0.1:8000`** in your browser and optionally open [`deck/Numen_Keynote_Live.html`](../deck/Numen_Keynote_Live.html) in a second tab for the 9-slide pitch.
2. Click **`Reset Demo Vault`** at the bottom of the left sidebar (Master Vault resets to `₹18,40,000`, all 3 agent sub-accounts reset to `ACTIVE`).

---

## 3-Act Live Stage Walkthrough

### Act 1 — Legitimate Autonomous Mint & Exact-Rupee Lock
1. In **`Treasury Overview`** (or **`Spend Firewall`**), click **`1. Valid GPU Scale (INR 3,400)`**.
2. Point out the **6-Step Horizontal Pipeline Stepper**: `AP2 Ed25519` → `Gemini Router (Flash)` → `Budget & Loop` → `CaMeL Provenance` → `AttriGuard Drift (0.00)` → `Mint`.
3. Under the brushed dark-pine **60s Virtual Card** on the right:
   - Click **`Test +₹1 (₹3401)`** → declined immediately (`AMOUNT_MISMATCH`).
   - Click **`Settle ₹3400`** → approved (`SETTLED`) and card status switches to **`SHREDDED`**.
   - Click **`Test 2nd Charge`** → declined (`CARD_SHREDDED`).

### Act 2 — Sub-Limit Indirect Prompt-Injection Block
1. Click **`2. Poisoned Webpage Hijack (INR 4,200)`**.
2. Highlight the contrast:
   - **Legacy `₹10,000` Static Card:** `BLINDLY APPROVED` (`4,200 <= 10,000`).
   - **Numen Cluster 2 Quorum:** Strips hidden `<span style='opacity:0'>` injection span, shows **World A vs. World B** counterfactual divergence (**Drift `1.00`**), blocks pre-mint (`₹0` lost), and auto-pauses `Procurement-Agent`.

### Act 3 — Hidden Fine-Print Trap & 1-Tap Passkey Escalation
1. Click **`3. INR 99 -> INR 36k/yr SaaS Trap`**.
2. Point out Clause 14.3 caught before any PAN issues (`₹36,000/yr` non-cancellable annual trap) and resolve via the **Founder Passkey** modal (**Deny & Block Trap** or **Approve 1-Time ₹99 Cap**).

---

## Bonus Architecture & Q&A Views
- **`AP2 Mandates & Ledger`:** Click **`Run +₹1 Tamper Test`** to show live `Ed25519` signature rejection.
- **`System & Integrations`:** Show the **3-Cluster Topology**, **Live Today vs. Production Adapters** honesty table, live `POST /mcp` inspector, and live `GET /.well-known/agent.json`.
- **`Red-Team & Lab`:** Click **`Run 240 Benchmarks`** (`100%` sub-limit block rate, `0/50` false positives, `₹0.00` bleed).
