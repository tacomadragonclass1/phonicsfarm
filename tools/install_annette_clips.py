#!/usr/bin/env python3
"""Install user-supplied recordings as Annette's lines.

The sentence wrappers are spliced straight in front of a block's own phoneme
in one audio queue, so they have to match those clips: same 24 kHz 16-bit mono,
same short lead-in, same peak. A clip carrying three quarters of a second of
trailing silence leaves audible dead air between "...that says" and the sound
the child is supposed to be matching.

So this applies exactly the postprocess tools/generate_annette.py applies to
its own output -- trim, normalize, re-pad to 30 ms / 140 ms -- and records the
source path and hash in the manifest. Source files are never modified.

  --raw   copy byte-for-byte instead, keeping whatever padding is in the file.
"""

import argparse
import hashlib
import json
import shutil
import sys
import wave
from pathlib import Path

SAMPLE_RATE = 24000
VOICE_DIR = Path(__file__).resolve().parent.parent / "assets/audio/voice"

# key -> (destination stem, the words, default source filename)
CLIPS = {
    "annette_find": ("Please find the letter that says", "annnette find the letter.wav"),
    "annette_good": ("Good job!", "annette good job.wav"),
}


def read_wav(path):
    import numpy as np
    with wave.open(str(path), "rb") as w:
        if w.getnchannels() != 1 or w.getsampwidth() != 2:
            sys.exit(f"{path.name}: need 16-bit mono, got "
                     f"{w.getsampwidth() * 8}-bit {w.getnchannels()}ch")
        rate, frames = w.getframerate(), w.getnframes()
        audio = np.frombuffer(w.readframes(frames), "<i2").astype(np.float32) / 32768.0
    return audio, rate


def postprocess(audio, peak=0.89, head_ms=30, tail_ms=140, floor=0.008):
    """Identical to tools/generate_annette.py, so hand-recorded and generated
    clips sit at the same level with the same lead-in."""
    import numpy as np
    loud = np.where(np.abs(audio) > floor)[0]
    if len(loud) == 0:
        sys.exit("silent clip")
    audio = audio[loud[0]:loud[-1] + 1]
    top = float(np.abs(audio).max())
    if top > 0:
        audio = audio * (peak / top)
    pad = lambda ms: np.zeros(int(SAMPLE_RATE * ms / 1000), dtype=np.float32)
    audio = np.concatenate([pad(head_ms), audio, pad(tail_ms)])
    return (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")


def write_wav(path, pcm16, rate):
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(pcm16.tobytes())
    return round(len(pcm16) / rate, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path,
                    default=Path.home() / "Desktop/PhonicsFarm Sound Review")
    ap.add_argument("--raw", action="store_true",
                    help="copy unchanged instead of trimming and normalizing")
    args = ap.parse_args()

    manifest_path = VOICE_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    records = {clip["key"]: clip for clip in manifest["clips"]}

    for key, (text, filename) in CLIPS.items():
        source = args.source / filename
        if not source.exists():
            sys.exit(f"missing source: {source}")
        target = VOICE_DIR / f"{key}.wav"
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()

        if args.raw:
            shutil.copyfile(source, target)
            audio, rate = read_wav(target)
            duration, how = round(len(audio) / rate, 3), "unchanged copy"
        else:
            audio, rate = read_wav(source)
            duration = write_wav(target, postprocess(audio), rate)
            how = "trimmed to 30 ms lead / 140 ms tail, normalized to 0.89 peak"

        records[key] = dict(
            key=key, text=text, voice="user-supplied recording",
            file=target.name, duration_seconds=duration, engine="user-supplied",
            source_file=str(source), source_sha256=source_hash,
            sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            processing=how, status="pending_user_review")
        print(f"{target.name:18} {duration:>5}s  <- {source.name}  ({how})")

    manifest["source"] = ("User-supplied recordings for Annette's sentences; "
                          "synthesized chime. Phonemes stay the human recordings in ../phonemes/.")
    manifest["clips"] = sorted(records.values(), key=lambda r: r["key"])
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{manifest_path.name} updated")


if __name__ == "__main__":
    main()
