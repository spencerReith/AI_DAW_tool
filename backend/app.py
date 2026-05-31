from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import mido
import replicate
import anthropic
import io
import os
import datetime
import requests as http_requests

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# Load stable audio prompt guide once at startup
_guide_path = os.path.join(os.path.dirname(__file__), '..', 'stable_audio_prompt_guide.md')
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
        except Exception as e:
            prompt = raw_prompt
            print(f'[claude] variation {index} error, falling back: {e}')

        output = replicate.run('stability-ai/stable-audio-2.5', input={'prompt': prompt, 'duration': duration})
        audio_bytes = http_requests.get(output.url).content

        filename = f'beat_{timestamp}_{index}.mp3'
        with open(os.path.join(GENERATED_DIR, filename), 'wb') as f:
            f.write(audio_bytes)

        return f'http://localhost:5000/generated/{filename}'
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

if __name__ == '__main__':
    app.run(port=5000)
