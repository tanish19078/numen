# Numen Design System (`DESIGN.md`)

> Canonical visual specification shared across the React Treasury Console, `.pptx` Pitch Deck, and 16:9 HTML Keynote.

## 1. Aesthetic Direction
**Calm Institutional Neobank meets High-Clarity Security Control Plane.**
Inspired by Mercury, Wise Business, and Stripe Dashboard — bright porcelain-alabaster surfaces, deep pine inks, refined emerald accents, zero visual noise, and strict tabular numerals.

## 2. Canonical Color Palette

| Role | Token | Hex | RGB |
| :--- | :--- | :--- | :--- |
| Global Canvas | `canvas` | `#F7FAF8` | `247, 250, 248` |
| Primary Card Surface | `surface` | `#FFFFFF` | `255, 255, 255` |
| Nested Well / Subtle Fill | `subtle` | `#F1F6F3` | `241, 246, 243` |
| Hairline Border | `line` | `#E2EBE5` | `226, 235, 229` |
| Deep Pine Ink | `pine` | `#0B1F16` | `11, 31, 22` |
| Muted Sage Ink | `sage` | `#526B5D` | `82, 107, 93` |
| Faint Stone / Axis Ink | `stone` | `#849B8E` | `132, 155, 142` |
| Emerald Primary | `emerald` | `#059669` | `5, 150, 105` |
| Mint Wash (Soft Verified) | `mint-wash` | `#ECFDF5` | `236, 253, 245` |
| Dark Pine Metallic Card | `card-pine` | `#0D261C` | `13, 38, 28` |
| Soft Silver-Mint on Dark | `card-mint` | `#6EE7B7` | `110, 231, 183` |
| Crimson Threat / Block | `threat` | `#DC2626` | `220, 38, 38` |
| Crimson Tint | `threat-wash` | `#FEF2F2` | `254, 242, 242` |
| Amber Review / Trap | `review` | `#D97706` | `217, 119, 6` |
| Amber Tint | `review-wash` | `#FFFBEB` | `255, 251, 235` |
| Cobalt Protocol Accent | `cobalt` | `#2563EB` | `37, 99, 235` |
| Cobalt Tint | `cobalt-wash` | `#EFF6FF` | `239, 246, 255` |

## 3. Typography
- **Display & Body (`font-sans`)**: `"Plus Jakarta Sans"`, fallback `system-ui, sans-serif` (Web); `"Segoe UI"` / `"Bahnschrift"` (PPTX fallback).
- **Technical / Financial Data (`font-mono`)**: `"JetBrains Mono"`, fallback `"Consolas", monospace` (with `font-variant-numeric: tabular-nums` enforced on all INR amounts, card numbers, timestamps, and drift scores).

## 4. Layout & Surface Rules
- Borders are crisp `1px solid #E2EBE5` (never heavy 2px neon frames).
- Cards use `16px` (`rounded-2xl`) radius in web UI and `0.06` corner radius ratio in `.pptx`.
- Virtual card credentials use brushed Dark Pine `#0D261C` metallic surface for contrast and scannability.
- Presentations maintain >= 35% whitespace, <= 60 body words/slide, and >= 13pt body typography.
