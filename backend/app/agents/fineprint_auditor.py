"""Fine-Print & Lookalike Domain Auditor: traps annual/monthly auto-debits, punycode & homoglyph spoofing."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from ..models import FinePrintResult, IntentMandate, SpendRequest
from .attriguard import normalize_untrusted_text

CANONICAL_DOMAINS = [
    "runpod.io",
    "aws.amazon.com",
    "cloud.google.com",
    "huggingface.co",
    "openai.com",
    "anthropic.com",
    "stripe.com",
    "datapulse.ai",
]

_RECURRING_PATTERNS = [
    re.compile(
        r"(auto[-\s]?renew|recurring\s+(?:annual|monthly)|non[-\s]?cancellable|locked\s+(?:for|in)\s+12\s+months|billed\s+annually)",
        re.IGNORECASE,
    ),
    re.compile(r"clause\s+\d+(?:\.\d+)?[^.\n]*(?:auto|renew|annual|monthly|debit|lock)", re.IGNORECASE),
]

_ANNUAL_AMOUNT_REGEX = re.compile(
    r"(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:/\s*(?:yr|year|annum)|per\s+year|annually|annual\s+plan)",
    re.IGNORECASE,
)

_MONTHLY_AMOUNT_REGEX = re.compile(
    r"(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:/\s*(?:mo|month)|per\s+month|monthly)",
    re.IGNORECASE,
)


def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        return _levenshtein(b, a)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            ins = prev[j + 1] + 1
            dele = curr[j] + 1
            sub = prev[j] + (ca != cb)
            curr.append(min(ins, dele, sub))
        prev = curr
    return prev[-1]


def _normalize_homoglyphs(domain: str) -> str:
    return (
        domain.lower()
        .replace("0", "o")
        .replace("1", "l")
        .replace("rn", "m")
        .replace("vv", "w")
    )


def extract_hostname(merchant_domain: str) -> str:
    raw = (merchant_domain or "").strip().lower()
    if "://" in raw:
        parsed = urlparse(raw)
        raw = parsed.hostname or raw
    else:
        raw = raw.split("/")[0].split(":")[0]
    return raw.strip(".")


def detect_lookalike_domain(merchant_domain: str) -> str | None:
    """Detect punycode IDN attacks, multi-label impersonation, typosquatting & homoglyph spoofing."""
    dom = extract_hostname(merchant_domain)
    if not dom:
        return None
    if dom in CANONICAL_DOMAINS:
        return None

    # IDN / Punycode spoofing detection
    if "xn--" in dom:
        return "punycode-idn-spoof"

    # Strip leading subdomains (e.g. billing.runp0d.io -> runp0d.io) while keeping multi-part canonical check
    labels = dom.split(".")
    registered_candidate = ".".join(labels[-2:]) if len(labels) >= 2 else dom

    for probe in (dom, registered_candidate):
        norm_dom = _normalize_homoglyphs(probe)
        for canon in CANONICAL_DOMAINS:
            if probe != canon and (norm_dom == canon or 1 <= _levenshtein(probe, canon) <= 2):
                return canon
            canon_root = canon.split(".")[0]
            dom_root = probe.split(".")[0]
            if probe != canon and len(canon_root) >= 3:
                norm_root = _normalize_homoglyphs(dom_root)
                if (norm_root.startswith(canon_root + "-") or norm_root.startswith(canon_root)) and dom_root != canon_root and len(canon_root) >= 5:
                    return canon
                if norm_root.startswith(canon_root + "-"):
                    return canon
                if len(canon_root) >= 5 and 1 <= _levenshtein(dom_root, canon_root) <= 1:
                    return canon
    return None


def evaluate_fineprint(
    mandate: IntentMandate,
    spend_req: SpendRequest,
    llm_hint: dict[str, Any] | None = None,
) -> FinePrintResult:
    terms = normalize_untrusted_text(spend_req.checkout_terms_text or "")
    clauses_flagged: list[str] = []
    hidden_annual_inr = 0.0

    for pat in _RECURRING_PATTERNS:
        for m in pat.finditer(terms):
            start = max(0, m.start() - 35)
            end = min(len(terms), m.end() + 85)
            excerpt = terms[start:end].strip()
            if excerpt and excerpt not in clauses_flagged:
                clauses_flagged.append(excerpt)

    for m in _ANNUAL_AMOUNT_REGEX.finditer(terms):
        raw_num = m.group(1).replace(",", "")
        try:
            val = float(raw_num)
            if val > spend_req.amount_inr * 2:
                hidden_annual_inr = max(hidden_annual_inr, val)
        except ValueError:
            pass

    for m in _MONTHLY_AMOUNT_REGEX.finditer(terms):
        raw_num = m.group(1).replace(",", "")
        try:
            monthly_val = float(raw_num)
            annualized = monthly_val * 12.0
            if annualized > spend_req.amount_inr * 2 and clauses_flagged:
                hidden_annual_inr = max(hidden_annual_inr, annualized)
        except ValueError:
            pass

    if llm_hint:
        try:
            hidden_annual_inr = max(hidden_annual_inr, float(llm_hint.get("hidden_annual_inr", 0.0)))
        except (TypeError, ValueError):
            pass

    spoofed_of = detect_lookalike_domain(spend_req.merchant_domain)
    if spoofed_of:
        clauses_flagged.insert(0, f"Lookalike / homoglyph domain '{spend_req.merchant_domain}' spoofs '{spoofed_of}'.")
        return FinePrintResult(
            has_trap=True,
            hidden_annual_inr=hidden_annual_inr,
            spoofed_domain_of=spoofed_of,
            clauses_flagged=clauses_flagged,
            severity="CRITICAL",
        )

    has_trap = (not mandate.allow_recurring) and (bool(clauses_flagged) or hidden_annual_inr > spend_req.amount_inr * 3)
    severity = "REVIEW" if has_trap else "NONE"
    return FinePrintResult(
        has_trap=has_trap,
        hidden_annual_inr=round(hidden_annual_inr, 2),
        spoofed_domain_of=None,
        clauses_flagged=clauses_flagged,
        severity=severity,
    )
