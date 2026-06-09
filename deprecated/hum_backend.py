# Deprecated: hum route removed from main app
# This was the /hum endpoint in backend/app.py, along with its MusicGen prompt setup
# and the pipeline imports it relied on.

import math
import shutil
import subprocess
import tempfile
import os

from imageio_ffmpeg import get_ffmpeg_exe
from music21 import converter
import mido
import replicate
import anthropic
import requests as http_requests

from pipeline.chord_infer import infer_chords
from pipeline.midi_merge import merge
from pipeline.render import render

_musicgen_guide_path = os.path.join(os.path.dirname(__file__), '..', 'prompt_guides', 'musicgen_prompting.md')
with open(_musicgen_guide_path, 'r') as f:
    MUSICGEN_GUIDE = f.read()

MUSICGEN_SYSTEM_PROMPT = f"""You are a prompt engineer for Meta's MusicGen model.

The user has hummed or recorded a melody. MusicGen will use that melody as a conditioning input and reimagine it in a new style. Your job is to take the user's style description and rewrite it into a single MusicGen prompt string that captures how the melody should be reimagined.

Use the guide below to write a prompt that directs MusicGen toward the target style, mood, and instrumentation — while staying true to what the user described.

Rules:
- Output the prompt string only. No explanation, no markdown, no labels.
- Use natural language sentences, not pipe-delimited fields.
- Do not invent elements the user did not describe or imply.
- Use vocabulary and phrasing drawn directly from the guide examples.
- Keep it concise — every word should add meaningful context.

--- MUSICGEN PROMPT GUIDE ---
{MUSICGEN_GUIDE}
"""


# Step 2: hum route — mp3 hum → melody MIDI → chords → MusicGen
def hum(request, claude, log, GENERATED_DIR):
    from flask import jsonify
    if 'file' not in request.files:
        return jsonify({'error': 'no file provided'}), 400

    mp3_file = request.files['file']
    prompt   = request.form.get('prompt', '').strip()

    if not mp3_file.filename.lower().endswith('.mp3'):
        return jsonify({'error': 'file must be an .mp3'}), 400
    if not prompt:
        return jsonify({'error': 'prompt is required'}), 400

    log(f'[musicgen] prompt="{prompt}" input="{mp3_file.filename}"')

    try:
        msg = claude.messages.create(
            model='claude-opus-4-8',
            max_tokens=256,
            system=MUSICGEN_SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': prompt}]
        )
        rewritten_prompt = msg.content[0].text.strip()
        log(f'[musicgen] claude rewritten prompt="{rewritten_prompt}"')
    except Exception as e:
        rewritten_prompt = prompt
        log(f'[musicgen] claude error, falling back to raw prompt: {e}')

    temp_dir = tempfile.mkdtemp()
    try:
        import datetime
        input_mp3 = os.path.join(temp_dir, 'input.mp3')
        mp3_file.save(input_mp3)

        input_wav = os.path.join(temp_dir, 'input.wav')
        subprocess.run(
            [get_ffmpeg_exe(), '-y', '-i', input_mp3, input_wav],
            check=True, capture_output=True
        )

        with open(input_wav, 'rb') as f:
            midi_output = replicate.run(
                'rhelsing/basic-pitch:a7cf33cf63fca9c71f2235332af5a9fdfb7d23c459a0dc429daa203ff8e80c78',
                input={'audio_file': f}
            )

        melody_midi = os.path.join(temp_dir, 'melody.mid')
        with open(melody_midi, 'wb') as f:
            f.write(midi_output.read())

        key_obj     = converter.parse(melody_midi).analyze('key')
        chord_midi  = infer_chords(melody_midi, key_obj, 120, temp_dir)
        merged_midi = os.path.join(temp_dir, 'merged.mid')
        merge(melody_midi, chord_midi, merged_midi)

        musicgen_duration = min(30, math.ceil(mido.MidiFile(merged_midi).length))

        timestamp  = datetime.datetime.now().strftime('%H_%M_%S')
        melody_mp3 = os.path.join(GENERATED_DIR, f'{timestamp}_melody.mp3')
        full_mp3   = os.path.join(GENERATED_DIR, f'{timestamp}_full.mp3')
        render(melody_midi, melody_mp3, temp_dir)
        render(merged_midi, full_mp3,   temp_dir)
        log(f'[musicgen] full render="{timestamp}_full.mp3"')

        with open(full_mp3, 'rb') as f:
            musicgen_output = replicate.run(
                'meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb',
                input={
                    'prompt':                 rewritten_prompt,
                    'melody':                 f,
                    'model_version':          'stereo-melody-large',
                    'output_format':          'mp3',
                    'normalization_strategy': 'peak',
                    'duration':               musicgen_duration,
                }
            )

        musicgen_url   = musicgen_output.url if hasattr(musicgen_output, 'url') else str(musicgen_output)
        musicgen_bytes = http_requests.get(musicgen_url).content
        musicgen_mp3   = os.path.join(GENERATED_DIR, f'musicgen_{timestamp}.mp3')
        with open(musicgen_mp3, 'wb') as f:
            f.write(musicgen_bytes)

        log(f'[musicgen] output="musicgen_{timestamp}.mp3"')
        local_url = f'http://localhost:5001/generated/musicgen_{timestamp}.mp3'
        return jsonify({'audio_url': local_url})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
