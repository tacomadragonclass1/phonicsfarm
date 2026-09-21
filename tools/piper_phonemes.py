#!/usr/bin/env python3
"""Render isolated phonemes with Piper, which accepts raw IPA phoneme ids.

Unlike Kokoro, Piper exposes `length_scale`, so an isolated phoneme can be
stretched instead of being emitted as a 60 ms sliver. Renders each letter at
several stretch factors so the user can pick by ear.

Piper uses the ESPEAK phoneme set: TRAP is /ae/ (U+00E6) and j is /dz/ (two
characters) -- BOTH DIFFER from Kokoro's misaki set. Do not copy a table
between engines.
"""
import html, json, sys, wave
from pathlib import Path
import numpy as np

VOICE = Path(__file__).parent.parent.parent.parent / ".local/share/phonicsfarm-tts/voices"
OUT = Path.home() / "Desktop/PhonicsFarm Sound Review/piper-ipa"
SCALES = [1.0, 2.0, 3.5]

# espeak-ng en-GB, derived from piper's own phonemizer on reference words.
PHONES = {
    "a": "æ", "b": "b", "c": "k", "d": "d", "e": "ɛ", "f": "f", "g": "ɡ",
    "h": "h", "i": "ɪ", "j": "dʒ", "k": "k", "l": "l", "m": "m", "n": "n",
    "o": "ɒ", "p": "p", "q": "kw", "r": "ɹ", "s": "s", "t": "t", "u": "ʌ",
    "v": "v", "w": "w", "x": "ks", "y": "j", "z": "z",
}


def norm(d, peak=0.89):
    d = np.asarray(d, dtype=np.float32).ravel()
    top = float(np.abs(d).max())
    return d * (peak / top) if top > 1e-7 else d


def main():
    from piper import PiperVoice
    from piper.config import SynthesisConfig

    model = next(VOICE.glob("*.onnx"), None)
    if not model:
        print(f"No piper voice in {VOICE}", file=sys.stderr); return 2
    v = PiperVoice.load(str(model))
    sr = v.config.sample_rate
    (OUT / "clips").mkdir(parents=True, exist_ok=True)

    rows, records = [], []
    for letter, ipa in PHONES.items():
        cells = []
        for scale in SCALES:
            ids = v.phonemes_to_ids(list(ipa))
            raw = v.phoneme_ids_to_audio(ids, SynthesisConfig(length_scale=scale))
            d = norm(raw)
            rel = f"clips/{letter}_x{scale:g}.wav"
            with wave.open(str(OUT / rel), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
                w.writeframes((np.clip(d, -1, 1) * 32767).astype("<i2").tobytes())
            dur = len(d) / sr
            records.append(dict(letter=letter, ipa=ipa, length_scale=scale,
                                file=rel, duration_seconds=round(dur, 3),
                                approval="pending_user_review"))
            cells.append(f'<div class=c><span class=l>&times;{scale:g} &middot; {dur:.2f}s</span>'
                         f'<audio controls preload=none src="{rel}"></audio></div>')
        print(f"  {letter}  /{ipa}/")
        rows.append(f'<tr><th>{letter}</th><td class=ipa>/{html.escape(ipa)}/</td>'
                    f'<td class=clips>{"".join(cells)}</td></tr>')

    (OUT / "manifest.json").write_text(json.dumps(dict(
        engine="piper", voice=model.stem, phoneme_set="espeak-ng en-GB",
        sample_rate=sr, length_scales=SCALES, license="MIT (piper) / see voice card",
        note="Raw IPA phoneme ids, peak-normalized. Targets, not verified pronunciations.",
        clips=records), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (OUT / "index.html").write_text('''<!doctype html>
<html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width">
<title>Piper &mdash; raw IPA phonemes</title>
<style>body{font:17px/1.6 system-ui,sans-serif;max-width:1050px;margin:40px auto;padding:0 20px;
background:#fffaf0;color:#20312a}table{border-collapse:collapse;width:100%;margin-top:1.4em}
th,td{padding:9px 12px;text-align:left;border-bottom:1px solid #d8d6c2;vertical-align:middle}
th{font-size:28px;width:1.5em}td.ipa{font-size:18px;color:#5a6b60;width:4.5em}
td.clips{display:flex;flex-wrap:wrap;gap:14px}.c{display:flex;flex-direction:column;gap:3px}
.l{font-size:11px;font-family:ui-monospace,monospace;color:#6b7a70}audio{height:32px;width:210px}
.note{background:#f4efe0;border-left:4px solid #b9ad84;padding:11px 16px;margin:1.3em 0;font-size:15px}
</style>
<h1>Piper &mdash; raw IPA phonemes</h1>
<p>Voice: <code>''' + model.stem + '''</code> &middot; fully local, downloadable, MIT.
Fed <b>raw IPA phoneme ids</b>, bypassing text entirely &mdash; so these are true
phonemes, not spellings.</p>
<div class=note><b>&times;1 / &times;2 / &times;3.5 is the stretch factor</b>
(Piper&rsquo;s <code>length_scale</code>). Isolated phonemes come out very short at
&times;1; stretching is the lever Kokoro did not expose. All clips are
peak-normalized, so a thin sound will also be a noisy one.</div>
<table><thead><tr><td>Letter</td><td>IPA</td><td>&times;1 &middot; &times;2 &middot; &times;3.5</td></tr></thead>
<tbody>''' + "\n".join(rows) + "</tbody></table></html>\n", encoding="utf-8")
    print(f"\n{len(records)} clips. Open: {OUT / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
