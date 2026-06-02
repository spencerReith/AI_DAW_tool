# GeneratorPage Remodel Spec

## Scope
Changes are isolated to `GeneratorPage` in `frontend/src/App.jsx` and its styles in `frontend/src/App.css`.
Do not touch `LaunchPage`, `PlayerPage`, or `HumPage`.

---

## Change 1 — Mic icon (replaces "hum a melody" button)

**Component:** Replace the `<button className="hum-btn">hum a melody</button>` with a mic icon from `lucide-react`.

- Use the `Mic` icon from `lucide-react` (`import { Mic } from 'lucide-react'`)
- Position: fixed to the top-right corner of the viewport (`position: fixed; top: 24px; right: 24px`)
- Size: 22px
- On hover, show a tooltip that says "hum a melody" (use a CSS `title` attribute or a simple CSS tooltip — no library)
- Clicking it still calls `onHum()` exactly as the old button did
- Remove the `.hum-btn` CSS class entirely

---

## Change 2 — Input field modernization

**Textarea ("describe your beat"):**
- Remove the gap between the `.field-label` and the textarea — set `gap` on `.gen-field` to `4px`
- Remove the full border. Replace with a bottom border only: `border: none; border-bottom: 1.5px solid #000`
- Remove border-radius (already 0, keep it)
- Set `caret-color: #000` and use a blinking underscore as the placeholder: replace placeholder text `"dark, slow, heavy bass..."` with `"_"` and animate it with a CSS `@keyframes` blink on the `::placeholder` pseudo-element (opacity 0 → 1, 1s step-start infinite)
- No focus outline (`outline: none` already set, keep it)

**BPM / Duration / Variations inputs:**
- Apply the same bottom-border-only treatment as the textarea
- Reduce the gap in `.gen-row` between label and input to `4px` (same as above)

---

## Change 3 — Generate button modernization

**Appearance:**
- Keep the full-width black button, but make the font `13px`, `font-weight: 400`, `letter-spacing: 0.12em`, `text-transform: uppercase`
- Reduce padding to `11px 14px`

**Loading animation (typewriter effect):**
- When `loading === true`, cycle the button text through `"generating."` → `"generating.."` → `"generating..."` → back to `"generating."`, changing every 400ms
- Implement with a `useEffect` + `setInterval` inside `GeneratorPage` that runs only when `loading` is true
- Button remains `disabled` during loading (no change to existing logic)
