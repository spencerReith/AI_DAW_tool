# Hum-to-MP3 Pipeline — Spec

## Overview

A CLI Python program that takes an MP3 of a hummed melody and outputs a rendered MP3 with the melody plus inferred chord accompaniment. No pitch quantization, no rhythm quantization, no autotuning — the raw melody is preserved exactly as hummed. CREPE is used exclusively for pitch detection.

---

## Usage

```bash
python hum_to_mp3.py input.mp3 output.mp3 [options]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--onset-threshold` | `0.5` | Basic Pitch onset confidence cutoff (0–1) |
| `--frame-threshold` | `0.3` | Basic Pitch frame confidence cutoff (0–1) |
| `--min-note-length` | `127.7` | Minimum note duration in milliseconds |
| `--instrument` | `81` | GM program number for melody (sawtooth synth lead) |
| `--chord-instrument` | `89` | GM program number for chords (warm pad) |
| `--key` | auto-detect | Root key (e.g. `C`, `G`, `Bb`). Auto-detected via music21 if not provided |
| `--scale` | `major` | Scale type: `major` or `minor` |
| `--soundfont` | `FluidR3_GM.sf2` | Path to `.sf2` soundfont file |

---

## Pipeline (v1 — melody only)

### 1. Convert MP3 → WAV
- Use ffmpeg subprocess to convert input MP3 to WAV

### 2. Basic Pitch Detection → `melody.mid`
- Run `basic_pitch.inference.predict()` on the WAV with onset/frame thresholds and minimum note length
- Basic Pitch returns a `pretty_midi.PrettyMIDI` object directly — no manual frequency conversion or note grouping needed
- Write the MIDI object to `melody.mid`

### 4. Render → MP3
- FluidSynth renders `melody.mid` → WAV using the specified soundfont
- ffmpeg converts WAV → MP3

### 5. Cleanup
- All temp files deleted on exit (success or error)

---

## Deferred: Chord Generation (v2)

Chord gen code exists but is not wired into the pipeline yet. When re-enabled:

- Load `melody.mid` with music21, auto-detect key
- Infer one diatonic triad per bar, constrained to detected key
- Write `chords.mid`, merge with melody using mido (melody track 0, chords track 1)
- Render `merged.mid` instead of `melody.mid`

---

## App Integration

Accessible via a **"hum" button on the GeneratorPage** in the Electron app.

### Frontend (HumPage)
- MP3 file upload
- "Generate" button
- On success: shows local path of output melody MP3
- On error: shows error message

### Backend (`backend/hum_app.py`, port 5001)
- POST `/hum` — accepts MP3 upload, runs pipeline, returns output path
- Saves to `generated/hum_<timestamp>.mp3`

---

## File Structure

```
hum_to_mp3.py              # CLI entry point
backend/
  hum_app.py               # Flask wrapper (port 5001)
  pipeline/
    preprocess.py          # MP3 → WAV via ffmpeg
    pitch_detect.py        # CREPE pitch detection → melody.mid
    chord_infer.py         # music21 chord inference → chords.mid
    midi_merge.py          # mido merge → merged.mid
    render.py              # FluidSynth + ffmpeg → MP3
temp/                      # Auto-cleaned on exit
generated/                 # Output MP3s
```

---

## Dependencies

### Python
```
basic-pitch
music21
mido
soundfile
numpy
```

### System
```
fluidsynth
ffmpeg
FluidR3_GM.sf2   # or any GM soundfont
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Basic Pitch detects no notes | Exit with clear error message |
| Key detection confidence low | Default to C major, warn user |
| Soundfont not found | Clear error with install instructions |
| Input too short | Exit with error |

---

## Constraints

- **No autotuning, no pitch quantization, no rhythm quantization** — melody preserved exactly
- **CREPE only** for pitch detection — not librosa
- All temp files cleaned up on exit
- CLI-first; Flask wraps the same pipeline for the Electron app

---

## Out of Scope (v1)

- Drum/rhythm track
- Real-time input
- VST support
- Routing output back into the app's audio player
