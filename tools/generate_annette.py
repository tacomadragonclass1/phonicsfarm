#!/usr/bin/env python3
"""Render Annette's spoken lines for Phoneme Village with local Kokoro TTS.

Annette is the village voice. She speaks only full sentences, so this uses
Kokoro's ordinary text path -- unlike tools/generate_phonemes.py, which must
feed raw IPA to get an isolated SOUND instead of a letter NAME.

The isolated phonemes themselves are NOT re-rendered here. Annette's sentence
is spliced in front of the existing human recording in
assets/audio/phonemes/, so the sound the child must match is byte-identical
to the one the alphabet block itself plays.

Also writes the wrong-answer chime, which is synthesized, not spoken.

Clips land straight in assets/audio/voice/. They are `pending_user_review`:
the assistant cannot hear them and must never call a rendering verified.
"""

import argparse
import json
from pathlib import Path
import sys
import wave

SAMPLE_RATE = 24000
REPO = "hexgrad/Kokoro-82M"
DEFAULT_VOICE = "bf_emma"

# Exactly the two lines the game speaks. Keep the keys in sync with the
# VOICE dictionary in audio/phoneme_audio.gd.
LINES = {
    "annette_find": "Please find the letter that says",
    "annette_good": "Good job!",
}


def postprocess(audio, peak=0.89, head_ms=30, tail_ms=140, floor=0.008):
    """Trim Kokoro's leading silence, normalize, re-pad. Same shape as the
    phoneme driver so Annette and the block sounds sit at one level."""
    import numpy as np
    audio = np.asarray(audio, dtype=np.float32)
    loud = np.where(np.abs(audio) > floor)[0]
    if len(loud) == 0:
        raise ValueError("silent clip")
    audio = audio[loud[0]:loud[-1] + 1]
    top = float(np.abs(audio).max())
    if top > 0:
        audio = audio * (peak / top)
    pad = lambda ms: np.zeros(int(SAMPLE_RATE * ms / 1000), dtype=np.float32)
    audio = np.concatenate([pad(head_ms), audio, pad(tail_ms)])
    return (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")


def chime(semitones=(0, -5), note_ms=150, peak=0.32):
    """A soft two-note fall for a wrong pick. Deliberately not a buzzer:
    it marks 'not that one' without sounding like a failure to a five-year-old.
    """
    import numpy as np
    parts = []
    for step in semitones:
        n = int(SAMPLE_RATE * note_ms / 1000)
        t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
        freq = 660.0 * (2.0 ** (step / 12.0))
        tone = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t)
        envelope = np.exp(-4.5 * t) * np.minimum(1.0, t * SAMPLE_RATE / 240.0)
        parts.append(tone * envelope)
    audio = np.concatenate(parts)
    audio = audio * (peak / float(np.abs(audio).max()))
    tail = np.zeros(int(SAMPLE_RATE * 0.08), dtype=np.float32)
    audio = np.concatenate([audio, tail])
    return (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")


def write_wav(path, pcm16):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes(pcm16.tobytes())
    return round(len(pcm16) / SAMPLE_RATE, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default=DEFAULT_VOICE,
                    help="Kokoro British voice for Annette")
    ap.add_argument("--output", type=Path,
                    default=Path(__file__).resolve().parent.parent / "assets/audio/voice")
    ap.add_argument("--force", action="store_true",
                    help="overwrite clips that already exist")
    args = ap.parse_args()

    from kokoro import KPipeline
    pipeline = KPipeline(lang_code="b", repo_id=REPO, device="cpu")

    records = []
    for key, text in LINES.items():
        target = args.output / f"{key}.wav"
        if target.exists() and not args.force:
            print(f"keep   {target.name} (exists; --force to replace)")
            continue
        audio = None
        for _, _, chunk in pipeline(text, voice=args.voice, speed=1.0):
            if chunk is not None:
                audio = chunk.numpy()
                break
        if audio is None:
            sys.exit(f"no audio for {key!r}")
        duration = write_wav(target, postprocess(audio))
        print(f"wrote  {target.name}  {duration:>5}s  “{text}”")
        records.append(dict(key=key, text=text, voice=args.voice,
                            file=target.name, duration_seconds=duration,
                            engine="kokoro", status="pending_user_review"))

    tone = args.output / "wrong_chime.wav"
    if tone.exists() and not args.force:
        print(f"keep   {tone.name} (exists; --force to replace)")
    else:
        duration = write_wav(tone, chime())
        print(f"wrote  {tone.name}  {duration:>5}s  (synthesized, not spoken)")
        records.append(dict(key="wrong_chime", text=None, voice=None,
                            file=tone.name, duration_seconds=duration,
                            engine="synthesized", status="pending_user_review"))

    if records:
        manifest = args.output / "manifest.json"
        existing = json.loads(manifest.read_text())["clips"] if manifest.exists() else []
        merged = {r["key"]: r for r in existing}
        merged.update({r["key"]: r for r in records})
        manifest.write_text(json.dumps(dict(
            source="local Kokoro-82M (Apache-2.0 model and voices) + synthesized chime",
            format="24 kHz 16-bit mono PCM WAV",
            note="Sentence wrappers only. Phonemes stay the human recordings in ../phonemes/.",
            clips=sorted(merged.values(), key=lambda r: r["key"]),
        ), indent=2) + "\n")
        print(f"wrote  {manifest.name}")


if __name__ == "__main__":
    main()
