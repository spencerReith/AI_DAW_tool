# Generator Page Spec

## Overview
The page where a user describes and configures the beat they want generated. Follows directly from the launch page.

---

## Layout (top to bottom)

### 1. Title
- Text: **"beats"** (all lowercase), same as launch page
- Top left corner
- Same font size and weight

### 2. Beat Description
- Label: **"describe your beat"** (all lowercase, small caps label style matching the app)
- Large multiline textarea below the label
- Placeholder: something minimal like *"dark, slow, heavy bass..."*
- No border radius — sharp corners consistent with the rest of the UI
- Expands vertically to fill available space

### 3. BPM
- Label: **"bpm"** (all lowercase, same label style)
- Single-line number input, narrower — sits below the description box
- Placeholder: *"120"*
- No spinner arrows (appearance: none)

### 4. Generate Button
- Full width, same style as the "go" button / generate button in the existing app
- Label: **"generate"** (all lowercase)
- Disabled until both description and BPM are filled in

---

## Style Notes
- White background, black text — matches inverted launch page aesthetic
- Same font family (system-ui)
- Minimal — no extra decoration, no icons
- Labels use the small uppercase tracking style already in App.css (`.field-label`)
- Textarea and BPM input use same border style as `.vibe-input` (1.5px solid #000, no border-radius)
