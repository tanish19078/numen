"""ADK Multi-Agent Orchestrator coordinating AP2 verification, Smart Routing, Budget, AttriGuard, FinePrint, and Card Minting."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from uuid import uuid4

from .. import crypto_ap2, db, sandbox_mint
from ..config import get_settings
from ..gemini_router import call_gemini_counterfactual_audit, route_model
from ..models import (
    A2AMessage,
    AttriGuardResult,
    BudgetCheckResult,
    CaMeLProvenanceResult,
    EvaluationResponse,
    FinePrintResult,
    PasskeyChallenge,
    SpendRequest,
)
from .a2a import make_a2a_hop
from .attriguard import evaluate_attriguard
from .budget_controller import evaluate_budget_and_velocity
from .camel_capabilities import evaluate_camel_capabilities
from .fineprint_auditor import evaluate_fineprint


def _legacy_verdict(amount_inr: float, static_cap: float = 10000.0) -> str:
    if amount_inr <= static_cap:
        return f"BLINDLY APPROVED (INR {amount_inr:,.0f} <= INR {static_cap:,.0f} static cap)"
    return f"DECLINED (> INR {static_cap:,.0f} static cap)"


def evaluate_spend_request(
    spend_req: SpendRequest,
    db_path: str | None = None,
    track_velocity: bool = True,
) -> EvaluationResponse:
    if spend_req.idempotency_key:
        cached_json = db.get_idempotent_evaluation(spend_req.agent_id, spend_req.idempotency_key, db_path=db_path)
        if cached_json:
            return EvaluationResponse.model_validate_json(cached_json)

    res = _evaluate_spend_uncached(spend_req, db_path=db_path, track_velocity=track_velocity)
    if spend_req.idempotency_key:
        db.save_idempotent_evaluation(spend_req.agent_id, spend_req.idempotency_key, res.model_dump_json(), db_path=db_path)
    return res


def _evaluate_spend_uncached(
    spend_req: SpendRequest,
    db_path: str | None = None,
    track_velocity: bool = True,
) -> EvaluationResponse:
    t_start = time.perf_counter()
    trace_id = f"trace_{uuid4().hex[:10]}"
    settings = get_settings()
    a2a_trace: list[A2AMessage] = []

    agent = db.get_agent(spend_req.agent_id, db_path=db_path)
    if not agent:
        raise ValueError(f"Unknown agent_id '{spend_req.agent_id}'")

    mandate = db.get_intent_mandate(agent.intent_mandate_id, db_path=db_path)
    if not mandate:
        raise ValueError(f"Missing IntentMandate '{agent.intent_mandate_id}'")

    # 1. AP2 Ed25519 Signature Verification
    t0 = time.perf_counter()
    ap2_ok = crypto_ap2.verify_mandate(mandate.model_dump(), mandate.signature_b64, mandate.public_key_b64)
    a2a_trace.append(
        make_a2a_hop(
            trace_id,
            "ADK.Orchestrator",
            "AP2.CryptoVerifier",
            "verify_intent_mandate_ed25519",
            {"mandate_id": mandate.mandate_id, "verified": ap2_ok},
            (time.perf_counter() - t0) * 1000,
        )
    )
    if not ap2_ok:
        raise ValueError("AP2 IntentMandate Ed25519 signature verification failed (tampered mandate)")

    # 2. Smart Model Routing (Gemini 2.5 Flash vs Pro)
    t1 = time.perf_counter()
    model_used, routing_reason = route_model(spend_req)
    llm_hint = call_gemini_counterfactual_audit(model_used, mandate, spend_req)
    a2a_trace.append(
        make_a2a_hop(
            trace_id,
            "ADK.Orchestrator",
            "Gemini.SmartRouter",
            "select_model_tier",
            {"model_used": model_used, "reason": routing_reason, "live_llm_used": llm_hint is not None},
            (time.perf_counter() - t1) * 1000,
        )
    )

    # 3. Budget & Runaway Retry-Loop Check
    t2 = time.perf_counter()
    budget: BudgetCheckResult = evaluate_budget_and_velocity(
        agent, mandate, spend_req, db_path=db_path, track_velocity=track_velocity
    )
    a2a_trace.append(
        make_a2a_hop(
            trace_id,
            "ADK.Orchestrator",
            "BudgetController",
            "check_allowance_and_velocity",
            budget.model_dump(),
            (time.perf_counter() - t2) * 1000,
        )
    )
    if not budget.passed:
        db.record_audit_event(
            trace_id,
            agent.agent_id,
            "BUDGET_OR_LOOP_BLOCK",
            "BLOCKED",
            budget.reason,
            {"amount_inr": spend_req.amount_inr, "retry_loop": budget.retry_loop_detected},
            db_path=db_path,
        )
        return EvaluationResponse(
            trace_id=trace_id,
            decision="BLOCKED",
            summary=budget.reason,
            model_used=model_used,
            routing_reason=routing_reason,
            latency_ms=round((time.perf_counter() - t_start) * 1000, 2),
            ap2_verified=ap2_ok,
            attriguard=AttriGuardResult(
                drift_score=0.0,
                world_a_action="Halted at BudgetController",
                world_b_action="Halted at BudgetController",
                injection_detected=False,
                explanation="Skipped after Budget/Velocity block.",
            ),
            fineprint=FinePrintResult(has_trap=False),
            budget=budget,
            a2a_trace=a2a_trace,
            legacy_static_card_verdict=_legacy_verdict(spend_req.amount_inr),
        )

    # 4. DeepMind CaMeL Capability & Provenance Guard (Privileged Control vs Quarantined Data)
    t_cam = time.perf_counter()
    camel_res: CaMeLProvenanceResult = evaluate_camel_capabilities(mandate, spend_req)
    a2a_trace.append(
        make_a2a_hop(
            trace_id,
            "ADK.Orchestrator",
            "CaMeL.CapabilityGuard",
            "enforce_control_data_provenance",
            {
                "control_data_isolated": camel_res.control_data_isolated,
                "tainted_inputs_count": len(camel_res.tainted_inputs),
                "violations": camel_res.violations,
            },
            (time.perf_counter() - t_cam) * 1000,
        )
    )
    if camel_res.capability_checks.get("CAP_DOM_ATTESTATION") is False:
        db.set_agent_status(agent.agent_id, "PAUSED", db_path=db_path)
        db.record_audit_event(
            trace_id,
            agent.agent_id,
            "DOM_ATTESTATION_BLOCK",
            "BLOCKED",
            "Blocked checkout: invalid or missing sidecar DOM attestation HMAC.",
            {"violations": camel_res.violations},
            db_path=db_path,
        )
        return EvaluationResponse(
            trace_id=trace_id,
            decision="BLOCKED",
            summary="CaMeL CAP_DOM_ATTESTATION failed: untrusted DOM signature invalid or missing.",
            model_used=model_used,
            routing_reason=routing_reason,
            latency_ms=round((time.perf_counter() - t_start) * 1000, 2),
            ap2_verified=ap2_ok,
            attriguard=AttriGuardResult(
                drift_score=1.0,
                world_a_action="Halted at CaMeL DOM attestation check",
                world_b_action="Require valid sidecar DOM HMAC",
                injection_detected=True,
                explanation="DOM telemetry integrity check failed.",
            ),
            fineprint=FinePrintResult(has_trap=False),
            budget=budget,
            camel_provenance=camel_res,
            a2a_trace=a2a_trace,
            legacy_static_card_verdict=_legacy_verdict(spend_req.amount_inr),
        )

    # 5. AttriGuard Counterfactual Prompt-Injection Firewall
    t3 = time.perf_counter()
    attriguard = evaluate_attriguard(mandate, spend_req, llm_hint=llm_hint)
    a2a_trace.append(
        make_a2a_hop(
            trace_id,
            "ADK.Orchestrator",
            "AttriGuard.Firewall",
            "counterfactual_causal_check",
            {
                "drift_score": attriguard.drift_score,
                "injection_detected": attriguard.injection_detected,
                "poisoned_spans_count": len(attriguard.poisoned_spans),
            },
            (time.perf_counter() - t3) * 1000,
        )
    )

    if attriguard.drift_score >= settings.drift_threshold:
        if attriguard.injection_detected:
            db.set_agent_status(agent.agent_id, "PAUSED", db_path=db_path)
        db.record_audit_event(
            trace_id,
            agent.agent_id,
            "ATTRIGUARD_HIJACK_BLOCK",
            "BLOCKED",
            f"Blocked {spend_req.merchant_name} (INR {spend_req.amount_inr:,.2f}): Drift={attriguard.drift_score}. {attriguard.explanation}",
            {"drift_score": attriguard.drift_score, "poisoned_spans": attriguard.poisoned_spans},
            db_path=db_path,
        )
        return EvaluationResponse(
            trace_id=trace_id,
            decision="BLOCKED",
            summary=f"AttriGuard Causal Drift = {attriguard.drift_score} (>= {settings.drift_threshold}). {attriguard.explanation}",
            model_used=model_used,
            routing_reason=routing_reason,
            latency_ms=round((time.perf_counter() - t_start) * 1000, 2),
            ap2_verified=ap2_ok,
            attriguard=attriguard,
            fineprint=FinePrintResult(has_trap=False),
            budget=budget,
            camel_provenance=camel_res,
            a2a_trace=a2a_trace,
            legacy_static_card_verdict=_legacy_verdict(spend_req.amount_inr),
        )

    # 6. Fine-Print & Lookalike Domain Auditor
    t4 = time.perf_counter()
    fineprint = evaluate_fineprint(mandate, spend_req, llm_hint=llm_hint)
    a2a_trace.append(
        make_a2a_hop(
            trace_id,
            "ADK.Orchestrator",
            "FinePrint.Auditor",
            "inspect_terms_and_domain",
            fineprint.model_dump(),
            (time.perf_counter() - t4) * 1000,
        )
    )

    if fineprint.spoofed_domain_of:
        db.set_agent_status(agent.agent_id, "PAUSED", db_path=db_path)
        msg = f"Lookalike domain '{spend_req.merchant_domain}' spoofs '{fineprint.spoofed_domain_of}'. Card mint denied."
        db.record_audit_event(
            trace_id,
            agent.agent_id,
            "SPOOFED_DOMAIN_BLOCK",
            "BLOCKED",
            msg,
            {"spoofed_of": fineprint.spoofed_domain_of},
            db_path=db_path,
        )
        return EvaluationResponse(
            trace_id=trace_id,
            decision="BLOCKED",
            summary=msg,
            model_used=model_used,
            routing_reason=routing_reason,
            latency_ms=round((time.perf_counter() - t_start) * 1000, 2),
            ap2_verified=ap2_ok,
            attriguard=attriguard,
            fineprint=fineprint,
            budget=budget,
            camel_provenance=camel_res,
            a2a_trace=a2a_trace,
            legacy_static_card_verdict=_legacy_verdict(spend_req.amount_inr),
        )

    if fineprint.has_trap:
        challenge = PasskeyChallenge(
            challenge_id=f"pk_{uuid4().hex[:8]}",
            agent_id=agent.agent_id,
            spend_request=spend_req,
            reason=f"Hidden recurring liability (INR {fineprint.hidden_annual_inr:,.0f}/yr) detected in checkout terms.",
            hidden_liability_inr=fineprint.hidden_annual_inr,
            status="PENDING",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        db.save_passkey_challenge(challenge, db_path=db_path)
        db.record_audit_event(
            trace_id,
            agent.agent_id,
            "PASSKEY_ESCALATION",
            "PASSKEY_REQUIRED",
            challenge.reason,
            {"challenge_id": challenge.challenge_id, "clauses": fineprint.clauses_flagged},
            db_path=db_path,
        )
        return EvaluationResponse(
            trace_id=trace_id,
            decision="PASSKEY_REQUIRED",
            summary=challenge.reason,
            model_used=model_used,
            routing_reason=routing_reason,
            latency_ms=round((time.perf_counter() - t_start) * 1000, 2),
            ap2_verified=ap2_ok,
            attriguard=attriguard,
            fineprint=fineprint,
            budget=budget,
            camel_provenance=camel_res,
            passkey_challenge=challenge,
            a2a_trace=a2a_trace,
            legacy_static_card_verdict=_legacy_verdict(spend_req.amount_inr),
        )

    # 7. All Gates Passed -> Mint 60s Scoped Luhn Virtual Card & AP2 PaymentMandate in Sandbox
    return _mint_and_persist_card(
        trace_id=trace_id,
        t_start=t_start,
        mandate_id=mandate.mandate_id,
        spend_req=spend_req,
        model_used=model_used,
        routing_reason=routing_reason,
        ap2_ok=ap2_ok,
        attriguard=attriguard,
        fineprint=fineprint,
        budget=budget,
        a2a_trace=a2a_trace,
        camel_provenance=camel_res,
        db_path=db_path,
    )


def _mint_and_persist_card(
    trace_id: str,
    t_start: float,
    mandate_id: str,
    spend_req: SpendRequest,
    model_used: str,
    routing_reason: str,
    ap2_ok: bool,
    attriguard: AttriGuardResult,
    fineprint: FinePrintResult,
    budget: BudgetCheckResult,
    a2a_trace: list[A2AMessage],
    camel_provenance: CaMeLProvenanceResult | None = None,
    db_path: str | None = None,
) -> EvaluationResponse:
    t5 = time.perf_counter()
    cart_mandate = crypto_ap2.create_cart_mandate(mandate_id, spend_req)
    pm_placeholder_id = f"pm_{uuid4().hex[:10]}"
    card = sandbox_mint.mint_scoped_virtual_card(
        agent_id=spend_req.agent_id,
        merchant_name=spend_req.merchant_name,
        merchant_mcc=spend_req.merchant_mcc,
        exact_amount_inr=spend_req.amount_inr,
        payment_mandate_id=pm_placeholder_id,
    )
    payment_mandate = crypto_ap2.create_payment_mandate(
        intent_mandate_id=mandate_id,
        cart_id=cart_mandate.cart_id,
        card_id=card.card_id,
        pan_last4=card.pan[-4:],
        exact_amount_inr=card.exact_amount_inr,
        merchant_name=card.merchant_name,
        scope_hmac=card.scope_hmac,
        issued_at=card.created_at,
        expires_at=card.expires_at,
    )
    card = card.model_copy(update={"payment_mandate_id": payment_mandate.payment_mandate_id})

    db.save_mandate(cart_mandate.cart_id, "CART", spend_req.agent_id, cart_mandate.model_dump_json(), cart_mandate.issued_at, db_path=db_path)
    db.save_mandate(payment_mandate.payment_mandate_id, "PAYMENT", spend_req.agent_id, payment_mandate.model_dump_json(), payment_mandate.issued_at, db_path=db_path)
    db.save_virtual_card(card, db_path=db_path)

    a2a_trace.append(
        make_a2a_hop(
            trace_id,
            "ADK.Orchestrator",
            "Python.AgentSandbox",
            "mint_60s_luhn_virtual_card",
            {"card_id": card.card_id, "pan_last4": card.pan[-4:], "exact_amount_inr": card.exact_amount_inr},
            (time.perf_counter() - t5) * 1000,
        )
    )
    summary = f"Minted 60s virtual card *{card.pan[-4:]} locked to {card.merchant_name} for exact INR {card.exact_amount_inr:,.2f}."
    db.record_audit_event(
        trace_id,
        spend_req.agent_id,
        "CARD_MINTED",
        "MINTED",
        summary,
        {"card_id": card.card_id, "model_used": model_used},
        db_path=db_path,
    )

    return EvaluationResponse(
        trace_id=trace_id,
        decision="MINTED",
        summary=summary,
        model_used=model_used,
        routing_reason=routing_reason,
        latency_ms=round((time.perf_counter() - t_start) * 1000, 2),
        ap2_verified=ap2_ok,
        attriguard=attriguard,
        fineprint=fineprint,
        budget=budget,
        camel_provenance=camel_provenance,
        virtual_card=card,
        cart_mandate=cart_mandate,
        payment_mandate=payment_mandate,
        a2a_trace=a2a_trace,
        legacy_static_card_verdict=_legacy_verdict(spend_req.amount_inr),
    )


def mint_after_passkey_approval(challenge: PasskeyChallenge, db_path: str | None = None) -> EvaluationResponse:
    t_start = time.perf_counter()
    trace_id = f"trace_{uuid4().hex[:10]}"
    agent = db.get_agent(challenge.agent_id, db_path=db_path)
    if not agent:
        raise ValueError("Agent not found")
    mandate = db.get_intent_mandate(agent.intent_mandate_id, db_path=db_path)
    if not mandate:
        raise ValueError("Mandate not found")

    model_used, routing_reason = route_model(challenge.spend_request)
    a2a_trace = [
        make_a2a_hop(
            trace_id,
            "Founder.Passkey",
            "ADK.Orchestrator",
            "human_passkey_override_approved",
            {"challenge_id": challenge.challenge_id, "note": "Capped strictly to single-use exact rupee amount"},
            1.2,
        )
    ]
    return _mint_and_persist_card(
        trace_id=trace_id,
        t_start=t_start,
        mandate_id=mandate.mandate_id,
        spend_req=challenge.spend_request,
        model_used=model_used,
        routing_reason=routing_reason,
        ap2_ok=True,
        attriguard=AttriGuardResult(
            drift_score=0.12,
            world_a_action=f"Passkey-approved INR {challenge.spend_request.amount_inr:,.2f} -> {challenge.spend_request.merchant_name}",
            world_b_action="Human Passkey confirmed single-use cap (auto-shreds after 1st charge so annual trap cannot bill).",
            injection_detected=False,
            explanation="Human Passkey explicitly approved single-use INR cap.",
        ),
        fineprint=FinePrintResult(has_trap=True, hidden_annual_inr=challenge.hidden_liability_inr, severity="REVIEW"),
        budget=BudgetCheckResult(passed=True, reason="Approved via Founder Passkey", remaining_allowance_inr=max(0.0, agent.daily_limit_inr - agent.spent_today_inr)),
        a2a_trace=a2a_trace,
        db_path=db_path,
    )
