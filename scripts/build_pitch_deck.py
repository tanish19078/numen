"""
Numen 9-Slide Fintech-First Pitch Deck Generator & Automated Craft Auditor
-------------------------------------------------------------------------
Layer-2 Fintech Positioning ("The Ramp + Stripe Radar Control Layer for AI Agents"):
- Slides 1-9 synced with DESIGN.md and docs/NUMEN_PITCH_AND_GUIDE.md
- Floats exact verified figures (McKinsey $3T-$5T, Gartner 90%/$15T, AgentDojo 55.0%,
  DeepMind CaMeL 77%/67%, Dual Firewalls ~0% ASR, AttriGuard 0% ASR/~3% drop)
- Dedicated Slide 08 for Zero-Charter Feasibility & 3-Stream Business Model
- Strict bounds + <= 95 body-word audit per slide
"""

from __future__ import annotations

import os
from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

SLIDE_W = 13.333
SLIDE_H = 7.5
EMU_PER_INCH = 914400

C_CANVAS = (247, 250, 248)       # #F7FAF8
C_WHITE = (255, 255, 255)
C_SUBTLE = (241, 246, 243)       # #F1F6F3
C_LINE = (226, 235, 229)         # #E2EBE5
C_PINE = (11, 31, 22)            # #0B1F16
C_SAGE = (82, 107, 93)           # #526B5D
C_STONE = (132, 155, 142)
C_EMERALD = (5, 150, 105)        # #059669
C_MINT_WASH = (236, 253, 245)    # #ECFDF5
C_MINT_BORDER = (167, 243, 208)
C_DARK_PINE = (13, 38, 28)       # #0D261C
C_CARD_MINT = (110, 231, 183)    # #6EE7B7
C_THREAT = (220, 38, 38)         # #DC2626
C_THREAT_WASH = (254, 242, 242)
C_THREAT_BORDER = (254, 202, 202)
C_REVIEW = (217, 119, 6)         # #D97706
C_REVIEW_WASH = (255, 251, 235)
C_REVIEW_BORDER = (253, 230, 138)
C_COBALT = (37, 99, 235)         # #2563EB
C_COBALT_WASH = (239, 246, 255)


def rgb(c: tuple[int, int, int]) -> RGBColor:
    return RGBColor(*c)


class EditorialSlide:
    def __init__(self, prs: Presentation, num: int, eyebrow: str, dark: bool = False) -> None:
        self.slide = prs.slides.add_slide(prs.slide_layouts[6])
        self.num = num
        self.dark = dark

        bg = self.slide.background.fill
        bg.solid()
        bg.fore_color.rgb = rgb(C_DARK_PINE if dark else C_CANVAS)

        eyebrow_col = C_CARD_MINT if dark else C_EMERALD
        foot_col = (148, 178, 164) if dark else C_STONE
        self.text(eyebrow, 0.65, 0.44, 6.8, 0.28, size=10.5, bold=True, font="Consolas", color=eyebrow_col, tag="__chrome__")
        self.text(f"0{num} / 09", 11.40, 6.96, 1.28, 0.28, size=10.0, bold=True, font="Consolas", color=foot_col, align="right", tag="__chrome__")
        self.text("NUMEN  ·  LAYER-2 ISSUER CONTROL PLANE FOR AI SPEND", 0.65, 6.96, 7.6, 0.28, size=9.5, font="Consolas", color=foot_col, tag="__chrome__")

        prog_w = 12.03 * (num / 9.0)
        self.rect(0.65, 6.84, 12.03, 0.03, fill=(30, 66, 51) if dark else C_LINE, border=None, rounded=False, tag="__chrome__")
        self.rect(0.65, 6.84, prog_w, 0.03, fill=C_CARD_MINT if dark else C_EMERALD, border=None, rounded=False, tag="__chrome__")

    def morph(self) -> None:
        sld = self.slide._element
        ns_p = "http://schemas.openxmlformats.org/presentationml/2006/main"
        ns_mc = "http://schemas.openxmlformats.org/markup-compatibility/2006"
        ns_p159 = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
        xml = (
            f'<mc:AlternateContent xmlns:mc="{ns_mc}" xmlns:p="{ns_p}" xmlns:p159="{ns_p159}">'
            f'  <mc:Choice Requires="p159"><p:transition spd="med" advClick="1"><p159:morph option="byObject"/></p:transition></mc:Choice>'
            f'  <mc:Fallback><p:transition spd="med" advClick="1"><p:fade thruBlk="0"/></p:transition></mc:Fallback>'
            f'</mc:AlternateContent>'
        )
        node = etree.fromstring(xml)
        insert_idx = 1
        for idx, ch in enumerate(sld):
            if ch.tag.endswith("cSld") or ch.tag.endswith("clrMapOvr"):
                insert_idx = idx + 1
        sld.insert(insert_idx, node)

    def notes(self, txt: str) -> None:
        self.slide.notes_slide.notes_text_frame.text = txt

    def headline(self, title: str, subtitle: str = "") -> None:
        tc = C_WHITE if self.dark else C_PINE
        sc = (196, 224, 211) if self.dark else C_SAGE
        self.text(title, 0.65, 0.78, 12.03, 0.78, size=24.5, bold=True, color=tc, spacing=1.12)
        if subtitle:
            self.text(subtitle, 0.65, 1.56, 11.4, 0.44, size=13.5, color=sc, spacing=1.2)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: tuple[int, int, int] | None = C_WHITE,
        border: tuple[int, int, int] | None = C_LINE,
        border_pt: float = 0.9,
        rounded: bool = True,
        radius: float = 0.06,
        tag: str | None = None,
    ):
        kind = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
        shp = self.slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
        if rounded and len(shp.adjustments) > 0:
            shp.adjustments[0] = radius
        if fill:
            shp.fill.solid()
            shp.fill.fore_color.rgb = rgb(fill)
        else:
            shp.fill.background()
        if border:
            shp.line.color.rgb = rgb(border)
            shp.line.width = Pt(border_pt)
        else:
            shp.line.fill.background()
        if tag:
            shp.name = tag
        return shp

    def pill(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        label: str,
        fill: tuple[int, int, int],
        fg: tuple[int, int, int],
        border: tuple[int, int, int] | None = None,
        size: float = 10.0,
    ):
        shp = self.rect(x, y, w, h, fill=fill, border=border, border_pt=0.9, rounded=True, radius=0.5)
        tf = shp.text_frame
        tf.word_wrap = False
        tf.margin_left = Inches(0.08)
        tf.margin_right = Inches(0.08)
        tf.margin_top = Inches(0.02)
        tf.margin_bottom = Inches(0.02)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = label
        r.font.name = "Consolas"
        r.font.size = Pt(size)
        r.font.bold = True
        r.font.color.rgb = rgb(fg)
        return shp

    def arrow_right(self, x: float, y: float, w: float = 0.34, h: float = 0.24, col: tuple[int, int, int] = C_EMERALD):
        shp = self.slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
        shp.fill.solid()
        shp.fill.fore_color.rgb = rgb(col)
        shp.line.fill.background()
        return shp

    def text(
        self,
        txt: str,
        x: float,
        y: float,
        w: float,
        h: float,
        size: float = 13.5,
        color: tuple[int, int, int] = C_PINE,
        bold: bool = False,
        font: str = "Segoe UI",
        align: str = "left",
        valign: str = "top",
        spacing: float = 1.22,
        tag: str | None = None,
    ):
        tb = self.slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        if tag:
            tb.name = tag
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.03)
        tf.margin_right = Inches(0.03)
        tf.margin_top = Inches(0.02)
        tf.margin_bottom = Inches(0.02)
        tf.vertical_anchor = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}[valign]
        al = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
        for idx, line in enumerate(txt.split("\n")):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.alignment = al
            p.line_spacing = spacing
            r = p.add_run()
            r.text = line
            r.font.name = font
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.color.rgb = rgb(color)
        return tb


def audit_deck(prs: Presentation) -> None:
    max_x, max_y = 12.98, 7.28
    min_x, min_y = 0.35, 0.25
    print("\n--- FINTECH PITCH DECK QUALITY AUDIT ---")
    for idx, slide in enumerate(prs.slides, start=1):
        words = 0
        for shp in slide.shapes:
            x = shp.left / EMU_PER_INCH
            y = shp.top / EMU_PER_INCH
            w = shp.width / EMU_PER_INCH
            h = shp.height / EMU_PER_INCH
            if x < min_x - 0.01 or y < min_y - 0.01 or (x + w) > max_x + 0.01 or (y + h) > max_y + 0.01:
                raise AssertionError(
                    f"Slide {idx} shape '{shp.name}' out of bounds: x={x:.2f}, y={y:.2f}, r={x+w:.2f}, b={y+h:.2f}"
                )
            if shp.has_text_frame and shp.name != "__chrome__":
                words += len(shp.text_frame.text.split())
        if words > 95:
            raise AssertionError(f"Slide {idx} exceeds 95-word cap ({words}w)")
        print(f"Slide 0{idx}: {words:2d} body words | bounds SAFE | OK")
    print("--- AUDIT PASSED ---\n")


def build_deck(out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)

    # SLIDE 1 — HERO ASYMMETRIC SPLIT (FINTECH LAYER-2 POSITIONING)
    s = EditorialSlide(prs, 1, "NUMEN  /  FINTECH FOR AGENTIC COMMERCE")
    s.morph()
    s.pill(0.65, 1.30, 4.10, 0.34, "PROGRAMMABLE AGENT ISSUER LAYER", C_MINT_WASH, C_EMERALD, border=C_MINT_BORDER, size=10.0)
    s.text("Numen", 0.65, 1.85, 5.4, 0.96, size=56, bold=True, font="Bahnschrift", color=C_PINE)
    s.text("The Ramp + Stripe Radar control layer for AI agent spend.", 0.65, 2.95, 5.6, 1.05, size=22, bold=True, color=C_EMERALD, spacing=1.18)
    s.text("Sub-accounts, pre-authorization fraud checks, and 60-second exact-rupee virtual cards.", 0.65, 4.22, 5.4, 0.80, size=14, color=C_SAGE)
    s.pill(0.65, 5.55, 2.55, 0.38, "Google AP2 + MCP + A2A", C_WHITE, C_PINE, border=C_LINE, size=10.0)
    s.pill(3.35, 5.55, 2.75, 0.38, "60s Exact-Rupee Cards", C_WHITE, C_PINE, border=C_LINE, size=10.0)

    s.rect(7.05, 1.48, 5.55, 1.18, fill=C_WHITE, border=C_LINE, radius=0.10)
    s.text("OPERATING TREASURY VAULT", 7.35, 1.65, 2.8, 0.25, size=10, bold=True, font="Consolas", color=C_SAGE)
    s.text("Acme AI Labs · 3 Sub-Accounts", 7.35, 1.98, 2.9, 0.36, size=13.5, bold=True, color=C_PINE)
    s.text("₹18,40,000", 10.10, 1.78, 2.25, 0.45, size=22, bold=True, font="Bahnschrift", color=C_PINE, align="right")

    s.rect(6.95, 3.02, 5.65, 2.52, fill=C_DARK_PINE, border=C_EMERALD, border_pt=1.4, radius=0.10)
    s.text("Numen", 7.30, 3.24, 1.8, 0.44, size=23, bold=True, font="Bahnschrift", color=C_WHITE)
    s.pill(10.35, 3.28, 1.95, 0.34, "ACTIVE · 60s TTL", C_EMERALD, C_WHITE, size=9.5)
    s.rect(7.30, 3.84, 0.56, 0.36, fill=(36, 79, 61), border=C_CARD_MINT, border_pt=1.0, radius=0.18)
    s.text("EXACT LOCK: ₹3,400.00", 9.65, 3.88, 2.65, 0.30, size=10.5, bold=True, font="Consolas", color=C_CARD_MINT, align="right")
    s.text("4532   8910   4402   9104", 7.30, 4.38, 4.95, 0.40, size=19, bold=True, font="Consolas", color=C_WHITE)
    s.text("DEVOPS-AGENT  ·  RUNPOD CLOUD  ·  AUTO-SHREDS", 7.30, 4.96, 4.95, 0.30, size=10.5, font="Consolas", color=(184, 217, 200))

    s.pill(7.05, 5.82, 2.70, 0.42, "Pre-Auth: Verified", C_MINT_WASH, C_EMERALD, border=C_MINT_BORDER, size=10.0)
    s.pill(9.92, 5.82, 2.68, 0.42, "Post-Settle Bleed: ₹0.00", C_SUBTLE, C_PINE, border=C_LINE, size=10.0)
    s.notes("SLIDE 1: Numen is the Ramp + Stripe Radar control layer for AI agent spend—governing treasury sub-accounts and 60-second exact-rupee virtual cards.")

    # SLIDE 2 — MACRO DATA + 4-LAYER PAYMENTS STACK (OWNING LAYER 2)
    s = EditorialSlide(prs, 2, "01 / MARKET & THE 4-LAYER STACK")
    s.morph()
    s.headline(
        "Agents drive $3T–$15T in spend — we own the issuer choke point.",
        "Banking rails miss agent hijacks; agent specs do not stop them.",
    )

    kpis = [
        ("$3T – $5T", "Agent commerce by 2030", "McKinsey ($1T U.S. B2C)", C_EMERALD),
        ("90% / $15T", "B2B via AI by 2028", "Gartner B2B forecast", C_COBALT),
        ("55.0% ASR", "Banking hijacks (79/144)", "AgentDojo GPT-4o (NeurIPS)", C_THREAT),
    ]
    for i, (num, head, src, col) in enumerate(kpis):
        kx = 0.65 + i * 4.15
        if i > 0:
            s.rect(kx - 0.22, 2.40, 0.015, 2.00, fill=C_LINE, border=None, rounded=False)
        s.text(num, kx, 2.40, 3.70, 0.68, size=38, bold=True, font="Bahnschrift", color=col)
        s.text(head, kx, 3.18, 3.70, 0.40, size=15, bold=True, color=C_PINE)
        s.text(src, kx, 3.64, 3.70, 0.50, size=13, color=C_SAGE)

    s.rect(0.65, 4.88, 12.03, 1.62, fill=C_WHITE, border=C_LINE, radius=0.08)
    s.text("4-LAYER AGENTIC PAYMENTS STACK (NUMEN OWNS LAYER 2)", 0.92, 5.04, 11.4, 0.26, size=10.0, bold=True, font="Consolas", color=C_EMERALD)
    layers = [
        ("L4: AGENTS", "Claude, Cursor, ADK", C_SUBTLE, C_SAGE, False),
        ("L3: SPECS", "A2A, MCP, AP2, ACP", C_COBALT_WASH, C_COBALT, False),
        ("L2: NUMEN", "Issuer & Spend Firewall", C_MINT_WASH, C_EMERALD, True),
        ("L1: RAILS", "Visa, Stripe, RazorpayX", C_SUBTLE, C_PINE, False),
    ]
    for i, (lk, lt, bgc, col, hl) in enumerate(layers):
        lx = 0.92 + i * 2.92
        s.rect(lx, 5.44, 2.72, 0.84, fill=bgc, border=col, border_pt=1.8 if hl else 0.9, radius=0.12)
        s.text(lk, lx + 0.14, 5.52, 2.44, 0.24, size=9.5, bold=True, font="Consolas", color=col)
        s.text(lt, lx + 0.14, 5.80, 2.44, 0.36, size=13, bold=True, color=C_PINE)
    s.notes("SLIDE 2: Layer 4 builds AI models, Layer 3 handles A2A/MCP/AP2, and Layer 1 settles Visa/Stripe. Numen owns Layer 2—the issuer choke point.")

    # SLIDE 3 — THE FINTECH PROBLEM: SUB-LIMIT FRAUD & TRAPS
    s = EditorialSlide(prs, 3, "02 / WHY STATIC CORPORATE CARDS FAIL")
    s.morph()
    s.headline(
        "A ₹10,000 spend cap approves a ₹4,200 theft unless the bank checks why.",
        "Prompt injections, phished links & annual traps strike below static limits.",
    )

    s.rect(0.65, 2.38, 3.65, 4.05, fill=C_THREAT_WASH, border=C_THREAT_BORDER, border_pt=1.2, radius=0.08)
    s.pill(0.88, 2.60, 2.35, 0.32, "STATIC ₹10,000 CARD", C_THREAT, C_WHITE, size=10.0)
    s.text("₹4,200 <= ₹10,000\nBlindly approved", 0.88, 3.16, 3.15, 0.85, size=16, bold=True, color=C_PINE)
    s.text("Hidden <span opacity:0>\nhijacks voucher spend.", 0.88, 4.30, 3.15, 1.1, size=14, color=C_THREAT)

    s.rect(4.55, 2.38, 3.85, 4.05, fill=C_MINT_WASH, border=C_MINT_BORDER, border_pt=1.2, radius=0.08)
    s.pill(4.78, 2.60, 2.45, 0.32, "NUMEN PRE-AUTH", C_EMERALD, C_WHITE, size=10.0)
    s.text("World A != World B\nCausal Drift: 1.00", 4.78, 3.16, 3.35, 0.85, size=16, bold=True, color=C_PINE)
    s.text("Cloud mandate rejects RETAIL;\nmint blocked, agent paused.", 4.78, 4.30, 3.35, 1.1, size=14, color=C_PINE)

    points = [
        ("Treasury Choke Point", "100% of money crosses issuance pre-mint."),
        ("Phishing & Loops", "Stops runp0d.io spoofs & 3x/60s retries."),
        ("Fine-Print Defense", "Holds ₹99 -> ₹36k/yr traps via Passkey."),
    ]
    for i, (pt, pd) in enumerate(points):
        py = 2.42 + i * 1.38
        s.rect(8.72, py, 3.96, 1.18, fill=C_WHITE, border=C_LINE, radius=0.08)
        s.text(pt, 8.95, py + 0.16, 3.50, 0.32, size=14.5, bold=True, color=C_PINE)
        s.text(pd, 8.95, py + 0.52, 3.50, 0.56, size=13, color=C_SAGE)
    s.notes("SLIDE 3: Static spend caps fail sub-limit fraud. Numen stops hidden prompt injections, homoglyph phishing, and hidden annual clauses pre-mint.")

    # SLIDE 4 — 3-CLUSTER ARCHITECTURE (ZERO LLM CUSTODY)
    s = EditorialSlide(prs, 4, "03 / 3-CLUSTER FINTECH ARCHITECTURE")
    s.morph()
    s.headline(
        "Three clusters isolate untrusted browsing from deterministic banking ledger custody.",
        "No LLM ever signs mandates, generates card PANs, or mutates rupee balances.",
    )

    clusters = [
        ("CLUSTER 1 · EDGE", "Commerce Agents", "DevOps, Procurement & Research\n\n• A2A /.well-known/agent.json\n• Calls POST /mcp\n• Zero PAN custody", C_WHITE, C_PINE, C_SAGE, C_LINE),
        ("CLUSTER 2 · QUORUM", "4 Pre-Auth Voters", "Gemini Flash / Pro Router\n\n• Budget & 3x Loop\n• CaMeL Provenance\n• AttriGuard & FinePrint", C_MINT_WASH, C_PINE, C_PINE, C_EMERALD),
        ("CLUSTER 3 · VAULT", "Zero-LLM Custody", "Deterministic Python Only\n\n• Ed25519 AP2 Mandates\n• 60s Luhn PAN (±₹0.00)\n• ACID Ledger & Shredder", C_DARK_PINE, C_WHITE, (204, 232, 217), C_EMERALD),
    ]
    for i, (ck, ct, cb, bgc, tc, bc, bdc) in enumerate(clusters):
        cx = 0.65 + i * 4.18
        s.rect(cx, 2.40, 3.68, 3.92, fill=bgc, border=bdc, border_pt=1.3, radius=0.08)
        s.text(ck, cx + 0.24, 2.62, 3.20, 0.26, size=10, bold=True, font="Consolas", color=C_CARD_MINT if bgc == C_DARK_PINE else C_EMERALD)
        s.text(ct, cx + 0.24, 2.98, 3.20, 0.42, size=17, bold=True, color=tc)
        s.text(cb, cx + 0.24, 3.55, 3.20, 2.45, size=13.5, color=bc, spacing=1.28)
        if i < 2:
            s.arrow_right(cx + 3.74, 4.22, 0.36, 0.24, C_EMERALD)
    s.notes("SLIDE 4: Strict neuro-symbolic separation: Cluster 2 runs 4 consensus voters; Cluster 3 handles Ed25519 signing, Luhn PAN minting, and ledger commits deterministically.")

    # SLIDE 5 — EMPIRICAL RESEARCH DATA FLOATED
    s = EditorialSlide(prs, 5, "04 / PEER-REVIEWED RESEARCH BASIS")
    s.morph()
    s.headline(
        "Empirical findings from four security papers compiled into one smart-routed quorum.",
        "Smart Routing avoids counterfactual overhead on clean cloud infrastructure.",
    )

    s.rect(0.65, 2.35, 12.03, 4.12, fill=C_WHITE, border=C_LINE, radius=0.08)
    s.text("RESEARCH PAPER", 0.92, 2.54, 3.8, 0.28, size=10, bold=True, font="Consolas", color=C_SAGE)
    s.text("PUBLISHED BENCHMARK DATA", 4.90, 2.54, 4.2, 0.28, size=10, bold=True, font="Consolas", color=C_EMERALD)
    s.text("NUMEN MODULE", 9.30, 2.54, 3.1, 0.28, size=10, bold=True, font="Consolas", color=C_COBALT)

    papers = [
        ("AgentDojo (arXiv:2406.13352)", "55.0% Banking ASR on GPT-4o (79/144); 47.7% avg", "scenarios.py (240 cases)"),
        ("DeepMind CaMeL (2503.18813)", "77% utility (vs 84%); 67% attacks neutralized", "camel_capabilities.py"),
        ("Dual Firewalls (2510.05244)", "~0% static ASR via tool-output sanitization", "extract_poisoned_spans()"),
        ("AttriGuard (2603.10749)", "0% static ASR; ~3% utility drop (~2x token cost)", "SmartRouter + attriguard.py"),
    ]
    for i, (p_name, p_stat, p_mod) in enumerate(papers):
        ry = 3.00 + i * 0.85
        s.rect(0.92, ry - 0.08, 11.48, 0.015, fill=C_LINE, border=None, rounded=False)
        s.text(p_name, 0.92, ry + 0.04, 3.80, 0.56, size=13.5, bold=True, color=C_PINE, valign="middle")
        s.text(p_stat, 4.90, ry + 0.04, 4.20, 0.56, size=13, color=C_PINE, valign="middle")
        s.text(p_mod, 9.30, ry + 0.04, 3.10, 0.56, size=12.5, font="Consolas", color=C_EMERALD, valign="middle")
    s.notes("SLIDE 5: Every layer maps to verified empirical numbers from AgentDojo, DeepMind CaMeL, Dual Firewalls, and AttriGuard.")

    # SLIDE 6 — LIVE 3-ACT FINTECH DEMO STORYBOARD
    s = EditorialSlide(prs, 6, "05 / LIVE STAGE DEMO")
    s.morph()
    s.headline(
        "Three live scenarios prove exact-rupee cards, hijack defense & clause protection.",
        "Interactive in our Treasury Console at http://127.0.0.1:8000.",
    )

    acts = [
        ("ACT I · EXACT-RUPEE MINT", "RunPod GPU (₹3,400)", "Flash approves mandate; mints 60s PAN.\n+₹1 declines; ₹3,400 settles & shreds.", "MINTED -> SHREDDED", C_EMERALD, C_MINT_WASH, C_MINT_BORDER),
        ("ACT II · SUB-LIMIT HIJACK", "Gift Vouchers (₹4,200)", "Strips opacity:0 injection below ₹10k limit.\nDrift 1.00 blocks mint & pauses agent.", "BLOCKED (₹0 LOST)", C_THREAT, C_THREAT_WASH, C_THREAT_BORDER),
        ("ACT III · SUBSCRIPTION TRAP", "₹99 Trial -> ₹36k/yr", "Exposes Clause 14.3 annual auto-debit.\n1-Tap Passkey denies or caps ₹99 once.", "PASSKEY ESCALATED", C_REVIEW, C_REVIEW_WASH, C_REVIEW_BORDER),
    ]
    for i, (ey, title, body, badge, col, bgc, bdc) in enumerate(acts):
        ax = 0.65 + i * 4.10
        s.rect(ax, 2.38, 3.82, 4.05, fill=C_WHITE, border=bdc, border_pt=1.2, radius=0.08)
        s.text(ey, ax + 0.24, 2.60, 3.34, 0.26, size=10, bold=True, font="Consolas", color=col)
        s.text(title, ax + 0.24, 2.98, 3.34, 0.42, size=17, bold=True, color=C_PINE)
        s.text(body, ax + 0.24, 3.65, 3.34, 1.75, size=14, color=C_SAGE, spacing=1.32)
        s.pill(ax + 0.24, 5.76, 3.34, 0.40, badge, bgc, col, border=bdc, size=10.5)
    s.notes("SLIDE 6: Live 3-act demo: exact-rupee lock (+₹1 overcharge rejected), sub-limit DOM hijack block, and Clause 14.3 1-Tap Passkey escalation.")

    # SLIDE 7 — 240-SCENARIO MEASURED BENCHMARK PROOF
    s = EditorialSlide(prs, 7, "06 / MEASURED RED-TEAM PROOF")
    s.morph()
    s.headline(
        "100% sub-limit hijack prevention across 240 cases with zero false positives.",
        "Reproducible live via POST /api/benchmarks/run and 10 / 10 pytest tests.",
    )

    s.rect(0.65, 2.35, 4.45, 1.92, fill=C_MINT_WASH, border=C_MINT_BORDER, border_pt=1.2, radius=0.08)
    s.text("100.0%", 0.92, 2.52, 3.9, 0.72, size=42, bold=True, font="Bahnschrift", color=C_EMERALD)
    s.text("90 / 90 sub-limit injections blocked\n(vs. 0.0% static ₹10k card)", 0.92, 3.32, 3.9, 0.72, size=13.5, bold=True, color=C_PINE)

    s.rect(0.65, 4.48, 4.45, 1.92, fill=C_WHITE, border=C_LINE, radius=0.08)
    s.text("₹0.00", 0.92, 4.66, 3.9, 0.72, size=42, bold=True, font="Bahnschrift", color=C_PINE)
    s.text("Bleed across 50 traps, 30 spoofs,\n20 loops & 50 clean checkouts", 0.92, 5.44, 3.9, 0.72, size=13.5, color=C_SAGE)

    s.rect(5.40, 2.35, 7.28, 4.05, fill=C_WHITE, border=C_LINE, radius=0.08)
    bars = [
        ("Numen (CaMeL + AttriGuard)", 1.00, C_EMERALD, "100.0%"),
        ("Regex Keyword Blocklist", 0.54, C_REVIEW, "54.2%"),
        ("Static ₹10k Spend Cap", 0.04, C_THREAT, "0.0%"),
    ]
    by = 2.68
    for lbl, ratio, bcol, val in bars:
        s.text(lbl, 5.72, by, 4.8, 0.30, size=14, bold=(bcol == C_EMERALD), color=C_PINE)
        s.text(val, 10.80, by, 1.56, 0.30, size=14, bold=True, font="Consolas", color=bcol, align="right")
        s.rect(5.72, by + 0.38, 6.64, 0.24, fill=C_SUBTLE, border=None, radius=0.5)
        s.rect(5.72, by + 0.38, max(0.28, 6.64 * ratio), 0.24, fill=bcol, border=None, radius=0.5)
        by += 0.96

    s.text("Deterministic pre-filter P95 < 1 ms · 10 / 10 pytest passing", 5.72, 5.72, 6.64, 0.42, size=12.5, bold=True, font="Consolas", color=C_SAGE)
    s.notes("SLIDE 7: 240 live cases confirm 90/90 sub-limit injections blocked, 50/50 fine-print traps caught, 30/30 spoofs blocked, and 0/50 false positives.")

    # SLIDE 8 — ZERO-CHARTER FEASIBILITY & BUSINESS FITNESS
    s = EditorialSlide(prs, 8, "07 / FEASIBILITY & BUSINESS MODEL")
    s.morph()
    s.headline(
        "Ships on JIT card rails with zero bank charter — and 3 revenue streams.",
        "Built on Ramp & Brex's sponsor-bank model with a 5-min MCP wedge.",
    )

    # Left Card: Actual Feasibility Today
    s.rect(0.65, 2.32, 5.85, 3.22, fill=C_WHITE, border=C_LINE, radius=0.08)
    s.text("ACTUAL FEASIBILITY TODAY", 0.92, 2.52, 5.3, 0.28, size=10.5, bold=True, font="Consolas", color=C_EMERALD)
    s.text(
        "• Zero Charter: Program layer over Stripe Issuing, Marqeta, RazorpayX.\n"
        "• JIT Webhooks: <500ms callbacks enforce ±₹0.00 & card shredding.\n"
        "• Live Now: MCP, A2A, Ed25519 & 60s sandbox.",
        0.92,
        2.90,
        5.3,
        2.45,
        size=13.5,
        color=C_PINE,
        spacing=1.28,
    )

    # Right Card: 3-Stream Revenue Model
    s.rect(6.83, 2.32, 5.85, 3.22, fill=C_MINT_WASH, border=C_MINT_BORDER, border_pt=1.2, radius=0.08)
    s.text("BUSINESS FITNESS & REVENUE", 7.10, 2.52, 5.3, 0.28, size=10.5, bold=True, font="Consolas", color=C_EMERALD)
    s.text(
        "1. 1.2%–1.8% Interchange: Merchant share on settled AI cards.\n"
        "2. $29–$99/agent/mo: CFO governance, audit logs & Passkeys.\n"
        "3. $0.01–$0.03/auth: Issuer firewall API licensing.",
        7.10,
        2.90,
        5.3,
        2.45,
        size=13.5,
        color=C_PINE,
        spacing=1.28,
    )

    s.rect(0.65, 5.74, 12.03, 0.80, fill=C_WHITE, border=C_LINE, radius=0.08)
    s.text(
        "ICP: AI startups spending ₹5L–₹1Cr+/mo  |  MOAT: Cross-merchant threat graph",
        0.92,
        5.90,
        11.4,
        0.48,
        size=13.0,
        bold=True,
        font="Consolas",
        color=C_PINE,
        align="center",
        valign="middle",
    )
    s.notes("SLIDE 8: Zero bank charter needed—we run over JIT webhooks from Stripe Issuing/RazorpayX and monetize via interchange, agent SaaS, and issuer licensing.")

    # SLIDE 9 — DARK-PINE EDITORIAL CLOSING
    s = EditorialSlide(prs, 9, "08 / SUMMARY", dark=True)
    s.morph()
    s.text("Protocols teach agents how to pay.\nNumen makes it safe to let them.", 0.65, 1.35, 11.4, 1.50, size=40, bold=True, font="Bahnschrift", color=C_WHITE, spacing=1.10)
    s.text("Layer-2 issuer control plane & 60-second exact-rupee cards.", 0.65, 3.12, 9.8, 0.56, size=17, color=C_CARD_MINT)

    recaps = [
        ("Treasury", "Sub-accounts & Ed25519 caps"),
        ("Pre-Auth", "Blocks injections & ₹36k traps"),
        ("60s Cards", "±₹0.00 lock & auto-shred"),
        ("Business", "Interchange + SaaS + Issuer API"),
    ]
    for i, (rk, rv) in enumerate(recaps):
        rx = 0.65 + i * 3.06
        s.rect(rx, 4.35, 2.86, 1.18, fill=(19, 54, 40), border=(40, 95, 72), border_pt=1.0, radius=0.08)
        s.text(rk.upper(), rx + 0.20, 4.50, 2.46, 0.26, size=10, bold=True, font="Consolas", color=C_CARD_MINT)
        s.text(rv, rx + 0.20, 4.84, 2.46, 0.56, size=13, color=C_WHITE)

    s.text("github.com/tanish19078/numen   ·   http://127.0.0.1:8000", 0.65, 6.08, 11.4, 0.36, size=13.5, bold=True, font="Consolas", color=C_CARD_MINT)
    s.notes("SLIDE 9: Protocols teach agents how to pay. Numen makes it safe to let them.")

    audit_deck(prs)
    prs.save(out_path)
    print(f"Saved revised fintech pitch deck: {out_path}")


if __name__ == "__main__":
    build_deck(r"c:\Users\Tanish Singla\Desktop\proj\deck\Numen_Pitch_Deck.pptx")
