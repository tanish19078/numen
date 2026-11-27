"""Google Cloud AP2 Cryptographic Mandate Engine using Ed25519 signatures, expiry & 3-link chain verification."""

from __future__ import annotations

import base64
import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .config import get_settings
from .models import CartMandate, IntentMandate, PaymentMandate, SpendRequest

_SIGNATURE_FIELDS = {"canonical_hash", "signature_b64", "public_key_b64"}


class SignerBackend(ABC):
    """Pluggable AP2 key custody backend (local Ed25519 dev signer or Cloud KMS / HSM adapter)."""

    @abstractmethod
    def sign(self, raw: bytes) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def public_key_b64(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def key_id(self) -> str:
        raise NotImplementedError


class LocalEd25519Signer(SignerBackend):
    """Local Ed25519 signer seeded from NUMEN_SIGNING_SEED_HEX or deterministic dev key."""

    def __init__(self, private_key: Ed25519PrivateKey | None = None, signer_key_id: str = "local-ed25519-v1") -> None:
        if private_key is not None:
            self._key = private_key
        else:
            seed_hex = get_settings().signing_seed_hex
            if seed_hex:
                seed = hashlib.sha256(bytes.fromhex(seed_hex)).digest() if len(seed_hex) != 64 else bytes.fromhex(seed_hex)
            else:
                seed = hashlib.sha256(b"numen-ap2-ed25519-treasury-signer-v1").digest()
            self._key = Ed25519PrivateKey.from_private_bytes(seed)
        self._key_id = signer_key_id

    def sign(self, raw: bytes) -> bytes:
        return self._key.sign(raw)

    def public_key_b64(self) -> str:
        pub_bytes = self._key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(pub_bytes).decode("ascii")

    def key_id(self) -> str:
        return self._key_id


_DEFAULT_SIGNER: SignerBackend | None = None


def get_default_signer() -> SignerBackend:
    global _DEFAULT_SIGNER
    if _DEFAULT_SIGNER is None:
        _DEFAULT_SIGNER = LocalEd25519Signer()
    return _DEFAULT_SIGNER


def canonical_json(payload: dict[str, Any]) -> bytes:
    """Serialize payload deterministically after stripping signature fields."""
    clean = {k: v for k, v in payload.items() if k not in _SIGNATURE_FIELDS}
    return json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sign_mandate(
    payload: dict[str, Any],
    private_key: Ed25519PrivateKey | None = None,
    signer: SignerBackend | None = None,
) -> tuple[str, str, str]:
    """Return (canonical_sha256_hex, ed25519_sig_b64, public_key_b64)."""
    backend = LocalEd25519Signer(private_key=private_key) if private_key is not None else (signer or get_default_signer())
    raw = canonical_json(payload)
    digest_hex = hashlib.sha256(raw).hexdigest()
    sig_b64 = base64.b64encode(backend.sign(raw)).decode("ascii")
    return digest_hex, sig_b64, backend.public_key_b64()


def verify_mandate(
    payload: dict[str, Any],
    signature_b64: str,
    public_key_b64: str,
    check_expiry: bool = True,
    now: datetime | None = None,
) -> bool:
    """Verify Ed25519 signature, canonical SHA-256 digest, and non-expiration."""
    try:
        raw = canonical_json(payload)
        expected_hash = payload.get("canonical_hash")
        if expected_hash and hashlib.sha256(raw).hexdigest() != expected_hash:
            return False

        if check_expiry and payload.get("expires_at"):
            exp_dt = datetime.fromisoformat(str(payload["expires_at"]))
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            ref_now = now or datetime.now(timezone.utc)
            if ref_now > exp_dt:
                return False

        pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
        pub.verify(base64.b64decode(signature_b64), raw)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def verify_ap2_chain(
    intent: IntentMandate,
    cart: CartMandate,
    payment: PaymentMandate,
    check_expiry: bool = True,
    now: datetime | None = None,
) -> tuple[bool, list[str]]:
    """
    Verify the complete 3-link Google AP2 chain:
      IntentMandate (human cap) -> CartMandate (merchant + terms) -> PaymentMandate (60s scoped PAN).
    """
    errors: list[str] = []

    if not verify_mandate(intent.model_dump(), intent.signature_b64, intent.public_key_b64, check_expiry=check_expiry, now=now):
        errors.append("IntentMandate signature, digest, or expiry invalid.")
    if not verify_mandate(cart.model_dump(), cart.signature_b64, cart.public_key_b64, check_expiry=False, now=now):
        errors.append("CartMandate signature or digest invalid.")
    if not verify_mandate(payment.model_dump(), payment.signature_b64, payment.public_key_b64, check_expiry=check_expiry, now=now):
        errors.append("PaymentMandate signature, digest, or expiry invalid.")

    if cart.intent_mandate_id != intent.mandate_id:
        errors.append(f"CartMandate intent link mismatch ({cart.intent_mandate_id} != {intent.mandate_id}).")
    if payment.intent_mandate_id != intent.mandate_id:
        errors.append(f"PaymentMandate intent link mismatch ({payment.intent_mandate_id} != {intent.mandate_id}).")
    if payment.cart_id != cart.cart_id:
        errors.append(f"PaymentMandate cart link mismatch ({payment.cart_id} != {cart.cart_id}).")

    if round(payment.exact_amount_inr, 2) != round(cart.amount_inr, 2):
        errors.append(f"Payment amount ({payment.exact_amount_inr}) != Cart amount ({cart.amount_inr}).")
    if cart.amount_inr > intent.max_single_tx_inr:
        errors.append(f"Cart amount ({cart.amount_inr}) exceeds Intent max_single_tx_inr ({intent.max_single_tx_inr}).")

    return len(errors) == 0, errors


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
    signer: SignerBackend | None = None,
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
    chash, sig_b64, pub_b64 = sign_mandate(base, signer=signer)
    return IntentMandate(**base, canonical_hash=chash, signature_b64=sig_b64, public_key_b64=pub_b64)


def create_cart_mandate(
    intent_mandate_id: str,
    spend_request: SpendRequest,
    signer: SignerBackend | None = None,
) -> CartMandate:
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
    chash, sig_b64, pub_b64 = sign_mandate(base, signer=signer)
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
    signer: SignerBackend | None = None,
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
    chash, sig_b64, pub_b64 = sign_mandate(base, signer=signer)
    return PaymentMandate(**base, canonical_hash=chash, signature_b64=sig_b64, public_key_b64=pub_b64)
