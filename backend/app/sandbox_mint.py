"""Deterministic Python Agent Sandbox: Luhn PAN minting, HMAC-SHA256 scope lock, and 60s TTL enforcement."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .config import get_settings
from .models import VirtualCard


def luhn_checksum_digit(partial_pan: str) -> str:
    """Compute final Luhn digit for a 15-digit numeric prefix."""
    digits = [int(ch) for ch in partial_pan]
    total = 0
    for idx, val in enumerate(reversed(digits)):
        if idx % 2 == 0:
            doubled = val * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += val
    return str((10 - (total % 10)) % 10)


def is_valid_luhn(pan: str) -> bool:
    """Verify full 16-digit PAN satisfies the Luhn mod-10 invariant."""
    cleaned = pan.replace(" ", "")
    if not cleaned.isdigit() or len(cleaned) != 16:
        return False
    digits = [int(ch) for ch in cleaned]
    total = 0
    for idx, val in enumerate(reversed(digits)):
        if idx % 2 == 1:
            doubled = val * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += val
    return total % 10 == 0


def compute_luhn_pan(bin_prefix: str = "453289") -> str:
    """Generate a cryptographically random, Luhn-valid 16-digit virtual Visa PAN."""
    body = "".join(str(secrets.randbelow(10)) for _ in range(15 - len(bin_prefix)))
    partial = f"{bin_prefix}{body}"
    return partial + luhn_checksum_digit(partial)


def compute_scope_hmac(
    card_id: str,
    merchant_name: str,
    merchant_mcc: str,
    exact_amount_inr: float,
    expires_at: str,
    secret: str | None = None,
) -> str:
    key = (secret or get_settings().hmac_secret).encode("utf-8")
    paise = int(round(exact_amount_inr * 100))
    msg = f"{card_id}|{merchant_name.strip().lower()}|{merchant_mcc.strip().upper()}|{paise}|{expires_at}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def mint_scoped_virtual_card(
    agent_id: str,
    merchant_name: str,
    merchant_mcc: str,
    exact_amount_inr: float,
    payment_mandate_id: str,
    ttl_seconds: int | None = None,
    now: datetime | None = None,
) -> VirtualCard:
    settings = get_settings()
    ttl = ttl_seconds if ttl_seconds is not None else settings.card_ttl_seconds
    ts = now or datetime.now(timezone.utc)
    exp = ts + timedelta(seconds=ttl)
    card_id = f"vc_{uuid4().hex[:10]}"
    pan = compute_luhn_pan("453289")
    cvv = f"{secrets.randbelow(900) + 100}"
    expires_iso = exp.isoformat()
    scope_hmac = compute_scope_hmac(
        card_id=card_id,
        merchant_name=merchant_name,
        merchant_mcc=merchant_mcc,
        exact_amount_inr=exact_amount_inr,
        expires_at=expires_iso,
        secret=settings.hmac_secret,
    )
    return VirtualCard(
        card_id=card_id,
        agent_id=agent_id,
        pan=pan,
        pan_masked=f"{pan[:4]} •••• •••• {pan[-4:]}",
        cvv=cvv,
        exp_month=f"{exp.month:02d}",
        exp_year=str(exp.year + 2)[-2:],
        merchant_name=merchant_name,
        merchant_mcc=merchant_mcc.upper(),
        exact_amount_inr=round(float(exact_amount_inr), 2),
        status="ACTIVE",
        scope_hmac=scope_hmac,
        payment_mandate_id=payment_mandate_id,
        created_at=ts.isoformat(),
        expires_at=expires_iso,
        settled_at=None,
    )


def validate_and_settle_charge(
    card: VirtualCard,
    merchant_name: str,
    merchant_mcc: str,
    charge_amount_inr: float,
    now: datetime | None = None,
) -> tuple[bool, str, str, VirtualCard]:
    """
    Strictly validate a merchant settlement attempt against a scoped ephemeral card.
    On approval, immediately transitions card status to SHREDDED so PAN cannot be reused.
    """
    ts = now or datetime.now(timezone.utc)

    if card.status == "SHREDDED":
        return False, "CARD_SHREDDED", "Card PAN permanently shredded after single-use settlement (zombie subscription blocked).", card
    if card.status != "ACTIVE":
        return False, f"CARD_{card.status}", f"Card is {card.status} and cannot accept charges.", card

    exp_dt = datetime.fromisoformat(card.expires_at)
    if ts > exp_dt:
        expired_card = card.model_copy(update={"status": "EXPIRED"})
        return False, "CARD_EXPIRED", "60-second ephemeral TTL window elapsed; virtual card auto-expired.", expired_card

    expected_hmac = compute_scope_hmac(
        card_id=card.card_id,
        merchant_name=card.merchant_name,
        merchant_mcc=card.merchant_mcc,
        exact_amount_inr=card.exact_amount_inr,
        expires_at=card.expires_at,
    )
    if not hmac.compare_digest(card.scope_hmac, expected_hmac):
        return False, "SCOPE_HMAC_INVALID", "Card scope HMAC verification failed.", card

    if merchant_name.strip().lower() != card.merchant_name.strip().lower() or merchant_mcc.strip().upper() != card.merchant_mcc.strip().upper():
        return (
            False,
            "MERCHANT_SCOPE_MISMATCH",
            f"Merchant '{merchant_name} ({merchant_mcc})' does not match locked scope '{card.merchant_name} ({card.merchant_mcc})'.",
            card,
        )

    if round(float(charge_amount_inr), 2) != round(float(card.exact_amount_inr), 2):
        return (
            False,
            "AMOUNT_MISMATCH",
            f"Charge INR {charge_amount_inr:,.2f} violates exact-rupee lock INR {card.exact_amount_inr:,.2f} (+/- 0% tolerance).",
            card,
        )

    shredded_card = card.model_copy(update={"status": "SHREDDED", "settled_at": ts.isoformat()})
    return (
        True,
        "SETTLED_AND_SHREDDED",
        f"Settled INR {charge_amount_inr:,.2f} with {merchant_name}; PAN *{card.pan[-4:]} immediately shredded.",
        shredded_card,
    )
