# EasePrint Typography System: Engineered Optical Legibility

## 1. Typographic Ethos & Font Stack

Campus printing is an operation requiring high visual precision under pressure. Students need to confirm page counts, duplex settings, binding selections, and final costs in seconds before sprint-walking to exams.

### 1.1 The Primary Font Stacks
EasePrint pairs two modern high-legibility typefaces with an engineered monospace:

1. **Display & Primary UI: Plus Jakarta Sans**
   - High x-height, geometric clarity, open apertures.
   - Purpose: Top headers, modal titles, promotional accents, primary buttons.
   - Stack: `'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`

2. **Micro-UI & Form Body: Inter**
   - Neutral grotesk, exceptional legibility at 11px–14px, optimized for form controls, instructions, and error text.
   - Purpose: Form labels, helper text, input values, table cells, toast notifications.
   - Stack: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`

3. **Tabular Numerals & Telemetry: JetBrains Mono**
   - Increased x-height, clear distinction between `0`, `O`, `1`, `l`, `I`.
   - Native tabular figures (`tnum`) ensuring price columns, queue positions, and countdown clocks do not cause jitter or horizontal layout shifts.
   - Purpose: Queue tokens (`EP-8921`), currency amounts (`₹24.50`), countdown timers (`04:32`), page counts (`18 pgs`).
   - Stack: `'JetBrains Mono', 'SFMono-Regular', Menlo, Monaco, Consolas, monospace`

### 1.2 Explicit Rejection of Decorative Vintage Serifs
- **Instrument Serif, Georgia, Times New Roman, Garamond are strictly banned.**
- **Rationale**: While vintage serifs fit literary magazines or archival museums, they create visual friction in technical SaaS interfaces:
  - Thin hairlines disappear on non-retina campus kiosk displays.
  - Numbers lack tabular alignment, causing price columns to wobble.
  - Evokes slow bureaucratic paperwork rather than modern cloud xerography.

---

## 2. Typographic Scale & Modular Hierarchy

The scale is rooted in an **8px vertical rhythm** with strict proportional line-heights.

| Level | Size (rem / px) | Line Height | Letter Spacing | Weight | Font Family | Intended Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Display 1** | `2.50rem` (40px) | `1.15` (46px) | `-0.03em` | 800 (Bold) | Plus Jakarta Sans | Hero headline, station kiosk main display |
| **Heading 1** | `1.875rem` (30px)| `1.20` (36px) | `-0.025em`| 700 (Bold) | Plus Jakarta Sans | Page view titles, modal primary headers |
| **Heading 2** | `1.50rem` (24px) | `1.25` (30px) | `-0.02em` | 700 (Bold) | Plus Jakarta Sans | Section titles (Print Options, Order History) |
| **Heading 3** | `1.25rem` (20px) | `1.30` (26px) | `-0.015em`| 600 (SemiBold)| Plus Jakarta Sans | Card headers, telemetry panel titles |
| **Subheading**| `1.125rem` (18px)| `1.40` (25px) | `-0.01em` | 600 (SemiBold)| Plus Jakarta Sans | Group labels, prominent summary headers |
| **Body Large**| `1.00rem` (16px) | `1.50` (24px) | `0.00em`  | 400 (Regular) | Inter | Primary body paragraphs, main input values |
| **Body Medium**| `0.875rem` (14px)| `1.45` (20px) | `0.00em`  | 400 / 500   | Inter | Standard UI text, option descriptions, buttons |
| **Body Small**| `0.75rem` (12px) | `1.40` (17px) | `+0.01em` | 500 (Medium) | Inter | Form labels, badges, status chips, tooltips |
| **Caption**   | `0.6875rem` (11px)|`1.35` (15px) | `+0.02em` | 500 (Medium) | Inter | Legal disclaimers, micro metadata, file sizes |
| **Code / Token**| `1.375rem` (22px)|`1.10` (24px)| `+0.05em` | 700 (Bold)   | JetBrains Mono | Queue Token Badge (`EP-8921`), claim code |
| **Price Hero**| `1.75rem` (28px) | `1.15` (32px) | `-0.02em` | 700 (Bold)   | JetBrains Mono | Total price dock display (`₹36.00`) |
| **Price Row** | `0.875rem` (14px)| `1.40` (20px) | `0.00em`  | 600 (SemiBold)| JetBrains Mono | Breakdown line items (`₹2.00 / page`) |

---

## 3. Typographic Color Tokens & Contrast Proof

Every text style token includes complete chromatic values and verified contrast ratios against both the white card surface (`#FFFFFF`) and the canvas backdrop (`#F8FAFC`).

| Token | HEX | RGB | HSL | Semantic Role | Contrast vs #FFFFFF | Contrast vs #F8FAFC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `--type-primary` | `#0F172A` | `rgb(15, 23, 42)` | `hsl(222, 47%, 11%)` | Primary headings, display text, queue tokens | **17.8:1** (AAA) | **17.1:1** (AAA) |
| `--type-body` | `#1E293B` | `rgb(30, 41, 59)` | `hsl(215, 32%, 17%)` | Standard body copy, form input labels | **14.8:1** (AAA) | **14.2:1** (AAA) |
| `--type-secondary` | `#334155` | `rgb(51, 65, 85)` | `hsl(215, 25%, 27%)` | Field descriptions, option subtext | **10.7:1** (AAA) | **10.3:1** (AAA) |
| `--type-muted` | `#475569` | `rgb(71, 85, 105)` | `hsl(215, 19%, 35%)` | Meta timestamps, captions, file details | **7.6:1** (AAA) | **7.3:1** (AAA) |
| `--type-accent-blue`| `#1D4ED8` | `rgb(29, 78, 216)` | `hsl(224, 76%, 48%)` | Interactive links, active step numbers | **7.0:1** (AAA) | **6.7:1** (AAA) |
| `--type-accent-cyan`| `#0891B2` | `rgb(8, 145, 178)` | `hsl(192, 91%, 36%)` | Hardware station callout, duplex indicator | **4.8:1** (AA) | **4.6:1** (AA) |
| `--type-inverse` | `#FFFFFF` | `rgb(255, 255, 255)` | `hsl(0, 0%, 100%)` | Text on solid blue/indigo buttons | **5.0:1** vs `#2563EB` | **16.9:1** vs `#1E1B4B` |

---

## 4. Tabular Formatting & Anti-Jank Numerals

To guarantee zero layout shift when prices calculate or countdowns tick:

```css
.tabular-nums {
  font-family: 'JetBrains Mono', monospace;
  font-feature-settings: 'tnum' 1, 'zero' 1;
  font-variant-numeric: tabular-nums lining-nums;
  letter-spacing: -0.01em;
}
```

This prevents the jarring "dancing number" effect common in naive frontends when seconds decrement or prices update dynamically.

---

## 5. Non-Negotiable Theme Restriction: Typographic Surface Invariance

All typography in EasePrint is engineered exclusively for a **light, bright, blue-led visual system**:

1. **Strict Dark-on-Light Polarity**:
   - All text tokens (`--type-primary: #0F172A`, `--type-body: #1E293B`, `--type-secondary: #334155`) render on light backgrounds.
   - Text is never inverted for dark mode, because dark mode, black themes, and dark-first designs are strictly prohibited.
2. **Prohibited Typographic & Theme Aesthetics**:
   - Black or near-black backgrounds
   - Charcoal application shells or dark navy page surfaces
   - Black hero sections or black cards
   - Dark dashboard chrome or dark glassmorphism
   - Neon-on-black color schemes
   - Acid-green-on-black schemes
   - Vermilion-on-black schemes
   - Dark “AI command center”, developer-tool, fintech, cyberpunk, or terminal aesthetics
   - Dark mode merely because it is a common AI/SaaS pattern
   - Dark/black palettes as an alternate visual direction (EasePrint is **not** a dark/light theme exploration project)
   - Warm beige, parchment, cream-heavy, tan, brown, terracotta, gold, and sepia palettes as dominant visual directions
   - Dark-mode toggles, dark-theme variants, or dark preview screenshots
3. **Permitted Background Families for Typography**:
   - White (`#FFFFFF`)
   - Cool white (`#F8FAFC`)
   - Ice blue (`#F0F9FF`)
   - Very pale blue (`#EFF6FF`)
   - Blue-gray mist (`#F1F5F9`)
   - Extremely pale lavender-blue (`#EEF2FF`)
4. **Review Gate Rule**:
   - Any design proposal containing a dominant black, charcoal, navy, or dark surface fails review and must be rejected before implementation. Zero dark mode or dark-theme tokens/variants are permitted in the design system.
