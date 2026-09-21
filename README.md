# Phonics Farm — physical interaction prototype

Godot **4.5.2**, GDScript, Compatibility renderer. Two clearings joined by a corridor,
one walking character, and 26 lowercase letter blocks in CVC Land and 23 in the village.

**CVC Land** (south) has the river, the bridge, the alphabet row, three pedestals and a
playback lever that checks short English words after sounding out the occupied blocks.

**Phoneme Village** (north) is a fetch game on three walkable levels: Annette names a
SOUND and Chuck finds the letter that makes it.

## Run

Import `project.godot` in Godot 4.5.2 or a compatible newer Godot 4 version and press
**F6** on `scenes/main.tscn`, or **F5** from anywhere. This machine's official binary:

```sh
/home/milo/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64 --path /home/milo/vibecodeprojects/phonicsfarm
```

## Controls

| Input | Walk | Pick up / put down |
| --- | --- | --- |
| Keyboard | WASD or arrow keys | E or Space |
| Standard controller | Left stick or D-pad | A / Cross / primary button |
| Touch | Lower-left pad | Pick / Put immediately to the pad's right |
| Mouse | Drag lower-left pad | Click Pick / Put |

Movement follows screen directions. Approach a block and interact to carry it.
Approach an empty pedestal while carrying and interact to snap it into place.
Interact near an occupied pedestal with empty hands to retrieve its block.
Otherwise, interacting while carrying places it on clear ground nearby. If every
nearby position is obstructed, it stays in your hands. Only one block can be carried.
The nearest reachable block wins when several are within range. Chuck walks at
6.4 units/second. Cross the central bridge to reach the dry alphabet row to the south.

Every successful pickup, ground drop, pedestal placement or retrieval plays the
block's phoneme. A new interaction replaces the previous sound to keep letters
clear. Failed interactions are silent. Sounds are bundled human recordings;
Maisie is deferred for the blocks. See `assets/audio/phonemes/README.md` for the
letter mapping and sources.

## Phoneme Village

Walk north out of CVC Land, through the gap in the trees and up the stone corridor.
Crossing into the village wakes Annette, who says *"Please find the letter that says"*
followed by one letter's sound. Her sentence is bundled speech; the phoneme itself is
the same human recording the block plays, so the child matches one sound against itself.

The village uses **23 letters, not 26**: k, q and x are left out so that every
question has exactly one right answer. `c.wav` and `k.wav` are the same recording
(both /k/), and q is /kw/ and x is /ks/ — two sounds blended, each opening on that
same /k/. CVC Land still carries the full 26; this only affects the fetch game.

Walk into Annette and she repeats just the sound, without her sentence. She stays
quiet if she is already speaking, so bumping her on the way in cannot cut the
question in half. She is not solid — Chuck cannot get wedged against her.

Pick up the letter she asked for and Chuck raises it over his head, it flashes gold and
white, then vanishes in a puff of smoke. Annette says *"Good job"* and waits six seconds
before asking for the next one. Pick up the wrong letter and you hear that letter's own
sound, a soft two-note chime, and the same question again — the block stays in your
hands to put down wherever you like. Nothing is lost and nothing buzzes.

When all the letters have been found the board refreshes: a fresh set of blocks is
scattered to **different** places and the alphabet starts over. Walking out of the
village pauses the round; walking back in asks the same letter again.

The village has three walkable levels — the clearing floor, a raised terrace reached by
a ramp on its south-west corner, and a lookout one level higher again. Each level is a
different shade of green and rimmed with boulders. Letters are scattered across all
three, so some have to be climbed for. Chuck cannot jump; every level change is a ramp.

CVC Land's own 26 blocks are never touched by a village round. The two games use
separate sets and can be left mid-play.

## CVC Land

The three pedestals are 2.38 units apart (30% closer than the original 3.4).
Approach the red-handled lever on their left and use E/Space, the controller
action button, or Pick / Put. It plays the occupied slots from left to right,
waiting for each clip to finish and skipping empty slots. Any one, two or three
slots can be filled; an empty row is silent. Pulling again restarts the sequence.
The lever also works while carrying a block. Pickup or placement interrupts
the sequence with that block's sound.

Pulling the lever sends out a golden pulse. Each sounding pedestal rises briefly
and its block's cream faces turn gold, with dark letters for contrast. The
pedestal returns to its exact resting height when that sound finishes. After the
whole sequence, a recognized English word keeps its blocks gold with a short
sparkle; other combinations return to their default colors. Removing a block
resets that block and rechecks the remaining letters. Placing a new block clears
the old result until the next lever pull. Empty slots are skipped for both
playback and recognition, so one- and two-letter words work too.

Recognition uses a bundled 870-word SCOWL subset for the current one-to-three
letter combinations, including British and American spellings. It is an offline
dictionary check, not a rule that every letter's usual phoneme must match the
word's pronunciation. Source, rebuild instructions and coverage limits are in
`assets/words/README.md`.

## Scene structure

```text
project.godot                 Input Map, rendering and window settings
scenes/main.tscn              Editable level: ground, both clearings, corridor, walls
player/player.tscn + .gd      CharacterBody3D, walking, animation, interaction/drop queries
alphabet_block/               Reusable AlphabetBlock scene and exported lowercase letter
audio/phoneme_audio.gd         Shared phoneme player (PhonemeAudio autoload)
assets/audio/phonemes/         26 local letter WAVs and source manifest
assets/words/                 Offline short-word dictionary and copyright notices
pedestal/                     Reusable Pedestal scene, occupant reference and SnapPoint
lever/                        Reusable animated lever, with ordered pedestal references
village/phoneme_village.tscn  Phoneme Village: terrain, props, spawn markers, trigger
village/phoneme_village.gd    The fetch round: prompts, judging, celebration, refresh
environment/kenney_props.gd  Softens the Nature Kit's metallic imported materials
assets/audio/voice/           Annette's two spoken lines and the wrong-answer chime
environment/tree.tscn        Kenney tree model with a simple trunk collider
environment/fixed_camera.gd  Follows Chuck, with fixed rotation and aspect-aware zoom
environment/river.tscn       Kenney river tiles, bridge, ramps and water barriers
environment/river_tile.tscn  Nature Kit tile with materials matching the clearing
ui/touch_controls.tscn + .gd  Minimal pointer controls feeding the existing Input Map
assets/kenney/                Selected original GLBs, their textures and CC0 licenses
assets/fonts/                 Fredoka variable font and SIL Open Font License
tests/smoke.gd                Physics and input integration checks
tests/layout.gd               Actual bridge traversal, fetch/return and tree-gap checks
tests/lever.gd                All eight slot occupancy patterns and playback sequencing
tests/feedback.gd             Sound-synced lift/color, word results and safe retrieval
tests/village.gd              Village round, wrong/right answers, ramps and board refresh
tests/capture.gd              Optional rendered screenshot check
export_presets.cfg            Single-threaded Web export preset
```

The supplied `kenney_*` directories remain intact. `.gdignore` files keep these
source archives out of Godot's import scan; the small set used at runtime is copied
into `assets/kenney/`, including each GLB's external `Textures/colormap.png`.

## Small implementation rules for handoff

- `AlphabetBlock.letter` is the only letter data; edit it in the inspector or set it
  before adding an instance. Five Label3D faces update together, including in the editor.
- Block origins sit at the bottom. The native cube is 0.8 units tall. Keep that origin
  and size when replacing its `Visual` child; pickup and snap positions rely on them.
- Carrying reparents the block beneath `Player/Visual/CarryAnchor` and disables its
  collision layers. A drop or placement restores collision. Blocks intentionally do
  not roll, bounce, stack, or use RigidBody3D simulation.
- `Pedestal.block` and `AlphabetBlock.pedestal` are reciprocal references. Use
  `place()` / `remove_block()` so both remain consistent. Each `SnapPoint` is the top
  surface. All slots accept every letter.
- Pedestal lift affects only visible meshes and block lettering. Physics bodies
  and SnapPoints stay fixed, keeping retrieval reliable even mid-animation.
  Face materials are duplicated per block so feedback cannot recolor neighbors.
- Physics layers: 1 environment, 2 player, 3 blocks, 4 pedestals. Ground drops use
  overlap and line checks. CVC Land is flat at Y = 0; Phoneme Village is not, so
  `Player.ground_height()` raycasts DOWN from just above Chuck's feet. Starting the ray
  above his head would let him drop a block onto whatever is boxing him in.
- `AlphabetBlock.home` is the container a dropped block returns to. It keeps the
  village's blocks out of CVC Land's `Blocks` node so a board refresh can free them.
- `AlphabetBlock.picked_up` is how the village judges an answer. Nothing in CVC Land
  connects to it.
- Phoneme Village's walkable geometry is native Godot boxes with hand-authored
  collision, like the ground and bridge. Imported GLBs carry no colliders, so every
  Kenney model in the village is decoration; the ramps and plateaus underneath are not.
- Touch uses virtual joypad device 100, with the same axis/button events already
  mapped to `move_left/right/up/down` and `interact`. It tracks two independent
  pointers, supports mouse drag, and clears input on focus loss. Player code has
  no touch-specific movement behavior.
- The camera follows Chuck at `pitch_degrees` down and `yaw_degrees` around Y,
  backed off by `distance`; it never turns with the character. All of those, plus
  `zoom` and `minimum_width`, are exported on `environment/fixed_camera.gd`, which
  derives BOTH the camera's position and its rotation — moving the camera node in
  the editor viewport will be overwritten. Current values: 18 degrees down, 30
  around, orthographic size max(13, 18/aspect).
- **Yaw 45 is the axis-aligned view**: at 45 the board's local +X is exactly
  screen-right and the river runs flat across the screen, but every box shows one
  face and the scene reads nearly top-down. The current 30 turns the board 15
  degrees on screen so boxes, cottages and the bridge each show two faces. Set
  `yaw_degrees` back to 45 to get the square-on framing back.
- Each clearing is 40×40. Environment and Blocks are rotated 45 degrees around Y;
  with the camera at yaw 45 that puts their local +Z at screen-south and local +X
  at screen-right, and at the current yaw 30 it is 15 degrees off that.
  Keep positions local
  when editing: river center Z=6, alphabet row Z=12, outer walls at ±16.75.
  There are no inner walls between trees, and **no wall between the two clearings** —
  a single boundary rings the whole world at x = +-20.25, z = +20.25 and z = -68.25.
  Only trunks, river barriers and that outer edge block movement. Bridge ramps allow
  crossing without jumping.
- The world is CVC Land (z -20..20), an 8-unit corridor, then Phoneme Village
  (z -28..-68) centred at z = -48. The grass mesh and the river run far past the
  boundary on every side so no edge is visible from the game camera.
- The font variation's integer key `2003265652` is the OpenType `wght` tag (600).

## Assets and placeholders

Trees/plants and characters are the supplied **Kenney Mini Forest / Mini Characters**
GLBs; walking and idle animations come from the character model. Annette is
`character-female-a` from the same pack. Phoneme Village's cottages are Mini Forest
`building-platform` + `building-structure` + `building-roof` stacked, and its props
(campfire, crops, fences, tents, boulders, flowers, path stones, obelisk) come from the
supplied **Kenney Nature Kit**. Nothing was downloaded; all four supplied packs were
already in the repository.

The Nature Kit's GLBs carry their colour in `baseColorFactor` but ship with
`metallicFactor: 1`, which reads dark and shiny under this project's flat lighting.
`environment/kenney_props.gd` on a container node duplicates and de-metallicizes every
material beneath it, which is what the river and bridge do by hand.

The supplied **Kenney Isometric Blocks** pack is **2D PNG/SVG artwork**, with no 3D
cube model. The blocks are native Godot BoxMeshes adapting its wood cube/frame style
and its `#CB9762` tan palette from `Vector/vector_complete.svg`, with cream inset
faces and real Fredoka Label3D text. They are not imported Kenney 3D models.
Ground and pedestals are deliberately simple native primitive geometry. To replace
them, edit their visual mesh children while retaining collision shapes and snap points.

The supplied Nature Kit includes 3D GLBs. Selected river and bridge models and the
CC0 license are copied into assets/kenney/nature. The original source pack stays
intact with a .gdignore to avoid importing thousands of unused assets. Water/bank
geometry comes from ground_riverStraight.glb; the crossing uses bridge_wood.glb.

Fredoka was obtained from [Google Fonts](https://github.com/google/fonts/tree/main/ofl/fredoka).
The font and asset licenses are included alongside the runtime assets. Kenney sources:
[Mini Forest](https://kenney.nl/assets/mini-forest),
[Mini Characters](https://kenney.nl/assets/mini-characters).

## Verification

```sh
# Set GODOT to your Godot 4 executable, or use the full path above.
GODOT=/home/milo/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64
"$GODOT" --headless --path . --editor --import
"$GODOT" --headless --path . --script res://tests/smoke.gd
"$GODOT" --headless --path . --script res://tests/layout.gd
"$GODOT" --headless --path . --script res://tests/lever.gd
"$GODOT" --headless --path . --script res://tests/feedback.gd
"$GODOT" --headless --path . --script res://tests/village.gd
"$GODOT" --path . --script res://tests/capture.gd
```

Run these from this project folder. The smoke suite injects actual keyboard,
controller, mouse and screen-touch events, checks carrying/placement/retrieval and
collision, and exits nonzero on failure. The capture script writes
`/tmp/phonics-clearing.png` then exits; `-- --close-up` captures block lettering.
Use `-- --river` for the normal follow-camera view at the bridge, or
`-- --overview` for a diagnostic view of the whole board. `-- --pedestals`
captures the lever and closer slots with example blocks. Captures require a
rendered window; do not pass --headless.
`-- --feedback` saves `/tmp/phonics-feedback-active.png` during the first lift
and `/tmp/phonics-feedback-word.png` after the completed word sparkles.
`-- --village` and `-- --village-close` capture Phoneme Village with a round scattered;
`-- --world` is a diagnostic view of both clearings and the corridor at once.

Native desktop rendering was inspected. A physical gamepad, physical multitouch
device, and browser export have **not** been tested. Input simulation is not a
substitute for those device checks. The closer follow camera shows part of the
board; moving Chuck reveals the rest. Landscape is preferred for the prototype.

## Web / GitHub Pages

**Push to `main` and the live game updates.** `.github/workflows/deploy.yml` installs
Godot 4.5.2, runs all five test suites, exports the Web preset and publishes it to
GitHub Pages. A failing suite stops the deploy, so a broken build cannot reach the
classroom — the previous version stays live. Nothing is built on your laptop, and the
work machine needs only a browser.

One-time setup on GitHub:

1. Create the repository (it must be **public** for Pages on a Free account).
2. `git remote add origin git@github.com:<you>/phonicsfarm.git && git push -u origin main`
3. **Settings → Pages → Build and deployment → Source: GitHub Actions.** Without this
   the workflow runs but has nowhere to publish.

The site then lives at `https://<you>.github.io/phonicsfarm/`. Watch a run under the
Actions tab; the first one takes a few minutes while it downloads Godot and the export
templates, and later runs reuse a cache.

### Why the preset looks the way it does

- `export_filter="all_resources"`. It was `"scenes"`, which follows only scene
  dependencies — every resource reached by a `preload()` in GDScript was left out. The
  exported game rendered but **every script failed to compile**: no audio, no
  movement, no lever, no village. Do not narrow this filter again.
- `thread_support=false`. Godot's threaded web build needs `SharedArrayBuffer`, which
  needs COOP/COEP headers that GitHub Pages cannot set. Single-threaded avoids that
  entirely.
- `.nojekyll` is written into the build so Pages serves files beginning with `_`.

### Exporting by hand

Only needed to test a build locally; `F5` in the editor is the normal way to play.
Install the 4.5.2 export templates through Godot's export-template manager, then:

```sh
GODOT=/home/milo/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64
"$GODOT" --headless --path . --export-release "Web" build/web/index.html
python3 -m http.server 8899 --directory build/web   # then open localhost:8899
```

Serve it over HTTP — opening `index.html` as a `file://` URL will not work.

### Verified in a browser

The exported build was loaded in Chrome from a local server: no console errors, and the
audio context reaches `running` at 48 kHz once a click or tap provides the user gesture
every browser requires before sound. On a touchscreen the first tap does that.

Browsers cache the 38 MB `index.wasm` after the first load. A physical gamepad and a
real multitouch device are still untested.

## Next small handoff tasks (not implemented)

1. **Listen to Annette.** `assets/audio/voice/` is `pending_user_review`; `bf_emma` was
   assumed because the phoneme review used it, and no voice was ever finally chosen.
2. Check this build with a real gamepad and multitouch tablet; record device-specific issues.
3. Export the existing Web preset and test it on a local static server and GitHub Pages.
4. Adjust only tree/block positions after a kindergarten readability playtest.
5. Tune existing joystick/button sizing for the target tablet's landscape viewport.
6. Refine pedestal visuals while preserving the scene origin, collider and SnapPoint.
