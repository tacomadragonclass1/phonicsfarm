# A WORLD THREE TIMES THE SIZE, a river, and things you cannot walk through — 2026-11-09

👉 **START HERE.** `lookdev/DECISIONS.md` is still the art-direction handoff
and is unchanged. This section is the state of the build.

## The world

| | old | new |
|---|---|---|
| ground | 40 x 88 m, 3,520 m2 | **68 x 178 m, 12,104 m2 (3.44x)** |
| vowel zone to the green | 19.5 m | **47.5 m** |
| village neighbours, centre to centre | ~5.2 m (touching) | **9.37 m** |
| pedestals to the south boundary | 20 m to a bare edge | **32 m to a river** |
| ground grid | 78,792 tris @ step 0.30 | 76,956 tris @ step 0.56 |

⛔⛔ **THE STEP HAS TO GROW WITH THE WORLD.** The ground is a heightfield, so
triangles scale with AREA: tripling it at step 0.30 would be ~264,000 against
a 90,000 budget, and a proportionally bigger baked collision shape for a
single-threaded web build. 0.56 is 0.30 x sqrt(3.44) and holds the count
flat. ⛔ The texture had to go 2048 -> 4096 for the same reason: at 2048 the
new ground carries ~12.5 texels/m, which is the density this project already
REJECTED once as worse than the blur it was fixing.

⭐ The village arc is now **generated from one number** (`VILLAGE_ARC_R`)
rather than five typed coordinate pairs, so breathing room is a dial.

## ⛔⛔ THE RIVER, and why the far bank is shaped the way it is

The south boundary is a river with a **real wall** on its north lip, not a
steep bank. Relying on steepness makes the edge of the world a side effect of
the character controller's floor angle -- an accidental rule that stops being
true the next time anybody touches movement.

⭐⭐ **THE TWO BANKS ARE DIFFERENT, AND THE FAR ONE IS DERIVED FROM THE CAMERA
ANGLE.** The ground is an open heightfield, so any slope tilting away from the
camera more steeply than the camera's own pitch shows the viewer its
UNDERSIDE -- which renders as a near-black band. First cut: a 44-degree far
bank, a black strip under the water. Softened to 30: still black. The fix is
arithmetic, not taste. A smoothstep bank rising 2.6 m over L peaks at
1.5 x 2.6 / L, and the game camera is pitch 16, so L must exceed
1.5 x 2.6 / tan(16) = 13.6 m. `RIVER_BANK_FAR = 15.0` gives 14.6 degrees and
the band is gone.

⛔ **THERE IS NO RIM ON THE SOUTH EDGE**, for the same reason: a shoulder that
rises toward the viewer can only ever be backfaces. `_edge_in` is built from
THREE edges. Tapering a four-edge rim was tried first and is worse -- the
taper adds its own gradient and the shore came out at 24 degrees.

👉 This also killed the horizon defect from the last pass. `START` moved from
away -3.4 to -11.0 and the south edge is 41 m further out, so the camera no
longer frames empty sky. Confirmed in the exported build in a browser.

## Collision: an asset knows its own

`tools/measure_footprints.gd` reads the real meshes; `tools/add_colliders.py`
writes a body into each wrapper from that table. Instancing a thing is now
enough to make it solid, here or in any other scene.

⛔ The old hand-me-down village table was **stale**: it called the bakery
2.90 m deep where the mesh measures 3.68, so Chuck could walk into the gable.
That table is deleted, not corrected.

⭐⭐ **THE REACHABILITY TEST EARNED ITS KEEP.** Making the landmarks solid
broke the fetch of `l`: `stack_yard` lays its columns ALONG the
zone-to-pedestal axis, so the yard reaches 2.7 m back on its own and the
woodshed's hull overlapped the last row of blocks. The 3.3 m standoff had
always been too short; nothing noticed while landmarks had no collision.
`STANDOFF` is now derived per landmark from the yard reach plus the measured
half-footprint.

⛔ Deliberately NOT solid, each for a reason: blossom and mushrooms (ankle
height -- stopping a five-year-old dead on a mushroom is worse), Annette (she
is TOUCHED to replay the prompt), bunting (overhead). Trees collide on the
TRUNK, the windmill on its TOWER -- the measured box is the canopy and the
sails, and a 1.3 m radius would stop Chuck in open air.

## ⛔⛔ The rim was climbable, and nobody could have known

It rises 6 m over 12 m, which smoothsteps to 36.9 degrees, and `chuck.tscn`
sets no `floor_max_angle` so he uses Godot's default 45. Chuck could walk up
the wooded shoulder and off the mesh. It had never mattered because until
this pass nobody could get that far from the pedestals. There are now walls
just inside the crest on the other three edges, using the same mechanism as
the river. 👉 This was NOT asked for -- it is the same bug as the river on
the other three sides, and it is flagged here rather than buried.

## What was checked

Six suites green. The river test is **driven, not teleported** -- it presses
the real movement action and lets `move_and_slide` decide, because the thing
under test IS the collision; every other check in that file teleports, which
goes straight through colliders. ⭐ It was verified to FAIL with the wall
disabled (Chuck reaches -37.2, ten metres into the water) before being
trusted.

The preview was EXPORTED and LOADED IN A BROWSER. Preview pck is 50.0 MB, up
from 39.9. The classroom build is untouched by all of this -- `main.tscn` is
not involved and the `Web` preset excludes every asset here.

## 👉 WHAT IS NOT DONE

1. **Nothing was driven beyond the river test.** CDP keyboard events do not
   reach the Godot web canvas on this box, so the long walk to the village,
   the touch controls and the lever are still unverified in the export.
2. **The village round still does not exist** -- no letters, no Annette
   script. She is furniture.
3. **Adoption.** `scenes/main.tscn` is still the classroom game.
4. **The workshop still shows the camera a blank gable** (west end of the
   arc, green to its east).
5. `lane_stone.tscn` and `wall_run.tscn` are still built and unused.
6. The troll is still **PARKED**.

# THE VILLAGE IS STANDING, and the world is one scene — 2026-11-09

👉 **START HERE.** `lookdev/DECISIONS.md` is still the design handoff and is
unchanged. This section is the state of the build.

✅ The rebuild is **committed and pushed** to `origin/cvc-land-rebuild`
(`6fae2e1` plus this pass). `main` is still `184d356` and still what deploys,
so nothing here is live. ⛔ `deploy.yml` fires only on a push to `main` --
pushing this branch cannot ship it, and that is checked, not assumed.

## What was done

**The village half of the world is no longer empty ground.** It turned out to
be a placement job, not an art job: all five shops, the windmill, Annette and
every prop were already modelled in `art_src/explore/village.py`, already
exported to `assets/storybook/village/*.glb`, and already wrapped as scenes in
`storybook/village/*.tscn`. The ground already spanned away -20..68 with the
green flat and the mill hill sculpted in. Nothing placed any of it.

| | |
|---|---|
| `tools/build_village.py` | NEW. Generates the village quarter from the plan |
| `scenes/village_quarter.tscn` | GENERATED -- do not hand-edit |
| `tools/build_cvc_land.py` | now instances the quarter into the world |

⭐ **TWO GENERATORS, TWO FILES, ONE WORLD.** `build_cvc_land.py` rewrites
`cvc_land.tscn` wholesale, so a second script writing that same file would
overwrite it. The village emits its own scene and CVC Land instances it:
one owner per generated file, and the village can be re-laid without
touching the clearing. It is instanced BEFORE the player so `PaintedSurface`
-- which runs last and walks every sibling -- reaches into it.

## ⛔ The facade is the asset's local +Z, not its forward

Every building is modelled with its door and windows on the Blender **-Y**
face (`front = -1.26` and friends in `village.py`), and the glTF conversion
sends Blender -Y to Godot **+Z**. So aiming a shop at the green means aiming
its BACK vector there. A yaw derived from the conventional -Z forward turns
all five shops around to face the hedge, and every suite still passes.
`facade_yaw()` carries the derivation.

⭐ Verified by SCREENSHOT, not by reasoning -- `lookdev/shoot.gd ... landwide`,
then cropped and upscaled before judging. The wide plate is too small to read
a shopfront in, which is exactly how an earlier pass mis-called the ink twice.

## ⛔⛔ NO MILL MOUND

`storybook/village/mill_mound.tscn` and `assets/storybook/collision/mill_mound.res`
belong to the OLD foundation village, where the mill stood on a 12 m cone set
down on flat ground -- the approach that was rejected, because "a hill you set
down is not a hill". `world_plan.mill_hill` sculpts the rise INTO the terrain
now. Instancing the mound would stack a second hill on the first. It is still
on disk and still baked by `tools/bake_collision.gd`; leave it alone.

## What is in the quarter

Five shops on the arc, each facing the green, each with a **box collider**
sized from the measured footprints (⛔ a StaticBody3D with no CollisionShape
child is not collision -- the first generated village had six of them and
Chuck walked through every building). The windmill on the crown at the plan's
own `MILL_H`, not a guessed height. Well, two benches, a fingerpost, two
planters and bunting on the green, the ring positions **searched** rather than
typed because the lane skirts the green. 34 pieces of scenery, kept off the
lane, the cart track, the pads, the open green, the mill crown and the
reserved `BONUS` site.

Six suites green with the village in: `smoke layout lever feedback village
cvc_land`, 0 failures each.

## ✅ The export was LOADED, not just built — 2026-11-09

⛔ "Passing locally proves NOTHING about the export" has cost this project a
shipped-broken build before, so both presets were exported and **opened in a
browser** off `build/web/serve.py` on loopback (a secure context, which Godot
web requires).

  * **Classroom build (`Web` preset): intact.** Boots and renders the
    shipping game exactly as before -- PLAY lever, pedestals, river, bridge,
    alphabet. `scenes/main.tscn` is byte-identical between `main` and this
    branch, and the pck is 6.11 MB against main's 6.98 MB, so it got
    SMALLER, not bigger.
  * **Preview build (`WebPreview`): boots and runs** the rebuilt world. The
    art direction IS in the export -- grade, patina and the ink hull all
    present. (Zoom before judging that: at game zoom a 3.4 px clip-space
    line is genuinely thin, and it reads as "no outline" in a fit-to-window
    screenshot.)

⛔⛔ **`scenes/village_quarter.tscn` was leaking into the CLASSROOM build.**
The `Web` preset excludes `scenes/cvc_land.tscn` by name, and the new scene
was not on that list while `export_filter` is `all_resources`. Now excluded.
Any further generated scene needs the same line.

## ⛔⛔ NEW: the world's outer boundary is VISIBLE from the game camera

Standing at `START`, the built game shows the clearing, then the rim, then
**past the rim into empty sky** across roughly the bottom third of the frame.
It is not an aspect-ratio artifact (`fit_clearing()` resolves to size 8.2 at
both 1.60 and 1.96) and it is not the art direction.

⭐⭐ **NO LOOKDEV PLATE CAN SHOW THIS, which is why it survived.**
`lookdev/shoot.gd` calls `camera.set_process(false)` and places the camera
itself at a fixed target, so every plate -- `land` included -- frames a point
near the pedestals. The GAME camera is `fixed_camera.gd`, which centres on
the PLAYER every frame, and `START` sits about 3.9 m nearer the near edge.
This is the same shape of mistake DECISIONS.md already lists four of:
a diagnostic that cannot see the thing it is diagnosing.

The plan itself is fine -- the rim rises as designed, measured along the
away axis from `START`:

    away -10: 0.000   -14: 1.083   -18: 3.422   -20: 3.848

So the fix is framing, not terrain. Candidates, cheapest first: move `START`
deeper in; raise `RIM_H`; or pull the camera's `zoom` in. ⛔ The camera is
SETTLED by decision -- changing `zoom` reopens an art-direction call, so
`START` is the honest first try.

⚠ Nothing was DRIVEN. Keyboard events dispatched over CDP do not reach the
Godot web canvas on this box, so Chuck never moved. Walking the world, the
touch controls and the lever all remain unverified in the export.

## 👉 WHAT IS NOT DONE — pick up here

1. **The workshop shows the camera a blank gable.** It sits at the west end of
   the arc with the green to its east, so "face the green" turns its front
   away from a camera that never moves. The rule is right for the other four.
   This one is a taste call: leave it, or give the end shops a yaw that splits
   the difference between the green and the viewer.
2. **`lane_stone.tscn` and `wall_run.tscn` are built, exported and unused.**
   The lane is carried by the ground's colour field alone. Paving it and
   walling the street frontage are both cheap and both taste calls.
3. **No letters, no round, no Annette script.** She is furniture. The village
   ROUND is gameplay adoption and stays downstream of this on purpose.
4. **Adoption.** `scenes/main.tscn` is still the classroom game: no
   tonemapper, old camera, Kenney mannequin for Chuck. Whether
   `cvc_land.tscn` BECOMES the game is the next real decision.
5. **`tests/village.gd` tests the OLD village** (`village/phoneme_village.tscn`,
   untouched) and still enforces the RETIRED no-hidden-letter rule. It passes,
   so it blocks nothing -- rewrite it to test the ROUTINE when the new village
   takes the round over, not before.
6. The troll is still **PARKED**. Three rounds did not converge; it needs its
   own face build like Chuck has. See DECISIONS.md.

# CVC LAND REBUILT, and a world to put it in — 2026-11-05/06

👉 **START HERE.** The art direction is SETTLED and written up in
`lookdev/DECISIONS.md` — read that first, it is the design handoff. This
section is the state of the build.

✅ **COMMITTED on branch `cvc-land-rebuild`** at `6fae2e1`, 104 files,
working tree clean. `main` is still at `184d356` and still what deploys, so
nothing here is live. The branch is pushed to `origin`; the deploy workflow
fires only on a push to `main`, so pushing the branch cannot ship it.

⛔ `scenes/main.tscn` (the classroom game) and `village/phoneme_village.tscn`
are UNTOUCHED and still the site root. Nothing here has reached a child.

## What exists now

| | |
|---|---|
| `scenes/cvc_land.tscn` | the rebuilt CVC Land, GENERATED — do not hand-edit |
| `tools/build_cvc_land.py` | generates it; every position read from the plan |
| `art_src/explore/world_plan.py` | **the plan**: no bpy, shared by sculpt and layout |
| `art_src/explore/cvcland.py` | ground + troll + pedestal + bell + shed + cart |
| `storybook/painted.gdshader` | the painted surface |
| `storybook/ink.gdshader` | the outline |
| `storybook/painted_surface.gd` | applies both — **without this node the build looks like the asset pack** |
| `tests/cvc_land.gd` | the loop, in CI |
| `lookdev/` | the look-dev kit: scenes, shooter, `measure.py` |

## The settled look

patina `grain_strength 0.12` · `diffuse_toon` · inverted-hull ink at **3.4 px**
(clip space, so one line weight covers a 4 m cottage and a 5 cm berry) ·
saturation 0.78 / exposure 1.22 · **orthographic, pitch 16**, zoom 8.2.

⭐ Verify any change with `python3 lookdev/measure.py` against the Cycles
control at sat 0.304 / val 0.546. "It still looks too green" is not a number
and cannot be aimed at; the published build was 2.3x over.

## ⭐⭐ The layout is a diagram of a word

Three pedestals; each letter zone sits DIRECTLY BEHIND its own pedestal, so
fetching a sound is an out-and-back in the direction of the slot it fills.
Onset left, vowel middle, ending right — the order a child reads them.

Three worn tracks run out to the zones. **The paths teach the game**: a child
can see where to go before anybody speaks to them.

⛔ `world_plan` works in SCREEN axes (`ROW`, `AWAY`), not world X/Y. At yaw 30
a row laid along world X comes out diagonal. The ground grid is generated in
those axes too — an axis-aligned box holding this world would be 76 x 85 m,
a third of it corner nobody can see.

## ⛔ 20 blocks, and the letters were chosen from the WORD LIST

`bdhlmpst` × `aeiou` × `bdgmnpt` = **172 CVC words**. Counted over the 516
strict CVC words in `assets/words`.

  * 42 (every usable letter) was TRIED and is too messy — the zones read as
    heaps of dice. The 5-letter vowel zone was the control in the same frame.
  * `w` is OUT: every word it bought is a vowel+w DIPHTHONG (bow law saw).
    ⛔ Do not promote the next letter down — `y` has the same problem, `r` is
    r-controlled, and `s` adds 12 junk words (bis dis hes pis).
  * `b` and `d` are in both consonant zones ON PURPOSE — the reversal pair.
  * The rest are BANKED for `world_plan.BONUS`, a reserved fourth site up the
    north lane for digraphs and a harder Annette-prompted round. It is sited
    now because the ground is a BAKED MESH; finding the spot later means
    re-sculpting and re-baking.

## 👉 WHAT IS NOT DONE — pick up here

1. **The village half of the world is empty ground.** `world_plan` knows
   where `VILLAGE_GREEN`, the five `VILLAGE` sites and `MILL` are, and the
   lane already runs to the foot of the cart track. Nothing places them.
   Needs a generator like `build_cvc_land.py`, reading the same plan.
2. **`tests/village.gd` does NOT block the deploy** -- that claim was wrong.
   All six suites are green on this branch (`smoke layout lever feedback
   village cvc_land`, 0 failures each, Godot 4.5.2 headless). The terrace it
   asserts at `Vector3(5.5, 0.1, 7.0)` is still there, because
   `village/phoneme_village.tscn` is UNTOUCHED: that suite tests the OLD
   village, not this world. ⚠ So it is not a blocker, it is a test aimed at
   the scene being replaced -- and it still enforces the RETIRED
   no-hidden-letter rule (it reports `[]` hidden over 663 visuals). Rewrite it
   to test the ROUTINE (Annette prompts, letters findable, a letter carried
   back) when the new village takes over, not before.
3. **The no-hidden-letter rule is RETIRED by decision** — *"the player will
   go around the space to collect letters, that's the fun of it."* Its
   replacement is REACHABILITY, which `tests/cvc_land.gd` already implements.
   `tools/village_spawn_probe.gd` and the occlusion rule in the village
   generator exist only to serve the retired rule.
4. **Adoption.** `scenes/main.tscn` still has no tonemapper, the old camera
   and a Kenney mannequin for Chuck. Deciding whether `cvc_land.tscn` BECOMES
   the game is a separate call, and should come after the village is in.
5. The troll is **PARKED** — three rounds did not converge. It needs a proper
   character pass with its own face build, like Chuck has. See DECISIONS.md.

## ⛔ Traps that cost real time, all in `lookdev/DECISIONS.md`

The one worth repeating here: **Godot serves a STALE IMPORT CACHE.** Rebuild
a mesh in Blender and anything that reads it through Godot — a capture, a
collision bake — silently uses the PREVIOUS geometry, with a plausible face
count. It caught this session out FOUR times. Always
`godot --headless --path . --import` first.

# Four fixes: flat floor, village spread, village letters, overcast light — 2026-11-03

Four notes from the classroom preview, all four addressed.

## 1. The rolling floor was the wrong call — the play area is FLAT

Rolling terrain worked, which is not the same as being right. Blocks on a
slope read as tipped, Chuck's feet float or sink by the slope error, and a
five-year-old aiming a block at a pedestal gets punished for a hill they
cannot see from a fixed camera.

`PLAY_RELIEF = 0.0` and `GENTLE = 0.0`, the hollow way is gone, and all six
hill centres moved out to >= 13 m. Measured on the rebuilt mesh:

    r < 9.0 m : height +0.000 .. +0.000, max slope 0.0 deg
    r < 11  m : max slope  3.9 deg
    r < 13  m : max slope 15.9 deg

The world still ROLLS where it is only scenery. Flat where it is played on.

## ⭐⭐ 2. Flattening the floor silently killed the ground's colour

This is the trap, and it is the kind that passes every test. The terrain's
colour field was driven mostly by `local_relief` and by SLOPE -- a crown
burns pale, a bank shows thin soil. On a dead-flat floor both of those are
EXACTLY ZERO. Nothing errored. The checks stayed green. The field just
quietly collapsed to one almost-uniform mint green and every bit of work
that had gone into giving the ground causes stopped doing anything.

`_grass_position` is re-weighted onto what survives flattening: everything
POSITIONAL (the mown line, the worn tracks, the path, the headland, damp
under a wall) plus three octaves of patchiness, which now carry the
variation the landform used to. Relief and slope are kept at small weights
so the far field, which still rises past 9 m, is not flat-coloured.

Measured on the baked albedo, which is the only place this shows up:

    hue p5..p95  47.3 .. 91.0 deg  (spread 43.7)
    val p5..p95   0.49 ..  0.64    (spread 0.149)

⭐ When you remove an INPUT, go and look at what was reading it.

## 3. The phoneme village: structured and spread

The houses were clustered in one central knot. They now front a lane at
z ~ -13 across 30 m of x, the mill mound moved out to (-16.5, -4.0) and the
green to (2.0, 1.0), with the trigger and green volumes enlarged to match.
74 spawn markers, 3 levels, 51 lane stones, 26 trees.

The fingerpost and the bench are now SEARCHED positions like the planters,
not fixed ones -- the layout generator runs the engine's own occlusion rule
backwards, so a prop can never end up on a sight-line to a letter. The check
caught exactly that case (`Spawn12 <- Model/Fingerpost`) before it shipped.

## 4. The village letters were a different typeface from Chuck's

Correct observation. The village was instantiating the OLD block scene while
the three blocks beside Chuck came from `storybook/foundation/block.tscn`.
`phoneme_village.gd` now has `@export var block_scene` -- default unchanged,
so the shipping village is untouched -- and the generated village passes the
foundation block in.

## 5. Lighting: a grey English day, not golden hour

⛔ The first attempt at "soft" came out BLEACHED PASTEL, and the reason is
worth keeping. The obvious way to soften light is to dim the key and raise
the fill, so I raised sky strength, added a 900 W dome AND pushed exposure
up, all at once -- three light sources stacked. Soft, and completely
colourless.

⛔ Dimming and AgX both pull chroma out, so doing both at once drains the
palette twice. Blender's grade solves it with the "Punchy" look; the engine's
equivalent is `adjustment_saturation`. **Dim the light, then put the colour
back.** Wet grass under cloud is if anything GREENER than grass in sun.

Landed, Blender and engine matched:

| | Blender | Godot |
|---|---|---|
| sky | `sky_world(strength=0.30)` | `ambient_light_energy = 0.82` |
| key | sun 0.55 at 22 deg, nearly overhead | `light_energy = 0.40` |
| softness | dome 165 W, size 46 | `light_angular_distance = 26.0` |
| shadow | -- | `shadow_opacity = 0.34`, `shadow_blur = 4.0` |
| grade | AgX Punchy, exposure -0.28 | AgX, exposure 1.02, saturation 1.22 |

## ⛔ What is NOT verified

**I have still never seen the village in-engine.** `tests/capture.gd` gained
`--preview`, `--preview-village` and `--preview-wide`, which load
`scenes/foundation_preview.tscn` instead of `scenes/main.tscn` -- the
classroom game and the storybook art build are different scenes with
different lighting and a separately generated village, so reviewing the art
set through `main.tscn` shows neither.

The flags are untested. Running capture from this session's shell HANGS at
the first frame -- and per the lesson at the top of this file I checked the
TOOL against a control first: the pre-existing `--overview` view on
`main.tscn` hangs identically. So the harness does not complete from a
non-session shell; the new flags are not implicated, and are not confirmed
either. Run them from a desktop terminal.

Everything above is verified by: the six suites green BY EXIT CODE (smoke,
layout, lever, feedback, village, plus `check_foundation_village.gd`), the
measured terrain geometry, the measured baked albedo, and the Blender review
render. The engine lighting numbers are a translation of an approved Blender
grade, not something I have looked at.

# ⛔⛔ I MISDIAGNOSED A CRASH FROM A BROKEN TOOL — 2026-11-03

**Correction to the section below.** I concluded the published preview
crashed Chrome, because screenshots timed out with "renderer unresponsive"
and Chrome was left with two processes. Then the SLICE that had worked all
session failed identically -- and so did **example.com**. Chrome's screenshot
capability was broken for every page. The evidence proved nothing about the
build.

⭐⭐ **Before blaming the thing under test, test the TOOL against a known-good
control.** One screenshot of example.com would have saved an hour and two
commits of "fixes" for a fault that was never demonstrated. The Godot console
showed a clean startup banner and no errors throughout -- evidence I had and
under-weighted, because a screenshot timeout felt more concrete than a log
that looked normal.

The two changes made on that diagnosis are KEPT, because both are defensible
anyway, and both are now described as hardening rather than as fixes:

- textures 1024 -> 512 (70 MB -> 28 MB of uncompressed texture). Indefensible
  on a Chromebook whatever else was true.
- trimesh collision baked to `.res` instead of built at `_ready`. The web
  export is SINGLE-THREADED, so 25,000 faces of shape-building block the only
  thread there is -- and that cost had grown 6x when the terrain grid was
  densified, with nothing re-testing it in a browser.

⭐ Also found: my local test command was weaker than CI's all along. Running
`godot ... | grep RESULT` discards the EXIT CODE, which is the only thing CI
checks. Capture to a file and test `$?`.

⛔ And one CI failure was the repo's OWN known village-suite flake
(`moved >= 18`), recorded in 1502d40 as able to "block a deploy that has
nothing wrong with it" -- not my changes.

# The original (wrong) diagnosis follows, kept for the record

The first published `/preview/` took Chrome down on first load. Not slow:
the renderer stopped answering, three screenshot attempts timed out, and
Chrome was down to two processes afterwards.

## The cause, measured

Fifteen assets at 1024 squared is **70 MB of UNCOMPRESSED texture**, loaded
at once, on top of a 38 MB wasm and a 32 MB pck. Everything dropped to 512
except the terrain:

    uncompressed texture   70 MB -> 28 MB
    preview pck            33 MB -> 27 MB

The resolution was never being earned. The camera is 142 px per metre, so a
3.5 m building is about 500 px on screen and a 1024 sheet is four times more
texels than pixels. The terrain keeps 1024 because it is 26 m across and is
already the blurriest thing in the frame.

## ⛔ The mistake behind the mistake

Download size had been explicitly ruled out as a concern at this scale, and
that got filed as "texture size does not matter". It does -- just not for
the reason that was dismissed. **This is a RUNTIME MEMORY fault, not a
download one**, and the two are easy to confuse because the same number
controls both.

The figure that mattered was never the kB in a report line. It was texel
count multiplied by every asset resident at once, and nothing in the build
output showed it. `[asset]` lines report kB and tris; neither would ever
have caught this.

⭐ For a web build, measure the sum of (width x height x 4) across every
texture a SCENE loads, not the size of any one asset.

## ⛔ And it only showed up in the published build

The local slice -- six assets, about 20 MB of texture -- ran in the browser
all session. The preview adds twenty more. Nothing in the headless checks,
the suites or the Blender renders touches a GPU, so none of them could have
caught it. The first thing that exercised the real load was the real URL.

# DEPLOYED — the new art lives at /preview/ — 2026-11-03

    the game     https://tacomadragonclass1.github.io/phonicsfarm/
    the new art  https://tacomadragonclass1.github.io/phonicsfarm/preview/

⛔ **The classroom game was not replaced.** Pages serves one site and
`deploy.yml` fires only on a push to `main`, so putting the new art on a URL
would ordinarily have meant swapping `run/main_scene` and taking the real
game offline. It is exported a SECOND time into `/preview/` instead:
`scenes/main.tscn` stays the site root, the preview is a side door, and
`scenes/main.tscn`, `village/phoneme_village.tscn`, `project.godot`, `tests/`,
`player/` and `alphabet_block/` are all verified untouched by the diff
against 0f4ae53.

`scenes/foundation_preview.tscn` puts the home field and the rebuilt village
in ONE walkable scene on purpose: the two sets were built weeks apart, and
the only real test is whether they look like one world when you walk between
them.

## ⛔⛔ TWO EXPORT PRESETS, and this one nearly shipped silently

Godot packs every imported resource, not only the ones the main scene
reaches. Merely adding the new art took the CLASSROOM build's pck from
**1.8 MB to 33 MB** -- a download the children pay for and never see, on a
game that is meant to open on a school Chromebook.

`Web` now excludes `assets/storybook/explore/*`, `assets/storybook/village/*`
and the parallel scenes, and is back to **5.8 MB**, which is exactly where
phase 1 left it. `WebPreview` includes everything and is the 33 MB one, which
only someone opening `/preview/` pays for.

⭐ The general lesson: adding assets to a Godot project costs download size
even when nothing references them. Check the pck, not the scene.

## Also fixed on the way

A `StaticBody3D` with no `CollisionShape` child is not collision, it is an
empty node. The generated village had six of them and Chuck walked through
every building.

## To put the new art in the real game

Not done, and deliberately a separate decision. It means pointing
`scenes/main.tscn` at the new village and assets, AND adopting a tonemapper
-- the shipping environment has none, so the palette renders raw and much
hotter than every review that was approved. `tests/village.gd` also hard-codes
the OLD terrace's ramp coordinates, so swapping the village into main.tscn
breaks it and would block the deploy until those are updated.

# THE RE-PLANNED VILLAGE — generated, verified, committed — 2026-11-03

`village/foundation_village.tscn`, built by
`tools/build_foundation_village.py`.

⛔ It is a NEW scene. `village/phoneme_village.tscn` is untouched: it is the
shipping village, the owner's source of truth, edited by hand in the editor,
and CLAUDE.md says not to regenerate it. `tests/village.gd` loads
`scenes/main.tscn` and still tests that one. Both pass.

⛔ Like `tools/build_phoneme_village.py` before it, the generator is a
SCAFFOLD and not a build step. Once the scene is edited in the editor the
scene is the truth and the script is history.

## ⛔ THE CAMERA DECIDES WHERE THE BUILDINGS GO

It is orthographic, at pitch 30 / yaw 30, and never turns -- so "behind" is
one fixed direction for the whole board, and anything at higher X and Z
stands between the viewer and everything past it. The first layout arranged
the six buildings in a ring and put the flower shop and workshop on the +Z
side; 15 of 35 markers failed the no-hidden-letter rule immediately.

The village sits on the FAR half now and the green -- where the letters are
-- is the near half. That is also simply the better picture: you look across
an open green AT the village.

For the same reason the mound is TURNED 200 degrees. Its shelf and steps are
built on one side of the asset, and unrotated that side faced away: the
mound hid its own middle level and every shelf marker failed.

## ⭐ THE GENERATOR CHECKS VISIBILITY ITSELF

Nudging marker positions by hand until the Godot check passes is the wrong
loop -- it is slow, and the next person to move a building silently breaks
it. The engine's occlusion rule is implemented in the generator, so the
layout is correct BY CONSTRUCTION and the Godot check confirms rather than
searches. Two refinements it needed:

- **An occluder the point stands inside is skipped**, exactly as the Godot
  check skips a box containing the sample. Without it the mound's own 8.4 m
  footprint rejected every marker on its shelf and the middle level vanished.
- **The rule also runs BACKWARDS.** Markers are fixed first, then every
  scattered prop -- mushrooms, blossom, bushes, wall runs, all 51 lane
  stones and the planters -- is offered a position and refused it if it
  would stand on somebody's sight-line. A gap in a lane reads as a missing
  stone, which is what an old path looks like anyway.

⛔ And when one marker still failed after two rounds of widening occluder
boxes, the fix was to make the check NAME THE CULPRIT rather than guess
again. It was a planter. Anything decorative whose exact spot does not
matter should be searched, not modelled and hoped for.

## A middle level is a requirement, not a flourish

`tests/village.gd` checks for spawn markers at three heights snapped to 0.5,
because the village is meant to scatter its letters "across all three
walkable levels". A mound with a top and a bottom gives two. The step
landing is therefore a real grassed terrace at 1.05 m with room to stand a
block on -- which is also what a flight that long would have anyway.

## Result

    46 spawn markers, three levels [0.0, 1.0, 2.0]
    51 lane stones, 26 trees alternating two silhouettes
    no letter can be hidden behind a structure

`tools/check_foundation_village.gd` is the check; it is separate from
`tests/village.gd` because that one tests the shipping village.

## State at commit

All five shipping suites: 0 failures. `verify_rig.py`: Chuck and Annette both
match the shipping skeleton. `scenes/main.tscn` and
`village/phoneme_village.tscn` untouched -- the game runs exactly as it did.

⚠️ Nothing is wired in. To see any of this you have to point
`run/main_scene` at `scenes/foundation_slice.tscn`, or instance
`village/foundation_village.tscn`. Adopting it in the real game is a
separate, deliberate step: it also means adopting a TONEMAPPER, because
`scenes/main.tscn` has none and the palette renders raw without one.

# THE MILL MOUND — what replaces the terrace and ramps — 2026-11-03

He called the ramp terrace garbage and asked for a clever, beautiful, TIGHT
way up onto a plain that looks over the village -- one with a reason for
being.

## ⭐ THE WHOLE THING FOLLOWS FROM ONE FACT: A WINDMILL NEEDS WIND

That is a real and legible reason for the ground to be raised exactly where
the windmill stands. It is not a ramp placed so the player can get up; it is
a mound that had to exist, with the ways up that such a mound would have.
Once the mound has a reason, everything attached to it gets one:

- **The way up is the miller's CART TRACK**, and a loaded cart cannot take a
  steep gradient. So it cannot go straight up -- it has to WRAP the mound.
  That is what makes this tight instead of a long diagonal ramp eating the
  map, and it means the village turns below you as you climb, which is the
  view the feature exists for. 174 degrees of wrap at **6.3 degrees**.
- **Nobody on foot walks the cart track.** A short flight of stone steps
  cuts up the bank on the far side. Two routes up, which is also simply
  better to play.
- **A bank cut that steep has to be held**, so it is revetted in drystone --
  the same wall vocabulary as the field boundary.
- **A dry bank with a door in it is a ROOT CELLAR.** Tucked under the
  flight, where a real one would be: the steps give it a dry lintel and the
  bank gives it a cold store. Strap hinges and a ring handle.
- At the top, a mill yard that is a place of WORK -- grain sacks, a
  hand-cart, a parapet to lean on and a bench facing the village.

## ⛔ Gameplay shaped the numbers, it did not decorate them

The village scatters 23 letter blocks over its levels, so:

- the **top is flat**. A block on a slope reads as a mistake and
  `drop_block` would roll it.
- the cart track is **6.3 degrees** and the steps **27**, both well under
  `move_and_slide`'s 45-degree floor limit. Chuck has no jump.
- ⛔ The steps are 27 degrees because cutting them straight INTO the bank
  gives only 2.2 m of run for a 2.15 m rise -- 44 degrees, which Godot would
  technically allow and which would feel like climbing a ladder. Projecting
  the flight OUT from the bank buys 3.8 m. The landing a third of the way up
  is there for the same reason a real flight has one.
- Mound height **2.15 m**: Chuck is 1.35, so his eyeline from the top clears
  a 2.05 m cottage eave. High enough to look over, not a cliff.

## ⛔⛔ A transform bug that NO RENDER WOULD EVER HAVE CAUGHT

`_spin_z` rotates raw `vert.co` about a world pivot. That is correct for
everything `forms` makes -- those generators write world coordinates into the
mesh and leave the object at the origin. `meshtools.torus` does NOT: it keeps
its offset in `obj.location`. Spinning one about a pivot five metres away
treats near-origin LOCAL coordinates as world ones and flings it five metres
the opposite way.

The cellar door's ring handle ended up **5 m underground**, and took the
asset's whole bounding box with it: `base_z = -4.995`, height 7.81 for a
2.15 m mound. Every render looked completely fine, because the thing that
moved was far too small to see. It was caught by reading the REPORT LINE, not
by looking. `_spin_z` now bakes `matrix_world` into the vertices first.

## ⛔ And one that a render did catch

The first outer revetment stacked a column of stones at each sampled angle.
The samples are half a metre apart and the stones are not, so it rendered as
free-standing stone pillars with daylight between them. The retaining FACE is
painted onto the causeway's own outer skirt now -- it costs nothing, it is the
face you see from the village, and all the stones add is the coping along the
top. 17,218 tris -> 11,226.

Wheel ruts are painted for the same reason: dents of 0.03 on a 2.3 m road are
invisible at 142 px per metre; two darker bands at wheel spacing are not.

## Cost

mill_mound: 11,226 tris, 1,486 kB, 16.7 m across, 2.84 m tall.

## Still to do

Collision (the `terrain_collision.gd` trimesh pattern already exists), and the
re-planned layout scene that places all of this with its 36 spawn points.

# DE-KENNIFIED — every village asset replaced — 2026-11-03

144 Kenney instances across 17 assets, plus seven buildings made of
`beveled_cube.obj`. All gone. The brief was to judge whether each asset
belongs in a Shire-like village at all, not to swap them one for one.

## ⛔ CUT, because they are the wrong REGISTER (35 instances)

- **campfire x2, tent x1, seat logs x2.** A campsite says "adventurer
  passing through". This is a settled village: it has hearths and benches,
  not a fire ring on the green.
- **statue obelisk x1.** A standing stone is fantasy-adventure furniture.
  A WELL does the same job of giving the green a centre and is the thing a
  village actually gathers at.
- **rocks x29.** A ring of boulders is the asset-pack answer to "edge of the
  world". A field is bounded by something somebody BUILT, and the foundation
  set already speaks drystone wall and hedgerow.

## Kept and rebuilt

| was | now | why |
|---|---|---|
| sign x1 | `fingerpost` | a fingerpost at a lane junction is as Shire as it gets |
| pot_large x2 | `planter` | a half-barrel, hooped, planted |
| mushroom_redGroup x7 | `mushrooms` | ⭐ KEPT deliberately -- hobbits prize them |
| plant_bushDetailed x2 | `bush` | cushion at shrub size, with berries |
| flowers x20 (3 assets) | `blossom` | one clump whose colours vary WITHIN it |
| path_stone x51 | `lane_stone` | 154 tris, 83 kB |
| tree x18 + tree-high x8 | foundation tree + `tree_b` | see below |
| (new) | `well`, `bench`, `wall_run`, `bunting` | what the place was missing |

## ⛔ A prop used 26 times is ONE PROP USED 26 TIMES

`tree_b` exists for that reason alone, and is deliberately NOT a tweak of
the foundation tree: that one is a broad fanned crown on an S-curve, this is
a tall upright cone of smaller cushions on a trunk that leans and recovers.
Two silhouettes alternating read as a wood; one repeated reads as wallpaper.
The same rule governs the lane stones, which take a yaw and a size per
instance -- 51 identical stones is a zip fastener.

## The bunting was beveled cubes too

A flag is a TRIANGLE and the line it hangs on is a CATENARY. Both are three
lines of maths and neither is a box, and the sag is the whole charm. Each
flag also hangs at its own angle: a row of identical pennants is a printed
border, not cloth.

## Cost -- the whole replacement set

| | tris | glb |
|---|---|---|
| well | 1,396 | 441 kB |
| fingerpost | 332 | 311 kB |
| bench | 384 | 388 kB |
| planter | 2,212 | 446 kB |
| bunting | 402 | 186 kB |
| tree_b | 2,940 | 942 kB |
| bush | 1,632 | 402 kB |
| mushrooms | 1,048 | 357 kB |
| blossom | 1,880 | 389 kB |
| lane_stone | 154 | 83 kB |
| wall_run | 1,692 | 429 kB |

Textures are 256-512 for everything but `tree_b`, because these are props
seen at a distance and placed in quantity.

## Still to do

The village TERRAIN (terrace, lookout, two ramps) and the re-planned LAYOUT
scene with its 36 spawn points and the no-hidden-letter rule. Every asset the
layout needs now exists.

# VILLAGE REDESIGN — the six buildings and Annette — 2026-11-03

Scope agreed with him: everything including Annette, the six building
identities kept, and the layout re-planned. ⛔ Re-planning the layout means a
NEW scene -- `village/phoneme_village.tscn` is his source of truth, he edits
it in the editor, and CLAUDE.md says not to regenerate it. The shipping
village and `tests/village.gd` (which loads `scenes/main.tscn`) stay exactly
as they are.

## ⛔ THE VILLAGE IS THE PUREST CASE OF WHAT PHASE 1 WAS REJECTED FOR

Every one of the six buildings is `assets/toy_village/beveled_cube.obj`,
instanced over and over with flat colour materials. A windmill, a bakery and
a clock tower, all made of the same box. That is the asset-pack vocabulary in
its most literal form and no amount of retexturing reaches it.

## The six, rebuilt out of `sb_lib/forms`

Each is designed around the ONE thing that makes it legible:

- **Windmill** -- the only true solid of revolution in the game, and the
  clearest case for `lathe`: a battered, pinched, flaring tower is six
  numbers and is flatly impossible out of a cube. Gallery with a rail, lathed
  slate cap, weathervane, and four sails that are a swept spar plus a lattice
  of bars plus canvas DOWN ONE SIDE ONLY, which is what stops the cross
  reading as a plus sign.
- **Bakery** -- read from the OVEN, so the coursed brick stack is the biggest
  thing on it and the arch of the oven mouth is repeated in the door. Striped
  awning, three loaves on the sill.
- **Clock house** -- read from the DIAL: lathed, pale, high, with twelve
  marks and hands at ten past ten. Open belfry with a bell on four posts, so
  the tower reads hollow at the top instead of as a stump with a hat.
- **Bookshop** -- read from the JETTY. Upper storey overhanging on brackets,
  a three-sided bay window with five leaning books in it, and the whole
  building leans 1.3 degrees because a bookshop should look oldest.
- **Flower shop** -- read from the STOCK. The building is deliberately the
  plainest of the six; everything legible about it is the awning, the trough
  of buckets, the window boxes and the rose climbing past the sign.
- **Workshop** -- read from being OPEN. Three walls and a header instead of
  four, a bench with a vice and tools under the opening, and a lean-to of
  stacked timber. It is the only building you can see INTO.

⛔ **Two corrections after the first lineup render.** Six buildings in a row
made faults invisible on any one of them obvious:

- They were all the same cream. A village of six cream buildings is one
  building six times. The bakery is ochre, the bookshop sage, the flower shop
  rose -- the limewash a shop can afford is part of what it is.
- They all had the same roof. Identical course tables gave six copies of one
  barrel-vaulted hut. The pitch now differs per building, and the last two
  courses collapse faster so the ridge is a crisp line rather than rounded
  over.

## Annette, as a classic librarian

She has one hard job: never be mistaken for Chuck at gameplay distance. So
every silhouette decision is the opposite of his.

| | Chuck | Annette |
|---|---|---|
| height | 1.35 m, 2.9 heads | 1.58 m, nearer 4.5 -- an adult |
| widest at | a hat brim | the hem of a long skirt |
| legs | bare and apart | one unbroken cone |
| hair | a wild black spray | a smooth bun, closed outline |
| glasses | LOST in his redesign | HERS now |

⭐ The glasses are the useful accident. Round spectacles were the old Chuck's
only distinguishing feature and dropping them was the risk in his pass;
moving them to Annette spends the idea instead of wasting it, and gives the
two characters one shared piece of visual language.

⭐ The skirt is a `lathe`, which is what an A-line skirt literally is: one
drawn silhouette revolved. Four shallow dents deny the lampshade.

Her rig is Chuck's skeleton so one set of motion ideas serves both, verified
against the shipping control:

    CONTROL chuck.glb    joints 14  skinned True  idle 9  walk 13
    ANNETTE annette.glb  joints 14  skinned True  idle 7  walk 9

Fewer moving channels BY DESIGN -- half his leg swing and twice his hip sway,
because a skirt that counter-swings with the thighs under it reads as
trousers, and almost all of the motion a viewer reads is in the hips and hem.

⛔ Three fixes from the close-up: her hands did not reach the book (the arms
ran straight down and she stood with a hardback floating in front of her
stomach), the spectacles were bright gold and read as goggles, and the loose
strands at her temples were thick enough to look like bolts screwed into her
head.

## Cost

| | tris |
|---|---|
| windmill | 2,812 |
| clock house | 2,444 |
| bakery | 3,036 |
| bookshop | 2,280 |
| flower shop | 14,192 |
| workshop | 2,352 |
| annette | 4,412 |

Flower shop is the outlier and it is the flowers: every bloom is petals, a
centre and a stem, and there are five bucketfuls plus a climbing rose.

## Still to do on the village

The Kenney NATURE props the village scene still references directly -- 18 rim
rocks, trees, flowers, mushrooms, bushes, path stones, tent, obelisk,
signpost, campfire, bunting. The village terrain (terrace, lookout, two
ramps). And the re-planned layout itself, as a new scene, with its 36 spawn
points re-derived and the no-hidden-letter rule verified.

⛔ Contract any new village scene must satisfy, read out of
`phoneme_village.gd` and `tests/village.gd`: root carries `phoneme_village.gd`
in group `phoneme_village`; `$Annette` is a VillageGuide with an `$Annette/Touch`
Area3D; `$SpawnPoints` holds the markers; `$Blocks` is the container; and
`$Trigger` is an Area3D. 23 letters -- k, q and x are out because they collide
with c by ear.

# PHASE 2 — the set is in the engine — 2026-11-02

Approved, and run. Everything that was a Blender render is now a Godot scene:
Chuck is RIGGED and is the avatar rather than a display model, the terrain has
real collision and is not flat, and the slice is walkable in the real web
export. `scenes/main.tscn` is still untouched.

## What was built

- `storybook/foundation/chuck.tscn` -- a drop-in for `player/player.tscn`.
  Capsule 1.16 -> 1.33 and its centre 0.58 -> 0.665 for a 1.35 m character.
  The capsule RADIUS stays 0.3, deliberately narrower than the straw hat: the
  brim reaches 0.385, and sized to the hat he would stop 8 cm short of every
  doorway he owns. A brim clipping a wall is the cheaper error.
- `storybook/foundation/{cottage,tree,terrain,props,garden}.tscn` and the
  block scene from the previous pass.
- `storybook/foundation/terrain_collision.gd` -- `create_trimesh_collision()`
  at load, on collision LAYER 1, which is what the rest of the game expects
  of ground (`ground_height()` raycasts mask 1; `can_reach()` mask 13
  includes it).
- `scenes/foundation_slice.tscn` -- the whole world, walkable. ⛔ Every
  object's Y is `foundation.terrain_height()` at its own x,z, not 0. The play
  area rolls 0.35 m, so y = 0 either floats or sinks an object by up to 20 cm.
- `art_src/explore/verify_rig.py` -- a real check, see below.

## The rig

Bone layout and motion are phase 1's, unchanged and on purpose: `player.gd`
has been driving that skeleton on real hardware since September and a
redesign of the BODY is not a reason to re-solve the MOVEMENT. The anatomy
constants are now SHARED between the mesh and the rig so they cannot drift.
Leg swing came in 26 -> 22 degrees and head counter-rotation went up, because
this Chuck has shorter legs under a much heavier head.

⛔ Scale FIRST, then rig. `facet` welds vertices and `_scale_to_height` moves
every one of them, so a skeleton built before either is bound to coordinates
that no longer exist. `_scale_to_height` returns its factor for that reason.

## ⛔⛔ How NOT to verify a rig

The obvious check fails, and fails SILENTLY in two different ways:

1. Importing six copies of the GLB and `frame_set`-ing a different frame
   before placing each one. Blender evaluates the whole scene at ONE current
   frame, so all six pose at whichever was set last and the sheet comes out
   as six identical figures standing still.
2. Re-importing and reading pose bones. Every rotation read 0.0 at every
   frame. In Blender 5 an action must be bound to an action SLOT as well as
   assigned, and without that it quietly does nothing.

Both look exactly like "the animation did not export", which is the wrong
thing to go and debug. `verify_rig.py` reads the glTF buffers directly --
no Blender, no failure mode -- and uses the SHIPPING `chuck.glb` as a
control. Result:

    CONTROL chuck.glb             joints 14  skinned True  idle 9  walk 13
    SUBJECT foundation_chuck.glb  joints 14  skinned True  idle 9  walk 13

Identical on every count. Run it after any character build.

## ⛔ The engine needs a TONEMAPPER, and this was proved not assumed

The first in-engine export came out markedly more saturated than every
Blender review of the same assets -- a red roof where the review had
terracotta. The tempting diagnosis is a colour-management bug, so it was
tested: exporting the same slice with `albedo_texture_force_srgb` DISABLED
produced the opposite failure exactly as this file describes it, washed out
and pale with plaster clipping to white. The sRGB fix is right and still
needed.

Sampling the baked PNGs settled the rest. They hold the palette bytes
EXACTLY -- `#E2CFB0` is `s_wall` verbatim, `#9B8E74` is `e_stone` verbatim.
So the bake is faithful and the whole difference is grade: `scenes/main.tscn`
has no tonemapper at all, and `render_foundation.py` renders through AgX.
The slice sets `tonemap_mode = 4` (AgX) with exposure 1.3.

⚠️ That is a DEVIATION from the shipping environment and a decision to take
deliberately: adopting these assets means adopting a tonemapper with them, or
re-grading the palette for linear output. The slice still reads hotter than
the Blender reviews; matching them properly is a grading pass, not a bug.

## ⛔⛔ The terrain's normals pointed DOWN, and it had broken the colour field

Caught only by sampling the baked texture, which is the lesson.

`bmesh.ops.recalc_face_normals` makes normals CONSISTENT, which for a closed
volume also means outward -- but an open heightfield has no outside, and it
chose -Z. Measured: nz was -1.0 at every vertex.

`_grass_position` computes `steep = 1 - max(nz, 0)`, so nz = -1 made steep = 1
EVERYWHERE and added a flat +0.55 to every vertex, saturating the ramp at its
palest stop. Before the fix the top five colours in the terrain texture were
five shades of `f_grass_sun` at about 23% of the sheet between them. After,
no single colour exceeds 0.62%.

The mown line, the tracks and the path edge still read throughout, because
those return or subtract absolutely -- which is exactly why the bug survived
three rounds of looking at renders.

⛔ The four field amplitudes were all tuned WHILE `steep` was pinned at 1.0
and three of the four were doing nothing. With the normals fixed they were
far too strong and the ground went blotchy, so they are halved and the
general sward is clamped to 0.38..0.86. The path, tracks and bed still return
absolutely and keep the full range -- they are the edges, and the edges are
meant to be the strong thing.

## Still not done

The village redesign. Matching the engine grade to the Blender reviews. The
1.203x lettering constants, which now have a working browser route to settle
them. Nothing is committed.

# The block's letters, verified in a browser — 2026-11-02

He asked whether the letters would actually appear on the final blocks,
because they were not appearing. Correct observation, and the cause was not
what it looks like.

## ⛔ THE LETTERS ARE NOT IN THE GLB AND NEVER WERE

`foundation_block.glb` ships five BLANK cream plaques named Front / Right /
Back / Left / Top. Every letter on every face is a runtime `Label3D` living in
the block's `.tscn`, set by `alphabet_block.gd::update_letter()`. The letters
in the Blender review renders are geometry that `render_foundation.py` builds
on the fly purely so a review image is not of a blank toy.

So the block had no letters because **it had no scene**. There was no
`storybook/foundation/` at all -- nothing in the project referenced a single
foundation asset. Nothing was broken; a file was missing.

## What was added

- `storybook/foundation/block.tscn` -- the hybrid block scene repointed at
  `foundation_block.glb`. font_size 83 and the 0.0847 label lift carried over
  UNCHANGED on purpose: both are believed wrong by 1.203 (see above) and that
  is a separate fix needing its own check.
- `scenes/foundation_blocks.tscn` -- six blocks spelling **f g y p a j**: the
  tallest ascender in the face and every descender there is.

## Verified, not assumed

`tests/capture.gd` hangs on this machine, so the route was the project's
documented one: set `run/main_scene`, export Web, serve with COOP/COEP, look
in Chrome, restore `project.godot` and confirm `git diff --quiet`.

**The letters render.** All six, on the front faces and the top faces, inside
the new tray, with the descenders clear. The inset rim also reads better in
the engine than it does in the Blender renders -- the shadow line round each
plaque is crisper under the Compatibility renderer.

⚠️ One honest tradeoff the test exposed: on faces turned more than about 60
degrees from the camera, the raised rim clips the leading edge of the letter.
The hybrid block's proud plaque would not do that. Those faces are
unreadable at that angle anyway, but it IS a cost of making the face inset.

## ⛔ Do not copy the camera basis out of scenes/main.tscn

It is stale, and it cost a whole export-and-look cycle. That camera carries
`fixed_camera.gd`, which overwrites `rotation` in `_ready()` from its
pitch/yaw exports -- so the basis stored in the scene file is never used and
need not be correct. Copied verbatim onto a camera with no script it aimed
about 25 degrees ABOVE the horizon, and the first browser test rendered
nothing but sky with no errors in the console. State pitch and yaw outright.

# Edges in the ground — 2026-11-02 (last pass of the day)

The ground had CAUSE after the previous pass but no EDGES, and a field is
read by its edges: the line a mower left, the track feet wore off the path,
the strip along a wall nothing reaches. Every one of those is a boundary, and
a boundary is the one thing the old field could not make.

## ⛔ THE GRID IS THE COLOUR RESOLUTION

This is why every previous attempt came out as soft mottle no matter what was
driving it. The colour field is evaluated per VERTEX, so at `GROUND_STEP` 0.80
the sharpest thing the ground can hold is about 1.6 m wide -- which is a
gradient by definition. No amount of better maths fixes that; the mesh has to
get denser first.

0.32 m now: 2,048 -> 13,122 triangles, about 300 kB more mesh, and an edge
around 0.6 m, which is roughly what a mower actually leaves.

`landform()` was split out of `terrain_height()` to pay for it. `local_relief`
runs nine height lookups per vertex over 7,700 vertices, and going through
`terrain_height` meant 4.9 million path-distance tests. It is also more
correct: relief should describe the LANDFORM, and the hollow way and the
building pad are cuts made into it, not features of it.

## The four edges

- **The mown line.** `MOWN` is the ground somebody actually cuts, round the
  house and garden. Mowing does not change a field's colour so much as REMOVE
  ITS VARIATION, so inside the line the ramp is compressed toward the middle
  and nudged very slightly lighter; rough ground beyond keeps its full range.
  ⛔ First attempt compressed 0.62 and lifted 0.055 and the kept ground went
  flat and pale -- a slab of lawn laid over the field, louder than the
  boundary it was supposed to draw. 0.42 and 0.030 reads as texture instead.
- **Its fringe.** A 0.5 m band of darker, uncut grass just OUTSIDE the turn,
  where the mower never quite reached. That band is what actually draws the
  line; the compression alone is too subtle to find.
- **Worn tracks.** `TRACKS` are desire lines -- one to the garden gate, one to
  the tree. A track is not a path: nobody laid it, feet made it, so it is
  narrow, it lands between the deep grass and the earth (scuffed, not bare),
  and it has a crisp edge either side.
- **The headland.** Within 0.45 m of the wall the ground is rougher and
  darker, with its own edge rather than a falloff.

## ⛔ And the path edge, which was the biggest single offender

The way's transition was 0.85 m. A worn path has an EDGE -- the grass stops
where the boots are -- and feathering it over most of a metre is most of why
the whole ground read as gradient. It is 0.30 m now.

## Cost

Terrain: 13,122 tris, 1,426 kB (about 300 kB of that the new mesh; the
texture did not change). `budget_tris` raised to match.

# Rhyme and reason — grass, ground, rows, flowers — 2026-11-02 (later still)

Four notes on the smallholding pass, all of them fair, all of them the same
underlying complaint: things had been PLACED rather than caused.

## 1. The grass was a sprinkle; now it is a rule

Tufts were being dropped three-at-a-time around whatever object happened to be
nearby, at arbitrary angles. That is not a rule, and it read as exactly what
it was.

The rule now: **grass is long where nothing cuts it.** A boot wears the middle
of a path and not its verge; nothing mows hard against a wall, a fence or a
plinth. So `_grass_fringe()` lays CONTINUOUS lines just outside the things
that keep grass short -- both verges of the worn way, both sides of the wall,
the foot of the cottage plinth -- and there is no grass at all loose in the
open field. Blades lean away from what they grow against, into the light.

## 2. ⛔⛔ Why the grass baked BLACK, finally

Three rounds of lightening the colour did nothing, because the colour was
never the problem.

`atlas_unwrap` packs UV islands by SURFACE AREA. A blade of grass has almost
none, so on a 1024 sheet shared with a wall and sixty stones its island lands
a few pixels across -- **smaller than the bake's 10-pixel margin**. What got
baked into those pixels was margin bleed and ambient occlusion from its
neighbours, every single time, whatever the vertex colours said.

Two fixes, both of which also happen to be the honest answer:

- A blade is a `ribbon`, not a `sweep`. A sweep is a thin tapering TUBE and
  three in a clump occlude each other from every direction; ao_strength 0.68
  and edge_dark 0.20 then stack and crush it. A ribbon is two broad faces
  that mostly see the sky, and it is also what a blade of grass actually is.
- Blades are tagged `flat_grass` and `_split_flat_grass()` pulls them out onto
  a FLAT material, so they never reach the atlas or the bake at all. Same
  mechanism that keeps the block's letter faces perfectly cream. Grass at
  142 px per metre wants a flat colour anyway.

## 3. The terrain's colour had no cause

The old field was absolute height plus three sine waves, and a 0.09 wash on
top. In a play area deliberately kept within 0.35 m of level, absolute height
returns the same answer everywhere -- so the sines were doing all the work,
and smooth noise over a whole field reads as smoke. The wash made it worse: at
0.22 it was the loudest thing on the ground.

The colour comes off the land now, in order of how much each matters:

- **`local_relief()`** -- height against the average of the ground 2.8 m
  around it, not against sea level. A crown drains and burns off pale; the
  hollow beside it holds water and stays dark; they can be a metre apart on
  ground that is level overall. This is the dominant term.
- **slope** -- a steep face has thin soil and goes pale and strawy.
- **shade** -- ground against a wall, a hedge, a building or under a canopy
  stays dark and lush. Driven off the actual positions of those things.
- **grain** -- a little break-up, LAST, so none of the above reads as a band.

`wash` dropped 0.22 → 0.09. The ramp also widened: the dry stop is strawier
(0.65) and the damp stop deeper (0.37), so the variation is in HUE and not
only in tone.

## 4. The garden was too full and the middle too tall

Nothing but the bean frame stands over 0.26 m now, and there is bare earth
visible between every row -- a row is read from its GAPS as much as from its
plants. Front to back, low to tall:

- **carrots**, 11, dead straight and evenly spaced, with the orange shoulder
  of the root breaking the soil. Two centimetres of orange is the entire
  reason anyone can tell what the row is.
- **onions**, 9, pale bulbs with upright straps.
- **cabbages**, 6, moved to the BACK and at half their old size. They were in
  the middle at full size and the rows stopped reading as rows.

The kitchen garden is also the one place in the scene allowed to be regular,
because it is the only thing a person measured out. Everything else leans.

## 5. The barrel flowers were lumps

A green cushion with five small coloured cushions sitting in it reads as a
leafy blob with pink bits. `_flower()` builds the three things a flower
actually needs -- scalloped petals, a contrasting centre, and a stem -- and
the heads stand clear ABOVE the foliage at varied heights instead of nesting
in it.

## On the triangle budget

He asked what it meant. It meant nothing: `budget_tris` only prints a warning,
enforces nothing, and the numbers were guesses. All seven assets together are
about 52,000 triangles, which no GPU made this century notices, and **69% of
the 8 MB download is texture, not mesh**. The budgets are reset to catch a
runaway rather than to nag, and the number worth watching in each report line
is the kB.

He has also said explicitly not to worry about download size at this scale:
the Godot wasm is already 37 MB, so the whole asset set is a ~20% swing on a
download the engine dominates.

# The smallholding — fences, rows, barrels, a scarecrow — 2026-11-02 (later)

The world was the weakest of the five and he said so. This pass makes the
place look LIVED IN. It is a seventh asset, `explore/foundation_garden.glb`,
built by `build_garden()`, plus wildflowers folded into `props`.

Note on the earlier instruction: "do not simply add lots of decorative props"
is not contradicted here. That note was about substituting props for
world-building when there was no world yet. The land, the way and the
boundary exist now, so things standing on them have somewhere to belong --
and the test for each one is narrower than the Shire test was: does it say
somebody LIVES here and grows things. A fence encloses, a row is planted, a
barrel catches water off a roof, a scarecrow is there because the crops are
worth defending. Nothing is scatter.

## What is in it

- **A low picket fence** round the kitchen garden, with a gateway gap, plus a
  short second run beside the cottage. 0.66 m against a 1.35 m Chuck: a fence
  at his shoulder walls the garden off visually, one at his hip encloses it
  and still lets the rows read over the top.
- **Three crop rows** -- cabbages, a leaf/leek row, a drill of sprouts -- and
  a **bean frame** of crossed poles with beans climbing it. The frame is the
  only diagonal in the entire scene, which is most of why it reads.
- **Two rain barrels** with flowers spilling out: one under the cottage eave
  where the water actually comes off, one inside the garden gate where it
  would actually be used. The iron hoops are PAINTED, not modelled -- the
  lathe profile carries two deliberately short steps so a height test with
  `repaint_faces` stamps exactly those rings for nothing.
- **A scarecrow**, 1.62 m, deliberately taller than Chuck. Post, cross-arm,
  stuffed shirt, sack head with button eyes and a stitched mouth, a battered
  lathed hat, and straw bursting from the cuffs and hem. Arms straight out
  and a slumped head, so its silhouette can never be confused with Chuck's.
- **Wildflowers in clumps** across the meadow, rejected if they land on the
  path or inside the fence, each with grass around it.

## ⛔ Five things that each cost a render

- **`press` takes a WORLD plane.** `press(head, "Y", plane=-0.13, ...)`
  flattened the scarecrow's face toward world y = -0.13 instead of toward its
  own front, so standing anywhere but the origin turned the sack head into a
  cone. It needs `plane=y - 0.145`.
- **The scarecrow was sited three times.** Garden far corner: behind the tree
  canopy from the gameplay camera, completely invisible. Back-left: merged
  into the cottage plaster. It needs open grass behind it, which is left of
  centre and forward of the bean frame.
- **The second fence run fenced Chuck out of his own house.** Drawn as a
  dogleg it crossed the path stones outside the front door. It has to stay
  east of the way.
- **A flower head is a `pad`, not a `cushion`.** The tree needed masses
  because foliage has a body; a flower head is a lens. Cushions put props
  9,500 triangles over budget for detail invisible at 142 px per metre --
  24 triangles against 126, for a better shape.
- ⭐⭐ **A thin blade of grass BAKES BLACK.** The gouache recipe runs
  ao_strength 0.68 and edge_dark 0.20, and on a 19 mm tapering tube standing
  in a clump almost every point is either self-occluded or on a concave
  crease, so the two terms stack and crush the whole blade. Every tuft in
  three rounds of renders read as a black spike. There is one bake recipe per
  ASSET, so it cannot be fixed per object -- the fix is to start the base
  colour well above where it should finish: sunlit green on the top AND the
  middle, deep green only on the undersides, and a slightly fatter blade.

## Also in this pass

The tree moved to (3.95, 0.75); at (3.35, 1.30) its canopy sat over the
garden's fence corner.

## Cost

| | tris | texture | glb |
|---|---|---|---|
| garden | 13,506 | 1024 | 1,407 kB |
| props | 19,344 | 1024 | 1,535 kB |

⚠️ Props is 19,344 against a 16,000 budget and the warning is left in
deliberately. The overage is the drystone wall (63 stones) plus the tufts.
These are REVIEW assets; shipping wants the wall instanced from one stone and
the tufts cut to the ones the camera actually passes. The garden is a
separate asset from props for a texture reason rather than an organisational
one: `atlas_unwrap` packs by surface area into ONE 1024 sheet, so folding the
garden into props would halve the texel density of the wall and path stones
along with it.

# Foundation pass — Chuck redesigned, the world built — 2026-11-02

The hybrid set was approved as a DIRECTION with five notes. This pass answers
those five and nothing else. `hybrid.py` is untouched and still builds the
approved set; this is `art_src/explore/foundation.py`, which imports it for the
palette and the measured lettering constants. Nothing is committed, the
shipping game is untouched, and all five suites still pass.

Review: `art_src/review/foundation_scene.png`, `_chuck`, `_cottage`, `_block`,
`_tree`. Every one is IN SITU -- same world, same terrain, same light, camera
moved in. "The scene feels disconnected" is not a question a turntable on a
grey backdrop can answer.

## 1. Chuck — a character design pass, not a retexture

Luffy crossed with Mowgli, resolved into five decisions:

- **The hat is the identity.** A wide straw brim is the one silhouette no
  asset pack ships, it reads at any size, and on a game called Phonics FARM it
  is earned rather than applied. Lathed from a drawn profile -- crown dome,
  hard turn at the brim line, brim falling away and LIFTING at the rim so the
  edge catches light as a line all the way round.
- **2.9 heads tall**, where phase 1 was about 3.6. Head slightly wider than
  the shoulders, oversized hands and feet. A character averaged toward
  realistic proportion is what "still feels generic" means.
- **Bare feet, bare chest, open vest** -- Mowgli's half. Skin stays the
  largest single colour on him, so the vest red and the straw read as accents.
  The vest is modelled open (two front panels, a back panel, two straps), not
  painted open, so the silhouette carries it.
- **The face is a plane**, pressed flat, tapered to a chin, swollen at the
  cheeks. Big round eyes set WIDE with a highlight, brows thin and angled up
  and out, and a wide open grin with a tooth line.
- **Glasses are gone.** They were the previous Chuck's one distinguishing
  feature, so this is the reversible decision in the pass: `GLASSES = True` in
  `foundation.py` brings the rims and bridge back in the new face's geometry.

Three things were measured rather than chosen, and each cost a render:

- ⛔ **The crown radius is a CLEARANCE.** The hair cap is 0.462 across, so the
  first hat at crown radius 0.172 was swallowed by it and rendered as a black
  dome with a khaki ring round it -- a beanie. The crown has to be wider than
  the hair it sits on.
- ⛔ **A grin is a CURVE.** The first mouth was a wide flat lozenge with a
  cream band across it and read as gritted teeth on an angry child -- which,
  under brows angled up and out, is the wrong face entirely. Swept along an
  arc, thick in the middle and thin at the lifting corners, it reads as a
  smile at any size.
- ⛔ **The hat brim tilts BACK 20 degrees.** Not styling: at the game's
  30-degree camera pitch a level brim puts the whole face in shadow and the
  expression -- the point of the pass -- is lost.

## 2. The tree — volume, with the approved silhouette kept

`forms.pad` is a LENS: a drawn edge with almost nothing behind it, which is
right for cut paper and wrong for foliage at a close-up. The new `cushion()`
generator stacks wavy rings and lofts them into a MASS: the scalloped edge
that was approved survives, and there is a real domed body behind it. Scallop
phase rotates as the rings rise, so the lobes spiral rather than stacking into
a lathe. Two swells and a dent per mass break the revolve for no extra
triangles.

⛔ Six masses of radius 0.7-0.84 spread across a 2.7 m span at nearly the same
height is a flat umbrella -- a thicker version of the pad stack. Narrower
masses lifted up the trunk rebuild the vertical fan. The canopy is now 1.9 m
wide over 3.1 m tall, where the first attempt was 2.7 wide over 2.95.

The three canopy greens were also re-spread from 0.24-0.53 to 0.21-0.59, and
the TOP colour now varies per layer. Giving every mass the same light top made
the whole canopy one value, which is how a layered form loses its layering.

## 3. The cottage — architecture, not trim

Terracotta pantiles as real COURSES: each course emits two loft stations, its
own plan and the same plan lifted by the lap, so there is a riser and a shadow
line all the way round at every course. The eave course is scalloped, so the
bottom edge is a row of pantile ends. Plus a battered base on a stone plinth,
two dormers of different sizes, a coursed leaning chimney, rafter ends under
the eave, stone lintels and sills, glazing bars, and a window box.

⛔ **TWO numbers decide whether this is a roof or a dome**, and the first
build got both wrong. DEPTH must stay nearly constant -- shrinking width and
depth together hips the roof in from all four sides, which with rounded
stations is a bulbous cap, and that is exactly what rendered: a mushroom with
faint steps on one side. CORNER RADIUS must be tiny -- at 0.16 the stations
are lozenges and the loft between them is a curved shell with no planes in it.
At 0.05 the same 32 points describe a near-rectangle and `facet` keeps the
planes.

⛔ **The door stands PROUD of its surround.** In the first build the stone
arch sat 0.055 in front of the door and was 0.16 wider, so it did not frame
the door, it covered it -- the entire blue of the front elevation vanished
behind a grey slab.

⛔ **The dormers took three attempts and each failure was a different kind.**
(1) They sat on the -Y face; once the roof gabled that face became a vertical
gable end and both ended up entirely inside it, rendering as nothing at all.
(2) Reseated on the -X slope with a 0.66-deep box centred on the slope line,
so half of each hung off into the air -- a red shed floating beside the
chimney. (3) Still the wrong plane: the ridge is pushed +0.62 so -X is the
long shallow one, and the reasonable-sounding conclusion was that a dormer
belongs there -- but the camera sits at +X/-Y and looks back along it, so -X
is the FAR slope and both read as ridges peeking over the roofline.

They are on +X now, the short steep plane the gameplay camera actually sees,
seated by a 1.30-deep box running from just outside the slope back INTO the
roof mass where the far end is swallowed. `roof_edge_x(z, side)` reads the
plane straight off `ROOF_COURSES`, so this survives the next time those
numbers are tuned. The rafter ends moved for the first reason: they were
poking out of a gable, which is simply wrong.

## 4. The world — a field, not a plane

Rolling terrain, a sunken hollow way, a drystone wall, four hedges, a dug
vegetable bed, and grass at every point where an object meets the ground.

⛔ **"The play area has to stay flat" was an ASSUMPTION, and it was wrong.**
It was never checked, and the first terrain was built masked to 10% relief
inside 5 m because of it. The engine walks slopes today:

- `player.gd` is a `CharacterBody3D` with gravity and `move_and_slide()`, and
  reads `is_on_floor()`. Nothing anywhere pins Y.
- `player.gd::ground_height()` already raycasts DOWN for the drop point, and
  its own comment says so: *"Phoneme Village has raised terrain, so a drop
  cannot assume ground Y = 0."*
- `village/phoneme_village.tscn` already ships a `Terrain` StaticBody3D with a
  terrace, a lookout and two ramps, each with its own collision shape.
- `fixed_camera.gd` tracks `target.global_position` in all three axes and is
  orthographic, so walking uphill just moves the frame.

So the play area ROLLS now: `PLAY_RELIEF` 0.35 plus an always-on `_gentle()`
undulation. Measured over r < 5 m: height range **0.352 m**, maximum slope
**7.8 degrees**.

Gentleness is still required, for three reasons that ARE measured rather than
assumed:

- `can_reach()` raycasts from +0.6 to +0.4 over at most 1.65 m on collision
  mask 13, which **includes the ground layer** -- a rise of about half a metre
  inside that span would make a block unpickable;
- `pedestal.gd` stretches a 0.5 m `$Base` straight down and lands it back on
  the ground, so a pedestal wants LEVEL footing;
- blocks are cubes, and a cube on a slope reads as a mistake.

7.8 degrees clears all three with room. Buildings still get a level pad.

The hills are seven hand-placed lobes, not noise -- a landscape made of noise
has no composition.

`paint_field()` blends a ramp of palette colours across a form by an arbitrary
field. `paint_by_normal` can only ask which way a surface faces, which is the
right question for a canopy and the wrong one for a meadow: a field's colour
comes from height, slope and distance to the path. Interpolating per corner
keeps it continuous -- `repaint_faces` would stamp whole 0.8 m quads and the
terrain would read as a patchwork of squares.

Four things that had to be rebuilt:

- ⛔ **The wall is built from STONES, not a swept band.** Two `ribbon` courses
  are cheap, correct in plan, and rendered as a smooth white snake lying in
  the field. A drystone wall is read entirely by the joints between its
  stones, and a continuous surface has none.
- ⛔ **The wall line was set OUT from the path.** At 1.4 m off the way it cut
  straight through the block row with Chuck standing in it. A field boundary
  belongs at the edge of the field, and the play area is the field.
- ⛔ **The vegetable bed is PAINTED INTO the terrain.** Two attempts at a
  ribbon of earth both rendered as a wooden boardwalk with shrubs on it,
  because a strip of geometry over grass has an EDGE and a dug bed does not.
- ⛔ **wash_scale 0.11 put three lobes across a 26 m field**, which is
  indistinguishable from a flat fill at gameplay framing -- the first render
  still showed exactly the uniform green this pass exists to remove. 0.95 is
  roughly a one-metre mottle: visible in frame, still far under the texel
  density. The colour field also needed three octaves; a single long sine put
  one patch boundary across the whole play area.

## 5. The block — proportions and lettering untouched, faces inset

0.8 cubed, exponent 5.2, the 0.640 plaque, the five plaque node names and the
single shared flat face material: all exactly as approved. What is new is a
moulded wooden rim so the cream reads as inset, and four shallow gouges of
grain in the body.

⛔ **The rim is seated on the superellipsoid's own surface, point by point.**
The approved plaque is 0.640 across a 0.800 block, leaving 0.080 of wood, and
the squircle has already curved away by then -- at 0.378 from the centre of a
face the surface has dropped 0.100 below the face plane. A rim drawn as a flat
ring at one depth floats off the block everywhere except dead centre, by a gap
bigger than the rim itself. `block_surface_depth()` solves the superellipsoid
for the outward axis so the rim grows out of the face instead.

The cream CANNOT move back: `plaque_centre` puts it at 0.413 because the
Label3D in `block.tscn` sits at 0.4178 and reads that surface as its ground.
So the wood comes up around it instead, by 0.014 -- enough for a shadow line
at 142 px per metre, shallow enough that it still reads as wood rather than as
a well.

⚠️ The rim takes the block's visual extent from 0.826 to 0.854 against a
0.80 collision box. Hybrid was already 0.826 over 0.80; this adds 14 mm a
side. Unavoidable given the Label3D contract, and worth knowing before blocks
are ever placed touching.

## ⭐⭐ The lettering constants in block.tscn are wrong, by a measurable factor

Measured off Fredoka in Blender, a-z, glyph outlines only:

| | recorded in hybrid | measured now | ratio |
|---|---|---|---|
| a-z ink span | 0.894 em | **0.744 em** | 1.203 |
| 'f' top above the text origin | +0.320 em | **+0.266 em** | 1.203 |
| 'y' bottom below it | -0.575 em | **-0.478 em** | 1.203 |
| ink centre off the origin | -0.1275 em | **-0.1059 em** | 1.203 |

All four are over by the SAME 1.203, which is a systematic scale error in the
original measurement rather than four separate mistakes. The span is pure
glyph outline and depends on no font metric at all, so it is the one number
that cannot be explained away by Godot and Blender disagreeing about where a
line box sits.

Two consequences:

1. `block.tscn` lifts every label **0.0847** where **0.0703** is correct. The
   ink currently clears the plaque by 0.0585 at the top and 0.0873 at the
   bottom -- it sits 14.4 mm high, which is the whole of the over-lift.
2. **The letters can be much bigger.** The ink fills 77% of the plaque, not
   the ~95% the earlier pass believed. Centred properly with a 0.030 margin
   the font goes 83 -> about **97**, which is +17% x-height over the hybrid
   block and +27% over the shipping one.

⛔ `block.tscn` was NOT changed. The span proves the headroom, but the OFFSET
depends on Godot's line box matching Blender's, and `tests/capture.gd` cannot
verify it on this machine. The honest next step is a web export in Chrome
spelling `f g y p a j`, which is the project's one working validation path.
The review render uses the corrected centring, so what is in
`foundation_block.png` is the fixed lettering at the approved font size 83.

## The lighting changed, and it is a result rather than a presentation choice

The study rig was a 5-degree sun at energy 3.1 against a flat grey background,
which is a point light in all but name. `render_foundation.py` uses a
7-degree sun (the shadow-edge fix), a physical sky so shadows fill with blue
while lit faces stay warm, and one low cool fill.

⛔ Two over-corrections, both caught in a render. The fill started at energy
110: softening shadows by flooding them with a big cool source REMOVED the
shadows and took the frame's warmth with it. It is 24 now -- the sun angle
softens an edge, the fill only keeps detail in the shade. And AgX at "Base
Contrast" turned terracotta into salmon, straw into khaki and warm plaster
into grey: the palette's values survived, its hues did not. "Punchy" restores
the chroma without giving back the clipped highlight.

⛔ **Blender 5 renamed the physical sky models.** What every tutorial still
calls "Nishita" is `MULTIPLE_SCATTERING`, and the old string is not an alias,
it raises. `dust_density` is also gone.

`s_wall` was dropped 0.84 -> 0.78 for the same reason: sitting on the palette
ceiling it rendered as grey-white and the warm plaster stopped being a colour.
Every relationship in the palette is intact -- the letter face at 0.90 is
still the lightest thing on screen by a wide margin.

The GAME's lighting needs the same three moves in Godot --
`DirectionalLight3D.light_angular_distance`, a `WorldEnvironment` with a sky
and ambient, and one low fill -- and none of them are in the engine yet. These
renders show the ASSETS under correct light; they are not a claim about the
shipping scene.

## ⛔ A latent bug in sb_lib, FLAGGED not fixed

`meshtools.drop_to_floor` writes `obj.location.z`, and `obj.matrix_world` does
not pick that up until the depsgraph is evaluated -- so `meshtools.bounds`,
which reads `matrix_world @ v.co`, silently returns LOCAL coordinates
afterwards. Two drops in a row then correct for the same offset twice and the
object floats by exactly the height it was lifted.

That is why the tree hovered 41 mm above the ground and Chuck did not: Chuck
runs `forms.facet`, whose Blender operators force an evaluation, and the tree
runs none. `foundation._scale_to_height` calls `bpy.context.view_layer.update()`
around its bounds reads.

`sb_lib/meshtools.py` was deliberately left alone -- shipping assets and the
three study directions were all built through that code path, and changing it
would move geometry that has already been reviewed. Worth fixing properly
before the next production run.

## Cost

| | tris | texture | glb |
|---|---|---|---|
| chuck | 4,580 | 1024 | 982 kB |
| tree | 4,566 | 1024 | 1,039 kB |
| cottage | 3,674 | 1024 | 1,195 kB |
| block | 3,714 | 512 | 409 kB |
| terrain | 2,048 | 1024 | 1,390 kB |
| props | 11,228 | 1024 | 1,155 kB |

Props is the outlier and it is the drystone wall: 63 stones in three staggered
courses. Shipping would decimate it or instance one stone. Terrain is only
2,048 triangles but 26 m across a 1024 atlas is about 33 px per metre against
a screen density of 142, which is why its bake recipe carries NO grain and no
streak -- any high-frequency term at that density is aliasing, not texture.

## What I would still change

Judged against the five notes: Chuck, the tree, the cottage and the block all
land. **The world is materially better and is still the weakest of the five.**

- (Answered 2026-11-02 by the "Edges in the ground" pass above -- the mown
  line, the worn tracks and the crisp path edge. What is still missing is a
  hedge shadow lying across the grass, which wants the hedges' footprints in
  the shade sources rather than just their centres.)
- The hedges are still smooth cushions. Deepening the lobes helped the
  silhouette; they want actual leaf clumps, which means the `cushion`
  generator nested one level.
- The drystone wall is regular: three staggered courses of similarly-sized
  stones along an even line. It needs size outliers and a few gaps.

None of those is blocking; all three are the same hour of work.

## 👉 Making the rolling terrain real IN GODOT

The renders show it; the engine does not have it yet. What it takes:

1. **Collision.** `scenes/main.tscn`'s ground is a flat `BoxShape3D`. The
   terrain is a REGULAR 33x33 grid straight out of `terrain_height(x, y)`, so
   the right shape is a `HeightMapShape3D` fed that array directly -- cheaper
   and far more robust than a trimesh, and it needs no mesh import step.
   A `ConcavePolygonShape3D` off the GLB also works; 2,048 triangles is
   nothing for static collision.
2. **Seat everything that stands on the ground.** Pedestals, blocks, levers
   and trees are placed at authored Y in the .tscn and would float or sink.
   A `@tool` script that raycasts each child down onto the terrain in the
   editor is the pattern already used by `tools/village_spawn_probe.gd`.
3. **Level pads under pedestals and the lever**, for the stretch-a-fixed-base
   reason above. Same trick `terrain_height` already uses for the cottage.
4. **Choose the terrain's collision layer deliberately** so `can_reach()`'s
   mask 13 does what is wanted. Blocking reach over a real hill is correct;
   blocking it over a 20 cm swell is not.

The 40x40-per-clearing field and the single outer boundary are box walls and
are unaffected.

## Still not done

No rigging and no animation: the walking avatar in `scenes/hybrid_slice.tscn`
is still phase-1 Chuck, and the new Chuck is a static model. Nothing is wired
into a Godot scene -- there is no `foundation_slice.tscn`. The village is
untouched. Adopting the new Chuck means one capsule-height line in a new chuck
scene; `player.gd` is unchanged.

Git: nothing committed, nothing pushed.

# The chosen set — D2 tree + D3 cottage + D1 block, unified — 2026-11-01 (later still)

Picks from the direction study, made per-object rather than per-direction:
tree from D2, cottage from D3, block from D1, Chuck delegated (D3 taken).

**The risk that created, and what was done about it.** Three objects from three
studies means three surface languages — flat-shaded faceting, painterly ink edges,
soft clay — plus three palettes. That would read as three games sharing a field. The
FORMS are kept exactly as chosen; everything else is unified in `art_src/explore/hybrid.py`:

- ONE palette. `palette.extend` overwrites the study entries the builders already ask
  for by name, so `d2_storybook` and `d3_sculptural` need no edits at all.
- ONE bake recipe, between D3's clean flat fields and D2's painterly wash: real wash,
  little grain, `edge_dark` 0.20 (D2 was 0.38, D3 was 0.07).
- Shading angle still varies, because it is a property of what a thing IS, not of the
  art direction: cottage 10 degrees (cut, faceted), block 18 (moulded), foliage 30.

**The lettering, which turned out to be measurable rather than a matter of taste.**
Measured from Fredoka: across a-z the glyph ink spans 0.894 em and is NOT centred on
the text origin — it runs +0.320 em at the top of 'f' to -0.575 em at the bottom of
'y', because Label3D centres the LINE BOX (ascent + descent) and not the ink.

On the SHIPPING block that means every descender — g j p q y — hangs 0.062 units
BELOW the plaque, onto the wooden frame, and the ink already fills 95% of the plaque.
So the choice of block form barely affects letter size; the plaque width and the label
offset do.

Fixed in `storybook/hybrid/block.tscn`: font_size 76 -> 83 and every Label3D lifted
0.0847 units, on a plaque widened 0.575 -> 0.640. x-height goes 0.287 -> 0.313 units,
9.2% larger, with 'f' and 'y' clearing the plaque edge by 0.023. Verified in a browser
with blocks spelling g y p a j.

A 0.660 plaque at font 86 was built first and gives +13%, but leaves a 0.07 wooden
frame that reads as a sugar cube rather than a toy. Two constants in `hybrid.py` if the
lettering should win over the frame.

**Assets** in `assets/storybook/explore/hybrid_*.glb`, Godot scenes in
`storybook/hybrid/`, composed in `scenes/hybrid_slice.tscn` (walkable, shipping camera,
live AlphabetBlock instances so the letters are generated at runtime).

| | tris | texture |
|---|---|---|
| tree (D2 form) | 1,760 | 1024 |
| cottage (D3 form) | 724 | 1024 |
| chuck (D3 form) | 3,044 | 1024 |
| block (D1 form, re-proportioned) | 2,644 | 512 |

Review: `art_src/review/study_hybrid.png`, `hybrid-in-engine.jpg`.

**Still not done:** no rigging or animation (the walking avatar in the slice is the
phase-1 Chuck); no environment work; the village is untouched. Adopting this set means
changing the capsule height in the new chuck scene for the 1.35 m figure — one line, in
a scene that is not the shipping one.

**Trap worth keeping:** `render_study.py` imports `hybrid` ONLY on demand. Importing it
at module scope re-points the study palettes onto the house family and silently
re-renders the d1/d2/d3 sheets in the wrong colours — which it did once.

Git: nothing committed, nothing pushed.

# Direction study — three visual languages — 2026-11-01 (later)

Phase 1's vertical slice was reviewed and the art direction was REJECTED, correctly:
it still read as an asset pack. The models had moved from Kenney to Blender but the
vocabulary had not — boxes, cylinders, cones and spheres with better textures. The
tree was the clearest case: a trunk plus a cluster of spheres.

So this is an exploration, not more production. Three genuinely different visual
languages applied to the same four subjects — cottage, tree, Chuck, alphabet block.
Nothing is wired into the game; phase 1's slice and the shipping game are both intact
and still pass.

**New: `art_src/sb_lib/forms.py`.** Not a primitive in it. `lathe` (revolve a drawn
silhouette), `loft` (bridge a stack of outlines, so a plan can change with height),
`sweep` (tube along a path with varying radius), `pad` (scalloped lens), `superform`
(superellipsoid), `ribbon`, plus `press` / `dents` / `swell` / `facet` / `jitter_verts`.
This is what the earlier failure actually came down to: the only shapes available were
asset-pack shapes.

**Three directions**, in `art_src/explore/`, documented in `art_src/explore/README.md`:

| | D1 handcrafted | D2 storybook | D3 sculptural |
|---|---|---|---|
| canopy | pressed pads on visible branches | layered painted pads, fanned | interlocking faceted masses |
| cottage | bulging lofted walls, scalloped thatch | tall, jettied, leaning 2.4 degrees | ridge pushed 1.14 off centre, lean-to |
| shading | smooth 54 degrees | 33 degrees, edge_dark 0.38 | FLAT, planar-decimated |

Review images in `art_src/review/`: `study_d1/d2/d3.png` (all four subjects in one
frame per direction), `lineup_tree/cottage/chuck/block.png` (one subject across all
three), `study-in-engine.jpg`.

**In Godot:** `scenes/direction_study.tscn` — all three side by side, 13 units apart,
walkable with the real controller under the shipping camera. The blocks are live
AlphabetBlock instances, so the Label3D letters are generated at runtime exactly as in
the game. `tools/check_direction_study.gd` asserts the contract holds in all three.

**Deliberately not done:** no rigging or animation (three rigged characters before one
is chosen is wasted work — the walking avatar is phase-1 Chuck, who is already rigged);
no environment work; the village is untouched.

**Chuck is now 1.35 m, up from 1.18**, because he read as too small. Adopting any
direction means changing the capsule height in the new chuck scene — one line, in a
scene that is not the shipping one. `player.gd` is untouched.

**Correction carried into the repo:** the earlier claim that the cream/ink value gap
was a low-vision accessibility requirement was WRONG and has been removed from
`palette.py`, `painter.py`, `build_block.py`, `build_meadow.py` and the README. High
letter contrast is kept as ordinary legibility for five-year-olds.

**Measured, worth keeping:** `albedo_color` on a plain StandardMaterial3D is consumed
as LINEAR in this project's Compatibility setup, exactly like the GLB albedo textures
are. A flat material given sRGB numbers renders as washed out as an unfixed texture.
Scene-authored colours therefore need linear values.

Validation: all five existing suites pass, `tools/check_storybook.gd` (phase 1) passes,
`tools/check_direction_study.gd` passes, Web export succeeds and was viewed in a real
browser. `project.godot` was flipped to the study scene for that export and restored,
verified clean with `git diff`.

Git: nothing committed, nothing pushed. Only PROGRESS.md is modified; everything else
is new untracked paths.

# Painted Storybook — visual reinvention, phase 1 (vertical slice) — 2026-11-01

A bespoke art direction built alongside the game, NOT wired into it. `scenes/main.tscn`,
Phoneme Village, CVC Land, every original asset and every Kenney asset are untouched and
still run. Nothing is committed or pushed. Awaiting review before phase 2.

**New Blender pipeline** — `art_src/` (`.gdignore`d; read `art_src/README.md` first).
Parts are coloured by palette NAME as vertex colours, joined, UV-atlassed, surfaced with
a Cycles "gouache" shader (broad wash + paper grain + brush streaks + ambient occlusion +
pointiness edge light) and BAKED to one texture per asset. What reaches Godot is one
material, one base-colour texture, no custom shader, no transparency, metallic 0.
Blender is needed only to rebuild art; the committed `.glb` files are the contract, so
GitHub Actions is unchanged and still never needs Blender.

**Seven assets** in `assets/storybook/`, with Godot scenes in `storybook/`:

| asset | tris | texture | notes |
|---|---|---|---|
| block | 1,128 | 512 | 0.8³, bottom origin, Cube + 5 named faces |
| chuck | 4,834 | 1024 | skinned, `idle` + `walk`, 1.18 m |
| cottage | 4,600 | 1024 | collision is 2 box shapes, kept off the mesh |
| tree | 2,052 | 1024 | |
| pedestal_base / _top | 732 / 504 | 512 each | two GLBs — see below |
| path_stone | 152 | 512 | |
| meadow | 1,058 | 1024 | slice-scoped ground patch only |

Slice scene: 30,848 triangles, 9 distinct materials.

**Nothing in gameplay was rewritten.** The storybook scenes REUSE `alphabet_block.gd`,
`player.gd` and `pedestal.gd` unchanged; `tools/check_storybook.gd` asserts the contracts
those scripts depend on (face node names, the duplicated face material, 0.8 block body,
runtime Label3D letters, `idle`/`walk` by exact name, CarryAnchor, the 1.16 capsule, the
0.62 snap height, and that SnapPoint does NOT move during the sound lift).

Three things that look like odd choices but are decisions:

- **The pedestal ships as TWO GLBs.** `pedestal.gd` raises a sounding letter by stretching
  `$Base` (`scale.y = 1 + lift/0.5`, node moved up by `lift/2`) and translating `$Top`.
  That only lands the base back on the ground if it is exactly 0.5 m tall with its origin
  at its own centre, and the cap must be a separate node or it is stretched too.
- **Every storybook scene carries a `SurfaceFix` child.** Godot's glTF import does not mark
  these GLB-embedded base-colour textures as sRGB, so the Compatibility renderer treats
  them as already-linear and everything renders about a gamma too bright. MEASURED: the
  baked PNG holds the right sRGB bytes, a flat `albedo_color` material rendered identically
  to the textured mesh, and in the browser the meadow read (254,255,179) against the
  shipping game's (145,190,115) with roof, plaster and block faces clipping to white.
  With `albedo_texture_force_srgb` the same measurement reads (149,203,89). Before/after:
  `art_src/review/slice-before-srgb-fix.jpg` and `slice-in-browser.jpg`.
- **Letters are still generated at runtime** and are NOT baked into any texture. Fredoka's
  lowercase `a` and `g` are already single-storey, so the existing font was kept.

**Validation.** All five existing suites pass. `tools/check_storybook.gd` passes. Web
export succeeds. The slice was reviewed in a real browser via a temporary export whose
main scene was flipped to the slice; `project.godot` was restored and verified clean with
`git diff` each time.

**Open and NOT done:**

- `tests/capture.gd` HANGS on this machine. `await RenderingServer.frame_post_draw` never
  fires under Godot 4.5.2 here, and viewport readback also comes back blank, so rendered
  captures were replaced by Blender reviews (`art_src/render_review.py`) plus real browser
  screenshots. Not investigated further; `capture.gd` was left untouched.
- **The web pck grew from 1.8 MB to 6.0 MB**, almost entirely the seven baked textures.
  The wasm is already 38 MB so this is about 11% on total download, but it is real. The
  lever is texture size: dropping cottage/tree/meadow to 512 would give back roughly 1.9 MB.
- Touch, mouse and Xbox controller were NOT re-tested on hardware. `ui/touch_controls.tscn`
  is in the slice so it can be, and no input code was changed.
- Classroom-device frame rate was not measured.
- The slice's ground is a mesh patch; mounding is 5 cm over 26 m against a flat collision
  box, so Chuck floats or sinks by up to 5 cm. Fine at this camera, wrong for a real level.
- Annette, the sound lever, the river, the bridge and the village buildings have NO
  storybook equivalent yet. That is phase 2 and is deliberately not started.

Git: nothing committed, nothing pushed. New untracked paths only — `art_src/`,
`assets/storybook/`, `storybook/`, `scenes/storybook_slice.tscn`,
`tools/check_storybook.gd`. No existing file was modified.

# Wooden-toy visual pass — 2026-10-04

The owner approved softer lighting, ground/path improvements, and a much more distinctive
wooden-toy village. Pedestals explicitly left alone. Implemented locally, not deployed.

- Warm daylight with a 52-degree sun, reduced direct/ambient energy, lighter short
  shadows and less fog. Gameplay camera framing is unchanged.
- `environment/meadow.gdshader` adds subtle world-space meadow variation, sandy
  connected lanes and an oval at the word-building station. The riverbank shares
  the meadow shader; terrace/lookout keep separate green shades without paths.
- Runtime material overrides give stepping stones, imported props and forest
  foliage a coordinated matte palette, including the Web export.
- Six original static scenes in `village/buildings/`: windmill, bakery, clock house,
  bookshop, flower shop and workshop. Painted roofs, chamfered timber, shutters,
  awnings, carved symbols, flower boxes and north-street bunting. North buildings
  face south; west buildings face southeast (-145 degrees), toward the green and
  visible from the fixed camera. `Cottage1..6` roots remain for existing tools.
- `tools/build_toy_village.py` authors those scenes and the shared original
  `assets/toy_village/beveled_cube.obj`. No downloaded assets or new dependencies.
  Re-running overwrites those generated assets, never the village layout.
- Slightly widened cottage colliders and regenerated all 36 explicit spawn markers
  with `tools/village_spawn_probe.gd`, accounting for the new visual silhouettes.

Validation: clean final editor import and Web export. All five existing suites
passed; village was rerun after the final building orientation/spawn changes and
passed, including visibility, ramps, prompts and board refresh. Fresh native
clearing/street/entrance/postcard captures inspected. Export loaded in headless
Chromium WebGL: no console/page errors, walking and camera follow visibly worked.
Real classroom hardware/performance and child readability were not retested.
The pre-existing village ObjectDB/resource-in-use exit warning remains; the
previously documented randomized drop-test flake was not changed.

Screenshots are direct engine/browser captures, never retouched. Original review
PNGs were copied from `/tmp` before modification. Both versions now live under
`visual-review/before/` and `visual-review/after/`, with `visual-review/index.html`
as a comparison page. This folder is ignored by Godot and Git. New capture option
`--village-postcard` uses a wider review camera only. README updated.

Git: preserved the earlier review note below. The owner reviewed the captures, approved
the result, and requested commit and push to GitHub. This visual pass is prepared
for `main`; the push triggers the existing test-and-deploy workflow. Local review
PNGs remain in the ignored `visual-review/` folder. `git diff --check` passes.

# Visual review — 2026-10-04

The owner asked to review status and discuss improving the appearance. No visual or
gameplay changes chosen or implemented. Fresh native captures reviewed:
`/tmp/phonics-clearing.png`, `/tmp/phonics-village-houses.png`, and
`/tmp/phonics-village-close.png`. Main discussion points: strong yellow/orange
lighting, heavy long shadows across letters, flat ground, bright stepping stones,
and simple pedestal geometry. These are observations, not an agreed work plan.

GitHub's latest test-and-deploy run for current HEAD `1502d40` succeeded on
2026-09-26 (run 36252604255). No test suites rerun for this discussion. All three
captures rendered; village-close logged an ObjectDB/resource-in-use warning at
exit. Working tree was clean on arrival; only this review note changed. No commit
or push. The previously documented intermittent village-test failure remains.

# Session handoff — 2026-09-26

## Annette's two clues, a silent village drop, a de-cluttered green, a counter

Five requested changes, all implemented, all five suites green, and the village
checked in a rendered capture (`/tmp/phonics-village-close.png`).

**Annette now shows where to look.** `village/annette.gd` (new, class
`VillageGuide`, attached to the `Annette` node) gives her two clues, both
deliberately weak:

1. She **turns to face** the letter she is asking for, every time she asks.
   `speak_prompt()` calls `annette.face(block.global_position)`.
2. On a **wrong answer** she **walks four or five steps toward** it —
   `annette.hint_toward(...)` from the wrong branch of `_on_block_picked_up`.
   The count is `randi_range(4, 5)` per hint so it does not look mechanical;
   a step is `step_length` 0.55 units, about one stride of the 1.6-unit model.

She is not a physics body, so the walk is hand-rolled: she steps along the
ground, raycasts DOWN for her footing (the village has three levels, so Y is
not 0), stops if a feeler ray hits a cottage or trunk on layer 1, and stops at
`standoff` 2.2 units from the letter — **she must never end up standing on the
answer**. `max_drift` 7.0 caps how far she can get from her post, and she walks
back home after every correct answer, when Chuck leaves, and instantly
(`snap_home()`) on a board refresh, so a long run of wrong answers cannot walk
her across the village. She also now plays `idle`/`walk` from the GLB; before
this she had no script and stood in the model's rest pose.

Every yaw in that script is a GLOBAL yaw. The village hangs off a
45-degree-rotated `Environment` node, so mixing local and global rotation
points her 45 degrees wide of the letter.

**A village block put down is now silent.** `AlphabetBlock.silent_drops`, set
on every block the village spawns. The bug it fixes: the block re-played its
own phoneme as it landed, and `play_sequence` stops whatever is playing — which
was Annette halfway through repeating her question. CVC Land leaves the flag
false, so every drop there still sounds the letter, and a village block placed
on a CVC pedestal still sounds too (only `put_on_ground` is gated). Both halves
are covered in `tests/village.gd`.

**`answered` now fires AFTER `found.append()`**, so a listener reading
`village.found` is not one letter behind. Nothing else depended on the order.

**Props removed from Phoneme Village** (scene edits only, no code):

| Removed | Was | Now |
| --- | --- | --- |
| The whole pumpkin patch | 12 pumpkins, 4 dirt rows, 10 fence sections | bare grass |
| Fallen logs (`log.glb`) | 3 around the campfire | 2, the symmetric pair |
| Leafy bushes (`plant_bushDetailed`) | 7 | 2 |

The owner chose each of those scopes. The pumpkin model "fails to translate on the
board"; 3 logs and 34 scatter props read as clutter. **Flowers were explicitly
kept** (all 20), and so were the 7 mushroom clusters — he ruled they are not
plants. `crops_dirtRow.glb`, `crop_pumpkin.glb` and `fence_simple.glb` are no
longer referenced by any scene; the files stay in `assets/kenney/nature/`.

**A found-letters counter.** `ui/found_counter.tscn` + `.gd`, a CanvasLayer
instanced in `scenes/main.tscn` after `TouchControls`. One number, top-left,
Fredoka to match the blocks, cream with a thin dark outline, 72% alpha, no box
and no animation on change. It **fades in only inside Phoneme Village** (the
new `presence_changed` signal) — CVC Land has no round to count and a stray "0"
over the lever game would be noise. It resets to 0 on a board refresh. The
digit is sized to about a sixteenth of the viewport height and both the size
and the margin are exported.

`presence_changed` is emitted BEFORE `_on_body_entered`'s early return, on
purpose: a capture script that starts a round by hand must still get the
counter on screen.

## Checks actually run

All five suites, repeatedly. `tests/village.gd` gained checks for: she faces
the letter she asks for; asking alone does not move her; a wrong answer walks
her at most five steps and TOWARD the letter; she never ends inside her own
standoff of it; a village block put down neither re-plays its letter nor
empties Annette's queue; a CVC Land block still sounds when put down; and the
counter's value, its fade in/out and its reset. The static no-hidden-letter
sweep now calls `annette.snap_home()` first — it measures the scene's own
props, and a hint walk could otherwise park her over a spawn point.

Rendered captures: `--village-close` (counter and both characters) and
`--village` (the patch is gone). Not checked on a touch device or a phone.

## Known, NOT introduced here

`tests/village.gd` is **flaky at roughly one run in ten, and was before this
work**. Diagnosed 2026-09-26; the cause is NOT what an earlier draft of this
note said.

The root cause is `Player.drop_block()` meeting a randomised board.
It tries 8 fixed spots in a ring 1.12 units around Chuck and, by design,
keeps the block if all 8 are obstructed ("If every nearby position is
obstructed, it stays in your hands"). The test puts Chuck 0.9 units from a
block that spawned at one of 36 shuffled markers -- and markers sit as close
as 1.51 apart -- then asserts the drop succeeds. Some layouts ring him with
blocks, the game correctly refuses, and the check fails. The game is right and
the test's assumption is wrong.

One failed drop reads as SEVEN failures, because Chuck can carry only one
block: he can never pick up the right letter, so the celebration, the poof,
the board count, the reported answer and the next prompt all fail behind it.
The signature is a `the wrong letter can be put down again` failure with six
others trailing it.

MEASURED, so it is not re-guessed: 400 board refreshes counting letters that
land within 0.5 of their old spot never once dropped below 19 of 23, so the
`moved >= 18` check is NOT the flake it was first blamed on. A single
standalone `(17 of 23 moved)` failure was seen at HEAD (`2209349`) and remains
unexplained; it carried no cascade, so it is a second and rarer thing.

This matters because `.github/workflows/deploy.yml` runs the suites before
publishing, so a flake can block a deploy that has nothing wrong with it.
The fix is NOT to seed the RNG -- that freezes one lucky layout and hides the
case. Teleport Chuck onto known-open ground before the drop, so the check
tests what it means to test. Not done, not requested.

Annette can, in principle, stand between the camera and a letter for the few
seconds of a hint walk. The standoff makes it unlikely and she walks back, but
the no-hidden-letter guarantee covers the scene's props, not her.

## Git

Not committed, not pushed. Working tree carries these changes plus the new
files `village/annette.gd`, `ui/found_counter.gd` and `ui/found_counter.tscn`.

# Session handoff — 2026-09-25 (b)

## Deployed, then confirmed on real hardware

Pushed `303a423` to `main`; the workflow ran all five suites, exported and
published. Verified the live URL itself serves the new build rather than
trusting the green tick.

The owner then played the live build and reported: the **resident Xbox controller
works**, **sound works**, and the **touch-screen controls work exactly as
intended**. That closes the two oldest open items in this file -- a physical
gamepad and a real multitouch device had only ever been simulated by
`tests/smoke.gd`, and every earlier handoff's "remain untested" line about them
is now superseded. Those older sections are left as written; they were true
when written.

Still untested: whether a **child** discovers the invisible drag control
without being told. Nothing on screen says "drag to walk".

Changes here are documentation only -- README's verification section and next
tasks. No game, audio, export or workflow changes.

# Session handoff — 2026-09-25

## Sunset light, an isometric camera, two alphabet rows, a laid-out village, and
## controls with nothing on screen

Five requested changes, all implemented and all five suites green.

**Sunset.** `scenes/main.tscn`'s WorldEnvironment now carries a ProceduralSky
sunset backdrop, a warm ambient-free palette split in two: a low key sun (24→28
degrees of elevation, `Color(1, 0.58, 0.3)`, energy 1.55) doing the warm work,
and a cool blue ambient plus a second shadowless `Skylight` DirectionalLight
filling the shade. The fill lights exist for READABILITY: the first warm pass
looked right and left blocks in roof shadow as dark navy squares, which is
useless in a classroom. Light fog (density 0.0018) adds depth; it is barely
visible at the game camera's 26-unit distance and only looks heavy in the
`--overview`/`--world` diagnostic captures, which sit much further back.
Shadow bias is 0.09 with normal bias 2.0 — a low sun grazes flat surfaces and
the bridge deck had acne at the defaults.

**Camera.** `pitch_degrees` 18 → **30**, `zoom` 13 → **9**, `minimum_width`
18 → **13**, `distance` 24 → 26. Yaw stays 30. The old 18 was nearly side-on,
which is why the village ramps read as flat rectangles: every top face was a
sliver. The alphabet no longer fits on screen at once, which the user
explicitly chose in favour of immersion.

**CVC Land.** One row of 26 became **two rows of 13**, a–m at local Z=11.2 and
n–z at Z=13.8, columns 1.9 apart. That leaves 1.1-unit gaps between blocks and
a 1.8-unit lane between the rows, both wider than Chuck's 0.6-wide body;
`tests/layout.gd` drives him through each.

**Phoneme Village.** The six roofed structures were scattered at random angles.
They are now six identical cottages in an L around the green — three on the
north rim facing south, three down the west side facing east, 5.0 apart — with
a new stone lane running in front of both rows to meet the main path. The camp
tent and its fire were squared up and paired; two stray pots became a doorway
pair. **All 36 spawn markers were regenerated** so that no letter can be hidden
behind a structure. Because the camera is orthographic and never turns, "behind"
is a single fixed direction (village-local `(-0.224, 0.5, 0.837)` toward the
camera), which makes this checkable: `tests/village.gd` now walks the AABB of
every mesh in Buildings/Props/Terrain/Trees/Path/Annette and fails if the line
from any spawn to the camera crosses one. Verified the check can fail by moving
a spawn behind a cottage. Roof overhangs, boulders and tree canopies have NO
collider, so this walks visuals, not physics rays.
`tools/village_spawn_probe.gd` regenerates the list — an aid, not a build step.

**Controls.** The on-screen joystick and Pick/Put button are gone;
`ui/touch_controls.gd` draws nothing. The first pointer anywhere is a floating
walking stick whose anchor trails the finger; any second finger taps the action;
a single quick tap that never moved does too, so the lever stays one-handed.
**Pickup is no longer a button at all** — `player.gd` picks up any loose block
Chuck walks within 0.95 of. Blocks on a pedestal are excluded, or crossing the
pedestal row would strip the word he just built, and the action's empty-handed
branch now ONLY retrieves from a pedestal. A block just put down is ignored
until he is 1.5 away, or he would grab it back the same frame.

### Traps found while doing this

- The action must be a PULSE held across two physics frames. Godot does not
  always flush a synthesised input event in the frame it was parsed, and the
  player polls `is_action_just_pressed` in `_physics_process`; a shorter pulse
  is silently missed. Test the EFFECT (the block was put down), not the action
  flag.
- A lost mouse-up leaves Chuck walking forever. Reproduced in the browser with
  a synthetic drag. `_process` now polls the real mouse button state and lets
  go. Touch reports its own cancellation, which was already handled.
- `tests/village.gd`'s terrace-drop check was flaky once pickup became
  contact-based: it fetched `queue[0]`, a different random letter each run.
  It now puts the block in Chuck's hands directly — the check is about drop
  height, not about reaching that particular block. Ran it three times clean.

### Checks

All five suites pass headless (smoke, layout, lever, feedback, village).
Rendered captures reviewed at every step: `--river`, `--overview`,
`--village`, `--village-close` and a new `--village-houses` mode.
**Exported the Web preset and loaded it in Chrome from a local server**: the
scene renders with the new light and camera, scripts compile, the village round
scatters, drag-to-walk works and Chuck stops on release, no console errors.

No commit or push yet at the time of writing; audio, the word list, the deploy
workflow and the export preset are untouched. The earlier uncommitted
source-audit and permission work is preserved.

# Session handoff — 2026-09-23

## Pronunciation Studio permission received

The owner supplied a permission grant signed by Scott Bessett of Pronunciation Studio
for the “Learn the 44 Sounds of British English” IPA Chart, recordings and
related educational content. Saved the full text in
[docs/pronunciation-studio-permission.md](docs/pronunciation-studio-permission.md).
This supersedes the earlier permission-outstanding status for non-profit
educational use, including public educational apps/websites and classroom use.

The project must remain exclusively educational and non-profit. No sale,
licensing, sublicensing, ads, paid subscriptions or other monetization without
prior written commercial permission. Voluntary support donations are permitted
if access stays free and the project is not operated for commercial gain.
Provide attribution to Pronunciation Studio and its website whenever reasonably
possible. Copyright/IP remain with the original creator; this is a limited,
non-exclusive, revocable permission with other rights reserved.

Updated the phoneme asset README's current permission status and persistent
Phonics Farm audio memory/index. Earlier source/hash findings are retained;
older handoffs describe historical permission status. The source-audit mapping
and q/l provenance notes are unchanged. No game, audio, deployment, commit or
push changes. Existing uncommitted source-audit work was preserved.

Checks: reviewed the saved grant and summaries against the user-provided text;
`git diff --check` passed. No Godot tests run for this memory/documentation-only
update. These changes and the earlier audit remain uncommitted.

# Session handoff — 2026-09-22

## Phoneme source identified; permission still outstanding

Investigated s5k/ipa at the user's request. All 46 chart MP3s are byte-identical
to Pronunciation Studio's The Sound of English 2023 web sample, which credits
Joseph Hudson 2021–23. Compared publisher downloads with GitHub's blob hashes
from tree a48f42073ff705cc373562e6089360edaa227b1e and saved SHA-256 hashes too.
No reuse licence found. Earlier publisher copyright text provides a written
permission route, including school enquiries; it does not grant reuse of these
MP3s. Source identification is resolved, distribution rights are not.

Updated assets/audio/phonemes/README.md with evidence links and practical scope
of the permission needed. Added source-audit.json there (hashes and runtime
mapping) and docs/phoneme-permission-request.md, an UNSENT draft addressed to
info@pronunciationstudio.com. No external contact made. Permission or replacement
audio remains necessary to establish documented distribution rights. Do not
assume the user-supplied q/l are independent recordings solely from filenames.

Checks: all 46 publisher MP3 hashes match the repository blobs; all 26 runtime
WAV hashes and every local source hash match manifest.json. The historical
extraction mapping links 24 outputs to 22 publisher MP3s; extraction not rerun.
No audio, gameplay, export configuration, or deployment changes; Godot tests not
rerun for documentation/evidence changes. Git diff whitespace check passed.
Started clean at 1c2c760; this task remains uncommitted. No commit or push.

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

`assets/audio/phonemes/l.wav` is now the owner's `~/Desktop/PhonicsFarm Sound Review/
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

## Annette's two lines replaced with the owner's own recordings

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
they are the owner's own voice. `wrong_chime.wav` is still synthesized and unheard.

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

The source repo has **no LICENSE file**. Correction (2026-09-22): the earlier
claim that this was automatically fine for classroom use was unsupported.
See the latest source investigation above; distribution permission is outstanding.

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

Environment: `~/.local/share/phonicsfarm-tts/venv` (uv, Python 3.12,
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
`~/Desktop/PhonicsFarm Sound Review/` with README, listening index,
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

Created `~/Desktop/PhonicsFarm-LLM-Edit-Instructions.md` at the user's
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

Playable Godot 4.5.2 prototype in ~/vibecodeprojects/phonicsfarm.
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
~/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64 --headless --path . --script res://tests/smoke.gd
~/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64 --headless --path . --script res://tests/layout.gd
~/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64 --path . --script res://tests/capture.gd -- --river
```

The installed Godot binary exists even though it is not named godot on PATH.
F5 plays and F8 stops in the editor. Capture needs a real rendered window;
--headless cannot produce a screenshot.

## Next session: Claude Code or OpenCode/Qwen

Start in ~/vibecodeprojects/phonicsfarm. Read AGENTS.md, this note, and
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
