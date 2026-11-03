"""The meadow patch the vertical slice stands on.

    blender --background --python art_src/build_meadow.py

Scoped to the slice. The live game's ground is `environment/meadow.gdshader`,
a procedural noise shader, and nothing here touches it.

It exists because the ground is roughly half of every frame, so judging five
new assets over the old flat-shaded field would be judging them against the
wrong background. A gently mounded mesh with a baked wash and baked ambient
occlusion gives the new assets something to sit IN rather than ON.

The mounding is deliberately tiny -- 5 cm over 26 m. The slice's collision is
a flat box at Y = 0, as the real game's is, so anything deeper than that would
have Chuck visibly floating over the hollows.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sb_lib import asset, meshtools  # noqa: E402

NAME = "meadow"
SIZE = 26.0
DIVISIONS = 22


def build():
    meshtools.reset_scene()
    ground = meshtools.plane_grid("Meadow", "grass", size=(SIZE, SIZE),
                                  divisions=(DIVISIONS, DIVISIONS))
    # Two octaves: broad swells plus a finer unevenness, both small enough
    # that the flat collision box underneath is never noticeable.
    meshtools.wobble(ground, amount=0.050, scale=0.16, seed=101,
                     axis_bias=(0, 0, 1))
    meshtools.wobble(ground, amount=0.018, scale=0.55, seed=102,
                     axis_bias=(0, 0, 1))
    # Hollows hold the damp and read darker; crowns are sun-bleached. Done on
    # the normal rather than on height so it survives the mesh being moved.
    meshtools.paint_by_normal(ground, "grass", "grass_dark", "grass_dark",
                              up_at=0.9995, down_at=-1.0)
    return [ground]


if __name__ == "__main__":
    asset.produce(NAME, build(), texture=asset.TEXTURE_LARGE,
                  roughness=1.0, budget_tris=1200, bake_samples=24,
                  smooth_angle=60.0,
                  # Scales are in metres of object space, so a 26 m field
                  # needs numbers an order of magnitude below a 0.8 m block's
                  # or the texture bakes to grey mush.
                  # Streaks are almost off here: at 26 m across a 1024 map
                  # they stretched into visible horizontal banding, which drags
                  # the eye away from the letters standing on the field.
                  gouache=dict(wash=0.17, wash_scale=0.30, grain=0.05,
                               grain_scale=3.2, streak=0.025, streak_scale=0.55,
                               ao_strength=0.30, ao_distance=1.2,
                               edge_light=0.06, edge_dark=0.05))
