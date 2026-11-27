# Research Derivations: From Landmark Papers to Numen Production Code

Numen is not an ad-hoc prompt wrapper. Every enforcement boundary in `backend/app/` is derived directly from four peer-reviewed / arXiv systems-security and AI-agent papers.

---

## 1. Threat Model Foundation — `AgentDojo` Banking Suite (`arXiv:2406.13352`)

- **Paper:** *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents* (Debenedetti et al., ETH Zurich & Invariant Labs).
- **Key Finding:** Tool-augmented financial agents reading untrusted bills, transaction memos, or web snippets suffer **50%–75%+ targeted Attack Success Rates (ASR)** on unshielded frontier models—specifically hijacking recipient accounts, amounts, and categories while remaining inside nominal user budgets.
- **Derivation in Numen:** We explicitly model every external webpage (`untrusted_dom_html`) and merchant checkout clause (`checkout_terms_text`) as **adversarial untrusted observations** capable of hijacking an authorized agent's tool call (`request_scoped_card`).

---

## 2. Structural Isolation — Google DeepMind `CaMeL` (`arXiv:2503.18813`)

- **Paper:** *Defeating Prompt Injections by Design* (Debenedetti, Shumailov, Carlini, Tramèr et al., Google / Google DeepMind / ETH Zurich).
- **Core Mechanism:**
  1. **Control-Flow vs. Data-Flow Separation:** The user's trusted query defines an immutable *privileged control plan*; untrusted external observations reside strictly in *quarantined data variables* and may never alter control flow or escalate tool capabilities.
  2. **Capability & Provenance Tagging:** Every variable carries provenance metadata checked by a deterministic Python runtime before sensitive sinks execute.
- **Mathematical Invariant in Numen:**
  Let $\mathcal{P}$ denote the **Privileged Human Mandate** (`IntentMandate`: `allowed_mccs`, `prohibited_keywords`, `allow_recurring`, `max_single_tx_inr`) and $\mathcal{Q}$ denote **Quarantined Untrusted Data** (`untrusted_dom_html`, `checkout_terms_text`, external `merchant_domain`). A payment sink $S$ is permitted if and only if:
  $$\forall c \in \text{Capabilities}(S),\quad \text{Provenance}(c) \subseteq \mathcal{P} \;\land\; \neg\,\text{TaintedInfluence}(\mathcal{Q} \to S)$$
- **Code Implementation:** [`backend/app/agents/camel_capabilities.py`](../backend/app/agents/camel_capabilities.py) (`evaluate_camel_capabilities`) explicitly tags all `SpendRequest` fields into `PRIVILEGED_HUMAN_MANDATE` vs. `QUARANTINED_UNTRUSTED_DATA` and enforces `CAP_MCC_SCOPE`, `CAP_NO_PROHIBITED_SINK`, `CAP_NO_RECURRING_BINDING`, and `CAP_UNTRUSTED_CONTROL_FLOW_BLOCK`.

---

## 3. Agent–Tool Boundary — Dual Tool Firewalls (`arXiv:2510.05244`)

- **Paper:** *Indirect Prompt Injections: Are Firewalls All You Need, or Stronger Benchmarks?* (Bhagwatkar, Kasa, Puri, Huang, Rish, Taylor, Dvijotham, Lacoste — ServiceNow, Mila, Vector Institute).
- **Core Mechanism:** Place model-agnostic **Tool-Input Minimizers** and **Tool-Output Sanitizers** directly at the agent–tool boundary so untrusted instructions inside tool observations are stripped before driving downstream actions.
- **Code Implementation:** `extract_poisoned_spans()` in [`backend/app/agents/attriguard.py`](../backend/app/agents/attriguard.py) scans untrusted HTML/DOM at the MCP boundary for hidden CSS (`opacity:0`, `display:none`, `visibility:hidden`, `font-size:0`, `color:white`/`#fff`, off-screen `left:-9999px`), HTML comments (`<!-- ... -->`), zero-width Unicode (`\u200b`–`\ufeff`), and adversarial imperatives (`SYSTEM OVERRIDE`, `IGNORE PREVIOUS`, `URGENT SECURITY PATCH`).

---

## 4. Causal Verification — `AttriGuard` (`arXiv:2603.10749`, USENIX Security)

- **Paper:** *AttriGuard: Defeating Indirect Prompt Injection in LLM Agents via Causal Attribution of Tool Invocations*.
- **Core Mechanism:** Input filtering alone fails against obfuscated injections; instead, test **action-level causality** via parallel counterfactual evaluation under control-attenuated external observations:
  - **World A ($A_{\text{full}}$):** Proposed payment action given `IntentMandate` + untrusted external observations $\mathcal{Q}$.
  - **World B ($A_{\text{cf}}$):** Counterfactual action after attenuating/stripping untrusted observations $\mathcal{Q}$.
  - **Causal Attribution Drift:**
    $$\Delta_{\text{causal}} = d\!\left(A_{\text{full}},\, A_{\text{cf}}\right) \in [0, 1]$$
    In the paper's evaluation across 4 LLMs and 2 agent benchmarks, causal attribution achieves **0% static indirect prompt-injection ASR** with negligible utility loss.
- **Code Implementation:** `evaluate_attriguard()` in [`backend/app/agents/attriguard.py`](../backend/app/agents/attriguard.py) computes $\Delta_{\text{causal}}$ against threshold $\tau = 0.25$ (`NUMEN_ATTRIGUARD_DRIFT_THRESHOLD`), optionally fusing `Gemini 2.5 Pro` structured counterfactual scoring conservatively via $\max(\Delta_{\text{det}}, \Delta_{\text{llm}})$.

---

## 5. Paper-to-Code Traceability Matrix

| Paper / Protocol | Core Guarantee | Exact File & Function in `numen` |
| :--- | :--- | :--- |
| **Google Cloud `AP2`** | Ed25519 `Intent -> Cart -> Payment` mandates | `backend/app/crypto_ap2.py` (`sign_mandate`, `verify_mandate`) |
| **DeepMind `CaMeL` (`2503.18813`)** | Control vs. quarantined data capability isolation | `backend/app/agents/camel_capabilities.py` (`evaluate_camel_capabilities`) |
| **Dual Tool Firewalls (`2510.05244`)** | Hidden CSS / zero-width / comment DOM sanitizer | `backend/app/agents/attriguard.py` (`extract_poisoned_spans`) |
| **`AttriGuard` (`2603.10749`)** | Counterfactual World A vs. World B drift check | `backend/app/agents/attriguard.py` (`evaluate_attriguard`) |
| **Parameter Poisoning Defense** | Homoglyph domain & hidden annual clause traps | `backend/app/agents/fineprint_auditor.py` (`evaluate_fineprint`, `detect_lookalike_domain`) |
| **Visa / Mastercard Tokenized Cards** | 60s Luhn PAN, `±₹0.00` HMAC lock, post-settlement shred | `backend/app/sandbox_mint.py` (`mint_scoped_virtual_card`, `validate_and_settle_charge`) |
