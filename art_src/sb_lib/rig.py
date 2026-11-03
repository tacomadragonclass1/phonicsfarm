"""Skeleton, skin weights and animation for storybook characters.

Weights are computed here rather than left to Blender's heat-map auto-weights,
for a practical reason: a storybook character is a UNION of separate shapes --
a head, a jumper, two boots -- and heat weighting routinely fails or produces
artefacts on meshes that are not one closed surface. Inverse-distance-to-bone
weighting is deterministic, runs the same every build, and for chunky,
cartoon proportions it is also simply better: the falloff power below is high
enough that a limb moves almost rigidly, with a soft blend only across the
joint itself.

Animations are authored as Blender actions and exported as glTF animations.
`exporter.rename_glb_animations` then forces the names `player.gd` looks up.
"""

import math

import bpy
from mathutils import Vector


class Rig:
    """A bone chain plus the weighting rules that bind a mesh to it."""

    def __init__(self, name="Armature"):
        bpy.ops.object.armature_add(enter_editmode=False, location=(0, 0, 0))
        self.object = bpy.context.active_object
        self.object.name = name
        self.object.data.name = name + "Data"
        self.segments = {}
        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones = self.object.data.edit_bones
        for bone in list(edit_bones):
            edit_bones.remove(bone)
        bpy.ops.object.mode_set(mode="OBJECT")

    def bone(self, name, head, tail, parent=None, connected=False):
        bpy.context.view_layer.objects.active = self.object
        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones = self.object.data.edit_bones
        bone = edit_bones.new(name)
        bone.head = Vector(head)
        bone.tail = Vector(tail)
        if parent:
            bone.parent = edit_bones[parent]
            bone.use_connect = connected
        bpy.ops.object.mode_set(mode="OBJECT")
        self.segments[name] = (Vector(head), Vector(tail))
        return name

    # -------------------------------------------------------------- binding

    def bind(self, mesh, falloff=5.0, influences=3, prefer=None,
             prefer_weight=0.55):
        """Attach `mesh` with inverse-distance weights.

        `prefer` maps a bone name to a predicate on the vertex's local
        position. A vertex the predicate accepts gets that bone's weight
        lifted to at least `prefer_weight`, which is how the hair, the
        glasses and the boots stay welded to the part they belong to instead
        of being half-claimed by whatever bone happens to pass nearby.
        """
        for name in self.segments:
            if name not in mesh.vertex_groups:
                mesh.vertex_groups.new(name=name)

        names = list(self.segments)
        for vert in mesh.data.vertices:
            point = mesh.matrix_world @ vert.co
            scores = []
            for name in names:
                head, tail = self.segments[name]
                distance = _point_to_segment(point, head, tail)
                scores.append((name, 1.0 / ((distance + 0.012) ** falloff)))
            scores.sort(key=lambda item: -item[1])
            top = scores[:influences]
            total = sum(weight for _, weight in top) or 1.0
            weights = {name: weight / total for name, weight in top}

            if prefer:
                for name, predicate in prefer.items():
                    if predicate(point):
                        weights = {name: prefer_weight}
                        remaining = 1.0 - prefer_weight
                        others = [(n, w) for n, w in top if n != name]
                        spread = sum(w for _, w in others) or 1.0
                        for other, weight in others:
                            weights[other] = remaining * weight / spread
                        break

            for name, weight in weights.items():
                if weight > 0.001:
                    mesh.vertex_groups[name].add([vert.index], weight, "REPLACE")

        modifier = mesh.modifiers.new("Armature", "ARMATURE")
        modifier.object = self.object
        mesh.parent = self.object

    # ------------------------------------------------------------ animation

    def action(self, name, frames):
        """Build one action. `frames` is {frame: {bone: pose}}.

        A pose is a dict with any of `rot` (XYZ degrees), `loc` (metres) and
        `scale`. Everything is relative to the rest pose.
        """
        armature = self.object
        armature.animation_data_create()
        action = bpy.data.actions.new(name)
        action.use_fake_user = True
        armature.animation_data.action = action

        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="POSE")
        for bone in armature.pose.bones:
            bone.rotation_mode = "XYZ"

        for frame in sorted(frames):
            bpy.context.scene.frame_set(frame)
            for bone in armature.pose.bones:
                bone.location = (0, 0, 0)
                bone.rotation_euler = (0, 0, 0)
                bone.scale = (1, 1, 1)
            for bone_name, pose in frames[frame].items():
                bone = armature.pose.bones[bone_name]
                if "rot" in pose:
                    bone.rotation_euler = tuple(math.radians(a)
                                                for a in pose["rot"])
                if "loc" in pose:
                    bone.location = Vector(pose["loc"])
                if "scale" in pose:
                    bone.scale = Vector(pose["scale"])
            for bone in armature.pose.bones:
                bone.keyframe_insert("rotation_euler", frame=frame)
                bone.keyframe_insert("location", frame=frame)
                bone.keyframe_insert("scale", frame=frame)

        for fcurve in _fcurves(action):
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "BEZIER"
                keyframe.easing = "EASE_IN_OUT"

        bpy.ops.object.mode_set(mode="OBJECT")
        armature.animation_data.action = None
        return action


def _fcurves(action):
    """Blender 5 moved an action's curves into layers/strips/channelbags."""
    if hasattr(action, "fcurves"):
        return list(action.fcurves)
    curves = []
    for layer in action.layers:
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                curves.extend(bag.fcurves)
    return curves


def _point_to_segment(point, head, tail):
    span = tail - head
    length_squared = span.dot(span)
    if length_squared < 1e-9:
        return (point - head).length
    t = max(0.0, min(1.0, (point - head).dot(span) / length_squared))
    return (point - (head + span * t)).length


def swing(amplitude, phase, frames):
    """Sine over a loop, in degrees. Keeps cycle maths out of build scripts."""
    return [amplitude * math.sin(2 * math.pi * (f / frames + phase))
            for f in range(frames)]
