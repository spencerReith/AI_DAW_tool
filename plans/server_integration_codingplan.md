# Server Integration Coding Plan

## Goal
Merge `hum_app.py` into `app.py` so there is one Flask server on port 5000.

---

## Steps

### Step 1 — Add missing imports to `app.py`
Add the imports that exist in `hum_app.py` but not `app.py`:
- `sys`, `tempfile`, `shutil`, `subprocess`, `math`
- `imageio_ffmpeg.get_ffmpeg_exe`
- `music21.converter`
- `pipeline.chord_infer.infer_chords`, `pipeline.midi_merge.merge`, `pipeline.render.render`
- Add `sys.path.insert(0, os.path.dirname(__file__))` so pipeline imports resolve

### Step 2 — Add the `/hum` route to `app.py`
Copy the `hum()` function from `hum_app.py` into `app.py` exactly as-is.

### Step 3 — Fix the hardcoded port in `/hum` response
In `hum_app.py` line 116, the returned URL hardcodes port `5001`:
```
local_url = f'http://localhost:5001/generated/musicgen_{timestamp}.mp3'
```
Change it to port `5000` so it matches the merged server.

### Step 4 — Delete `hum_app.py`
The file is no longer needed once its logic lives in `app.py`.

---

## What does NOT change
- All existing routes in `app.py` (`/health`, `/parse`, `/generate`, `/generated/<filename>`)
- Frontend code (no changes per the spec)
- Port (stays 5000)
