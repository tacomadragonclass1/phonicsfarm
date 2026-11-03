"""The tree -- the foliage language for the whole village.

    blender --background --python art_src/build_tree.py

Trees are scenery, which in a reading game means they must be INTERESTING AND
QUIET at the same time: strong enough to make a composition, never loud enough
to compete with a letter.

  * The canopy is built as five overlapping masses and then voxel-remeshed into
    one skin. That is the whole trick: separate balls read as a pile of balls,
    a remeshed union reads as a single organic form with a scalloped,
    asymmetric silhouette. A cone would read as a Christmas tree and a sphere
    as a lollipop; neither is a storybook tree.
  * The trunk curves and flares into roots. A straight cylinder is a post.
  * Value is painted by direction, not by random: the top of the canopy takes
    the light, the underside goes dark. At the game's fixed camera that reads
    as a tree with a lit side and a shaded one, from a single flat material.
  * 3.1 m, so it stands about two and a half Chucks tall and sits comfortably
    below the cottage ridge.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sb_lib import asset, meshtools  # noqa: E402

NAME = "tree"
HEIGHT = 3.10


def build():
    meshtools.reset_scene()
    parts = []

    trunk = meshtools.cone("Trunk", "bark", r1=0.150, r2=0.072, depth=1.78,
                           at=(0, 0, 0.89), segments=11)
    meshtools.subdivide(trunk, levels=2, smooth=False)
    meshtools.bend(trunk, degrees=26.0, bottom_z=0.0, top_z=1.78, axis="Y")
    meshtools.flare_base(trunk, height=0.30, strength=0.72)
    meshtools.wobble(trunk, amount=0.020, scale=2.4, seed=61,
                     axis_bias=(1, 1, 0.3))
    meshtools.paint_by_normal(trunk, "bark", "bark", "bark_dark",
                              down_at=-0.55)
    parts.append(trunk)

    # One bare branch, long enough to actually clear the canopy. It breaks the
    # outline and tells the eye there is a structure under all that foliage.
    branch = meshtools.cone("Branch", "bark", r1=0.056, r2=0.018, depth=1.20,
                            at=(-0.62, 0.05, 1.72),
                            rot=(0, -math.radians(76), 0), segments=7)
    parts.append(branch)

    canopy_parts = []
    # Varied radii on an uneven arrangement. Equal masses merge into one
    # boulder; a big one with smaller lobes around it keeps a leafy outline.
    masses = [
        (0.06, -0.02, 2.14, 0.72),
        (-0.50, 0.16, 1.92, 0.47),
        (0.50, -0.14, 2.00, 0.50),
        (0.08, 0.46, 2.26, 0.44),
        (-0.22, -0.42, 2.40, 0.42),
        (0.30, 0.10, 2.58, 0.40),
        (-0.34, 0.04, 2.52, 0.34),
        (0.00, -0.30, 1.84, 0.38),
    ]
    for x, y, z, radius in masses:
        canopy_parts.append(meshtools.ball("Mass", "foliage", radius=radius,
                                           at=(x, y, z), subdiv=2))
    canopy = meshtools.join(canopy_parts, "Canopy")
    meshtools.remesh_organic(canopy, voxel=0.070)
    meshtools.wobble(canopy, amount=0.042, scale=3.2, seed=77)
    meshtools.shrink_to_budget(canopy, 1500)
    meshtools.set_part_color(canopy, "foliage")
    # Light reaches the crown; the underside never sees it. Blended on the
    # vertex normal so it is a gradient, not a patchwork.
    meshtools.paint_by_normal(canopy, "foliage_light", "foliage",
                              "foliage_dark", up_at=0.95, down_at=-0.25)
    parts.append(canopy)

    merged = meshtools.join(parts, "Tree")
    meshtools.drop_to_floor(merged)
    return [merged]


if __name__ == "__main__":
    asset.produce(NAME, build(), texture=asset.TEXTURE_MEDIUM,
                  roughness=0.97, budget_tris=2400, bake_samples=24,
                  smooth_angle=44.0,
                  gouache=dict(wash=0.26, wash_scale=4.0, grain=0.07,
                               grain_scale=45.0, streak=0.12, streak_scale=3.4,
                               ao_strength=0.58, ao_distance=0.45,
                               edge_light=0.17, edge_dark=0.13))
