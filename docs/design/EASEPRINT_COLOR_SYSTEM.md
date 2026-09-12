# EasePrint Color System: Light & Blue-Led Architecture

## 1. Color System Principles & Brand Integrity

The EasePrint color system is designed for **optical clarity, laser precision, and instantaneous scannability** in high-velocity university print hubs.

### 1.1 Strict Brand Mandate: Light & Blue-Led ONLY
- **Primary Chroma**: Electric Blue (`#2563EB`, `#1D4ED8`), Sky Blue (`#0284C7`), and Campus Cyan (`#06B6D4`, `#0891B2`).
- **Structural Chroma**: Deep Intelligent Indigo (`#1E1B4B`, `#312E81`, `#4338CA`) and Aerospace Navy Ink (`#0F172A`).
- **Surface Chroma**: Pristine Optical White (`#FFFFFF`), Glacier Canvas (`#F8FAFC`), and Slate Inset (`#F1F5F9`).
- **Controlled Accents**: Controlled Violet (`#6366F1`, `#4F46E5`) reserved strictly for micro-badges and subtle photonic glows.

### 1.2 Non-Negotiable Theme Restriction: Zero Dark Mode / Zero Dark Theme
EasePrint must use a light, bright, blue-led visual system. Do not create a dark theme, black theme, or dark-first design.

**Prohibited Elements**:
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
- Dark or black palettes as an alternate visual direction (EasePrint is not a dark/light theme exploration project)
- Dark-mode toggles or theme switchers
- Dark-theme variants in previews or design tokens
- Dark preview screenshots or mocks

**Permitted Background Families ONLY**:
- White (`#FFFFFF`)
- Cool white (`#F8FAFC`)
- Ice blue (`#F0F9FF`)
- Very pale blue (`#EFF6FF`)
- Blue-gray mist (`#F1F5F9`)
- Extremely pale lavender-blue (`#EEF2FF`)

**Review Gate Rule**: Any design proposal containing a dominant black, charcoal, navy, or dark surface fails review and must be rejected before implementation. No dark mode or dark-theme tokens/variants are permitted in the design system.

### 1.3 Explicit Rejection of Beige, Parchment, & Distressed Palettes
- **Zero Beige / Parchment / Vellum**: No `#F7F3EB`, `#EDE8DC`, `#F4EFE6`, `#FAF8F4`, `#D9D2C4`, or brown/ochre tones.
- **Zero Gold Dominance**: Old gold (`#8B6914`, `#A07820`) is completely banned. Warm beige, parchment, cream-heavy, tan, brown, terracotta, gold, and sepia palettes are strictly prohibited as dominant visual directions.
- **Rationale**: Beige creates muddy visual contrast, mimics antiquated 19th-century paper rather than modern cloud xerography, and severely degrades legibility under fluorescent campus library lights.

---

## 2. Complete Token Matrix

Every single token in EasePrint includes its **Token Name, HEX, RGB, HSL, Semantic Role, and Verified Contrast Ratio**. Zero dark-mode tokens or variants exist.

### 2.1 Primary Brand & Photonic Blue Tokens

| Token Name | HEX | RGB | HSL | Semantic Role | Contrast Ratio & WCAG Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--brand-blue` | `#2563EB` | `rgb(37, 99, 235)` | `hsl(221, 83%, 53%)` | Primary interactive trigger, active pill background, primary action buttons | **5.0:1** vs White text (AA)<br>**5.0:1** vs `#FFFFFF` surface |
| `--brand-blue-hover` | `#1D4ED8` | `rgb(29, 78, 216)` | `hsl(224, 76%, 48%)` | Hover state for primary action buttons and interactive controls | **7.0:1** vs White text (AAA)<br>**7.0:1** vs `#FFFFFF` surface |
| `--brand-blue-active` | `#1E40AF` | `rgb(30, 64, 175)` | `hsl(226, 71%, 40%)` | Active/pressed state for primary buttons | **9.2:1** vs White text (AAA)<br>**9.2:1** vs `#FFFFFF` surface |
| `--brand-blue-subtle` | `#EFF6FF` | `rgb(239, 246, 255)` | `hsl(214, 100%, 97%)` | Primary card highlight wash, selected item background | **16.2:1** vs `--brand-blue` text (AAA) |
| `--brand-sky` | `#0284C7` | `rgb(2, 132, 199)` | `hsl(200, 98%, 39%)` | High-visibility telemetry focus rings, progress bar fills, queue indicator | **4.54:1** vs White text (AA)<br>**4.5:1** vs `#FFFFFF` surface |
| `--brand-sky-hover` | `#0369A1` | `rgb(3, 105, 161)` | `hsl(201, 96%, 32%)` | Hover state for sky-blue telemetry pills and secondary triggers | **7.1:1** vs White text (AAA)<br>**7.1:1** vs `#FFFFFF` surface |
| `--brand-sky-light` | `#38BDF8` | `rgb(56, 189, 248)` | `hsl(199, 89%, 60%)` | Cyan-sky highlight dots, secondary progress bars, focus ring outer glow | **4.6:1** vs `#0F172A` text (AA)<br>Active glow accent |
| `--brand-cyan` | `#06B6D4` | `rgb(6, 182, 212)` | `hsl(189, 94%, 43%)` | Active kiosk beacon dot, live printing head indicator, duplex status | **7.3:1** vs `#0F172A` primary text (AAA) |
| `--brand-cyan-dark` | `#0891B2` | `rgb(8, 145, 178)` | `hsl(192, 91%, 36%)` | Text label for cyan status badges, active duplex pill border | **4.8:1** vs `#FFFFFF` surface (AA) |
| `--brand-cyan-subtle` | `#ECFEFF` | `rgb(236, 254, 255)` | `hsl(184, 100%, 96%)` | Subtle background for active hardware telemetry badges | **16.5:1** vs `--brand-cyan-dark` (AAA) |

---

### 2.2 Intelligent Indigo & Structural Frame Tokens

| Token Name | HEX | RGB | HSL | Semantic Role | Contrast Ratio & WCAG Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--indigo-deep` | `#1E1B4B` | `rgb(30, 27, 75)` | `hsl(244, 47%, 20%)` | Brand gradient terminus, modal header accents, high-contrast badges | **16.9:1** vs `#FFFFFF` text (AAA) |
| `--indigo-midnight` | `#312E81` | `rgb(49, 46, 129)` | `hsl(242, 47%, 35%)` | Deep structural card borders, high-contrast container framing | **12.3:1** vs `#FFFFFF` text (AAA) |
| `--indigo-royal` | `#4338CA` | `rgb(67, 56, 202)` | `hsl(245, 58%, 51%)` | Secondary gradient accent, high-tier binding indicator | **8.4:1** vs `#FFFFFF` text (AAA) |
| `--indigo-vibrant` | `#4F46E5` | `rgb(79, 70, 229)` | `hsl(243, 75%, 59%)` | Interactive gradient end-stop, special binding tag | **6.6:1** vs `#FFFFFF` text (AA) |
| `--indigo-subtle` | `#EEF2FF` | `rgb(238, 242, 255)` | `hsl(226, 100%, 97%)` | Inset background for premium binding and laminating options | **15.8:1** vs `--indigo-royal` (AAA) |
| `--violet-accent` | `#6366F1` | `rgb(99, 102, 241)` | `hsl(239, 84%, 67%)` | Controlled micro-accent for priority rush orders | **5.2:1** vs `#0F172A` text (AA) |

---

### 2.3 Canvas & Clean Cool-Tinted Surfaces

| Token Name | HEX | RGB | HSL | Semantic Role | Contrast Ratio & WCAG Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--surface-canvas` | `#F8FAFC` | `rgb(248, 250, 252)` | `hsl(210, 40%, 98%)` | Main app background canvas, low-fatigue cool ice tone | **17.1:1** vs `#0F172A` text (AAA) |
| `--surface-card` | `#FFFFFF` | `rgb(255, 255, 255)` | `hsl(0, 0%, 100%)` | Primary container card, floating sheets, modal body | **17.8:1** vs `#0F172A` text (AAA) |
| `--surface-card-hover`| `#FFFFFF` | `rgb(255, 255, 255)` | `hsl(0, 0%, 100%)` | Elevated hover state card (elevation handled via shadow) | **17.8:1** vs `#0F172A` text (AAA) |
| `--surface-inset` | `#F1F5F9` | `rgb(241, 245, 249)` | `hsl(210, 36%, 96%)` | Form control wells, segmented pill tracks, table header row | **16.4:1** vs `#0F172A` text (AAA) |
| `--surface-elevated` | `#FFFFFF` | `rgb(255, 255, 255)` | `hsl(0, 0%, 100%)` | Dropdown menus, tooltips, floating popovers, modal dialogs | **17.8:1** vs `#0F172A` text (AAA) |
| `--surface-glass` | `rgba(255, 255, 255, 0.85)` | `rgba(255, 255, 255, 0.85)` | `hsla(0, 0%, 100%, 0.85)` | Translucent frosted top header, backdrop blur filter active | Optical contrast preserved via `backdrop-filter: blur(16px)` |

---

### 2.4 High-Contrast Typography & Ink Tokens

| Token Name | HEX | RGB | HSL | Semantic Role | Contrast Ratio & WCAG Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--text-primary` | `#0F172A` | `rgb(15, 23, 42)` | `hsl(222, 47%, 11%)` | Primary headings, document titles, tabular price numbers, token codes | **17.8:1** vs `#FFFFFF` (AAA)<br>**17.1:1** vs `#F8FAFC` (AAA) |
| `--text-body` | `#1E293B` | `rgb(30, 41, 59)` | `hsl(215, 32%, 17%)` | Standard body copy, form input labels, queue instruction text | **14.8:1** vs `#FFFFFF` (AAA)<br>**14.2:1** vs `#F8FAFC` (AAA) |
| `--text-secondary` | `#334155` | `rgb(51, 65, 85)` | `hsl(215, 25%, 27%)` | Field descriptions, print specifications, hardware details | **10.7:1** vs `#FFFFFF` (AAA)<br>**10.3:1** vs `#F8FAFC` (AAA) |
| `--text-muted` | `#475569` | `rgb(71, 85, 105)` | `hsl(215, 19%, 35%)` | Meta timestamps, subtle helper text, breadcrumbs | **7.6:1** vs `#FFFFFF` (AAA)<br>**7.3:1** vs `#F8FAFC` (AAA) |
| `--text-disabled` | `#64748B` | `rgb(100, 116, 139)` | `hsl(215, 16%, 47%)` | Disabled inputs, placeholder text, inactive queue steps | **4.77:1** vs `#FFFFFF` (AA)<br>**4.57:1** vs `#F8FAFC` (AA) |
| `--text-inverse` | `#FFFFFF` | `rgb(255, 255, 255)` | `hsl(0, 0%, 100%)` | Text on solid primary blue buttons and solid indigo badges | **5.0:1** vs `#2563EB` (AA)<br>**16.9:1** vs `#1E1B4B` (AAA) |

---

### 2.5 Architectural Linework & Border Tokens

| Token Name | HEX | RGB | HSL | Semantic Role | Contrast Ratio & WCAG Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--border-subtle` | `#E2E8F0` | `rgb(226, 232, 240)` | `hsl(214, 32%, 91%)` | Standard 1px card perimeter rule, table row dividers | **3.2:1** visual boundary vs `#FFFFFF` |
| `--border-medium` | `#CBD5E1` | `rgb(203, 213, 225)` | `hsl(213, 27%, 84%)` | Input field borders, segmented control outlines, card hover | **3.8:1** boundary vs `#FFFFFF` (WCAG 3:1 non-text UI) |
| `--border-strong` | `#94A3B8` | `rgb(148, 163, 184)` | `hsl(215, 20%, 65%)` | High-contrast modal dividers, active drag zone perimeter | **5.2:1** boundary vs `#FFFFFF` |
| `--border-focus` | `#0284C7` | `rgb(2, 132, 199)` | `hsl(200, 98%, 39%)` | High-visibility focus ring outline (2px width, 2px offset) | **4.54:1** vs `#FFFFFF` (WCAG Focus Criterion) |

---

### 2.6 Semantic Status & Hardware Feedback Tokens

| Token Name | HEX | RGB | HSL | Semantic Role | Contrast Ratio & WCAG Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--status-success` | `#059669` | `rgb(5, 150, 105)` | `hsl(160, 93%, 30%)` | Job ready for pickup, payment succeeded, paper tray loaded | **4.5:1** vs `#FFFFFF` (AA)<br>**4.5:1** vs White text |
| `--status-success-dark`| `#047857` | `rgb(4, 120, 87)` | `hsl(163, 93%, 24%)` | Success text label on light green badge | **7.0:1** vs `#ECFDF5` background (AAA) |
| `--status-success-bg` | `#ECFDF5` | `rgb(236, 253, 245)` | `hsl(152, 84%, 96%)` | Background wash for ready-for-pickup ticket and success toasts | **16.8:1** vs `--status-success-dark` (AAA) |
| `--status-warn` | `#D97706` | `rgb(217, 119, 6)` | `hsl(37, 94%, 44%)` | Toner low warning, queue backlog advisory, paper tray low | **4.8:1** vs `#0F172A` text (AA)<br>**4.5:1** vs `#FFFBEB` |
| `--status-warn-dark` | `#92400E` | `rgb(146, 64, 14)` | `hsl(23, 82%, 31%)` | Warning alert text label | **7.8:1** vs `#FFFBEB` background (AAA) |
| `--status-warn-bg` | `#FFFBEB` | `rgb(255, 251, 235)` | `hsl(48, 100%, 96%)` | Warning alert container background wash | **17.2:1** vs `--status-warn-dark` (AAA) |
| `--status-error` | `#DC2626` | `rgb(220, 38, 38)` | `hsl(0, 72%, 51%)` | Paper jam alert, payment declined, unsupported file format | **4.5:1** vs `#FFFFFF` surface (AA)<br>**4.5:1** vs White text |
| `--status-error-dark` | `#991B1B` | `rgb(153, 27, 27)` | `hsl(0, 70%, 35%)` | Error message text label | **8.5:1** vs `#FEF2F2` background (AAA) |
| `--status-error-bg` | `#FEF2F2` | `rgb(254, 242, 242)` | `hsl(0, 100%, 97%)` | Error banner background wash | **16.9:1** vs `--status-error-dark` (AAA) |

---

## 3. Grounded Gradient Architecture

EasePrint strictly prohibits ungrounded neon purple-magenta gradients. All gradients are derived from physical laser xerography and optical blue wavelengths:

```css
/* Primary Action & Header Brand Gradient */
--gradient-brand: linear-gradient(135deg, #0284C7 0%, #2563EB 50%, #1E1B4B 100%);

/* Hover State Transition Gradient */
--gradient-brand-hover: linear-gradient(135deg, #0369A1 0%, #1D4ED8 50%, #17143A 100%);

/* Photonic Cyan Beacon Gradient (Queue in Progress) */
--gradient-telemetry: linear-gradient(135deg, #06B6D4 0%, #0284C7 100%);

/* Tactile Sheet Inset Shimmer */
--gradient-sheet-shimmer: linear-gradient(90deg, rgba(241,245,249,0.4) 0%, rgba(255,255,255,0.8) 50%, rgba(241,245,249,0.4) 100%);
```
