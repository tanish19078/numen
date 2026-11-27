---
name: pitch-deck-design
description: >-
  Investor & hackathon keynote deck craft rules synthesized from Anthropic pptx skill and
  frontend-slides 16:9 presentation standards. Use when generating or auditing .pptx decks
  or standalone HTML slide decks.
---

# Pitch Deck & 16:9 Presentation Craft Standard

Read [DESIGN.md](../../../DESIGN.md) and [references/layout-archetypes.md](./references/layout-archetypes.md) before modifying `scripts/build_pitch_deck.py` or `deck/Numen_Keynote_Live.html`.

## 1. Non-Negotiable Slide Rules
1. **Assertion-Evidence Headlines**: Every slide title states the takeaway insight in plain English (24pt–28pt bold), not a generic label.
2. **Word-Count Cap**: Strictly **<= 60 body words per slide** (excluding eyebrow and footer number). If a bullet wraps past 2 lines, cut words—never shrink the font below **13pt**.
3. **Zero Fake Chrome**: Never put a multi-tab web app navbar inside a slide header. Use only a quiet top-left eyebrow (`01 / THE SHIFT`) and quiet bottom-right slide number (`01 / 09`).
4. **Layout Variety**: Two consecutive slides MUST NEVER share the same card-grid structure. Alternate between typographic strips, flowcharts, comparisons, tables, storyboards, and contrast dark slides.
5. **Visual Breathing Room**: Keep >= 35% open alabaster whitespace (`#F7FAF8`) across slides.

## 2. Fixed 16:9 HTML Keynote Standard
- Render inside a fixed **`1920x1080` logical stage** scaled uniformly via CSS transform (`scale(min(vw/1920, vh/1080))`) so slides never clip or scroll on any monitor or projector.
- Support `ArrowRight` / `ArrowLeft` / `Space` / click navigation and display crisp slide counter dots.

## 3. Automated Bounds & Density Verification
Every Python `.pptx` build script must run a post-generation audit asserting:
- No shape extends outside safe canvas bounds (`0.35" <= x`, `x + w <= 12.98"`, `0.25" <= y`, `y + h <= 7.25"` for `13.333" x 7.5"` widescreen slides).
- Reports per-slide word counts and flags any slide exceeding 75 total words.
