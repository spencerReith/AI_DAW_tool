import mido


def merge(melody_midi_path, chord_midi_path, output_path):
    """Merge melody and chord MIDIs using mido to preserve all notes at tick level."""
    melody = mido.MidiFile(melody_midi_path)
    chords = mido.MidiFile(chord_midi_path)
    tpb = melody.ticks_per_beat

    merged = mido.MidiFile(type=1, ticks_per_beat=tpb)

    # Conductor track
    conductor = mido.MidiTrack()
    conductor.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))  # 120 BPM
    merged.tracks.append(conductor)

    # Melody track — force channel 0, skip program_change (we set our own)
    melody_track = mido.MidiTrack()
    melody_track.append(mido.Message('program_change', program=81, channel=0, time=0))
    for track in melody.tracks:
        for msg in track:
            if not msg.is_meta and msg.type != 'program_change':
                melody_track.append(msg.copy(channel=0))
    merged.tracks.append(melody_track)

    # Chord track — rescale ticks if TPB differs, force channel 1
    ratio = tpb / chords.ticks_per_beat
    chord_track = mido.MidiTrack()
    chord_track.append(mido.Message('program_change', program=88, channel=1, time=0))
    for track in chords.tracks:
        for msg in track:
            if not msg.is_meta and msg.type != 'program_change':
                chord_track.append(msg.copy(channel=1, time=int(msg.time * ratio)))
    merged.tracks.append(chord_track)

    merged.save(output_path)
    return output_path
