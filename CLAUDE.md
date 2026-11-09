# Claude Code handoff

Read AGENTS.md for repository instructions, PROGRESS.md for current session
state and outstanding limitations, and README.md for architecture and test
commands before editing. Keep shared handoff updates in PROGRESS.md so Claude
Code, Codex, and OpenCode/Qwen use the same memory.

Start with **THE VILLAGE IS STANDING, and the world is one scene — 2026-11-09**
at the top of PROGRESS.md, then read `lookdev/DECISIONS.md`, which is the art
direction handoff. Each section ends with "WHAT IS NOT DONE", which is the
list to pick up from.

✅ The rebuild is committed and pushed to `origin/cvc-land-rebuild`. `main` is
still `184d356` and still what deploys, so nothing in it is live. Work on the
branch. ⛔ `deploy.yml` fires only on a push to `main`.

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

⛔⛔ That rule is RETIRED for the rebuild, by decision: *"I'm fine with the
letter S off camera. The player will go around the space to collect letters,
that's the fun of it."* The probe and the occlusion checks exist only to
serve it. Its replacement is REACHABILITY -- every letter must be pickable
from somewhere -- which `tests/cvc_land.gd` already implements.

⚠ `tests/village.gd` does NOT gate the deploy, despite what this file said
for weeks. It tests `village/phoneme_village.tscn`, which is UNTOUCHED, so
its terrace assertions still pass -- all six suites are green. It is a test
aimed at the scene being replaced, not a blocker. Rewrite it to test the
ROUTINE when the new village takes the round over.

Annette's two sentences are now **the owner's own recordings**, not TTS -- do not
re-render them. Only `wrong_chime.wav` is still synthesized and unheard.

`tools/build_phoneme_village.py` was a one-time scaffold.
`village/phoneme_village.tscn` is the SHIPPING village and is still the site
root, so do not regenerate it casually.

⛔ But it is NOT sacred, and an earlier version of this file implied it was.
The owner's words: *"I don't know how that got elevated to sacred... it was
my first foray into godot, and I fumbled my way through it."* The layout is
being replaced; the ROUTINE is what must survive. Treat hand-placed
coordinates in it as disposable and the gameplay contract as load-bearing.

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
tonemapper, the old camera and a Kenney mannequin for Chuck. Adopting the
assets means adopting a tonemapper with them.

The art pipeline lives in `art_src/` (Blender 5 headless, run it with ABSOLUTE
paths -- a relative path doubles when run from inside `art_src/explore`).
`tools/build_foundation_village.py` generates the preview village and is safe
to re-run; it applies the engine's own occlusion rule so no prop can land on a
sight-line. `tools/check_foundation_village.gd` enforces that.

⛔ Do not push, regenerate voices or expand gameplay on resume. Pushing
`main` DEPLOYS -- `deploy.yml` fires on push and publishes both builds.

## The rebuild (2026-11-05/06)

The art direction is settled: patina + an ink outline + a low orthographic
camera. `storybook/painted_surface.gd` is what applies it -- **a scene
without that node renders raw StandardMaterial3D and looks exactly like the
asset pack the whole pass was spent escaping.** The first /preview/ export
shipped that way and only a screenshot caught it, so `tests/cvc_land.gd`
checks it now.

`scenes/cvc_land.tscn` is GENERATED by `tools/build_cvc_land.py` and
`scenes/village_quarter.tscn` by `tools/build_village.py` -- edit a generator
or `art_src/explore/world_plan.py`, never a scene. ⛔ Two generators, two
files, one world: CVC Land INSTANCES the village quarter, because one script
rewriting the other's file would overwrite it. The plan has no bpy import on
purpose: the Blender sculpt and both Godot layouts read the same module,
which is what makes "the village sits on the hill" true by construction
rather than by hand.

⛔ A building's FACADE is its local +Z, not its forward. Modelled on Blender
-Y, which glTF sends to Godot +Z -- so a yaw built from the usual -Z forward
turns every shop around, and every test still passes. Check a screenshot,
zoomed.
