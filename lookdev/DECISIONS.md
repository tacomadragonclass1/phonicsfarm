# The art direction, settled — 2026-11-04

This file is the handoff for the look. `lookdev/` is a self-contained kit: a
four-object scene, two shaders, a shooting harness and a measuring script.
**Nothing in it touches the game.** No asset was rebaked at any point in this
pass — same GLBs, same atlases, same bakes — so deleting `lookdev/` restores
the set exactly as it was.

    godot --path . --script lookdev/shoot.gd -- patina
    python3 lookdev/measure.py /tmp/lookdev-*.png

⛔ Not `--headless`. Capture needs a rendered window; the draw is forced
rather than awaited. See the trap list at the bottom.

## What was chosen

| | Setting | Where |
|---|---|---|
| Surface marks | **patina**, `grain_strength 0.12` | `lookdev/painted.gdshader` |
| Shading | `diffuse_toon`, built-in | same |
| Line | inverted hull, `width_screen 11.0` | `lookdev/ink.gdshader` |
| Grade | `adjustment_saturation 0.78`, exposure 1.22 | `shoot.gd::_regrade` |
| Light | warm key 34°, cool ambient, light depth fog | `shoot.gd::_relight` |
| Camera | **orthographic, pitch 16**, size 8.2, pulled in | `shoot.gd::_frame` |

Reference plate: the `near16` view at grain 0.12.

## Why each one, in the owner's terms

**Patina over brushwork.** Brushwork "reads too messy". It also failed a test
it was not asked to sit: world-space strokes seen at a grazing angle project
into long smears, so a receding field reads as motion blur. Isotropic marks
have no direction to stretch and are unaffected. If brushwork is ever revived,
its stroke length has to be scaled by viewing angle.

**Ink is the identity.** It is the only lever in this pass that changes what
the art *is* rather than how it is lit, and the only one the path tracer could
not have supplied. ⭐ The line varies slightly along its length on purpose: a
perfectly even outline reads as a computer-drawn edge, which is the thing this
is escaping.

**Camera pitch, not the lens.** ⭐⭐ Orthographic at pitch 30 is how an asset
store photographs the thing it is selling. Dropping the pitch alone — same
projection — removes most of the diorama reading, because the horizon arrives
in frame. Ortho is KEPT, and that matters: constant scale is what lets a
five-year-old judge a block anywhere on the board.

⭐ The lower camera makes the letters BIGGER, not smaller. Measured on the
plaque: 28 px at the shipping camera, 39 px here.

## ⛔⛔ A RULE WAS RETIRED, and it has code attached

At pitch 16 a letter can fall outside the frame. That was accepted
deliberately: *"I'm fine with the letter S off camera. The player will go
around the space to collect letters, that's the fun of it."*

This **retires the no-hidden-letter guarantee**, which is not just a principle
— it is enforced machinery:

  * `tests/village.gd` fails the build if any letter is hidden from the fixed
    camera, and it gates the deploy
  * `tools/village_spawn_probe.gd` exists to place markers so that never
    happens
  * `tools/build_foundation_village.py` runs the same occlusion rule forwards
    for markers and backwards for props

👉 None of that is wrong yet, because none of this is in the game. But
adopting this camera means deciding what those three become. The honest
replacement is probably "every letter is REACHABLE", not "every letter is
visible", and that is a different test.

## What was rejected, so it is not re-proposed

- **2.5D / pre-rendered backdrops.** Withdrawn by me after the control
  disproved it: the same assets path-traced in Cycles still read low-poly.
  Pre-rendering buys a prettier photograph of the same geometry.
- **three.js, or restarting in Codex.** The engine was never the constraint.
  Every plate in this pass runs in the Compatibility renderer the browser
  build already ships. Download size on district wifi is "truly meaningless".
- **Eye-level camera.** Charming, and deferred rather than refused. It is a
  GAME decision with a level-design bill: letters stop being one size (54–64
  px by distance), and it fully exposes the foliage facets.

## The numbers this pass established

- **Texel density is the reason the die works and nothing else does.** Block
  ~260 px/m, camera 142 px/m, terrain **16 px/m**. The terrain cannot hold a
  baked mark at any quality setting. ⭐ The grain is added per-pixel in WORLD
  SPACE precisely so it is independent of this.
- **The published grade was 2.3× over on saturation.** Mean 0.707 against the
  Cycles control's 0.304. ⭐ "It still looks too green" cannot be aimed at;
  `lookdev/measure.py` turns it into a number that can.
- Chosen plate measures sat +3%, val −4% against the control.

## ✅ The tree, remodelled (same day)

⭐⭐ **The facets were never the problem, and one A/B render is what kept this
from solving the wrong thing.** The internal lines were the outline hull
TEARING at split normals -- which happens wherever two faces meet at more than
the smoothing angle. `SMOOTH["tree"]` 28 -> 62 removed them without touching a
vertex. Only then was it clear the remodel was about SILHOUETTE.

⭐⭐ **With an ink line, NEGATIVE SPACE is the subject.** A solid mass outlines
as a solid mass, so no surface work inside it will read as foliage. The old
canopy was six overlapping pancakes with no sky between them -- and it
survived three review rounds because at pitch 30, far back, its outline was a
small soft blob and nobody could see what it was made of. The ink line and the
lower camera put the construction on display.

Three rules the rebuild follows:

  * ⛔ **Every clump is CARRIED.** A clump with no limb under it reads as a
    cloud parked beside a tree -- which is what the old free-floating sprigs
    did. The trunk now runs all the way to the crown.
  * ⛔ **Unequal masses.** Five clumps of one size read as balloons; the first
    cut of this did exactly that. One dominant crown, two mid, two small.
  * ⛔ **Flat tops, undercut bottoms.** Foliage spreads where it meets the
    light and falls away underneath. Holding the radius wide through the upper
    half puts the widest point ABOVE centre, which is what makes a canopy look
    supported rather than balanced.

Cost: 5,128 tris against 4,566; texture unchanged at 512. Five suites plus
`check_storybook.gd` green by exit code.

## ✅ The rest of the foliage, and a real outline (same day)

⛔⛔ **THE INK WAS A FIXED NUMBER OF METRES, which is not a line, it is a
moat.** The hull was pushed along the normal in MODEL space, so the setting
that drew cleanly on a 4 m cottage would have been wider than a 5 cm berry is
round -- and it scaled with whatever scale a prop was instanced at, so two
copies of one tree at 0.9 and 1.15 would have carried different line weights.
⭐ Caught by reasoning about the bush's berries BEFORE building them, which is
the first time this session something was predicted rather than discovered.

Fixed: the offset happens in CLIP space, by a pixel count. One line weight for
the whole world, which is what a drawn line is -- the pen does not get thicker
for bigger subjects. `width_screen` is now **3.4 px**.

⛔⛔ **`village.py` had ONE smoothing angle for everything.** `SMOOTH = 11.0`
is right for a wall, a sign and a cart, and catastrophic for a canopy: it
splits normals at every lobe, and a split normal tears the ink hull open. So
every internal facet of every bush was being drawn. There is a
`SMOOTH_BY_SUBJECT` table now; foliage sits at 46-62.

Rebuilt to the same three rules:

  * **`tree_b`** -- clumps now alternate left and right up the trunk so the
    gaps are on BOTH sides, with the widest mass at two thirds height. Still
    deliberately a different species from the foundation tree: ⭐ a prop used
    26 times is ONE PROP USED 26 TIMES, and two alternating silhouettes read
    as a wood where one repeated reads as wallpaper.
  * **`bush`** -- two lobes and a notch, not three merged cushions. ⛔ Also a
    scale lesson: at 0.56 m radius, seven scallops at amplitude 0.27 are
    convolutions and it read as a cabbage. **The fold count has to fall as
    the mass gets smaller**, or folds stop being leaf clumps and become
    texture. Five at 0.19 now.
  * **berries** -- were NINE spheres floating in the air up to 0.56 m from
    the mass. Invisible under flat shading, confetti the moment each gets a
    line. Five now, bedded onto the surface at 0.94 of the lobe radius --
    proud enough to read, not free of it.
  * **`blossom`, `mushrooms`** -- checked under ink and left alone. The
    mushrooms are the best small prop in the set; a drawn line suits them.

`lookdev/foliage.tscn` shoots the whole set in a row with the die in frame as
the scale reference and the quality bar.

    godot --path . --script lookdev/shoot.gd -- patina 0.12 3.4 6.0 foliage

## 👉 What is NOT done

1. **Adoption.** None of this is in `scenes/main.tscn`, which still has no
   tonemapper. Adopting means taking the grade, the two shaders, the camera,
   and settling the retired rule above.
3. **The terrain's own ring artifacts** are visible on the far hills in the
   reference plate. Not investigated.

## ⛔ Traps this pass cost real time to find

- **`await RenderingServer.frame_post_draw` never returns** when the window is
  not composited. The main loop keeps running, so it looks exactly like a hung
  scene. ⭐⭐ This single defect is why so much of this project's handoff said
  "never verified". Force the draw instead — `tests/capture.gd::_draw_now`.
- **Godot serves a STALE IMPORT CACHE in `--script` mode.** Rebuild an asset,
  capture, and you get the old mesh back with no warning. Run
  `godot --headless --path . --import` first.
- **Re-importing rewrites `assets/storybook/explore/*_albedo.png`**, because
  those are extracted from the GLBs' embedded textures. They are tracked in
  git, so any import dirties the tree with meaningless churn. Consider
  ignoring them.
- **Do not write a custom `light()` in Compatibility.** Measured: `NORMAL`
  varied correctly, `LIGHT` was correctly constant, and `dot()` still came
  back in a 0.10–0.18 band across every surface, with all cast shadows gone
  though `ATTENUATION` alone rendered them perfectly.
- **Writing `ALPHA` below 1 drops a pass out of the opaque queue.** The ink
  outline silently never drew, and I read the blank result as "outlines don't
  help".
- **Depth fog is set against the CAMERA'S STANDOFF, not the scene's size.** An
  orthographic camera 24 m back puts every pixel deep in fog before the
  subject starts. 0.013 was a white sheet; 0.0022 is right.

⭐⭐ Four of those six produced a confident WRONG CONCLUSION before being
caught, and every one came from the same mistake: running a diagnostic
*through* the pipeline being diagnosed. Two probes read as "the effect does
not work" when the effect was fine and the measurement was broken. Test the
instrument against a known control first, and sample pixel values rather than
looking at the picture.
