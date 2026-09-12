# EasePrint Interaction Patterns & State Machines

## 1. The 30-Second Student Execution Flow

EasePrint is engineered for the high-pressure campus sprint: between consecutive lectures, students have less than 5 minutes to submit, pay, and collect lab reports.

```
[1. File Dropped] ──────> [2. Instant Analysis] ──────> [3. 1-Click Config]
       │                          │                            │
  Drag PDF onto              Extracts pages,             Duplex & B&W
  upload dropzone            color count, GSM            selected by default
       │                          │                            │
       ▼                          ▼                            ▼
[6. Collect Paper] <──── [5. Live Telemetry] <───── [4. 1-Click Wallet Pay]
  Show QR at Station B3     Queue Token #EP-8921        Instant deduction
  tray when green           ticks down in real-time     from student balance
```

---

## 2. Deterministic State Machine Specifications

Every view and component in EasePrint operates under a strictly defined deterministic state machine.

### 2.1 Order Lifecycle States

| State | Trigger | Visual UI Representation | Permitted Next States |
| :--- | :--- | :--- | :--- |
| `IDLE` | App load | Empty dropzone, disabled price dock | `UPLOADING` |
| `UPLOADING` | File drop | Progress bar, skeleton preview, spinner | `ANALYZED`, `UPLOAD_ERROR` |
| `ANALYZED` | S3 upload + backend page count complete | Document card visible, default price calculated | `CONFIGURING`, `IDLE` |
| `CONFIGURING` | Student clicks print toggles | Price dock updates in <16ms, itemized breakdown recalculated | `PAYMENT_PENDING`, `IDLE` |
| `PAYMENT_PENDING`| Student clicks "Proceed to Payment" | Payment modal sheet opens, wallet balance verified | `PAYMENT_SUCCESS`, `PAYMENT_FAILED`, `CONFIGURING` |
| `QUEUED` | Payment confirmed | Holographic Queue Ticket (`EP-8921`), countdown timer starts | `PRINTING`, `REJECTED` |
| `PRINTING` | Staff / hardware starts spooling | Cyan beacon pulse, "Printing on Station B3" progress bar | `READY_FOR_PICKUP`, `HARDWARE_ERROR` |
| `READY_FOR_PICKUP`| Hardware marks job done | High-contrast emerald ticket, pickup QR code active, pickup bin # | `COMPLETED` |
| `COMPLETED` | Student scans QR at bin | Order archived in History, receipt available | `REORDER` |

---

## 3. Keyboard Navigation & Accessibility Contracts

EasePrint implements full **Roving Tabindex** and standard keyboard navigation contracts:

### 3.1 Global Shortcuts
- `Tab` / `Shift+Tab`: Navigates sequentially through interactive controls in logical DOM reading order.
- `Escape`: Closes open modal sheets (Payment modal, Queue Ticket expanded view, Error alert).
- `Space` / `Enter`: Activates buttons, toggles segmented pill selections, and opens file picker.

### 3.2 Segmented Option Controls
- `ArrowRight` / `ArrowDown`: Moves active selection to the next print option pill (e.g. B&W → Color).
- `ArrowLeft` / `ArrowUp`: Moves active selection to previous print option pill.
- Focus indicator remains visibly locked with a **2px solid `--border-focus` (`#0284C7`) outline and 2px offset**.

---

## 4. Error Recovery & Idempotency Workflows

Campus networks are frequently unreliable, especially in basement print shops. EasePrint implements rock-solid recovery workflows:

1. **Idempotent Order Submission**:
   - Every order generates a client-side UUID idempotency key before payment dispatch.
   - Repeated clicks or rapid double-taps on the submit button are de-bounced and deduplicated, preventing duplicate charges.
2. **Network Timeout Grace Period**:
   - If payment verification times out, the system displays a persistent non-destructive retry banner: `"Verifying payment with campus bank... [Retry Status Check] [Switch to Cash at Counter]"`.
3. **Hardware Jam Automatic Re-Queue**:
   - If an operator reports a paper jam on Station B3, the queue service automatically reroutes pending jobs to alternate Station B4 without requiring student re-submission.

---

## 5. Non-Negotiable Theme Restriction: Interaction Invariance & Ban on Theme Switching

EasePrint is designed exclusively as a **light, bright, blue-led platform**. It is strictly **not** a dark/light exploration project.

### 5.1 Ban on Theme Toggles & Dark Modes
- **Zero Theme Switching Interactions**: Do not introduce a dark-mode toggle, toggle shortcut, or theme-selection menu.
- **Zero OS Dark Mode Inversion**: Interactions and state transitions remain strictly in the light visual spectrum regardless of operating system dark-mode preferences.
- **Prohibited Aesthetics**:
  - Black backgrounds or near-black backgrounds
  - Charcoal application shells or dark navy page surfaces
  - Black hero sections or black cards
  - Dark dashboard chrome or dark glassmorphism
  - Neon-on-black, acid-green-on-black, or vermilion-on-black color schemes
  - Dark “AI command center”, developer-tool, fintech, cyberpunk, or terminal aesthetics
  - Dark mode merely because it is a common AI/SaaS pattern
  - Warm beige, parchment, cream-heavy, tan, brown, terracotta, gold, and sepia palettes
  - Dark-theme variants in previews or dark preview screenshots

### 5.2 Required Light-First Interaction Atmosphere
All states, modals, and focus rings remain:
- **Light** and **Bright**
- **Blue-led** (`#2563EB`, `#0284C7`)
- **Cyan-accented** (`#06B6D4`)
- **Indigo-supported** (`#1E1B4B`, `#4F46E5` strictly for high-contrast linework and micro-accents)
- **Violet-accented only where useful** (`#6366F1`)
- **White or cool-white based**
- **Clear, Premium, Energetic, Trustworthy, Campus-technology oriented**

### 5.3 Permitted Background Families
- White (`#FFFFFF`)
- Cool white (`#F8FAFC`)
- Ice blue (`#F0F9FF`)
- Very pale blue (`#EFF6FF`)
- Blue-gray mist (`#F1F5F9`)
- Extremely pale lavender-blue (`#EEF2FF`)

**Review Gate Rule**: Any design or interaction proposal containing a dominant black, charcoal, navy, or dark surface fails review and must be rejected before implementation. Zero dark mode or dark-theme tokens/variants are permitted in the design system.
