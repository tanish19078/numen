# Numen 90-Second Stage Demo Runbook

## Pre-Flight Checklist (30 Seconds Before Judging)
1. Start the unified Numen server:
   ```powershell
   cd backend
   .\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. Open `http://127.0.0.1:8000` in your browser (or open `deck/Numen_Keynote_Live.html` alongside it).
3. Click **Reset Demo State** in the top bar so Master Vault is `₹18,40,000` and all 3 agents are `ACTIVE`.

---

## 90-Second 3-Act Live Demo Script

### Act 1 — Legitimate Autonomous Mint & Exact-Rupee Lock (~30s)
1. Click **`1. Valid GPU Scale (₹3,400)`** (`DevOps-Agent` -> `RunPod Cloud`).
2. Point out on the Right Pane:
   - Smart Router selected **`gemini-2.5-flash`** (~185ms fast path).
   - Ed25519 `IntentMandate` verified, `AttriGuard Drift = 0.00 (SAFE)`.
3. Point out the live ticking **Mint-Lime 60s Virtual Card** on the Left Pane.
4. Click **`Test +₹1 Overcharge (₹3,401)`** directly under the card -> **DECLINED (`AMOUNT_MISMATCH`)**.
5. Click **`Test Valid Charge (₹3,400)`** -> **SETTLED** and card immediately turns **SHREDDED**.
6. Click **`Test 2nd Recurring Charge`** -> **DECLINED (`CARD_SHREDDED`)**, proving zero future subscription bleed.

### Act 2 — Sub-Limit Indirect Prompt-Injection Block (~30s)
1. Click **`2. Poisoned Webpage Hijack (₹4,200)`** (`Procurement-Agent`).
2. Highlight the killer comparison:
   - **Legacy `₹10,000` spend-cap card:** **`BLINDLY APPROVED`** (`4,200 < 10,000`).
   - **Numen (`AttriGuard` + `gemini-2.5-pro`):** Strips the hidden `<span style="opacity:0">` prompt injection, detects **Causal Drift = 0.94**, highlights the exact poisoned DOM span in red, **blocks minting**, and **auto-pauses `Procurement-Agent`**.

### Act 3 — Hidden Fine-Print Trap & 1-Tap Passkey (~30s)
1. Click **`3. ₹99 → ₹36k/yr SaaS Trap`** (`Research-Agent`).
2. Show how `FinePrintAuditor` inspects checkout T&Cs, catches **Clause 14.3 (`₹36,000/yr` non-cancellable annual auto-debit)** behind the `₹99` headline, holds minting, and pops the **Founder Passkey Approval Drawer**.
3. Click **`Deny & Block Trap`** (or **`Approve 1-Time Cap`**) to complete the live HITL loop.

---

## Bonus Judge Proof (If Asked in Q&A)
- Switch to the **Benchmarks & MCP** tab and click **`Run 240-Scenario Red-Team Suite`** to execute all 240 live attacks/checkouts in ~1 second and display live measured block rates.
- Switch to the **Custom Attack Lab** tab and let any judge type their own poisoned HTML or fine-print clause to test `AttriGuard` live!
