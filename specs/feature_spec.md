# AI Accompaniment Tool — POC Feature Spec (V1)

## Overview

A desktop application that reads a MIDI file exported from a DAW, analyzes its musical properties, and uses MusicGen (via HuggingFace API) to generate a new accompaniment track, returned as a downloadable `.mid` or audio file the user drags into their DAW.

---

## Stack

| Layer | Technology |
|---|---|
| Desktop shell | Electron |
| Frontend UI | React |
| Backend | Python / Flask (local subprocess) |
| Music generation | MusicGen via HuggingFace Inference API |
| MIDI parsing | `mido` or `music21` |
| Output format | `.wav` audio file (V1) |

---

## Scope

### In Scope (V1)
- MIDI file ingestion via drag-and-drop or file picker
- Automatic extraction of tempo and time signature from MIDI
- User selects accompaniment type (see below)
- Generation request sent to HuggingFace MusicGen API
- Generated audio returned as downloadable `.wav` file
- Basic status/progress feedback during generation

### Out of Scope (V1 — planned for V2+)
- IAC MIDI bus / direct DAW injection

---

## User Flow

```
1. User opens the app
2. User drags a MIDI file (exported from GarageBand or Logic) into the app
3. App parses the MIDI: extracts tempo, time signature, key (best effort)
4. User sees a summary: "120 BPM · 4/4 · Key of A minor"
5. User selects accompaniment type (drums / bass / melody)
6. User hits "Generate"
7. App sends a prompt + musical context to MusicGen via HuggingFace API
8. Progress indicator shown during generation (typically 10–30 seconds)
9. Generated .wav file is available to download
10. User drags the file into a new track in GarageBand / Logic
```

---

## UI Screens

### Screen 1 — Drop Zone
- App name / logo
- Large drag-and-drop zone: "Drop your MIDI file here"
- Or "Browse file" link
- Clean, minimal — nothing else until a file is loaded

### Screen 2 — Session Summary
Shown after MIDI is parsed:
- Detected tempo (BPM)
- Detected time signature
- Detected key / scale (if resolvable)
- Warning if time signature is non-standard (not 4/4)
- Accompaniment type selector: Drums · Bass · Melody (radio or segmented control)
- Optional: short text prompt field ("describe the vibe, e.g. 'dark, lo-fi, sparse'")
- "Generate" button

### Screen 3 — Generating
- Progress indicator (spinner or animated waveform)
- Estimated wait time
- Cancel option

### Screen 4 — Result
- "Your track is ready"
- Download `.wav` button
- "Generate another variation" button (re-runs with same settings)
- "Start over" link

---

## MusicGen Integration

### Prompt Construction
The app constructs a MusicGen prompt from the parsed MIDI data:

```
"{accompaniment_type} track, {tempo}bpm, {time_signature}, {key}, {user_vibe_description}"
```

Example:
```
"bass line, 120bpm, 4/4, A minor, dark lo-fi sparse"
```

### API Call
- Model: `facebook/musicgen-small` (fast, free tier) or `facebook/musicgen-medium` (higher quality)
- Via: HuggingFace Inference API (free tier to start)
- Output: `.wav` audio file
- Duration: target 15–30 seconds (one loop / phrase)

### Tempo Conditioning
MusicGen accepts BPM as a conditioning parameter — the extracted tempo from the MIDI is passed directly to constrain the generation rhythmically.

---

## MIDI Parsing

Using `mido` or `music21` to extract:

| Property | Method |
|---|---|
| Tempo (BPM) | Read `set_tempo` message from MIDI header |
| Time signature | Read `time_signature` meta message |
| Key | Read `key_signature` meta message (if present) |
| Duration | Calculate from total ticks + tempo |

If key is not present in MIDI metadata, app displays "Key: Unknown" and omits from prompt — does not attempt to infer.

---

## DAW Compatibility

| DAW | Supported |
|---|---|
| GarageBand (Mac) | ✅ MIDI export in, audio file out |
| Logic Pro (Mac) | ✅ MIDI export in, audio file out |
| Other DAWs | ✅ (DAW-agnostic by design) |
| Windows DAWs | ✅ (Electron is cross-platform, no Mac-only features in V1) |

---

## V2 Planned Features
- IAC MIDI bus output — send generated track directly into DAW
- Per-track selection from multi-track MIDI export
- Audio stem input (not just MIDI)
- Local model inference (Apple Silicon MPS support)
- ACE-Step Singing2Accompaniment integration (when mature)

---

## Open Questions (Pre-Build)
- HuggingFace free tier rate limits — may need a paid key for sustained use
- MusicGen tempo conditioning reliability in practice — needs testing
- Whether to target `musicgen-small` or `musicgen-medium` for POC quality bar
- Electron + Python subprocess communication approach (REST vs stdio)