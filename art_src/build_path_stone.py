"""One flagstone. Laid in groups, it becomes the village path.

    blender --background --python art_src/build_path_stone.py

Deliberately a SINGLE irregular stone rather than a path section: rotated and
scaled per instance in the scene, one mesh gives a path that never repeats,
costs 190 triangles, and can follow any route the level needs.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sb_lib import asset, meshtools  # noqa: E402

NAME = "path_stone"


def build():
    meshtools.reset_scene()
    stone = meshtools.cylinder("PathStone", "stone", radius=0.46, depth=0.10,
                               at=(0, 0, 0.05), segments=9)
    stone.scale = (1.0, 0.82, 1.0)
    meshtools.apply_transform(stone)
    # Worn unevenly, and sunk a little at one edge, as a laid stone is.
    meshtools.wobble(stone, amount=0.030, scale=2.6, seed=52,
                     axis_bias=(1, 1, 0.35))
    meshtools.bevel(stone, 0.026, segments=2)
    # Deliberately NOT lightened on top. The first version used stone_light
    # for upward faces and the path came out as a row of white chalk discs
    # that pulled the eye straight off the letters.
    meshtools.paint_by_normal(stone, "stone", "stone", "slate",
                              up_at=0.90, down_at=-0.6)
    meshtools.drop_to_floor(stone)
    return [stone]


if __name__ == "__main__":
    asset.produce(NAME, build(), texture=asset.TEXTURE_SMALL,
                  roughness=0.97, budget_tris=360, bake_samples=20,
                  smooth_angle=30.0,
                  gouache=dict(wash=0.20, wash_scale=7.0, grain=0.07,
                               grain_scale=70.0, streak=0.10, streak_scale=6.0,
                               ao_strength=0.50, ao_distance=0.14,
                               edge_light=0.16, edge_dark=0.12))
