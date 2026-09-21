# Annette's voice

Annette is Phoneme Village's teacher. She speaks **only the sentence wrappers**;
the phoneme inside her question is the human recording from `../phonemes/`, so
the sound the child is asked to find is byte-identical to the sound the
alphabet block itself plays. Two voices are heard in one sentence by design —
the alternative was a second, TTS-imitated phoneme set that would not match
the blocks.

| Clip | Words | Source |
| --- | --- | --- |
| `annette_find.wav` | "Please find the letter that says" | **Milo's own recording** |
| `annette_good.wav` | "Good job!" | **Milo's own recording** |
| `wrong_chime.wav` | — | synthesized two-note fall, no speech |

24 kHz 16-bit mono PCM WAV, trimmed and normalized to match the phoneme clips.
`manifest.json` records the text, voice and duration of each.

## Status

The two sentences were **replaced with Milo's own recordings on 2026-09-20**,
superseding the Kokoro `bf_emma` renderings. Sources live in
`~/Desktop/PhonicsFarm Sound Review/` as `annnette find the letter.wav` (three
n's, as spelled there) and `annette good job.wav`; `manifest.json` records both
paths and their hashes. The originals are never modified.

They were installed through `tools/install_annette_clips.py`, which applies the
same postprocess the generator applies to its own output: trim to a 30 ms
lead-in and 140 ms tail, normalize to 0.89 peak. As supplied they carried 248 ms
and 211 ms of lead-in and 759 ms and 494 ms of trailing silence, and peaked at
0.74 and 0.92. The trailing silence is the one that matters: the phoneme plays
immediately after the sentence in the same queue, so that gap would have sat
between "...that says" and the sound the child has to match. Pass `--raw` to
install them byte-for-byte instead.

`wrong_chime.wav` is still synthesized and has not been heard by anyone.

## Why this route

A static GitHub Pages build has no server, so speech has to ship as audio.
The browser's Web Speech API was rejected: it needs a user gesture before it
will speak, offers no guarantee which voice (or any voice) exists on a given
browser or device, and its licensing for a distributed game is unclear.
Pre-rendered clips behave identically on every device and work offline.

## Regenerating

Reinstall from the review folder (this is what produced the current clips):

```sh
~/.local/share/phonicsfarm-tts/venv/bin/python tools/install_annette_clips.py
```

`tools/generate_annette.py` still renders synthetic stand-ins with local
[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache-2.0 model and
voices, so redistributable) if the recordings are ever lost. Either way no cloud
account, API key or network call is involved at build or run time.
