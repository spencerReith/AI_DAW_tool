# Hum Page Remodel — Plan

## Overview

The hum page takes an audio recording of a hummed melody plus a text prompt, runs it through a multi-step pipeline, and delivers a MusicGen-produced track to the existing PlayerPage.

---

## UI

- MP3 file upload input
- Text prompt input (same style as the beat generator's description field)
- "Generate" button — disabled until both inputs are filled
- On completion: navigates to PlayerPage with the MusicGen output
- On error: shows error message inline

---

## Pipeline

### 1. Hum → Melody MIDI
- Upload audio to Replicate Basic Pitch
- Receive `melody.mid`

### 2. Chord Generation
- Run chord inference on `melody.mid` (music21, diatonic triads, one per bar)
- Merge melody + chords → `merged.mid`

### 3. Local Renders (saved to `generated/`)
- Render `melody.mid` → `HH_MM_SS_melody.mp3`
- Render `merged.mid` → `HH_MM_SS_full.mp3`

### 4. MusicGen
- Send `HH_MM_SS_full.mp3` + text prompt to MusicGen on Replicate
- Download output → save locally as `musicgen_HH_MM_SS.mp3`

### 5. PlayerPage
- Pass `musicgen_HH_MM_SS.mp3` local URL to the existing PlayerPage
- Same player experience as generated beats

---

## Backend Changes (`hum_app.py`)

- Add `prompt` field to the POST request body (alongside the audio file)
- After rendering full MP3, call MusicGen Replicate model with `full.mp3` + prompt
- Download and save MusicGen output to `generated/musicgen_{timestamp}.mp3`
- Return local URL of MusicGen output to frontend (same format as `/generate` endpoint)

## Frontend Changes (`HumPage`)

- Add text prompt input field
- On success: navigate to PlayerPage with the MusicGen audio URL (not just show a file path)
- Disable generate button until both file and prompt are provided

---

## Files Saved Per Run

| File | Description |
|------|-------------|
| `HH_MM_SS_melody.mp3` | Raw melody only, rendered from Basic Pitch MIDI |
| `HH_MM_SS_full.mp3` | Melody + chords rendered, used as MusicGen conditioning |
| `musicgen_HH_MM_SS.mp3` | Final MusicGen output, sent to PlayerPage |
