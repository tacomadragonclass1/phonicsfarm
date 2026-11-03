"""The alphabet block -- a beautiful physical learning toy.

    blender --background --python art_src/build_block.py

This asset has the tightest constraints in the game, and all of them come from
`alphabet_block/alphabet_block.gd`, which this GLB has to satisfy exactly:

  * 0.8 x 0.8 x 0.8, ORIGIN ON THE BOTTOM FACE. The script's sibling nodes put
    a collision box and five Label3D letters at hard-coded offsets from that
    origin; the pickup, carry and pedestal-snap maths all assume it.
  * A child named exactly `Cube` -- the only child the script does NOT
    repaint. Everything else under `Visual` is treated as a letter face.
  * Five more children named `Front`, `Right`, `Back`, `Left`, `Top`. The
    script duplicates `Front`'s material and applies it to all five, which is
    how the lever's gold "this letter is sounding" feedback works. They must
    therefore share one material and it must be the cream one.
  * Letter faces must stay at the same depth, because the Label3D letters are
    positioned in the SCENE, not here. The outer face of each plaque sits at
    0.413 from centre, just inside the 0.4178 the letters sit at.

Letters are deliberately NOT baked into the texture. Every block in the game
changes its letter at runtime.

Art direction notes:

  * The body is honey-toned painted wood with a 48 mm corner round -- a real
    chamfer a child's hand would feel, not a "rounded cube" default.
  * The letter plaques are inlaid: half sunk into the wood, half proud, so the
    cream catches its own highlight and the letter reads as a label ON an
    object rather than a decal.
  * The plaques use `flat_material`, NOT the painterly one. Every other
    surface in this game is painterly; this one surface is flat on purpose,
    so a five-year-old never has to separate a letterform from a texture
    behind it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sb_lib import asset, meshtools, painter  # noqa: E402

NAME = "block"

SIZE = 0.80          # engine contract -- do not change
PLAQUE = 0.60        # leaves a 50 mm wooden frame inside the body's chamfer
PLAQUE_DEPTH = 0.026
FACE_OUT = 0.413     # outer surface of a side plaque, from the block centre
TOP_OUT = 0.813      # outer surface of the top plaque, from the block base

# Blender is Z-up and Godot is Y-up, so a Blender -Y face exports as Godot +Z.
# Each entry is (node name, centre, size) in Blender space.
_HALF = PLAQUE_DEPTH * 0.5
FACES = [
    ("Front", (0.0, -(FACE_OUT - _HALF), SIZE / 2), (PLAQUE, PLAQUE_DEPTH, PLAQUE)),
    ("Right", ((FACE_OUT - _HALF), 0.0, SIZE / 2), (PLAQUE_DEPTH, PLAQUE, PLAQUE)),
    ("Back", (0.0, (FACE_OUT - _HALF), SIZE / 2), (PLAQUE, PLAQUE_DEPTH, PLAQUE)),
    ("Left", (-(FACE_OUT - _HALF), 0.0, SIZE / 2), (PLAQUE_DEPTH, PLAQUE, PLAQUE)),
    ("Top", (0.0, 0.0, TOP_OUT - _HALF), (PLAQUE, PLAQUE, PLAQUE_DEPTH)),
]


def build():
    meshtools.reset_scene()

    body = meshtools.box("Cube", "honey", size=(SIZE, SIZE, SIZE),
                         at=(0, 0, SIZE / 2))
    # A wide three-facet CHAMFER, not a round. Shaded at a low angle (see
    # `smooth_angle` below) each facet stays flat and catches its own band of
    # light, which is what makes a wooden toy read as turned and painted
    # rather than moulded in plastic.
    meshtools.bevel(body, 0.050, segments=3)
    # Barely-there unevenness. A toy that came off a lathe, not a render.
    meshtools.wobble(body, amount=0.0022, scale=3.0, seed=7)
    # The chamfers are where a well-loved block's paint goes deepest, so they
    # are painted a shade down. It also draws a soft line around every face,
    # which is what separates one face from the next at a glance.
    meshtools.repaint_faces(
        body,
        lambda centre, normal: max(abs(normal.x), abs(normal.y),
                                   abs(normal.z)) < 0.97,
        "honey_deep")

    plaques = []
    for name, centre, size in FACES:
        plaque = meshtools.box(name, "cream", size=size, at=centre)
        meshtools.bevel(plaque, 0.011, segments=3)
        plaques.append(plaque)

    cream = painter.flat_material("block_face", "cream", roughness=0.94)
    painter.assign(plaques, cream)

    asset.verify_contract([body] + plaques,
                          ["Cube", "Front", "Right", "Back", "Left", "Top"])
    return [body] + plaques


if __name__ == "__main__":
    asset.produce(NAME, build(), texture=asset.TEXTURE_SMALL,
                  roughness=0.90, budget_tris=1600, bake_samples=32,
                  smooth_angle=16.0,
                  gouache=dict(wash=0.14, wash_scale=5.0,
                               grain=0.05, grain_scale=70.0,
                               streak=0.16, streak_scale=5.0,
                               ao_strength=0.40, ao_distance=0.22,
                               edge_light=0.14, edge_dark=0.10))
