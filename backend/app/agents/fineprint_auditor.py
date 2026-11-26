"""Fine-Print & Lookalike Domain Auditor: traps hidden annual auto-debits and homoglyph spoofing."""

from __future__ import annotations

import re
from typing import Any

from ..models import FinePrintResult, IntentMandate, SpendRequest

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
    re.compile(r"(auto[-\s]?renew|recurring\s+(?:annual|monthly)|non[-\s]?cancellable|locked\s+for\s+12\s+months|billed\s+annually)", re.IGNORECASE),
    re.compile(r"clause\s+\d+(?:\.\d+)?[^.\n]*(?:auto|renew|annual|debit|lock)", re.IGNORECASE),
]

_ANNUAL_AMOUNT_REGEX = re.compile(
    r"(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:/\s*(?:yr|year|annum)|per\s+year|annually|annual\s+plan)",
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


def detect_lookalike_domain(merchant_domain: str) -> str | None:
    """Detect 1-2 character typosquatting or homoglyph spoofing against canonical SaaS/cloud vendors."""
    dom = merchant_domain.strip().lower()
    if dom in CANONICAL_DOMAINS:
        return None
    norm_dom = _normalize_homoglyphs(dom)
    for canon in CANONICAL_DOMAINS:
        if dom != canon and (norm_dom == canon or 1 <= _levenshtein(dom, canon) <= 2):
            return canon
        # Catch prefix-spoof combos like runp0d-billing.io or aws-billiing.com
        canon_root = canon.split(".")[0]
        dom_root = dom.split(".")[0]
        if dom != canon and len(canon_root) >= 3:
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
    terms = spend_req.checkout_terms_text or ""
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

    if llm_hint:
        try:
            hidden_annual_inr = max(hidden_annual_inr, float(llm_hint.get("hidden_annual_inr", 0.0)))
        except (TypeError, ValueError):
            pass

    spoofed_of = detect_lookalike_domain(spend_req.merchant_domain)
    if spoofed_of:
        clauses_flagged.insert(0, f"Lookalike / homoglyph domain '{spend_req.merchant_domain}' spoofs canonical vendor '{spoofed_of}'.")
        return FinePrintResult(
            has_trap=True,
            hidden_annual_inr=hidden_annual_inr,
            spoofed_domain_of=spoofed_of,
            clauses_flagged=clauses_flagged,
            severity="CRITICAL",
        )

    if (clauses_flagged or hidden_annual_inr > 0) and not mandate.allow_recurring:
        return FinePrintResult(
            has_trap=True,
            hidden_annual_inr=hidden_annual_inr or round(spend_req.amount_inr * 12, 2),
            spoofed_domain_of=None,
            clauses_flagged=clauses_flagged or ["Recurring auto-debit commitment violates allow_recurring=False in IntentMandate."],
            severity="REVIEW",
        )

    return FinePrintResult(has_trap=False, hidden_annual_inr=0.0, spoofed_domain_of=None, clauses_flagged=[], severity="NONE")
