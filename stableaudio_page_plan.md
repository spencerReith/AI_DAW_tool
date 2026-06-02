# GeneratorPage Remodel — Coding Plan

## Steps

### 1 — Install lucide-react
Run `npm install lucide-react` in `frontend/`.

### 2 — Add Mic icon, remove hum button (App.jsx)
- Import `Mic` from `lucide-react` at the top of `App.jsx`
- In `GeneratorPage`, remove `<button className="hum-btn">hum a melody</button>`
- Add a fixed-position `<button>` wrapping `<Mic size={22} />` with a `title="hum a melody"` attribute that calls `onHum()`

### 3 — Add typewriter loading state (App.jsx)
- Add a `loadingText` state variable initialized to `'generate'`
- Add a `useEffect` that runs when `loading` changes: when `loading` is true, start a `setInterval` (400ms) cycling `'generating.'` → `'generating..'` → `'generating...'`; clear the interval when `loading` becomes false and reset text to `'generate'`
- Replace the button label `{loading ? 'generating...' : 'generate'}` with `{loadingText}`

### 4 — Update textarea styles (App.css)
- `.gen-field`: change `gap` from `10px` to `4px`
- `.gen-textarea`: replace `border: 1.5px solid #000` with `border: none; border-bottom: 1.5px solid #000`; add `caret-color: #000`
- `.gen-textarea::placeholder`: add `@keyframes blink { 50% { opacity: 0 } }` and apply `animation: blink 1s step-start infinite`
- Change placeholder text in JSX from `"dark, slow, heavy bass..."` to `"_"`

### 5 — Update BPM/duration/variations input styles (App.css)
- `.gen-bpm`: replace `border: 1.5px solid #000` with `border: none; border-bottom: 1.5px solid #000`

### 6 — Update generate button styles (App.css)
- `.generate-btn`: set `font-size: 13px`, `font-weight: 400`, `letter-spacing: 0.12em`, `text-transform: uppercase`, `padding: 11px 14px`

### 7 — Add mic button CSS (App.css)
- Add `.mic-btn` class: `position: fixed; top: 24px; right: 24px; background: none; border: none; cursor: pointer; color: #000; padding: 0`
- Add `.mic-btn:hover { color: #555 }`
- Remove `.hum-btn` styles entirely
