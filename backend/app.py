import sys
import os
import io
import math
import shutil
import subprocess
import tempfile
import datetime

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from imageio_ffmpeg import get_ffmpeg_exe
from music21 import converter
import mido
import replicate
import anthropic
import requests as http_requests

from pipeline.chord_infer import infer_chords
from pipeline.midi_merge import merge
from pipeline.render import render

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'app.log')
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_PATH, 'a') as f:
        f.write(f'[{timestamp}] {msg}\n')

# Load stable audio prompt guide once at startup
_guide_path = os.path.join(os.path.dirname(__file__), '..', 'prompt_guides', 'stable_audio_prompt_guide.md')
with open(_guide_path, 'r') as f:
    STABLE_AUDIO_GUIDE = f.read()

SYSTEM_PROMPT = f"""You are a prompt engineer for Stability AI's Stable Audio 2.5 model.

Your only job is to rewrite a user's beat description into a single Stable Audio prompt string.

Follow the guide below exactly. Structure the output in this order:
1. Core style/genre (with subgenre if applicable)
2. Use case phrase (e.g. "perfect for a long drive")
3. Key instruments — primary, supporting, rhythm, texture
4. Mood descriptors (precise, evocative language — not generic words like "happy" or "sad")
5. BPM (always include the exact value provided)
6. Any relevant production characteristics (recording quality, arrangement style, era references)

Rules:
- Output the prompt string only. No explanation, no markdown, no labels.
- Use natural language sentences, not pipe-delimited fields.
- Do not invent elements the user did not describe or imply.
- Use specific instrument names (e.g. "808 kick" over "bass drum", "pedal steel guitar" over "guitar").
- Use vocabulary and phrasing drawn directly from the guide examples.
- Keep it concise — every word should add meaningful context.

--- STABLE AUDIO PROMPT GUIDE ---
{STABLE_AUDIO_GUIDE}
"""

claude = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_KEY'))

# Load musicgen prompt guide once at startup
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

app = Flask(__name__)
CORS(app)  # Step 4: allow requests from Electron renderer (localhost:5173)

# Step 2: health check
@app.route('/health')
def health():
    return {'status': 'ok'}

# Step 5: MIDI parsing — extract BPM, time signature, key
@app.route('/parse', methods=['POST'])
def parse():
    if 'file' not in request.files:
        return jsonify({'error': 'no file provided'}), 400

    mid = mido.MidiFile(file=io.BytesIO(request.files['file'].read()))

    bpm = 120
    time_sig = '4/4'
    key = None  # not inferred if absent

    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                bpm = round(mido.tempo2bpm(msg.tempo))
            elif msg.type == 'time_signature':
                time_sig = f'{msg.numerator}/{msg.denominator}'
            elif msg.type == 'key_signature':
                key = msg.key

    return jsonify({'bpm': bpm, 'time_signature': time_sig, 'key': key})

GENERATED_DIR = os.path.join(os.path.dirname(__file__), '..', 'generated')
os.makedirs(GENERATED_DIR, exist_ok=True)


def generate_one(description, bpm, duration, timestamp, index):
    """Run one variation: Claude rewrite → Stable Audio → save. Returns local URL or None."""
    try:
        raw_prompt = f'{description}, {bpm} BPM'
        try:
            msg = claude.messages.create(
                model='claude-opus-4-8',
                max_tokens=256,
                system=SYSTEM_PROMPT,
                messages=[{'role': 'user', 'content': f'Description: {description}\nBPM: {bpm}'}]
            )
            prompt = msg.content[0].text.strip()
            print(f'[claude] variation {index}: {prompt}')
            log(f'[stable-audio] variation {index} claude prompt="{prompt}"')
        except Exception as e:
            prompt = raw_prompt
            print(f'[claude] variation {index} error, falling back: {e}')

        output = replicate.run('stability-ai/stable-audio-2.5', input={'prompt': prompt, 'duration': duration})
        audio_bytes = http_requests.get(output.url).content

        filename = f'beat_{timestamp}_{index}.mp3'
        with open(os.path.join(GENERATED_DIR, filename), 'wb') as f:
            f.write(audio_bytes)

        log(f'[stable-audio] variation {index} output="{filename}"')
        return f'http://localhost:5001/generated/{filename}'
    except Exception as e:
        print(f'[generate_one] variation {index} failed: {e}')
        return None


@app.route('/generate', methods=['POST'])
def generate():
    body = request.get_json()
    description = body.get('description', '').strip()
    bpm        = body.get('bpm', 120)
    duration   = max(1, min(int(body.get('duration', 90)), 190))
    variations = max(1, min(int(body.get('variations', 1)), 4))

    print(f'[request] description="{description}" bpm={bpm} duration={duration} variations={variations}')
    log(f'[stable-audio] prompt="{description}" bpm={bpm} duration={duration} variations={variations}')

    timestamp = datetime.datetime.now().strftime('%H_%M_%S')

    with ThreadPoolExecutor(max_workers=variations) as ex:
        futures = [ex.submit(generate_one, description, bpm, duration, timestamp, i + 1) for i in range(variations)]
        audio_urls = [f.result() for f in futures]

    audio_urls = [u for u in audio_urls if u is not None]
    if not audio_urls:
        return jsonify({'error': 'all variations failed'}), 502

    return jsonify({'audio_urls': audio_urls})

@app.route('/generated/<filename>')
def serve_generated(filename):
    return send_from_directory(GENERATED_DIR, filename)


# Step 2: hum route — mp3 hum → melody MIDI → chords → MusicGen
@app.route('/hum', methods=['POST'])
def hum():
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
        input_mp3 = os.path.join(temp_dir, 'input.mp3')
        mp3_file.save(input_mp3)

        # MP3 → WAV for Basic Pitch
        input_wav = os.path.join(temp_dir, 'input.wav')
        subprocess.run(
            [get_ffmpeg_exe(), '-y', '-i', input_mp3, input_wav],
            check=True, capture_output=True
        )

        # Hum WAV → melody MIDI via Basic Pitch on Replicate
        with open(input_wav, 'rb') as f:
            midi_output = replicate.run(
                'rhelsing/basic-pitch:a7cf33cf63fca9c71f2235332af5a9fdfb7d23c459a0dc429daa203ff8e80c78',
                input={'audio_file': f}
            )

        melody_midi = os.path.join(temp_dir, 'melody.mid')
        with open(melody_midi, 'wb') as f:
            f.write(midi_output.read())

        # Chord generation + merge
        key_obj     = converter.parse(melody_midi).analyze('key')
        chord_midi  = infer_chords(melody_midi, key_obj, 120, temp_dir)
        merged_midi = os.path.join(temp_dir, 'merged.mid')
        merge(melody_midi, chord_midi, merged_midi)

        # Duration for MusicGen: match merged MIDI length, ceil, cap at 30s
        musicgen_duration = min(30, math.ceil(mido.MidiFile(merged_midi).length))

        # Render and save melody + full locally
        timestamp  = datetime.datetime.now().strftime('%H_%M_%S')
        melody_mp3 = os.path.join(GENERATED_DIR, f'{timestamp}_melody.mp3')
        full_mp3   = os.path.join(GENERATED_DIR, f'{timestamp}_full.mp3')
        render(melody_midi, melody_mp3, temp_dir)
        render(merged_midi, full_mp3,   temp_dir)
        log(f'[musicgen] full render="{timestamp}_full.mp3"')

        # Send full MP3 + prompt to MusicGen (melody-conditioned)
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

        # Download and save MusicGen result
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

if __name__ == '__main__':
    app.run(port=5001)
