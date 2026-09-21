#!/usr/bin/env python3
"""Prepare Maisie review materials; contact Azure only with --generate."""

import argparse
import html
import io
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
import wave


VOICE = "en-GB-MaisieNeural"
FORMAT = "riff-24khz-16bit-mono-pcm"
PHONES = dict(zip("abcdefghijklmnopqrstuvwxyz", (
    "æ", "b", "k", "d", "ɛ", "f", "g", "h", "ɪ", "dʒ", "k", "l", "m",
    "n", "ɒ", "p", "kw", "ɹ", "s", "t", "ʌ", "v", "w", "ks", "j", "z",
)))
PAIRED = set("bcdgkpt")


def candidates():
    result = []
    for letter, phone in PHONES.items():
        variants = [("no_schwa_target", phone), ("with_schwa_target", phone + "ə")] \
            if letter in PAIRED else [("sound_target", phone)]
        for variant, ipa in variants:
            stem = f"{letter}_{variant}"
            ssml = (
                '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
                f'xml:lang="en-GB"><voice name="{VOICE}">'
                f'<phoneme alphabet="ipa" ph="{ipa}">{letter}</phoneme>'
                '</voice></speak>\n'
            )
            result.append(dict(letter=letter, variant=variant, ipa=ipa,
                               file=f"clips/{stem}.wav", ssml=ssml))
    return result


def validate_wav(data):
    with wave.open(io.BytesIO(data), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 24000):
            raise ValueError("Expected 24 kHz, 16-bit mono WAV")
        frames = audio.getnframes()
        samples = audio.readframes(frames)
        if frames == 0 or len(samples) != frames * 2 or not any(samples):
            raise ValueError("Empty, silent, or truncated WAV")
        return round(frames / 24000, 3)


def write_review(folder, entries):
    rows = []
    manifest = []
    for entry in entries:
        clip = folder / entry["file"]
        record = {k: v for k, v in entry.items() if k != "ssml"}
        record["approval"] = "pending_user_review"
        record["status"] = "awaiting_generation"
        player = "Awaiting generation"
        if clip.exists():
            record["duration_seconds"] = validate_wav(clip.read_bytes())
            record["status"] = "generated_unreviewed"
            player = f'<audio controls preload="none" src="{entry["file"]}"></audio>'
        manifest.append(record)
        label = entry["variant"].replace("_", " ")
        rows.append(f'<tr><th>{entry["letter"]}</th><td>{label}</td>'
                    f'<td>/{html.escape(entry["ipa"])}/</td><td>{player}</td></tr>')
    (folder / "manifest.json").write_text(json.dumps(dict(
        voice=VOICE, format=FORMAT, note="Targets, not verified pronunciations. Approval is recorded separately.",
        clips=manifest), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "index.html").write_text('''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>CVC Land — Maisie sound review</title>
<style>body{font:18px system-ui;max-width:1000px;margin:40px auto;padding:0 20px;background:#fffaf0;color:#20312a}
table{border-collapse:collapse;width:100%}th,td{padding:12px;text-align:left;border-bottom:1px solid #c9c8b8}
th{font-size:26px}audio{max-width:100%}</style>
<h1>CVC Land — Maisie sound review</h1>
<p>Compare the two versions of b, c, d, g, k, p, and t. Choose whichever makes the
consonant clearest to you. A short “uh” is an acceptable choice for this game.</p>
<p>Labels describe what Azure was asked to produce, not a verified result.
Nothing here is approved or connected to the game. Tell the assistant your
choices by letter and version, and which clips need another attempt.</p>
<p>Hard c and g; unvoiced s; consonant y; short British vowels. Proposed q = /kw/,
x = /ks/. Audio is unchanged Azure output for this first comparison.</p>
<table><thead><tr><td>Letter</td><td>Requested version</td><td>Target</td><td>Listen</td></tr></thead>
<tbody>''' + "\n".join(rows) + "</tbody></table></html>\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path.home() / "Desktop/PhonicsFarm Sound Review")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--credentials", type=Path, help="Private JSON file with SPEECH_KEY and SPEECH_REGION")
    parser.add_argument("--letters", default="abcdefghijklmnopqrstuvwxyz", help="Generate only these letters; e.g. b")
    args = parser.parse_args()
    if not args.letters or set(args.letters) - set(PHONES):
        parser.error("--letters must contain lowercase a-z")
    folder = args.output.expanduser()
    for name in ("clips", "requests"):
        (folder / name).mkdir(parents=True, exist_ok=True)
    entries = candidates()
    for entry in entries:
        request_path = folder / "requests" / (Path(entry["file"]).stem + ".ssml")
        if (folder / entry["file"]).exists() and (
                not request_path.exists() or request_path.read_text(encoding="utf-8") != entry["ssml"]):
            raise ValueError("Existing clip has different or missing request metadata; use a new --output folder")
        request_path.write_text(entry["ssml"], encoding="utf-8")
    write_review(folder, entries)
    if not args.generate:
        print(f"Prepared {len(entries)} candidates at {folder}. No Azure calls made.")
        return 0
    config = json.loads(args.credentials.expanduser().read_text()) if args.credentials else os.environ
    key = config.get("SPEECH_KEY", "").strip()
    region = config.get("SPEECH_REGION", "").strip()
    if not key or not re.fullmatch(r"[a-z0-9-]+", region):
        print("Generation blocked: configure SPEECH_KEY and SPEECH_REGION. No audio generated.", file=sys.stderr)
        return 2
    base = f"https://{region}.tts.speech.microsoft.com/cognitiveservices"
    headers = {"Ocp-Apim-Subscription-Key": key, "User-Agent": "PhonicsFarmSoundReview"}
    request = urllib.request.Request(base + "/voices/list", headers=headers)
    with urllib.request.urlopen(request, timeout=45) as response:
        voices = json.load(response)
    if not any(v.get("ShortName") == VOICE for v in voices):
        raise ValueError("Maisie is unavailable in this region; no substitute voice used")
    for entry in entries:
        clip = folder / entry["file"]
        if entry["letter"] not in args.letters or clip.exists():
            continue
        request = urllib.request.Request(base + "/v1", data=entry["ssml"].encode("utf-8"), headers={
            **headers, "Content-Type": "application/ssml+xml", "X-Microsoft-OutputFormat": FORMAT,
        })
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
        validate_wav(data)
        clip.write_bytes(data)
        write_review(folder, entries)
        print(f"Generated {clip.name} (unreviewed)", flush=True)
    print(f"Review page: {folder / 'index.html'}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.HTTPError as error:
        # Never print request headers, credentials, or Azure's response body.
        print(f"Azure returned HTTP {error.code}; existing clips retained. Check credentials, region, quota, or SSML.", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError:
        print("Azure connection failed; existing clips retained. Check network access.", file=sys.stderr)
        sys.exit(1)
    except (ValueError, OSError, wave.Error, EOFError):
        print("Invalid configuration, review files, or audio response. Existing clips retained; inspect local inputs.", file=sys.stderr)
        sys.exit(1)
