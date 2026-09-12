# EasePrint Component Catalog & Technical Specifications

## 1. Component Architecture Overview

Every component in EasePrint is engineered for **speed, accessibility, and high operational clarity**. Components operate within a strict tokenized hierarchy, preventing hardcoded styles and ensuring consistent light, blue-led visual identity.

---

## 2. Core Campus Print Components

### 2.1 Document Upload Zone (`<UploadDropzone />`)

#### Anatomy & Layout
A high-tactile drag-and-drop area that immediately begins optical page and color analysis upon file drop.
- **Outer Shell**: 12px rounded container (`--radius-lg`), 2px dashed border (`--border-medium`, `#CBD5E1`), background `--surface-card` (`#FFFFFF`).
- **Drag-Active State**: Border switches to 2px solid `--brand-sky` (`#0284C7`), background transforms to subtle blue wash `--brand-blue-subtle` (`#EFF6FF`).
- **Dropzone Icon**: Centered 32px Lucide `<UploadCloud />` icon in `--brand-blue` (`#2563EB`).
- **Typography**: Primary instruction `"Drop lecture notes, PDF, or DOCX"` (`--type-primary`, `#0F172A`), subtitle `"Supports PDF, DOCX, PPTX up to 100 MB"` (`--type-muted`, `#475569`).

#### Document Analysis Card (Post-Upload)
- Displays file name (`#0F172A`, SemiBold), detected page count badge (`14 Pages`, `--brand-blue-subtle`, text `--brand-blue`), file size (`2.4 MB`), and detected color balance (`12 B&W pages, 2 Color pages`).
- Page thumbnail preview with cool-slate paper aspect ratio (1:1.414 for A4).

#### Component Tokens & Contrast
| Element | Token | HEX | Contrast Ratio |
| :--- | :--- | :--- | :--- |
| Container Background | `--surface-card` | `#FFFFFF` | Canvas base |
| Active Drag Wash | `--brand-blue-subtle` | `#EFF6FF` | **16.2:1** vs `--brand-blue` |
| Primary Label | `--text-primary` | `#0F172A` | **17.8:1** vs `#FFFFFF` (AAA) |
| File Meta Text | `--text-muted` | `#475569` | **7.6:1** vs `#FFFFFF` (AAA) |
| Focus Ring | `--border-focus` | `#0284C7` | **4.54:1** vs `#FFFFFF` |

---

### 2.2 Print Configuration Stepper (`<PrintConfigurator />`)

#### Anatomy & Controls
Organized into 4 tactile option groups:
1. **Color Mode Switcher**: Segmented toggle pill with two choices:
   - `Black & White` (`₹1.50 / page`) — default cost-effective campus option.
   - `Full Color` (`₹6.00 / page`) — laser color reproduction.
2. **Duplex (Sides) Selector**:
   - `Double-Sided (Duplex)` — highlighted with a green savings chip: `Save 25% Paper & Cost`.
   - `Single-Sided (Simplex)` — standard layout.
3. **Paper Weight & Size**:
   - `Standard 75 GSM (A4)` — lecture notes and assignments.
   - `Heavy 100 GSM Bond` — project reports and presentations (`+₹1.00 / sheet`).
   - `A3 Technical Drawing` — engineering and architecture schematics.
4. **Binding Options**:
   - `None (Loose Sheets)` (`₹0.00`).
   - `Corner Staple` (`₹2.00`).
   - `Spiral Coil Binding` (`₹25.00`).
   - `Hardbound Thesis Book` (`₹180.00`).

#### States & Micro-Interactions
- **Segmented Pill Indicator**: Active option indicator slides horizontally behind selected label using `--ease-spring` (180ms).
- **Active Pill**: Solid `--brand-blue` (`#2563EB`) background with crisp `#FFFFFF` text (5.0:1 contrast).
- **Inactive Pill**: Background `--surface-inset` (`#F1F5F9`), text `--text-secondary` (`#334155`), hover background `#E2E8F0`.

---

### 2.3 Real-Time Price Estimator & Breakdown Dock (`<PriceEstimatorDock />`)

#### Anatomy & Reactive Calculation
A persistent, sticky card located in the execution column that reacts instantaneously (<16ms) to any configuration toggle change.
- **Formula**: `Total = (Pages / (Duplex ? 2 : 1)) * BasePrice + ColorDelta + BindingFee + RushFee`.
- **Itemized Breakdown Rows**:
  - `Pages & Paper`: 14 pages (7 double-sided sheets) × ₹1.50 = `₹10.50`
  - `Color Pages`: 2 pages × ₹4.50 delta = `₹9.00`
  - `Spiral Binding`: 1 × ₹25.00 = `₹25.00`
  - `Student Subsidy Discount`: `-₹4.50` (Emerald Green `#059669`)
  - **Estimated Total**: Large prominent JetBrains Mono display: `₹40.00`
- **Station Telemetry Badge**: Displays destination station:
  `Station B3 • Ground Floor Library • 2 Jobs Ahead (~4 mins)`
- **Submit Action**: Full-width primary button `"Simulate Payment & Send to Queue"`.

---

### 2.4 Live Holographic Queue Ticket (`<QueueTicket />`)

#### Anatomy & Visual Hierarchy
The signature campus physical-digital bridge. Modeled as a high-tech optical boarding pass:
- **Card Geometry**: 14px rounded white card with subtle top border accent `--gradient-brand`.
- **Perforated Separation Line**: A tactile dashed horizontal rule with semi-circular cutouts on left and right borders, mimicking a physical tear-off claim stub.
- **Queue Token Identifier**: `EP-8921` rendered in bold JetBrains Mono at 1.75rem (`#0F172A`), flanked by a pulsing cyan beacon dot indicating live active spooling.
- **Estimated Completion**: Live countdown clock: `03:42 remaining`, with a smooth animated sky-blue progress bar (`--brand-sky`, `#0284C7`).
- **Station Location Pin**: `Station B3 • Kiosk Terminal #2`.
- **Claim Verification QR Code**: High-contrast QR code for instant scanner check-in at the physical printer tray.

---

### 2.5 Simulated Instant Campus Payment Modal (`<PaymentSheet />`)

#### Architecture & Deterministic State Machine
Allows instantaneous, risk-free student payment testing with three deterministic triggers:
1. **Mode A: Campus ID Card Wallet (1-Click Instant)**:
   - Reads student wallet balance: `Current Balance: ₹142.50`.
   - Single click deducts `₹40.00`, immediately emits `PAYMENT_SUCCESS`, and transitions to Queue Ticket.
2. **Mode B: UPI QR Code**:
   - Generates dynamic high-contrast UPI QR code for mobile scanner payment.
3. **Mode C: Deterministic Sandbox Testing Bar**:
   - Explicit buttons for developer testing: `[Trigger Success]`, `[Trigger Insufficient Funds]`, `[Trigger Network Timeout]`.

---

### 2.6 Staff / Operator Kiosk Queue Management (`<StaffQueueCockpit />`)

#### Anatomy for High-Volume Shop Staff
- **Filter Pills**: `All Jobs (12)`, `Queued (5)`, `Printing (2)`, `Ready for Pickup (4)`, `Completed (148)`.
- **Order Table**:
  - `Token`: Monospace clickable link (`EP-8921`).
  - `Student`: Name and College ID (`Rahul Sharma • 24R21A05`).
  - `Document`: File name, page count, and binding badges.
  - `Hardware Action`: One-click actions:
    - `[Start Print]` (triggers hardware spooler)
    - `[Mark Ready]` (sends student SMS / push notification)
    - `[Reprint Sheet]` (clears paper jam, re-queues file)
    - `[Reject with Reason]` (refunds student wallet immediately)
- **Hardware Telemetry Bar**:
  - `Canon imageRUNNER DX C5860i`: Online (Tray 1: 82% Paper, Black Toner: 64%, Cyan: 48%).

---

## 3. Non-Negotiable Theme Restriction: Component Surface & Variant Rules

All components in EasePrint are engineered strictly for a **light, bright, blue-led design system**.

### 3.1 Prohibited Component Variants & Aesthetic Tropes
Under no circumstances may the following be introduced to any component:
- Dark-theme variants, dark-mode states, or inverted dark cards
- Black or near-black backgrounds
- Charcoal application shells or dark navy page surfaces
- Black hero sections or black cards
- Dark dashboard chrome or dark glassmorphism
- Neon-on-black, acid-green-on-black, or vermilion-on-black chips or telemetry bars
- Dark “AI command center”, developer-tool, fintech, cyberpunk, or terminal aesthetics
- Dark mode toggles, theme switcher dropdowns, or alternate dark visual directions
- Warm beige, parchment, cream-heavy, tan, brown, terracotta, gold, and sepia palettes
- Dark preview screenshots or mocks

### 3.2 Required Component Foundation
Components must remain:
- **Light** and **Bright**
- **Blue-led** (`--brand-blue: #2563EB`, `--brand-sky: #0284C7`)
- **Cyan-accented** (`--brand-cyan: #06B6D4`)
- **Indigo-supported** (`--indigo-deep: #1E1B4B`, `--indigo-vibrant: #4F46E5` for high-contrast borders, text, and micro-accents)
- **Violet-accented only where useful** (`--violet-accent: #6366F1`)
- **White or cool-white based**
- **Clear, Premium, Energetic, Trustworthy, Campus-technology oriented**

### 3.3 Permitted Background Families for Components
Component surfaces, insets, and badges must draw strictly from:
- White (`#FFFFFF`)
- Cool white (`#F8FAFC`)
- Ice blue (`#F0F9FF`)
- Very pale blue (`#EFF6FF`)
- Blue-gray mist (`#F1F5F9`)
- Extremely pale lavender-blue (`#EEF2FF`)

**Review Gate Rule**: Any component proposal containing a dominant black, charcoal, navy, or dark surface fails review and must be rejected before implementation. Zero dark mode or dark-theme tokens/variants are permitted in the component library.
