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

23 files are unchanged copies of the selected 24 kHz, 16-bit mono PCM WAVs.
The user's replacement l is processed separately, as described below.
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

## Source and distribution permission — updated 2026-09-23

The recordings obtained from [s5k/ipa](https://github.com/s5k/ipa) are copies
of audio hosted by **Pronunciation Studio** for
[*The Sound of English*, 2023 sample](https://pronunciationstudio.com/wp-content/uploads/in5-archives/in5/in5/index.html).
All 46 chart MP3s matched the publisher's files byte for byte, including
`SOUND 13a.mp3`. The sample credits **© Joseph Hudson 2021–23**.
This identifies the published source; it does not establish the speaker's
identity or the allocation of recording rights between author and company.

**Non-profit educational permission received.** On 2026-09-23 Milo supplied
Pronunciation Studio's grant, signed by Scott Bessett, for the “Learn the 44
Sounds of British English” IPA Chart, associated recordings and related
educational content. The full user-provided text is preserved in
[the permission record](../../../docs/pronunciation-studio-permission.md).

The grant covers non-profit educational mobile apps, websites, classroom
resources, language-learning tools and public/private educational projects,
including use by the general public. Projects must remain exclusively
educational and not operated for profit. Materials may not be sold, licensed,
sublicensed or monetized; commercial use, paid subscriptions, advertising and
other profit-generating uses need prior written permission. Voluntary support
donations are permitted if access stays free and the project is noncommercial.
Attribute the original source and website whenever reasonably possible:
**Pronunciation Studio — http://www.pronunciationstudio.com**.

Original creators retain all copyrights and IP. This is a limited,
non-exclusive, revocable permission, with all other rights reserved. The audio
is not public domain or covered by a general open-source licence. This grant
supersedes the 2026-09-22 permission-outstanding status for non-profit
educational use; the source identification below remains unchanged.

`source-audit.json` records the upstream tree, publisher URLs, Git blob hashes,
SHA-256 hashes, and letter mapping. All 26 installed WAV hashes and their local
source hashes matched the existing manifest. The historical extraction mapping
was used; extraction was not rerun. The 24 outputs other than q/l derive from
22 distinct publisher recordings: c/k share one, and x joins k+s. The local
q/l overrides are user-supplied; this audit does not prove whether they are
new performances or edits of other recordings.

The earlier [permission request draft](../../../docs/phoneme-permission-request.md)
is retained as historical context. The user-supplied grant linked above is now
the permission record. No audio has been replaced by this documentation update.

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
