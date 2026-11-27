"""Stripe Issuing Just-In-Time (JIT) Real-Time Authorization Webhook Adapter."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from .. import db
from ..config import get_settings
from .base import JITAuthRequest
from .sandbox import SandboxIssuingAdapter


def verify_stripe_signature(raw_body: bytes, sig_header: str, secret: str) -> bool:
    """Verify Stripe-Signature header (`t=<ts>,v1=<hmac_hex>`) via HMAC-SHA256."""
    if not sig_header or not secret:
        return False
    parts: dict[str, str] = {}
    for item in sig_header.split(","):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            parts[k] = v
    ts = parts.get("t")
    sig_v1 = parts.get("v1")
    if not ts or not sig_v1:
        return False
    signed_payload = f"{ts}.".encode("utf-8") + raw_body
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_v1)


class StripeIssuingJITAdapter(SandboxIssuingAdapter):
    """Maps Stripe Issuing `issuing_authorization.request` webhooks to Numen atomic JIT enforcement."""

    def handle_webhook(self, raw_body: bytes, sig_header: str, db_path: str | None = None) -> tuple[int, dict[str, Any]]:
        secret = get_settings().stripe_webhook_secret
        if not verify_stripe_signature(raw_body, sig_header, secret):
            return 401, {"error": "Invalid Stripe-Signature HMAC"}

        event = json.loads(raw_body.decode("utf-8"))
        auth_obj = (event.get("data") or {}).get("object") or {}
        card_meta = (auth_obj.get("card") or {}).get("metadata") or {}
        card_id = card_meta.get("numen_card_id") or auth_obj.get("card_id", "")
        tolerance_bps = int(card_meta.get("tolerance_bps", 0))

        card = db.get_virtual_card(card_id, db_path=db_path)
        if not card:
            return 200, {"approved": False, "metadata": {"reason_code": "UNKNOWN_CARD", "message": f"Unknown Numen card '{card_id}'"}}

        merch_data = auth_obj.get("merchant_data") or {}
        merchant_name = merch_data.get("name", card.merchant_name)
        merchant_mcc = merch_data.get("category", card.merchant_mcc)
        amount_inr = round(float(auth_obj.get("amount", 0)) / 100.0, 2)

        decision = self.authorize_jit(
            card=card,
            auth_req=JITAuthRequest(
                card_id=card_id,
                merchant_name=merchant_name,
                merchant_mcc=merchant_mcc,
                amount_inr=amount_inr,
                tolerance_bps=tolerance_bps,
            ),
        )
        approved = decision.approved
        reason_code = decision.reason_code
        message = decision.message

        if approved:
            settled_ok, cas_code, _ = db.settle_card_atomic(decision.updated_card, amount_inr, db_path=db_path)
            if not settled_ok:
                approved = False
                reason_code = cas_code
                message = "Concurrent Stripe JIT authorization conflict."

        db.record_audit_event(
            trace_id=f"stripe_jit_{card_id}",
            agent_id=card.agent_id,
            event_type="STRIPE_JIT_WEBHOOK",
            decision="APPROVED" if approved else "DECLINED",
            summary=f"[{reason_code}] {message}",
            metadata={"card_id": card_id, "amount_inr": amount_inr, "tolerance_bps": tolerance_bps},
            db_path=db_path,
        )
        return 200, {
            "approved": approved,
            "metadata": {
                "reason_code": reason_code,
                "card_status": decision.updated_card.status if approved else card.status,
                "message": message,
            },
        }
