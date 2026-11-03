"""Copy me to start a new Painted Storybook asset.

    blender --background --python art_src/template_asset.py

Read `art_src/README.md` first. The rules that matter:

  * build Z-up, at final metre scale, base at Z = 0
  * colour each part with a PALETTE NAME, never a literal colour
  * bevel everything, then `finish()` to smooth by angle
  * hand `produce()` the finished objects and let it surface, bake and export
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sb_lib import asset, meshtools   # noqa: E402

NAME = "template"


def build():
    meshtools.reset_scene()

    body = meshtools.box("Body", "plaster", size=(0.6, 0.6, 0.9),
                         at=(0, 0, 0.45))
    meshtools.taper(body, top_scale=0.9, bottom_z=0.0, top_z=0.9)
    meshtools.wobble(body, amount=0.008, seed=3)
    meshtools.bevel(body, meshtools.BEVEL_MASONRY, segments=2)

    cap = meshtools.cylinder("Cap", "terracotta", radius=0.34, depth=0.12,
                             at=(0, 0, 0.94), segments=16)
    meshtools.bevel(cap, meshtools.BEVEL_TOY, segments=2)

    merged = meshtools.join([body, cap], NAME.capitalize())
    meshtools.drop_to_floor(merged)
    return [merged]


if __name__ == "__main__":
    asset.produce(NAME, build(), texture=asset.TEXTURE_SMALL,
                  budget_tris=800)
