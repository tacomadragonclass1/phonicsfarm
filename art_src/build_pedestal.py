"""The pedestal -- where a letter is placed to be sounded out.

    blender --background --python art_src/build_pedestal.py

Engine contract, from `pedestal/pedestal.gd`:

  * The top surface must be at Y = 0.62. `SnapPoint` sits there and a block's
    origin is its bottom face, so a block placed on this pedestal rests
    exactly on the cap.
  * Nothing may reach wider than 0.66 from the centre; that is the radius of
    the collision cylinder, and anything wider would be visually solid but
    walk-through.
  * TWO separate meshes, `Base` and `Top`. This is why the pedestal is the one
    asset that ships as two GLBs. When a letter sounds, `pedestal.gd` raises
    it by STRETCHING `Base` -- `scale.y = 1 + lift / 0.5` with the node moved
    up by `lift / 2` -- and translating `Top`. That arithmetic only lands the
    base's bottom back on the ground if the base is EXACTLY 0.5 m tall with
    its origin at its own centre, and it only leaves the cap undistorted if
    the cap is a different node. One joined mesh would have stretched the cap
    along with the shaft every time a block was played.

Art direction: a small carved plinth, not a cake stand. Stepped stone base,
a slightly tapered fluted shaft, and a dished cream cap that reads as a place
to PUT something -- the dish is functional storytelling, it says the block
belongs there.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sb_lib import asset, exporter, meshtools  # noqa: E402

NAME = "pedestal"
TOP_Z = 0.62        # engine contract -- do not change
SPLIT_Z = 0.50      # engine contract -- base is exactly this tall
MAX_RADIUS = 0.64   # inside the 0.66 collision cylinder


def build():
    meshtools.reset_scene()
    parts = []

    footing = meshtools.cylinder("Footing", "stone", radius=MAX_RADIUS,
                                 depth=0.11, at=(0, 0, 0.055), segments=16)
    meshtools.wobble(footing, amount=0.010, scale=3.0, seed=3)
    meshtools.bevel(footing, meshtools.BEVEL_MASONRY, segments=2)
    parts.append(footing)

    step = meshtools.cylinder("Step", "stone_light", radius=0.52, depth=0.09,
                              at=(0, 0, 0.145), segments=16)
    meshtools.wobble(step, amount=0.008, scale=3.4, seed=8)
    meshtools.bevel(step, 0.024, segments=2)
    parts.append(step)

    shaft = meshtools.cone("Shaft", "plaster_warm", r1=0.335, r2=0.285,
                           depth=0.315, at=(0, 0, 0.3425), segments=16)
    meshtools.bevel(shaft, 0.020, segments=2)
    parts.append(shaft)

    # Six flutes. Carving, not decoration: they catch a rim of light down one
    # side of the shaft and stop it reading as a plain tube.
    for index in range(6):
        angle = math.radians(index * 60.0 + 15.0)
        flute = meshtools.cylinder("Flute", "timber", radius=0.042,
                                   depth=0.275,
                                   at=(math.cos(angle) * 0.305,
                                       math.sin(angle) * 0.305, 0.3425),
                                   segments=8)
        parts.append(flute)

    base = meshtools.join(parts, "Base")
    meshtools.drop_to_floor(base)

    # ------------------------------------------------------------- the cap
    crown = []
    collar = meshtools.cylinder("Collar", "timber", radius=0.360, depth=0.046,
                                at=(0, 0, 0.517), segments=16)
    meshtools.bevel(collar, 0.014, segments=2)
    crown.append(collar)

    cap = meshtools.cylinder("Cap", "cream", radius=0.545, depth=0.085,
                             at=(0, 0, TOP_Z - 0.0425), segments=20)
    meshtools.bevel(cap, 0.026, segments=3)
    # Dish the top very slightly. The block still rests at 0.62 because only
    # the inner vertices drop; the rim -- what the eye reads as the surface --
    # stays where the contract says it is.
    for vert in cap.data.vertices:
        radial = math.hypot(vert.co.x, vert.co.y)
        if vert.co.z > 0.0 and radial < 0.40:
            vert.co.z -= 0.012 * (1.0 - (radial / 0.40) ** 2)
    crown.append(cap)
    top = meshtools.join(crown, "Top")

    # Origins the engine contract depends on: the base pivots about its own
    # centre so stretching it keeps its feet on the ground, and the cap pivots
    # at the split so it can be lifted by exactly `lift`.
    meshtools.set_origin(base, (0, 0, SPLIT_Z / 2))
    meshtools.set_origin(top, (0, 0, SPLIT_Z))
    base.location = (0, 0, 0)
    top.location = (0, 0, 0)
    return base, top


GOUACHE = dict(wash=0.17, wash_scale=5.5, grain=0.055,
               grain_scale=60.0, streak=0.09, streak_scale=5.0,
               ao_strength=0.62, ao_distance=0.22,
               edge_light=0.15, edge_dark=0.12)


if __name__ == "__main__":
    base_obj, top_obj = build()
    asset.produce(NAME + "_base", [base_obj], texture=asset.TEXTURE_SMALL,
                  roughness=0.94, budget_tris=1500, bake_samples=28,
                  smooth_angle=26.0, gouache=GOUACHE, save_source=False)
    asset.produce(NAME + "_top", [top_obj], texture=asset.TEXTURE_SMALL,
                  roughness=0.94, budget_tris=600, bake_samples=28,
                  smooth_angle=26.0, gouache=GOUACHE, save_source=False)
    # One source file holding BOTH halves, named for the asset rather than for
    # whichever half happened to be exported last.
    exporter.save_blend(os.path.join(asset.BLEND_DIR, NAME + ".blend"))
