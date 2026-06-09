# Spec: Audio-to-Audio Frontend Redesign

## Overview

Add an optional seed audio section to the generator page, enabling Stable Audio 3's audio-to-audio (init audio) mode. The user can provide a seed in one of two ways: uploading a file, or recording directly into the mic ("sketch"). When no seed is provided, behavior is identical to the current text-to-audio flow.

---

## Layout Changes — GeneratorPage

Current field order:
1. describe your beat (textarea)
2. bpm / duration / variations (row)

New field order:
1. describe your beat (textarea)
2. **seed audio** section (new — optional)
3. bpm / duration / variations (row)

---

## Seed Audio Section

Label: `seed audio` with a subdued `(optional)` tag beside it.

Two side-by-side options for providing a seed:

### Option A — Upload
- Button: `+ choose file` when empty, filename when a file is selected
- Accepts `.mp3` and `.wav`
- An `×` clear button appears once a file is selected

### Option B — Sketch
- Button: `sketch` (mic recording — sing, hum, or play into the computer)
- Clicking starts recording from the browser mic (`MediaRecorder` API)
- Button label changes to `stop` while recording
- On stop, the recording becomes the seed (same slot as a file upload — only one seed at a time)
- An `×` clear button appears once a recording exists, labelled with e.g. `sketch (0:07)` showing duration

Only one seed can be active at a time. Selecting a file clears any existing sketch and vice versa.

### Noise Level Slider

- Appears to the right of whichever seed input is active, only after a seed exists
- Label: `noise level`
- Range: `0.1` to `1.0`, step `0.05`, default `0.5`
- Current value displayed inline (e.g. `noise level 0.50`)
- Lower = output stays closer to the seed; higher = more creative deviation
- Disappears (and resets to `0.5`) if the seed is cleared

---

## Behavior

- No seed → generate request sends text + bpm + duration + variations only (unchanged)
- Seed present → generate request sends text + bpm + duration + variations + audio blob + noise level (audio-to-audio mode)
- Generate button disabled logic unchanged: requires description + bpm, seed is never required

---

## State to Add

```
const [seedFile, setSeedFile]     = useState(null);   // File | Blob | null
const [seedLabel, setSeedLabel]   = useState('');     // display name or sketch duration
const [noiseLevel, setNoiseLevel] = useState(0.5);    // float
const [recording, setRecording]   = useState(false);  // mic is live
```

---

## Out of Scope for This Spec

- Backend changes to handle the audio seed and `init_noise_level` param
- Player page changes
