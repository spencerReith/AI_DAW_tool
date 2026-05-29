from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import mido
import replicate
import io  # used by mido to read file bytes
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

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

# Step 7: call Replicate Stable Audio 2.5; returns MP3 URL
@app.route('/generate', methods=['POST'])
def generate():
    body = request.get_json()
    bpm = body.get('bpm', 120)
    time_sig = body.get('time_signature', '4/4')
    key = body.get('key')
    accompaniment = body.get('accompaniment', '').lower()
    vibe = body.get('vibe', '').strip()

    parts = [f'{accompaniment} track', f'{bpm}bpm', time_sig]
    if key:
        parts.append(key)
    if vibe:
        parts.append(vibe)
    prompt = ', '.join(parts)

    try:
        duration = body.get('duration', 90)
        output = replicate.run(
            'stability-ai/stable-audio-2.5',
            input={'prompt': prompt, 'duration': duration}
        )
        return jsonify({'audio_url': output.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 502

if __name__ == '__main__':
    app.run(port=5000)
