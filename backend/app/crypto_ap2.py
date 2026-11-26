"""Google Cloud AP2 Cryptographic Mandate Engine using Ed25519 signatures and canonical SHA-256."""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .models import CartMandate, IntentMandate, PaymentMandate, SpendRequest

_SIGNATURE_FIELDS = {"canonical_hash", "signature_b64", "public_key_b64"}

# Deterministic fallback seed derived locally for process continuity across restarts
_DEFAULT_SEED = hashlib.sha256(b"numen-ap2-ed25519-treasury-signer-v1").digest()
_SIGNING_KEY = Ed25519PrivateKey.from_private_bytes(_DEFAULT_SEED)


def canonical_json(payload: dict[str, Any]) -> bytes:
    """Serialize payload deterministically after stripping signature fields."""
    clean = {k: v for k, v in payload.items() if k not in _SIGNATURE_FIELDS}
    return json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sign_mandate(payload: dict[str, Any], private_key: Ed25519PrivateKey | None = None) -> tuple[str, str, str]:
    """Return (canonical_sha256_hex, ed25519_sig_b64, public_key_b64)."""
    key = private_key or _SIGNING_KEY
    raw = canonical_json(payload)
    digest_hex = hashlib.sha256(raw).hexdigest()
    sig_b64 = base64.b64encode(key.sign(raw)).decode("ascii")
    pub_bytes = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    pub_b64 = base64.b64encode(pub_bytes).decode("ascii")
    return digest_hex, sig_b64, pub_b64


def verify_mandate(payload: dict[str, Any], signature_b64: str, public_key_b64: str) -> bool:
    """Verify Ed25519 signature & canonical SHA-256 digest; returns False on any 1-byte tamper."""
    try:
        raw = canonical_json(payload)
        expected_hash = payload.get("canonical_hash")
        if expected_hash and hashlib.sha256(raw).hexdigest() != expected_hash:
            return False
        pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
        pub.verify(base64.b64decode(signature_b64), raw)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def create_intent_mandate(
    agent_id: str,
    natural_language_intent: str,
    max_daily_inr: float,
    max_single_tx_inr: float,
    allowed_mccs: list[str],
    prohibited_keywords: list[str] | None = None,
    allow_recurring: bool = False,
    mandate_id: str | None = None,
    issuer: str = "Acme AI Labs — Treasury Owner",
    ttl_days: int = 365,
) -> IntentMandate:
    now = datetime.now(timezone.utc)
    base = {
        "mandate_id": mandate_id or f"mandate_{uuid4().hex[:10]}",
        "agent_id": agent_id,
        "issuer": issuer,
        "natural_language_intent": natural_language_intent,
        "max_daily_inr": round(float(max_daily_inr), 2),
        "max_single_tx_inr": round(float(max_single_tx_inr), 2),
        "allowed_mccs": [m.upper() for m in allowed_mccs],
        "prohibited_keywords": [k.lower() for k in (prohibited_keywords or ["gift", "voucher", "crypto", "casino", "wire"])],
        "allow_recurring": bool(allow_recurring),
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(days=ttl_days)).isoformat(),
    }
    chash, sig_b64, pub_b64 = sign_mandate(base)
    return IntentMandate(**base, canonical_hash=chash, signature_b64=sig_b64, public_key_b64=pub_b64)


def create_cart_mandate(intent_mandate_id: str, spend_request: SpendRequest) -> CartMandate:
    now = datetime.now(timezone.utc)
    terms_digest = hashlib.sha256((spend_request.checkout_terms_text or "").encode("utf-8")).hexdigest()
    base = {
        "cart_id": f"cart_{uuid4().hex[:10]}",
        "intent_mandate_id": intent_mandate_id,
        "agent_id": spend_request.agent_id,
        "merchant_name": spend_request.merchant_name,
        "merchant_domain": spend_request.merchant_domain.lower(),
        "merchant_mcc": spend_request.merchant_mcc.upper(),
        "amount_inr": round(float(spend_request.amount_inr), 2),
        "currency": spend_request.currency.upper(),
        "cart_items": list(spend_request.cart_items),
        "terms_sha256": terms_digest,
        "issued_at": now.isoformat(),
    }
    chash, sig_b64, pub_b64 = sign_mandate(base)
    return CartMandate(**base, canonical_hash=chash, signature_b64=sig_b64, public_key_b64=pub_b64)


def create_payment_mandate(
    intent_mandate_id: str,
    cart_id: str,
    card_id: str,
    pan_last4: str,
    exact_amount_inr: float,
    merchant_name: str,
    scope_hmac: str,
    issued_at: str,
    expires_at: str,
) -> PaymentMandate:
    base = {
        "payment_mandate_id": f"pm_{uuid4().hex[:10]}",
        "intent_mandate_id": intent_mandate_id,
        "cart_id": cart_id,
        "card_id": card_id,
        "pan_last4": pan_last4,
        "exact_amount_inr": round(float(exact_amount_inr), 2),
        "merchant_name": merchant_name,
        "scope_hmac": scope_hmac,
        "issued_at": issued_at,
        "expires_at": expires_at,
    }
    chash, sig_b64, pub_b64 = sign_mandate(base)
    return PaymentMandate(**base, canonical_hash=chash, signature_b64=sig_b64, public_key_b64=pub_b64)
