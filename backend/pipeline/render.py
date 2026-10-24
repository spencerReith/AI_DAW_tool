import os
import subprocess
import numpy as np
import soundfile as sf
import mido
from imageio_ffmpeg import get_ffmpeg_exe

SR = 44100


def _hz(midi_note):
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def _sawtooth(freq, dur, amp=0.3):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    wave = 2.0 * (t * freq - np.floor(0.5 + t * freq))
    n = len(wave)
    env = np.ones(n)
    a = min(int(0.01 * SR), n // 4)
    r = min(int(0.05 * SR), n // 4)
    if a: env[:a] = np.linspace(0, 1, a)
    if r: env[-r:] = np.linspace(1, 0, r)
    return wave * env * amp


def _organ(freq, dur, amp=0.18):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    wave = (np.sin(2 * np.pi * freq * t)
            + 0.5 * np.sin(2 * np.pi * 2 * freq * t)
            + 0.25 * np.sin(2 * np.pi * 3 * freq * t)) / 1.75
    n = len(wave)
    env = np.ones(n)
    a = min(int(0.05 * SR), n // 4)
    r = min(int(0.1 * SR), n // 4)
    if a: env[:a] = np.linspace(0, 1, a)
    if r: env[-r:] = np.linspace(1, 0, r)
    return wave * env * amp


def _parse_notes(mid):
    tempo = 500000
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                break
        else:
            continue
        break

    def to_sec(ticks):
        return mido.tick2second(ticks, mid.ticks_per_beat, tempo)

    events = []
    for track in mid.tracks:
        t = 0.0
        active = {}
        for msg in track:
            t += to_sec(msg.time)
            if msg.type == 'note_on' and msg.velocity > 0:
                active[(msg.note, msg.channel)] = t
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                key = (msg.note, msg.channel)
                if key in active:
                    events.append((active.pop(key), t, msg.note, msg.channel))
        for (pitch, ch), start in active.items():
            events.append((start, t + 0.1, pitch, ch))
    return events


def render(midi_path, output_mp3_path, temp_dir):
    """Synthesize MIDI with numpy oscillators → WAV → MP3."""
    mid = mido.MidiFile(midi_path)
    notes = _parse_notes(mid)

    if not notes:
        raise ValueError('No note events found in MIDI.')

    total_samples = int((mid.length + 0.5) * SR)
    audio = np.zeros(total_samples)

    for start, end, pitch, channel in notes:
        dur = max(0.05, end - start)
        wave = _sawtooth(_hz(pitch), dur) if channel == 0 else _organ(_hz(pitch), dur)
        s = int(start * SR)
        e = min(s + len(wave), total_samples)
        audio[s:e] += wave[:e - s]

    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = (audio / peak * 0.9).astype(np.float32)

    wav_path = os.path.join(temp_dir, 'output.wav')
    sf.write(wav_path, audio, SR)
    subprocess.run(
        [get_ffmpeg_exe(), '-y', '-i', wav_path, '-b:a', '192k', output_mp3_path],
        check=True, capture_output=True
    )
    return output_mp3_path
