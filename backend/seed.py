# Desktop-only seed audio (audio-to-audio) route. Registered by app.py when ENABLE_SEED=1.
# Seed → basic-pitch melody MIDI → inferred chords → synth render → Stable Audio A2A.
import os
import shutil
import tempfile
import datetime
import subprocess
from flask import request, jsonify

STABILITY_A2A_URL = 'https://api.stability.ai/v2beta/audio/stable-audio/audio-to-audio'


def init_seed(app, guide, rewrite_prompt, run_stability, run_variations, log):
    system_prompt = f"""You are a prompt engineer for Stability AI's Stable Audio 3 model.

The user has provided a seed audio file. Stable Audio 3 will transform that seed into a new composition guided by your prompt. Your job is to rewrite the user's description into a single prompt string that describes the *target style* the seed should be transformed into.

Follow the guide below. Structure the output in this order:
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
- Remember: the output will be a transformation of the seed audio, not a blank-slate generation.

--- STABLE AUDIO 3 PROMPT GUIDE ---
{guide}
"""

    def generate_one_audio(description, bpm, seed_path, strength, duration, timestamp, index):
        """One audio-to-audio variation. Returns relative URL or None."""
        try:
            prompt = rewrite_prompt(system_prompt, description, bpm, 'stable-audio-a2a', index)
            with open(seed_path, 'rb') as audio_f:
                return run_stability(STABILITY_A2A_URL, {'audio': audio_f},
                                     {'prompt': prompt, 'output_format': 'mp3', 'duration': duration, 'strength': strength},
                                     'stable-audio-a2a', timestamp, index)
        except Exception as e:
            print(f'[generate_one_audio] variation {index} failed: {e}')
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
        log(f'[stable-audio-a2a] seed rendered via midi pipeline, key={key_obj}')
        return render_path

    @app.route('/generate-seed', methods=['POST'])
    def generate_seed():
        timestamp   = datetime.datetime.now().strftime('%H_%M_%S')
        description = request.form.get('description', '').strip()
        bpm         = request.form.get('bpm', 120)
        duration    = max(1, min(int(request.form.get('duration', 90)), 380))
        variations  = max(1, min(int(request.form.get('variations', 1)), 4))
        strength    = max(0.0, min(float(request.form.get('noise_level', 0.5)), 1.0))
        seed_file   = request.files.get('seed')

        if not seed_file:
            return jsonify({'error': 'seed file missing'}), 400

        print(f'[request-a2a] description="{description}" bpm={bpm} duration={duration} variations={variations} strength={strength} seed="{seed_file.filename}"')
        log(f'[stable-audio-a2a] prompt="{description}" bpm={bpm} duration={duration} variations={variations} strength={strength} seed="{seed_file.filename}"')

        temp_dir = tempfile.mkdtemp()
        try:
            try:
                seed_path = seed_to_render(seed_file, temp_dir)
            except Exception as e:
                print(f'[seed pipeline] failed: {e}')
                return jsonify({'error': f'seed processing failed: {e}'}), 500
            return run_variations(generate_one_audio, variations, description, bpm, seed_path, strength, duration, timestamp)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
