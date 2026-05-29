# Launch Page Spec — "beats"

## Overview
A fullscreen launch/splash page that greets the user before entering the main tool.

---

## Layout (top to bottom)

### 1. Title
- Text: **"beats"** (all lowercase)
- Positioned at the top center of the screen
- Large, bold, clean font

### 2. ASCII Art — Rick Rubin
- Centered on screen
- Animates in character-by-character (typewriter style), writing out from top-left to bottom-right
- ASCII art provided by user (portrait of Rick Rubin)
- Monospace font to preserve ASCII art alignment

### 3. "Go" Button
- Single button, centered below the ASCII art
- Label: **"go"** (all lowercase, consistent with title style)
- Clicking it navigates into the main app

---

## Behavior
- Page loads → title appears immediately
- ASCII art begins writing out (typewriter animation)
- "go" button appears **only after** the animation completes
- Clicking "go" transitions to the main app view

---

## Style Notes
- Dark background (consistent with DAW aesthetic)
- Minimal — no extra UI elements, no nav, no footer
- Monospace font for ASCII art; title/button can use a display font
