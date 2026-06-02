# Logging Plan

## Overview
Append-only logging to a single `logs/app.log` txt file. Each entry is timestamped.
All logging lives in `backend/app.py`.

---

## Steps

### Step 1 — Create log helper
Add a `log(msg)` function at the top of `app.py` that:
- Appends a line to `logs/app.log` in the format: `[YYYY-MM-DD HH:MM:SS] msg`
- Creates the `logs/` directory if it doesn't exist

### Step 2 — Log StableAudio calls
In `generate()`, log before dispatching to the thread pool:
- User prompt (description)
- BPM, duration, variations requested

In `generate_one()`, log after each event:
- Claude's reworded prompt for each variation
- The output filename for each variation

### Step 3 — Log MusicGen calls
In `hum()`, log:
- User prompt
- Input file name (uploaded mp3)
- The name of the rendered full mp3 (`{timestamp}_full.mp3`)
- The name of the MusicGen output file (`musicgen_{timestamp}.mp3`)
