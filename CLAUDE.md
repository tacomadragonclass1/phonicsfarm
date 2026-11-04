# Claude Code handoff

Read AGENTS.md for repository instructions, PROGRESS.md for current session
state and outstanding limitations, and README.md for architecture and test
commands before editing. Keep shared handoff updates in PROGRESS.md so Claude
Code, Codex, and OpenCode/Qwen use the same memory.

Start with **Four fixes: flat floor, village spread, village letters,
overcast light — 2026-11-03** at the top of PROGRESS.md. That section ends
with "What is NOT verified", which is the list to pick up from.
Implemented: CVC Land audio, lever, visual feedback, word recognition,
Phoneme Village, the 40x40-per-clearing field, the single outer boundary, the
camera/crop/prompt/Annette-touch fixes, and the 2026-09-25 pass (sunset light,
pitch-30 camera, two alphabet rows of 13, the laid-out village, and controls
with nothing drawn on screen).

Four things that look like bugs but are decisions: the board sits 15 degrees off
screen-axis because the camera yaw is 30 for a three-quarter view (45 is the
axis-aligned value); Phoneme Village uses 23 letters because k, q and x collide
with c by ear; the alphabet rows deliberately do NOT fit on screen, because the
user chose immersion over seeing every letter; and there is deliberately no
on-screen controller -- drag anywhere to walk, second finger taps to put down,
and walking into a loose block picks it up. All are explained in README and
PROGRESS. Older sections record superseded decisions; they are not pending
instructions.

`tools/village_spawn_probe.gd` regenerates Phoneme Village's spawn markers so no
letter is hidden behind a structure. Like `build_phoneme_village.py` it is an
aid, NOT a build step; the scene is the source of truth. `tests/village.gd`
enforces the no-hidden-letter rule on every run.

Annette's two sentences are now **the owner's own recordings**, not TTS -- do not
re-render them. Only `wrong_chime.wav` is still synthesized and unheard.

`tools/build_phoneme_village.py` was a one-time scaffold. `village/phoneme_village.tscn`
is the source of truth now and the user edits scenes in the editor; do not
regenerate it with `--force`.

The live build has been played on real hardware (Xbox controller, sound, and the
touch controls all confirmed 2026-09-25). Older PROGRESS sections saying a
gamepad or multitouch device is untested are superseded.

## The storybook art set (as of 2026-11-03)

There are now TWO builds. `scenes/main.tscn` is the classroom game and is the
site root; `scenes/foundation_preview.tscn` is the storybook art build that the
`/preview/` deploy boots. They have separate lighting and separately generated
villages, so reviewing the new art through `main.tscn` shows neither. Two
export presets exist for the same reason -- "Web" EXCLUDES the new art to keep
the classroom pck small, "WebPreview" includes it.

⛔ None of the art set is in the classroom game yet. `main.tscn` has no
tonemapper, and `tests/village.gd` still holds the old terrace ramp
coordinates. Adopting the assets means adopting a tonemapper with them.

The art pipeline lives in `art_src/` (Blender 5 headless, run it with ABSOLUTE
paths -- a relative path doubles when run from inside `art_src/explore`).
`tools/build_foundation_village.py` generates the preview village and is safe
to re-run; it applies the engine's own occlusion rule so no prop can land on a
sight-line. `tools/check_foundation_village.gd` enforces that.

The tree is committed and pushed. Await the user's next task; do not push,
regenerate voices or expand gameplay on resume.
