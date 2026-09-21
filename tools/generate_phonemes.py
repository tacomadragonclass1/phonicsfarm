#!/usr/bin/env python3
"""Render isolated phoneme clips for CVC Land with local Kokoro TTS.

No cloud account, no API key, no network after the first model download.
Kokoro accepts a raw IPA string, which is what makes isolated phonemes
possible at all: a text-only engine says the letter NAME ("bee") instead
of the sound /b/.

Two stages:
  --probe   audition every British voice on a few letters, pick one by ear
  --full    render all 33 candidates in the chosen voice

Nothing here touches the game. Clips land in a desktop review folder and
stay `pending_user_review` until the user approves them by name.
"""

import argparse
import html
import json
from pathlib import Path
import sys
import wave

SAMPLE_RATE = 24000
REPO = "hexgrad/Kokoro-82M"

# Derived from Kokoro's own British G2P (misaki lang_code='b'), not guessed.
# Verify with tools/generate_phonemes.py --check.
# Traps: ASCII "g" is NOT in Kokoro's vocab (needs U+0261 SCRIPT G) and unknown
# symbols are dropped SILENTLY, yielding a vowel-only clip. British TRAP is
# "a" (U+0061), not "ae". "j" is the single character U+02A4.
PHONES = {
    "a": "a",        "b": "b",       "c": "k",        "d": "d",
    "e": "ɛ",   "f": "f",       "g": "ɡ",   "h": "h",
    "i": "ɪ",   "j": "ʤ",  "k": "k",        "l": "l",
    "m": "m",        "n": "n",       "o": "ɒ",   "p": "p",
    "q": "kw",       "r": "ɹ",  "s": "s",        "t": "t",
    "u": "ʌ",   "v": "v",       "w": "w",        "x": "ks",
    "y": "j",        "z": "z",
}
# Stops: silent without a release vowel, so render both ways and let the ear decide.
PAIRED = set("bcdgkpt")
VOWELS = set("aeiou")
SCHWA = "ə"
STRESS = "ˈ"

BRITISH_VOICES = ["bf_alice", "bf_emma", "bf_isabella", "bf_lily",
                  "bm_daniel", "bm_fable", "bm_george", "bm_lewis"]
PROBE_LETTERS = "bgmas"


def candidates(letters):
    """Build the synthesis targets. Labels are requests, not verified results."""
    out = []
    for letter in letters:
        phone = PHONES[letter]
        nucleus = STRESS if letter in VOWELS else ""
        variants = [("no_schwa", nucleus + phone)]
        if letter in PAIRED:
            variants.append(("with_schwa", phone + STRESS + SCHWA))
        for variant, ipa in variants:
            out.append(dict(letter=letter, variant=variant, ipa=ipa))
    return out


def check_vocab(model):
    """Fail loudly on a symbol Kokoro would silently drop."""
    bad = []
    for letter, phone in PHONES.items():
        missing = [c for c in phone if c not in model.vocab]
        if missing:
            bad.append(f"{letter}=/{phone}/ unknown: " +
                       " ".join(f"U+{ord(c):04X}" for c in missing))
    for name, sym in (("schwa", SCHWA), ("stress", STRESS)):
        if sym not in model.vocab:
            bad.append(f"{name} U+{ord(sym):04X} not in vocab")
    return bad


def postprocess(audio, peak=0.89, head_ms=30, tail_ms=120, floor=0.008):
    """Trim Kokoro's leading/trailing silence, normalize, re-pad.

    Raw output starts with ~200 ms of silence, which reads as lag when a
    block is picked up. Keep a short tail so stop releases are not clipped.
    """
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


def write_wav(path, pcm16):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes(pcm16.tobytes())
    return round(len(pcm16) / SAMPLE_RATE, 3)


def render(pipeline, ipa, voice):
    for _, _, audio in pipeline.generate_from_tokens(ipa, voice=voice, speed=1.0):
        if audio is not None:
            return audio.numpy()
    raise ValueError(f"no audio for /{ipa}/ in {voice}")


def page(folder, records, stage, voice):
    groups = {}
    for r in records:
        groups.setdefault(r["letter"], []).append(r)
    rows = []
    for letter in sorted(groups):
        cells = []
        for r in sorted(groups[letter], key=lambda x: (x["voice"], x["variant"])):
            label = r["voice"] if stage == "probe" else r["variant"].replace("_", " ")
            cells.append(
                f'<div class=c><span class=l>{html.escape(label)}</span>'
                f'<audio controls preload=none src="{html.escape(r["file"])}"></audio></div>')
        ipa = html.escape(groups[letter][0]["ipa"])
        rows.append(f'<tr><th>{letter}</th><td class=ipa>/{ipa}/</td>'
                    f'<td class=clips>{"".join(cells)}</td></tr>')

    if stage == "probe":
        intro = (f"<p><b>Stage 1 — pick a voice.</b> Every British Kokoro voice on "
                 f"{len(PROBE_LETTERS)} test letters. Listen across a row, tell the "
                 f"assistant which voice, then it renders all 26 letters in that one.</p>")
    else:
        intro = (f"<p><b>Stage 2 — approve the sounds.</b> Voice: <code>"
                 f"{html.escape(voice)}</code>. Stop consonants (b, c, d, g, k, p, t) "
                 f"have two versions: without a schwa and with one. Pick whichever is "
                 f"clearer — a short &ldquo;uh&rdquo; is a fine choice for this game.</p>")

    (folder / "index.html").write_text('''<!doctype html>
<html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width">
<title>CVC Land &mdash; sound review</title>
<style>
body{font:17px/1.5 system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 20px;
background:#fffaf0;color:#20312a}
h1{margin-bottom:.2em}table{border-collapse:collapse;width:100%;margin-top:1.5em}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #d8d6c2;vertical-align:middle}
th{font-size:30px;width:1.6em}td.ipa{font-size:19px;color:#5a6b60;width:5em}
td.clips{display:flex;flex-wrap:wrap;gap:14px}
.c{display:flex;flex-direction:column;gap:3px}
.l{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:#6b7a70}
audio{height:34px}code{background:#efe9da;padding:1px 5px;border-radius:3px}
.note{background:#f4efe0;border-left:4px solid #b9ad84;padding:10px 16px;margin:1.4em 0;font-size:15px}
</style>
<h1>CVC Land &mdash; sound review</h1>''' + intro + '''
<div class=note>Labels describe what the engine was <em>asked</em> to produce, not a
verified result. Nothing here is approved or wired into the game. Reply by letter,
e.g. &ldquo;b: with schwa; c: without; g: try again.&rdquo;</div>
<table><thead><tr><td>Letter</td><td>Target</td><td>Clips</td></tr></thead><tbody>
''' + "\n".join(rows) + "</tbody></table></html>\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", type=Path,
                    default=Path.home() / "Desktop/PhonicsFarm Sound Review")
    ap.add_argument("--probe", action="store_true",
                    help="Stage 1: audition every British voice on a few letters")
    ap.add_argument("--voice", default="bf_emma", help="Stage 2 voice")
    ap.add_argument("--letters", default="abcdefghijklmnopqrstuvwxyz")
    ap.add_argument("--check", action="store_true",
                    help="Validate the phoneme table against Kokoro's vocab and exit")
    ap.add_argument("--force", action="store_true", help="Re-render existing clips")
    args = ap.parse_args()

    if set(args.letters) - set(PHONES):
        ap.error("--letters must be lowercase a-z")

    from kokoro import KPipeline

    pipeline = KPipeline(lang_code="b", repo_id=REPO, device="cpu")
    problems = check_vocab(pipeline.model)
    if problems:
        print("Phoneme table is invalid; Kokoro would drop these silently:", file=sys.stderr)
        print("\n".join("  " + p for p in problems), file=sys.stderr)
        return 2
    if args.check:
        print(f"OK: all {len(PHONES)} phonemes, schwa and stress are in Kokoro's vocab.")
        return 0

    stage = "probe" if args.probe else "full"
    letters = PROBE_LETTERS if args.probe else args.letters
    voices = BRITISH_VOICES if args.probe else [args.voice]
    folder = (args.output / "voice-probe") if args.probe else args.output

    records = []
    for voice in voices:
        for cand in candidates(letters):
            stem = (f"{cand['letter']}_{voice}" if args.probe
                    else f"{cand['letter']}_{cand['variant']}")
            rel = f"clips/{stem}.wav"
            clip = folder / rel
            if clip.exists() and not args.force:
                with wave.open(str(clip), "rb") as w:
                    duration = round(w.getnframes() / w.getframerate(), 3)
            else:
                duration = write_wav(clip, postprocess(render(pipeline, cand["ipa"], voice)))
                print(f"  {stem:28s} /{cand['ipa']}/  {duration:.2f}s", flush=True)
            records.append(dict(**cand, voice=voice, file=rel, duration_seconds=duration,
                                approval="pending_user_review"))

    (folder / "manifest.json").write_text(json.dumps(dict(
        engine="kokoro", repo=REPO, license="Apache-2.0", stage=stage,
        sample_rate=SAMPLE_RATE, format="24 kHz 16-bit mono PCM WAV",
        note="IPA targets, not verified pronunciations. Approval is recorded separately.",
        clips=records), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    page(folder, records, stage, args.voice)
    print(f"\n{len(records)} clips ready. Open: {folder / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
