# 🌸 DARE BLOOM — Technical Documentation

> **Version:** 1.0 · **Author:** Sribendu Prasad Muduli · **Last Updated:** August 2026

---

## 1. Project Overview

**Dare Bloom** is a browser-based party game that combines **real-time hand tracking** with a **dare challenge system**. Players use their index finger (tracked via webcam) to draw shapes on screen — hearts, stars, circles, infinity signs, spirals, and waves. Each shape is scored on accuracy and coverage, and after every round, players can unlock a **scratch-card dare** from one of four escalating tiers. Proof of completing dares can be uploaded and verified by **Gemini AI** for bonus points.

The game blends creative hand-tracking gameplay with social party mechanics, creating an experience where drawing skill directly gates how wild the dares get.

| Attribute | Detail |
|---|---|
| **Project Name** | Dare Bloom — Flower Drawing Game & Dare Challenge |
| **Creator** | Sribendu Prasad Muduli |
| **Type** | Single-page browser application (SPA) |
| **Primary File** | [`index.html`](file:///c:/Users/Sribendu%20Prasad/OneDrive/Desktop/flowers/index.html) (~1,478 lines, ~100 KB) |
| **Live Deployment** | Vercel (auto-deploy from GitHub) |
| **Repository** | `SRIBENDUPRASADMUDULI/DareBloom` |

---

## 2. Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Structure** | HTML5 | Semantic markup, screen-based SPA layout |
| **Styling** | CSS3 (vanilla, CSS variables) | Design system, animations, responsive layout |
| **Logic** | JavaScript ES6+ (modules + non-module) | Game engine, hand tracking, state management |
| **Hand Tracking** | [MediaPipe Hand Landmarker](https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18) v0.10.18 | Real-time 21-landmark hand detection via webcam |
| **Authentication** | Firebase Auth v10.12.0 (compat SDK) | Google Sign-In with redirect flow |
| **Database** | Cloud Firestore v10.12.0 (compat SDK) | Global leaderboard storage |
| **AI Verification** | Google Gemini 2.0 Flash API | Dare proof image analysis & verification |
| **Drawing** | Canvas 2D API | Shape guides, flower particles, sparkles, trails |
| **Audio** | Web Audio API | Procedurally generated tones & sound effects |
| **Typography** | Google Fonts: Creepster, Space Grotesk, Space Mono | Themed font system |
| **Deployment** | Vercel | Static hosting with auto-deploy |
| **Dev Server** | Python `http.server` ([`server.py`](file:///c:/Users/Sribendu%20Prasad/OneDrive/Desktop/flowers/server.py)) | Local dev with COOP/COEP headers |

### Supporting Files (Legacy / Adjacent Projects)

| File | Technology | Purpose |
|---|---|---|
| [`app.py`](file:///c:/Users/Sribendu%20Prasad/OneDrive/Desktop/flowers/app.py) | Streamlit + PyTorch (ResNet18) | Flower classification web app (104 classes) |
| [`predict.py`](file:///c:/Users/Sribendu%20Prasad/OneDrive/Desktop/flowers/predict.py) | PyTorch | CLI flower classification script |
| [`hand_tracker.py`](file:///c:/Users/Sribendu%20Prasad/OneDrive/Desktop/flowers/hand_tracker.py) | OpenCV + MediaPipe (Python) | Desktop hand-tracked flower filter prototype |
| `flower_model.pth` | PyTorch weights | Trained ResNet18 model (~45 MB) |
| `hand_landmarker.task` | MediaPipe | Hand landmark detection model (~7.8 MB) |

---

## 3. Architecture

### 3.1 Single-Page Application Structure

The entire game lives in a single `index.html` file. Navigation is handled via CSS class toggling (`.screen.on`) — no routing library is needed.

```mermaid
graph TB
    subgraph "index.html — 1,478 lines"
        HEAD["HEAD<br/>CSS Design System — 195 lines<br/>Firebase SDK imports"]
        BODY["BODY<br/>Screen Elements — 164 lines"]
        S1["Script 1 — Non-Module<br/>Firebase Init + Auth<br/>Gemini AI Verification"]
        S2["Script 2 — ES Module<br/>MediaPipe Import<br/>Game Engine — 1,000+ lines"]
    end

    HEAD --> BODY --> S1 --> S2

    style HEAD fill:#1a1a2e,stroke:#FF006E,color:#fff
    style BODY fill:#1a1a2e,stroke:#FF006E,color:#fff
    style S1 fill:#0d0022,stroke:#FFB703,color:#fff
    style S2 fill:#0d0022,stroke:#06D6A0,color:#fff
```

### 3.2 Script Separation Strategy

The app uses **two script blocks** — a deliberate architecture choice:

| Script | Type | Lines | Responsibility |
|---|---|---|---|
| Script 1 (L365–L470) | `<script>` (non-module) | ~105 | Firebase init, `doGoogleSignIn()`, `verifyDareProof()`, `auth.onAuthStateChanged()` |
| Script 2 (L471–L1476) | `<script type="module">` | ~1,005 | MediaPipe import, entire game engine, all event handlers |

> [!NOTE]
> Firebase compat SDK uses global `firebase.*` objects which must be initialized in a **non-module** script. The module script then accesses `db`, `auth`, `firebaseUser`, and `playerName` as globals set by Script 1.

### 3.3 State Machine

The game uses a string-based state variable `gSt` to control flow:

```mermaid
stateDiagram-v2
    [*] --> loading: Page load
    loading --> intro: Hand tracker ready
    intro --> menu: Name entered
    menu --> countdown: Career or Shape Select
    menu --> shapes: Shape Select button
    shapes --> countdown: Shape picked
    countdown --> drawing: Countdown complete
    drawing --> done: Timer reaches zero
    done --> results: 600ms delay
    results --> countdown: Next or Retry
    results --> shapes: Next in free play
    results --> careerEnd: All 6 shapes done
    careerEnd --> menu: Play Again
```

### 3.4 Key Global Variables

| Variable | Type | Purpose |
|---|---|---|
| `gSt` | `string` | Game state: `'menu'`, `'intro'`, `'countdown'`, `'drawing'`, `'done'`, `'results'`, `'careerEnd'`, `'freeplay'` |
| `cMd` | `boolean` | Career mode active flag |
| `cRd` | `number` | Current round index in career mode |
| `cOr` | `string[]` | Shuffled shape order for career mode |
| `cScs` | `object[]` | Career scores accumulator `[{k, sc, em, nm}]` |
| `curS` | `object` | Current shape: `{k, d, pts}` |
| `covM` | `boolean[80]` | Coverage bitmask (80 segments per shape) |
| `hits` / `miss` | `number` | On-path vs off-path drawing counts |
| `tLeft` | `number` | Timer countdown (starts at 35 seconds) |
| `dareModeActive` | `boolean` | Dare system toggle |
| `dareStreak` | `number` | Consecutive dares completed |
| `totalDaresCompleted` | `number` | Lifetime dare count (persisted in localStorage) |
| `fls` / `sps` / `trs` | `array` | Flower particles / sparkles / trail particles |
| `HL` | `HandLandmarker` | MediaPipe hand tracker instance |
| `firebaseUser` | `object\|null` | Current Firebase auth user |
| `playerName` | `string` | Player display name |

---

## 4. Game Flow / Stages

### Stage 1: Loading Screen
- Shows a CSS spinner ring and "loading hand tracking..." text
- `init()` function resolves MediaPipe WASM vision tasks
- Creates `HandLandmarker` with GPU delegate, 1 hand, VIDEO running mode
- Requests webcam access (`getUserMedia` at 1280×720)
- On success: starts `requestAnimationFrame` loop, transitions to Intro

### Stage 2: Intro / How to Play
- Explains controls: ☝️ index finger = draw, ✋ open palm = erase
- Name input field (required, max 20 chars, persisted to localStorage)
- Google Sign-In button (Firebase Auth redirect flow)
- Continue button gated until name is entered or user is signed in

### Stage 3: Main Menu
- Shows game title with animated gradient logo + glitch effect
- Displays best score and total dares completed (from localStorage)
- User info bar (if signed in: avatar + name + sign out)
- Creator credit: "Created by Sribendu Prasad Muduli"
- Buttons:
  - 🎮 **Play Career Mode** — all 6 shapes in random order
  - ✏️ **Shape Select** — pick a single shape
  - 🔥 **Dare Mode toggle** — ON/OFF
  - 🏆 **Leaderboard** — local + Firestore rankings
  - ℹ️ **How to Play** — returns to intro screen

### Stage 4: Shape Selection
- 3×2 grid of shape cards, each showing emoji, name, and difficulty
- 6 shapes: Heart (medium), Star (hard), Circle (easy), Infinity (hard), Spiral (medium), Wave (easy)
- Clicking a shape starts countdown for that single shape

### Stage 5: Countdown (3-2-1)
- Three-step countdown with animated number scaling (`cpulse` animation)
- Shows current shape emoji and name
- Sound effect on each tick

### Stage 6: Drawing Phase (35 seconds)
- **Camera feed** streams as full-screen background (mirrored)
- **Canvas overlay** renders shape guide, flowers, sparkles, trails
- **HUD** shows: shape name, real-time score, grade, accuracy bar, coverage bar, streak
- **Timer** renders as circular progress in top-right
- **Round dots** (career mode) show position in the 6-shape sequence
- **Guide toggle** button shows/hides the dotted shape outline
- Controls:
  - ☝️ Index finger draws flowers along traced path
  - ✋ Open palm (600ms hold) triggers dissipation — erases drawing + resets score
- In-game buttons: 🔄 Restart Shape, ✖ Quit to Menu

### Stage 7: Results Screen
- Animated card with score, grade badge, snarky message
- Stats: Accuracy %, Coverage %, On-path hits
- Buttons: Next → (career) / ↩ Retry

### Stage 8: Dare System (if enabled)
- **Scratch Card**: metallic overlay canvas with tier-themed colors
  - Mouse/touch to scratch off (destination-out compositing)
  - Auto-reveals when >55% cleared
  - 3-note reveal chord plays on reveal
- **Dare Display**: tier badge, dare text, bonus points
- **Actions**:
  - 📸 Upload Proof (+FULL BONUS) → triggers Gemini AI verification
  - 🤞 Claim (+HALF BONUS) → honor system, half points
  - 🙈 Skip (0 PTS) → resets dare streak
  - 🔄 Change Dare → re-rolls from same tier pool
- **AI Verification Flow**: upload image → spinner → Gemini analyzes → ✅ Verified or ❌ Rejected
- **Flower Explosion**: 80 flowers burst on verified, 40 on claimed

### Stage 9: Career Summary / Leaderboard
- Average score across all 6 shapes
- Grade badge for overall performance
- Chip list showing per-shape scores
- Total dares completed counter
- Play Again button returns to menu

---

## 5. Core Systems — Technical Deep Dive

### 5.1 Hand Tracking System

**Technology:** MediaPipe Hand Landmarker (WASM + WebGL, GPU-accelerated)

```javascript
// Initialization (L1230-1231)
const v = await FilesetResolver.forVisionTasks(
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm"
);
HL = await HandLandmarker.createFromOptions(v, {
  baseOptions: {
    modelAssetPath: "https://storage.googleapis.com/mediapipe-models/...",
    delegate: "GPU"
  },
  numHands: 1,
  runningMode: "VIDEO",
  minHandDetectionConfidence: 0.2,
  minHandPresenceConfidence: 0.2,
  minTrackingConfidence: 0.2
});
```

**Landmark Processing Pipeline:**

1. `HL.detectForVideo(vid, timestamp)` runs each animation frame
2. If hand detected, checks `isOpen(lm)` — requires ≥4 extended fingers + thumb ratio
3. If **open palm**: triggers dissipation after 600ms hold
4. If **pointing**: extracts landmark 8 (index tip) position
5. **Coordinate transform**: `rx = (1 - tip.x) * W` (mirrored), `ry = tip.y * H`
6. **Adaptive smoothing**: speed-dependent interpolation (fast = less smooth, slow = more precise)
   - `SMN = 0.06` (min smooth factor), `SMX = 0.22` (max), `SPT = 70` (speed threshold)
7. **Interpolation**: between previous and current position, spawning flowers every ~3px
8. **Hit testing**: each interpolated point checked against shape path

### 5.2 Shape Generation System

Each shape uses a parametric mathematical function `gen(cx, cy, sz)` that returns an array of `[x, y]` points:

| Shape | Formula | Difficulty | Points |
|---|---|---|---|
| ❤️ Heart | `16sin³(t)`, `13cos(t) - 5cos(2t) - 2cos(3t) - cos(4t)` | Medium | 361 |
| ⭐ Star | 5-pointed star with alternating outer/inner radius | Hard | 361 |
| ⭕ Circle | `r·cos(t)`, `r·sin(t)` with r = 43% of size | Easy | 361 |
| ♾️ Infinity | Lemniscate of Bernoulli: `cos(t)/(1+sin²(t))` | Hard | 361 |
| 🌀 Spiral | Archimedean spiral with 3 full rotations | Medium | 1081 |
| 〰️ Wave | `A·sin(f·5π)` over horizontal span | Easy | 361 |

```javascript
// Heart shape parametric equation (L510)
heart: {
  gen(cx, cy, sz) {
    const p = [];
    for (let i = 0; i <= 360; i++) {
      const t = i * Math.PI / 180;
      p.push([
        cx + sz * 0.04 * 16 * Math.pow(Math.sin(t), 3),
        cy - sz * 0.04 * (13*Math.cos(t) - 5*Math.cos(2*t)
             - 2*Math.cos(3*t) - Math.cos(4*t))
      ]);
    }
    return p;
  }
}
```

### 5.3 Scoring Algorithm

```
Final Score = Accuracy × 0.55 + Coverage × 0.45
```

| Metric | Weight | Calculation |
|---|---|---|
| **Accuracy** | 55% | `hits / (hits + miss) × 100` — how many drawn points fell within `HIT = 65px` of the shape path |
| **Coverage** | 45% | Percentage of 80 path segments touched (each segment = `points.length / 80` path points, hit threshold `COV = 90px`) |

**Grade Thresholds:**

| Grade | Score Range | CSS Class | Style |
|---|---|---|---|
| **S** | ≥ 90 | `.gS` | Gold (#FFD700) |
| **A** | 75–89 | `.gA` | Cyan (var(--cy)) |
| **B** | 58–74 | `.gB` | Purple (#a570ff) |
| **C** | 40–57 | `.gC` | Amber (var(--am)) |
| **D** | 0–39 | `.gD` | Pink (var(--pk)) |

Each grade has 4–6 snarky Gen-Z messages, e.g.:
- **S**: "💅 understood the assignment COMPLETELY. ate and left zero crumbs bestie"
- **D**: "💀 ratio'd by a dotted line. touch grass and retry."

### 5.4 Flower Particle System

Three particle types managed in parallel arrays:

| Type | Array | Max Count | Properties |
|---|---|---|---|
| **Flowers** | `fls[]` | 700 | position, size, palette, petal count, rotation, scale, grow time, alpha, state, velocity |
| **Sparkles** | `sps[]` | 500 | position, velocity, alpha, size, hue |
| **Trails** | `trs[]` | 350 | position, alpha, size, color string |

**Flower Lifecycle:**
1. **Growing** (state 0): elastic ease-out scale animation (`eEl` function), alpha ramp
2. **Static** (state 1): fully visible, no animation
3. **Dissipating** (state 2): radial delay, upward velocity with gravity, wind oscillation, spin, fade

**Rendering Pipeline (per flower):**
1. Radial gradient glow halo
2. Outer petals (bezier curves via `dpet()`)
3. Inner petals (smaller, offset by half-petal angle)
4. Center gradient circle

**Color Palettes:**
- `PH[]` — 2 hit palettes (green-cyan tones, for on-path flowers)
- `PM[]` — 2 miss palettes (red-pink tones, for off-path flowers)
- `PF[]` — 5 freeplay palettes (pink, purple, blue, teal, yellow)

### 5.5 Scratch Card System

A self-contained canvas module (L826–L1020) that implements the reveal mechanic:

```mermaid
flowchart LR
    A["initScratchCard"] -->|rAF| B["Draw metallic overlay"]
    B --> C["User scratches"]
    C -->|throttled 5x/sec| D["Sample pixel alpha"]
    D -->|55% cleared| E["Auto-reveal + enable buttons"]
```

**Performance Optimizations:**
- `getImageData` throttled to max 5 calls/sec (200ms gate) — avoids 180ms/sec frame budget waste
- Pixel sampling stride of 4 (only checks every 4th pixel's alpha)
- Canvas reuses existing DOM element (no GC pressure)
- CSS `opacity` transition for reveal (GPU composited, zero JS per-frame cost)

**Tier Color Themes:**

| Tier | Background | Shine Color |
|---|---|---|
| Mild | `#0b3328` → `#053d27` | `#06D6A0` |
| Spicy | `#3a2400` → `#4a2e00` | `#FFB703` |
| Hard | `#38001a` → `#4a0022` | `#FF006E` |
| Chaos | `#380600` → `#200000` | `#FF3B00` |

### 5.6 Dare Tier System

**160 total dares** across 4 escalating tiers of 40 each:

| Tier | Badge | Bonus | Emoji | Count | Theme |
|---|---|---|---|---|---|
| **Mild** | LEVEL 1: CREEPY DARE 🌸 | +30 pts | 🌸 | 40 | Silly, awkward, harmless fun |
| **Spicy** | LEVEL 2: HORROR DARE 🌶️ | +50 pts | 🌶️ | 40 | Cringey social dares |
| **Hard** | LEVEL 3: NIGHTMARE 🔥 | +75 pts | 🔥 | 40 | Bold, embarrassing |
| **Chaos** | LEVEL 4: PURE TERROR 💀 | +100 pts | 💣 | 40 | Nuclear chaos dares |

> [!NOTE]
> The tier selection is **random** (not score-gated) — `getDareForScore()` picks a random tier from all 4 options each round.

**Anti-Repetition System:**
- Per-tier seen-dare tracking in `localStorage['bloomDareSeen_<tier>']`
- Stores a sparse boolean array of seen indices
- Auto-resets when all dares in a tier are exhausted
- Guarantees no dare repeats until full pool is cycled

### 5.7 AI Proof Verification (Gemini Integration)

```mermaid
sequenceDiagram
    participant Player
    participant Game
    participant Gemini as Gemini 2.0 Flash API

    Player->>Game: Upload proof image
    Game->>Game: Convert to base64 and extract MIME type
    Game->>Gemini: POST generateContent
    Note over Game,Gemini: Prompt: Be lenient and fun.<br/>Only reject if completely unrelated.
    Gemini-->>Game: JSON with verified, reason, confidence
    Game->>Player: Verified or Rejected with verdict UI
```

**Gemini Prompt Strategy:**
```
You are a dare verification judge for a party game.
The player was given this dare: "<dare text>"
They uploaded an image as proof. Analyze if this is a legitimate attempt.
Be lenient and fun — if the image shows any reasonable effort, APPROVE it.
Only reject if completely unrelated (random photo, blank screen, or fake).
Respond with ONLY a JSON object: {verified, reason, confidence}
```

**Fallback behavior:** On API errors, the system **auto-approves** with fun messages like "AI is sleeping — approved by default! 😴"

### 5.8 Audio System

All sounds are procedurally generated via Web Audio API — zero audio files loaded.

| Function | Sound | Waveform | Purpose |
|---|---|---|---|
| `sfxSp(h)` | Soft ping | sine | Flower spawn (hit vs miss pitch) |
| `sfxC(n)` | Countdown beep | sine | 3-2-1 countdown ticks |
| `sfxOK()` | Ascending chord | sine | C5→E5→G5→C6 (results/career reveal) |
| `sfxSc()` | Scatter burst | sine | 6 random tones (dissipation) |
| `sfxT()` | Low tick | sine | Timer warning (last 5 seconds) |
| `sfxDareDone()` | Power-up arpeggio | triangle | 300→500→800→1200 Hz (dare completed) |
| `sfxSkip()` | Low buzz | sawtooth | Dare skipped |

**Core tone generator:**
```javascript
function tone(freq, type, duration, volume = 0.08, delay = 0) {
  const o = AC.createOscillator(), g = AC.createGain();
  o.connect(g); g.connect(AC.destination);
  o.type = type; o.frequency.value = freq;
  const T = AC.currentTime + delay;
  g.gain.setValueAtTime(0, T);
  g.gain.linearRampToValueAtTime(volume, T + 0.01);
  g.gain.exponentialRampToValueAtTime(0.001, T + duration);
  o.start(T); o.stop(T + duration + 0.01);
}
```

### 5.9 Leaderboard System

**Dual-storage architecture:**

| Storage | Scope | Max Entries | Auth Required |
|---|---|---|---|
| `localStorage['bloomLeaderboard']` | Local device | 50 | No |
| Firestore `leaderboard` collection | Global | Top 10 queried | Yes (Google Auth) |

**Firestore Document Schema:**
```javascript
{
  name: string,          // Player display name
  base: number,          // Base drawing score
  bonus: number,         // Dare bonus points
  total: number,         // base + bonus
  photoURL: string,      // Google profile picture
  uid: string,           // Firebase Auth UID
  updatedAt: Timestamp   // Server timestamp
}
```

**Deduplication Logic:**
- Firestore: Document ID = `firebaseUser.uid` → only stores best score per user
- localStorage: Matches by case-insensitive name → updates if new total is higher
- Leaderboard display: Tries Firestore first, falls back to localStorage
- Highlights current player's row with `.lb-me` class and "👈" indicator
- Shows player rank even if outside top 10 (separated by "• • •")

### 5.10 Google Authentication

```javascript
// Non-module script (L366-L469)
firebase.initializeApp({
  apiKey: "AIzaSyBee3zwZDoMKt7DlpTMYkpZvT4u1xUkMCw",
  authDomain: "dare-bloom.firebaseapp.com",
  projectId: "dare-bloom"
  // ...
});

// Redirect flow (not popup — better mobile support)
function doGoogleSignIn() {
  var provider = new firebase.auth.GoogleAuthProvider();
  auth.signInWithRedirect(provider);
}

// Handle redirect result on return
auth.getRedirectResult().then(function(result) { /* ... */ });

// Reactive state listener updates UI across intro + menu screens
auth.onAuthStateChanged(function(user) {
  // Sets playerName from Google display name
  // Enables continue button automatically
});
```

---

## 6. CSS Design System

### 6.1 Color Palette

```css
:root {
  --pk: #FF0022;     /* Primary Pink/Red — brand color */
  --vi: #4A0000;     /* Deep Violet — dark accent */
  --cy: #8A0303;     /* Cyan/Red variant — success states */
  --am: #FF3300;     /* Amber/Orange — warning, spicy tier */
  --bg: #050000;     /* Near-black background */
  --br: rgba(255,0,34,.2);  /* Border glow */
  --flame: #FF0000;  /* Pure red — fire effects */
}
```

> [!TIP]
> The palette is intentionally dark and dramatic — the game has a "nightmare/horror" aesthetic with bloom and fire motifs despite being a flower-drawing game.

### 6.2 Typography

| Font | Family | Usage |
|---|---|---|
| **Creepster** | Cursive/Display | Logo, headings, dare text, grade labels |
| **Space Grotesk** | Sans-serif | Body text, buttons, scores |
| **Space Mono** | Monospace | Labels, stats, badges, tech UI elements |

### 6.3 Key Animations

| Animation | Keyframes | Duration | Usage |
|---|---|---|---|
| `spin` | `rotate(0 → 360deg)` | 0.9s linear ∞ | Loading spinner, AI spinner |
| `grad` | Background-position shift | 5s ease ∞ | Logo gradient, button glows |
| `glitch` | Alternating text-shadow | 0.4s ease ∞ alternate | Score display, logo |
| `orb` | Translate + scale | 12–15s ease ∞ alternate | Menu background orbs |
| `cpulse` | Scale 1.6→1→0.75, opacity 0→1→0 | 1s forwards | Countdown numbers |
| `cIn` | Scale 0.78→1, translateY 40→0, opacity 0→1 | 0.55s cubic-bezier | Result card entrance |
| `flamePulse` | Box-shadow pulse | 1.5s ∞ alternate | Chaos tier badge |
| `scratchAnim` | Translate + rotate oscillation | 1.2s ease ∞ | Scratch hand hint |
| `aiPulse` | Opacity 0.5→1→0.5 | 1.2s ease ∞ | "AI ANALYZING" text |

### 6.4 Custom Cursor

Every element uses a custom SVG cursor — a red arrow pointer:
```css
cursor: url("data:image/svg+xml,...") 5 3, auto;
```

### 6.5 Responsive Design

- Fluid typography: `clamp()` for logo sizes (`clamp(4rem, 10vw, 8rem)`)
- Shape grid: `grid-template-columns: repeat(3, 1fr)` with `gap: 14px`
- Result card: `max-width: 460px; width: 92vw`
- Full-viewport canvas and video: `position: fixed; inset: 0; width: 100%; height: 100%`
- Window resize handler: `rsz()` recalculates `W` and `H` for canvas

---

## 7. Deployment

### 7.1 Vercel Configuration

[`vercel.json`](file:///c:/Users/Sribendu%20Prasad/OneDrive/Desktop/flowers/vercel.json) is minimal (empty object `{}`), meaning Vercel uses default static hosting settings — auto-detects `index.html` and serves it.

### 7.2 Netlify Configuration (Alternative)

[`netlify.toml`](file:///c:/Users/Sribendu%20Prasad/OneDrive/Desktop/flowers/netlify.toml) sets security headers required for SharedArrayBuffer (MediaPipe WASM):

```toml
[[headers]]
  for = "/*"
  [headers.values]
    Cross-Origin-Embedder-Policy = "require-corp"
    Cross-Origin-Opener-Policy   = "same-origin"
    X-Content-Type-Options       = "nosniff"
    X-Frame-Options              = "DENY"
```

### 7.3 Local Development Server

[`server.py`](file:///c:/Users/Sribendu%20Prasad/OneDrive/Desktop/flowers/server.py) provides a Python dev server with COOP/COEP headers:

```python
class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()
```

Run with: `python server.py` → serves on `localhost:8002`

> [!IMPORTANT]
> The COOP/COEP headers are **mandatory** for MediaPipe WASM to access `SharedArrayBuffer`. A plain file:// or basic HTTP server will fail.

---

## 8. Development Journey

```mermaid
timeline
    title Dare Bloom Development Timeline
    section Foundation
        Desktop Prototype : Python OpenCV MediaPipe hand_tracker.py
                         : Flower spawning on hand movement
                         : 6 flower types and dual-palm dissipation
    section ML Experiment
        Flower Classifier : PyTorch ResNet18 with 104 classes
                         : Streamlit web app and CLI predictor
    section Web Game
        Core Engine : Ported hand tracking to browser via MediaPipe JS
                   : Canvas-based flower particle system
                   : 6 mathematical shape generators
    section Gameplay
        Scoring System : Accuracy plus Coverage weighted formula
                      : S A B C D grading with snarky messages
                      : Real-time HUD with progress bars
    section Social
        Dare System : 160 dares across 4 tiers
                   : Scratch card reveal mechanic
                   : Anti-repetition localStorage tracking
    section Integration
        AI and Auth : Gemini 2.0 Flash proof verification
                   : Firebase Auth with Google Sign-In
                   : Firestore global leaderboard
    section Deploy
        Production : Vercel auto-deploy from GitHub
                  : Netlify config as alternative
                  : Local dev server with COOP COEP headers
```

---

## 9. API Keys & Configuration

| Service | Key/Config | Location in Code |
|---|---|---|
| **Firebase** | `apiKey`, `projectId`, `appId` | L367–L374 (non-module script) |
| **Gemini AI** | `GEMINI_KEY` | L391 (non-module script) |
| **MediaPipe WASM** | CDN URL | L507, L1230 (module script) |
| **MediaPipe Model** | Google Storage URL | L1231 (module script) |
| **Google Fonts** | CDN URL | L9 (link tag) |

> [!CAUTION]
> The Firebase API key and Gemini API key are exposed in client-side code. Firebase Security Rules on Firestore should restrict read/write access. The Gemini key should ideally be proxied through a backend.

**localStorage Keys:**

| Key | Purpose |
|---|---|
| `bloomPlayerName` | Persisted player name |
| `bloomBest` | Best career score |
| `bloomDaresCount` | Total dares completed lifetime |
| `bloomLeaderboard` | Local leaderboard JSON array |
| `bloomDareSeen_lvl-mild` | Seen dare indices (mild tier) |
| `bloomDareSeen_lvl-spicy` | Seen dare indices (spicy tier) |
| `bloomDareSeen_lvl-hard` | Seen dare indices (hard tier) |
| `bloomDareSeen_lvl-chaos` | Seen dare indices (chaos tier) |

---

## 10. File Structure

```
flowers/
├── index.html              # Main game — entire SPA (1,478 lines, ~100 KB)
├── vercel.json             # Vercel deployment config (empty — defaults)
├── netlify.toml            # Netlify config (COOP/COEP headers)
├── server.py               # Python dev server with security headers
├── app.py                  # Streamlit flower classifier (legacy)
├── predict.py              # CLI flower prediction script (legacy)
├── hand_tracker.py         # Desktop hand tracker prototype (356 lines)
├── flower_model.pth        # PyTorch ResNet18 weights (~45 MB)
├── hand_landmarker.task    # MediaPipe model file (~7.8 MB)
├── rose.jpg                # Test image for prediction (~72 KB)
├── braces.txt              # Text data file (~70 KB)
├── .git/                   # Git repository
├── .venv/                  # Python virtual environment
└── venv/                   # Python virtual environment (alt)
```

### File Size Breakdown

| File | Size | Lines | Role |
|---|---|---|---|
| `index.html` | 100.6 KB | 1,478 | Complete game application |
| `flower_model.pth` | 45.0 MB | — | ML model weights |
| `hand_landmarker.task` | 7.8 MB | — | Hand detection model |
| `braces.txt` | 70.5 KB | — | Data file |
| `rose.jpg` | 72.1 KB | — | Test image |
| `hand_tracker.py` | 14.4 KB | 356 | Desktop prototype |
| `app.py` | 1.9 KB | 56 | Streamlit app |
| `predict.py` | 1.7 KB | 49 | CLI predictor |
| `server.py` | 503 B | 16 | Dev server |
| `netlify.toml` | 235 B | 9 | Deploy config |
| `vercel.json` | 4 B | 3 | Deploy config |

---

## 11. Game Constants Reference

| Constant | Value | Purpose |
|---|---|---|
| `HIT` | 65 px | Max distance from path to count as "on-path" |
| `COV` | 90 px | Max distance from path to count segment as "covered" |
| `TIME` | 35 sec | Drawing phase duration |
| `SEGS` | 80 | Number of path segments for coverage tracking |
| `MXF` | 700 | Maximum flower particles |
| `MXS` | 500 | Maximum sparkle particles |
| `MXT` | 350 | Maximum trail particles |
| `SMN` | 0.06 | Minimum smoothing factor (fast hand movement) |
| `SMX` | 0.22 | Maximum smoothing factor (slow hand movement) |
| `SPT` | 70 | Speed threshold for adaptive smoothing |

---

> 🌸 **DARE BLOOM** · Created by **Sribendu Prasad Muduli**
>
> *"Draw flowers with ur finger · complete dares or face chaos 💀"*
