"""Review renders for the rebuilt village.

    blender --background --python art_src/explore/render_village.py
    blender --background --python art_src/explore/render_village.py -- pair

Same lighting rig and tone mapping as `render_foundation.py`, imported rather
than restated, so a village building and the home cottage can be compared
without the light being a variable.

`pair` is the one that matters most: Annette beside Chuck at true relative
scale. Two characters in a game for five-year-olds have to be
distinguishable as SILHOUETTES, and that is not something a close-up of
either one can tell you.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import common  # noqa: E402,F401
import foundation  # noqa: E402,F401
import village  # noqa: E402,F401
import render_foundation as R  # noqa: E402

PROJECT = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(PROJECT, "art_src", "review")
VILLAGE_GLB = os.path.join(PROJECT, "assets", "storybook", "village")
FOUND_GLB = os.path.join(PROJECT, "assets", "storybook", "explore")

BUILDINGS = ["windmill", "clock_house", "bakery", "bookshop", "flower_shop",
             "workshop"]


def ground(colour="f_grass"):
    from sb_lib import palette
    bpy.ops.mesh.primitive_plane_add(size=220, location=(0, 0, 0))
    plane = bpy.context.active_object
    material = bpy.data.materials.new("Ground")
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = palette.linear(colour)
    bsdf.inputs["Roughness"].default_value = 1.0
    plane.data.materials.append(material)


def place(path, at, spin=0.0):
    if not os.path.exists(path):
        print("[village] MISSING", os.path.basename(path))
        return
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    for root in [o for o in bpy.data.objects
                 if o not in before and o.parent is None]:
        root.location = Vector(at)
        root.rotation_euler = (0.0, 0.0, math.radians(spin))


def lineup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    R.studio((2000, 760), samples=96)
    ground()
    # Spaced by their own footprints rather than evenly, so the sheet reads
    # as a street and the relative sizes stay honest.
    cursor = -13.0
    for name in BUILDINGS:
        place(os.path.join(VILLAGE_GLB, "%s.glb" % name), (cursor, 0.0, 0.0),
              spin=16.0)
        cursor += 5.1
    # Chuck at the end for scale. A village of buildings with nothing to
    # measure them against is a village of unknown size.
    place(os.path.join(FOUND_GLB, "foundation_chuck.glb"), (cursor - 1.4, -2.6, 0.0),
          spin=18.0)
    R.camera((-0.9, -0.6, 2.4), 32.0, pitch=22.0, yaw=26.0)
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR,
                                                     "village_lineup.png")
    bpy.ops.render.render(write_still=True)
    print("[village] wrote village_lineup.png")


def pair():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    R.studio((1200, 1000), samples=110)
    ground()
    place(os.path.join(FOUND_GLB, "foundation_chuck.glb"), (-0.62, 0.0, 0.0),
          spin=16.0)
    place(os.path.join(VILLAGE_GLB, "annette.glb"), (0.62, 0.0, 0.0),
          spin=-14.0)
    R.camera((0.0, 0.0, 0.84), 2.75, pitch=12.0, yaw=18.0)
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR,
                                                     "village_pair.png")
    bpy.ops.render.render(write_still=True)
    print("[village] wrote village_pair.png")


def annette():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    R.studio((1050, 1300), samples=110)
    ground()
    place(os.path.join(VILLAGE_GLB, "annette.glb"), (0.0, 0.0, 0.0), spin=-16.0)
    R.camera((0.0, 0.0, 1.06), 1.35, pitch=10.0, yaw=20.0)
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR,
                                                     "village_annette.png")
    bpy.ops.render.render(write_still=True)
    print("[village] wrote village_annette.png")


PROPS = [("well", 0.0), ("fingerpost", 0.0), ("bench", 0.0),
         ("planter", 0.0), ("bunting", 0.0), ("tree_b", 0.0),
         ("bush", 0.0), ("mushrooms", 0.0), ("blossom", 0.0),
         ("lane_stone", 0.0), ("wall_run", 0.0)]


def props():
    """Everything that replaces the 144 Kenney instances, in one frame."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    R.studio((2000, 720), samples=96)
    ground()
    cursor = -9.6
    for name, _ in PROPS:
        gap = {"bunting": 3.6, "wall_run": 3.2, "tree_b": 2.3}.get(name, 1.55)
        place(os.path.join(VILLAGE_GLB, "%s.glb" % name), (cursor, 0.0, 0.0),
              spin=18.0)
        cursor += gap
    place(os.path.join(FOUND_GLB, "foundation_chuck.glb"),
          (cursor + 0.3, -0.5, 0.0), spin=18.0)
    R.camera((-0.4, -0.3, 1.1), 24.0, pitch=18.0, yaw=24.0)
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR,
                                                     "village_props.png")
    bpy.ops.render.render(write_still=True)
    print("[village] wrote village_props.png")


def mound():
    """The mill mound with the mill on it, and the village it looks over.

    Rendered with the buildings below BECAUSE the whole point of the feature
    is the view from the top. A mound photographed on its own is a lump.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)
    R.studio((1900, 980), samples=96)
    ground()
    place(os.path.join(VILLAGE_GLB, "mill_mound.glb"), (0.0, 0.0, 0.0))
    place(os.path.join(VILLAGE_GLB, "windmill.glb"), (-1.1, -0.5, 2.15),
          spin=28.0)
    place(os.path.join(VILLAGE_GLB, "bench.glb"), (2.0, -2.5, 2.15), spin=152.0)
    # The village below, on the side the parapet looks over.
    for name, at, spin in (("bakery", (-6.2, -11.0, 0.0), 22.0),
                           ("bookshop", (-1.4, -12.6, 0.0), -8.0),
                           ("clock_house", (3.9, -11.2, 0.0), 14.0),
                           ("flower_shop", (8.6, -9.4, 0.0), -24.0)):
        place(os.path.join(VILLAGE_GLB, "%s.glb" % name), at, spin)
    place(os.path.join(VILLAGE_GLB, "well.glb"), (1.2, -7.6, 0.0))
    place(os.path.join(VILLAGE_GLB, "tree_b.glb"), (-8.6, -5.2, 0.0), spin=30.0)
    place(os.path.join(FOUND_GLB, "foundation_chuck.glb"), (5.1, 2.4, 0.42),
          spin=-120.0)
    R.camera((0.4, -3.4, 2.1), 24.0, pitch=24.0, yaw=34.0)
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR,
                                                     "village_mound.png")
    bpy.ops.render.render(write_still=True)
    print("[village] wrote village_mound.png")


VIEWS = {"lineup": lineup, "pair": pair, "annette": annette, "props": props,
         "mound": mound}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name in [a for a in args if a in VIEWS] or list(VIEWS):
        VIEWS[name]()
