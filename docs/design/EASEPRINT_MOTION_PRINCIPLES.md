# EasePrint Motion Principles: Kinetic Spring Precision

## 1. Motion Philosophy: Purpose-Driven Fluidity

In campus printing operations, motion is **never decorative entertainment**; it is **tactile spatial feedback**.

Influenced by **Emil Kowalski** and modern spring mechanics, EasePrint's motion system obeys three immutable laws:
1. **Perceptual Instantaneity**: Every user action (button click, toggle switch) triggers immediate visual response in under 16ms (1 frame).
2. **Spring Damping over Rigid Easing**: Natural physical deceleration replaces mechanical linear transitions.
3. **Hard Duration Budget**: Interactive transitions MUST complete within **180ms–280ms**. Modal entries are capped at **350ms**. Slow 600ms–800ms floaty animations are strictly prohibited.

---

## 2. Motion Token Architecture

```css
:root {
  /* Calibrated Spring & Deceleration Curves */
  --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);    /* Primary fluid spring */
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1); /* Tactile checkmark/badge micro-pop */
  --ease-in: cubic-bezier(0.7, 0, 0.84, 0);       /* Rapid exit curve */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);      /* Smooth entry deceleration */

  /* Duration Budget Tokens */
  --duration-instant: 100ms;  /* Radio pill active state, toggle switch */
  --duration-fast:    180ms;  /* Button hover, tooltip reveal, dropdown item */
  --duration-normal:  280ms;  /* Card hover lift, segmented indicator slide */
  --duration-enter:   350ms;  /* Modal sheet entrance, full queue ticket expand */
}
```

---

## 3. Signature Micro-Interactions

### 3.1 Button Press Compression (The Haptic Click)
Interactive buttons visually depress on click, providing physical confirmation:
```css
.btn-primary {
  transition: transform var(--duration-fast) var(--ease-spring),
              background-color var(--duration-fast) ease,
              box-shadow var(--duration-fast) ease;
}
.btn-primary:active {
  transform: scale(0.98) translateY(1px);
}
```

### 3.2 Segmented Pill Sliding Indicator
When a student switches between "Black & White" and "Full Color", the background indicator slides smoothly across the track:
```css
.pill-indicator {
  position: absolute;
  top: 4px;
  bottom: 4px;
  border-radius: var(--radius-sm);
  background: var(--brand-blue);
  transition: transform var(--duration-normal) var(--ease-spring),
              width var(--duration-normal) var(--ease-spring);
}
```

### 3.3 Zero-Jank Skeleton Shimmer
During file upload and price calculation, containers render a fluid cool-blue shimmer wave to prevent Cumulative Layout Shift (CLS):
```css
@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
.skeleton-shimmer {
  position: relative;
  overflow: hidden;
  background-color: var(--surface-inset);
}
.skeleton-shimmer::after {
  content: '';
  position: absolute;
  top: 0; right: 0; bottom: 0; left: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.6) 50%, transparent 100%);
  animation: shimmer 1.5s infinite;
}
```

---

## 4. Accessibility & Reduced Motion Protocol

For users with vestibular disorders or motion sensitivity, EasePrint provides an uncompromising `@media (prefers-reduced-motion: reduce)` contract:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  .pill-indicator, .btn-primary {
    transform: none !important;
  }
}
```
All state transitions degrade gracefully to instant opacity switches.

---

## 5. Non-Negotiable Theme Restriction: Photonic Motion & Ban on Dark Aesthetics

The motion system operates exclusively within a **light, bright, blue-led visual environment**.

### 5.1 Photonic Lighting vs. Dark Tropes
- **Photonic Laser Shimmers**: Shimmer and state pulses use pure white transmission (`rgba(255, 255, 255, 0.6)`) and cyan-blue beacon glow (`rgba(2, 132, 199, 0.2)`).
- **Prohibited Motion Aesthetics**:
  - Dark cyberpunk scanlines or glowing neon pulses on black
  - Neon-on-black, acid-green-on-black, or vermilion-on-black effects
  - Dark “AI command center”, developer-tool, fintech, or terminal aesthetic animations
  - Black backgrounds or near-black backgrounds
  - Charcoal application shells or dark navy page surfaces
  - Black hero sections or black cards
  - Dark dashboard chrome or dark glassmorphism
  - Dark mode merely because it is a common AI/SaaS pattern
  - Dark or black palettes as an alternate visual direction (EasePrint is **not** a dark/light theme exploration project)
  - Warm beige, parchment, cream-heavy, tan, brown, terracotta, gold, and sepia palettes
  - Dark-mode toggles, dark-theme animation variants, or dark preview screenshots

### 5.2 Required Motion Character
All animations must remain:
- **Light** and **Bright**
- **Blue-led** (`#2563EB`, `#0284C7`)
- **Cyan-accented** (`#06B6D4`)
- **Indigo-supported** (`#1E1B4B`, `#4F46E5` for high-contrast borders and micro-accents)
- **Violet-accented only where useful** (`#6366F1`)
- **White or cool-white based**
- **Clear, Premium, Energetic, Trustworthy, Campus-technology oriented**

### 5.3 Permitted Background Families for Motion Surfaces
- White (`#FFFFFF`)
- Cool white (`#F8FAFC`)
- Ice blue (`#F0F9FF`)
- Very pale blue (`#EFF6FF`)
- Blue-gray mist (`#F1F5F9`)
- Extremely pale lavender-blue (`#EEF2FF`)

**Review Gate Rule**: Any motion or visual design proposal containing a dominant black, charcoal, navy, or dark surface fails review and must be rejected before implementation. Zero dark mode or dark-theme tokens/variants are permitted in the design system.
