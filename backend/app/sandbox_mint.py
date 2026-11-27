"""Deterministic Python Agent Sandbox wrapper delegating to SandboxIssuingAdapter."""

from __future__ import annotations

from datetime import datetime

from .issuers.base import JITAuthRequest
from .issuers.sandbox import (
    SandboxIssuingAdapter,
    compute_luhn_pan,
    compute_scope_hmac,
    is_valid_luhn,
    luhn_checksum_digit,
)
from .models import VirtualCard

_DEFAULT_ADAPTER = SandboxIssuingAdapter()


def mint_scoped_virtual_card(
    agent_id: str,
    merchant_name: str,
    merchant_mcc: str,
    exact_amount_inr: float,
    payment_mandate_id: str,
    ttl_seconds: int | None = None,
    now: datetime | None = None,
) -> VirtualCard:
    return _DEFAULT_ADAPTER.mint_card(
        agent_id=agent_id,
        merchant_name=merchant_name,
        merchant_mcc=merchant_mcc,
        exact_amount_inr=exact_amount_inr,
        payment_mandate_id=payment_mandate_id,
        ttl_seconds=ttl_seconds,
        now=now,
    )


def validate_and_settle_charge(
    card: VirtualCard,
    merchant_name: str,
    merchant_mcc: str,
    charge_amount_inr: float,
    now: datetime | None = None,
    tolerance_bps: int = 0,
) -> tuple[bool, str, str, VirtualCard]:
    decision = _DEFAULT_ADAPTER.authorize_jit(
        card=card,
        auth_req=JITAuthRequest(
            card_id=card.card_id,
            merchant_name=merchant_name,
            merchant_mcc=merchant_mcc,
            amount_inr=charge_amount_inr,
            tolerance_bps=tolerance_bps,
        ),
        now=now,
    )
    return decision.approved, decision.reason_code, decision.message, decision.updated_card
