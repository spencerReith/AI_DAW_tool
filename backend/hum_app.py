import os
import sys
import datetime
import tempfile
import shutil
import subprocess
import math
import mido

sys.path.insert(0, os.path.dirname(__file__))

from imageio_ffmpeg import get_ffmpeg_exe
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from music21 import converter
import replicate
import requests as http_requests

from pipeline.chord_infer import infer_chords
from pipeline.midi_merge import merge
from pipeline.render import render

app = Flask(__name__)
CORS(app)

GENERATED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generated'))
os.makedirs(GENERATED_DIR, exist_ok=True)


@app.route('/health')
def health():
    return {'status': 'ok'}


@app.route('/generated/<filename>')
def serve_generated(filename):
    return send_from_directory(GENERATED_DIR, filename)


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

        # Send full MP3 + prompt to MusicGen (melody-conditioned)
        with open(full_mp3, 'rb') as f:
            musicgen_output = replicate.run(
                'meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb',
                input={
                    'prompt':                 prompt,
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
