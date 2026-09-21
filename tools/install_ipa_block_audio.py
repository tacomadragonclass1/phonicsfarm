#!/usr/bin/env python3
"""Copy selected phonemes and the user's own edits into the game; assemble x.

Rerunning this rebuilds every letter from the IPA recordings, so any letter the
user has replaced by hand has to be listed in OVERRIDES or it is silently
reverted to the generic clip.
"""
import argparse
import array
import hashlib
import json
from pathlib import Path
import shutil
import sys
import wave


# Letters the user recorded or edited themselves, which beat the IPA clip.
# `process` trims the lead-in and matches the level of the other letters; a
# clip that already matches (q) is copied byte for byte instead.
OVERRIDES = {
    "q": dict(filename="q sound.wav", ipa="kw", process=False,
              note="unchanged copy of user's edited q sound.wav"),
    "l": dict(filename="new letter l phoneme.wav", ipa="l", process=True,
              note="user's replacement for the IPA l; trimmed and normalized"),
}
PEAK, HEAD_MS, TAIL_MS, FLOOR = 0.89, 12, 60, 0.008


def read_samples(path):
    with wave.open(str(path), "rb") as recording:
        if (recording.getnchannels(), recording.getsampwidth(), recording.getcomptype()) != (1, 2, "NONE"):
            sys.exit(f"{path}: need uncompressed 16-bit mono")
        rate = recording.getframerate()
        data = array.array("h")
        data.frombytes(recording.readframes(recording.getnframes()))
    if sys.byteorder == "big":
        data.byteswap()
    return data, rate


def trim_and_normalize(source, output):
    """Cut leading/trailing silence, normalize, re-pad. Keeps the source's own
    sample rate -- resampling would only lose detail, and Godot plays any rate.
    A quiet or slow-starting letter is the audible problem: it lags on pickup
    and drops in level against its neighbours in a lever sequence."""
    data, rate = read_samples(source)
    limit = FLOOR * 32768
    voiced = [index for index, value in enumerate(data) if abs(value) > limit]
    if not voiced:
        sys.exit(f"{source}: silent clip")
    clip = data[voiced[0]:voiced[-1] + 1]
    gain = PEAK * 32767 / max(abs(value) for value in clip)
    out = array.array("h", [0] * int(rate * HEAD_MS / 1000))
    out.extend(max(-32768, min(32767, int(value * gain))) for value in clip)
    out.extend([0] * int(rate * TAIL_MS / 1000))
    if sys.byteorder == "big":
        out.byteswap()
    with wave.open(str(output), "wb") as recording:
        recording.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        recording.writeframes(out.tobytes())
    return rate


LETTER_SOUNDS = dict(zip(
    "abcdefghijklmnopqrstuvwxyz",
    ["a", "b", "k", "d", "ɛ", "f", "ɡ", "h", "ɪ", "dʒ", "k", "l", "m",
     "n", "ɒ", "p", "kw", "r", "s", "t", "ʌ", "v", "w", "ks", "j", "z"],
))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.home() / "Desktop/PhonicsFarm Sound Review/ipa-recordings")
    parser.add_argument("--q-source", type=Path, help="Overrides the default q sound.wav location")
    parser.add_argument("--overrides", type=Path,
                        help="Folder holding the user's own recordings; defaults beside ipa-recordings")
    args = parser.parse_args()
    override_dir = args.overrides or args.source.parent
    override_sources = {letter: override_dir / spec["filename"]
                        for letter, spec in OVERRIDES.items()}
    if args.q_source:
        override_sources["q"] = args.q_source
    for letter, source in override_sources.items():
        if not source.exists():
            sys.exit(f"missing {letter} override: {source}")
    destination = Path(__file__).resolve().parents[1] / "assets/audio/phonemes"
    source_manifest = json.loads((args.source / "manifest.json").read_text())
    phonemes = {entry["ipa"]: entry for entry in source_manifest["phonemes"]}
    destination.mkdir(parents=True, exist_ok=True)
    entries = []
    for letter, ipa in LETTER_SOUNDS.items():
        if letter in OVERRIDES:
            spec = OVERRIDES[letter]
            source = override_sources[letter]
            output = destination / f"{letter}.wav"
            if spec["process"]:
                rate = trim_and_normalize(source, output)
                note = f"{spec['note']} to {PEAK} peak, {HEAD_MS} ms lead, {TAIL_MS} ms tail ({rate} Hz)"
            else:
                shutil.copyfile(source, output)
                note = spec["note"]
            entries.append({
                "letter": letter, "ipa": spec["ipa"], "file": output.name,
                "source_files": [str(source)],
                "source_sha256": [hashlib.sha256(source.read_bytes()).hexdigest()],
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "processing": note,
            })
            continue
        parts = list(ipa) if letter in "qx" else [ipa]
        sources = [args.source / phonemes[part]["file"] for part in parts]
        frames = []
        for source in sources:
            with wave.open(str(source), "rb") as recording:
                assert (recording.getnchannels(), recording.getsampwidth(), recording.getframerate(), recording.getcomptype()) == (1, 2, 24000, "NONE"), source
                frames.append(recording.readframes(recording.getnframes()))
        output = destination / f"{letter}.wav"
        if len(sources) == 1:
            shutil.copyfile(sources[0], output)
        else:
            # Remove only the known 70 ms tail and 25 ms head padding at the
            # join. Preserve the recorded utterances and their existing fades.
            joined = frames[0][:-1680 * 2] + frames[1][600 * 2:]
            with wave.open(str(output), "wb") as recording:
                recording.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
                recording.writeframes(joined)
        entries.append({
            "letter": letter, "ipa": ipa, "file": output.name,
            "source_files": [phonemes[part]["file"] for part in parts],
            "source_sha256": [hashlib.sha256(source.read_bytes()).hexdigest() for source in sources],
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "processing": "unchanged copy" if len(parts) == 1 else "concatenated; remove 70 ms tail and 25 ms head padding at join",
        })
    manifest = {
        "source": source_manifest["source"],
        "selection": "User selected the human IPA recordings for alphabet blocks on 2026-09-20; Maisie deferred.",
        "format": source_manifest["format"] + "; user-supplied overrides keep their own sample rate",
        "letters": entries,
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Installed {len(entries)} letter sounds in {destination}")


if __name__ == "__main__":
    main()
