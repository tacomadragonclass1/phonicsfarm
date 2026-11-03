"""Geometry conventions for the Painted Storybook look.

Scale: 1 Blender unit = 1 Godot unit = 1 metre. Chuck is 1.21 m, an alphabet
block is 0.80 m, a cottage is about 3.6 m. Authoring at final scale means every
asset drops into a scene at scale 1 and the bevel widths below stay physically
consistent across the whole game.

Up axis: Blender is Z-up, Godot is Y-up. `exporter.py` passes `export_yup`, so
build everything Z-up here and forget about it.

Origins: feet/base at Z = 0, centred on X/Y, unless an engine contract says
otherwise (the alphabet block's origin is its bottom face because
`alphabet_block.gd` positions a 0.8 cube at y = +0.4 above it).

The three rules that make these assets read as one game:

1. BEVEL. Every hard edge gets a bevel. `BEVEL_*` below are real widths in
   metres, so a 2 cm chamfer on a cottage beam and on a toy block catch light
   the same way. Unbevelled edges are what make 3D look like untouched
   primitives.
2. IRREGULARITY. Hand-made surfaces get `wobble()`. A straight wall is a
   factory wall; a wall that leans 1 cm over its height was built by someone.
   Keep it small -- this is a storybook, not a cartoon.
3. SMOOTH BY ANGLE. `finish()` shades smooth with a 38 degree threshold, so a
   bevel reads as a soft rolled edge while a real panel break stays crisp.
"""

import math
import random

import bmesh
import bpy
from mathutils import Vector

# Bevel widths in metres. Pick by how the object was made, not by its size.
BEVEL_TOY = 0.022      # turned or moulded: blocks, pedestal caps, toys
BEVEL_CARPENTRY = 0.016  # sawn timber: beams, window frames, doors
BEVEL_MASONRY = 0.030   # plaster, thatch, stone: soft and worn
BEVEL_FINE = 0.008     # small parts: hinges, glasses, toggles

SMOOTH_ANGLE = math.radians(38.0)


# ---------------------------------------------------------------- scene setup

def reset_scene() -> None:
    """Empty .blend, metric units, Cycles ready for a bake."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    random.seed(20261101)


def deselect_all() -> None:
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
    bpy.context.view_layer.objects.active = None


def activate(obj: bpy.types.Object) -> bpy.types.Object:
    deselect_all()
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


# ---------------------------------------------------------------- primitives

def _new(mesh_op, name: str, color: str, **kwargs) -> bpy.types.Object:
    mesh_op(**kwargs)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name + "Mesh"
    set_part_color(obj, color)
    return obj


def box(name, color, size=(1, 1, 1), at=(0, 0, 0), rot=(0, 0, 0)):
    """Axis-aligned box. `at` is the CENTRE, like every other primitive here."""
    obj = _new(bpy.ops.mesh.primitive_cube_add, name, color, size=1.0,
               location=at, rotation=rot)
    obj.scale = size
    apply_transform(obj)
    return obj


def cylinder(name, color, radius=0.5, depth=1.0, at=(0, 0, 0), rot=(0, 0, 0),
             segments=20):
    return _new(bpy.ops.mesh.primitive_cylinder_add, name, color,
                radius=radius, depth=depth, location=at, rotation=rot,
                vertices=segments)


def cone(name, color, r1=0.5, r2=0.0, depth=1.0, at=(0, 0, 0), rot=(0, 0, 0),
         segments=20):
    return _new(bpy.ops.mesh.primitive_cone_add, name, color, radius1=r1,
                radius2=r2, depth=depth, location=at, rotation=rot,
                vertices=segments)


def gable(name, color, width=1.0, depth=0.2, height=1.0, at=(0, 0, 0),
          along="X"):
    """A triangular prism: the wall that fills the end of a pitched roof.

    `along` is the axis the apex collapses onto -- it must be the axis the
    ROOF SLOPES DOWN, which is not always the building's long axis.

    Built by collapsing the top edge of a box rather than by rotating a
    four-sided cone. `apply_transform` bakes SCALE FIRST and rotation second,
    so scaling a rotated pyramid splays it across both ground axes instead of
    stretching it along one -- which is exactly how the first cottage ended up
    5.5 m deep.
    """
    obj = box(name, color, size=(width, depth, height), at=at)
    axis = {"X": 0, "Y": 1}[along]
    for vert in obj.data.vertices:
        if vert.co.z > 0.0:
            vert.co[axis] = 0.0
    merge_doubles(obj)
    return obj


def ball(name, color, radius=0.5, at=(0, 0, 0), subdiv=2):
    return _new(bpy.ops.mesh.primitive_ico_sphere_add, name, color,
                radius=radius, location=at, subdivisions=subdiv)


def uvball(name, color, radius=0.5, at=(0, 0, 0), segments=20, rings=12):
    return _new(bpy.ops.mesh.primitive_uv_sphere_add, name, color,
                radius=radius, location=at, segments=segments, ring_count=rings)


def blob(name, color, radius=0.5, at=(0, 0, 0), segments=10, rings=7):
    """A cheap round mass. Most of a storybook character is made of these.

    A UV sphere at these counts is about 120 triangles -- a quarter of what an
    icosphere at subdivision 2 costs, and at this art scale the difference is
    invisible. Reach for `uvball` only when a shape is large enough on screen
    to show faceting.
    """
    return uvball(name, color, radius=radius, at=at, segments=segments,
                  rings=rings)


def torus(name, color, major=0.5, minor=0.08, at=(0, 0, 0), rot=(0, 0, 0),
          major_seg=20, minor_seg=8):
    return _new(bpy.ops.mesh.primitive_torus_add, name, color,
                major_radius=major, minor_radius=minor, location=at,
                rotation=rot, major_segments=major_seg,
                minor_segments=minor_seg)


def plane_grid(name, color, size=(1, 1), divisions=(1, 1), at=(0, 0, 0)):
    obj = _new(bpy.ops.mesh.primitive_grid_add, name, color, size=1.0,
               location=at, x_subdivisions=divisions[0] + 1,
               y_subdivisions=divisions[1] + 1)
    obj.scale = (size[0], size[1], 1.0)
    apply_transform(obj)
    return obj


# ---------------------------------------------------------------- part colour

def set_part_color(obj: bpy.types.Object, palette_name: str) -> None:
    """Stamp a palette colour onto the mesh as vertex colours.

    This is the hinge of the whole pipeline. Parts are coloured individually
    and then JOINED; the colour survives the join, so one finished asset has
    one material whose base colour is read from the `Paint` attribute. That is
    how a cottage with eleven colours still costs exactly one draw call and one
    texture.
    """
    from . import palette
    mesh = obj.data
    mesh.attributes.new(name="Paint", type="FLOAT_COLOR", domain="CORNER") \
        if "Paint" not in mesh.attributes else None
    rgba = palette.linear(palette_name)
    layer = mesh.attributes["Paint"]
    for i in range(len(mesh.loops)):
        layer.data[i].color = rgba
    obj["paint"] = palette_name


def paint_by_normal(obj, up, mid, down, up_at=0.55, down_at=-0.35) -> None:
    """Blend three palette colours across a form by which way it faces.

    Use this, not `repaint_faces`, on anything organic. A per-face test on a
    low-polygon remeshed canopy paints whole facets light or dark and the
    result reads as camouflage; blending on the SMOOTH vertex normal gives a
    continuous gradient from a sunlit crown to a shaded underside, which is
    the single strongest "hand-painted" cue a foliage mass has.
    """
    from . import palette
    up_rgba = palette.linear(up)
    mid_rgba = palette.linear(mid)
    down_rgba = palette.linear(down)
    layer = obj.data.attributes["Paint"]
    normals = [v.normal.z for v in obj.data.vertices]
    for poly in obj.data.polygons:
        for loop_index, vert_index in zip(poly.loop_indices, poly.vertices):
            nz = normals[vert_index]
            if nz >= 0.0:
                t = min(nz / max(up_at, 1e-6), 1.0)
                base, target = mid_rgba, up_rgba
            else:
                t = min(nz / min(down_at, -1e-6), 1.0)
                base, target = mid_rgba, down_rgba
            layer.data[loop_index].color = tuple(
                base[i] + (target[i] - base[i]) * t for i in range(4))


def flare_base(obj, height=0.35, strength=0.9) -> None:
    """Swell the bottom of a trunk or post into the ground.

    Smooth, so it reads as growth. Separate root cones were tried first and
    read as loose blocks lying next to the tree.
    """
    for vert in obj.data.vertices:
        local_top = height - obj.location.z
        if vert.co.z < local_top:
            t = 1.0 - max(vert.co.z - (-obj.location.z), 0.0) / max(
                local_top + obj.location.z, 1e-6)
            factor = 1.0 + strength * (t ** 2.2)
            vert.co.x *= factor
            vert.co.y *= factor


def repaint_faces(obj, predicate, palette_name) -> int:
    """Recolour only the faces `predicate(face_centre_world, normal)` accepts.

    Used for things like painting just the top of a canopy lighter, or the
    riser of a step, without splitting the mesh into another object.
    """
    from . import palette
    mesh = obj.data
    rgba = palette.linear(palette_name)
    layer = mesh.attributes["Paint"]
    touched = 0
    for poly in mesh.polygons:
        centre = obj.matrix_world @ poly.center
        normal = (obj.matrix_world.to_3x3() @ poly.normal).normalized()
        if predicate(centre, normal):
            for li in poly.loop_indices:
                layer.data[li].color = rgba
            touched += 1
    return touched


# ---------------------------------------------------------------- deformation

def apply_transform(obj, location=False, rotation=True, scale=True) -> None:
    activate(obj)
    bpy.ops.object.transform_apply(location=location, rotation=rotation,
                                   scale=scale)


def wobble(obj, amount=0.012, scale=2.2, seed=0, axis_bias=(1, 1, 1)) -> None:
    """Push vertices around with smooth noise so nothing is machine-flat.

    `amount` is a displacement in metres. Above ~0.03 on a wall it stops
    reading as "hand-built" and starts reading as "melted", so keep it small
    and let the eye find it rather than see it.
    """
    rng = random.Random(seed or 1)
    offs = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50),
                   rng.uniform(-50, 50)))
    mesh = obj.data
    for vert in mesh.vertices:
        p = (vert.co * scale) + offs
        d = Vector((_noise3(p.x, p.y, p.z),
                    _noise3(p.y + 11.3, p.z, p.x),
                    _noise3(p.z, p.x + 7.7, p.y)))
        vert.co += Vector((d.x * axis_bias[0], d.y * axis_bias[1],
                           d.z * axis_bias[2])) * amount


def _noise3(x, y, z) -> float:
    """Cheap smooth value noise in -1..1. Deterministic across runs."""
    import mathutils.noise as bnoise
    return bnoise.noise(Vector((x, y, z))) * 2.0


def lean(obj, degrees=1.6, axis="Y", pivot_z=0.0) -> None:
    """Tilt an object about its base. Storybook buildings are never plumb.

    `pivot_z` is a WORLD height. See the note on `taper`.
    """
    activate(obj)
    rad = math.radians(degrees)
    index = {"X": 0, "Y": 1, "Z": 2}[axis]
    pivot_z -= obj.location.z
    for vert in obj.data.vertices:
        h = vert.co.z - pivot_z
        if index == 1:
            vert.co.x += math.sin(rad) * h
        else:
            vert.co.y += math.sin(rad) * h


def taper(obj, top_scale=0.94, bottom_z=0.0, top_z=1.0) -> None:
    """Narrow an object toward its top -- reads as weight bearing down.

    HEIGHTS ARE WORLD HEIGHTS. Vertices live in object space with the origin
    wherever the primitive was placed, so a call written against world heights
    (which is how anyone thinks about a building) silently does nothing, or
    everything. `obj.location.z` is subtracted here so the call site can say
    what it means. Call before rotating the object.
    """
    bottom_z -= obj.location.z
    top_z -= obj.location.z
    span = max(top_z - bottom_z, 1e-6)
    for vert in obj.data.vertices:
        t = min(max((vert.co.z - bottom_z) / span, 0.0), 1.0)
        factor = 1.0 + (top_scale - 1.0) * t
        vert.co.x *= factor
        vert.co.y *= factor


def sag(obj, depth=0.06, along="X", span=1.0) -> None:
    """Drop the middle of a span. A roof ridge that sags has been there years."""
    index = 0 if along == "X" else 1
    for vert in obj.data.vertices:
        t = min(max(abs(vert.co[index]) / max(span, 1e-6), 0.0), 1.0)
        vert.co.z -= depth * (1.0 - t * t)


def bend(obj, degrees=10.0, bottom_z=0.0, top_z=1.0, axis="Y") -> None:
    """Curve a trunk or chimney over its height. World heights, as `taper`."""
    bottom_z -= obj.location.z
    top_z -= obj.location.z
    span = max(top_z - bottom_z, 1e-6)
    rad = math.radians(degrees)
    for vert in obj.data.vertices:
        t = min(max((vert.co.z - bottom_z) / span, 0.0), 1.0)
        offset = (1.0 - math.cos(rad * t)) / max(rad, 1e-6) * span * rad
        if axis == "Y":
            vert.co.x += offset * t
        else:
            vert.co.y += offset * t


# ---------------------------------------------------------------- finishing

def bevel(obj, width=BEVEL_TOY, segments=2, angle_limit=48.0,
          clamp=True) -> None:
    activate(obj)
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angle_limit)
    mod.use_clamp_overlap = clamp
    mod.harden_normals = False
    mod.miter_outer = "MITER_ARC"
    bpy.ops.object.modifier_apply(modifier=mod.name)


def subdivide(obj, levels=1, smooth=True) -> None:
    activate(obj)
    mod = obj.modifiers.new("Subsurf", "SUBSURF")
    mod.levels = levels
    mod.render_levels = levels
    if not smooth:
        mod.subdivision_type = "SIMPLE"
    bpy.ops.object.modifier_apply(modifier=mod.name)


def remesh_organic(obj, voxel=0.05, adaptivity=0.0) -> None:
    """Fuse overlapping masses into one organic skin. Foliage, rocks, hair."""
    activate(obj)
    mod = obj.modifiers.new("Remesh", "REMESH")
    mod.mode = "VOXEL"
    mod.voxel_size = voxel
    mod.adaptivity = adaptivity
    mod.use_smooth_shade = False
    bpy.ops.object.modifier_apply(modifier=mod.name)


def decimate(obj, ratio=0.4, angle=None) -> None:
    activate(obj)
    mod = obj.modifiers.new("Decimate", "DECIMATE")
    if angle is not None:
        mod.decimate_type = "DISSOLVE"
        mod.angle_limit = math.radians(angle)
    else:
        mod.ratio = ratio
    bpy.ops.object.modifier_apply(modifier=mod.name)


def shrink_to_budget(obj, max_tris: int) -> None:
    """Decimate only as far as the budget actually requires."""
    tris = tri_count(obj)
    if tris <= max_tris:
        return
    decimate(obj, ratio=max(0.05, max_tris / float(tris)))


def merge_doubles(obj, distance=0.0006) -> None:
    activate(obj)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)
    bm.to_mesh(obj.data)
    bm.free()


def finish(obj, angle=SMOOTH_ANGLE) -> None:
    """Smooth-by-angle. The last thing done to every finished mesh."""
    activate(obj)
    bpy.ops.object.shade_auto_smooth(angle=angle)


def join(objects, name) -> bpy.types.Object:
    """Join parts into the finished asset. Vertex colours survive."""
    objects = [o for o in objects if o and o.name in bpy.data.objects]
    deselect_all()
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    merged = bpy.context.active_object
    merged.name = name
    merged.data.name = name + "Mesh"
    return merged


def mirror_x(obj, name=None):
    """Duplicate across X. Returns the new object; join it yourself."""
    activate(obj)
    bpy.ops.object.duplicate()
    copy = bpy.context.active_object
    copy.name = name or (obj.name + "_R")
    for vert in copy.data.vertices:
        vert.co.x = -vert.co.x
    copy.data.flip_normals()
    return copy


def clamp_axis(obj, axis="Y", limit=-0.14, softness=0.45) -> None:
    """Flatten one side of a form, softly.

    A face is not a sphere. Pressing the front of a head back toward a plane
    is what gives features somewhere to SIT, and it is the difference between
    a character and a decorated ball.
    """
    index = {"X": 0, "Y": 1, "Z": 2}[axis]
    for vert in obj.data.vertices:
        value = vert.co[index]
        if limit < 0 and value < limit:
            vert.co[index] = limit + (value - limit) * softness
        elif limit > 0 and value > limit:
            vert.co[index] = limit + (value - limit) * softness


def set_origin(obj, point=(0, 0, 0)) -> None:
    """Move the origin to a world point without moving the geometry."""
    offset = Vector(point) - obj.location
    for vert in obj.data.vertices:
        vert.co -= offset
    obj.location = Vector(point)


def drop_to_floor(obj, floor=0.0) -> None:
    lowest = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
    obj.location.z += floor - lowest


def tri_count(obj) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def bounds(obj):
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts),
                 min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts),
                 max(p.z for p in pts)))
    return mn, mx
