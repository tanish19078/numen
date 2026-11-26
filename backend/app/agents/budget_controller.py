"""Budget, MCC Allowlist, and 60-Second Runaway Retry-Loop Velocity Circuit Breaker."""

from __future__ import annotations

from .. import db
from ..models import AgentAccount, BudgetCheckResult, IntentMandate, SpendRequest


def evaluate_budget_and_velocity(
    agent: AgentAccount,
    mandate: IntentMandate,
    spend_req: SpendRequest,
    db_path: str | None = None,
    track_velocity: bool = True,
) -> BudgetCheckResult:
    remaining = round(max(0.0, agent.daily_limit_inr - agent.spent_today_inr), 2)

    if agent.status != "ACTIVE":
        return BudgetCheckResult(
            passed=False,
            reason=f"Agent '{agent.name}' is currently PAUSED pending security review.",
            retry_loop_detected=False,
            remaining_allowance_inr=remaining,
        )

    if track_velocity:
        dup_count = db.record_spend_attempt_for_loop_check(
            agent_id=agent.agent_id,
            merchant_name=spend_req.merchant_name,
            amount_inr=spend_req.amount_inr,
            db_path=db_path,
        )
        if dup_count >= 3:
            db.set_agent_status(agent.agent_id, "PAUSED", db_path=db_path)
            return BudgetCheckResult(
                passed=False,
                reason=f"RETRY_LOOP_DETECTED: {dup_count} identical requests to '{spend_req.merchant_name}' for INR {spend_req.amount_inr:,.2f} within 60s; agent auto-paused.",
                retry_loop_detected=True,
                remaining_allowance_inr=remaining,
            )

    if spend_req.amount_inr > mandate.max_single_tx_inr:
        return BudgetCheckResult(
            passed=False,
            reason=f"Requested INR {spend_req.amount_inr:,.2f} exceeds signed single-tx cap INR {mandate.max_single_tx_inr:,.2f}.",
            retry_loop_detected=False,
            remaining_allowance_inr=remaining,
        )

    if spend_req.amount_inr > remaining:
        return BudgetCheckResult(
            passed=False,
            reason=f"Requested INR {spend_req.amount_inr:,.2f} exceeds remaining daily allowance INR {remaining:,.2f}.",
            retry_loop_detected=False,
            remaining_allowance_inr=remaining,
        )

    return BudgetCheckResult(
        passed=True,
        reason=f"Allowance verified (INR {remaining:,.2f} available; no retry loop).",
        retry_loop_detected=False,
        remaining_allowance_inr=remaining,
    )
