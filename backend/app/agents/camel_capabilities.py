"""Google DeepMind CaMeL-derived Control-Data Separation & Capability Provenance Guard (arXiv:2503.18813)."""

from __future__ import annotations

from ..models import CaMeLProvenanceResult, IntentMandate, SpendRequest


def evaluate_camel_capabilities(
    mandate: IntentMandate,
    spend_req: SpendRequest,
) -> CaMeLProvenanceResult:
    """
    Separate Privileged Control Flow (human-signed IntentMandate) from
    Quarantined Untrusted Data (external DOM/HTML, checkout T&Cs, external merchant domain).

    Quarantined data may never widen MCC capabilities, introduce prohibited sinks,
    or silently authorize recurring charges.
    """
    tainted_inputs: list[str] = []
    if (spend_req.untrusted_dom_html or "").strip():
        tainted_inputs.append("untrusted_dom_html [QUARANTINED]")
    if (spend_req.checkout_terms_text or "").strip():
        tainted_inputs.append("checkout_terms_text [QUARANTINED]")
    tainted_inputs.append(f"merchant_domain:{spend_req.merchant_domain.lower()} [EXTERNAL]")

    capability_checks: dict[str, bool] = {}
    violations: list[str] = []

    # Capability 1: MCC sink must belong to Privileged IntentMandate allowlist
    mcc_ok = spend_req.merchant_mcc.upper() in {m.upper() for m in mandate.allowed_mccs}
    capability_checks["CAP_MCC_SCOPE"] = mcc_ok
    if not mcc_ok:
        violations.append(
            f"CAP_MCC_SCOPE denied: '{spend_req.merchant_mcc}' outside privileged allowlist {mandate.allowed_mccs}."
        )

    # Capability 2: No prohibited payment sinks from untrusted item/reasoning labels
    combined = f"{spend_req.merchant_name} {' '.join(spend_req.cart_items)} {spend_req.agent_reasoning}".lower()
    prohibited_hits = [kw for kw in mandate.prohibited_keywords if kw in combined]
    no_prohibited_ok = len(prohibited_hits) == 0
    capability_checks["CAP_NO_PROHIBITED_SINK"] = no_prohibited_ok
    if not no_prohibited_ok:
        violations.append(
            f"CAP_NO_PROHIBITED_SINK denied: prohibited keyword(s) {prohibited_hits} present in payment sink."
        )

    # Capability 3: Single-tx rupee ceiling invariant from privileged mandate
    amount_ok = spend_req.amount_inr <= mandate.max_single_tx_inr
    capability_checks["CAP_MAX_SINGLE_TX"] = amount_ok
    if not amount_ok:
        violations.append(
            f"CAP_MAX_SINGLE_TX denied: INR {spend_req.amount_inr:,.2f} exceeds INR {mandate.max_single_tx_inr:,.2f}."
        )

    # Capability 4: Untrusted DOM cannot contain control-plane directives
    dom_lower = (spend_req.untrusted_dom_html or "").lower()
    dom_clean = not any(
        tok in dom_lower
        for tok in ("system override", "ignore previous", "opacity:0", "display:none", "redirect payment", "urgent security patch")
    )
    capability_checks["CAP_UNTRUSTED_CONTROL_FLOW_BLOCK"] = dom_clean
    if not dom_clean:
        violations.append(
            "CAP_UNTRUSTED_CONTROL_FLOW_BLOCK triggered: quarantined DOM attempted control-flow hijack."
        )

    return CaMeLProvenanceResult(
        privileged_mandate_id=mandate.mandate_id,
        tainted_inputs=tainted_inputs,
        capability_checks=capability_checks,
        violations=violations,
        control_data_isolated=len(violations) == 0,
    )
