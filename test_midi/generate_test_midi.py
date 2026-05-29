"""Generates test MIDI files for verifying Step 5 parsing."""
import mido
import os

OUT_DIR = os.path.dirname(__file__)

def make_midi(filename, key=None, bpm=120, time_sig=(4, 4)):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))
    track.append(mido.MetaMessage('time_signature', numerator=time_sig[0], denominator=time_sig[1]))
    if key:
        track.append(mido.MetaMessage('key_signature', key=key))

    # A few notes so the file isn't empty
    for note in [60, 62, 64, 65]:
        track.append(mido.Message('note_on', note=note, velocity=64, time=0))
        track.append(mido.Message('note_off', note=note, velocity=64, time=480))

    mid.save(os.path.join(OUT_DIR, filename))
    print(f'Generated {filename}')

make_midi('key_of_d.mid', key='D')
make_midi('key_of_e.mid', key='E')
make_midi('no_key.mid', key=None)
