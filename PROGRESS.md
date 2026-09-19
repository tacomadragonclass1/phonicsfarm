# Session handoff — 2026-09-18

## Current status

Initial playable prototype implemented. The original requested scope is complete;
wait for the user's next task before extending gameplay. The last user request
before saving this note was how to open the project in Godot; launch instructions
were provided. No user playtest feedback has been received yet.

Project: `/home/milo/vibecodeprojects/phonicsfarm/`
Engine installed for this task: Godot 4.5.2 standard Linux binary (GDScript).

Open editor:

```sh
/home/milo/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64 --editor --path /home/milo/vibecodeprojects/phonicsfarm
```

F5 plays; F8 stops. Alternatively import this folder's `project.godot` through the
Godot Project Manager. The folder was not a Git repository when work began.

## Implemented

- One compact forest clearing, stationary orthographic camera at approximately
  40 degrees down / 45 degrees around Y, perimeter tree colliders and invisible walls.
- Mini Characters GLB with idle/walk animations, CharacterBody3D walking with
  acceleration/deceleration and camera-relative direction/facing.
- 26 lowercase a–z blocks placed around the clearing. One reusable AlphabetBlock
  scene, exported `letter` data, Fredoka labels on four sides and top, solid collision.
- One visible carried block, pickup/retrieval, clear-ground drops, exactly three
  pedestals with snap points and reciprocal occupant references.
- WASD/arrows; E/Space. Standard controller left stick/D-pad and primary action.
  Mouse/touch joystick and interaction button share the same Input Map using a
  virtual joypad device. Two simultaneous touches and focus-loss cleanup supported.
- Separate small scene/scripts, README, smoke/capture scripts, single-threaded Web
  export preset using Compatibility rendering. No backend or plugins.

## Assets / important decisions

Original Kenney packs were present. Runtime GLBs and required external
`Textures/colormap.png` files were copied to `assets/kenney/`. Original pack folders
have `.gdignore` files to avoid importing everything.

The isometric-blocks pack contains only 2D PNG/SVG art. Blocks therefore use native
BoxMeshes adapting its wood/frame style and #CB9762 palette, with cream face panels.
They are not imported Kenney 3D block models. Ground and pedestals also use primitives.
Trees/plants/character are the supplied Kenney models. Fredoka came from Google
Fonts, with its OFL included; weight 600 uses integer OpenType tag 2003265652.

Blocks use StaticBody3D, not free rigid-body simulation. Carrying reparents to
Player/Visual/CarryAnchor and disables block collision layers. Drops check overlaps
and obstructions; when surrounded the player keeps holding the block. Ground Y=0
is intentional. Pedestal occupancy is managed by `place()` / `remove_block()`.

See README.md for the full file map and implementation conventions.

## Verification at completion of implementation

- Godot editor import completed without errors.
- `tests/smoke.gd` passed with zero failures: all letters/three slots, all arrow
  bindings, screen-relative walking/stopping, pickup/carry/drop/retrieval, each
  pedestal's independent occupancy, touch/mouse/controller event bindings,
  simultaneous touch input, focus reset, mouse release outside the pad, preserving
  held keyboard input after touch release, actual touch pickup, blocked drops,
  Space drop, and tree/block/pedestal/boundary collision.
- Native Compatibility-renderer screenshots inspected, including close-up Fredoka
  lettering. Capture outputs were `/tmp/phonics-clearing.png` and
  `/tmp/phonics-close-up.png`; temporary files may not persist.
- These are the previous implementation test results, not a new test run at the
  time this handoff was saved. The project may have since been opened in the editor;
  preserve any user changes.

Run tests:

```sh
cd /home/milo/vibecodeprojects/phonicsfarm
/home/milo/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64 --headless --path . --script res://tests/smoke.gd
```

## Outstanding validation / next tasks

No known failing automated checks at implementation completion. Physical gamepad,
physical multitouch tablet, and browser export remain untested. Export templates
are not installed; no GitHub Pages deployment was performed. Portrait fits the
whole clearing but makes letters smaller; landscape is preferred for this prototype.

Suggested small OpenCode/Qwen3.8 or Claude Code tasks, not yet authorized or started:

1. Device testing with a real controller and multitouch tablet.
2. Install matching export templates and test Web export / GitHub Pages.
3. Adjust only tree/block placement after a readability playtest.
4. Tune existing touch controls for the target tablet viewport.
5. Refine pedestal visuals while retaining collider/origin/SnapPoint conventions.

## User scope to preserve

This is intentionally a small physical-interaction foundation. No scoring, levels,
menus, dialogue, titles, music/sounds, enemies, timers, achievements, phoneme/word/CVC
validation, inventory, jumping, sprinting, combat, or other gameplay systems were
requested. Do not add these unless the user explicitly expands the scope.
Favor straightforward, descriptive GDScript and reusable scenes so later work is
easy to hand to a smaller local model.
