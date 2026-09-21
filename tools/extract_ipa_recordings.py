#!/usr/bin/env python3
"""Extract isolated phonemes from the s5k/ipa interactive chart recordings.

Source: https://github.com/s5k/ipa  (clone it next to this script, or pass --repo)

Each `SOUND n.mp3` is a human speaker saying the phoneme, a ~2 s pause, then an
example word. This keeps segment 1 and discards the example.

The number -> phoneme mapping is not in any data file; it was recovered from the
chart's own geometry and cross-checked three ways:
  1. the reading order of each region's `alt` text
  2. the numbered overlay labels ("1)" ... "46)") positioned on each hotspot
  3. voiceless/voiced pairing (fricatives 5 over 4, h unpaired; plosives 4 over 3)
"""
import argparse, html, json, shutil, subprocess, sys, wave
from pathlib import Path
import numpy as np

SR = 24000

# sound number -> (IPA, example word, ascii name, category)
MAP = {
    1:  ("i",  "bean",    "close front",            "monophthongs"),
    2:  ("ɪ",  "tip",     "near-close front",       "monophthongs"),
    3:  ("ɛ",  "met",     "open-mid front",         "monophthongs"),
    4:  ("ɛː", "hair",    "open-mid front long",    "monophthongs"),
    5:  ("a",  "pan",     "open front",             "monophthongs"),
    6:  ("u",  "moon",    "close back",             "monophthongs"),
    7:  ("ə",  "the",     "schwa",                  "monophthongs"),
    8:  ("əː", "sir",     "schwa long",             "monophthongs"),
    9:  ("ʌ",  "fun",     "open-mid back unrounded","monophthongs"),
    10: ("ɑː", "card",    "open back long",         "monophthongs"),
    11: ("ʊ",  "shook",   "near-close back",        "monophthongs"),
    12: ("ɔː", "shore",   "open-mid back long",     "monophthongs"),
    13: ("ɒ",  "lock",    "open back rounded",      "monophthongs"),
    14: ("ɪə", "dear",    "near-close to schwa",    "diphthongs"),
    15: ("eɪ", "same",    "mid to near-close",      "diphthongs"),
    16: ("aʊ", "loud",    "open to near-close back","diphthongs"),
    17: ("əʊ", "go",      "schwa to near-close back","diphthongs"),
    18: ("ʌɪ", "hide",    "open-mid to near-close", "diphthongs"),
    19: ("ɔɪ", "choice",  "open-mid back to near-close", "diphthongs"),
    20: ("ʊə", "curious", "near-close back to schwa","diphthongs"),
    21: ("f",  "first",   "voiceless labiodental",  "fricatives"),
    22: ("v",  "van",     "voiced labiodental",     "fricatives"),
    23: ("θ",  "thick",   "voiceless dental (theta)","fricatives"),
    24: ("ð",  "these",   "voiced dental (eth)",    "fricatives"),
    25: ("s",  "saw",     "voiceless alveolar",     "fricatives"),
    26: ("z",  "zen",     "voiced alveolar",        "fricatives"),
    27: ("ʃ",  "she",     "voiceless postalveolar (esh)","fricatives"),
    28: ("ʒ",  "casual",  "voiced postalveolar (ezh)","fricatives"),
    29: ("h",  "hard",    "voiceless glottal",      "fricatives"),
    30: ("p",  "pick",    "voiceless bilabial",     "plosives"),
    31: ("b",  "bed",     "voiced bilabial",        "plosives"),
    32: ("t",  "team",    "voiceless alveolar",     "plosives"),
    33: ("d",  "dine",    "voiced alveolar",        "plosives"),
    34: ("k",  "code",    "voiceless velar",        "plosives"),
    35: ("ɡ",  "get",     "voiced velar",           "plosives"),
    45: ("ʔ",  "witness", "glottal stop",           "plosives"),
    36: ("tʃ", "choose",  "voiceless postalveolar", "affricates"),
    37: ("dʒ", "jet",     "voiced postalveolar",    "affricates"),
    38: ("w",  "watch",   "labial-velar",           "approximants"),
    39: ("r",  "rug",     "alveolar",               "approximants"),
    40: ("j",  "yet",     "palatal",                "approximants"),
    41: ("l",  "look",    "clear l",                "lateral-approximants"),
    46: ("ɫ",  "tall",    "dark l",                 "lateral-approximants"),
    42: ("m",  "mode",    "bilabial",               "nasals"),
    43: ("n",  "neck",    "alveolar",               "nasals"),
    44: ("ŋ",  "song",    "velar (eng)",            "nasals"),
}
# SOUND 13a.mp3 supersedes an unused SOUND 13.mp3 that no chart button references.
FILENAME = {13: "SOUND 13a.mp3"}
ORDER = ["monophthongs", "diphthongs", "plosives", "fricatives", "affricates",
         "nasals", "approximants", "lateral-approximants"]


def decode(mp3):
    out = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", str(mp3),
         "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype="<f4").copy()


def first_segment(d, gap_ms=120, thr_rel=0.035):
    """Return (start, end) samples of the first utterance.

    Every file is <phoneme> <~2s pause> <example word>, so the first segment is
    the phoneme. A gap shorter than gap_ms is kept inside a segment, which keeps
    a plosive's closure attached to its release instead of splitting it in two.
    """
    fl = int(SR * 0.010)
    n = len(d) // fl
    rms = np.sqrt((d[:n * fl].reshape(n, fl) ** 2).mean(axis=1) + 1e-12)
    thr = max(rms.max() * thr_rel, 0.002)
    on = rms > thr
    if not on.any():
        raise ValueError("silent file")
    i = int(np.argmax(on))
    j, gapf = i, max(1, gap_ms // 10)
    while j < n:
        if on[j]:
            j += 1; continue
        k = j
        while k < n and not on[k]:
            k += 1
        if k - j >= gapf or k >= n:
            break
        j = k
    a, b = i * fl, min(j * fl, len(d))
    # Creep outward over quiet onsets/releases (a /f/ or /θ/ starts below thr).
    soft = max(thr * 0.18, 1e-4)
    lim = int(SR * 0.15)
    while a > 0 and a > i * fl - lim and abs(d[a - 1]) > soft:
        a -= 1
    while b < len(d) - 1 and b < j * fl + lim and abs(d[b]) > soft:
        b += 1
    return a, b


def process(d, a, b, pad_head=0.025, pad_tail=0.070, fade=0.005, peak=0.89):
    a = max(0, a - int(SR * pad_head))
    b = min(len(d), b + int(SR * pad_tail))
    seg = d[a:b].astype(np.float32).copy()
    top = float(np.abs(seg).max())
    if top > 1e-6:
        seg *= peak / top
    r = min(int(SR * fade), len(seg) // 2)
    if r:
        ramp = np.linspace(0, 1, r, dtype=np.float32)
        seg[:r] *= ramp
        seg[-r:] *= ramp[::-1]
    return seg


def write_wav(path, seg):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(seg, -1, 1) * 32767).astype("<i2").tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, required=True, help="clone of s5k/ipa")
    ap.add_argument("--out", type=Path,
                    default=Path.home() / "Desktop/PhonicsFarm Sound Review/ipa-recordings")
    args = ap.parse_args()

    media = args.repo / "assets/media"
    if not media.is_dir():
        print(f"No assets/media in {args.repo}", file=sys.stderr); return 2
    if not shutil.which("ffmpeg"):
        print("ffmpeg is required", file=sys.stderr); return 2

    records = []
    for num in sorted(MAP, key=lambda k: (ORDER.index(MAP[k][3]), k)):
        ipa, word, name, cat = MAP[num]
        mp3 = media / FILENAME.get(num, f"SOUND {num}.mp3")
        if not mp3.exists():
            print(f"  MISSING {mp3.name}", file=sys.stderr); continue
        d = decode(mp3)
        a, b = first_segment(d)
        seg = process(d, a, b)
        rel = f"clips/{cat}/{num:02d}_{ipa}_{word}.wav"
        write_wav(args.out / rel, seg)
        records.append(dict(ipa=ipa, example=word, description=name, category=cat,
                            file=rel, source=mp3.name, duration_seconds=round(len(seg)/SR, 3),
                            kept=[round(a/SR, 3), round(b/SR, 3)],
                            source_duration_seconds=round(len(d)/SR, 3),
                            approval="pending_user_review"))
        print(f"  {cat:22s} /{ipa}/ ({word})  {len(seg)/SR:.2f}s  from {mp3.name}")

    (args.out / "manifest.json").write_text(json.dumps(dict(
        source="https://github.com/s5k/ipa", extraction="first utterance; example word discarded",
        sample_rate=SR, format="24 kHz 16-bit mono PCM WAV",
        processing="peak-normalised to -1 dBFS, 5 ms fades, 25 ms head / 70 ms tail padding",
        note="Human recordings. Mapping recovered from chart geometry; pronunciation unverified by ear.",
        count=len(records), phonemes=records), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    groups = {}
    for r in records:
        groups.setdefault(r["category"], []).append(r)
    sections = []
    for cat in ORDER:
        if cat not in groups:
            continue
        cells = "".join(
            f'<div class=c><div class=ipa>{html.escape(r["ipa"])}</div>'
            f'<div class=ex>{html.escape(r["example"])}</div>'
            f'<audio controls preload=none src="{html.escape(r["file"])}"></audio>'
            f'<div class=meta>{r["duration_seconds"]:.2f}s</div></div>'
            for r in groups[cat])
        sections.append(f'<h2>{cat.replace("-", " ")} <span>({len(groups[cat])})</span></h2>'
                        f'<div class=grid>{cells}</div>')

    (args.out / "index.html").write_text('''<!doctype html>
<html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width">
<title>IPA phoneme recordings</title>
<style>
body{font:17px/1.6 system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 20px;
background:#fffaf0;color:#20312a}
h1{margin-bottom:.15em}h2{margin:1.8em 0 .7em;font-size:16px;text-transform:uppercase;
letter-spacing:.07em;color:#6b7a70;border-bottom:1px solid #d8d6c2;padding-bottom:6px}
h2 span{color:#a8b0a6;letter-spacing:0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:14px}
.c{background:#fff;border:1px solid #e3ded0;border-radius:10px;padding:11px 12px}
.ipa{font-size:27px;line-height:1.1}.ex{font-size:13px;color:#7a8a80;margin-bottom:7px}
.meta{font-size:11px;color:#a8b0a6;font-family:ui-monospace,monospace;margin-top:3px}
audio{width:100%;height:32px}
.note{background:#f4efe0;border-left:4px solid #b9ad84;padding:11px 16px;margin:1.2em 0;font-size:15px}
</style>
<h1>IPA phoneme recordings</h1>
<p>Human recordings, one isolated phoneme each &mdash; the example word that
followed it in the source has been trimmed off.</p>
<div class=note>Source: <code>github.com/s5k/ipa</code> (that clone has been
deleted). Each source file was &lt;phoneme&gt; &middot; 2&nbsp;s pause &middot;
&lt;example word&gt;; only the first utterance is kept, peak-normalised with 5&nbsp;ms
fades. <b>The number&rarr;phoneme mapping was reconstructed from the chart's
geometry, and no clip has been checked by ear.</b> Spot-check a few before use.</div>
''' + "\n".join(sections) + "\n</html>\n", encoding="utf-8")

    print(f"\n{len(records)} phonemes -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
