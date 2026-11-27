"""FastAPI application entrypoint for Numen — REST API, SSE stream, MCP server, and SPA host."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import crypto_ap2, db, sandbox_mint
from .agents.a2a import broadcaster
from .agents.orchestrator import evaluate_spend_request, mint_after_passkey_approval
from .config import get_settings
from .models import (
    CreateIntentMandateRequest,
    MerchantChargeRequest,
    MerchantChargeResponse,
    PasskeyResolveRequest,
    SpendRequest,
)
from .scenarios import DEMO_SCENARIOS, run_240_benchmarks
from .issuers.stripe_jit import StripeIssuingJITAdapter
from .mcp_server import handle_mcp_rpc


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_and_seed_db()
    yield


app = FastAPI(
    title="Numen — AP2-Native Neobank & Spend Firewall for AI Agents",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/.well-known/agent.json")
def agent_card() -> dict[str, Any]:
    """A2A Protocol discovery card describing Numen capabilities, protocols, and MCP/REST endpoints."""
    return {
        "name": "Numen",
        "description": (
            "AP2-native agentic neobank and pre-spend causal firewall. Verifies Ed25519 mandates, "
            "CaMeL provenance, AttriGuard counterfactual drift, and checkout terms before minting 60s exact-rupee virtual cards."
        ),
        "version": "1.0.0",
        "architecture": "3-Cluster Agentic Quorum (Edge -> Verification Quorum -> Zero-LLM Custody)",
        "protocols": ["A2A/0.2", "MCP/2025-03-26", "AP2/Ed25519"],
        "clusters": [
            {
                "id": "edge_commerce_cluster",
                "name": "Cluster 1 · Edge Commerce Agents",
                "role": "Untrusted agent workloads (DevOps, Procurement, Research, Claude/Cursor) requesting scoped spend via MCP",
            },
            {
                "id": "verification_quorum_cluster",
                "name": "Cluster 2 · Verification & Consensus Quorum",
                "role": "Gemini 2.5 Flash/Pro Smart Router coordinating 4 specialist voters: Budget/Loop, CaMeL, AttriGuard, FinePrint",
            },
            {
                "id": "deterministic_custody_cluster",
                "name": "Cluster 3 · Zero-LLM Deterministic Custody",
                "role": "Ed25519 AP2 Signer, 60s exact-rupee Luhn PAN Minter (+0.00 INR lock), Auto-Shredder & SQLite WAL",
            },
        ],
        "capabilities": {
            "streaming": True,
            "ephemeral_cards": True,
            "passkey_hitl": True,
        },
        "endpoints": {
            "mcp": "/mcp",
            "evaluate": "/api/spend/evaluate",
            "charge": "/api/cards/{card_id}/charge",
            "stream": "/api/stream",
            "health": "/api/health",
        },
        "skills": [
            {
                "id": "request_scoped_card",
                "name": "Request 60s Scoped Virtual Card",
                "description": "Evaluate spend causal intent and mint an exact-rupee single-use Luhn virtual card.",
            },
            {
                "id": "get_agent_allowance",
                "name": "Inspect Agent Sub-Account & Mandate",
                "description": "Return daily budget allowance, MCC allowlist, and Ed25519 IntentMandate.",
            },
            {
                "id": "settle_ephemeral_card",
                "name": "Settle Ephemeral Card",
                "description": "Validate merchant, MCC, and exact rupee tolerance (+/- 0.00 INR) then auto-shred.",
            },
        ],
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    s = get_settings()
    return {
        "status": "ok",
        "service": "numen-ap2-neobank",
        "gemini_mode": "live_gemini" if s.gemini_api_key else "deterministic_offline",
        "flash_model": s.gemini_flash_model,
        "pro_model": s.gemini_pro_model,
        "card_ttl_seconds": s.card_ttl_seconds,
        "drift_threshold": s.drift_threshold,
    }


@app.get("/api/state")
def get_state() -> dict[str, Any]:
    return {
        "vault": db.get_vault().model_dump(),
        "agents": [a.model_dump() for a in db.list_agents()],
        "mandates": db.list_mandates(),
        "cards": [c.model_dump() for c in db.list_virtual_cards()],
        "passkeys": [p.model_dump() for p in db.list_passkeys()],
        "audit_events": [e.model_dump() for e in db.list_audit_events()],
    }


@app.post("/api/reset")
def reset_state() -> dict[str, Any]:
    db.reset_demo_state()
    broadcaster.publish_sync({"type": "state_reset", "data": {"message": "Demo treasury reset cleanly"}})
    return get_state()


@app.get("/api/scenarios")
def list_scenarios() -> dict[str, Any]:
    return {"scenarios": DEMO_SCENARIOS}


@app.post("/api/agents/{agent_id}/toggle-status")
def toggle_agent_status(agent_id: str) -> dict[str, Any]:
    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    next_status = "PAUSED" if agent.status == "ACTIVE" else "ACTIVE"
    updated = db.set_agent_status(agent_id, next_status)
    db.record_audit_event(
        trace_id="trace_manual",
        agent_id=agent_id,
        event_type="AGENT_STATUS_TOGGLED",
        decision=next_status,
        summary=f"Treasury owner switched {agent.name} status to {next_status}.",
    )
    return {"agent": updated.model_dump() if updated else None}


@app.post("/api/mandates")
def create_mandate(req: CreateIntentMandateRequest) -> dict[str, Any]:
    agent = db.get_agent(req.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{req.agent_id}' not found")
    mandate = crypto_ap2.create_intent_mandate(
        agent_id=req.agent_id,
        natural_language_intent=req.natural_language_intent,
        max_daily_inr=req.max_daily_inr,
        max_single_tx_inr=req.max_single_tx_inr,
        allowed_mccs=req.allowed_mccs,
        prohibited_keywords=req.prohibited_keywords,
        allow_recurring=req.allow_recurring,
    )
    db.update_agent_intent_mandate(mandate)
    db.record_audit_event(
        trace_id="trace_mandate",
        agent_id=req.agent_id,
        event_type="INTENT_MANDATE_SIGNED",
        decision="SIGNED",
        summary=f"Signed new Ed25519 IntentMandate {mandate.mandate_id} (cap INR {mandate.max_daily_inr:,.0f}/day).",
    )
    return {"mandate": mandate.model_dump()}


@app.post("/api/mandates/{mandate_id}/verify-tamper")
def verify_mandate_tamper(mandate_id: str) -> dict[str, Any]:
    """Demonstrate Ed25519 cryptographic integrity: original passes, 1-rupee tamper fails."""
    mandate = db.get_intent_mandate(mandate_id)
    if not mandate:
        raise HTTPException(status_code=404, detail=f"IntentMandate '{mandate_id}' not found")
    orig_dict = mandate.model_dump()
    original_valid = crypto_ap2.verify_mandate(orig_dict, mandate.signature_b64, mandate.public_key_b64)
    tampered_dict = mandate.model_copy(update={"max_daily_inr": mandate.max_daily_inr + 1.0}).model_dump()
    tampered_valid = crypto_ap2.verify_mandate(tampered_dict, mandate.signature_b64, mandate.public_key_b64)
    return {
        "mandate_id": mandate_id,
        "original_valid": original_valid,
        "tampered_valid": tampered_valid,
        "canonical_hash": mandate.canonical_hash,
        "algorithm": "Ed25519 + SHA-256",
    }


@app.post("/api/mandates/verify-chain/{payment_mandate_id}")
def verify_full_ap2_chain(payment_mandate_id: str) -> dict[str, Any]:
    """Verify the entire 3-link AP2 chain: IntentMandate -> CartMandate -> PaymentMandate."""
    payment = db.get_payment_mandate(payment_mandate_id)
    if not payment:
        raise HTTPException(status_code=404, detail=f"PaymentMandate '{payment_mandate_id}' not found")
    cart = db.get_cart_mandate(payment.cart_id)
    intent = db.get_intent_mandate(payment.intent_mandate_id)
    if not cart or not intent:
        raise HTTPException(status_code=404, detail="Incomplete AP2 chain (missing Intent or Cart mandate)")
    ok, errors = crypto_ap2.verify_ap2_chain(intent, cart, payment)
    return {
        "valid": ok,
        "errors": errors,
        "intent_mandate_id": intent.mandate_id,
        "cart_id": cart.cart_id,
        "payment_mandate_id": payment.payment_mandate_id,
        "signer_key_id": crypto_ap2.get_default_signer().key_id(),
    }


@app.post("/api/spend/evaluate")
def evaluate_spend(req: SpendRequest) -> dict[str, Any]:
    try:
        res = evaluate_spend_request(req)
        return res.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/cards/{card_id}/charge", response_model=MerchantChargeResponse)
def charge_card(card_id: str, req: MerchantChargeRequest) -> MerchantChargeResponse:
    card = db.get_virtual_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"Virtual card '{card_id}' not found")

    ok, code, msg, updated = sandbox_mint.validate_and_settle_charge(
        card=card,
        merchant_name=req.merchant_name,
        merchant_mcc=req.merchant_mcc,
        charge_amount_inr=req.amount_inr,
    )
    if ok:
        settled_ok, cas_code, vault = db.settle_card_atomic(updated, req.amount_inr)
        if not settled_ok or vault is None:
            ok = False
            code = cas_code
            msg = "Concurrent settlement rejected: card was already settled or vault lacks funds."
            vault_bal = db.get_vault().balance_inr
        else:
            vault_bal = vault.balance_inr
    else:
        vault_bal = db.get_vault().balance_inr

    db.record_audit_event(
        trace_id=f"charge_{card_id}",
        agent_id=card.agent_id,
        event_type="MERCHANT_CHARGE",
        decision="SETTLED" if ok else "DECLINED",
        summary=f"[{code}] {msg}",
        metadata={"card_id": card_id, "amount_inr": req.amount_inr},
    )
    broadcaster.publish_sync(
        {
            "type": "merchant_charge",
            "data": {"card_id": card_id, "approved": ok, "reason_code": code, "message": msg, "card_status": updated.status},
        }
    )
    return MerchantChargeResponse(
        approved=ok,
        reason_code=code,
        message=msg,
        card_status=updated.status,
        vault_balance_inr=vault_bal,
    )


@app.post("/api/passkeys/{challenge_id}/resolve")
def resolve_passkey(challenge_id: str, req: PasskeyResolveRequest) -> dict[str, Any]:
    challenge = db.get_passkey_challenge(challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail=f"Passkey challenge '{challenge_id}' not found")
    if challenge.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Challenge already resolved as {challenge.status}")

    now_iso = datetime.now(timezone.utc).isoformat()
    if req.action == "deny":
        updated = challenge.model_copy(update={"status": "DENIED", "resolved_at": now_iso})
        db.save_passkey_challenge(updated)
        db.record_audit_event(
            trace_id=f"pk_{challenge_id}",
            agent_id=challenge.agent_id,
            event_type="PASSKEY_DENIED",
            decision="BLOCKED",
            summary=f"Founder denied passkey challenge {challenge_id}; blocked INR {challenge.hidden_liability_inr:,.0f}/yr trap.",
        )
        return {"challenge": updated.model_dump(), "evaluation": None}

    updated = challenge.model_copy(update={"status": "APPROVED", "resolved_at": now_iso})
    db.save_passkey_challenge(updated)
    eval_res = mint_after_passkey_approval(updated)
    return {"challenge": updated.model_dump(), "evaluation": eval_res.model_dump()}


@app.post("/api/benchmarks/run")
def run_benchmarks() -> dict[str, Any]:
    summary = run_240_benchmarks()
    return summary.model_dump()


@app.get("/api/ledger/entries")
def get_ledger_entries(limit: int = 100) -> dict[str, Any]:
    return db.list_ledger_entries(limit=limit)


@app.get("/api/audit/verify-chain")
def verify_audit_chain() -> dict[str, Any]:
    return db.verify_audit_log_chain()


@app.post("/api/webhooks/stripe-issuing")
async def stripe_issuing_jit_webhook(request: Request):
    """Real-time Stripe Issuing JIT Authorization webhook enforcing ±₹0.00 / tolerance_bps & single-use shredding."""
    raw_body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    status_code, payload = StripeIssuingJITAdapter().handle_webhook(raw_body, sig_header)
    return JSONResponse(status_code=status_code, content=payload)


@app.get("/api/stream")
async def sse_stream(request: Request):
    queue = broadcaster.subscribe()

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'connected', 'data': {'status': 'streaming'}})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(item)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    body = await request.json()
    return JSONResponse(content=handle_mcp_rpc(body))


# Serve compiled React SPA from frontend/dist when present
_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _FRONTEND_DIST.exists() and (_FRONTEND_DIST / "index.html").exists():
    assets_dir = _FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend_assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        if full_path.startswith(("api/", "mcp")):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_FRONTEND_DIST / "index.html"))
