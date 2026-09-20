# Session handoff — 2026-09-19

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

Keep scope small: no phonics/word validation, scoring, menus, audio, or other
gameplay systems. The next agent should read README and inspect the current diff
before edits, then update this note with actual validation and outstanding issues.
