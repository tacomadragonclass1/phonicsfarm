#!/usr/bin/env python3
"""Step 1: is the voice any good, and is it British?

Renders a normal sentence in every British Kokoro voice. This is IN
distribution for the model, unlike a bare isolated phoneme. It separates
two very different failures:

  sentences sound fine  -> engine/voice are OK, isolated phonemes were the bug
  sentences sound bad   -> wrong engine, abandon Kokoro

Also renders the same sound three ways in one voice to show the difference.
"""
import html, sys, wave
from pathlib import Path
import numpy as np

OUT = Path.home() / "Desktop/PhonicsFarm Sound Review/step1-voices"
SR = 24000
VOICES = ["bf_alice", "bf_emma", "bf_isabella", "bf_lily",
          "bm_daniel", "bm_fable", "bm_george", "bm_lewis"]
SENTENCE = "The cat sat on the mat, and the dog ran to the bus stop."


def save(path, audio):
    audio = np.asarray(audio, dtype=np.float32)
    loud = np.where(np.abs(audio) > 0.008)[0]
    if len(loud):
        audio = audio[loud[0]:loud[-1] + 1]
    top = float(np.abs(audio).max()) or 1.0
    audio = np.concatenate([np.zeros(720, np.float32), audio * (0.89 / top),
                            np.zeros(2880, np.float32)])
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    return round(len(audio) / SR, 2)


def main():
    from kokoro import KPipeline
    p = KPipeline(lang_code="b", repo_id="hexgrad/Kokoro-82M", device="cpu")

    sent_rows, ipa_seen = [], {}
    for v in VOICES:
        audio = np.concatenate([a.numpy() for _, ps, a in p(SENTENCE, voice=v)
                                if a is not None] or [np.zeros(1, np.float32)])
        ipa_seen[v] = [ps for _, ps, a in p(SENTENCE, voice=v)][0]
        d = save(OUT / f"clips/sentence_{v}.wav", audio)
        print(f"  sentence  {v:14s} {d:5.2f}s")
        sent_rows.append((v, f"clips/sentence_{v}.wav", d))

    # Why the phoneme clips broke: same target, three amounts of context.
    demo, V = [], "bf_lily"
    for label, kind, text in [
        ("the word 'bat' (normal speech)", "word", "bat"),
        ("'buh' as a word", "word", "buh"),
        ("bare /b/ (what I sent you before)", "ipa", "b"),
    ]:
        if kind == "word":
            audio = np.concatenate([a.numpy() for _, _, a in p(text, voice=V) if a is not None])
        else:
            audio = np.concatenate([a.numpy() for _, _, a in
                                    p.generate_from_tokens(text, voice=V) if a is not None])
        f = f"clips/demo_{kind}_{text}.wav"
        d = save(OUT / f, audio)
        print(f"  demo      {label:36s} {d:5.2f}s")
        demo.append((label, f, d))

    row = lambda t, f, d: (f'<tr><td>{html.escape(t)}</td>'
                           f'<td><audio controls preload=none src="{f}"></audio></td>'
                           f'<td class=d>{d:.2f}s</td></tr>')
    (OUT / "index.html").write_text(f'''<!doctype html>
<html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width">
<title>Step 1 &mdash; do these voices sound British?</title>
<style>body{{font:17px/1.6 system-ui,sans-serif;max-width:860px;margin:40px auto;padding:0 20px;
background:#fffaf0;color:#20312a}}table{{border-collapse:collapse;width:100%;margin:1em 0 2.4em}}
td{{padding:9px 12px;border-bottom:1px solid #d8d6c2;vertical-align:middle}}
td:first-child{{font-weight:600}}td.d{{color:#7a8a80;font-size:14px;width:4em}}audio{{height:34px;width:300px}}
h2{{margin-top:1.6em;font-size:20px}}.q{{background:#f4efe0;border-left:4px solid #b9ad84;padding:12px 16px;font-size:15px}}
</style>
<h1>Step 1 &mdash; do these voices sound British?</h1>
<p>The same ordinary sentence in all 8 British Kokoro voices. This is normal
speech, which is what the model was trained on &mdash; unlike the single bare
phonemes I sent before.</p>
<p class=q><b>One question only:</b> does any voice here sound like a clean,
British speaker? If yes, name it and the phoneme problem is fixable. If they
all still sound foreign or garbled, Kokoro is the wrong engine and we drop it.</p>
<h2>The eight voices</h2>
<table>{"".join(row(f"{v}  ({'female' if v[1] == 'f' else 'male'})", f, d) for v, f, d in sent_rows)}</table>
<h2>Why the letter clips were garbled</h2>
<p>Same voice ({V}), same target sound, three amounts of context.
The last one is what I sent you before.</p>
<table>{"".join(row(t, f, d) for t, f, d in demo)}</table>
</html>
''', encoding="utf-8")
    print(f"\nOpen: {OUT / 'index.html'}")


if __name__ == "__main__":
    sys.exit(main())
