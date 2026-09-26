# Phonics Farm — physical interaction prototype

Godot **4.5.2**, GDScript, Compatibility renderer. Two clearings joined by a corridor,
one walking character, and 26 lowercase letter blocks in CVC Land and 23 in the village.
The world is lit for late golden hour: a low warm sun, long shadows and a cool blue
skylight filling the shade so a letter standing in shadow is still easy to read.

**CVC Land** (south) has the river, the bridge, two alphabet rows of 13, three pedestals
and a playback lever that checks short English words after sounding out the occupied
blocks.

**Phoneme Village** (north) is a fetch game on three walkable levels: Annette names a
SOUND and Chuck finds the letter that makes it.

## Run

Import `project.godot` in Godot 4.5.2 or a compatible newer Godot 4 version and press
**F6** on `scenes/main.tscn`, or **F5** from anywhere. This machine's official binary:

```sh
/home/milo/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64 --path /home/milo/vibecodeprojects/phonicsfarm
```

## Controls

**Picking a block up is not a button.** Chuck picks up any loose block he walks into.
Blocks resting on a pedestal are the exception: those are taken back with the action,
so crossing the pedestal row cannot undo the word he has just built.

| Input | Walk | Put down / lever |
| --- | --- | --- |
| Touch | One finger dragged in any direction, anywhere on screen | A second finger tapped anywhere |
| Mouse | Press and drag anywhere | Click without dragging |
| Keyboard | WASD or arrow keys | E or Space |
| Standard controller | Left stick or D-pad | A / Cross / primary button |

**There is nothing drawn on screen.** The whole viewport is the control surface. The
first finger down plants a walking stick wherever it lands and steers from there; the
anchor trails the finger so one long drag keeps steering instead of running out of
travel. A second finger tapped anywhere puts the carried block down. A single quick tap
that never moved does the same, so the lever can be pulled one-handed.

Movement follows screen directions. Walk into a block to carry it. Approach an empty
pedestal while carrying and act to snap it into place. Act next to an occupied pedestal
with empty hands to retrieve its block. Otherwise, acting while carrying places the
block on clear ground nearby. If every nearby position is obstructed, it stays in your
hands. Only one block can be carried. A block just put down is ignored until Chuck has
stepped away from it, or he would pick it straight back up. The nearest reachable block
wins when several are within range. Chuck walks at 6.4 units/second. Cross the central
bridge to reach the dry alphabet rows to the south.

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

**She shows where to look, twice over.** Whenever she asks, she turns to face the
letter she is asking for. Get one wrong and she walks four or five steps toward it
as well, so the clue gets stronger the longer the hunt goes on. Neither clue points
at the block outright, and she always stops well short of it — she must never end up
standing on the answer. She walks back to her post after every letter found, so she
cannot drift across the village.

Pick up the letter she asked for and Chuck raises it over his head, it flashes gold and
white, then vanishes in a puff of smoke. Annette says *"Good job"* and waits six seconds
before asking for the next one. Pick up the wrong letter and you hear that letter's own
sound, a soft two-note chime, and the same question again — the block stays in your
hands to put down wherever you like. Nothing is lost and nothing buzzes.

Putting a village block back down is **silent**, unlike CVC Land where every drop
sounds its letter. A sound stops whatever is already playing, and what was playing
was Annette repeating the question the child still needs to hear.

A small number in the very top-left corner counts the letters found so far. It
fades in only inside the village, and starts over when the board refreshes.

When all the letters have been found the board refreshes: a fresh set of blocks is
scattered to **different** places and the alphabet starts over. Walking out of the
village pauses the round; walking back in asks the same letter again.

The village is laid out, not scattered. Six identical cottages stand in an L around the
green -- three along the north rim facing south, three down the west side facing east,
all evenly spaced -- and a stone lane runs in front of both rows to meet the main path
from the south gate. The camp (tent and its fire) sits square on the east side. **No
letter is ever hidden behind a structure**: the camera is orthographic and never turns,
so "behind" is one fixed direction for the whole board, and `tests/village.gd` checks
every spawn point against the visuals of every building, boulder, prop and tree.
`tools/village_spawn_probe.gd` prints a fresh set of spawn positions that are standable,
block-sized and unobscured; run it if the buildings are ever moved, then paste the
result into `SpawnPoints`. It is an aid, not a build step -- the scene stays the source
of truth.

The village has three walkable levels — the clearing floor, a raised terrace reached by
a ramp on its south-west corner, and a lookout one level higher again. Each level is a
different shade of green and rimmed with boulders. Letters are scattered across all
three, so some have to be climbed for. Chuck cannot jump; every level change is a ramp.

CVC Land's own 26 blocks are never touched by a village round. The two games use
separate sets and can be left mid-play.

## CVC Land

The 26 letters stand in **two rows of 13**, a-m nearest the river and n-z behind them.
Columns are 1.9 apart and the rows 2.6 apart, so the 1.1-unit column gaps and the
1.8-unit lane between the rows both clear Chuck's 0.6-wide body: he can walk into the
grid, not just along its front. `tests/layout.gd` walks him through both gaps.

The three pedestals are 2.38 units apart (30% closer than the original 3.4).
Approach the red-handled lever on their left and use E/Space, the controller
action button, or a tap. It plays the occupied slots from left to right,
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
village/annette.gd            Annette: faces the letter, walks a few steps toward it
environment/kenney_props.gd  Softens the Nature Kit's metallic imported materials
assets/audio/voice/           Annette's two spoken lines and the wrong-answer chime
environment/tree.tscn        Kenney tree model with a simple trunk collider
environment/fixed_camera.gd  Follows Chuck, with fixed rotation and aspect-aware zoom
environment/river.tscn       Kenney river tiles, bridge, ramps and water barriers
environment/river_tile.tscn  Nature Kit tile with materials matching the clearing
ui/touch_controls.tscn + .gd  Invisible drag/tap pointer layer feeding the Input Map
ui/found_counter.tscn + .gd   Top-left count of letters found, village only
tools/village_spawn_probe.gd  One-off aid: prints unobscured village spawn positions
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
  connects to it. `AlphabetBlock.silent_drops` is the village's other hook: its
  blocks land without playing their letter, because that sound would cut off
  Annette's repeated question. Only `put_on_ground` is gated — a village block
  placed on a CVC pedestal still sounds.
- `PhonemeVillage.answered` fires AFTER the letter is appended to `found`, so a
  listener reading that array is not one letter behind. The counter depends on it.
- Annette's script works entirely in GLOBAL yaw. The village hangs off a
  45-degree-rotated `Environment` node, so mixing local and global rotation points
  her 45 degrees wide of the letter she means. She has no collider and no physics
  body: her walk raycasts down for footing and forward for cottages and trunks,
  both on layer 1.
- Phoneme Village's walkable geometry is native Godot boxes with hand-authored
  collision, like the ground and bridge. Imported GLBs carry no colliders, so every
  Kenney model in the village is decoration; the ramps and plateaus underneath are not.
- Touch uses virtual joypad device 100, with the same axis/button events already
  mapped to `move_left/right/up/down` and `interact`. Player code has no
  touch-specific movement behavior. The layer draws nothing, tracks the first
  pointer as the walking stick and treats every later one as an action tap, and
  clears input on focus loss. The action is a PULSE: Godot may not flush a
  synthesised event until the next frame, so it is held across two physics frames
  before being released, or the player's `is_action_just_pressed` poll misses it.
  A lost mouse-up (released outside the canvas, swallowed by the browser) would
  otherwise leave Chuck walking forever, so `_process` polls the real button state
  and lets go.
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
  when editing: river center Z=6, alphabet rows Z=11.2 and Z=13.8, outer walls at ±16.75.
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
(campfire, tents, boulders, flowers, mushrooms, path stones, obelisk) come from the
supplied **Kenney Nature Kit**. Nothing was downloaded; all four supplied packs were
already in the repository.

The village green was thinned on 2026-09-26 at Milo's request: the pumpkin patch
(pumpkins, dirt rows and its fence) is gone entirely, the campfire keeps 2 of its 3
fallen logs, and the leafy bushes are down from 7 to 2. All 20 flowers and all 7
mushroom clusters stay. `crop_pumpkin.glb`, `crops_dirtRow.glb` and
`fence_simple.glb` are still in `assets/kenney/nature/` but no scene uses them.

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
`-- --village`, `-- --village-close` and `-- --village-houses` capture Phoneme Village
with a round scattered -- the last one frames the cottage rows from the green;
`-- --world` is a diagnostic view of both clearings and the corridor at once.

Native desktop rendering was inspected, and the live build has since been played on
real hardware (see **Confirmed on real hardware** below). Input simulation is not a
substitute for a device check, so keep confirming anything new on the actual screen.
The closer follow camera shows part of the board; moving Chuck reveals the rest.
Landscape is preferred for the prototype.

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

Browsers cache the 38 MB `index.wasm` after the first load.

### Confirmed on real hardware

Milo played the **live GitHub Pages build** on 2026-09-25 and confirmed:

- the resident **Xbox controller** works;
- **sound works** on the real device;
- the **touch-screen controls work exactly as intended** -- drag anywhere to walk,
  a second finger taps to put the block down, walking into a block picks it up.

That closes the two longest-standing unknowns on this project: until then a physical
gamepad and a real multitouch device had only ever been *simulated* by `tests/smoke.gd`.
What is still untested is whether a **child** discovers the invisible drag control
without being told -- nothing on screen says "drag to walk".

## Next small handoff tasks (not implemented)

1. **Listen to Annette.** `assets/audio/voice/` is `pending_user_review`; `bf_emma` was
   assumed because the phoneme review used it, and no voice was ever finally chosen.
2. Adjust only tree/block positions after a kindergarten readability playtest.
3. Watch a child use the invisible controls. Nothing on screen says "drag to walk";
   if that turns out to need teaching, a one-off fading hint is the smallest fix.
   The controls themselves are confirmed working on the classroom screen.
4. Refine pedestal visuals while preserving the scene origin, collider and SnapPoint.
