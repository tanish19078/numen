"""Abstract issuing adapter & JIT authorization contracts with configurable FX/GST tolerance bands."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel, Field

from ..models import VirtualCard


class JITAuthRequest(BaseModel):
    card_id: str
    merchant_name: str
    merchant_mcc: str
    amount_inr: float = Field(gt=0)
    tolerance_bps: int = Field(default=0, ge=0, le=500)


class JITAuthDecision(BaseModel):
    approved: bool
    reason_code: str
    message: str
    updated_card: VirtualCard


class IssuingAdapter(ABC):
    """Unified interface across Sandbox, Stripe Issuing, Marqeta, or RazorpayX virtual card rails."""

    @abstractmethod
    def mint_card(
        self,
        agent_id: str,
        merchant_name: str,
        merchant_mcc: str,
        exact_amount_inr: float,
        payment_mandate_id: str,
        ttl_seconds: int | None = None,
        now: datetime | None = None,
    ) -> VirtualCard:
        raise NotImplementedError

    @abstractmethod
    def authorize_jit(
        self,
        card: VirtualCard,
        auth_req: JITAuthRequest,
        now: datetime | None = None,
    ) -> JITAuthDecision:
        raise NotImplementedError
