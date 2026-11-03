"""Form generators for shapes that are DESIGNED rather than assembled.

Phase 1 built everything out of boxes, cylinders, cones and spheres. That is
the same vocabulary every asset pack uses, and it is why swapping Kenney for
Blender changed the source of the models without changing the look of them: a
trunk plus a cluster of spheres reads as "asset-pack tree" no matter how
nicely it is textured.

Nothing in this module is a primitive. Each generator takes a profile, an
outline or a path that was DRAWN -- a list of numbers an art director chose --
and builds a surface from it. The shape comes from the drawing, not from a
parameterised ball.

    lathe()   revolve a hand-drawn silhouette      bodies, trunks, pots, caps
    loft()    bridge a stack of outlines           buildings whose plan changes
    sweep()   tube along a path, varying radius    calligraphic trunks, branches
    pad()     scalloped lens                       layered foliage, leaf masses
    superform() superellipsoid                     squircle toys, soft cubes
    ribbon()  swept flat strip                     roof sweeps, brims, collars

plus deformers that leave a HAND on the surface rather than noise:

    press()   flatten against a plane with falloff   thumb-pressed clay
    dents()   local dimples at chosen points         tool marks, knuckle prints
    facet()   planar decimate + flat shade           carved, crystalline planes
    swell()   push outward along normals by a mask   bulges, bellies, cheeks
"""

import math
import random

import bmesh
import bpy
from mathutils import Vector


# ----------------------------------------------------------------- curves

def spline(points, samples=24, closed=False, tension=0.0):
    """Catmull-Rom through `points`. The drawing tool for every path here."""
    pts = [Vector(p) for p in points]
    if len(pts) < 2:
        return pts
    if closed:
        control = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        control = [pts[0] + (pts[0] - pts[1])] + pts + \
                  [pts[-1] + (pts[-1] - pts[-2])]
    out = []
    span = len(pts) if closed else len(pts) - 1
    for segment in range(span):
        p0, p1, p2, p3 = control[segment:segment + 4]
        for step in range(samples):
            t = step / float(samples)
            t2, t3 = t * t, t * t * t
            out.append(0.5 * (
                (2 * p1) + (-p0 + p2) * t +
                (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                (-p0 + 3 * p1 - 3 * p2 + p3) * t3) * (1.0 - tension)
                + p1 * tension)
    if not closed:
        out.append(pts[-1])
    return out


def _finish(bm, name, color):
    from . import meshtools
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    meshtools.set_part_color(obj, color)
    return obj


# ------------------------------------------------------------------ lathe

def lathe(name, color, profile, segments=16, at=(0, 0, 0), smooth_profile=0,
          twist=0.0):
    """Revolve a drawn silhouette `[(radius, z), ...]` around Z.

    This is how a shape gets a SILHOUETTE instead of a bounding box. A trunk
    that swells at the base, pinches at the neck and flares again under the
    canopy is six numbers here and is impossible with a cone.

    A radius of 0 at either end closes that end into a point.
    """
    if smooth_profile:
        profile = [(p.x, p.y) for p in
                   spline([(r, z) for r, z in profile], smooth_profile)]

    bm = bmesh.new()
    rings, origin = [], Vector(at)
    for radius, z in profile:
        if abs(radius) < 1e-6:
            rings.append([bm.verts.new(origin + Vector((0, 0, z)))])
            continue
        ring = []
        for s in range(segments):
            angle = 2 * math.pi * s / segments + twist * z
            ring.append(bm.verts.new(origin + Vector(
                (math.cos(angle) * radius, math.sin(angle) * radius, z))))
        rings.append(ring)

    for i in range(len(rings) - 1):
        lower, upper = rings[i], rings[i + 1]
        if len(lower) == 1:
            for s in range(segments):
                bm.faces.new([lower[0], upper[s], upper[(s + 1) % segments]])
        elif len(upper) == 1:
            for s in range(segments):
                bm.faces.new([lower[s], lower[(s + 1) % segments], upper[0]])
        else:
            for s in range(segments):
                t = (s + 1) % segments
                bm.faces.new([lower[s], lower[t], upper[t], upper[s]])

    if len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    return _finish(bm, name, color)


# ------------------------------------------------------------------- loft

def loft(name, color, stations, close_bottom=True, close_top=True,
         at=(0, 0, 0)):
    """Bridge a stack of outlines: `[(z, [(x, y), ...]), ...]`.

    Every outline must have the same number of points. This is how a building
    stops being a box: the plan can shrink, grow, rotate or change shape as it
    rises, so an upper storey can overhang, a wall can batter outward at the
    foot, and a roof can twist off square.
    """
    bm = bmesh.new()
    origin = Vector(at)
    rings = []
    for z, outline in stations:
        rings.append([bm.verts.new(origin + Vector((x, y, z)))
                      for x, y in outline])
    count = len(rings[0])
    for i in range(len(rings) - 1):
        for s in range(count):
            t = (s + 1) % count
            bm.faces.new([rings[i][s], rings[i][t],
                          rings[i + 1][t], rings[i + 1][s]])
    if close_bottom:
        bm.faces.new(list(reversed(rings[0])))
    if close_top:
        bm.faces.new(rings[-1])
    return _finish(bm, name, color)


def ngon(sides, radius, rotation=0.0, squash=1.0):
    """A regular outline, for `loft` stations."""
    return [(math.cos(2 * math.pi * i / sides + rotation) * radius,
             math.sin(2 * math.pi * i / sides + rotation) * radius * squash)
            for i in range(sides)]


def rounded_rect(width, depth, radius, per_corner=4):
    """A rectangle whose corners are arcs. Outlines for `loft`."""
    hw, hd = width / 2 - radius, depth / 2 - radius
    out = []
    for cx, cy, start in ((hw, hd, 0.0), (-hw, hd, math.pi / 2),
                          (-hw, -hd, math.pi), (hw, -hd, 3 * math.pi / 2)):
        for i in range(per_corner):
            a = start + (math.pi / 2) * i / float(per_corner - 1)
            out.append((cx + math.cos(a) * radius, cy + math.sin(a) * radius))
    return out


def scallop_ring(radius, lobes=7, amplitude=0.14, points=48, phase=0.0,
                 squash=1.0):
    """A wavy outline. The edge of a leaf mass, a thatch eave, a flower."""
    out = []
    for i in range(points):
        a = 2 * math.pi * i / points
        r = radius * (1.0 + amplitude * math.cos(lobes * a + phase))
        out.append((math.cos(a) * r, math.sin(a) * r * squash))
    return out


# -------------------------------------------------------------------- pad

def pad(name, color, radius=0.6, lobes=7, amplitude=0.16, dome=0.22,
        underside=0.09, points=40, at=(0, 0, 0), tilt=(0.0, 0.0)):
    """A scalloped lens: ONE mass of foliage, seen as a designed shape.

    The replacement for "a cluster of spheres". A pad has a drawn edge, a flat
    enough top to catch light as a plane, and a thin shaded underside, so a
    tree built by stacking a few of them reads as layered foliage with a
    deliberate outline instead of as lumps.
    """
    # Built at the ORIGIN, tilted about its own centre, and only then moved
    # into place. Tilting after translating rotates the pad about the world
    # origin instead, which throws it clear across the scene -- it is what
    # launched a cottage door arch into the roof and a character's mouth out
    # past his shoulder.
    from mathutils import Euler
    rotation = Euler((math.radians(tilt[0]), math.radians(tilt[1]), 0.0), "XYZ")
    offset = Vector(at)

    def place(point):
        return rotation.to_matrix() @ Vector(point) + offset

    bm = bmesh.new()
    rim = scallop_ring(radius, lobes, amplitude, points)
    rim_verts, low_verts = [], []
    for x, y in rim:
        rim_verts.append(bm.verts.new(place((x, y, 0.0))))
        low_verts.append(bm.verts.new(
            place((x * 0.94, y * 0.94, -underside))))
    top = bm.verts.new(place((0, 0, dome)))
    bottom = bm.verts.new(place((0, 0, -underside - dome * 0.22)))
    for i in range(points):
        j = (i + 1) % points
        bm.faces.new([rim_verts[i], rim_verts[j], top])
        bm.faces.new([low_verts[j], low_verts[i], bottom])
        bm.faces.new([rim_verts[j], rim_verts[i], low_verts[i], low_verts[j]])
    return _finish(bm, name, color)


# -------------------------------------------------------------- superform

def superform(name, color, size=(1, 1, 1), exponent=4.0, segments=20,
              rings=14, at=(0, 0, 0)):
    """A superellipsoid: a cube and a sphere share a dial.

    Exponent 2 is a sphere, 4 is a soft squircle, 8 is nearly a rounded cube.
    A moulded toy is this shape; a bevelled box is not.
    """
    bm = bmesh.new()
    origin = Vector(at)
    power = 2.0 / exponent

    def sgn_pow(value, p):
        return math.copysign(abs(value) ** p, value)

    grid = []
    for r in range(rings + 1):
        v = -math.pi / 2 + math.pi * r / rings
        row = []
        for s in range(segments):
            u = 2 * math.pi * s / segments
            x = sgn_pow(math.cos(v), power) * sgn_pow(math.cos(u), power)
            y = sgn_pow(math.cos(v), power) * sgn_pow(math.sin(u), power)
            z = sgn_pow(math.sin(v), power)
            row.append(bm.verts.new(origin + Vector(
                (x * size[0] / 2, y * size[1] / 2, z * size[2] / 2))))
        grid.append(row)
    for r in range(rings):
        for s in range(segments):
            t = (s + 1) % segments
            bm.faces.new([grid[r][s], grid[r][t], grid[r + 1][t], grid[r + 1][s]])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    return _finish(bm, name, color)


# ------------------------------------------------------------------ sweep

def sweep(name, color, path, radii, segments=10, caps=True, samples=0,
          profile_squash=1.0):
    """A tube that follows a drawn path, thickening and thinning along it.

    A trunk made this way can lean, recover, and taper like a brush stroke.
    A cone cannot do any of those things.
    """
    pts = [Vector(p) for p in path]
    if samples:
        dense = spline(pts, samples)
        stretch = [i * (len(radii) - 1) / float(len(dense) - 1)
                   for i in range(len(dense))]
        radii = [_lerp_list(radii, s) for s in stretch]
        pts = dense

    bm = bmesh.new()
    rings = []
    count = len(pts)
    for i, (point, radius) in enumerate(zip(pts, radii)):
        if i == 0:
            tangent = pts[1] - pts[0]
        elif i == count - 1:
            tangent = pts[-1] - pts[-2]
        else:
            tangent = pts[i + 1] - pts[i - 1]
        tangent.normalize()
        helper = Vector((0, 0, 1))
        if abs(tangent.dot(helper)) > 0.94:
            helper = Vector((1, 0, 0))
        side = tangent.cross(helper).normalized()
        up = side.cross(tangent).normalized()
        ring = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            offset = (side * math.cos(a) * radius +
                      up * math.sin(a) * radius * profile_squash)
            ring.append(bm.verts.new(point + offset))
        rings.append(ring)

    for i in range(count - 1):
        for s in range(segments):
            t = (s + 1) % segments
            bm.faces.new([rings[i][s], rings[i][t],
                          rings[i + 1][t], rings[i + 1][s]])
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return _finish(bm, name, color)


def _lerp_list(values, position):
    low = int(math.floor(position))
    high = min(low + 1, len(values) - 1)
    t = position - low
    return values[low] * (1 - t) + values[high] * t


def ribbon(name, color, path, width, thickness=0.05, samples=0, roll=0.0):
    """A flat strip swept along a path: a roof sweep, a brim, a collar."""
    pts = [Vector(p) for p in path]
    if samples:
        pts = spline(pts, samples)
    widths = width if isinstance(width, (list, tuple)) else [width] * len(pts)
    if len(widths) != len(pts):
        widths = [_lerp_list(list(width), i * (len(width) - 1) /
                             float(len(pts) - 1)) for i in range(len(pts))]
    bm = bmesh.new()
    rows = []
    for i, point in enumerate(pts):
        if i == 0:
            tangent = pts[1] - pts[0]
        elif i == len(pts) - 1:
            tangent = pts[-1] - pts[-2]
        else:
            tangent = pts[i + 1] - pts[i - 1]
        tangent.normalize()
        side = tangent.cross(Vector((0, 0, 1)))
        if side.length < 1e-5:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(tangent).normalized()
        side = side * math.cos(roll) + up * math.sin(roll)
        half = widths[i] / 2.0
        rows.append([
            bm.verts.new(point - side * half),
            bm.verts.new(point + side * half),
            bm.verts.new(point + side * half - up * thickness),
            bm.verts.new(point - side * half - up * thickness)])
    for i in range(len(rows) - 1):
        a, b = rows[i], rows[i + 1]
        for k in range(4):
            m = (k + 1) % 4
            bm.faces.new([a[k], a[m], b[m], b[k]])
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    return _finish(bm, name, color)


# -------------------------------------------------------------- deformers

def press(obj, axis="Z", plane=0.0, amount=0.35, radius=0.5, centre=(0, 0, 0)):
    """Flatten part of a surface toward a plane, with a soft falloff.

    A thumb pressing clay. Unlike `wobble`, which is noise everywhere, this
    leaves ONE deliberate mark, which is what reads as handmade.
    """
    index = {"X": 0, "Y": 1, "Z": 2}[axis]
    centre = Vector(centre)
    for vert in obj.data.vertices:
        world = obj.matrix_world @ vert.co
        distance = (world - centre).length
        if distance > radius:
            continue
        falloff = (1.0 - (distance / radius)) ** 2
        local_plane = plane - obj.location[index]
        vert.co[index] += (local_plane - vert.co[index]) * amount * falloff


def dents(obj, points, depth=0.03, radius=0.12):
    """Push the surface in at chosen spots: knuckle marks, tool nicks."""
    marks = [Vector(p) for p in points]
    for vert in obj.data.vertices:
        world = obj.matrix_world @ vert.co
        for mark in marks:
            distance = (world - mark).length
            if distance < radius:
                falloff = (1.0 - distance / radius) ** 2
                direction = (world - mark)
                if direction.length < 1e-6:
                    continue
                vert.co -= direction.normalized() * depth * falloff


def swell(obj, centre, radius=0.3, amount=0.05):
    """Push a region outward along its own normals: a belly, a cheek, a knot."""
    centre = Vector(centre)
    for vert in obj.data.vertices:
        world = obj.matrix_world @ vert.co
        distance = (world - centre).length
        if distance < radius:
            falloff = math.cos(distance / radius * math.pi * 0.5)
            vert.co += vert.normal * amount * falloff


def facet(obj, angle=12.0):
    """Planar-decimate into flat planes, then shade flat.

    Turns a smooth volume into something that reads as CARVED -- a surface made
    of decisions rather than of subdivisions.
    """
    from . import meshtools
    meshtools.activate(obj)
    modifier = obj.modifiers.new("Planar", "DECIMATE")
    modifier.decimate_type = "DISSOLVE"
    modifier.angle_limit = math.radians(angle)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.ops.object.shade_flat()


def jitter_verts(obj, amount=0.006, seed=1):
    """Tiny uncorrelated wobble. Hand tremor, not landscape noise."""
    rng = random.Random(seed)
    for vert in obj.data.vertices:
        vert.co += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                           rng.uniform(-1, 1))) * amount
