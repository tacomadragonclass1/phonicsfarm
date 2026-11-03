"""Render a review sheet for finished assets, from their saved .blend sources.

    blender --background --python art_src/render_review.py -- block chuck

Cycles on the CPU, because this has to work over SSH and in a shell with no
compositor. The camera copies the game's: orthographic, pitch 30, yaw 30 --
so a judgement made here is a judgement about how the asset actually reads in
Phonics Farm, not about a beauty render.

Output goes to `art_src/review/`, which is an authoring folder and not part of
the game.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from sb_lib import palette  # noqa: E402

BLEND_DIR = os.path.join(HERE, "blend")
OUT_DIR = os.path.join(HERE, "review")

# How wide a frame each asset wants, in metres. Keep these honest: a block
# reviewed at 1.4 m is reviewed at roughly the size a child sees it.
FRAMING = {
    "block": (1.5, (0, 0, 0.40)),
    "chuck": (1.9, (0, 0, 0.62)),
    "cottage": (5.4, (0, 0, 1.70)),
    "tree": (4.2, (0, 0, 1.50)),
    "pedestal": (1.9, (0, 0, 0.35)),
    "path_stone": (1.6, (0, 0, 0.05)),
    "meadow": (16.0, (0, 0, 0.0)),
    # Detail framings, for checking one feature rather than a silhouette.
    "cottage_door": (2.0, (-0.52, -1.3, 1.45)),
}

# Detail framings reuse another asset's .blend.
SOURCE = {"cottage_door": "cottage"}


def _studio(width_m, look, frame_w=900, frame_h=700):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = frame_w
    scene.render.resolution_y = frame_h
    scene.render.film_transparent = False

    world = bpy.data.worlds.new("Review")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.74, 0.78, 1.0)
    bg.inputs[1].default_value = 0.85
    scene.world = world

    # A ground card in the meadow colour, so silhouettes are judged against
    # the value they will actually sit on.
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, 0))
    ground = bpy.context.active_object
    mat = bpy.data.materials.new("ReviewGround")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = \
        palette.linear("grass")
    mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
    ground.data.materials.append(mat)

    sun = bpy.data.lights.new("Sun", type="SUN")
    sun.energy = 3.2
    sun.angle = math.radians(4.0)
    sun.color = (1.0, 0.94, 0.84)
    sun_obj = bpy.data.objects.new("Sun", sun)
    bpy.context.collection.objects.link(sun_obj)
    # Matches scenes/main.tscn's DirectionalLight3D (-52 pitch, -25 yaw) once
    # converted from Godot's Y-up to Blender's Z-up.
    sun_obj.rotation_euler = (math.radians(38.0), 0.0, math.radians(25.0))

    camera_data = bpy.data.cameras.new("Review")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = width_m
    camera = bpy.data.objects.new("Review", camera_data)
    bpy.context.collection.objects.link(camera)
    pitch, yaw = math.radians(30.0), math.radians(30.0)
    direction = Vector((math.sin(yaw) * math.cos(pitch),
                        -math.cos(yaw) * math.cos(pitch),
                        math.sin(pitch)))
    camera.location = Vector(look) + direction * 30.0
    camera.rotation_euler = (math.radians(90.0) - pitch, 0.0, yaw)
    bpy.context.scene.camera = camera


def render(spec):
    """`spec` is "name", or "name:action:frame" to review a pose."""
    name, _, pose = spec.partition(":")
    blend = os.path.join(BLEND_DIR, SOURCE.get(name, name) + ".blend")
    if not os.path.exists(blend):
        print("[review] no source for", name)
        return
    bpy.ops.wm.open_mainfile(filepath=blend)
    for light in [o for o in bpy.data.objects if o.type in {"LIGHT", "CAMERA"}]:
        bpy.data.objects.remove(light, do_unlink=True)
    label = name
    if pose:
        action_name, _, frame = pose.partition(":")
        armature = next((o for o in bpy.data.objects if o.type == "ARMATURE"),
                        None)
        action = next((a for a in bpy.data.actions
                       if action_name in a.name), None)
        if armature and action:
            armature.animation_data_create()
            armature.animation_data.action = action
            if hasattr(armature.animation_data, "action_slot"):
                slots = getattr(action, "slots", [])
                if slots:
                    armature.animation_data.action_slot = slots[0]
            bpy.context.scene.frame_set(int(frame or 1))
            label = "%s_%s_%s" % (name, action_name, frame or 1)
        else:
            print("[review] no action", action_name, "on", name)
    width, look = FRAMING.get(name, (3.0, (0, 0, 0.5)))
    _studio(width, look)
    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR, label + ".png")
    bpy.ops.render.render(write_still=True)
    print("[review] wrote", bpy.context.scene.render.filepath)


if __name__ == "__main__":
    wanted = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for item in wanted or [k for k in sorted(FRAMING) if k not in SOURCE]:
        render(item)
