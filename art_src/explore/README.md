# Direction study — three visual languages

Phase 1 replaced Kenney models with Blender models and kept the vocabulary:
boxes, cylinders, cones and spheres, textured nicely. That is why it still
looked like an asset pack. This study changes the vocabulary instead.

    blender --background --python art_src/explore/d1_handcrafted.py
    blender --background --python art_src/explore/d2_storybook.py
    blender --background --python art_src/explore/d3_sculptural.py
    blender --background --python art_src/explore/render_study.py -- d1 d2 d3
    blender --background --python art_src/explore/render_study.py -- d1 d2 d3 lineup

In Godot, open `scenes/direction_study.tscn` and press play. All three stand
side by side 13 units apart; walk right to move from one world to the next.
The camera is the shipping one, so every judgement is made at the size and
angle a child actually sees.

## What is actually different

Not three palettes on the same models. Three construction methods.

| | D1 handcrafted | D2 storybook | D3 sculptural |
|---|---|---|---|
| premise | made on a table from clay and carved wood | a picture-book page given depth | moulded contemporary, designed object |
| trunk | revolved silhouette that swells, pinches and knots | one calligraphic stroke, flattened across its depth | a single decisive arc |
| canopy | four pressed pads on **visible branches**, cloud-pruned | six thin layered pads, fanned, each its own green | three interlocking faceted masses |
| cottage | lofted walls that bulge at waist height, scalloped thatch | tall, narrow, jettied upper storey, leans 2.4° | asymmetric roof, ridge pushed 1.14 off centre, plus a lean-to |
| block | superellipsoid with knuckle dents | crisp painted faces with a modelled ink border | squircle with a deep, crisply recessed well |
| shading | smooth, 54° | 33° | **flat**, planar-decimated into facets |
| surface | fine even tooth, very strong AO, no sheen | broad washes, visible brush, `edge_dark` 0.38 | almost no texture at all; form does the work |

The shading angle and `edge_dark` are the two dials that matter most. D3 is
planar-decimated and flat-shaded, so nothing in it is smooth; D2's `edge_dark`
of 0.38 is four times anything else in the project and is what produces a
drawn line wherever a form turns away.

## New form generators

`sb_lib/forms.py`. Nothing in it is a primitive — each takes a profile, an
outline or a path that was **drawn**:

    lathe()     revolve a hand-drawn silhouette
    loft()      bridge a stack of outlines (plans that change with height)
    sweep()     tube along a path with varying radius
    pad()       scalloped lens (layered foliage)
    superform() superellipsoid (the cube/sphere dial)
    ribbon()    swept flat strip

plus deformers that leave a hand on the surface rather than noise: `press`
(thumb against a plane), `dents`, `swell`, `facet`, `jitter_verts`.

## Engine contracts are intact in all three

Every block exposes `Cube` + `Front`/`Right`/`Back`/`Left`/`Top`, the five
faces share one flat material, and the letters are still five runtime Label3D
nodes. `tools/check_direction_study.gd` asserts it. Whichever direction wins
drops into `alphabet_block.gd` without a line of gameplay code changing.

## What is deliberately NOT done

* **No rigging or animation.** Three characters rigged before one is chosen is
  wasted work. The study Chucks are static; the walking avatar in the Godot
  scene is the phase-1 Chuck, who is already rigged.
* **No environment.** Ground, paths and planting come after the direction is
  settled, per the brief.
* **Chuck is 1.35 m, up from 1.18.** He read as too small. Adopting any of
  these means changing the capsule height in the new chuck scene — one line,
  in a scene that is not the shipping one; `player.gd` is untouched either way.

## Traps found building these

* **`pad(tilt=...)` rotated about the world origin, not the pad's centre.**
  It threw a cottage door arch into the roof and a character's mouth out past
  his shoulder. Fixed in `forms.py`; pads are now built at the origin, tilted,
  then moved.
* **A flat pad makes bad hair.** Its rim is its widest part, so it always
  overhangs the brow and hides the glasses. All three now use a solid cap
  pressed back in Y.
* **Voxel remeshing destroys a faceted canopy.** D3's three masses were being
  melted back into one soft cloud — the exact blob the direction exists to
  avoid. It builds at low segment counts and never remeshes.
* **A coplanar trim wins the depth test.** D2's ink border sat level with the
  label and every face of the block came out solid black. The border is now
  sunk 16 mm behind it.
* **`albedo_color` is consumed as LINEAR here, like the GLB textures.**
  Measured in the browser twice. Hand-written material colours in scenes need
  linear values, not the sRGB ones the palette is written in.
