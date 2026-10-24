import sys
import os
import io
import time
import datetime

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import mido
import anthropic
import requests as http_requests

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'app.log')
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_PATH, 'a') as f:
        f.write(f'[{timestamp}] {msg}\n')

# Load stable audio 3 prompt guide once at startup
_guide_path = os.path.join(os.path.dirname(__file__), '..', 'stable-audio-3-prompting.md')
with open(_guide_path, 'r') as f:
    STABLE_AUDIO_GUIDE = f.read()

SYSTEM_PROMPT = f"""You are a prompt engineer for Stability AI's Stable Audio 3 model.

Your only job is to rewrite a user's beat description into a single Stable Audio 3 prompt string.

Follow the guide below exactly. Structure the output in this order:
1. Core style/genre (with subgenre if applicable)
2. Key instruments — primary, supporting, rhythm, texture
3. Mood & energy descriptors (precise, evocative language — not generic words like "happy" or "sad")
4. BPM (always include the exact value provided)
5. Any relevant production characteristics (recording quality, arrangement style, era references)
6. Where appropriate, include AudioSparx tags (e.g. TrackType: Music, VocalType: Instrumental, Genre: ..., Instruments: ...)

Rules:
- Output the prompt string only. No explanation, no markdown, no labels.
- Use natural language sentences. AudioSparx tags may be appended at the end.
- Do not invent elements the user did not describe or imply.
- Use specific instrument names (e.g. "808 kick" over "bass drum", "pedal steel guitar" over "guitar").
- Use vocabulary and phrasing drawn directly from the guide examples.
- Keep it concise — every word should add meaningful context.

--- STABLE AUDIO 3 PROMPT GUIDE ---
{STABLE_AUDIO_GUIDE}
"""

claude = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_KEY'))

STABILITY_KEY      = os.environ.get('STABILITY_KEY')
STABILITY_URL      = 'https://api.stability.ai/v2beta/audio/stable-audio/text-to-audio'
STABILITY_POLL     = 'https://api.stability.ai/v2beta/audio/results/{}'

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


def rewrite_prompt(system, description, bpm, tag, index):
    """Claude rewrites description into a Stable Audio prompt; falls back to raw text on error."""
    try:
        msg = claude.messages.create(
            model='claude-opus-4-8',
            max_tokens=256,
            system=system,
            messages=[{'role': 'user', 'content': f'Description: {description}\nBPM: {bpm}'}]
        )
        prompt = msg.content[0].text.strip()
        print(f'[claude] variation {index}: {prompt}')
        log(f'[{tag}] variation {index} claude prompt="{prompt}"')
        return prompt
    except Exception as e:
        print(f'[claude] variation {index} error, falling back: {e}')
        return f'{description}, {bpm} BPM'


def run_stability(url, files, data, tag, timestamp, index):
    """Start a Stable Audio job, poll until done, save mp3. Returns relative URL."""
    headers = {'authorization': f'Bearer {STABILITY_KEY}', 'accept': 'audio/*'}
    res = http_requests.post(url, headers=headers, files=files, data=data)
    if res.status_code != 202:
        raise Exception(f'stability start failed: {res.json()}')

    generation_id = res.json()['id']
    while True:
        poll = http_requests.get(STABILITY_POLL.format(generation_id), headers=headers)
        if poll.status_code == 202:
            time.sleep(3)
        elif poll.status_code == 200:
            break
        else:
            raise Exception(f'stability poll failed: {poll.json()}')

    return save_audio(poll.content, tag, timestamp, index)


def save_audio(audio_bytes, tag, timestamp, index):
    """Save mp3 bytes to GENERATED_DIR. Returns relative URL."""
    filename = f'beat_{timestamp}_{index}.mp3'
    with open(os.path.join(GENERATED_DIR, filename), 'wb') as f:
        f.write(audio_bytes)

    log(f'[{tag}] variation {index} output="{filename}"')
    return f'/generated/{filename}'  # relative; frontend prefixes API host


def generate_one(description, bpm, duration, timestamp, index):
    """One text-to-audio variation. Returns relative URL or None."""
    try:
        prompt = rewrite_prompt(SYSTEM_PROMPT, description, bpm, 'stable-audio', index)
        return run_stability(STABILITY_URL, {'none': ''},
                             {'prompt': prompt, 'output_format': 'mp3', 'duration': duration},
                             'stable-audio', timestamp, index)
    except Exception as e:
        print(f'[generate_one] variation {index} failed: {e}')
        return None


def run_variations(fn, variations, *args):
    """Run fn(*args, index) in parallel; returns JSON response with successful URLs."""
    with ThreadPoolExecutor(max_workers=variations) as ex:
        futures = [ex.submit(fn, *args, i + 1) for i in range(variations)]
        audio_urls = [u for u in (f.result() for f in futures) if u is not None]
    if not audio_urls:
        return jsonify({'error': 'all variations failed'}), 502
    return jsonify({'audio_urls': audio_urls})


@app.route('/generate', methods=['POST'])
def generate():
    timestamp   = datetime.datetime.now().strftime('%H_%M_%S')
    body        = request.get_json()
    description = body.get('description', '').strip()
    bpm         = body.get('bpm', 120)
    duration    = max(1, min(int(body.get('duration', 90)), 380))
    variations  = max(1, min(int(body.get('variations', 1)), 4))

    print(f'[request] description="{description}" bpm={bpm} duration={duration} variations={variations}')
    log(f'[stable-audio] prompt="{description}" bpm={bpm} duration={duration} variations={variations}')
    return run_variations(generate_one, variations, description, bpm, duration, timestamp)


# Seed audio (audio-to-audio) is desktop-only; set ENABLE_SEED=0 for the web deploy
if os.environ.get('ENABLE_SEED', '1') == '1':
    from seed import init_seed
    init_seed(app, rewrite_prompt, save_audio, run_variations, log)

@app.route('/generated/<filename>')
def serve_generated(filename):
    return send_from_directory(GENERATED_DIR, filename)

# Web deploy: serve built frontend (frontend/dist) for all other GET paths
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and os.path.isfile(os.path.join(FRONTEND_DIST, path)):
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, 'index.html')

if __name__ == '__main__':
    app.run(port=int(os.environ.get('PORT', 5001)))  # PORT set by Cloud Run
