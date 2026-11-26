"""Gemini Enterprise Smart Model Router across Gemini 2.5 Flash and Gemini 2.5 Pro."""

from __future__ import annotations

import json
import logging
from typing import Any

from .config import get_settings
from .models import IntentMandate, SpendRequest

logger = logging.getLogger(__name__)

TRUSTED_FASTPATH_DOMAINS = {
    "runpod.io",
    "aws.amazon.com",
    "cloud.google.com",
    "huggingface.co",
    "openai.com",
    "anthropic.com",
    "stripe.com",
}


def route_model(spend_req: SpendRequest) -> tuple[str, str]:
    """
    Choose optimal Gemini Enterprise model:
    - Fast-path -> gemini-2.5-flash when domain is trusted, untrusted DOM is empty, and T&Cs are short.
    - Escalate -> gemini-2.5-pro whenever untrusted HTML/DOM is present, T&Cs exceed 120 chars, or domain is unfamiliar.
    """
    settings = get_settings()
    domain = spend_req.merchant_domain.strip().lower()
    has_untrusted_dom = bool((spend_req.untrusted_dom_html or "").strip())
    has_dense_terms = len((spend_req.checkout_terms_text or "").strip()) > 120

    if not has_untrusted_dom and not has_dense_terms and domain in TRUSTED_FASTPATH_DOMAINS:
        return (
            settings.gemini_flash_model,
            "Trusted infrastructure merchant with zero untrusted DOM; routed to low-latency Flash path.",
        )

    reasons = []
    if has_untrusted_dom:
        reasons.append("untrusted external DOM/HTML payload")
    if has_dense_terms:
        reasons.append("dense checkout terms (>120 chars)")
    if domain not in TRUSTED_FASTPATH_DOMAINS:
        reasons.append(f"unverified merchant domain '{domain}'")

    return (
        settings.gemini_pro_model,
        f"Escalated to Pro deep reasoning due to: {', '.join(reasons)}.",
    )


def call_gemini_counterfactual_audit(
    model_name: str,
    mandate: IntentMandate,
    spend_req: SpendRequest,
) -> dict[str, Any] | None:
    """
    Optional live Gemini 2.5 Flash/Pro structured verification via google-genai SDK.
    Returns None gracefully if GEMINI_API_KEY is unset or network is unavailable.
    """
    settings = get_settings()
    if not settings.gemini_api_key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = (
            "You are Numen's AttriGuard & FinePrint counterfactual security verifier.\n"
            f"Human Signed IntentMandate: {mandate.natural_language_intent} | "
            f"Allowed MCCs: {mandate.allowed_mccs} | Prohibited: {mandate.prohibited_keywords} | "
            f"AllowRecurring: {mandate.allow_recurring}\n\n"
            f"Proposed Spend: merchant={spend_req.merchant_name} ({spend_req.merchant_domain}), "
            f"mcc={spend_req.merchant_mcc}, amount_inr={spend_req.amount_inr}, items={spend_req.cart_items}\n"
            f"Agent Reasoning: {spend_req.agent_reasoning}\n"
            f"Untrusted DOM/HTML: {spend_req.untrusted_dom_html[:2000]}\n"
            f"Checkout Terms: {spend_req.checkout_terms_text[:2000]}\n\n"
            "Return strict JSON with keys: drift_score (float 0..1), world_b_action (string), "
            "injection_detected (bool), hidden_annual_inr (float), summary (string)."
        )
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        if resp and resp.text:
            return json.loads(resp.text)
    except Exception as exc:  # pragma: no cover - graceful offline/timeout fallback
        logger.warning("Gemini live call fell back to deterministic engine: %s", exc)
    return None
