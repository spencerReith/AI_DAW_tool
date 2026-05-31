import os
import math
from music21 import (converter, stream, note as m21note, chord as m21chord,
                     tempo as m21tempo, instrument as m21instr, scale as m21scale)


def _diatonic_triads(key_obj):
    sc = m21scale.MajorScale(key_obj.tonic) if key_obj.mode == 'major' else m21scale.MinorScale(key_obj.tonic)
    pcs = [sc.pitchFromDegree(d).pitchClass for d in range(1, 8)]
    triads = []
    for i in range(7):
        r = pcs[i]
        t = pcs[(i + 2) % 7]
        f = pcs[(i + 4) % 7]
        root_midi  = 48 + r
        third_midi = 48 + t + (0 if t > r else 12)
        fifth_midi = 48 + f + (0 if f > r else 12)
        if fifth_midi <= third_midi:
            fifth_midi += 12
        triads.append(m21chord.Chord([root_midi, third_midi, fifth_midi]))
    return triads


def _best_chord(window_notes, triads):
    if not window_notes:
        return triads[0]
    melody_pcs = {n.pitch.pitchClass for n in window_notes}
    return max(triads, key=lambda t: len({p.pitchClass for p in t.pitches} & melody_pcs))


def infer_chords(melody_midi_path, key_obj, bpm, temp_dir):
    """Infer one diatonic triad per bar from melody MIDI. Returns chord MIDI path."""
    score = converter.parse(melody_midi_path)
    triads = _diatonic_triads(key_obj)

    notes = [n for n in score.flatten().notes if isinstance(n, m21note.Note)]
    if not notes:
        raise ValueError('No notes found in melody MIDI.')

    total_ql = max(float(n.offset) + float(n.quarterLength) for n in notes)
    bar_ql = 4.0
    n_bars = math.ceil(total_ql / bar_ql)

    part = stream.Part()
    instr = m21instr.Instrument()
    instr.midiProgram = 88  # New Age Pad
    instr.midiChannel = 1
    part.insert(0, instr)
    part.insert(0, m21tempo.MetronomeMark(number=bpm))

    for i in range(n_bars):
        start, end = i * bar_ql, (i + 1) * bar_ql
        window = [n for n in notes if start <= float(n.offset) < end]
        triad = _best_chord(window, triads)
        out_chord = m21chord.Chord([p.midi for p in triad.pitches])
        out_chord.quarterLength = bar_ql
        part.insert(start, out_chord)

    out_score = stream.Score()
    out_score.append(part)
    out_path = os.path.join(temp_dir, 'chords.mid')
    out_score.write('midi', out_path)
    return out_path
