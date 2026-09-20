# Phonics Farm — physical interaction prototype

Godot **4.5.2**, GDScript, Compatibility renderer. One forest clearing, 26 lowercase
letter blocks, one walking character, exactly three pedestals. No phonics rules or
other gameplay systems.

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

## Scene structure

```text
project.godot                 Input Map, rendering and window settings
scenes/main.tscn              Editable level: ground, trees, walls, 26 blocks, 3 slots
player/player.tscn + .gd      CharacterBody3D, walking, animation, interaction/drop queries
alphabet_block/               Reusable AlphabetBlock scene and exported lowercase letter
pedestal/                     Reusable Pedestal scene, occupant reference and SnapPoint
environment/tree.tscn        Kenney tree model with a simple trunk collider
environment/fixed_camera.gd  Follows Chuck, with fixed rotation and aspect-aware zoom
environment/river.tscn       Kenney river tiles, bridge, ramps and water barriers
environment/river_tile.tscn  Nature Kit tile with materials matching the clearing
ui/touch_controls.tscn + .gd  Minimal pointer controls feeding the existing Input Map
assets/kenney/                Selected original GLBs, their textures and CC0 licenses
assets/fonts/                 Fredoka variable font and SIL Open Font License
tests/smoke.gd                Physics and input integration checks
tests/layout.gd               Actual bridge traversal, fetch/return and tree-gap checks
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
- Physics layers: 1 environment, 2 player, 3 blocks, 4 pedestals. Ground drops use
  overlap and line checks. This deliberately flat level assumes ground Y = 0.
- Touch uses virtual joypad device 100, with the same axis/button events already
  mapped to `move_left/right/up/down` and `interact`. It tracks two independent
  pointers, supports mouse drag, and clears input on focus loss. Player code has
  no touch-specific movement behavior.
- The camera follows Chuck at 25 degrees downward and 45 degrees around Y.
  Its orthographic size is max(18, 25/aspect); it never turns with the character.
- The board is 34×34. Environment and Blocks are rotated 45 degrees around Y so
  their local +Z is screen-south and local +X is screen-right. Keep positions local
  when editing: river center Z=6, alphabet row Z=12, outer walls at ±16.75.
  There are no inner walls between trees. Only trunks, river barriers, and the
  outer edge block movement. Bridge ramps allow crossing without jumping.
- The font variation's integer key `2003265652` is the OpenType `wght` tag (600).

## Assets and placeholders

Trees/plants and character are the supplied **Kenney Mini Forest / Mini Characters**
GLBs; walking and idle animations come from the character model. No replacement
character or forest assets were downloaded.

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
"$GODOT" --path . --script res://tests/capture.gd
```

Run these from this project folder. The smoke suite injects actual keyboard,
controller, mouse and screen-touch events, checks carrying/placement/retrieval and
collision, and exits nonzero on failure. The capture script writes
`/tmp/phonics-clearing.png` then exits; `-- --close-up` captures block lettering.
Use `-- --river` for the normal follow-camera view at the bridge, or
`-- --overview` for a diagnostic view of the whole board. Captures require a
rendered window; do not pass --headless.

Native desktop rendering was inspected. A physical gamepad, physical multitouch
device, and browser export have **not** been tested. Input simulation is not a
substitute for those device checks. The closer follow camera shows part of the
board; moving Chuck reveals the rest. Landscape is preferred for the prototype.

## Web / GitHub Pages

The Web preset uses Compatibility rendering and disables threads and extensions,
following the [Godot web export guidance](https://docs.godotengine.org/en/4.5/tutorials/export/exporting_for_web.html).
All runtime assets are local. There is no backend, network API or database.

Install matching **4.5.2 export templates** through Godot's export-template manager,
create `build/web/`, then export the `Web` preset to `build/web/index.html`. Publish
all files in that directory together to GitHub Pages without renaming them. Serve
locally over HTTP to test; don't open the HTML via `file://`. Export templates are
not installed and no deployment has been performed. Browsers require WebGL 2;
a controller may need its first button press before the browser recognizes it.

## Next small handoff tasks (not implemented)

1. Check this build with a real gamepad and multitouch tablet; record device-specific issues.
2. Export the existing Web preset and test it on a local static server and GitHub Pages.
3. Adjust only tree/block positions after a kindergarten readability playtest.
4. Tune existing joystick/button sizing for the target tablet's landscape viewport.
5. Refine pedestal visuals while preserving the scene origin, collider and SnapPoint.
