# Google AP2 (Agent Payments Protocol) Implementation in Numen

Numen implements the **Agent Payments Protocol (AP2)** Verifiable Credential mandate chain using **Ed25519 asymmetric signatures**, **canonical JSON SHA-256 digests**, and **HMAC-SHA256 virtual card scope tokens** (`backend/app/crypto_ap2.py` & `backend/app/sandbox_mint.py`).

---

## 1. The Three-Mandate Cryptographic Chain

```mermaid
flowchart LR
    IM["1. IntentMandate (Human Ed25519 Signed)"] -->|"Bounds agent budget, MCCs & prohibitions"| CM["2. CartMandate (Merchant & T&C Hash)"]
    CM -->|"Passes AttriGuard & FinePrint"| PM["3. PaymentMandate (Bound to 60s Luhn Card)"]
```

### 1.1 `IntentMandate` (Human Delegation Contract)
Signed by the human treasury owner when provisioning or updating an AI agent sub-account. Captures natural-language intent alongside machine-verifiable constraints:

```json
{
  "mandate_id": "mandate_devops_01",
  "agent_id": "agent-devops",
  "issuer": "Acme AI Labs — Treasury Owner",
  "natural_language_intent": "Auto-scale RunPod/GCP GPU compute & buy inference APIs up to INR 25,000/day; zero recurring annual lock-ins.",
  "max_daily_inr": 25000.0,
  "max_single_tx_inr": 15000.0,
  "allowed_mccs": ["CLOUD", "INFRA", "API"],
  "prohibited_keywords": ["gift", "voucher", "crypto", "casino", "wire"],
  "allow_recurring": false,
  "issued_at": "2026-11-26T16:30:00+00:00",
  "expires_at": "2027-11-26T16:30:00+00:00",
  "canonical_hash": "sha256_hex...",
  "signature_b64": "ed25519_sig_base64...",
  "public_key_b64": "ed25519_pub_base64..."
}
```

### 1.2 `CartMandate` (Point-of-Checkout Digest)
Constructed when the agent invokes `request_scoped_card`. Commits to exact merchant identity, MCC, itemized cart list, exact rupee total, and SHA-256 hash of any checkout terms inspected:

```json
{
  "cart_id": "cart_7f9a21c0",
  "intent_mandate_id": "mandate_devops_01",
  "agent_id": "agent-devops",
  "merchant_name": "RunPod Cloud",
  "merchant_domain": "runpod.io",
  "merchant_mcc": "CLOUD",
  "amount_inr": 3400.0,
  "currency": "INR",
  "cart_items": ["2x NVIDIA A100 GPU hours"],
  "terms_sha256": "e3b0c442...",
  "canonical_hash": "sha256_hex...",
  "signature_b64": "ed25519_sig_base64..."
}
```

### 1.3 `PaymentMandate` (Settlement Authorization)
Minted only after `BudgetController`, `AttriGuard`, and `FinePrintAuditor` all return passing verdicts (or after 1-Tap Founder Passkey approval). Binds the `IntentMandate` and `CartMandate` hashes to a **60-second single-use Luhn virtual card**:

```json
{
  "payment_mandate_id": "pm_881b44e2",
  "intent_mandate_id": "mandate_devops_01",
  "cart_id": "cart_7f9a21c0",
  "card_id": "vc_991a03f4",
  "pan_last4": "9104",
  "exact_amount_inr": 3400.0,
  "merchant_name": "RunPod Cloud",
  "scope_hmac": "hmac_sha256_hex...",
  "expires_at": "2026-11-26T16:45:00+00:00",
  "canonical_hash": "sha256_hex...",
  "signature_b64": "ed25519_sig_base64..."
}
```

---

## 2. Canonical Serialization & Tamper Verification

1. Before signing or verifying any mandate payload, signature metadata fields (`canonical_hash`, `signature_b64`, `public_key_b64`) are stripped.
2. The remaining dictionary is serialized with `json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")`.
3. `canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()`.
4. `signature_b64` is produced via `Ed25519PrivateKey.sign(canonical_bytes)`.
5. `verify_mandate(payload, sig_b64, pubkey_b64)` recomputes `canonical_bytes` and verifies the Ed25519 signature. **Changing a single digit in `max_daily_inr`, `allowed_mccs`, or `exact_amount_inr` causes immediate signature rejection (`InvalidSignature -> False`).**

---

## 3. Virtual Card Scope Token (`scope_hmac`)

Inside `sandbox_mint.py`, every ephemeral card carries an HMAC-SHA256 tag over:

```text
"{card_id}|{merchant_name.lower()}|{merchant_mcc.upper()}|{exact_amount_paise}|{expires_at_iso}"
```

At merchant settlement (`POST /api/cards/{card_id}/charge`), the sandbox recomputes and compares `hmac.compare_digest` alongside:
- `card.status == "ACTIVE"` (rejects `SETTLED` / `SHREDDED` / `EXPIRED`)
- `now_utc <= card.expires_at` (enforces 60-second TTL)
- `round(charge_amount_inr, 2) == round(card.exact_amount_inr, 2)` (blocks `+₹1` overcharges)
- `merchant_name` & `merchant_mcc` exact match

Upon successful settlement, the card transitions to **`SHREDDED`** irreversibly.
