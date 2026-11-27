---
name: frontend-design
description: >-
  Editorial fintech & neobank UI design system rules synthesized from Anthropic frontend-design,
  Impeccable craft audits, and UI/UX Pro Max fintech constraints. Use when building or redesigning
  React/Tailwind banking, treasury, or security interfaces.
---

# Frontend Design Craft & Neobank Anti-Slop Standard

Always read [DESIGN.md](../../../DESIGN.md) at the workspace root before writing UI components or CSS.

## 1. Anti-Slop Bans (Zero Tolerance)
- **No default system fonts** (`Segoe UI`, `Arial`, `Inter`) when editorial fintech typefaces (`Plus Jakarta Sans` + `JetBrains Mono`) are available.
- **No radioactive neon borders/fills** (`#8CE563` 2px outlines or bright green boxes across every card). Reserve saturated emerald (`#059669`) and forest mint (`#0D261C`) strictly for active states, primary actions, and verified settlement badges.
- **No cyberpunk/AI-slop dotted matrix backgrounds** or glowing neon drop-shadows. Use calm porcelain/alabaster surfaces (`#F7FAF8`) and `1px solid #E2EBE5` hairline borders.
- **No rainbow badge overload**: Maximum 2 status accent hues visible within any single card.
- **No single-screen cramming**: Group workflows into clean left-rail navigation views so each route has 1 primary job and >= 30% breathing room.

## 2. Neobank Layout & Hierarchy Rules
1. **Persistent Left Rail (`256px`)**: Houses brand identity, live treasury balance summary, route links, engine mode pill, and demo reset control.
2. **Tabular Numerals**: Apply `tabular-nums` (`font-variant-numeric: tabular-nums`) on all currency amounts (`₹`), Luhn PAN digits, drift scores, latencies (`ms`), and timestamps.
3. **Calm Surface Stack**:
   - Canvas: `#F7FAF8`
   - Card surface: `#FFFFFF` with `border: 1px solid #E2EBE5`, `border-radius: 16px`, and featherweight shadow (`0 1px 3px rgba(11, 31, 22, 0.04)`).
   - Brushed Dark-Pine Virtual Card: `#0D261C` -> `#14392A` gradient surface with crisp silver/mint typography.
4. **Progressive Disclosure**: Keep high-density forensic traces (raw A2A hops, raw JSON envelopes, CaMeL capability matrices) inside clean expandable accordions so decision clarity hits in under 3 seconds.

## 3. Verification Loop
After any UI change:
1. Run `npm run build` in `frontend/` and ensure zero warnings/errors.
2. Inspect [references/neobank-tokens.md](./references/neobank-tokens.md) to verify token consistency across components.
