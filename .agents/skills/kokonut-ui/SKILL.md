---
name: kokonut-ui
description: Discover, inspect, install, and customize 100+ modern animated components from Kokonut UI (kokonutui.com) including AI inputs, liquid glass cards, beam backgrounds, morphic navbars, and particle buttons via shadcn CLI, direct registry URLs, or manual copy-paste. Trigger on requests like "add kokonut component", "use kokonut ui", "install particle button", or when building cutting-edge React/Tailwind interfaces.
---

# Kokonut UI Component Integration

Kokonut UI (https://kokonutui.com) is a library of 100+ modern, animated UI components built with **Next.js / React**, **Tailwind CSS v4**, **Motion**, and **shadcn/ui**.

Components are distributed via the official shadcn registry protocol and can be installed with zero configuration.

---

## 1. Quick Setup & Configuration

### A. Add the Kokonut Registry to `components.json`
If your project uses shadcn, add `@kokonutui` to the `registries` section of your `components.json`:

```json
{
  "registries": {
    "@kokonutui": "https://kokonutui.com/r/{name}.json"
  }
}
```

### B. Core Utilities
Ensure the standard `cn` utility function is installed:
```bash
npx shadcn@latest add https://kokonutui.com/r/utils.json
```
or verify your `lib/utils.ts` has:
```ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### C. Common Dependencies
Most components require:
```bash
npm install lucide-react motion clsx tailwind-merge
```

---

## 2. Component Catalog by Category

### AI Components
- `ai-prompt`: Animated AI chat input with model selector, file attachment, and auto-resizing textarea.
- `ai-input-search`: AI search chat bar with toggleable web search mode and animated indicators.
- `ai-loading`: Animated task execution log with scrolling terminal status and SVG spinner.
- `ai-text-loading`: Thinking indicator that cycles status messages with shimmering gradient text.
- `ai-voice`: Voice input button with pulse waveform animations, timer, and listening states.

### Backgrounds & Heros
- `beams-background`: Drifting light beams on HTML canvas with configurable intensity.
- `background-paths`: Flowing SVG line path animations drawn smoothly across hero banners.
- `shape-hero`: Floating translucent geometric shapes over a modern gradient backdrop.
- `flow-field`: Canvas particle flow field with noise-driven light streams and color themes.

### Cards & Grids
- `liquid-glass-card`: Apple-inspired liquid glass card with SVG refractive displacement filters.
- `bento-grid`: Responsive bento grid of feature cards with animated charts and counters.
- `spotlight-cards`: Feature card grid with ambient aurora glow and 3D magnetic tilt.
- `card-flip`: 3D flipping card on hover to reveal details and call to action.
- `card-stack`: Expandable card stack revealing product specs with spring physics.
- `mouse-effect-card`: Dot pattern card that repels away from the cursor.
- `tweet-card`: X/Twitter style post card with author info, reply thread, and hover gradient.
- `currency-transfer`: Multi-step exchange card with animated progress and checkmarks.
- `carousel-cards`: Horizontally scrolling card carousel with badges and navigation.

### Navigation & Drawers
- `morphic-navbar`: Active link morphs smoothly into a rounded pill indicator.
- `toolbar`: Figma-style floating toolbar expanding labels on tool selection.
- `smooth-tab`: Animated tab switcher with sliding active indicator.
- `profile-dropdown`: User account dropdown with subscription info and actions.
- `action-search-bar`: Fast command search bar with shortcut badges and suggested actions.
- `smooth-drawer`: Spring-based slide-in bottom drawer with staggered reveal.

### Buttons
- `particle-button`: Bursts animated particles outward on click with tactile scale press.
- `attract-button`: Magnetic button pulling nearby floating particles to center on hover.
- `gradient-button`: Multi-layer animated gradient with emerald, purple, and orange themes.
- `hold-button`: Press-and-hold confirmation button with animated fill and custom duration.
- `social-button`: Expands into a row of staggered social media share icons on hover.
- `command-button`: Keyboard shortcut button with Command glyph and shimmer sweep.
- `switch-button`: Light/dark theme toggle button with rotating sun/moon transitions.
- `slide-text-button`: Animated link button with vertical text roll on hover.

### Text & Typographic Effects
- `shimmer-text`: Looping gradient sweep across typography.
- `type-writer`: Multi-sequence typewriter effect with blinking cursor.
- `matrix-text`: Cyberpunk matrix scramble effect revealing final text.
- `glitch-text`: Customizable glitch effect with adjustable chromatic aberration.
- `dynamic-text`: Multi-language greeting cycle with smooth enter/exit animations.
- `scroll-text`: Scroll-driven word highlighting using IntersectionObserver.
- `sliced-text`: Text splits into offset slices and rejoins on hover.
- `swoosh-text`: Colorful layered shadow displacement on mouseover.

### Inputs & Uploaders
- `file-upload`: Drag-and-drop file upload with animated progress and validation states.
- `avatar-picker`: Multi-avatar selector with color rings and username inputs.
- `team-selector`: Overlapping avatar stack with spring increment/decrement controls.
- `loader`: Rotating gradient ring loaders with multiple sizes and labels.

---

## 3. Installation Methods

### Method 1: Using shadcn CLI (Recommended)
Once `@kokonutui` is added to `components.json`:
```bash
npx shadcn@latest add @kokonutui/particle-button
npx shadcn@latest add @kokonutui/liquid-glass-card
npx shadcn@latest add @kokonutui/beams-background
```

### Method 2: Direct URL Installation (No config needed)
You can directly install any component URL without altering `components.json`:
```bash
npx shadcn@latest add https://kokonutui.com/r/particle-button.json
npx shadcn@latest add https://kokonutui.com/r/morphic-navbar.json
```

### Method 3: Direct API / Inspection
To inspect the code or embed it directly in a non-CLI workflow:
```bash
curl -s https://kokonutui.com/r/<component-name>.json
```
The JSON contains the target path, required npm packages (`dependencies`), and full TypeScript source code (`content`).
