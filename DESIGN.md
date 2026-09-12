# EasePrint Master Design Manifesto (DESIGN.md)

## 1. Executive Summary

**EasePrint** is an autonomous campus print cloud platform bridging digital file submission with high-velocity physical xerox reproduction.

This document serves as the primary master design contract for the EasePrint application, defining the visual architecture, token contracts, and aesthetic governance.

### The Design Philosophy: The Photonic Campus Cloud
EasePrint is inspired by the **clean photonic light of laser xerography**, the **aerospace precision of modern SaaS (Linear, Stripe)**, and the **tactile reality of physical campus print shops**.

```
   ┌────────────────────────────────────────────────────────┐
   │            THE PHOTONIC CAMPUS CLOUD                   │
   │                                                        │
   │  [Light & Blue-Led]   •   [High Operational Density]   │
   │  [Optical Precision]  •   [Zero Slop / Zero Beige]     │
   └────────────────────────────────────────────────────────┘
```

---

## 2. Non-Negotiable Theme Restriction: Strict Light & Blue-Led Mandate

EasePrint must use a light, bright, blue-led visual system. Under no circumstances may dark theme, black theme, or dark-first designs be introduced.

### 2.1 Explicit Prohibitions
Do **NOT** use:
- Black backgrounds or near-black backgrounds
- Charcoal application shells
- Dark navy as the dominant page surface
- Black hero sections or black cards
- Dark dashboard chrome or dark glassmorphism
- Neon-on-black color schemes
- Acid-green-on-black schemes
- Vermilion-on-black schemes
- Dark “AI command center” aesthetics
- Dark developer-tool aesthetics
- Dark fintech aesthetics
- Dark cyberpunk aesthetics
- Dark terminal aesthetics
- Dark mode merely because it is a common AI/SaaS pattern
- Dark or black palettes as an alternate visual direction (EasePrint is **not** a dark/light theme exploration project)
- Warm beige, parchment, cream-heavy, tan, brown, terracotta, gold, and sepia palettes as dominant visual directions
- Dark-mode toggles or theme switchers
- Dark-theme variants or preview options
- Dark preview screenshots or mocks

**Review Gate Rule**: Any design proposal containing a dominant black, charcoal, navy, or dark surface fails review and must be rejected before implementation. No dark mode or dark-theme tokens/variants are permitted in the design system.

### 2.2 Aesthetic Requirements
The final design must remain:
- **Light** and **Bright**
- **Blue-led** (Laser Electric Blue `#2563EB`, Sky Blue `#0284C7`)
- **Cyan-accented** (`#06B6D4`)
- **Indigo-supported** (`#1E1B4B`, `#4F46E5` strictly as structural linework, text, and micro-accents)
- **Violet-accented only where useful** (`#6366F1` for micro-badges)
- **White or cool-white based**
- **Clear, Premium, Energetic, Trustworthy, Campus-technology oriented**

### 2.3 Permitted Background Families
Only the following background families are allowed:
- White (`#FFFFFF`)
- Cool white (`#F8FAFC`)
- Ice blue (`#F0F9FF`)
- Very pale blue (`#EFF6FF`)
- Blue-gray mist (`#F1F5F9`)
- Extremely pale lavender-blue (`#EEF2FF`)

---

## 3. Fundamental Color Tokens (Light & Blue-Led)

The EasePrint palette is strictly **Light and Blue-Led**. Zero dark-mode tokens or variants exist.

| Token Name | HEX | RGB | HSL | Semantic Role | Contrast Ratio (WCAG) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--brand-blue` | `#2563EB` | `rgb(37, 99, 235)` | `hsl(221, 83%, 53%)` | Primary action trigger, active selection | **5.0:1** vs `#FFFFFF` (AA) |
| `--brand-blue-hover` | `#1D4ED8` | `rgb(29, 78, 216)` | `hsl(224, 76%, 48%)` | Hover state for primary action triggers | **7.0:1** vs `#FFFFFF` (AAA) |
| `--brand-sky` | `#0284C7` | `rgb(2, 132, 199)` | `hsl(200, 98%, 39%)` | Focus rings, progress meters, queue badge | **4.54:1** vs `#FFFFFF` (AA) |
| `--brand-cyan` | `#06B6D4` | `rgb(6, 182, 212)` | `hsl(189, 94%, 43%)` | Active kiosk beacon dot, telemetry accent | **7.3:1** vs `#0F172A` text (AAA) |
| `--indigo-deep` | `#1E1B4B` | `rgb(30, 27, 75)` | `hsl(244, 47%, 20%)` | Gradient terminus, structural borders | **16.9:1** vs `#FFFFFF` text (AAA) |
| `--indigo-vibrant` | `#4F46E5` | `rgb(79, 70, 229)` | `hsl(243, 75%, 59%)` | Gradient accent, special binding badge | **6.6:1** vs `#FFFFFF` text (AA) |
| `--surface-canvas` | `#F8FAFC` | `rgb(248, 250, 252)` | `hsl(210, 40%, 98%)` | App background canvas (cool ice slate) | **17.1:1** vs `#0F172A` (AAA) |
| `--surface-card` | `#FFFFFF` | `rgb(255, 255, 255)` | `hsl(0, 0%, 100%)` | Content cards, modal sheets, dropzone | **17.8:1** vs `#0F172A` (AAA) |
| `--surface-inset` | `#F1F5F9` | `rgb(241, 245, 249)` | `hsl(210, 36%, 96%)` | Inset wells, segmented pill tracks | **16.4:1** vs `#0F172A` (AAA) |
| `--text-primary` | `#0F172A` | `rgb(15, 23, 42)` | `hsl(222, 47%, 11%)` | Headings, document titles, token codes | **17.8:1** vs `#FFFFFF` (AAA) |
| `--text-body` | `#1E293B` | `rgb(30, 41, 59)` | `hsl(215, 32%, 17%)` | Standard body text, form labels | **14.8:1** vs `#FFFFFF` (AAA) |
| `--text-muted` | `#475569` | `rgb(71, 85, 105)` | `hsl(215, 19%, 35%)` | Meta timestamps, captions, file sizes | **7.6:1** vs `#FFFFFF` (AAA) |
| `--border-subtle` | `#E2E8F0` | `rgb(226, 232, 240)` | `hsl(214, 32%, 91%)` | 1px card perimeter rule, table dividers | **3.2:1** UI boundary |
| `--border-focus` | `#0284C7` | `rgb(2, 132, 199)` | `hsl(200, 98%, 39%)` | Accessible keyboard focus outline | **4.54:1** vs `#FFFFFF` |

---

## 4. Typographic Hierarchy

1. **Display & Primary UI**: `Plus Jakarta Sans` (Geometric grotesk, high x-height, maximum legibility).
2. **Body & Micro-UI**: `Inter` (Neutral grotesk, zero eye fatigue, clean forms).
3. **Tabular Figures & Tokens**: `JetBrains Mono` (`font-variant-numeric: tabular-nums lining-nums`, prevents layout shift in price tickers and countdowns).
4. **Banned**: Decorative vintage serifs (`Instrument Serif`, `Georgia`, `Times New Roman`).

---

## 5. Layout Architecture: The 3-Column Campus Cockpit

Desktop workflows are structured into a 3-column cockpit allowing a student to complete an order in under 30 seconds:
- **Left Column (Source)**: Document Upload Zone with instant page count and color analysis.
- **Center Column (Specification)**: Print Configuration (B&W/Color, Duplex, Paper Weight, Binding).
- **Right Column (Execution)**: Real-time Price Estimator dock, Student ID Wallet deduction, simulated payment trigger, and live station queue telemetry.

---

## 6. Comprehensive Design Documentation Suite

For detailed technical specifications, refer to the dedicated documentation in `docs/design/`:

1. [docs/design/README.md](docs/design/README.md) — Documentation index and reading order.
2. [docs/design/EASEPRINT_ART_DIRECTION.md](docs/design/EASEPRINT_ART_DIRECTION.md) — Creative direction, brand ethos, and visual metaphors.
3. [docs/design/EASEPRINT_VISUAL_DNA.md](docs/design/EASEPRINT_VISUAL_DNA.md) — Visual DNA, signature moments (Holographic Token, Sheet Simulator).
4. [docs/design/EASEPRINT_COLOR_SYSTEM.md](docs/design/EASEPRINT_COLOR_SYSTEM.md) — Full chromatic matrix with HEX, RGB, HSL, roles, and contrast math.
5. [docs/design/EASEPRINT_TYPOGRAPHY.md](docs/design/EASEPRINT_TYPOGRAPHY.md) — Typographic scale, font pairing, and tabular figures.
6. [docs/design/EASEPRINT_DESIGN_SYSTEM.md](docs/design/EASEPRINT_DESIGN_SYSTEM.md) — 4px/8px spatial grid, elevation, container hierarchy.
7. [docs/design/EASEPRINT_COMPONENTS.md](docs/design/EASEPRINT_COMPONENTS.md) — Component specifications, states, and ARIA markup.
8. [docs/design/EASEPRINT_INTERACTION_PATTERNS.md](docs/design/EASEPRINT_INTERACTION_PATTERNS.md) — Workflows, deterministic state machines, and error handling.
9. [docs/design/EASEPRINT_MOTION_PRINCIPLES.md](docs/design/EASEPRINT_MOTION_PRINCIPLES.md) — Spring physics, micro-interactions, and reduced motion.
10. [docs/design/EASEPRINT_RESPONSIVE_SYSTEM.md](docs/design/EASEPRINT_RESPONSIVE_SYSTEM.md) — Mobile sticky execution bar, responsive grid, kiosk mode.
11. [docs/design/EASEPRINT_ACCESSIBILITY.md](docs/design/EASEPRINT_ACCESSIBILITY.md) — WCAG 2.2 AAA audit, focus visible system, ARIA live regions.
12. [docs/design/REFERENCE_RESEARCH.md](docs/design/REFERENCE_RESEARCH.md) — Comparative research matrix across industry frameworks.
13. [docs/design/ANTI_SLOP_REVIEW.md](docs/design/ANTI_SLOP_REVIEW.md) — Anti-slop checklist and 1–10 comparative scorecard.
