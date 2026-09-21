# Alphabet block recordings

Selected by the user on 2026-09-20 from
`~/Desktop/PhonicsFarm Sound Review/ipa-recordings/`. Maisie is deferred for
the blocks. These files are bundled locally; the game needs no TTS or network.

| Letter | IPA | Source example |
| --- | --- | --- |
| a | a | pan (short a) |
| b | b | bed |
| c | k | code |
| d | d | dine |
| e | ɛ | met |
| f | f | first |
| g | ɡ | get |
| h | h | hard |
| i | ɪ | tip |
| j | dʒ | jet |
| k | k | code |
| l | l | look (clear l) |
| m | m | mode |
| n | n | neck |
| o | ɒ | lock (short British o) |
| p | p | pick |
| q | kw | user's edited q sound.wav |
| r | r | rug (source chart's notation) |
| s | s | saw |
| t | t | team |
| u | ʌ | fun |
| v | v | van |
| w | w | watch |
| x | ks | code + saw |
| y | j | yet |
| z | z | zen |

Example words identify the source recordings; only isolated sounds play.
The source chart uses /a/ for the British TRAP vowel. c and k intentionally
use identical recordings. q uses the usual qu sound /kw/; x uses /ks/.

24 files are unchanged copies of the selected 24 kHz, 16-bit mono PCM WAVs.
q is an unchanged copy of the user's revised
`~/Desktop/PhonicsFarm Sound Review/q sound.wav` (also 24 kHz, 16-bit mono),
replacing the earlier automatic k+w assembly. The installer requires that edit
and preserves it on rebuild; use `--q-source` if it has moved.
x combines k+s, removing only the extraction's known 70 ms tail and 25 ms
head padding at the join. Its assembled join still needs a listening check.
No pitch, voice, or speed changes are applied.
The checked-in Godot import settings disable compression, trimming,
normalization and looping to preserve these short recordings.

`manifest.json` records exact source paths, processing and SHA-256 hashes.
The original extraction source is https://github.com/s5k/ipa, recorded by the
existing review manifest. The extraction handoff records no source LICENSE;
no distribution permission has been established by this integration.

To rebuild from the selected review folder, from the project root:

```sh
python3 tools/install_ipa_block_audio.py
```

The desktop source files and their historical review metadata are untouched.

## User replacements

Two letters are Milo's own audio, not the IPA recording, and `tools/
install_ipa_block_audio.py` must preserve both on any rerun — they are listed
in its `OVERRIDES` table. Sources live in `~/Desktop/PhonicsFarm Sound Review/`
and are never modified.

| Letter | Source file | Handling |
| --- | --- | --- |
| `q` | `q sound.wav` | unchanged copy (already 24 kHz at 0.89 peak) |
| `l` | `new letter l phoneme.wav` | trimmed and normalized; keeps its native 48 kHz |

`l` was replaced on 2026-09-20 because the IPA clip was not right. As supplied
it was 48 kHz with 135 ms of lead-in and a 0.46 peak, so it would have lagged
on pickup and dropped in level against its neighbours in a lever sequence —
hence the trim and normalize. The sample rate is left alone: resampling only
loses detail and Godot plays any rate. It is the one clip in this folder that
is not 24 kHz.

Adding another hand-made letter means adding a row to `OVERRIDES`, or the next
rerun of the installer silently reverts it.
