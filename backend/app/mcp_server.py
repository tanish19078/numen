"""Model Context Protocol (MCP) JSON-RPC 2.0 server exposing Numen payment tools."""

from __future__ import annotations

from typing import Any

from . import db, sandbox_mint
from .agents.orchestrator import evaluate_spend_request
from .models import SpendRequest

MCP_TOOLS = [
    {
        "name": "request_scoped_card",
        "description": (
            "Request a 60-second single-use virtual Visa card and signed AP2 PaymentMandate. "
            "Runs BudgetController, AttriGuard counterfactual prompt-injection check, and FinePrintAuditor."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "merchant_name": {"type": "string"},
                "merchant_domain": {"type": "string"},
                "merchant_mcc": {"type": "string"},
                "amount_inr": {"type": "number"},
                "cart_items": {"type": "array", "items": {"type": "string"}},
                "agent_reasoning": {"type": "string"},
                "untrusted_dom_html": {"type": "string"},
                "checkout_terms_text": {"type": "string"},
            },
            "required": ["agent_id", "merchant_name", "merchant_domain", "merchant_mcc", "amount_inr"],
        },
    },
    {
        "name": "get_agent_allowance",
        "description": "Retrieve live daily allowance, status, allowed MCCs, and signed AP2 IntentMandate for an AI agent.",
        "inputSchema": {
            "type": "object",
            "properties": {"agent_id": {"type": "string"}},
            "required": ["agent_id"],
        },
    },
    {
        "name": "settle_ephemeral_card",
        "description": "Attempt merchant settlement against an active 60-second scoped virtual card.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "card_id": {"type": "string"},
                "merchant_name": {"type": "string"},
                "merchant_mcc": {"type": "string"},
                "amount_inr": {"type": "number"},
            },
            "required": ["card_id", "merchant_name", "merchant_mcc", "amount_inr"],
        },
    },
]


def handle_mcp_rpc(payload: dict[str, Any], db_path: str | None = None) -> dict[str, Any]:
    req_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "serverInfo": {"name": "numen-ap2-neobank-mcp", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            },
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOLS}}

    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments") or {}

        try:
            if tool_name == "request_scoped_card":
                spend_req = SpendRequest(**args)
                eval_res = evaluate_spend_request(spend_req, db_path=db_path)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "isError": eval_res.decision == "BLOCKED",
                        "content": [{"type": "text", "text": eval_res.summary}],
                        "structuredContent": eval_res.model_dump(),
                    },
                }

            if tool_name == "get_agent_allowance":
                agent_id = args.get("agent_id", "")
                agent = db.get_agent(agent_id, db_path=db_path)
                if not agent:
                    raise ValueError(f"Unknown agent_id '{agent_id}'")
                mandate = db.get_intent_mandate(agent.intent_mandate_id, db_path=db_path)
                data = {
                    "agent": agent.model_dump(),
                    "remaining_daily_inr": round(max(0.0, agent.daily_limit_inr - agent.spent_today_inr), 2),
                    "intent_mandate": mandate.model_dump() if mandate else None,
                }
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "isError": False,
                        "content": [{"type": "text", "text": f"{agent.name} status={agent.status} remaining=INR {data['remaining_daily_inr']:,.2f}"}],
                        "structuredContent": data,
                    },
                }

            if tool_name == "settle_ephemeral_card":
                card_id = args.get("card_id", "")
                card = db.get_virtual_card(card_id, db_path=db_path)
                if not card:
                    raise ValueError(f"Unknown card_id '{card_id}'")
                ok, code, msg, updated = sandbox_mint.validate_and_settle_charge(
                    card=card,
                    merchant_name=args["merchant_name"],
                    merchant_mcc=args["merchant_mcc"],
                    charge_amount_inr=float(args["amount_inr"]),
                )
                if ok:
                    vault = db.record_settlement_and_debit(updated, float(args["amount_inr"]), db_path=db_path)
                    vault_bal = vault.balance_inr
                else:
                    vault_bal = db.get_vault(db_path=db_path).balance_inr
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "isError": not ok,
                        "content": [{"type": "text", "text": msg}],
                        "structuredContent": {
                            "approved": ok,
                            "reason_code": code,
                            "card_status": updated.status,
                            "vault_balance_inr": vault_bal,
                        },
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool '{tool_name}'"},
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": str(exc)},
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method '{method}' not supported"},
    }
