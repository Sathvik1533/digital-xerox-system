# EasePrint Responsive System & Kiosk Architecture

## 1. Responsive Grid & Breakpoint Matrix

EasePrint adapts seamlessly from a student's mobile smartphone checking queue status while walking across campus, to a dual-monitor desktop in a computer lab, to a dedicated touch-screen physical kiosk in the campus print center.

### 1.1 Breakpoint Scale

| Breakpoint | Viewport Range | Target Devices | Layout Adaptation |
| :--- | :--- | :--- | :--- |
| **Mobile (`sm`)** | `< 640px` | iPhone, Android phones | Single-column stack, sticky bottom action bar, swipeable tabs |
| **Tablet (`md`)** | `640px – 1023px` | iPad, Android tablets | 2-column layout (Left: Upload + Config, Right: Sticky Summary) |
| **Desktop (`lg`)** | `1024px – 1439px`| Laptops, lab PCs | 3-column cockpit (Upload, Options, Sticky Price/Queue) |
| **Ultrawide (`xl`)**| `>= 1440px` | 4K displays, monitors | Centered 1320px container with enhanced telemetry margins |
| **Kiosk Mode** | `1920×1080` / `1080×1920` | Physical campus print kiosks | Touch-first ergonomics, 48px min touch targets, on-screen numpad |

---

## 2. Touch Target Ergonomics

Following WCAG 2.2 Criterion 2.5.8 (Target Size):
- Every interactive button, pill option, and dropdown trigger has a **minimum hit area of 44×44px** on touch viewports (`< 1024px`).
- In Kiosk mode, touch targets expand to **56×56px** to accommodate diverse student hand sizes and rapid touch inputs.
- Spacing between adjacent touch targets is strictly maintained at `>= 8px` to eliminate accidental mis-clicks.

---

## 3. Mobile Execution Architecture (Sticky Execution Bar)

On mobile viewports (`< 640px`), the 3-column desktop layout collapses gracefully:
1. **Step 1 (Top)**: Quick Document Upload Zone.
2. **Step 2 (Middle)**: Accordion-style Print Options with large tactile toggle cards.
3. **Step 3 (Bottom Fixed Dock)**: Sticky Bottom Bar showing:
   - Left: Live Total (`₹28.00`, bold JetBrains Mono).
   - Right: Prominent full-width button `[Pay & Send to Queue]`.
   - Backdrop: Frosted glass (`rgba(255, 255, 255, 0.92)` with `backdrop-filter: blur(16px)`).

```
┌───────────────────────────────────────┐
│ EASEPRINT MOBILE                      │
├───────────────────────────────────────┤
│ [Upload PDF Dropzone]                 │
│                                       │
│ [Color: B&W / Color Segmented Pill]   │
│ [Sides: Double-Sided (Save 25%)]      │
│ [Binding: Spiral Coil (+₹25)]         │
├───────────────────────────────────────┤
│ FIXED BOTTOM DOCK:                    │
│ Total: ₹35.50   │ [Swipe / Tap to Pay]│
└───────────────────────────────────────┘
```

---

## 4. Physical Campus Kiosk Mode Specification

EasePrint includes an automatic kiosk detection mode (`?kiosk=true` or terminal user agent):
- **High-Contrast Touch UI**: Font sizes scale up by 1.15×; button borders thicken to 2px.
- **Auto-Logout / Session Reset**: Automatically returns to clean idle screen after 45 seconds of inactivity.
- **Physical Barcode Scanner Listener**: Global keyboard-wedge listener ready to capture student physical RFID cards or order QR stubs instantly.

---

## 5. Non-Negotiable Theme Restriction: Responsive & Kiosk Surface Invariance

All responsive viewports (Mobile, Tablet, Desktop, Ultrawide, and Kiosk) operate strictly under a **light, bright, blue-led visual system**:

### 5.1 Responsive Theme Invariance & Glare Prevention
- **No Mobile Dark Mode**: Mobile viewports ignore OS dark-mode preferences (`prefers-color-scheme: dark`); EasePrint maintains its crisp, high-contrast light blue-led interface.
- **No Dark Kiosk Interfaces**: Campus kiosks operate under harsh overhead fluorescent library/corridor lights. Dark backgrounds produce heavy specular reflections and visual fatigue. EasePrint mandates pristine light backgrounds for maximum optical clarity.
- **Prohibited Aesthetics**:
  - Black backgrounds or near-black backgrounds
  - Charcoal application shells or dark navy page surfaces
  - Black hero sections or black cards
  - Dark dashboard chrome or dark glassmorphism
  - Neon-on-black, acid-green-on-black, or vermilion-on-black schemes
  - Dark “AI command center”, developer-tool, fintech, cyberpunk, or terminal aesthetics
  - Dark mode merely because it is a common AI/SaaS pattern
  - Dark or black palettes as an alternate visual direction (EasePrint is **not** a dark/light theme exploration project)
  - Warm beige, parchment, cream-heavy, tan, brown, terracotta, gold, and sepia palettes
  - Dark-mode toggles, dark-theme variants in previews, or dark preview screenshots

### 5.2 Required Responsive Character
The UI across all form factors must remain:
- **Light** and **Bright**
- **Blue-led** (`#2563EB`, `#0284C7`)
- **Cyan-accented** (`#06B6D4`)
- **Indigo-supported** (`#1E1B4B`, `#4F46E5` strictly for high-contrast linework and micro-accents)
- **Violet-accented only where useful** (`#6366F1`)
- **White or cool-white based**
- **Clear, Premium, Energetic, Trustworthy, Campus-technology oriented**

### 5.3 Permitted Background Families Across All Devices
- White (`#FFFFFF`)
- Cool white (`#F8FAFC`)
- Ice blue (`#F0F9FF`)
- Very pale blue (`#EFF6FF`)
- Blue-gray mist (`#F1F5F9`)
- Extremely pale lavender-blue (`#EEF2FF`)

**Review Gate Rule**: Any design proposal containing a dominant black, charcoal, navy, or dark surface fails review and must be rejected before implementation. Zero dark mode or dark-theme tokens/variants are permitted in the design system.
