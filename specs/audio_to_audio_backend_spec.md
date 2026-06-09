# Spec: Audio-to-Audio Backend

## Overview

Update `/generate` to handle two paths:
- **Text-only** (existing): JSON body, calls `POST /v2beta/audio/stable-audio/text-to-audio`
- **Audio + text** (new): FormData body with a seed file, calls `POST /v2beta/audio/stable-audio/audio-to-audio`

Both paths use Claude to rewrite the prompt first, but with different system prompts. Both support multiple variations in parallel. Both use the same polling loop.

---

## Route Detection

`/generate` currently expects JSON. When a seed is present the frontend sends FormData. Detect the path by checking `request.content_type`:

- `application/json` → text-only path (no change to existing logic)
- `multipart/form-data` → audio-to-audio path

---

## Seed Format Conversion

The Stability AI audio-to-audio endpoint only accepts `mp3` and `wav`.

- If the uploaded file is `.mp3` or `.wav` → send as-is
- If the uploaded file is `.webm` (sketch recording from browser `MediaRecorder`) → convert to `.wav` using ffmpeg before sending

Use `imageio_ffmpeg.get_ffmpeg_exe()` for the conversion (already a project dependency, lives in `deprecated/hum_backend.py`).

---

## Prompt Rewriter — Audio-to-Audio Agent

Add a second system prompt `SYSTEM_PROMPT_A2A` alongside the existing `SYSTEM_PROMPT`. Same structure and rules, but the preamble explicitly tells Claude that a seed audio file is attached and the generated audio will be a transformation of it — so the prompt should describe the *target style* the seed is being transformed into, not a standalone track.

---

## New Helper: `generate_one_audio`

Mirror of `generate_one` for the audio-to-audio path. Signature:

```python
def generate_one_audio(description, bpm, seed_path, strength, duration, timestamp, index):
```

Steps:
1. Claude rewrite using `SYSTEM_PROMPT_A2A` (fall back to raw description on error)
2. POST to `https://api.stability.ai/v2beta/audio/stable-audio/audio-to-audio`
   - `files={'audio': open(seed_path, 'rb')}`
   - `data={'prompt': prompt, 'output_format': 'mp3', 'duration': duration, 'strength': strength}`
3. Assert 202, extract `generation_id`
4. Poll `GET /v2beta/audio/results/{generation_id}` every 3 seconds (same as text path)
5. Save bytes → `generated/beat_{timestamp}_{index}.mp3`
6. Return local URL

---

## Updated `/generate` Route

```python
@app.route('/generate', methods=['POST'])
def generate():
    if request.content_type.startswith('multipart/form-data'):
        # audio-to-audio path
        description = request.form.get('description', '').strip()
        bpm         = request.form.get('bpm', 120)
        duration    = max(1, min(int(request.form.get('duration', 90)), 380))
        variations  = max(1, min(int(request.form.get('variations', 1)), 4))
        strength    = max(0.0, min(float(request.form.get('noise_level', 0.5)), 1.0))
        seed_file   = request.files['seed']
        # save + convert if needed → seed_path (temp file)
        # run generate_one_audio x variations in ThreadPoolExecutor
    else:
        # existing text-only path — no changes
```

Seed file is saved to a temp file, converted if `.webm`, then path passed to each `generate_one_audio` call. Temp file cleaned up after all variations complete.

---

## Imports to Restore

These were removed when hum was deprecated but are needed again:

- `import subprocess`
- `import tempfile`  
- `import shutil`
- `from imageio_ffmpeg import get_ffmpeg_exe`

---

## Logging

- Log `[stable-audio-a2a]` prefix for audio-to-audio generations to distinguish from text-only in `app.log`
- Log `strength`, `seed filename`, and claude rewritten prompt

---

## No Frontend Changes

The frontend already sends the correct FormData shape. This spec is purely backend.
