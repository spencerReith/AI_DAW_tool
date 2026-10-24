# Desktop-only seed audio route. Registered by app.py when ENABLE_SEED=1.
# Seed → basic-pitch melody MIDI → inferred chords → synth render → MusicGen melody conditioning.
import os
import shutil
import tempfile
import datetime
import subprocess
from flask import request, jsonify
import requests as http_requests

MUSICGEN_MODEL = 'meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb'
MUSICGEN_MAX_DURATION = 30


def init_seed(app, rewrite_prompt, save_audio, run_variations, log):
    with open(os.path.join(os.path.dirname(__file__), '..', 'prompt_guides', 'musicgen_prompting.md')) as f:
        guide = f.read()

    system_prompt = f"""You are a prompt engineer for Meta's MusicGen model.

The user has hummed or recorded a melody. MusicGen will use that melody as a conditioning input and reimagine it in a new style. Your job is to take the user's style description and rewrite it into a single MusicGen prompt string that captures how the melody should be reimagined.

Use the guide below to write a prompt that directs MusicGen toward the target style, mood, and instrumentation — while staying true to what the user described.

Rules:
- Output the prompt string only. No explanation, no markdown, no labels.
- Use natural language sentences, not pipe-delimited fields.
- Do not invent elements the user did not describe or imply.
- Use vocabulary and phrasing drawn directly from the guide examples.
- Keep it concise — every word should add meaningful context.

--- MUSICGEN PROMPT GUIDE ---
{guide}
"""

    def generate_one_musicgen(description, bpm, seed_path, duration, timestamp, index):
        """One MusicGen variation conditioned on the rendered seed. Returns relative URL or None."""
        import replicate
        try:
            prompt = rewrite_prompt(system_prompt, description, bpm, 'musicgen', index)
            with open(seed_path, 'rb') as f:
                output = replicate.run(MUSICGEN_MODEL, input={
                    'prompt':                 prompt,
                    'melody':                 f,
                    'model_version':          'stereo-melody-large',
                    'output_format':          'mp3',
                    'normalization_strategy': 'peak',
                    'duration':               duration,
                })
            url = output.url if hasattr(output, 'url') else str(output)
            return save_audio(http_requests.get(url).content, 'musicgen', timestamp, index)
        except Exception as e:
            print(f'[generate_one_musicgen] variation {index} failed: {e}')
            return None

    def seed_to_render(seed_file, temp_dir):
        """Run the melody → chords → render pipeline on the uploaded seed. Returns rendered mp3 path."""
        import replicate
        from imageio_ffmpeg import get_ffmpeg_exe
        from music21 import converter
        from pipeline.chord_infer import infer_chords
        from pipeline.midi_merge import merge
        from pipeline.render import render

        # any input format → wav for basic-pitch
        saved_path = os.path.join(temp_dir, 'seed_original')
        seed_file.save(saved_path)
        wav_path = os.path.join(temp_dir, 'seed.wav')
        subprocess.run([get_ffmpeg_exe(), '-y', '-i', saved_path, wav_path], check=True, capture_output=True)

        # audio → melody MIDI
        with open(wav_path, 'rb') as f:
            midi_output = replicate.run(
                'rhelsing/basic-pitch:a7cf33cf63fca9c71f2235332af5a9fdfb7d23c459a0dc429daa203ff8e80c78',
                input={'audio_file': f}
            )
        melody_midi = os.path.join(temp_dir, 'melody.mid')
        with open(melody_midi, 'wb') as f:
            f.write(midi_output.read())

        # melody + inferred chords → rendered mp3
        key_obj     = converter.parse(melody_midi).analyze('key')
        chord_midi  = infer_chords(melody_midi, key_obj, 120, temp_dir)
        merged_midi = os.path.join(temp_dir, 'merged.mid')
        merge(melody_midi, chord_midi, merged_midi)
        render_path = os.path.join(temp_dir, 'render.mp3')
        render(merged_midi, render_path, temp_dir)
        log(f'[musicgen] seed rendered via midi pipeline, key={key_obj}')
        return render_path

    @app.route('/generate-seed', methods=['POST'])
    def generate_seed():
        timestamp   = datetime.datetime.now().strftime('%H_%M_%S')
        description = request.form.get('description', '').strip()
        bpm         = request.form.get('bpm', 120)
        duration    = max(1, min(int(request.form.get('duration', 30)), MUSICGEN_MAX_DURATION))
        variations  = max(1, min(int(request.form.get('variations', 1)), 4))
        seed_file   = request.files.get('seed')

        if not seed_file:
            return jsonify({'error': 'seed file missing'}), 400

        print(f'[request-musicgen] description="{description}" bpm={bpm} duration={duration} variations={variations} seed="{seed_file.filename}"')
        log(f'[musicgen] prompt="{description}" bpm={bpm} duration={duration} variations={variations} seed="{seed_file.filename}"')

        temp_dir = tempfile.mkdtemp()
        try:
            try:
                seed_path = seed_to_render(seed_file, temp_dir)
            except Exception as e:
                print(f'[seed pipeline] failed: {e}')
                return jsonify({'error': f'seed processing failed: {e}'}), 500
            return run_variations(generate_one_musicgen, variations, description, bpm, seed_path, duration, timestamp)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
