# Painted Storybook — asset production

Blender source and build scripts for Phonics Farm's visual direction. Nothing
in this folder is part of the game: a `.gdignore` keeps Godot from scanning it,
and the runtime assets are the committed `.glb` files in `assets/storybook/`.
That separation is deliberate — GitHub Actions builds the web export from those
GLBs and never needs Blender installed.

    art_src/build_all.sh            rebuild every asset
    blender --background --python art_src/build_block.py    rebuild one
    blender --background --python art_src/render_review.py -- cottage chuck:walk:7

After rebuilding, re-import before the change reaches a scene:

    ~/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64 \
        --headless --path . --editor --import

Built with Blender 5.2.3 LTS.

---

## The art direction, in one page

A children's picture book given dimension. What separates it from the
asset-store look it replaces:

**Value before colour.** Every palette entry in `sb_lib/palette.py` records
roughly where it sits from 0 to 1, and the palette is grouped by value rather
than by hue. Two relationships are load-bearing and are commented in that file:

* cream letter face (0.90) against ink lettering (0.10). Nothing else in the
  game is allowed above 0.84, so the block is always the lightest thing on
  screen and a five-year-old's eye lands on the letter first.
* canopy (0.36) against meadow (0.60). The first palette had those at 0.52 and
  0.55 and trees simply disappeared into the field behind them.

**Bevel everything.** `meshtools.BEVEL_*` are real widths in metres, chosen by
how an object was made rather than by how big it is — 22 mm for turned toys,
16 mm for sawn timber, 30 mm for plaster and stone. A consistent chamfer across
every asset is most of why they look like one game.

**Nothing is plumb.** `wobble`, `lean`, `taper`, `sag` and `bend` are all small
— 1.4 degrees of lean, 18 mm of noise across a wall. None of it is visible as
an effect; together it is the difference between hand-built and extruded.

**Scale against Chuck.** He is 1.21 m. The cottage door is 1.46 m and the ridge
is 3.4 m. Every asset is authored at final metre scale and instanced at scale 1.

**Surface is painted, not tinted.** See the pipeline below.

---

## The pipeline

Every build script is the same five lines of plumbing (`sb_lib/asset.py`)
around a `build()` that makes geometry:

```
parts coloured by PALETTE NAME        meshtools.set_part_color / paint_by_normal
  -> joined into as few objects as possible
  -> atlas_unwrap()                   one shared UV layout for the whole asset
  -> gouache_material()               Cycles-only painterly shader
  -> bake_to_texture()                albedo x AO x pointiness x wash -> one image
  -> finalize_material()              plain Image -> Principled, exportable
  -> export_glb()
```

Parts are coloured with **vertex colours** and then joined, so an eleven-colour
cottage still ships as one mesh, one material and one texture. The painterly
look is baked, not shaded at runtime: `gouache_material` multiplies the vertex
colour by broad washes, paper grain, brush streaks, ambient occlusion in the
creases and a pointiness term that lightens convex edges and darkens concave
ones. Cycles computes that once; the browser just draws a texture.

Every noise is pushed through a contrast expansion first. Raw Blender noise
sits in a narrow band around 0.5, and without that step an amplitude of 0.10
bakes out as about 1% of actual variation — a flat fill, which is exactly what
the first block build produced.

What reaches Godot per asset: **one material, one base-colour texture, no
custom shader, no transparency, metallic 0.** As cheap as a textured mesh gets,
and it survives the Compatibility renderer unchanged.

### Texture sizes

The camera is orthographic at size 9 over a 1280-wide viewport, so one metre is
about 142 px on screen. 512 across a 0.8 m block is already more texels than
pixels.

| | size | why |
|---|---|---|
| block, pedestal, path stone | 512 | small props |
| chuck, cottage, tree, meadow | 1024 | large, or looked at closely |

---

## Adding an asset

Copy `template_asset.py`, change `build()`, add it to `build_all.sh`.

Rules the template encodes:

1. Build **Z-up** at final metre scale, base at Z = 0. `export_yup` handles
   Godot's Y-up; Blender -Y becomes Godot +Z.
2. Colour parts with a **palette name**, never a literal colour.
3. Bevel, then let `produce()` smooth by angle. `smooth_angle` is a real dial:
   16 degrees keeps a toy block's chamfers flat and crisp, 44 rounds a tree
   canopy off.
4. Use `paint_by_normal`, not `repaint_faces`, on anything organic. A per-face
   test on a low-poly canopy paints whole facets and reads as camouflage.
5. Hand `produce()` the finished objects and let it surface, bake and export.
6. If a Godot script reaches into the model by node name, call
   `asset.verify_contract()` so a rename breaks the BUILD rather than the game.

### Traps that cost real time here

* **`apply_transform` bakes scale first, rotation second.** Scaling a rotated
  four-sided cone splays it across both ground axes instead of stretching it
  along one — that is how the first cottage came out 5.5 m deep. Use
  `meshtools.gable()`, or rotate after the primitive helper has baked its
  dimensions.
* **Deformers take WORLD heights; raw vertex maths does not.** `taper`, `lean`
  and `bend` subtract `obj.location.z` for you. Anything you write by hand
  against `vert.co` or `face.calc_center_median()` is in OBJECT space, and an
  object whose origin is up at head height will have every face fail a world-Z
  test. That emptied Chuck's hair completely on one build.
* **A box has one face per side.** Stripes, courses and bands need
  `subdivide()` first or the predicate repaints all of it or none of it.
* **Opaque means opaque.** Chuck's eyes sat behind his lenses for two builds
  and were simply invisible; there is no transparency in this game.

---

## Engine contracts

Three Godot scripts reach into these models by name and must not be touched.
`asset.verify_contract()` and `tools/check_storybook.gd` both guard them.

| Asset | Contract | Set by |
|---|---|---|
| block | 0.8³, origin on the BOTTOM face; children named `Cube`, `Front`, `Right`, `Back`, `Left`, `Top`; the five faces share one material; letter faces at 0.413 from centre | `alphabet_block/alphabet_block.gd` |
| chuck | 1.21 m, faces local +Z, animations named exactly `idle` and `walk` | `player/player.gd` |
| pedestal | TWO GLBs. `Base` exactly 0.5 m tall with its origin at its own centre; `Top` separate | `pedestal/pedestal.gd` |

The pedestal split is the non-obvious one. When a letter sounds, `pedestal.gd`
raises it by stretching `Base` (`scale.y = 1 + lift/0.5`, node moved up by
`lift/2`) and translating `Top`. That arithmetic only lands the base's feet
back on the ground at exactly 0.5 m tall, and the cap has to be its own node or
it would be stretched too, every time a block was played.

## The sRGB correction

`storybook/storybook_surface.gd` sets `albedo_texture_force_srgb` on every
imported storybook material, and every storybook scene carries a `SurfaceFix`
child that applies it.

It is there because Godot's glTF import does not mark these GLB-embedded
base-colour textures as sRGB, so the Compatibility renderer treats them as
already-linear and everything renders about a gamma too bright. This was
measured, not guessed: the baked PNG holds exactly the right sRGB bytes
(#93AC64 for meadow grass, checked byte for byte), a flat `albedo_color`
material rendered identically to the textured mesh, and in the browser the
meadow measured (254, 255, 179) against the shipping game's (145, 190, 115),
with roof, plaster and block faces all clipping to white. With the flag set the
same measurement reads (149, 203, 89).

`art_src/review/slice-before-srgb-fix.jpg` and `slice-in-browser.jpg` are the
before and after.
