"""Render a comparison sheet per direction.

    blender --background --python art_src/explore/render_study.py -- d1 d2 d3

Imports the EXPORTED GLBs rather than the .blend sources, so what is compared
is exactly what Godot would receive -- baked texture, final material, final
triangle count. The camera is the game's: orthographic, pitch 30, yaw 30.

All four subjects share one frame at true relative scale. That matters more
than four beauty shots: the thing being judged is whether a cottage, a tree, a
character and a toy block look like they belong to the SAME world.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

sys.path.insert(0, HERE)

import common  # noqa: E402,F401  -- importing it registers the direction palettes
from sb_lib import palette  # noqa: E402

PROJECT = os.path.dirname(os.path.dirname(HERE))
GLB_DIR = os.path.join(PROJECT, "assets", "storybook", "explore")
OUT_DIR = os.path.join(PROJECT, "art_src", "review")

# Where each subject stands. Laid out so the cottage reads behind, the tree
# frames the right, and the two things a child actually touches -- Chuck and a
# block -- are together at the front where they can be compared directly.
LAYOUT = [
    ("cottage", (-2.55, 2.25, 0.0), 18.0),
    ("tree", (2.95, 1.55, 0.0), -24.0),
    ("chuck", (-0.55, -1.55, 0.0), 14.0),
    ("block", (1.25, -2.15, 0.0), -22.0),
]

GROUND = {"d1": "c_ground", "d2": "g_ground", "d3": "s_ground",
          "hybrid": "hb_ground"}


def studio(ground_colour, width=11.6, look=(0, 0, 1.35)):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 56
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1300
    scene.render.resolution_y = 820

    world = bpy.data.worlds.new("Study")
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs[0].default_value = (0.66, 0.74, 0.76, 1.0)
    background.inputs[1].default_value = 0.42
    scene.world = world

    bpy.ops.mesh.primitive_plane_add(size=140, location=(0, 0, 0))
    ground = bpy.context.active_object
    material = bpy.data.materials.new("StudyGround")
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = palette.linear(ground_colour)
    bsdf.inputs["Roughness"].default_value = 1.0
    ground.data.materials.append(material)

    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 3.1
    sun_data.angle = math.radians(5.0)
    sun_data.color = (1.0, 0.95, 0.86)
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(40.0), 0.0, math.radians(28.0))

    camera_data = bpy.data.cameras.new("Study")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = width
    camera = bpy.data.objects.new("Study", camera_data)
    bpy.context.collection.objects.link(camera)
    pitch, yaw = math.radians(30.0), math.radians(30.0)
    direction = Vector((math.sin(yaw) * math.cos(pitch),
                        -math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
    camera.location = Vector(look) + direction * 40.0
    camera.rotation_euler = (math.radians(90.0) - pitch, 0.0, yaw)
    scene.camera = camera


def place(path, location, spin):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    imported = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in imported if o.parent is None]
    for root in roots:
        root.location = Vector(location)
        root.rotation_euler = (0.0, 0.0, math.radians(spin))
    return imported


def render(direction):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    studio(GROUND.get(direction, "stone"))
    found = 0
    for subject, location, spin in LAYOUT:
        path = os.path.join(GLB_DIR, "%s_%s.glb" % (direction, subject))
        if not os.path.exists(path):
            print("[study] missing", os.path.basename(path))
            continue
        place(path, location, spin)
        found += 1
    if not found:
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.context.scene.render.filepath = os.path.join(
        OUT_DIR, "study_%s.png" % direction)
    bpy.ops.render.render(write_still=True)
    print("[study] wrote", bpy.context.scene.render.filepath)


def lineup(subject, directions, width, look):
    """One subject, all three directions side by side."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    studio("stone", width=width, look=look)
    spacing = width / 3.2
    for index, direction in enumerate(directions):
        path = os.path.join(GLB_DIR, "%s_%s.glb" % (direction, subject))
        if not os.path.exists(path):
            continue
        offset = (index - 1) * spacing
        place(path, (offset * 0.866, -offset * 0.5, 0.0), 16.0)
    bpy.context.scene.render.filepath = os.path.join(
        OUT_DIR, "lineup_%s.png" % subject)
    bpy.ops.render.render(write_still=True)
    print("[study] wrote", bpy.context.scene.render.filepath)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    wanted = [a for a in args if a in GROUND] or ["d1", "d2", "d3"]
    if "hybrid" in wanted:
        # Imported ONLY on demand: hybrid.py re-points the study palettes onto
        # the house family, so importing it at module scope would silently
        # re-render d1/d2/d3 in the wrong colours.
        import hybrid  # noqa: F401
    if "lineup" in args:
        for subject, width, look in (("tree", 11.0, (0, 0, 1.3)),
                                     ("cottage", 14.0, (0, 0, 1.6)),
                                     ("chuck", 5.2, (0, 0, 0.7)),
                                     ("block", 3.4, (0, 0, 0.4))):
            lineup(subject, wanted, width, look)
    else:
        for direction in wanted:
            render(direction)
