# Session handoff — 2026-09-20 (k)

## Deployed to GitHub Pages via Actions; two export bugs found and fixed

Goal: hit a URL from a work laptop with no Godot, play on a classroom touch
screen, take notes, tweak, push, repeat.

### The pipeline

`.github/workflows/deploy.yml`: on push to main it installs Godot 4.5.2 and the
export templates (cached), imports, **runs all five test suites**, exports the
Web preset, checks the output is non-empty, and publishes to Pages. A failing
suite stops the deploy so the last good build stays live. Nothing is built
locally; the work machine needs only a browser.

One-time manual step, because the `gh` CLI token is dead (a known state -- SSH
works fine): create the repo on github.com and set **Settings → Pages → Source:
GitHub Actions**. Without that the workflow runs with nowhere to publish.

### Bug 1 — the export shipped a game whose scripts could not compile

`export_filter="scenes"` follows only scene dependencies. Everything reached by
a `preload()` inside GDScript was omitted: all 26 phonemes, Annette's 3 clips,
and the word list. In the browser the clearing rendered normally and looked
fine, but the console showed 39 errors -- every preload missing, the
PhonemeAudio autoload failing to instantiate, `player.gd` failing to compile.
No audio, no movement, no lever, no village. Fixed with
`export_filter="all_resources"` (the pack went 872 KB → 1.69 MB). **Do not
narrow that filter again.**

### Bug 2 — the bridge deck rendered grey in the export only

`river.tscn` set `surface_material_override/0..2` on the GLB's mesh node at
`parent="Bridge/Model"`. That node lives inside a *nested* instanced scene, and
those overrides are dropped in an exported build. The deck fell back to the
model's own "stone" material -- pale blue-grey at metallic 1 -- which reads as
a flat grey slab. The sibling `river_tile.tscn` survives the same trick only
because its override targets a direct child of the instance root.

Confirmed by matching the browser's grey against the GLB's own
`stone rgb(0.72,0.89,0.91)`, and by checking the river tiles were showing the
project's blue water rather than the model's pale cyan. Fixed with
`environment/bridge_materials.gd`, a @tool script on the plain `Bridge` node
that assigns the three colours at runtime, where nothing can drop them.

Neither bug was visible natively or in any headless test. Both were caught only
by loading the real exported build in a browser.

### Verified

Clean import; all five suites zero failures; export produces a complete build;
loaded in Chrome from a local server with **zero console errors**; bridge now
matches the native render; AudioContext reaches `running` at 48 kHz after a
real click (browsers require a gesture -- the first tap supplies it on a touch
screen). Export templates are now installed locally too, so hand exports work.

### Still open

- A physical gamepad and a real multitouch device remain untested. The giant
  touch screen is the first real test of the touch controls.
- `wrong_chime.wav` is synthesized and unheard.
- The repo tracks the four Kenney source packs (74 MB, 44 MB of history). Fine
  for GitHub; only `assets/kenney/` is actually used at runtime.
- Publishing makes the phoneme recordings public; their licence provenance is
  still unresolved, as recorded in `assets/audio/phonemes/README.md`.

# Session handoff — 2026-09-20 (j)

## New letter l phoneme, and the installer no longer reverts hand-made letters

`assets/audio/phonemes/l.wav` is now Milo's `~/Desktop/PhonicsFarm Sound Review/
new letter l phoneme.wav`; the IPA `41_l_look.wav` clip was not right. Nothing
else referenced that source, and `l` is one shared file, so both CVC Land and
Phoneme Village pick it up.

As supplied the clip was 48 kHz, 135 ms of lead-in, 0.46 peak. It was trimmed
to a 12 ms lead / 60 ms tail and normalized to 0.89, matching the rest of the
folder: the lead-in is the documented pickup-lag trap, and 0.46 would have made
l audibly quieter than its neighbours in a lever sequence. The 48 kHz rate was
deliberately KEPT -- resampling only loses detail and Godot plays any rate, so
l is the one clip in the folder that is not 24 kHz. `--raw`-style byte-for-byte
install is available by flipping `process` to False in the installer's
OVERRIDES table.

`tools/install_ipa_block_audio.py` had the q override hardcoded, so a rerun
would have silently reverted l to the generic IPA clip. That special case is
now an `OVERRIDES` table holding both q and l, with per-letter processing, and
the docstring says that any future hand-made letter must be added to it. The
script stays stdlib-only (no numpy, and no audioop -- removed in Python 3.13,
and this box runs 3.14).

Verified by hashing all 26 clips before and after a full installer rerun: only
`l.wav` changed, the other 25 are byte-identical, so the q override held and
nothing else drifted. Clean Godot import; smoke, lever, feedback and village
suites pass with zero failures.

Git checkpoint remains `ba152a3`; everything still uncommitted.

# Session handoff — 2026-09-20 (i)

## Annette's two lines replaced with Milo's own recordings

Swapped `assets/audio/voice/annette_find.wav` and `annette_good.wav` for
`~/Desktop/PhonicsFarm Sound Review/annnette find the letter.wav` (three n's, as
spelled there) and `annette good job.wav`. The Kokoro `bf_emma` renderings are
superseded. Source files were not modified.

Installed via the new `tools/install_annette_clips.py`, which applies the same
postprocess `generate_annette.py` applies to its own output: trim to 30 ms lead
/ 140 ms tail, normalize to 0.89 peak. As supplied the clips carried 248/211 ms
of lead-in, 759/494 ms of trailing silence, and peaked at 0.74/0.92. The
trailing silence was the reason to process rather than straight-copy -- the
phoneme plays immediately after the sentence in the same audio queue, so three
quarters of a second of dead air would have landed between "...that says" and
the sound being asked for. `--raw` installs byte-for-byte if that is ever
wanted. Both files are 24 kHz 16-bit mono, matching the phonemes.

`manifest.json` now records each clip's source path, source hash and output
hash. The **`pending_user_review` caveat no longer applies to these two** --
they are Milo's own voice. `wrong_chime.wav` is still synthesized and unheard.

Separately, `~/Desktop/tts app.html` was patched (backup alongside it): its
"Save .wav..." dialog called `showSaveFilePicker`, which Chromium refuses on
`file://` pages, and the failure only wrote a line to the app's status bar. Two
saves produced no file anywhere on the system. Any picker failure now falls
through to a normal browser download and the status names the destination.
That app is outside this repo.

Checks: clean Godot import; village, lever and feedback suites pass with zero
failures. Git checkpoint remains `ba152a3`; everything still uncommitted.

# Session handoff — 2026-09-20 (h)

## Camera angle, the white crop patch, the stuck-prompt bug, and Annette's touch

Four requested fixes. One of them uncovered a second, separate bug.

### 1. Camera

`environment/fixed_camera.gd` now derives the camera's position AND rotation
from exported `pitch_degrees` / `yaw_degrees` / `distance` / `zoom` /
`minimum_width`, instead of a transform baked into the scene. The scene node no
longer carries a transform; the script owns it, so dragging the camera in the
editor viewport will be overwritten. Tune it in the inspector.

Now 18 degrees down (was 25), yaw 30 (was 45), size max(13, 18/aspect) (was
max(18, 25/aspect)). Lower, closer, and turned off-axis so boxes, cottages and
the bridge each show two faces instead of one flat one.

**Yaw 45 is the axis-aligned value.** At 45 the board's local +X is exactly
screen-right and the river runs flat across the screen; at 30 the whole board
sits 15 degrees rotated on screen, which is what produces the three-quarter
look. That trade is the point of the change, but it does mean the old handoff
rule "local +X is screen-right" is only true at yaw 45. README says so now.
Player movement needed no change -- it reads its axes off the camera basis.

### 2. The white patch below the fence

It was the crop plot. Kenney's `crops_wheatStageB` has two surfaces and the
larger one is an untextured `_defaultMat` at pure white (1,1,1), so twelve of
them read as a glitchy white smear. Replaced with `crop_pumpkin`, one readable
shape each. Several other Nature Kit props carry the same white `_defaultMat`
but only as a small highlight surface (path stones, mushroom stems, a rim on
`rock_largeB`, the sign post); those are left alone.

### 3. The stuck prompt -- two causes, both fixed

**Cause A, the one reported.** `c.wav` and `k.wav` are byte-identical (sha256
`33d6e55b...`, both from `clips/plosives/34_k_code.wav`). So "find the letter
that says /k/" had TWO right answers and the game accepted one. q is /kw/ and
x is /ks/, both opening on that same /k/. The village alphabet is now 23
letters -- k, q and x removed, as requested. CVC Land keeps all 26; the lever
game needs them.

**Cause B, found while fixing A.** `target` was never cleared after a correct
answer. Walking out during the celebration or the six-second pause put the
village to sleep with the found letter still set as the target, and walking
back in re-asked for the block that had just poofed -- a question with no
answer on the board. Fixed: `target` is cleared the moment a letter is found,
a `found` list is kept per round, `next_prompt()` skips any queued letter that
is no longer on the board, and `resume()` now decides between starting a round,
moving to the next letter, or repeating the outstanding one. `celebrate()` also
no longer overwrites the ASLEEP state if Chuck leaves mid-celebration.

`tests/village.gd` has a regression for exactly this: find a letter, walk out
mid-celebration, walk back in, and assert the new question is neither the
letter just found nor any earlier one, and that the letter asked for is
actually on the board.

### 4. Annette repeats the sound on touch

A 1.15-radius `Area3D` on Annette. Walking into her replays just the target
phoneme -- no sentence. She does nothing while she is still speaking, so
bumping her on the way into the village cannot chop her question in half, and
nothing changes about the question. She has no collision body: a five-year-old
should not be able to wedge Chuck against the teacher.

### Affected

`environment/fixed_camera.gd` (rewritten), `scenes/main.tscn` (camera node),
`village/phoneme_village.gd` (letter set, target/found tracking, resume,
Annette touch), `village/phoneme_village.tscn` + `tools/build_phoneme_village.py`
(pumpkins, Annette's Area3D), `tests/village.gd`, README.

### Checks actually run

Clean Godot 4.5.2 import. All five suites pass with zero failures; the village
suite is now 42 checks. Captures inspected at `/tmp/phonics-clearing.png`,
`/tmp/phonics-village.png` and `/tmp/phonics-village-close.png`.

### Still open

- **Nobody has listened to Annette.** `assets/audio/voice/` is
  `pending_user_review`; `bf_emma` was assumed, never chosen.
- No physical gamepad, multitouch or browser export test.
- Human phoneme licence provenance still unresolved.

### Git

Checkpoint remains `ba152a3`; everything is still **uncommitted**. No commit,
push or deployment was requested or performed.

# Session handoff — 2026-09-20 (g)

## Phoneme Village, a 40x40 field per clearing, and one outer wall

Implemented the four requested items. Four clarifying answers shaped the build:
a **separate** block set for the village, Annette **spliced** in front of the
existing human phonemes, a **soft tone + re-prompt** on a wrong pick, and
**40x40 per clearing with one wall around both**. All four were the recommended
option. Stated assumptions, not asked: ramps rather than a jump (Chuck has no
jump), the round pauses when he leaves, and Annette is an on-screen villager.

### 1. CVC Land field and river

The editor changes left in place (Ground scaled X by 50, both grass meshes
stretched in Z) were replaced with a coherent layout rather than reverted. The
grass now runs 260 wide and from z -204 to z +140, and two new `RiverBand`
meshes fill the z 4..8 strip outside the river so no background shows through
at the river line -- that pale band either side of the river was the visible
artifact of the stretch. The river itself went from 17 tiles to 41, spanning
x -41..41, and the water barriers grew from 15.6 to 18.85 to reach the new
wall while still leaving the bridge gap. The clearing grew 34 -> 40, so the
tree/plant ring was pushed out by the same 40/34 factor and the north tree
line respaced evenly around a 13.6-unit gate. Scaling alone had put Tree04/06
0.19 apart and Tree08/10 1.13 apart; that is fixed.

### 2. One boundary, not two

The four walls that ringed the 34x34 clearing are gone. A single boundary now
rings the entire world: x = +-20.25, z = +20.25 south and z = -68.25 north.
The ground collider matches at 40.5 x 88.5. Chuck can walk out of either
clearing, around the back of the trees, and up the corridor without meeting
anything. `tests/layout.gd` now proves both halves of this: that he passes
straight through where the old wall stood, and that he is still stopped at the
edge of the world.

### 3. Phoneme Village

North of CVC Land across an 8-unit corridor, centred at z = -48. A circular
clearing ringed by 26 trees with a south gate, six Mini Forest cottages, a
village green with campfire and seating logs, a fenced crop plot, a camp, a
stone path, scattered undergrowth, and Annette (`character-female-a`) at the
gate. Three walkable levels: the floor, a 13x14 terrace at y = 1.0 reached by
a ramp on its south-west, and a 6x6 lookout at y = 2.0 on top of that. Each
level is a different shade of green and rimmed with boulders -- the first
version used the clearing's own grass for the raised caps and the levels were
invisible from the game camera, which is the only view the child gets.

The round: entering wakes Annette, who asks for one letter's sound. The right
block rises over Chuck's head, flashes white/gold, poofs into smoke, and she
says "Good job"; six seconds later she asks for the next. The wrong block
plays its own sound, a soft two-note chime, and the same question again, and
stays in his hands to put down. All 26 found -> a fresh board with the letters
in different places. Leaving pauses; returning repeats the same question.

### 4. Speech that survives a static export

Web Speech API was rejected, not attempted: it needs a user gesture, offers no
voice guarantee per browser/device, and its licensing for a distributed game is
unclear. Annette is **pre-rendered** with the existing local Kokoro-82M setup
(Apache-2.0 model and voices, so shippable) into `assets/audio/voice/`:
`annette_find.wav`, `annette_good.wav`, and a synthesized `wrong_chime.wav`.
Only the sentence wrappers are TTS. The phoneme in her question is the same
human recording the block plays.

**These three clips are `pending_user_review` and have not been heard by
anyone.** `bf_emma` was used because the phoneme review set used it; a final
voice was never chosen. Re-render with
`tools/generate_annette.py --voice <name> --force`.

### Affected

New: `village/phoneme_village.tscn` + `.gd`, `environment/kenney_props.gd`,
`tests/village.gd`, `tools/build_phoneme_village.py`, `tools/generate_annette.py`,
`assets/audio/voice/`, 35 more Kenney GLBs under `assets/kenney/`.
Changed: `scenes/main.tscn` (ground, walls, tree ring, corridor, village),
`environment/river.tscn` (41 tiles, wider barriers), `audio/phoneme_audio.gd`
(a VOICE dict sequenced in the same queue as letters), `alphabet_block.gd`
(`picked_up` signal, `home` container, `set_face_color`, `vanish`),
`player.gd` (`ground_height` raycast, drops return to `home`),
`tests/layout.gd`, `tests/capture.gd`, `export_presets.cfg`, README.

`tools/build_phoneme_village.py` is a one-time scaffold. The .tscn it produced
is the source of truth now and is meant to be edited in the editor; rerunning
it with `--force` discards those edits.

### Checks actually run

Godot 4.5.2 editor import clean. All five headless suites pass with zero
failures: smoke, layout, lever, feedback, and the new village suite (35
checks covering the round, a wrong answer, a right answer, the pause/resume,
spawn markers on all three levels, Chuck actually walking up the ramp under
input, a block dropped on the terrace staying on the terrace, the board
refresh moving 25 of 26 letters, and CVC Land's row being untouched
throughout). Rendered captures inspected at `/tmp/phonics-village.png`,
`/tmp/phonics-village-close.png`, `/tmp/phonics-overview.png` and
`/tmp/phonics-world.png`.

One real bug was found by the smoke suite and fixed, not worked around: the
first version of `ground_height` cast from above Chuck's head, so a player
boxed in by obstacles could drop a block onto the top of one of them.

### Not done / still open

- **Nobody has listened to Annette.** Do not call her clips verified.
- No physical gamepad, multitouch device or browser export test.
- Audio-source licence provenance for the human phonemes is still unresolved,
  as recorded in `assets/audio/phonemes/README.md`.
- The river ends at x +-41, visible only in the `--world` diagnostic capture,
  never at the game camera's zoom.

### Git

Checkpoint remains `ba152a3`. Everything above is **uncommitted**, on top of
the previous session's uncommitted work. `assets/audio/`, `assets/words/`,
`audio/`, `lever/`, `village/`, `tools/` and the new tests are untracked --
`git diff` alone will not show them. No commit, push or deployment performed;
none was requested.

# Session handoff — 2026-09-20 (f)

## Claude Code resume brief — 2026-09-20

**Status: requested implementation complete; awaiting the user's next task.**
Latest request was to update the handoff for Claude Code, not add gameplay or
commit. Read AGENTS.md and README.md, inspect status/diff, and preserve all
existing work. The sections below are newest-first history: old pending voice
approvals, no-audio/no-word-validation scope, and future-lever notes are superseded.

Current decisions to preserve:
- Human recordings are installed for all 26 letters; Maisie is deferred for
  blocks. Do not restart the abandoned TTS/provider experiments.
- q uses the user's `~/Desktop/PhonicsFarm Sound Review/q sound.wav`, copied
  unchanged to `assets/audio/phonemes/q.wav`. The installer preserves that
  override. Other source phonemes are in the review folder's `ipa-recordings/`;
  x remains the assembled k+s clip. No source files were modified.
- Pedestal centers are 2.38 units apart (30% closer). Left-hand lever plays
  occupied slots left-to-right with no minimum occupancy and no word gate on
  sound playback. All existing interaction controls work, including carrying.
- Lever pulse, per-sound pedestal lift/gold faces, exact height reset, valid-word
  gold/sparkle, removal color reset and remaining-word revalidation are complete.
  Physics bodies/SnapPoints stay fixed; only visible geometry lifts.
- Offline recognition uses 870 one-to-three-letter dictionary entries. It is
  finite word-list membership, not pronunciation validation. Empty slots are
  ignored. Source, coverage, filters and copyright are in `assets/words/`.

Implementation entry points: `audio/phoneme_audio.gd` owns playback and sequence
completion/cancellation; `lever/sound_lever.gd` coordinates the ordered slots,
effects and word result; `pedestal/pedestal.gd` owns occupancy and visual lift;
`alphabet_block/alphabet_block.gd` owns isolated face materials and sparkles.
`player/player.gd` chooses the nearest reachable interaction. Main-scene lever
paths define slot order. See README for architecture and commands.

Last implementation validation: Godot 4.5.2 import and all four headless suites
(`smoke.gd`, `layout.gd`, `lever.gd`, `feedback.gd`) passed. Rendered feedback
captures were inspected and still exist at `/tmp/phonics-feedback-active.png`
and `/tmp/phonics-feedback-word.png`; regenerate with the capture helper's
`-- --feedback` option, without --headless. Physical devices, browser export
and listening validation remain untested. Audio-source license provenance is
still unresolved as recorded in `assets/audio/phonemes/README.md`.

Git checkpoint remains `ba152a3` (Fix clearing layout, river crossing, and Chuck
controls). Everything since that checkpoint remains **uncommitted**. In
particular `assets/audio/`, `assets/words/`, `audio/`, `lever/`, the new lever/
feedback tests and `tools/` are untracked; `git diff` alone will not show them.
There are also tracked changes to project/scenes, block/pedestal/player scripts,
export settings, existing tests and documentation. Do not discard or overwrite
these directories or blindly stage the abandoned tools as part of unrelated work.
No commit, push or deployment was requested or performed.

This handoff-only task updates CLAUDE.md and PROGRESS.md. Checked current Git
state, existing test log and capture files, then ran `git diff --check`.
Runtime tests were not rerun for this documentation-only update.

## Previous implementation handoff — 2026-09-20 (e)

## Lever bounce/glow and offline word recognition

Implemented the approved visual-feedback suggestion:
- Lever pull snaps down and emits a 0.45-second expanding golden ring.
- Each occupied pedestal lifts its visible column, top and block by 0.35 units
  during that slot's actual sound. The faces turn gold; letters remain dark.
  The previous pedestal returns to its exact rest geometry before the next
  sound, and the final pedestal resets on completion. SnapPoint and physics
  bodies do not move, so Chuck can retrieve a block even mid-lift.
- After a complete sequence, recognized words retain gold faces and emit a
  brief sparkle. Invalid combinations return to default colors. Empty slots
  are skipped for spelling just as for sound; a/i and two-letter words work.
- Removing a block immediately restores that block's default color/lift and
  rechecks the remaining slots (cat -> at retains gold; at -> t clears it).
  Placement clears the old result until the next pull. Repeated pulls restart
  cleanly; interrupted audio cancels pending lift/color effects. Per-block
  material copies prevent shared-resource recoloring of other blocks.

Offline dictionary: `assets/words/english_words.gd`, 870 short words derived
from SCOWL 2020.12.07 English/British/American word categories through size 70,
plus qat from size 80. a/i are the only standalone one-letter entries.
Proper-name/uppercase/abbreviation categories are excluded; explicit filters
also remove alphabet plurals and several unit/math abbreviations appearing
in the ordinary-word files. This is finite dictionary membership, not CVC or
phoneme-to-word pronunciation validation. Some rare/regional words may be
absent. Source and coverage are documented in `assets/words/README.md`.
`tools/build_short_word_list.py` rebuilds from the upstream tar archive.
Full upstream copyright notices are bundled and included in the Web preset.

Affected: alphabet block material/lift/sparkle code, pedestal occupancy and
lift code, audio completion/cancellation signals, lever sequencing/pulse/word
feedback, new dictionary and builder, export notices filter, README, capture
helper, new `tests/feedback.gd`, and this handoff. Existing audio assets,
pedestal spacing, controls and user-edited q remain in use.

Checks actually run: Godot 4.5.2 editor import; smoke, layout, lever and new
feedback suites all passed with zero failures. Feedback tests cover sound
order, lift/rest geometry, fixed collider/snap heights, independent material
colors, valid/invalid/sparse/single-letter words, removal revalidation,
actual player retrieval while raised, cancellation, restart and empty pulls.
The final feedback rerun includes rejection of unit/math abbreviations and
acceptance of qat. `git diff --check` passed.
Rendered `tests/capture.gd -- --feedback` using the actual Compatibility
renderer; inspected `/tmp/phonics-feedback-active.png` (pulse, raised gold c)
and `/tmp/phonics-feedback-word.png` (all pedestals at rest, gold cat/sparkles).
No physical device, browser export or new pronunciation listening check.

Git: prior uncommitted work preserved; all changes remain uncommitted.
No push or deployment performed. Other CVC Land changes remain future work.

## Previous lever/audio handoff — 2026-09-20 (d)

## Revised q, closer pedestals and playback lever

Implemented the user's next request:
- `assets/audio/phonemes/q.wav` is an exact copy of
  `~/Desktop/PhonicsFarm Sound Review/q sound.wav` (24 kHz, 16-bit mono,
  about 0.549 seconds). Its source and hash are recorded in the manifest.
  `tools/install_ipa_block_audio.py` now requires/preserves this edited q
  instead of rebuilding k+w; `--q-source` can override the source location.
- The outer pedestals moved 30% toward the unchanged center pedestal.
  Adjacent center spacing is now 2.38 units instead of 3.4.
- New `lever/sound_lever.tscn` + `.gd`: wooden base, metal shaft, red handle,
  PLAY marking, solid collider and pull/return animation, screen-left of
  the pedestal row. The main scene assigns its three pedestal paths in
  left-to-right order. Interact near it with the existing E/Space/controller/
  Pick / Put action, with either empty hands or a carried block.
- The lever snapshots occupied slot letters at activation and plays them
  consecutively, skipping empty slots. There is no word validation or
  minimum occupancy: zero slots is silent, any one/two/three slots works.
  `audio/phoneme_audio.gd` advances on audio completion. Another pull
  restarts the queue; normal block pickup/placement replaces the queue.
- `player/player.gd` selects the nearest reachable lever or block/empty
  pedestal, preserving usual placement and retrieval. Lever reach uses
  the same distance and obstruction checks as other interactions.

Checks actually run: Godot 4.5.2 editor import, existing headless smoke and
layout suites, and new `tests/lever.gd` all pass (zero test failures).
Lever tests cover all eight occupancy masks, left-to-right screen order,
30% spacing, completion-based sequence timing, rapid restart, pickup
interruption, carrying while pulling, handle return, obstruction and range.
The test waits for both playback and the queue to finish, accounting for the
brief interval before Godot emits its completion signal. File comparison
confirms q is byte-identical to the user edit; all 26 manifest hashes match.
`git diff --check` passed. The sandbox's editor socket restriction required
rerunning import outside the sandbox; that import completed cleanly.

Rendered `tests/capture.gd -- --pedestals` without --headless and inspected
`/tmp/phonics-pedestals.png`: clear lever left of the three closer pedestals.
The capture uses temporary c/a/t blocks only in its running scene, not the
saved level. README and audio provenance notes updated. No listening check,
physical controller/tablet test or browser export performed.

Git: previous uncommitted audio integration and tools preserved. This task
also changes player, main scene, capture helper, q asset/manifest/installer,
audio queue, documentation, and adds the lever scene/script and lever test.
No commit, push or deployment performed. Other CVC Land work remains future.

## Previous audio integration — 2026-09-20 (c)

## Human phonemes integrated for all 26 alphabet blocks

The user selected the clean recordings in
`~/Desktop/PhonicsFarm Sound Review/ipa-recordings/` and deferred Maisie for
the blocks. This supersedes the pending voice decisions/review gates below.

All successful pickups, ground drops, pedestal placements and retrievals now
play the letter's recording. Failed actions are silent. One shared player
restarts for the latest interaction so sounds do not overlap. No sound plays
on startup or while editing. Original desktop recordings remain untouched.

Mapping uses short British vowels, hard c/g, unvoiced s, clear l, consonant y;
c/k share the same source. q=/kw/ and x=/ks/ are assembled from k+w and k+s,
removing only the extraction padding at the join. 24 letter WAVs are exact
source copies. See `assets/audio/phonemes/README.md` for the complete mapping
and `manifest.json` for provenance, processing and SHA-256 hashes.

Affected files: `alphabet_block/alphabet_block.gd`, `pedestal/pedestal.gd`,
`project.godot`, new `audio/phoneme_audio.gd` autoload, 26 WAVs and import
settings under `assets/audio/phonemes/`, `tools/install_ipa_block_audio.py`,
`tests/smoke.gd`, README and this handoff. Import settings preserve PCM audio
without compression, normalization, trimming or looping.

Checks: all 26 WAVs are valid 24 kHz 16-bit mono PCM, non-silent, unclipped;
manifest hashes match and 24 copies match their sources byte-for-byte.
Godot 4.5.2 editor import completed; the initial pass reported missing WAV
loaders before importing the new files, and the following pass was clean.
Expanded headless smoke suite and existing layout suite both passed with
zero failures, covering all 26 audio streams, replacement playback,
pickup/drop/placement/retrieval audio and silent failed actions.

Limitations: no listening check performed here, especially for assembled q/x
joins. Physical audio output and Web playback remain untested. The earlier
source-license uncertainty is recorded in the asset README. Lever sequencing
and CVC Land changes remain future work, outside this alphabet-audio task.

Git: existing PROGRESS.md edits and untracked tools preserved. This task adds
the files above; no commit, push or deployment requested or performed.

## Previous extraction handoff — 2026-09-20 (b)

## TTS ABANDONED for phonemes — using real human recordings instead

The user rejected every synthesis route by ear: Kokoro (garbled, "sounds
foreign"), and isolated phonemes generally. Root cause established: a bare
phoneme is out-of-distribution for any sentence-trained neural TTS, and is
entirely utterance-initial AND utterance-final, the least stable positions.
Confirmed by the user — the word "bat" sounded fine, "buh" and bare /b/ were
"like a damn modem". Do not re-propose Kokoro/edge-tts for isolated phonemes.
Azure was reconsidered but NOT adopted; still no account.

**Current source of truth: `~/Desktop/PhonicsFarm Sound Review/ipa-recordings/`**
46 human-recorded British English phonemes, the full inventory:
13 monophthongs, 7 diphthongs, 7 plosives, 9 fricatives, 2 affricates,
3 nasals, 3 approximants, 2 lateral approximants.

Extracted by `tools/extract_ipa_recordings.py` from https://github.com/s5k/ipa
(an InDesign/in5 export of an interactive IPA chart). Each source mp3 is
<phoneme> · ~2 s pause · <example word>; only the first utterance is kept.
**The clone was deleted after extraction, per the user's instruction** — re-clone
to re-run. 24 kHz 16-bit mono WAV, peak-normalised to -1 dBFS, 5 ms fades.

### How the number -> phoneme mapping was recovered

No data file contains it. The chart is ONE page of 46 absolutely-positioned
hotspots. Buttons carry `data-click-play="<audio item id>"`; positions live in
`assets/css/pages.css` keyed by `#item<id>`, NOT inline. Region labels are in
`<img alt>` text; numbered overlays ("1)".."46)") sit on each hotspot.
Cross-checked three ways: alt reading order, the numbered overlays, and
voiceless/voiced pairing (fricatives 5 over 4 with h unpaired; plosives 4 over 3).
Internal consistency confirms it — extracted short/long vowel pairs came out
with the expected durations (/ɪ/ 0.35s vs /i/ 0.79s, /ɒ/ 0.34s vs /ɔː/ 0.81s),
plosives shortest (/ʔ/ 0.23s), fricatives and nasals held long.
Note `SOUND 13a.mp3` supersedes an orphan `SOUND 13.mp3` no button references.

### Checks run

All 46 verified programmatically: correct format, none silent, none clipped,
and none containing an internal gap >250 ms (which would mean the example word
leaked in). **No clip has been checked by ear — mapping and pronunciation are
unverified aurally.** The user should spot-check before wiring anything in.

The chart uses a modern SSB transcription: /a/ for TRAP, /ɛː/ for SQUARE,
/ʌɪ/ for PRICE, /əː/ for NURSE. Game letters map to a SUBSET of these 46;
that letter->phoneme mapping is NOT yet decided.

⚠️ The source repo has **no LICENSE file**. Fine for classroom use; if the game
is ever distributed, provenance needs checking.

### Also on disk from the abandoned TTS work

`tools/generate_phonemes.py` (Kokoro), `tools/piper_phonemes.py` (Piper raw
IPA), `tools/step1_voice_check.py`, and `tools/prepare_phoneme_review.py`
(Azure, unused, NOT run). Review pages: `voice-probe/`, `step1-voices/`,
`piper-ipa/`. `TTS-INPUTS.md` holds per-engine IPA tables — the IPA differs
per engine (Kokoro `a`/`ʤ` vs espeak `æ`/`dʒ`); both reject ASCII `g`.
Venv at `~/.local/share/phonicsfarm-tts/venv` (Python 3.12, CPU torch).

Nothing is wired into the game. No commit, no push.

## Superseded — Kokoro route (2026-09-20 a)

The user ruled out Azure: giving Microsoft a credit card is non-negotiable.
Do not re-propose Azure, and do not re-propose edge-tts (it cannot take
`<phoneme>`, so it says letter NAMES — the blocker recorded in the previous
handoff below).

Chosen route: **Kokoro-82M (`hexgrad/Kokoro-82M`), Apache-2.0, local CPU.**
It accepts a raw IPA string via `KPipeline.generate_from_tokens`, which is the
exact capability Azure SSML `<phoneme>` provided and edge-tts lacked. Apache-2.0
covers model and voices, so clips can ship inside a distributed Godot game —
cleaner than the edge-tts licensing question. Maisie is not available by this
route; the 8 British Kokoro voices are the substitute and the user picks by ear.

Environment: `/home/milo/.local/share/phonicsfarm-tts/venv` (uv, Python 3.12,
CPU-only torch, 1.2 GB). Deliberately NOT the system Python (3.14, which kokoro
does not support) and NOT GPU torch (avoids VRAM contention with ComfyUI).
The venv lives outside the repo so Godot does not try to import it.

`tools/generate_phonemes.py` replaces the Azure-specific
`tools/prepare_phoneme_review.py`, which is retained, unused, for reference.
The new script keeps the prepared comparison workflow: generate, user chooses,
then integrate. All approvals remain `pending_user_review`.

### Generated and awaiting the user's ear

- Stage 1, `~/Desktop/PhonicsFarm Sound Review/voice-probe/index.html`:
  56 clips, all 8 British voices x b, g, m, a, s. User names a voice.
- Stage 2, `~/Desktop/PhonicsFarm Sound Review/index.html`:
  33 clips in `bf_emma` — 26 letters, with b/c/d/g/k/p/t rendered both without
  and with a schwa. Per the user's standing instruction, neither is preferred
  automatically; a schwa is acceptable if it is clearer.

Once the user names a voice: `--voice <name> --force` re-renders the batch in
about a minute. Only then wire approved clips into the game.

### Phoneme table — corrected against ground truth

The Azure table was wrong in three places. Phonemes are now derived from
Kokoro's own British G2P, not guessed:

- **ASCII `g` is not in Kokoro's vocab** (needs U+0261 SCRIPT G), and unknown
  symbols are dropped SILENTLY — that clip would have been vowel-only with no
  error. `--check` validates the whole table against the vocab and now guards
  this. Run it after any table edit.
- British TRAP is `a` (U+0061), not `æ`.
- `j` is the single character `ʤ` (U+02A4).

c and k render identically (both /k/); that is correct, not a duplicate bug.
q=/kw/ and x=/ks/ remain reviewable choices as before.

### Checks actually run

`--check` passes: all 26 phonemes plus schwa and stress are in the vocab.
All 89 clips verified programmatically as well-formed 24 kHz 16-bit mono PCM
WAV, none silent, none clipped, every clip carrying >=0.15 s of audio above the
noise floor. Post-processing trims Kokoro's ~200 ms of leading silence,
peak-normalizes to -1 dBFS, and re-pads 30 ms head / 120 ms tail so stop
releases are not clipped.

**Pronunciation is unverified — the assistant cannot hear the clips.** Labels
are synthesis targets, not results. No Godot test was run; this is tooling and
asset generation only, nothing wired into the game. No commit, no push.
Repository changes: this handoff plus untracked `tools/`. Desktop review files
remain outside Git.

## Previous handoff — 2026-09-19 (superseded above)

## Paused for tomorrow morning — user choosing the TTS route

Latest instruction (2026-09-19): save memory and pause. The user is consulting
CC (Claude Code) on avoiding an Azure account and sorting the sound pipeline.
They may drop Maisie and use one of their existing local TTS models instead.
Resume when the user returns, expected tomorrow morning (2026-09-20), with their
chosen route. Do not require Azure setup, install/select a different model,
generate audio, or wire sounds into the game while this decision is pending.
No scheduled/background work has been set up.

Next session: read this handoff and inspect any changes made by the user or CC.
Use the user's chosen model/voice and local command or endpoint, adapting the
review generator as needed. The existing script is Azure-specific scaffolding,
not a commitment to that provider; the desktop review page and SSML still say
Maisie and will need updating if the voice changes. Preserve the comparison
workflow: generate review clips, let the user choose/approve, then integrate.
Keep both a clean/minimal-schwa attempt and a with-schwa attempt for stop
consonants. The user accepts and may prefer a schwa if it improves clarity.

Memory-save task changed only PROGRESS.md. Verified with `git diff --check`;
no generation, runtime tests, app edits, commit, or push. Existing uncommitted
state is PROGRESS.md plus the untracked tools/ generator. Desktop review files
remain outside the repository. No audio has been generated or approved.

## Prepared work — CVC Land sound review

The user names the existing clearing CVC Land and intends future Lands in all
four directions. Before game changes, generate phonics clips for user review.
Maisie (`en-GB-MaisieNeural`) was the initial voice; the provider and voice are
now undecided, as noted above. A short schwa after stop consonants is acceptable
and may be preferred for clarity. Let the user compare and choose; do not impose
a clean-stop preference. Use hard c/g, unvoiced s, consonant y, short UK vowels.
Proposed q=/kw/ and x=/ks/ remain reviewable choices.

Prepared `tools/prepare_phoneme_review.py` and the desktop folder
`/home/milo/Desktop/PhonicsFarm Sound Review/` with README, listening index,
manifest, and exact SSML requests. There are 33 candidates: two versions for
b/c/d/g/k/p/t (without requested schwa and with requested schwa), one for every
other letter. Labels are synthesis targets, not verified pronunciations. The
generator preserves existing clips, validates WAV structure, verifies Maisie's
regional availability, and keeps all approvals pending. Output is 24 kHz,
16-bit mono PCM WAV. No runtime assets have been added.

Earlier Azure route: no Speech credentials were available. The generator accepts
SPEECH_KEY and SPEECH_REGION via environment or private JSON passed with
--credentials. This setup is optional now, pending the user's provider decision.
No actual audio generated, no Azure calls made, and no pronunciation evaluated.
After the user supplies their chosen sound pipeline, start with the b comparison
to establish whether the voice is suitable, then prepare the remaining batch.
User approval of clips is required before wiring audio into the game.

Later requested behavior: every successful letter pickup or put-down anywhere
plays its sound. A lever screen-left of the three pedestals, activated by Chuck,
plays occupied pedestal letters sequentially left-to-right. These features and
the CVC Land scene changes have NOT been implemented. Other Lands come later.

Checks run: offline request generation; 33 unique well-formed SSML candidates;
specified pronunciation targets; missing-credential failure without WAV output;
WAV-format validation and manifest/listening-page rendering using temporary
synthetic test data outside the review folder. All passed. No Godot tests needed
for this tooling-only change; live Azure behavior is untested. Git already had
the desktop-guide PROGRESS.md update; it is preserved. This task adds tools/ and
updates this handoff. Desktop files are outside Git. No commit or push.

## Documentation task — desktop editing guide

Created `/home/milo/Desktop/PhonicsFarm-LLM-Edit-Instructions.md` at the user's
request. It explains play-space vocabulary, screen directions and local-coordinate
caveats, asset/scene locations, instance versus shared-asset edits, and reusable
prompts with practical acceptance checks. Facts were checked against README.md,
this handoff, and the current main, river, player, pedestal, and camera files.
No application code or assets changed; no runtime tests were needed or run for
this documentation task. The desktop guide is outside the project repository.
Git was clean before this task; only this PROGRESS.md update changes the repository.
No commit or push was requested or performed. Existing gameplay/device limitations
below remain unchanged.

## Current state

Playable Godot 4.5.2 prototype in /home/milo/vibecodeprojects/phonicsfarm.
The user authorized saving this working state and handoff together in the commit
"Fix clearing layout, river crossing, and Chuck controls". Find its hash with
`git log -1 --oneline` immediately after this handoff. The earlier recovery point
is 7d5cb98 ("Phonics Farm checkpoint before Qwen changes").
The user added kenney_nature-kit themselves; the source pack is included in this
checkpoint alongside the selected runtime GLBs. Do not reset or overwrite later
changes. No remote push or deployment was requested.

Latest authorized work: fix the river/bridge, remove invisible barriers between
trees, keep every block on dry land, double Chuck's walking speed, and put Pick/Put
beside the joystick. Earlier requests authorized a doubled board and closer
following camera. These requests supersede the original stationary-camera scope.

## Implemented layout and behavior

- Board is now a coherent 34×34 square (twice the original 17×17 width/depth).
  Environment and Blocks have 45° Y rotation: local +Z is screen-south, +X right.
- Main scene: northern ground mesh ends at local Z=4, southern ground starts at
  Z=8; river tiles fill the gap. Floor collision remains continuous at Y=0.
- Perimeter walls at ±16.75; old internal walls/gate and enormous outer board
  removed. Tree trunks remain solid, gaps between trunks are traversable.
- River center (0,0,6) in Environment space. Native Kenney 3D river tiles supply
  shaped banks and recessed water. A complete wooden bridge crosses north/south.
  Water barriers prevent wading; smooth collision ramps and rails match the bridge.
- 26 lowercase blocks in alphabetic order, local X=-14.375…14.375, Z=12,
  spacing 1.15. All are dry and inside the outer boundary. Front trees no longer
  obscure the row.
- Chuck: walk_speed=6.4 (previously 3.2), acceleration=32 (previously 16),
  preserving roughly the same acceleration time. Walking only.
- Camera follows Chuck at offset (16,10.55,16), fixed pitch -25°, yaw 45°.
  Orthographic size max(18,25/aspect). Whole board need not fit simultaneously.
- Pick/Put center is 160 logical pixels to the right of the joystick center.
  Their hit regions do not overlap; both remain at the lower left.
- Pickup/carry/drop and all three pedestals retain the existing interaction system.
  The character is called Chuck by the user; the scene node remains Player.

## Files and assets

- scenes/main.tscn: level geometry and instance placements.
- environment/river.tscn: reusable river and bridge with collision ramps/rails.
- environment/river_tile.tscn: inherited GLB tile with coordinated materials.
- assets/kenney/nature/: selected ground_riverStraight.glb, bridge_wood.glb, CC0 license.
- kenney_nature-kit/.gdignore excludes the intact source pack from import scans.
  Contrary to an earlier assistant report, this pack DOES contain 3D river models.
- environment/fixed_camera.gd: follow camera (historical filename retained).
- player/player.gd and ui/touch_controls.gd: walking speed and control placement.
- tests/smoke.gd: original interaction/input regression suite, updated approach
  positions for the row orientation. Tests must approach perpendicular to the row
  so they don't inadvertently select a neighboring letter.
- tests/layout.gd: walks the bridge both directions, fetches/returns a letter,
  checks every letter's pickup/dry location, camera following, speed, river
  barriers, tree gap traversal, and outer boundary.
- tests/capture.gd: rendered screenshots, supports --river and --overview.

## Verification

Godot editor import passed. Both smoke.gd and layout.gd report zero failures.
Rendered river and whole-board screenshots inspected with Compatibility renderer.
The layout test uses actual walking across the bridge; a bridge-node existence
check alone is insufficient. Test simulated keyboard/gamepad/multitouch remains
distinct from physical device testing.

Run from project directory:
```sh
/home/milo/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64 --headless --path . --script res://tests/smoke.gd
/home/milo/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64 --headless --path . --script res://tests/layout.gd
/home/milo/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64 --path . --script res://tests/capture.gd -- --river
```

The installed Godot binary exists even though it is not named godot on PATH.
F5 plays and F8 stops in the editor. Capture needs a real rendered window;
--headless cannot produce a screenshot.

## Next session: Claude Code or OpenCode/Qwen

Start in /home/milo/vibecodeprojects/phonicsfarm. Read AGENTS.md, this note, and
README.md, then run `git status --short` and inspect any existing diff. The requested
repairs are complete; await the user's next task rather than extending the game.
Use the full Godot binary path below/above; absence of `godot` on PATH does not mean
the engine is missing. Keep tasks narrowly scoped. Update this note after changes,
recording what was actually tested and what remains unverified.

## Remaining limitations

Physical touch/controller devices and Web export remain untested. No export
templates or GitHub Pages deployment were added. Ground-drop logic expects Y=0;
on the bridge it may retain the held block when nearby deck/rail collisions prevent
a clear drop. Carry it to a dry bank to drop/place. No swimming/jumping was added.

Historical scope note: later requests implemented audio, the lever and short-word
recognition as described at the top. Scoring, menus and unrelated gameplay remain
outside the completed scope; await the user's next task.
The next agent should read README and inspect the current diff
before edits, then update this note with actual validation and outstanding issues.
