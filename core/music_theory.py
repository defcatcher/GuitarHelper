"""
Music Theory Engine
───────────────────
Chromatic scale, tunings, fretboard note calculation,
diatonic chord generation, and capo transposition.
"""

from __future__ import annotations
import re
from dataclasses import dataclass

# ── Chromatic Scale ──────────────────────────────────────────────────────────

CHROMATIC = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Enharmonic normalization map (flats → sharps, common alternates)
_ENHARMONIC: dict[str, str] = {
    'Db': 'C#', 'Eb': 'D#', 'Fb': 'E', 'Gb': 'F#',
    'Ab': 'G#', 'Bb': 'A#', 'Cb': 'B',
    'E#': 'F', 'B#': 'C',
}

def normalize_note(note: str) -> str:
    """Normalize a note name to its sharp-based equivalent."""
    return _ENHARMONIC.get(note, note)

def note_index(note: str) -> int:
    """Return 0-11 index of a note in the chromatic scale."""
    return CHROMATIC.index(normalize_note(note))

def note_from_index(idx: int) -> str:
    """Return note name from 0-11 index."""
    return CHROMATIC[idx % 12]

# ── Tunings ──────────────────────────────────────────────────────────────────

# Each tuning maps to a list of 6 notes, from string 6 (low) to string 1 (high).
TUNINGS: dict[str, list[str]] = {
    'Standard (EADGBE)':  ['E', 'A', 'D', 'G', 'B', 'E'],
    'Open D (DADF#AD)':   ['D', 'A', 'D', 'F#', 'A', 'D'],
    'Open G (DGDGBD)':    ['D', 'G', 'D', 'G', 'B', 'D'],
    'Drop D (DADGBE)':    ['D', 'A', 'D', 'G', 'B', 'E'],
    'Drop C (CGCFAD)':    ['C', 'G', 'C', 'F', 'A', 'D'],
}

TUNING_NAMES: list[str] = list(TUNINGS.keys())

# ── Fretboard ────────────────────────────────────────────────────────────────

NUM_FRETS = 12  # 0 (open) through 12

def get_fret_note(open_note: str, fret: int) -> str:
    """Return the note at a given fret on a string with the specified open note."""
    base = note_index(open_note)
    return note_from_index(base + fret)

def get_fretboard(tuning_name: str) -> list[list[str]]:
    """
    Return a 6×13 matrix of note names for the given tuning.
    Row 0 = string 6 (lowest), Row 5 = string 1 (highest).
    Column 0 = open string, Column 12 = fret 12.
    """
    tuning = TUNINGS[tuning_name]
    return [
        [get_fret_note(open_note, fret) for fret in range(NUM_FRETS + 1)]
        for open_note in tuning
    ]

# ── Fret marker positions (standard guitar inlays) ──────────────────────────

SINGLE_DOT_FRETS = [3, 5, 7, 9]
DOUBLE_DOT_FRETS = [12]

# ── Standard tuning frequencies (for tuner reference) ────────────────────────
# Frequencies for standard tuning, string 6→1.  Other tunings derive from note.

# Reference: A4 = 440 Hz
A4_FREQ = 440.0

def note_to_freq(note: str, octave: int) -> float:
    """Convert a note name + octave to its frequency in Hz."""
    semitones_from_a4 = (octave - 4) * 12 + (note_index(note) - note_index('A'))
    return A4_FREQ * (2.0 ** (semitones_from_a4 / 12.0))

# Standard tuning reference frequencies (octave included)
STANDARD_FREQS: list[tuple[str, int, float]] = [
    ('E', 2, note_to_freq('E', 2)),   # string 6 — 82.41 Hz
    ('A', 2, note_to_freq('A', 2)),   # string 5 — 110.0 Hz
    ('D', 3, note_to_freq('D', 3)),   # string 4 — 146.83 Hz
    ('G', 3, note_to_freq('G', 3)),   # string 3 — 196.0 Hz
    ('B', 3, note_to_freq('B', 3)),   # string 2 — 246.94 Hz
    ('E', 4, note_to_freq('E', 4)),   # string 1 — 329.63 Hz
]

# Tuning octave assignments for all supported tunings
TUNING_OCTAVES: dict[str, list[int]] = {
    'Standard (EADGBE)':  [2, 2, 3, 3, 3, 4],
    'Open D (DADF#AD)':   [2, 2, 3, 3, 4, 4],
    'Open G (DGDGBD)':    [2, 2, 3, 3, 3, 4],
    'Drop D (DADGBE)':    [2, 2, 3, 3, 3, 4],
    'Drop C (CGCFAD)':    [2, 2, 3, 3, 4, 4],
}

def get_tuning_freqs(tuning_name: str) -> list[tuple[str, int, float]]:
    """Return list of (note, octave, freq) for each string in the given tuning."""
    notes = TUNINGS[tuning_name]
    octaves = TUNING_OCTAVES[tuning_name]
    return [(n, o, note_to_freq(n, o)) for n, o in zip(notes, octaves)]

# ── Scales & Diatonic Chords ─────────────────────────────────────────────────

# Major scale intervals (in semitones from root)
MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

# Chord quality for each degree of the major scale
_MAJOR_DEGREE_QUALITY = ['', 'm', 'm', '', '', 'm', 'dim']
_MAJOR_ROMAN_NUMERALS = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']

# Chord quality for each degree of the natural minor scale
_MINOR_DEGREE_QUALITY = ['m', 'dim', '', 'm', 'm', '', '']
_MINOR_ROMAN_NUMERALS = ['i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII']

@dataclass
class DiatonicChord:
    roman: str       # e.g. "I", "ii", "vii°"
    name: str        # e.g. "C", "Dm", "Bdim"
    root: str        # e.g. "C", "D", "B"
    quality: str     # e.g. "", "m", "dim"

def get_scale_notes(key: str, mode: str = "Major") -> list[str]:
    """Return the 7 notes of the scale for the given key and mode."""
    root = note_index(key)
    intervals = MAJOR_SCALE_INTERVALS if mode == "Major" else MINOR_SCALE_INTERVALS
    return [note_from_index(root + interval) for interval in intervals]

def get_diatonic_chords(key: str, mode: str = "Major") -> list[DiatonicChord]:
    """Return the 7 diatonic chords for the key and mode."""
    scale = get_scale_notes(key, mode)
    chords: list[DiatonicChord] = []
    
    qualities = _MAJOR_DEGREE_QUALITY if mode == "Major" else _MINOR_DEGREE_QUALITY
    romans = _MAJOR_ROMAN_NUMERALS if mode == "Major" else _MINOR_ROMAN_NUMERALS

    for i, (note, quality, roman) in enumerate(zip(scale, qualities, romans)):
        name = note + quality
        chords.append(DiatonicChord(roman=roman, name=name, root=note, quality=quality))
    return chords

# ── Capo Transposition ───────────────────────────────────────────────────────

# Regex to find chord tokens — matches things like C, C#m, Dm7, F#maj7, Bb, etc.
_CHORD_RE = re.compile(
    r'\b([A-G][#b]?)(m|min|maj|dim|aug|sus[24]?|add\d+|7|maj7|m7|dim7|6|9|11|13)*\b'
)

def transpose_chord_name(chord: str, semitones: int) -> str:
    """Transpose a single chord name by the given number of semitones."""
    t = chord.strip()
    t = t.replace("\u266f", "#").replace("\u266d", "b").replace("\u266e", "")
    t = re.sub(r"([A-G])#+", r"\1#", t)
    m = re.match(r"^([A-G])([#b]?)(.*)$", t)
    if not m:
        return chord
    letter, acc, suffix = m.group(1), m.group(2), m.group(3)
    root_token = letter + acc if acc else letter
    try:
        root_norm = normalize_note(root_token)
    except ValueError:
        return chord
    if semitones == 0:
        return letter + acc + suffix
    new_root = note_from_index(note_index(root_norm) + semitones)
    return new_root + suffix

def capo_transpose(text: str, capo_fret: int) -> str:
    """
    Given text with chord names, transpose DOWN by capo_fret semitones.
    This shows the 'sounding' chords when a capo is applied.
    """
    if capo_fret == 0:
        return text

    def _replace(m: re.Match) -> str:
        return transpose_chord_name(m.group(0), capo_fret)

    return _CHORD_RE.sub(_replace, text)

def capo_display_chords(chords: list[DiatonicChord], capo_fret: int) -> list[DiatonicChord]:
    """
    Return new DiatonicChord list showing how chord shapes transpose with a capo.
    E.g., if key=C and capo=2, a 'C shape' now sounds like 'D'.
    Negative values transpose down (chart / virtual capo).
    """
    if capo_fret == 0:
        return chords
    result: list[DiatonicChord] = []
    for c in chords:
        new_name = transpose_chord_name(c.name, capo_fret)
        new_root = note_from_index(note_index(c.root) + capo_fret)
        result.append(DiatonicChord(
            roman=c.roman,
            name=new_name,
            root=new_root,
            quality=c.quality,
        ))
    return result
