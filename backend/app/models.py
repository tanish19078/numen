"""Strict Pydantic v2 schemas for Numen treasury, AP2 mandates, firewall verdicts, and MCP."""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


AgentStatus = Literal["ACTIVE", "PAUSED"]
CardStatus = Literal["ACTIVE", "SETTLED", "EXPIRED", "SHREDDED"]
DecisionKind = Literal["MINTED", "BLOCKED", "PASSKEY_REQUIRED"]
PasskeyStatus = Literal["PENDING", "APPROVED", "DENIED"]


class MasterVault(BaseModel):
    vault_id: str
    name: str
    balance_inr: float
    currency: str = "INR"


class AgentAccount(BaseModel):
    agent_id: str
    name: str
    role: str
    status: AgentStatus
    daily_limit_inr: float
    spent_today_inr: float
    allowed_mccs: list[str]
    intent_mandate_id: str


class IntentMandate(BaseModel):
    mandate_id: str
    agent_id: str
    issuer: str
    natural_language_intent: str
    max_daily_inr: float
    max_single_tx_inr: float
    allowed_mccs: list[str]
    prohibited_keywords: list[str]
    allow_recurring: bool = False
    issued_at: str
    expires_at: str
    canonical_hash: str
    signature_b64: str
    public_key_b64: str


class CartMandate(BaseModel):
    cart_id: str
    intent_mandate_id: str
    agent_id: str
    merchant_name: str
    merchant_domain: str
    merchant_mcc: str
    amount_inr: float
    currency: str = "INR"
    cart_items: list[str]
    terms_sha256: str
    issued_at: str
    canonical_hash: str
    signature_b64: str
    public_key_b64: str


class PaymentMandate(BaseModel):
    payment_mandate_id: str
    intent_mandate_id: str
    cart_id: str
    card_id: str
    pan_last4: str
    exact_amount_inr: float
    merchant_name: str
    scope_hmac: str
    issued_at: str
    expires_at: str
    canonical_hash: str
    signature_b64: str
    public_key_b64: str


class SpendRequest(BaseModel):
    agent_id: str
    merchant_name: str
    merchant_domain: str
    merchant_mcc: str
    amount_inr: float = Field(gt=0)
    currency: str = "INR"
    cart_items: list[str] = Field(default_factory=list)
    agent_reasoning: str = ""
    untrusted_dom_html: str = ""
    checkout_terms_text: str = ""
    idempotency_key: str | None = None


class CreateIntentMandateRequest(BaseModel):
    agent_id: str
    natural_language_intent: str
    max_daily_inr: float = Field(gt=0)
    max_single_tx_inr: float = Field(gt=0)
    allowed_mccs: list[str]
    prohibited_keywords: list[str] = Field(default_factory=lambda: ["gift", "voucher", "crypto", "casino", "wire"])
    allow_recurring: bool = False


class AttriGuardResult(BaseModel):
    drift_score: float = Field(ge=0.0, le=1.0)
    world_a_action: str
    world_b_action: str
    poisoned_spans: list[str] = Field(default_factory=list)
    injection_detected: bool
    explanation: str


class FinePrintResult(BaseModel):
    has_trap: bool
    hidden_annual_inr: float = 0.0
    spoofed_domain_of: str | None = None
    clauses_flagged: list[str] = Field(default_factory=list)
    severity: Literal["NONE", "REVIEW", "CRITICAL"] = "NONE"


class BudgetCheckResult(BaseModel):
    passed: bool
    reason: str
    retry_loop_detected: bool = False
    remaining_allowance_inr: float


class CaMeLProvenanceResult(BaseModel):
    privileged_mandate_id: str
    tainted_inputs: list[str] = Field(default_factory=list)
    capability_checks: dict[str, bool] = Field(default_factory=dict)
    violations: list[str] = Field(default_factory=list)
    control_data_isolated: bool = True


class VirtualCard(BaseModel):
    card_id: str
    agent_id: str
    pan: str
    pan_masked: str
    cvv: str
    exp_month: str
    exp_year: str
    merchant_name: str
    merchant_mcc: str
    exact_amount_inr: float
    status: CardStatus
    scope_hmac: str
    payment_mandate_id: str
    created_at: str
    expires_at: str
    settled_at: str | None = None


class PasskeyChallenge(BaseModel):
    challenge_id: str
    agent_id: str
    spend_request: SpendRequest
    reason: str
    hidden_liability_inr: float
    status: PasskeyStatus
    created_at: str
    resolved_at: str | None = None


class A2AMessage(BaseModel):
    trace_id: str
    from_agent: str
    to_agent: str
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0
    timestamp: str


class EvaluationResponse(BaseModel):
    trace_id: str
    decision: DecisionKind
    summary: str
    model_used: str
    routing_reason: str
    latency_ms: float
    ap2_verified: bool
    attriguard: AttriGuardResult
    fineprint: FinePrintResult
    budget: BudgetCheckResult
    camel_provenance: CaMeLProvenanceResult | None = None
    virtual_card: VirtualCard | None = None
    cart_mandate: CartMandate | None = None
    payment_mandate: PaymentMandate | None = None
    passkey_challenge: PasskeyChallenge | None = None
    a2a_trace: list[A2AMessage] = Field(default_factory=list)
    legacy_static_card_verdict: str


class MerchantChargeRequest(BaseModel):
    merchant_name: str
    merchant_mcc: str
    amount_inr: float = Field(gt=0)


class MerchantChargeResponse(BaseModel):
    approved: bool
    reason_code: str
    message: str
    card_status: CardStatus
    vault_balance_inr: float


class PasskeyResolveRequest(BaseModel):
    action: Literal["approve", "deny"]


class AuditEvent(BaseModel):
    event_id: str
    trace_id: str
    agent_id: str
    event_type: str
    decision: str
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class BenchmarkSummary(BaseModel):
    total_cases: int
    sublimit_injections_total: int
    sublimit_injections_blocked: int
    injection_block_rate_pct: float
    static_card_block_rate_pct: float
    fineprint_traps_caught: int
    fineprint_traps_total: int
    spoofed_domains_blocked: int
    spoofed_domains_total: int
    retry_loops_blocked: int
    retry_loops_total: int
    legit_false_positives: int
    legit_total: int
    post_settlement_bleed_inr: float
    p50_latency_ms: float
    p95_latency_ms: float
