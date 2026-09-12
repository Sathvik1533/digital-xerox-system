# EasePrint Comprehensive Design System Specification

## 1. Spatial Foundation: The 4px/8px Geometric Grid

EasePrint is built on a rigid **4px base unit with an 8px macro grid**. Every padding, margin, height, gap, and radius is an integer multiple of 4px.

### 1.1 Spatial Tokens

| Token Name | Value | Rem Equivalent | Primary Application |
| :--- | :--- | :--- | :--- |
| `--space-1` | `4px` | `0.25rem` | Micro padding, icon-text gap, border offset |
| `--space-2` | `8px` | `0.50rem` | Tight tag padding, input inner vertical padding |
| `--space-3` | `12px` | `0.75rem` | Standard input inner horizontal padding, badge gap |
| `--space-4` | `16px` | `1.00rem` | Default card inner padding, grid gap on mobile |
| `--space-5` | `20px` | `1.25rem` | Card header separation, modal inner gutters |
| `--space-6` | `24px` | `1.50rem` | Section padding, desktop grid gutters |
| `--space-8` | `32px` | `2.00rem` | Major card padding, modal content wrapper |
| `--space-10` | `40px` | `2.50rem` | View section vertical rhythm |
| `--space-12` | `48px` | `3.00rem` | Top navigation bar height, primary hero spacing |

---

## 2. Corner Radius & Tactile Elevation

EasePrint balances modern precision with subtle tactile ergonomics:

### 2.1 Radius Tokens
- `--radius-xs: 4px` — Micro chips, sub-tags, table badges.
- `--radius-sm: 6px` — Form inputs, dropdown items, segmented toggle buttons.
- `--radius-md: 10px` — Standard surface cards, upload dropzone.
- `--radius-lg: 14px` — Modal sheets, sticky price dock, queue ticket card.
- `--radius-full: 9999px` — Circular status avatars, pill indicators, counter chips.

### 2.2 Elevation & Shadow Hierarchy
Shadows are tinted with deep aerospace navy (`#0F172A`) rather than harsh neutral black, creating organic, diffused depth:

| Elevation Level | CSS Box Shadow Token | Visual Depth Purpose |
| :--- | :--- | :--- |
| **Level 0 (Flat)** | `none` | Inset wells, table rows, inactive cards |
| **Level 1 (Card)** | `0 1px 3px rgba(15, 23, 42, 0.05), 0 1px 2px rgba(15, 23, 42, 0.03)` | Resting surface cards, upload container |
| **Level 2 (Hover)**| `0 4px 12px -2px rgba(15, 23, 42, 0.08), 0 2px 6px -1px rgba(15, 23, 42, 0.04)`| Interactive cards on hover, active option pill |
| **Level 3 (Dock)** | `0 10px 25px -5px rgba(15, 23, 42, 0.10), 0 8px 10px -6px rgba(15, 23, 42, 0.05)`| Sticky price dock, floating action banner |
| **Level 4 (Modal)**| `0 25px 50px -12px rgba(15, 23, 42, 0.20), 0 0 0 1px rgba(15, 23, 42, 0.05)` | Queue ticket modal, simulated payment sheet |

---

## 3. Layout Architecture: The 3-Column Campus Cockpit

To enable rapid 30-second order completion, EasePrint eliminates multi-step wizards on desktop in favor of a cohesive **3-Column Cockpit Layout**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ EASEPRINT HEADER: Campus Location (Station B3) • Wallet: ₹142.50 • Nav Links│
├──────────────────────┬───────────────────────────────┬──────────────────────┤
│ COLUMN 1: SOURCE     │ COLUMN 2: SPECIFICATION       │ COLUMN 3: EXECUTION  │
│ (Width: 320px)       │ (Width: Flexible 1fr)         │ (Width: 340px Sticky)│
│                      │                               │                      │
│ ┌──────────────────┐ │ ┌───────────────────────────┐ │ ┌──────────────────┐ │
│ │ Drag & Drop PDF  │ │ │ Print Mode: B&W / Color   │ │ │ Price Estimator  │ │
│ │ Dropzone         │ │ │ (Segmented Pill Switcher) │ │ │ Subtotal: ₹18.00 │ │
│ ├──────────────────┤ │ ├───────────────────────────┤ │ │ Binding:  ₹10.00 │ │
│ │ Document Preview │ │ │ Duplex: Single / 2-Sided  │ │ │ Total:    ₹28.00 │ │
│ │ • 14 Pages       │ │ ├───────────────────────────┤ │ ├──────────────────┤ │
│ │ • A4 Portrait    │ │ │ Paper: 75 GSM / 100 GSM   │ │ │ [Pay & Submit]   │ │
│ │ • PDF 2.4 MB     │ │ ├───────────────────────────┤ │ ├──────────────────┤ │
│ └──────────────────┘ │ │ Binding: None/Staple/Spiral │ │ │ Station B3 State │ │
│                      │ └───────────────────────────┘ │ │ Queue: 2 Jobs (4m)│ │
│                      │                               │ └──────────────────┘ │
└──────────────────────┴───────────────────────────────┴──────────────────────┘
```

---

## 4. UI Component Architecture & Tokenized Primitives

### 4.1 Buttons & Interactive Controls

| Variant | Resting Style | Hover / Focus Style | Semantic Use Case |
| :--- | :--- | :--- | :--- |
| **Primary Action** | Background: `--brand-blue` (`#2563EB`)<br>Text: `#FFFFFF`<br>Shadow: `0 2px 4px rgba(37,99,235,0.2)` | Background: `--brand-blue-hover` (`#1D4ED8`)<br>Transform: `translateY(-1px)`<br>Ring: `2px solid #0284C7` | Primary order submission, payment confirmation |
| **Secondary Neutral**| Background: `#FFFFFF`<br>Border: `1px solid #CBD5E1`<br>Text: `#0F172A` | Background: `#F8FAFC`<br>Border: `1px solid #94A3B8` | Re-order button, cancel order, print test page |
| **Segmented Pill** | Inactive: `#F1F5F9`, text `#334155`<br>Active: `#2563EB`, text `#FFFFFF` | Slide indicator transition `180ms ease` | Color vs B&W, Duplex vs Simplex, Paper Size |
| **Danger Ghost** | Background: `transparent`<br>Text: `#DC2626` | Background: `#FEF2F2`<br>Text: `#991B1B` | Delete uploaded file, abandon draft order |

### 4.2 Form Inputs & Interactive Wells
- **Border**: `1px solid var(--border-medium)` (`#CBD5E1`).
- **Focus**: `outline: none; border-color: var(--brand-sky); box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.15);`.
- **Background**: `#FFFFFF` with resting placeholder `#64748B` (4.77:1 contrast).

---

## 5. Non-Negotiable Theme Restriction: Strict Light & Blue-Led Foundation

EasePrint must use a light, bright, blue-led visual system. Do not create a dark theme, black theme, or dark-first design.

### 5.1 Prohibited Shell & Surface Styles
Do **NOT** use:
- Black backgrounds or near-black backgrounds
- Charcoal application shells
- Dark navy as the dominant page surface
- Black hero sections or black cards
- Dark dashboard chrome or dark glassmorphism
- Neon-on-black, acid-green-on-black, or vermilion-on-black schemes
- Dark “AI command center” aesthetics
- Dark developer-tool aesthetics
- Dark fintech aesthetics
- Dark cyberpunk aesthetics
- Dark terminal aesthetics
- Dark mode merely because it is a common AI/SaaS pattern
- Dark or black palettes as an alternate visual direction (EasePrint is not a dark/light theme exploration project)
- Warm beige, parchment, cream-heavy, tan, brown, terracotta, gold, and sepia palettes as dominant visual directions
- Dark-mode toggles or theme switchers
- Dark-theme variants in previews or design tokens
- Dark preview screenshots or mocks

### 5.2 Required Aesthetic Foundation
The final design must remain:
- **Light** and **Bright**
- **Blue-led** (Primary Blue `#2563EB`, Sky Blue `#0284C7`)
- **Cyan-accented** (`#06B6D4`)
- **Indigo-supported** (`#1E1B4B`, `#4F46E5` strictly for high-contrast borders, text, and micro-accents)
- **Violet-accented only where useful** (`#6366F1`)
- **White or cool-white based**
- **Clear, Premium, Energetic, Trustworthy, Campus-technology oriented**

### 5.3 Permitted Background Families
Only the following background families are permitted:
- White (`#FFFFFF`)
- Cool white (`#F8FAFC`)
- Ice blue (`#F0F9FF`)
- Very pale blue (`#EFF6FF`)
- Blue-gray mist (`#F1F5F9`)
- Extremely pale lavender-blue (`#EEF2FF`)

**Review Gate Rule**: Any design proposal containing a dominant black, charcoal, navy, or dark surface fails review and must be rejected before implementation. Zero dark mode or dark-theme tokens/variants are permitted in the design system.
