"""AttriGuard Counterfactual Firewall (arXiv:2603.10749) & Hardened Dual Tool Sanitizer (arXiv:2510.05244)."""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Any

from ..models import AttriGuardResult, IntentMandate, SpendRequest

_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\ufeff\u00ad]+")

# Hidden CSS / HTML-comment / obfuscation patterns
_HIDDEN_CSS_PATTERNS = [
    re.compile(
        r"<[^>]+style\s*=\s*[\"'][^\"']*(?:opacity\s*:\s*0|display\s*:\s*none|visibility\s*:\s*hidden|"
        r"font-size\s*:\s*0|height\s*:\s*0|width\s*:\s*0|clip\s*:\s*rect\(\s*0|text-indent\s*:\s*-\d{3,}px|"
        r"color\s*:\s*(?:#fff(?:fff)?|white)|(?:left|top)\s*:\s*-\d{3,}px)[^\"']*[\"'][^>]*>(.*?)</[^>]+>",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(r"<!--(.*?)-->", re.IGNORECASE | re.DOTALL),
]

_HIJACK_DIRECTIVES = [
    re.compile(r"SYSTEM\s+OVERRIDE[^<\n]*", re.IGNORECASE),
    re.compile(r"IGNORE\s+(?:ALL\s+)?PREVIOUS\s+INSTRUCTIONS[^<\n]*", re.IGNORECASE),
    re.compile(r"URGENT\s+SECURITY\s+PATCH[^<\n]*", re.IGNORECASE),
    re.compile(r"DO\s+NOT\s+(?:TELL|NOTIFY)\s+(?:THE\s+)?USER[^<\n]*", re.IGNORECASE),
    re.compile(r"REDIRECT\s+PAYMENT[^<\n]*", re.IGNORECASE),
    re.compile(r"BUY\s+(?:INR|USD|\$|₹)?\s*[\d,]+\s+(?:GIFT|VOUCHER|CARD)[^<\n]*", re.IGNORECASE),
    re.compile(r"ADMIN\s+EXECUTION\s+REQUIRED[^<\n]*", re.IGNORECASE),
]


def normalize_untrusted_text(raw: str) -> str:
    """Defeat HTML entity encoding, full-width NFKC homoglyphs, and zero-width char splitting."""
    if not raw:
        return ""
    unescaped = html.unescape(raw)
    nfkc = unicodedata.normalize("NFKC", unescaped)
    return _ZERO_WIDTH_RE.sub("", nfkc)


def extract_poisoned_spans(dom_html: str) -> list[str]:
    """Dual Tool Output Sanitizer: isolate hidden CSS, zero-width obfuscation, comments & override directives."""
    if not dom_html:
        return []
    spans: list[str] = []

    if _ZERO_WIDTH_RE.search(dom_html):
        spans.append("[ZERO_WIDTH_UNICODE_OBFUSCATION_DETECTED]")

    normalized = normalize_untrusted_text(dom_html)

    for pat in _HIDDEN_CSS_PATTERNS:
        for m in pat.finditer(normalized):
            snippet = m.group(0).strip()
            if snippet and snippet not in spans:
                spans.append(snippet[:280])

    for pat in _HIJACK_DIRECTIVES:
        for m in pat.finditer(normalized):
            snippet = m.group(0).strip()
            if snippet and not any(snippet in existing for existing in spans):
                spans.append(snippet[:280])
    return spans


def evaluate_attriguard(
    mandate: IntentMandate,
    spend_req: SpendRequest,
    llm_hint: dict[str, Any] | None = None,
) -> AttriGuardResult:
    """
    Run counterfactual causal attribution (World A: full untrusted context vs World B: mandate-only context).
    Returns drift_score in [0.0, 1.0] plus exact highlighted poisoned DOM spans.
    """
    poisoned_spans = extract_poisoned_spans(spend_req.untrusted_dom_html)
    norm_reasoning = normalize_untrusted_text(spend_req.agent_reasoning or "")
    combined_untrusted = f"{spend_req.merchant_name} {spend_req.merchant_domain} {' '.join(spend_req.cart_items)} {norm_reasoning}".lower()

    matched_prohibited = [kw for kw in mandate.prohibited_keywords if kw in combined_untrusted]
    mcc_allowed = spend_req.merchant_mcc.upper() in {m.upper() for m in mandate.allowed_mccs}

    # Check if normalized agent reasoning echoes adversarial override phrasing
    reasoning_hijacked = any(pat.search(norm_reasoning) for pat in _HIJACK_DIRECTIVES)

    drift = 0.0
    reasons: list[str] = []

    if poisoned_spans:
        drift += 0.55
        reasons.append(f"Detected {len(poisoned_spans)} hidden/adversarial prompt-injection span(s) inside untrusted DOM")

    if matched_prohibited:
        drift += 0.40
        reasons.append(f"Proposed purchase contains prohibited items/keywords: {', '.join(matched_prohibited)}")

    if not mcc_allowed:
        drift += 0.35
        reasons.append(f"Merchant MCC '{spend_req.merchant_mcc}' violates human IntentMandate allowed MCCs {mandate.allowed_mccs}")

    if reasoning_hijacked:
        drift += 0.30
        reasons.append("Agent reasoning trace mirrors imperative override directives from untrusted content")

    # Blend optional live Gemini counterfactual verification conservatively
    llm_world_b = None
    if llm_hint:
        try:
            llm_drift = float(llm_hint.get("drift_score", 0.0))
            drift = max(drift, min(1.0, llm_drift))
            llm_world_b = llm_hint.get("world_b_action")
        except (TypeError, ValueError):
            pass

    drift = round(min(1.0, drift), 2)
    world_a = f"Pay INR {spend_req.amount_inr:,.2f} -> {spend_req.merchant_name} ({spend_req.merchant_mcc}) [{', '.join(spend_req.cart_items) or 'item'}]"

    if drift >= 0.25:
        world_b = llm_world_b or f"Revert to Human Mandate: '{mandate.natural_language_intent[:95]}...'"
        injection_detected = bool(poisoned_spans or reasoning_hijacked or matched_prohibited)
        explanation = "; ".join(reasons) or "Counterfactual World B diverges from World A purchase target."
    else:
        world_b = world_a
        injection_detected = False
        explanation = "Counterfactual World B matches World A: purchase is causally grounded in human IntentMandate."

    return AttriGuardResult(
        drift_score=drift,
        world_a_action=world_a,
        world_b_action=world_b,
        poisoned_spans=poisoned_spans,
        injection_detected=injection_detected,
        explanation=explanation,
    )
