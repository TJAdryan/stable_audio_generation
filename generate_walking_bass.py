import argparse
import os
import time

from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo


NOTE_TO_SEMITONE = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}


def note_name_to_midi(note_name: str, octave: int) -> int:
    semitone = NOTE_TO_SEMITONE.get(note_name)
    if semitone is None:
        raise ValueError(f"Unsupported note name: {note_name}")
    return (octave + 1) * 12 + semitone


def parse_key(key: str) -> tuple[str, str]:
    normalized = key.strip()
    lower = normalized.lower()

    if lower.endswith("min"):
        quality = "min"
        root = normalized[:-3]
    elif lower.endswith("m"):
        quality = "min"
        root = normalized[:-1]
    else:
        quality = "maj"
        root = normalized

    root = root.strip()
    if not root:
        raise ValueError("Key is empty.")

    root = root[0].upper() + root[1:]
    if root not in NOTE_TO_SEMITONE:
        raise ValueError(f"Unsupported key root: {root}")

    return root, quality


def build_12_bar_blues_progression(root: str) -> list[str]:
    root_semitone = NOTE_TO_SEMITONE[root]
    semitone_to_primary_name = {
        0: "C",
        1: "C#",
        2: "D",
        3: "Eb",
        4: "E",
        5: "F",
        6: "F#",
        7: "G",
        8: "Ab",
        9: "A",
        10: "Bb",
        11: "B",
    }

    i = semitone_to_primary_name[root_semitone]
    iv = semitone_to_primary_name[(root_semitone + 5) % 12]
    v = semitone_to_primary_name[(root_semitone + 7) % 12]

    return [i, i, i, i, iv, iv, i, i, v, iv, i, v]


def build_minor_loop_progression(root: str) -> list[str]:
    root_semitone = NOTE_TO_SEMITONE[root]
    semitone_to_primary_name = {
        0: "C",
        1: "C#",
        2: "D",
        3: "Eb",
        4: "E",
        5: "F",
        6: "F#",
        7: "G",
        8: "Ab",
        9: "A",
        10: "Bb",
        11: "B",
    }

    i = semitone_to_primary_name[root_semitone]
    vi = semitone_to_primary_name[(root_semitone + 8) % 12]
    iv = semitone_to_primary_name[(root_semitone + 5) % 12]
    v = semitone_to_primary_name[(root_semitone + 7) % 12]

    return [i, vi, iv, v]


def chord_tones(root_name: str, quality: str) -> list[int]:
    root_midi = note_name_to_midi(root_name, 2)
    if quality == "min":
        third = root_midi + 3
    else:
        third = root_midi + 4
    fifth = root_midi + 7
    flat_seventh = root_midi + 10
    return [root_midi, third, fifth, flat_seventh]


def build_bar_notes(root_name: str, quality: str, next_root_name: str | None = None) -> list[int]:
    tones = chord_tones(root_name, quality)

    if next_root_name is None:
        return [tones[0], tones[1], tones[2], tones[3]]

    next_root = note_name_to_midi(next_root_name, 2)
    last_note = tones[3]
    if next_root > last_note:
        passing = last_note + 1
    elif next_root < last_note:
        passing = last_note - 1
    else:
        passing = last_note

    return [tones[0], tones[1], tones[2], passing]


def build_walking_bass_notes(root: str, quality: str, bars: int) -> list[int]:
    if quality == "min":
        base_progression = build_minor_loop_progression(root)
    else:
        base_progression = build_12_bar_blues_progression(root)

    progression = [base_progression[i % len(base_progression)] for i in range(bars)]
    all_notes: list[int] = []

    for bar_idx, chord_root in enumerate(progression):
        next_root = progression[(bar_idx + 1) % len(progression)]
        all_notes.extend(build_bar_notes(chord_root, quality, next_root))

    return all_notes


def write_walking_bass_midi(
    output_path: str,
    key: str = "C",
    bpm: int = 120,
    bars: int = 12,
    velocity: int = 88,
    channel: int = 0,
):
    root, quality = parse_key(key)
    if bars < 1:
        raise ValueError("Bars must be at least 1.")
    if not (1 <= bpm <= 300):
        raise ValueError("BPM must be between 1 and 300.")

    midi = MidiFile(type=1)
    ticks_per_beat = midi.ticks_per_beat

    track = MidiTrack()
    midi.tracks.append(track)

    tempo = bpm2tempo(bpm)
    track.append(MetaMessage("set_tempo", tempo=tempo, time=0))
    track.append(MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    track.append(MetaMessage("track_name", name="Walking Bass", time=0))
    track.append(Message("program_change", channel=channel, program=32, time=0))

    quarter_note_ticks = ticks_per_beat

    notes = build_walking_bass_notes(root, quality, bars)
    for note in notes:
        track.append(Message("note_on", note=note, velocity=velocity, channel=channel, time=0))
        track.append(Message("note_off", note=note, velocity=0, channel=channel, time=quarter_note_ticks))

    track.append(MetaMessage("end_of_track", time=0))

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    midi.save(output_path)


def main():
    parser = argparse.ArgumentParser(description="Generate a loopable walking bass MIDI file for REAPER")
    parser.add_argument("--key", type=str, default="C", help="Key root and optional quality, e.g. C, F#, Bbmin")
    parser.add_argument("--bpm", type=int, default=120, help="Tempo in BPM")
    parser.add_argument("--bars", type=int, default=12, help="Number of bars to generate")
    parser.add_argument("--velocity", type=int, default=88, help="MIDI velocity (1-127)")
    parser.add_argument("--channel", type=int, default=0, help="MIDI channel (0-15)")
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Output .mid path (default writes into exports/ with timestamp)",
    )

    args = parser.parse_args()

    if args.output:
        output_path = args.output
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        clean_key = args.key.replace("#", "sharp").replace("b", "flat")
        output_path = f"exports/walking_bass_{timestamp}_{clean_key}.mid"

    write_walking_bass_midi(
        output_path=output_path,
        key=args.key,
        bpm=args.bpm,
        bars=args.bars,
        velocity=args.velocity,
        channel=args.channel,
    )
    print(f"DONE: {output_path}")


if __name__ == "__main__":
    main()