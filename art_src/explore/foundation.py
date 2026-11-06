"""The foundation pass: the hybrid set pushed to a designed identity.

    blender --background --python art_src/explore/foundation.py

The hybrid set was approved as a DIRECTION, with five notes. This module
answers those notes and nothing else, so the diff against `hybrid.py` is the
art direction rather than a rewrite:

  1. Chuck is REDESIGNED, not retextured. See CHARACTER below.
  2. The tree keeps its layered silhouette and gains volume: every foliage
     layer becomes a scalloped CUSHION lofted from stacked rings instead of a
     flat lens, so the layers read as masses with an edge rather than as cut
     paper.
  3. The cottage keeps the off-centre ridge that was picked and gains real
     architecture: tile COURSES, two dormers, a scalloped pantile eave, stone
     lintels, window boxes and purlin ends.
  4. The world replaces the flat green plane: rolling terrain, a sunken path,
     a drystone wall, hedges, a vegetable row, and grass that grows where
     objects meet the ground.
  5. The block keeps its proportions, its plaque and its lettering EXACTLY,
     and gains a raised wooden rim so the cream face reads as inset.

Everything is unified by one palette, one bake recipe family and one lighting
rig, which is what the hybrid pass established and what this pass inherits by
importing it.
"""

import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common  # noqa: E402,F401  -- registers the study palettes first
from common import BLOCK_FACES, BLOCK_SIZE, plaque_centre  # noqa: E402
from sb_lib import asset, forms, meshtools, painter, palette, rig  # noqa: E402

# Importing hybrid re-points the study palettes onto the house family and
# hands over the measured lettering constants. It does not build anything --
# its builders are behind a __main__ guard.
import hybrid  # noqa: E402
from hybrid import (LETTER_FONT_SIZE, LETTER_PIXEL_SIZE,  # noqa: E402
                    LETTER_MARGIN, LETTER_PLAQUE, letter_offset)

D = "foundation"
RR = forms.rounded_rect

CHUCK_HEIGHT = 1.35      # unchanged, so the capsule line does not move
TREE_HEIGHT = 3.10
COTTAGE_RIDGE = 3.95
GROUND_SIZE = 26.0       # metres across; the game camera sees about 14
# ⛔ THE GRID IS THE COLOUR RESOLUTION. The colour field is evaluated per
# VERTEX, so at 0.80 m the sharpest edge the ground can hold is about 1.6 m
# wide -- which is a gradient, not an edge, and is why every attempt at this
# so far came out as soft mottle no matter what drove it. 0.32 m costs about
# 13,000 extra triangles (~300 kB of mesh) and buys an edge around 0.6 m,
# which is roughly what a mower actually leaves.
GROUND_STEP = 0.32


# ----------------------------------------------------------------- palette
#
# Additions only. Every hybrid colour keeps its name and its value, so the
# approved set does not shift underneath this pass. The one house rule that
# governs all of it: nothing goes above 0.84 except the block's letter face at
# 0.90, so the letter is always the lightest thing on screen.

EXTRA = {
    # --- corrections to two hybrid colours, both because they CLIPPED.
    # s_wall at 0.84 sat right on the palette ceiling and under a real sun it
    # rendered as grey-white: the warm plaster stopped being a colour at all.
    # Dropping it to 0.78 keeps every relationship in the palette intact --
    # the letter face at 0.90 is still the lightest thing on screen by a wide
    # margin -- and gives the walls their cream back.
    "s_wall":       ("#E2CFB0", 0.78, "plaster"),
    "s_wall_shade": ("#BFA887", 0.63, "plaster plane in shade"),
    # --- the roof, which is now tiles rather than a painted plane ----------
    "t_tile":       ("#C4674A", 0.43, "terracotta pantile"),
    "t_tile_sun":   ("#D98B5E", 0.56, "pantile catching the sun"),
    "t_tile_deep":  ("#92422F", 0.27, "the shadow under a course lap"),
    # --- masonry and earth -------------------------------------------------
    "e_stone":      ("#9B8E74", 0.50, "drystone, lintels, path"),
    "e_stone_sun":  ("#B3A88C", 0.59, "a stone the sun has bleached"),
    "e_stone_deep": ("#6E6757", 0.40, "stone in shade, wall joints"),
    "e_earth":      ("#A8814F", 0.50, "the worn path"),
    "e_earth_deep": ("#785A38", 0.34, "a rut, a dug bed"),
    # --- the field ---------------------------------------------------------
    # Canopy 0.39 against meadow 0.56 is the load-bearing pair: at 0.52/0.55
    # trees disappeared into the field behind them, which is recorded in
    # palette.py and is still the trap here.
    "f_grass":      ("#7B9A54", 0.56, "meadow body"),
    "f_grass_dry":  ("#B3B264", 0.65, "burnt off on a crown -- the HUE step"),
    "f_grass_sun":  ("#B2BE74", 0.70, "the crown of a rise"),
    "f_grass_deep": ("#466538", 0.37, "a hollow, under a hedge"),
    "f_hedge":      ("#456B3C", 0.32, "hedge body"),
    "f_hedge_sun":  ("#648A48", 0.45, "hedge top"),
    "f_bloom":      ("#D9746B", 0.56, "window box, hedgerow flower"),
    "f_bloom_pale": ("#E8C87A", 0.74, "the other flower"),
    # --- the canopy. Overriding hybrid's three greens, which sat inside 0.24
    # to 0.53 and read as one colour once layered. A wider spread is what
    # makes a stack of masses legible AS a stack.
    "g_leaf_light": ("#8FB15F", 0.59, "canopy lit"),
    "g_leaf":       ("#5A8044", 0.41, "canopy body"),
    "g_leaf_deep":  ("#2C4729", 0.21, "canopy shadow"),
    # --- the smallholding -------------------------------------------------
    "w_picket":     ("#DCCDAC", 0.74, "limewashed picket"),
    "w_picket_sh":  ("#B6A481", 0.58, "picket in shade"),
    "w_rail":       ("#B2956C", 0.54, "fence rail and post"),
    "w_barrel":     ("#9B7347", 0.42, "barrel staves"),
    "w_barrel_sun": ("#B88F5C", 0.54, "a stave in the sun"),
    "w_iron":       ("#4C4740", 0.23, "barrel hoop, nail"),
    "w_sack":       ("#C9B189", 0.66, "the scarecrow's sacking"),
    "w_cloth":      ("#A85F4E", 0.37, "the scarecrow's shirt"),
    "w_water":      ("#4B6A6B", 0.30, "what is in the barrel"),
    "f_crop":       ("#7E9C54", 0.55, "a carrot top, an onion strap"),
    "f_crop_pale":  ("#9DB46A", 0.65, "a cabbage heart, an onion bulb"),
    "c_carrot":     ("#D3762F", 0.46, "the shoulder of the root"),
    "f_crop_deep":  ("#4E6D39", 0.31, "between the leaves"),
    "f_bloom_sun":  ("#E6C258", 0.71, "the yellow one"),
    # --- the character -----------------------------------------------------
    "h_straw":      ("#D9B972", 0.69, "the straw hat"),
    "h_straw_deep": ("#A5854A", 0.49, "under the brim"),
    "h_band":       ("#B35340", 0.36, "hat band"),
    "h_vest":       ("#C25A3E", 0.39, "the open vest"),
    "h_vest_deep":  ("#8E3A28", 0.26, "vest in shade"),
    "h_shorts":     ("#44688A", 0.39, "rolled shorts"),
    "h_shorts_deep": ("#2E4A66", 0.26, "shorts in shade"),
    "h_skin":       ("#C07F4F", 0.50, "skin"),
    "h_skin_deep":  ("#8E5A36", 0.34, "skin in shade"),
    "h_hair":       ("#2A211D", 0.12, "hair"),
    "h_tooth":      ("#F4E8D2", 0.88, "the grin"),
}
palette.extend(EXTRA)


# --------------------------------------------------------------- surfacing
#
# One recipe family. SURFACE is the hybrid recipe, unchanged, because that is
# what was approved. The two variants exist for a measurable reason rather
# than a stylistic one.

SURFACE = dict(hybrid.SURFACE)

# The terrain is 26 m across on a 1024 atlas, about 33 px per metre against a
# screen density of 142. Any HIGH-FREQUENCY term baked at that density is
# aliasing, not texture -- grain at scale 48 would land as sparkle. So the
# terrain gets the same wash and the same AO and no fine detail at all, and
# the wash is scaled up to the size of a field rather than of an object.
# wash_scale 0.11 put about three lobes across the whole 26 m field, which is
# indistinguishable from a flat fill at gameplay framing -- the first render
# still showed exactly the uniform green this pass exists to remove. 0.55 is
# roughly a two-metre mottle: visible in a 9 m frame, still far below the
# texel density, so it costs nothing in aliasing.
# ⛔ `wash` is a broad VALUE drift in the bake, and at 0.22-0.28 it was the
# loudest thing on the ground -- soft grey-green cloud over everything, which
# is what "the terrain's colour" was really complaining about. The colour
# belongs in the vertex field, where it has a cause; the wash is only there
# so no two square metres are identical.
TERRAIN_SURFACE = dict(SURFACE, grain=0.0, streak=0.0,
                       wash=0.09, wash_scale=0.95,
                       ao_strength=0.30, ao_distance=1.10,
                       edge_light=0.06, edge_dark=0.08)

# A cottage is cut, a block is moulded, foliage is in between, and a character
# is moulded a little softer than a toy.
SMOOTH = {"cottage": 10.0, "block": 18.0, "tree": 62.0, "chuck": 20.0,
          "terrain": 44.0, "props": 26.0, "garden": 22.0}


# ⛔ `budget_tris` only prints a warning -- it enforces nothing, and the
# numbers were guesses. Triangles are also the wrong thing to watch: all seven
# assets together are about 52,000, which no GPU made this century notices,
# and 69% of the download is TEXTURE rather than mesh. The budgets below are
# set to "loud enough to catch a runaway, quiet enough to be believed", and
# the number to actually watch is the kB in each report line.
# ⛔ See the note in village.py: 1024 everywhere put 70 MB of uncompressed
# texture in one scene and crashed the browser. Terrain keeps 1024 because it
# is 26 m wide; everything else drops to 512, which is still more texels than
# the 142 px-per-metre camera can show.
def produce(subject, objects, texture=asset.TEXTURE_SMALL, budget_tris=None,
            surface=None, bake_samples=24, with_animation=False,
            animation_names=None):
    return asset.produce("explore/%s_%s" % (D, subject), objects,
                         texture=texture, roughness=0.93,
                         budget_tris=budget_tris, bake_samples=bake_samples,
                         smooth_angle=SMOOTH[subject],
                         with_animation=with_animation,
                         animation_names=animation_names,
                         gouache=surface or SURFACE)


# ----------------------------------------------------------------- helpers

def shift(outline, dx, dy=0.0):
    """Offset a loft station. Off-centre stations are what break symmetry."""
    return [(x + dx, y + dy) for x, y in outline]


def wavy(outline, lobes=8, amount=0.035):
    """Push an outline in and out along its own radius: pantile ends, scallops.

    Applied BEFORE `shift`, because it works along the radius from the origin
    and a shifted outline has no meaningful radius.
    """
    count = len(outline)
    out = []
    for index, (x, y) in enumerate(outline):
        length = math.hypot(x, y) or 1e-6
        push = amount * math.cos(2 * math.pi * lobes * index / count)
        out.append((x + x / length * push, y + y / length * push))
    return out


def rotate_x(obj, degrees, pivot=(0.0, 0.0, 0.0)):
    """Rotate vertices about a world X axis.

    Done on the vertices rather than with `apply_transform` deliberately:
    `apply_transform` bakes SCALE first and ROTATION second, which is how the
    first cottage came out 5.5 m deep. Every generator in `forms` writes world
    coordinates straight into the mesh and leaves the object at the origin, so
    plain vertex maths is both correct and the only thing that reads clearly.
    """
    rad = math.radians(degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    for vert in obj.data.vertices:
        y = vert.co.y - pivot[1]
        z = vert.co.z - pivot[2]
        vert.co.y = pivot[1] + y * cos_a - z * sin_a
        vert.co.z = pivot[2] + y * sin_a + z * cos_a


def paint_field(obj, stops, field):
    """Blend a ramp of palette colours across a form by an arbitrary field.

    `paint_by_normal` can only ask which way a surface faces, which is the
    right question for a canopy and the wrong one for a meadow -- a field's
    colour comes from how high it is, how steep it is and how close it is to
    the path, not from its normal. Interpolating per CORNER off per-vertex
    values keeps it continuous: `repaint_faces` would stamp whole 0.8 m quads
    and the terrain would read as a patchwork of squares.

    `stops` is `[(position, palette_name), ...]` ascending over 0..1.
    `field(position_vector, normal_vector)` returns where a vertex sits on it.
    """
    ramp = [(t, palette.linear(name)) for t, name in stops]
    mesh = obj.data
    if "Paint" not in mesh.attributes:
        meshtools.set_part_color(obj, stops[0][1])
    layer = mesh.attributes["Paint"]

    values = []
    for vert in mesh.vertices:
        t = min(max(field(vert.co, vert.normal), 0.0), 1.0)
        low = ramp[0]
        high = ramp[-1]
        for index in range(len(ramp) - 1):
            if ramp[index][0] <= t <= ramp[index + 1][0]:
                low, high = ramp[index], ramp[index + 1]
                break
        span = max(high[0] - low[0], 1e-6)
        k = min(max((t - low[0]) / span, 0.0), 1.0)
        values.append(tuple(low[1][i] + (high[1][i] - low[1][i]) * k
                            for i in range(4)))

    for poly in mesh.polygons:
        for loop_index, vert_index in zip(poly.loop_indices, poly.vertices):
            layer.data[loop_index].color = values[vert_index]


def cushion(name, colour, radius, height, at, lobes=7, amount=0.17,
            squash=1.0, twist=24.0, points=26, profile=None):
    """A scalloped MASS: stacked wavy rings lofted into a volume.

    This is the answer to "the leaves look like overlapping flat pieces". A
    `pad` is a lens -- a drawn edge with almost nothing behind it, which is
    exactly right for cut paper and exactly wrong for foliage that has to hold
    up at a close-up. A cushion keeps the drawn scalloped EDGE, which is the
    silhouette that was approved, and puts a real domed body behind it.

    `twist` rotates the scallop phase as the rings rise, so the lobes spiral
    instead of stacking into a lathe. Without it the mass reads as turned on a
    lathe, which is a different kind of generic.
    """
    profile = profile or [(-0.46, 0.34), (-0.22, 0.74), (-0.02, 0.98),
                          (0.20, 1.00), (0.42, 0.82), (0.60, 0.46),
                          (0.72, 0.15)]
    stations = []
    for rel_z, rel_r in profile:
        # The scallops are strongest at the equator and fade at both poles,
        # so the silhouette is drawn and the top still reads as a dome.
        fade = 1.0 - min(abs(rel_z) / 0.72, 1.0) ** 2
        ring = forms.scallop_ring(radius * rel_r, lobes=lobes,
                                  amplitude=amount * fade, points=points,
                                  phase=math.radians(twist) * rel_z,
                                  squash=squash)
        stations.append((at[2] + rel_z * height, shift(ring, at[0], at[1])))
    return forms.loft(name, colour, stations)


BLOCK_EXPONENT = 5.2     # unchanged from the approved block
BLOCK_CENTRE_Z = BLOCK_SIZE / 2


def block_surface_depth(u, v, exponent=BLOCK_EXPONENT):
    """How far the block's own surface stands out at a point ON a face.

    The superform is a true superellipsoid, so this is exact rather than
    sampled: |x/a|^n + |y/a|^n + |z/a|^n = 1 solved for the outward axis.

    It exists because of a measurement that killed the obvious approach. The
    approved plaque is 0.640 across a 0.800 block, which leaves 0.080 of wood,
    and the squircle has ALREADY curved away by then: at 0.378 from the centre
    of a face the surface has dropped 0.100 below the face plane. A raised rim
    drawn as a flat ring at a single depth therefore floats off the block
    everywhere except dead centre -- a 0.08 gap, which is bigger than the rim.
    So the rim's outer edge is seated on this curve instead, point by point,
    and the rim grows out of the face rather than being parked on it.
    """
    a = BLOCK_SIZE / 2
    remainder = 1.0 - abs(u / a) ** exponent - abs(v / a) ** exponent
    return a * max(remainder, 0.0) ** (1.0 / exponent)


def face_bezel(name, colour, normal, plaque=LETTER_PLAQUE, lip=0.014,
               buried=0.020):
    """A moulded wooden rim that rises out of the face and holds the plaque.

    He asked for inset faces while keeping the plaque, the proportions and the
    lettering exactly as approved. Those three cannot move: `plaque_centre`
    puts the cream at 0.413 from the block's centre because the Label3D in
    `block.tscn` sits at 0.4178 and reads that surface as its ground. So the
    cream cannot go DOWN -- the wood has to come UP around it, and `lip` is how
    far. 0.014 is enough for a shadow line at the camera's 142 px per metre
    and shallow enough that the frame still reads as wood rather than as a
    well.

    Five rings bridged by hand rather than by `loft`, because the outer ring
    needs a DIFFERENT depth at every point -- it follows
    `block_surface_depth` -- and a loft station has one height for the whole
    outline.
    """
    import bmesh
    from mathutils import Vector

    out = common.FACE_OUT          # 0.413 from the block's centre, both ways
    rings = [
        # width, depth -- None means "sit on the block's own surface"
        (0.760, None),
        (0.726, 0.62),
        (0.686, 0.985),
        (plaque + 0.016, 1.0),     # the flat top of the lip
        (plaque + 0.012, 0.0),     # drop away behind the plaque, unseen
    ]
    top = out + lip

    bm = bmesh.new()
    built = []
    for width, depth in rings:
        outline = RR(width, width, width * 0.16, 6)
        verts = []
        for u, v in outline:
            seated = block_surface_depth(u, v) - buried
            if depth is None:
                w = seated
            else:
                w = seated + (top - seated) * depth
            verts.append(bm.verts.new(Vector(_to_face(normal, u, v, w))))
        built.append(verts)

    count = len(built[0])
    for index in range(len(built) - 1):
        lower, upper = built[index], built[index + 1]
        for s in range(count):
            t = (s + 1) % count
            bm.faces.new([lower[s], lower[t], upper[t], upper[s]])
    bm.faces.new(built[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    meshtools.set_part_color(obj, colour)
    return obj


def _to_face(normal, u, v, w):
    """Face-local (across, up, outward) -> world, around the block's centre."""
    if abs(normal[2]) > 0.5:
        return (u, v, BLOCK_CENTRE_Z + w * (1 if normal[2] > 0 else -1))
    if abs(normal[0]) > 0.5:
        return (w * (1 if normal[0] > 0 else -1), u, BLOCK_CENTRE_Z + v)
    return (u, w * (1 if normal[1] > 0 else -1), BLOCK_CENTRE_Z + v)


# ------------------------------------------------------------------- CHUCK
#
# A character design pass, not a retexture. The brief was Luffy crossed with
# Mowgli, and the decisions that came out of it are:
#
# THE HAT is the identity. A wide straw brim is the one silhouette no asset
# pack ships, it reads at any size and from any angle, and on a game called
# Phonics FARM it is earned rather than applied. It is tilted BACK 15 degrees,
# which is not styling: at the game's 30-degree pitch a level brim puts the
# whole face in shadow and the character loses his expression.
#
# PROPORTION is committed to: 2.9 heads tall, where phase 1 was about 3.6.
# The head is slightly wider than the shoulders and the hands and feet are
# oversized. A character averaged toward realistic proportion is what "still
# feels generic" means.
#
# BARE FEET AND BARE CHEST under an open vest -- Mowgli's half of the brief,
# and it keeps skin as the largest single colour on him so the vest red and
# the straw read as accents.
#
# THE FACE is a plane, not a sphere: pressed flat so features sit ON something.
# Big round eyes with a highlight, brows angled up and out, and a wide open
# grin with a tooth band. The grin does more for "memorable" than any amount
# of modelling.
#
# GLASSES ARE GONE. They were the previous Chuck's one distinguishing feature,
# so this is the reversible decision in the pass -- flip GLASSES back on and
# the lenses, rims and bridge return, in the new face's geometry.
GLASSES = False

# ⭐ The skeleton and the body read the SAME numbers. Phase 1 kept its bone
# positions as separate constants from the shapes they were meant to be
# inside, which works right up until a proportion is tuned and the rig is
# silently left behind. These are authored heights; `build_chuck` scales the
# finished mesh to CHUCK_HEIGHT and the rig is built with the same factor.
HIP_X = 0.096
ANKLE_Z = 0.095
KNEE_Z = 0.250
HIP_Z = 0.440
CHEST_Z = 0.700
NECK_Z = 0.800
HEAD_TOP = 1.260
SHOULDER = (0.158, 0.740)
ELBOW = (0.205, 0.600)
HAND = (0.226, -0.044, 0.420)

HEAD_Z = 1.030
HEAD = (0.440, 0.400, 0.460)
FACE_Y = -0.168


def build_chuck():
    meshtools.reset_scene()
    parts = []

    # --- feet. Bare, big, and splayed out a few degrees so the stance reads
    # planted rather than parked.
    for side in (-1, 1):
        foot = forms.superform(
            "Foot", "h_skin", size=(0.150, 0.250, 0.098), exponent=3.2,
            segments=14, rings=10, at=(side * 0.098, -0.028, 0.049))
        forms.press(foot, "Z", plane=0.0, amount=0.55, radius=0.16,
                    centre=(side * 0.098, -0.028, 0.0))
        rotate_x(foot, 0.0)
        parts.append(foot)
        # toes: one band of three dimples, enough to say "not a shoe"
        forms.dents(foot, [(side * 0.098 + dx, -0.118, 0.062)
                           for dx in (-0.038, 0.0, 0.038)],
                    depth=0.012, radius=0.030)

        parts.append(forms.sweep(
            "Leg", "h_skin",
            [(side * 0.092, 0.004, 0.070), (side * 0.096, 0.0, 0.230),
             (side * 0.100, -0.004, 0.400)],
            [0.072, 0.066, 0.078], segments=10, samples=5))

    # --- rolled shorts. The roll is the out-in-out station at the hem; a
    # straight-hemmed short leg reads as a swimsuit.
    shorts = forms.loft("Shorts", "h_shorts", [
        (0.255, RR(0.300, 0.230, 0.075, 4)),
        (0.290, RR(0.330, 0.255, 0.080, 4)),
        (0.330, RR(0.296, 0.228, 0.074, 4)),
        (0.455, RR(0.310, 0.240, 0.078, 4)),
    ])
    meshtools.paint_by_normal(shorts, "h_shorts", "h_shorts",
                             "h_shorts_deep", up_at=0.8, down_at=-0.5)
    parts.append(shorts)

    # --- torso. A small barrel chest over a narrow waist, bare.
    torso = forms.loft("Torso", "h_skin", [
        (0.420, RR(0.280, 0.215, 0.070, 4)),
        (0.520, RR(0.268, 0.205, 0.067, 4)),
        (0.660, RR(0.330, 0.238, 0.082, 4)),
        (0.740, RR(0.352, 0.248, 0.088, 4)),
        (0.790, RR(0.300, 0.220, 0.075, 4)),
    ])
    meshtools.paint_by_normal(torso, "h_skin", "h_skin", "h_skin_deep",
                             up_at=0.9, down_at=-0.4)
    parts.append(torso)

    # --- the open vest: two front panels, a back panel, two shoulder straps.
    # Modelled open rather than painted open, so the silhouette carries it.
    for side in (-1, 1):
        panel = forms.loft("VestFront", "h_vest", [
            (0.430, RR(0.120, 0.075, 0.030, 3)),
            (0.620, RR(0.132, 0.080, 0.033, 3)),
            (0.772, RR(0.118, 0.072, 0.030, 3)),
        ], at=(side * 0.112, -0.108, 0.0))
        meshtools.lean(panel, degrees=side * -2.2, axis="Y", pivot_z=0.430)
        parts.append(panel)
        parts.append(forms.sweep(
            "VestStrap", "h_vest",
            [(side * 0.112, -0.100, 0.760), (side * 0.140, -0.010, 0.800),
             (side * 0.118, 0.090, 0.760)],
            [0.040, 0.044, 0.038], segments=8, samples=5,
            profile_squash=0.55))
    back = forms.loft("VestBack", "h_vest", [
        (0.430, RR(0.290, 0.070, 0.035, 4)),
        (0.640, RR(0.320, 0.076, 0.038, 4)),
        (0.772, RR(0.284, 0.068, 0.034, 4)),
    ], at=(0.0, 0.102, 0.0))
    meshtools.paint_by_normal(back, "h_vest", "h_vest", "h_vest_deep",
                              up_at=0.8, down_at=-0.4)
    parts.append(back)

    # --- arms, held clear of the body so the silhouette stays open.
    for side in (-1, 1):
        parts.append(forms.sweep(
            "Arm", "h_skin",
            [(side * 0.158, -0.004, 0.740), (side * 0.205, -0.020, 0.600),
             (side * 0.222, -0.036, 0.470)],
            [0.058, 0.050, 0.046], segments=9, samples=5))
        hand = forms.superform(
            "Hand", "h_skin", size=(0.108, 0.112, 0.098), exponent=2.9,
            segments=12, rings=9, at=(side * 0.226, -0.044, 0.420))
        forms.dents(hand, [(side * 0.226, -0.096, 0.420)], depth=0.012,
                    radius=0.045)
        parts.append(hand)

    parts.append(forms.sweep("Neck", "h_skin",
                             [(0, 0.004, 0.760), (0, 0.004, 0.830)],
                             [0.070, 0.066], segments=10))

    # --- the head. Pressed flat at the front so the face is a PLANE, tapered
    # to a chin, and swollen at the cheeks. A sphere with features stuck on it
    # is the generic read this pass exists to break.
    head = forms.superform("Head", "h_skin", size=HEAD, exponent=3.0,
                           segments=24, rings=18, at=(0, 0, HEAD_Z))
    forms.press(head, "Y", plane=FACE_Y, amount=0.52, radius=0.30,
                centre=(0, -0.21, HEAD_Z + 0.01))
    _chin(head, HEAD_Z)
    forms.swell(head, (0.135, -0.120, HEAD_Z - 0.030), radius=0.11,
                amount=0.014)
    forms.swell(head, (-0.135, -0.120, HEAD_Z - 0.030), radius=0.11,
                amount=0.014)
    parts.append(head)
    parts += _face()
    parts += _hair()
    parts += _hat()

    chuck = meshtools.join(parts, "Chuck")
    meshtools.merge_doubles(chuck, 0.0004)
    forms.facet(chuck, angle=7.0)
    meshtools.drop_to_floor(chuck)
    # ⛔ Scale FIRST, then rig. `facet` welds vertices and `_scale_to_height`
    # moves every one of them, so a skeleton built before either is bound to
    # coordinates that no longer exist. The factor comes back so the bones
    # can be placed in the same space the mesh ended up in.
    factor = _scale_to_height(chuck, CHUCK_HEIGHT)
    skeleton = _build_rig(chuck, factor)
    _idle_action(skeleton)
    _walk_action(skeleton)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 49
    return [chuck, skeleton.object]


def _chin(head, head_z):
    """Narrow the lower half of the head. Six numbers, and he has a face."""
    for vert in head.data.vertices:
        drop = head_z - vert.co.z
        if drop <= 0.0:
            continue
        t = min(drop / (HEAD[2] * 0.5), 1.0)
        factor = 1.0 - 0.30 * (t ** 1.7)
        vert.co.x *= factor
        vert.co.y = (vert.co.y) * factor


def _face():
    parts = []
    eye_z = HEAD_Z + 0.022
    for side in (-1, 1):
        # Big, round, and set WIDE. Small eyes close together is the single
        # most reliable way to make a stylised character read as generic.
        parts.append(forms.superform(
            "Eye", "h_hair", size=(0.092, 0.040, 0.106), exponent=2.2,
            segments=14, rings=10, at=(side * 0.104, FACE_Y - 0.012, eye_z)))
        parts.append(forms.superform(
            "Spark", "h_tooth", size=(0.030, 0.020, 0.034), exponent=2.2,
            segments=9, rings=7,
            at=(side * 0.112, FACE_Y - 0.030, eye_z + 0.030)))
        # Brows angled up and OUT: cheeky rather than worried. The sign of
        # that angle is the whole personality of the face.
        # Thinner, higher and at a gentler angle than the first pass, where
        # heavy brows starting low beside the nose read as a scowl.
        parts.append(forms.sweep(
            "Brow", "h_hair",
            [(side * 0.064, FACE_Y - 0.012, eye_z + 0.082),
             (side * 0.150, FACE_Y - 0.008, eye_z + 0.100)],
            [0.011, 0.008], segments=7, samples=4, profile_squash=0.55))

    parts.append(forms.superform(
        "Nose", "h_skin", size=(0.052, 0.054, 0.044), exponent=2.7,
        segments=10, rings=8, at=(0, FACE_Y - 0.020, HEAD_Z - 0.052)))

    # ⛔ A GRIN IS A CURVE. The first version was a wide flat lozenge with a
    # cream band across it, and it read as gritted teeth on an angry child --
    # which, with brows angled up and out, is exactly the wrong face. The
    # corners have to LIFT. Swept along an arc, thick in the middle and thin
    # at the corners, it reads as an open smile at any size.
    grin = [(-0.092, FACE_Y + 0.016, HEAD_Z - 0.112),
            (0.0, FACE_Y - 0.014, HEAD_Z - 0.158),
            (0.092, FACE_Y + 0.016, HEAD_Z - 0.112)]
    parts.append(forms.sweep("Mouth", "h_hair", grin,
                             [0.013, 0.038, 0.013], segments=10, samples=6,
                             profile_squash=0.80))
    # The tooth line rides the UPPER edge of the grin and stands proud of it.
    # Opaque means opaque: an inset band is simply invisible, which cost two
    # builds when Chuck's eyes sat behind his lenses.
    parts.append(forms.sweep(
        "Teeth", "h_tooth",
        [(-0.064, FACE_Y - 0.010, HEAD_Z - 0.118),
         (0.0, FACE_Y - 0.034, HEAD_Z - 0.140),
         (0.064, FACE_Y - 0.010, HEAD_Z - 0.118)],
        [0.006, 0.016, 0.006], segments=9, samples=5, profile_squash=0.70))

    if GLASSES:
        for side in (-1, 1):
            parts.append(meshtools.torus(
                "Rim", "h_hair", major=0.080, minor=0.014,
                at=(side * 0.104, FACE_Y - 0.034, HEAD_Z + 0.022),
                rot=(math.radians(90), 0, 0), major_seg=16, minor_seg=6))
        parts.append(forms.sweep(
            "Bridge", "h_hair",
            [(-0.058, FACE_Y - 0.034, HEAD_Z + 0.040),
             (0.058, FACE_Y - 0.034, HEAD_Z + 0.040)],
            [0.012, 0.012], segments=7))
    return parts


def _hair():
    """A moulded cap plus tufts that break the outline.

    The tufts are not decoration: the hat covers the top of the head, so
    without hair escaping at the sides and the nape the character is a hat
    with a face under it. They are what survives the brim.
    """
    parts = []
    cap = forms.superform("Hair", "h_hair", size=(0.448, 0.408, 0.268),
                          exponent=3.3, segments=20, rings=14,
                          at=(0.0, 0.026, HEAD_Z + 0.112))
    forms.press(cap, "Y", plane=FACE_Y + 0.044, amount=0.40, radius=0.26,
                centre=(0, -0.20, HEAD_Z + 0.10))
    parts.append(cap)

    # origin, tip, radius -- a forward cowlick, two side flicks, a nape
    # Bigger, and aimed OUT AND DOWN rather than up. The first set pointed
    # skyward and the hat brim cut them off at the root, so they read as a few
    # stray bristles. Hair that escapes BELOW the brim is what tells you there
    # is a head under the hat.
    tufts = [
        ((-0.198, -0.052, HEAD_Z + 0.020), (-0.318, -0.136, HEAD_Z - 0.040), 0.050),
        ((0.202, -0.032, HEAD_Z + 0.012), (0.330, -0.100, HEAD_Z - 0.062), 0.048),
        ((-0.034, 0.188, HEAD_Z - 0.004), (-0.072, 0.300, HEAD_Z - 0.104), 0.052),
        ((0.112, 0.178, HEAD_Z - 0.024), (0.198, 0.278, HEAD_Z - 0.126), 0.046),
        ((-0.160, 0.130, HEAD_Z + 0.030), (-0.262, 0.214, HEAD_Z - 0.030), 0.042),
    ]
    for origin, tip, radius in tufts:
        middle = tuple((origin[i] + tip[i]) / 2 for i in range(3))
        middle = (middle[0], middle[1], middle[2] + 0.022)
        parts.append(forms.sweep(
            "Tuft", "h_hair", [origin, middle, tip],
            [radius, radius * 0.72, 0.006], segments=7, samples=5))
    return parts


def _hat():
    """A lathed straw hat: a drawn silhouette revolved, which is what `lathe`
    is for and what no primitive can do.

    The profile is the design. Crown dome, a hard turn at the brim line, then
    a brim that falls away and LIFTS at its rim, so the edge catches light as
    a line all the way round instead of dying into shadow.
    """
    # ⛔ The crown radius is a CLEARANCE, not a style choice. The hair cap is
    # 0.462 across, so the first hat -- crown radius 0.172 -- was swallowed by
    # it: the render showed a black dome with a khaki ring round it, which read
    # as a beanie. The crown has to be wider than the hair it sits on.
    profile = [
        (0.000, 0.152), (0.090, 0.148), (0.168, 0.126), (0.222, 0.078),
        (0.250, 0.030), (0.258, 0.006),                      # brim line
        (0.305, -0.014), (0.348, -0.032), (0.372, -0.030),
        (0.384, -0.008), (0.376, 0.002),                     # lifted rim
    ]
    hat = forms.lathe("Hat", "h_straw", profile, segments=28,
                      at=(0.0, 0.030, HEAD_Z + 0.150), smooth_profile=0)
    meshtools.paint_by_normal(hat, "h_straw", "h_straw", "h_straw_deep",
                              up_at=0.55, down_at=-0.25)
    # Tilted BACK. At the game's 30-degree camera pitch a level brim shades
    # the entire face and the expression -- the whole point of the redesign --
    # is lost. 20 degrees clears the eyes and still reads as a worn hat.
    rotate_x(hat, -20.0, pivot=(0.0, 0.040, HEAD_Z + 0.124))
    meshtools.wobble(hat, amount=0.006, scale=5.0, seed=7)

    band = forms.lathe("Band", "h_band", [
        (0.000, 0.000), (0.238, 0.000), (0.248, 0.014),
        (0.251, 0.052), (0.242, 0.060), (0.000, 0.060),
    ], segments=28, at=(0.0, 0.030, HEAD_Z + 0.154))
    rotate_x(band, -20.0, pivot=(0.0, 0.040, HEAD_Z + 0.124))
    return [hat, band]


def _scale_to_height(obj, height):
    """Scale a finished object to an exact height and sit it on the floor.

    ⛔ `view_layer.update()` is LOAD-BEARING, twice. `drop_to_floor` writes
    `obj.location.z`, and `obj.matrix_world` does not pick that up until the
    depsgraph is evaluated -- so `meshtools.bounds`, which reads
    `matrix_world @ v.co`, silently returns LOCAL coordinates afterwards.
    Two drops in a row then correct for the same offset twice and the object
    ends up floating by exactly the height it was lifted.

    It is why the tree hovered 41 mm above the ground and the character did
    not: Chuck runs `forms.facet`, whose Blender operators force an
    evaluation, and the tree runs none.
    """
    bpy.context.view_layer.update()
    low, high = meshtools.bounds(obj)
    factor = height / max(high.z - low.z, 1e-6)
    for vert in obj.data.vertices:
        vert.co *= factor
    bpy.context.view_layer.update()
    meshtools.drop_to_floor(obj)
    bpy.context.view_layer.update()
    return factor


# ------------------------------------------------------------- CHUCK'S RIG
#
# The bone layout is phase 1's, unchanged, and so is the motion. That is
# deliberate: `player.gd` has been driving this skeleton on real hardware
# since September, the walk was tuned against the shipping camera, and a
# redesign of the BODY is not a reason to re-solve the MOVEMENT. What changes
# is the proportions the bones sit in -- shorter legs, a much bigger head --
# which the shared anatomy constants carry over on their own.

def _build_rig(mesh, factor):
    """Skeleton and skin weights for the redesigned Chuck."""
    def at(x, z, y=0.0):
        return (x * factor, y * factor, z * factor)

    skeleton = rig.Rig("ChuckRig")
    skeleton.bone("root", at(0, 0), at(0, 0.12))
    skeleton.bone("hips", at(0, HIP_Z), at(0, CHEST_Z), parent="root")
    skeleton.bone("chest", at(0, CHEST_Z), at(0, NECK_Z), parent="hips",
                  connected=True)
    skeleton.bone("head", at(0, NECK_Z), at(0, HEAD_TOP), parent="chest",
                  connected=True)
    for side, tag in ((-1, "L"), (1, "R")):
        skeleton.bone("arm_" + tag, at(side * SHOULDER[0], SHOULDER[1]),
                      at(side * ELBOW[0], ELBOW[1]), parent="chest")
        skeleton.bone("hand_" + tag, at(side * ELBOW[0], ELBOW[1]),
                      at(side * HAND[0], HAND[2], HAND[1]),
                      parent="arm_" + tag, connected=True)
        skeleton.bone("thigh_" + tag, at(side * HIP_X, HIP_Z - 0.03),
                      at(side * HIP_X, KNEE_Z), parent="hips")
        skeleton.bone("shin_" + tag, at(side * HIP_X, KNEE_Z),
                      at(side * HIP_X, ANKLE_Z), parent="thigh_" + tag,
                      connected=True)
        skeleton.bone("foot_" + tag, at(side * HIP_X, ANKLE_Z),
                      at(side * HIP_X, 0.03, -0.13), parent="shin_" + tag,
                      connected=True)

    # ⛔ Everything above the brow belongs to the HEAD, at 0.97. Without it
    # the chest bone part-claims whatever hangs near it and the piece shears
    # on every step. On this Chuck that is far more dangerous than it was on
    # phase 1's: the straw hat brim reaches 0.37 out from the skull, which is
    # wider than his shoulders, so by raw distance the arm bones are closer
    # to most of the hat than the head bone is.
    neck = (NECK_Z + 0.015) * factor
    skeleton.bind(mesh, falloff=5.5, influences=3, prefer={
        "head": lambda p: p.z > neck,
    }, prefer_weight=0.97)
    return skeleton


def _idle_action(skeleton):
    """Two seconds of breathing. Nothing travels; he just occupies the world."""
    frames = {}
    for frame, phase in ((1, 0.0), (25, 1.0), (49, 0.0)):
        frames[frame] = {
            "root": {"loc": (0, 0, 0.005 * phase)},
            "hips": {"rot": (-1.4 * phase, 0, 0.8 * phase)},
            "chest": {"rot": (2.2 * phase, 0, -0.6 * phase),
                      "scale": (1.0, 1.0 + 0.018 * phase, 1.0)},
            "head": {"rot": (-1.6 * phase, 2.2 * phase, 0)},
            "arm_L": {"rot": (0, 0, -3.5 * phase)},
            "arm_R": {"rot": (0, 0, 3.5 * phase)},
            "hand_L": {"rot": (-4.0 * phase, 0, 0)},
            "hand_R": {"rot": (-4.0 * phase, 0, 0)},
        }
    # A small off-beat head turn stops the loop reading as a metronome.
    frames[13] = dict(frames[1])
    frames[13]["head"] = {"rot": (-0.8, -3.0, 1.2)}
    frames[37] = dict(frames[25])
    frames[37]["head"] = {"rot": (-2.0, 4.0, -1.0)}
    return skeleton.action("chuck_idle", frames)


def _walk_action(skeleton):
    """One second, two steps. Contacts at 1 and 13, passes at 7 and 19.

    The leg swing is pulled in from phase 1's 26 degrees to 22: this Chuck's
    legs are shorter against a much heavier head, and the old amplitude threw
    the silhouette about. The head counter-rotation is up for the same reason
    -- a big head that does not settle reads as a bobblehead.
    """

    def step(lead, trail, bob, lean, twist):
        return {
            "root": {"loc": (0, 0, bob)},
            "hips": {"rot": (lean, twist, 0)},
            "chest": {"rot": (lean * 0.4, -twist * 0.8, 0)},
            "head": {"rot": (-lean * 0.9, -twist * 0.45, 0)},
            "thigh_" + lead: {"rot": (-22, 0, 0)},
            "shin_" + lead: {"rot": (6, 0, 0)},
            "foot_" + lead: {"rot": (12, 0, 0)},
            "thigh_" + trail: {"rot": (17, 0, 0)},
            "shin_" + trail: {"rot": (24, 0, 0)},
            "foot_" + trail: {"rot": (-8, 0, 0)},
            "arm_" + lead: {"rot": (22, 0, 0)},
            "arm_" + trail: {"rot": (-26, 0, 0)},
            "hand_" + lead: {"rot": (-14, 0, 0)},
            "hand_" + trail: {"rot": (-22, 0, 0)},
        }

    def pass_pose(planted, lifted, twist):
        return {
            "root": {"loc": (0, 0, 0.020)},
            "hips": {"rot": (1.0, twist * 0.4, 0)},
            "chest": {"rot": (0.5, -twist * 0.3, 0)},
            "head": {"rot": (-0.5, 0, 0)},
            "thigh_" + planted: {"rot": (-4, 0, 0)},
            "shin_" + planted: {"rot": (2, 0, 0)},
            "foot_" + planted: {"rot": (0, 0, 0)},
            "thigh_" + lifted: {"rot": (-2, 0, 0)},
            "shin_" + lifted: {"rot": (40, 0, 0)},
            "foot_" + lifted: {"rot": (-14, 0, 0)},
            "arm_" + planted: {"rot": (2, 0, 0)},
            "arm_" + lifted: {"rot": (-2, 0, 0)},
            "hand_" + planted: {"rot": (-16, 0, 0)},
            "hand_" + lifted: {"rot": (-16, 0, 0)},
        }

    frames = {
        1: step("L", "R", -0.014, 2.5, 5.0),
        7: pass_pose("L", "R", 2.0),
        13: step("R", "L", -0.014, 2.5, -5.0),
        19: pass_pose("R", "L", -2.0),
        25: step("L", "R", -0.014, 2.5, 5.0),
    }
    return skeleton.action("chuck_walk", frames)


# -------------------------------------------------------------------- TREE
#
# The approved silhouette, kept exactly: the calligraphic S-curve trunk and
# the fanned layering. What changes is that each layer is now a MASS.

def build_tree():
    """The tree, rebuilt for an INKED silhouette.

    ⛔⛔ THE OLD CANOPY WAS SIX OVERLAPPING PANCAKES and it survived three
    review rounds because at the shipping camera -- orthographic, pitch 30,
    far back -- its outline was a small soft blob and nobody could see what it
    was made of. The moment the camera came down and an ink line went round
    it, the whole construction was on display: a stack of flat lobed discs
    with no sky between them.

    ⭐⭐ WITH AN INK LINE, NEGATIVE SPACE IS THE SUBJECT. A solid mass outlines
    as a solid mass, so no amount of surface work inside it will read as
    foliage. What makes a drawn tree a tree is the holes: clumps that sit
    APART, on branches you can see, with sky between them. That is the whole
    redesign -- five separated clumps instead of six merged pads.

    ⭐ The facets were a SEPARATE fault and are already fixed without touching
    geometry. The internal lines were not faceting: they were the outline
    hull TEARING at split normals, which happens wherever two faces meet at
    more than the smoothing angle. `SMOOTH["tree"]` went 28 -> 62 and they
    vanished. Measured by A/B render before any remodelling was done, which
    is what kept this rebuild about silhouette rather than about polygons.
    """
    meshtools.reset_scene()
    parts = []

    # ⭐ The trunk runs ALL THE WAY to the crown now, rather than stopping at
    # 2.3 and letting a pad stack sit on top of nothing. A visible spine is
    # what the clumps hang off, and it is the difference between a tree and a
    # bush on a stick.
    stroke = [(0.00, 0.00, 0.00), (0.06, 0.02, 0.62), (0.00, -0.03, 1.22),
              (0.09, 0.02, 1.84), (0.13, -0.02, 2.38), (0.10, -0.04, 2.70)]
    trunk = forms.sweep("Trunk", "g_timber", stroke,
                        [0.235, 0.160, 0.120, 0.086, 0.056, 0.034],
                        segments=12, samples=9, profile_squash=0.82)
    meshtools.flare_base(trunk, height=0.32, strength=0.58)
    # Bark: four vertical gouges rather than noise. Noise everywhere reads as
    # dirt; a few marks read as a surface that was cut.
    forms.dents(trunk, [(0.07, -0.19, 0.34), (-0.12, 0.14, 0.72),
                        (0.14, -0.14, 1.18), (0.02, 0.16, 1.52)],
                depth=0.022, radius=0.13)
    meshtools.paint_by_normal(trunk, "g_timber", "g_timber", "g_ink",
                              up_at=0.7, down_at=-0.45)
    parts.append(trunk)

    # ⛔ EVERY CLUMP IS CARRIED. A clump with no branch under it reads as a
    # cloud parked beside a tree -- which is what the old sprigs did. Each
    # limb below ends inside its clump, so the join is hidden but the REACH
    # is visible, and that reach is what says the gap between two clumps is a
    # gap and not a mistake.
    limbs = [
        ((0.02, 0.00, 1.30), (-0.68, 0.09, 2.02), 0.064),
        ((0.09, 0.01, 1.52), (0.72, -0.07, 2.20), 0.060),
        ((0.05, -0.02, 1.18), (0.16, -0.58, 1.88), 0.052),
        ((0.11, 0.02, 1.74), (-0.22, 0.54, 2.36), 0.048),
    ]
    for origin, tip, radius in limbs:
        middle = tuple((origin[i] + tip[i]) / 2 for i in range(3))
        # Lift the midpoint: a limb leaves the trunk rising, then levels out
        # under the weight it carries. A straight line reads as a strut.
        middle = (middle[0], middle[1], middle[2] + 0.13)
        parts.append(forms.sweep(
            "Limb", "g_timber", [origin, middle, tip],
            [radius, radius * 0.66, radius * 0.34], segments=9, samples=6,
            profile_squash=0.84))

    # ⭐ FIVE CLUMPS, SEPARATED, one of them clearly the crown. Deliberately
    # odd-numbered and deliberately unequal: four equal masses round a trunk
    # is a clover, and a tree has a side it grew toward.
    #
    # ⛔ ROUNDER than the old pads. Height is now about 1.15x radius rather
    # than 0.9x, so each clump is a ball and not a bun -- a flat mass seen
    # from a low camera presents its edge, which is exactly the "stacked
    # plates" reading we are escaping.
    #
    # ⛔ points=36, not 26. The outline is now DRAWN in ink at a closer
    # camera, so the silhouette's own polygon count is visible. Fewer, deeper
    # lobes (5-6 at amount 0.19-0.23) read as foliage clumps; many shallow
    # ones read as a crinkle-cut edge.
    #
    # ⛔ AND UNEQUAL. Five clumps of nearly one size read as a bunch of
    # balloons, which is its own kind of generic -- the first cut of this did
    # exactly that. One dominant crown, two mid, two small, and the small
    # ones tucked so they break the outline rather than adding to the count.
    #     centre, radius, height, (up, mid, down), lobes, amount, squash, twist
    clumps = [
        ((-0.04, -0.10, 2.86), 0.70, 0.66, ("g_leaf_light", "g_leaf", "g_leaf_deep"), 6, 0.20, 0.96, 22),
        ((-0.78, 0.12, 2.14), 0.58, 0.58, ("g_leaf", "g_leaf", "g_leaf_deep"), 5, 0.24, 0.94, -28),
        ((0.82, -0.10, 2.30), 0.52, 0.54, ("g_leaf_light", "g_leaf", "g_leaf_deep"), 6, 0.22, 0.92, 30),
        ((0.26, -0.66, 1.92), 0.38, 0.42, ("g_leaf", "g_leaf_deep", "g_leaf_deep"), 5, 0.25, 0.96, -18),
        ((-0.30, 0.56, 2.44), 0.34, 0.38, ("g_leaf_light", "g_leaf_light", "g_leaf"), 4, 0.27, 0.95, 14),
    ]
    rng = random.Random(4)
    for index, (centre, radius, height, greens, lobes, amount, squash, twist) \
            in enumerate(clumps):
        # ⭐ A FLATTER TOP AND AN UNDERCUT BOTTOM. The default cushion
        # profile is near-spherical, and a sphere of leaves is a balloon.
        # Foliage spreads where it meets the light and falls away
        # underneath, so the radius is held wide through the upper half and
        # pulled in hard below the equator. It also puts the mass's widest
        # point ABOVE centre, which is what makes a canopy look supported
        # rather than balanced.
        mass = cushion("Leaf", greens[1], radius, height, centre,
                       lobes=lobes, amount=amount, squash=squash, twist=twist,
                       points=36,
                       profile=[(-0.52, 0.22), (-0.30, 0.62), (-0.08, 0.92),
                                (0.14, 1.00), (0.36, 0.96), (0.56, 0.74),
                                (0.74, 0.30)])
        # Two swells and a dent per mass: clumps within the clump. Enough to
        # break the revolve without costing a single extra triangle.
        for _ in range(2):
            angle = rng.uniform(0, math.tau)
            forms.swell(mass, (centre[0] + math.cos(angle) * radius * 0.6,
                               centre[1] + math.sin(angle) * radius * 0.6,
                               centre[2] + height * 0.12),
                        radius=radius * 0.52, amount=0.060)
        angle = rng.uniform(0, math.tau)
        forms.dents(mass, [(centre[0] + math.cos(angle) * radius * 0.7,
                            centre[1] + math.sin(angle) * radius * 0.7,
                            centre[2] - height * 0.10)],
                    depth=0.050, radius=radius * 0.44)
        forms.jitter_verts(mass, 0.007, seed=11 + index)
        meshtools.paint_by_normal(mass, greens[0], greens[1], greens[2],
                                  up_at=0.50, down_at=-0.28)
        parts.append(mass)

    # ⛔ ONLY TWO SPRIGS, and both sit ON a clump's edge rather than in open
    # air. The old four were free-floating and, once outlined, each one read
    # as a separate little bush hovering next to the tree. A sprig is for
    # roughening a silhouette that already exists.
    for centre, radius, lobes in (((-1.12, 0.16, 2.02), 0.20, 5),
                                  ((1.10, -0.14, 2.52), 0.18, 4)):
        sprig = cushion("Sprig", "g_leaf", radius, radius * 1.25, centre,
                        lobes=lobes, amount=0.26, points=22, twist=20)
        meshtools.paint_by_normal(sprig, "g_leaf_light", "g_leaf",
                                  "g_leaf_deep", up_at=0.5, down_at=-0.3)
        parts.append(sprig)

    tree = meshtools.join(parts, "Tree")
    meshtools.merge_doubles(tree)
    meshtools.drop_to_floor(tree)
    _scale_to_height(tree, TREE_HEIGHT)
    return [tree]


# ----------------------------------------------------------------- COTTAGE
#
# The off-centre ridge was the approved decision and it stays. Everything
# added here is ARCHITECTURE rather than trim: a course has a lap line, a
# dormer has a roof, a lintel carries a wall. That is the difference between
# "assembled from basic geometric shapes" and a building.

TILE_PTS = 8            # 32 outline points, so a scalloped eave has 4 per lobe
EAVE_Z = 2.05

# ⛔ TWO numbers decide whether this is a roof or a dome, and the first build
# got both wrong.
#
# DEPTH must stay nearly constant. Shrinking width AND depth together hips the
# roof in from all four sides, and with rounded-rectangle stations that is a
# bulbous cap -- which is exactly what rendered: a mushroom with faint steps on
# one side. A cottage roof is a GABLE: the width collapses to the ridge, the
# depth barely moves, and the ends stay as near-vertical triangles.
#
# CORNER RADIUS must be tiny. At 0.16 the stations are lozenges and the loft
# between them is a curved shell with no planes in it. At 0.05 the same 32
# points describe a near-rectangle, the loft gives flat planes, and `facet`
# keeps them.
#
# The ridge is pushed +0.62, so -X is the long shallow plane. `roof_edge_x`
# reads that plane straight off this table, which is how the dormers stay ON
# the roof when these numbers are next tuned.
#   z, width, depth, corner, x-shift
ROOF_COURSES = [
    (1.98, 3.42, 3.04, 0.05, -0.08),
    (2.26, 3.12, 3.00, 0.05, 0.06),
    (2.60, 2.70, 2.94, 0.05, 0.22),
    (2.94, 2.22, 2.86, 0.05, 0.36),
    (3.28, 1.68, 2.78, 0.05, 0.48),
    (3.60, 1.08, 2.70, 0.05, 0.57),
    (3.84, 0.56, 2.64, 0.04, 0.61),
    (COTTAGE_RIDGE, 0.20, 2.58, 0.03, 0.62),
]


def roof_edge_x(z, side=-1):
    """Where a roof plane is at height `z`. `side` is -1 for the long shallow
    plane and +1 for the short steep one."""
    edges = [(c[0], side * c[1] / 2.0 + c[4]) for c in ROOF_COURSES]
    if z <= edges[0][0]:
        return edges[0][1]
    for (z0, x0), (z1, x1) in zip(edges, edges[1:]):
        if z0 <= z <= z1:
            return x0 + (x1 - x0) * (z - z0) / max(z1 - z0, 1e-6)
    return edges[-1][1]


def build_cottage():
    meshtools.reset_scene()
    parts = []

    # Narrower and taller than the study box, with a BATTERED base -- the wall
    # is widest at the foot, which is what makes a building look like it is
    # standing on the ground rather than resting on it.
    walls = forms.loft("Walls", "s_wall", [
        (0.00, RR(2.86, 2.48, 0.14, 5)),
        (0.22, RR(2.70, 2.34, 0.13, 5)),
        (1.40, RR(2.64, 2.29, 0.13, 5)),
        (2.08, RR(2.60, 2.26, 0.13, 5)),
    ])
    meshtools.wobble(walls, amount=0.016, scale=2.6, seed=3,
                     axis_bias=(1, 1, 0.3))
    forms.dents(walls, [(-1.30, -0.60, 1.10), (1.32, 0.30, 0.70),
                        (0.20, -1.22, 1.70)], depth=0.024, radius=0.34)
    meshtools.paint_by_normal(walls, "s_wall", "s_wall", "s_wall_shade",
                              up_at=0.8, down_at=-0.55)
    parts.append(walls)

    # A plinth course: the house meets the ground in stone, not in plaster.
    parts.append(forms.loft("Plinth", "e_stone", [
        (0.00, RR(3.00, 2.62, 0.15, 5)),
        (0.30, RR(2.92, 2.54, 0.14, 5)),
        (0.34, RR(2.76, 2.39, 0.13, 5)),
    ]))

    parts.append(_tiled_roof())
    parts += _purlins()
    # Low on the slope, near the eave, which is where a dormer actually sits
    # and the only place one reads from the gameplay camera.
    parts += _dormer(y_pos=-0.74, width=0.84, height=0.80, roof_z=2.62)
    parts += _dormer(y_pos=0.60, width=0.64, height=0.66, roof_z=2.44)
    parts += _chimney()
    parts += _door()
    parts += _windows()

    cottage = meshtools.join(parts, "Cottage")
    meshtools.merge_doubles(cottage)
    # Low angle: the tile laps are 90-degree steps and survive a 10-degree
    # dissolve, while the wall wobble collapses into the flat planes the
    # sculptural direction wants.
    forms.facet(cottage, angle=10.0)
    meshtools.lean(cottage, degrees=0.8, axis="Y", pivot_z=0.0)
    meshtools.drop_to_floor(cottage)
    return [cottage]


def _tiled_roof():
    """Terracotta pantiles as real COURSES.

    Each course emits two loft stations -- its own plan, then the same plan
    lifted by the lap -- so there is a vertical riser and a shadow line all
    the way round at every course. That is what reads as tile; a smooth plane
    with a red texture on it reads as a painted roof, which is what it was.

    The eave course is scalloped, so the bottom edge of the roof is a row of
    pantile ends rather than a straight cut. It is the single most "illustrated"
    detail on the building and it costs nothing.
    """
    courses = ROOF_COURSES
    stations = []
    for index, (z, width, depth, corner, dx) in enumerate(courses):
        outline = RR(width, depth, corner, TILE_PTS)
        if index == 0:
            outline = wavy(outline, lobes=TILE_PTS, amount=0.050)
        outline = shift(outline, dx)
        stations.append((z, outline))
        if index < len(courses) - 1:
            stations.append((z + 0.058, outline))
    roof = forms.loft("Roof", "t_tile", stations, close_bottom=False)
    meshtools.sag(roof, depth=0.030, along="Y", span=1.5)
    meshtools.paint_by_normal(roof, "t_tile_sun", "t_tile", "t_tile_deep",
                              up_at=0.70, down_at=-0.15)
    return roof


def _purlins():
    """Rafter ends poking out under the EAVE.

    ⛔ The eave is on the X sides, not the front. When the roof was a dome
    these sat on the -Y face and looked right; once it became a proper gable
    that face became the GABLE END, and rafter ends poking out of a gable are
    simply wrong -- they rendered as three brown pegs stuck on the front wall.
    A rafter end belongs where the roof slope meets the wall head.
    """
    parts = []
    for y_pos in (-0.86, 0.0, 0.86):
        parts.append(forms.sweep(
            "Purlin", "s_wood_deep",
            [(-1.26, y_pos, 2.00), (-1.62, y_pos, 1.94)],
            [0.052, 0.046], segments=6, profile_squash=0.78))
    return parts


def _dormer(y_pos, width, height, roof_z, side=1):
    """A gabled dormer, seated on whichever roof plane `side` names.

    ⛔ Where a dormer can go is decided by the roof, and the roof changed. The
    first pair sat on the -Y face at x = +/-0.5; when the roof stopped doming
    and started gabling, that face became a vertical gable end and both
    dormers ended up entirely INSIDE it -- they rendered as nothing at all.
    ⛔ And then on the WRONG PLANE. The ridge is pushed +0.62, so -X is the
    long shallow plane, and the reasonable-sounding conclusion was that a
    dormer belongs there. But the camera sits at +X/-Y and looks back along
    it, so -X is the FAR slope: both dormers rendered as two red ridges
    peeking over the roofline. The plane the gameplay camera actually sees is
    +X, the short steep one -- which is an ordinary place for a dormer, and it
    also breaks up the one large blank area in the elevation.

    ⛔ And a dormer GROWS OUT of the roof. The second seating centred a
    0.66-deep box on the slope line, so half of it hung off into the air and
    the render showed a red shed floating beside the chimney. The box runs
    1.30 deep from just outside the slope back INTO the roof mass, where the
    far end is swallowed -- which is how a real dormer is framed anyway.
    `roof_edge_x` reads the slope off the course table, so this survives the
    next time those numbers are tuned.
    """
    parts = []
    outer = roof_edge_x(roof_z, side) + side * 0.24
    front = outer - side * 0.65
    depth = 1.30
    base = roof_z - height * 0.58

    parts.append(forms.loft("DormerWall", "s_wall", [
        (base, RR(depth, width, 0.07, 4)),
        (base + height * 0.72, RR(depth, width, 0.07, 4)),
    ], at=(front, y_pos, 0.0)))

    top = base + height * 0.72
    parts.append(forms.loft("DormerRoof", "t_tile", [
        (top, RR(depth + 0.06, width + 0.26, 0.04, 5)),
        (top + 0.050, RR(depth + 0.06, width + 0.26, 0.04, 5)),
        (top + 0.155, RR(depth, width * 0.62, 0.03, 5)),
        (top + 0.205, RR(depth, width * 0.62, 0.03, 5)),
        (top + 0.290, RR(depth - 0.04, width * 0.16, 0.03, 5)),
    ], at=(front, y_pos, 0.0), close_bottom=False))
    parts.append(forms.loft("DormerFrame", "s_cream", [
        (base + 0.07, RR(0.09, width - 0.12, 0.03, 3)),
        (base + height * 0.66, RR(0.09, width - 0.12, 0.03, 3)),
    ], at=(outer - side * 0.02, y_pos, 0.0)))
    parts.append(forms.loft("DormerPane", "s_wood_deep", [
        (base + 0.11, RR(0.07, width - 0.22, 0.03, 3)),
        (base + height * 0.60, RR(0.07, width - 0.22, 0.03, 3)),
    ], at=(outer + side * 0.015, y_pos, 0.0)))
    parts.append(forms.loft("DormerSill", "e_stone", [
        (base + 0.03, RR(0.16, width + 0.08, 0.04, 3)),
        (base + 0.09, RR(0.14, width + 0.02, 0.03, 3)),
    ], at=(outer - side * 0.02, y_pos, 0.0)))
    return parts


def _chimney():
    """Coursed stone, leaning, with a corbelled cap. Lean, courses and cap are
    three decisions; a tapered box is none."""
    # Shorter and fatter than the first pass, which at 0.50 across and 1.9 m
    # of stack read as a factory chimney on a cottage.
    stations = []
    z = 2.46
    for index in range(4):
        width = 0.68 - index * 0.016
        outline = RR(width, width * 0.92, 0.06, 4)
        stations.append((z, outline))
        stations.append((z + 0.24, outline))
        z += 0.26
    stations.append((z + 0.02, RR(0.82, 0.76, 0.07, 4)))
    stations.append((z + 0.17, RR(0.78, 0.72, 0.07, 4)))
    chimney = forms.loft("Chimney", "e_stone", stations, at=(-1.16, 0.52, 0.0))
    meshtools.lean(chimney, degrees=2.6, axis="Y", pivot_z=2.46)
    meshtools.paint_by_normal(chimney, "e_stone_sun", "e_stone",
                              "e_stone_deep", up_at=0.8, down_at=-0.4)
    return [chimney]


def _door():
    """A round-headed arch with the knob dead centre.

    The arch is nearly a semicircle, which is the one shape on the building
    that is allowed to be perfectly drawn -- everything else leans or wobbles,
    so the door becomes the thing the eye settles on, and it is where the
    player walks out of.
    """
    parts = []
    front = -1.22
    width, jamb = 0.78, 0.22
    # The arch: stations whose width follows a circle, so the head is round
    # rather than chamfered.
    arch, head_z = [], 1.62
    springing = 1.20
    for z, factor in ((0.0, 1.0), (springing, 1.0),
                      (springing + 0.13, 0.985), (springing + 0.24, 0.94),
                      (springing + 0.33, 0.86), (springing + 0.39, 0.74)):
        arch.append((z, RR(width * factor, jamb, 0.05, 4)))
    arch.append((head_z, RR(width * 0.30, jamb, 0.04, 4)))
    # ⛔ The door stands PROUD of its surround. In the first build the stone
    # arch sat 0.055 in front of the door and was 0.16 wider, so it did not
    # frame the door -- it covered it, and the whole blue of the front
    # elevation simply vanished behind a grey slab.
    parts.append(forms.loft("Door", "s_blue", arch,
                            at=(-0.30, front - 0.065, 0.0)))

    surround = []
    for z, factor in ((0.0, 1.0), (springing, 1.0),
                      (springing + 0.15, 0.985), (springing + 0.28, 0.94),
                      (springing + 0.39, 0.85), (springing + 0.46, 0.72)):
        surround.append((z, RR((width + 0.16) * factor, jamb * 0.74, 0.05, 4)))
    surround.append((head_z + 0.10, RR((width + 0.16) * 0.28, jamb * 0.74,
                                       0.04, 4)))
    parts.append(forms.loft("DoorArch", "e_stone", surround,
                            at=(-0.30, front + 0.010, 0.0)))

    parts.append(forms.superform(
        "Knob", "s_accent", size=(0.098, 0.098, 0.098), exponent=2.7,
        segments=11, rings=9, at=(-0.30, front - 0.120, 0.80)))
    for z_pos, size in ((0.0, (1.34, 0.86)), (0.085, (1.18, 0.70))):
        parts.append(forms.loft("Step", "e_stone", [
            (z_pos, RR(size[0], size[1], 0.09, 4)),
            (z_pos + 0.095, RR(size[0] - 0.10, size[1] - 0.08, 0.08, 4)),
        ], at=(-0.30, front - 0.44, 0.0)))
    return parts


def _windows():
    """Two ground-floor windows, a stone lintel and sill each, and a window
    box with flowers under one of them.

    The box is not a prop: it sits on the sill, it is the only saturated
    colour on the wall, and it is what makes the house look lived in.
    """
    parts = []
    front = -1.20
    for x_pos, z_pos, width, box in ((0.76, 1.12, 0.74, True),
                                     (-1.36, 1.06, 0.60, False)):
        on_side = x_pos < -1.2
        if on_side:
            at = (-1.34, 0.10, 0.0)
            frame = RR(0.14, width, 0.04, 4)
            pane = RR(0.08, width - 0.18, 0.03, 4)
            stone = RR(0.22, width + 0.22, 0.05, 4)
            at_pane = (-1.40, 0.10, 0.0)
        else:
            at = (x_pos, front, 0.0)
            frame = RR(width, 0.14, 0.04, 4)
            pane = RR(width - 0.18, 0.08, 0.03, 4)
            stone = RR(width + 0.22, 0.22, 0.05, 4)
            at_pane = (x_pos, front - 0.06, 0.0)

        parts.append(forms.loft("WinFrame", "s_cream", [
            (z_pos - width * 0.58, frame), (z_pos + width * 0.58, frame)],
            at=at))
        parts.append(forms.loft("Pane", "s_wood_deep", [
            (z_pos - width * 0.46, pane), (z_pos + width * 0.46, pane)],
            at=at_pane))
        # Glazing bars. Without them a window is a dark rectangle, which reads
        # as a hole punched in the wall rather than as glass -- and a cross of
        # two thin bars is the single most "illustrated" mark on the building.
        bar_y = at_pane[1] - (0.055 if not on_side else 0.0)
        bar_x = at_pane[0] - (0.055 if on_side else 0.0)
        if on_side:
            parts.append(forms.sweep("BarV", "s_cream",
                [(bar_x, at_pane[1], z_pos - width * 0.44),
                 (bar_x, at_pane[1], z_pos + width * 0.44)],
                [0.019, 0.019], segments=5, profile_squash=0.5))
            parts.append(forms.sweep("BarH", "s_cream",
                [(bar_x, at_pane[1] - width * 0.40, z_pos),
                 (bar_x, at_pane[1] + width * 0.40, z_pos)],
                [0.019, 0.019], segments=5, profile_squash=0.5))
        else:
            parts.append(forms.sweep("BarV", "s_cream",
                [(at_pane[0], bar_y, z_pos - width * 0.44),
                 (at_pane[0], bar_y, z_pos + width * 0.44)],
                [0.019, 0.019], segments=5, profile_squash=0.5))
            parts.append(forms.sweep("BarH", "s_cream",
                [(at_pane[0] - width * 0.40, bar_y, z_pos),
                 (at_pane[0] + width * 0.40, bar_y, z_pos)],
                [0.019, 0.019], segments=5, profile_squash=0.5))
        for offset, thickness in ((width * 0.62, 0.11), (-width * 0.66, 0.13)):
            parts.append(forms.loft("Lintel", "e_stone", [
                (z_pos + offset, stone),
                (z_pos + offset + thickness, stone)], at=at))
        if box:
            parts.append(forms.loft("Box", "s_wood", [
                (z_pos - width * 0.80, RR(width + 0.10, 0.22, 0.04, 4)),
                (z_pos - width * 0.66, RR(width + 0.16, 0.26, 0.05, 4)),
            ], at=(x_pos, front - 0.11, 0.0)))
            for index in range(3):
                bloom = "f_bloom" if index != 1 else "f_bloom_pale"
                parts.append(cushion(
                    "Bloom", bloom, 0.11, 0.13,
                    (x_pos - 0.22 + index * 0.22, front - 0.13,
                     z_pos - width * 0.60),
                    lobes=5, amount=0.26, points=14, twist=18))
    return parts


# ------------------------------------------------------------------- BLOCK
#
# The approved block, UNCHANGED where it matters: 0.8 cubed, exponent 5.2, the
# 0.640 plaque, the measured label offset, the five plaque node names and the
# single shared flat face material. What is new is the raised rim, so the
# cream face reads as inset rather than applied, and the wood gets some grain.

def build_block():
    meshtools.reset_scene()
    half = BLOCK_SIZE / 2

    body = forms.superform("Cube", "c_wood", size=(BLOCK_SIZE,) * 3,
                           exponent=BLOCK_EXPONENT, segments=26, rings=18,
                           at=(0, 0, half))
    forms.dents(body, [(half, half, half * 1.9), (-half, half, half * 0.3),
                       (half, -half, half * 0.4)], depth=0.018, radius=0.28)
    forms.jitter_verts(body, 0.0030, seed=31)
    # Grain: four long shallow gouges down the wood, not noise. The wash in
    # the bake carries colour drift already; what it cannot do is suggest that
    # the block was cut out of something.
    forms.dents(body, [(0.0, -half, 0.26), (0.0, -half, 0.58),
                       (half, 0.0, 0.30), (-half, 0.12, 0.62)],
                depth=0.006, radius=0.22)
    meshtools.paint_by_normal(body, "c_wood", "c_wood", "c_wood_deep",
                              up_at=0.9, down_at=-0.7)

    plaques, bezels = [], []
    thickness = 0.048
    for name, normal in BLOCK_FACES:
        centre = plaque_centre(normal, thickness)
        if normal[2] > 0.5:
            size = (LETTER_PLAQUE, LETTER_PLAQUE, thickness)
        elif abs(normal[0]) > 0.5:
            size = (thickness, LETTER_PLAQUE, LETTER_PLAQUE)
        else:
            size = (LETTER_PLAQUE, thickness, LETTER_PLAQUE)
        plaques.append(forms.superform(name, "c_cream", size=size,
                                       exponent=6.0, segments=16, rings=12,
                                       at=centre))
        bezel = face_bezel(name + "Rim", "c_wood", normal)
        meshtools.paint_by_normal(bezel, "c_wood", "c_wood", "c_wood_deep",
                                  up_at=0.85, down_at=-0.55)
        bezels.append(bezel)

    cream = painter.flat_material("foundation_block_face", "c_cream",
                                  roughness=0.96)
    painter.assign(plaques, cream)
    # The rims join the BODY, not the plaques: `alphabet_block.gd` duplicates
    # Front's material onto every child that is not called Cube, and the
    # lever's gold highlight depends on exactly the five plaques getting it.
    body = meshtools.join([body] + bezels, "Cube")
    asset.verify_contract([body] + plaques,
                          ["Cube", "Front", "Right", "Back", "Left", "Top"])
    return [body] + plaques


# ------------------------------------------------------------------- WORLD
#
# "Does this look like the Shire?" is the test, and the honest answer for the
# flat green plane was no. What a field like that is missing is not props:
#
#   * LAND. Ground that rolls, so there is a horizon behind the cottage and a
#     reason for the eye to travel.
#   * A WORN WAY. A path that is sunk into the ground rather than laid on top
#     of it -- a hollow way, which is the single most Shire-like thing there
#     is, and it comes free once the terrain can be deformed.
#   * BOUNDARY. A drystone wall and a hedge: a field is only a field because
#     something encloses it.
#   * CULTIVATION. One vegetable row. Somebody lives here and eats.
#   * CONTACT. Grass growing where every object meets the ground, so nothing
#     looks dropped onto the surface.
#
# The one constraint that is not aesthetic: THE PLAY AREA MUST STAY FLAT. The
# game walks a character around and puts blocks down on it, so the terrain is
# masked almost flat within 5 m of the origin and only rolls beyond 8 m. Flat
# where you play, rolling where you look.

# Where everything stands. Shared by the terrain shaper and the render script
# so that the pad under the cottage and the cottage are in the same place --
# that agreement IS the integration he asked for.
SCENE = {
    "cottage": ((-2.70, 3.00), 14.0),
    "tree": ((3.95, 0.75), -24.0),
    "chuck": ((-0.45, -1.85), 18.0),
}
# The first block's 38 degrees is not a composition choice: the gameplay
# camera is at yaw 30, so a block spun -22 presents its plaques at 62 degrees
# off-normal and a letter on one is foreshortened to a sliver. 38 turns a face
# almost square to the camera, which is what a close-up of a LETTER block has
# to show.
BLOCKS = [((1.35, -2.45), 38.0), ((2.42, -1.95), 11.0), ((0.30, -3.05), -24.0)]

# The worn way, drawn from the cottage door out past where the blocks lie.
PATH = [(-2.95, 1.45), (-2.45, 0.20), (-1.35, -1.00), (0.35, -1.95),
        (2.05, -2.85), (3.45, -4.05), (4.70, -5.60), (6.20, -7.40)]

# ⛔ Set OUT from the path, not beside it. The first line ran about 1.4 m off
# the way and the render showed the wall cutting straight through the block
# row with Chuck standing in it -- a field boundary has to be at the edge of
# the field, and the play area is the field.
# ⛔ The kitchen garden moved OUT from behind the cottage. At (-0.30, 4.70) it
# was directly behind the house from the gameplay camera and the player would
# never once have seen it. It sits beside the house now, in the mid-ground,
# between the cottage and the tree.
#
# BED is the dug ground -- painted into the terrain, not laid on it -- and the
# picket fence, the rows, the frame and the scarecrow are all placed off it,
# so moving the garden moves the whole smallholding.
BED = (0.95, 2.70)
BED_HALF = (1.72, 1.34)

WALL = [(-7.60, 0.20), (-6.00, -1.40), (-4.40, -2.90), (-2.80, -4.20),
        (-1.10, -5.40), (0.60, -6.80)]

# centre_x, centre_y, amplitude, radius -- hand-placed, not noise. A landscape
# made of noise has no composition; these are chosen so the big rise sits
# BEHIND the cottage and the eye is carried left to right across the frame.
# ⛔ Every hill centre is pushed OUTSIDE the play area. Three of them used
# to sit within 8 m of the origin, suppressed by the play mask -- which was
# fine while the mask only damped them to 35%, and became a 43-degree WALL
# the moment the play area went properly flat and the mask had to carry the
# whole transition. Hills belong where nothing walks.
# centre_x, centre_y, amplitude, radius
HILLS = [
    (-13.0, 14.5, 2.30, 10.5),
    (14.5, 15.0, 2.70, 11.5),
    (-17.5, 2.5, 1.70, 9.5),
    (2.0, 18.5, 2.10, 10.5),
    (16.5, -6.5, 1.30, 8.5),
    (-9.5, -16.0, 1.50, 9.5),
]


def _densify(points, samples=8):
    out = []
    for index in range(len(points) - 1):
        ax, ay = points[index]
        bx, by = points[index + 1]
        for step in range(samples):
            k = step / float(samples)
            out.append((ax + (bx - ax) * k, ay + (by - ay) * k))
    out.append(points[-1])
    return out


_PATH_DENSE = _densify(PATH, 10)


def path_distance(x, y, dense=None):
    """Distance from a point to the worn way, in metres."""
    best = 1e9
    for px, py in (dense or _PATH_DENSE):
        best = min(best, (px - x) ** 2 + (py - y) ** 2)
    return math.sqrt(best)


# ⛔⛔ THE PLAY AREA IS DEAD FLAT. This has now been decided twice in
# opposite directions, so the reasoning matters.
#
# It started flat on an unchecked assumption that the engine needed it.
# That assumption was wrong -- `player.gd` is a CharacterBody3D with gravity
# and Phoneme Village has shipped raised terrain since September -- so the
# floor was given 0.35 m of roll at up to 7.8 degrees.
#
# Seeing it decided it: "the up and down hill-like nature of the floor was
# the wrong call, as it doesn't work and even if you got it to work like you
# have it mapped, it would be wrong." Which is right, and the engine
# argument was never the point. A floor that rolls fights everything placed
# on it -- a dropped cube sits crooked, a building needs its own pad, and at
# this gentle an amplitude it reads as wobble rather than as landscape.
#
# So: zero inside the play area, and the hand-placed hills still rise beyond
# 8 m where nothing is walked on and they are pure horizon. The HOLLOW WAY
# goes too; the path reads from its colour and its edge, which is where it
# was always doing the work.
PLAY_RELIEF = 0.0
GENTLE = 0.0


def _play_mask(x, y):
    """0 in the play area, 1 out in the landscape.

    ⛔ Flat to 9 m and the rise spread over the next 7, not 5 m and 3.2. The
    mask now carries the ENTIRE transition from dead flat to full hills, so
    a short ramp puts a cliff exactly where the player is standing.
    """
    distance = math.hypot(x, y)
    return min(max((distance - 9.0) / 7.0, 0.0), 1.0) ** 1.5


def _raw_height(x, y):
    height = 0.0
    for cx, cy, amplitude, radius in HILLS:
        distance = math.hypot(x - cx, y - cy)
        if distance < radius:
            height += amplitude * math.cos(
                distance / radius * math.pi * 0.5) ** 2
    # One long low ridge, and a fine undulation so no plane is ever quite flat.
    height += 0.14 * math.sin(x * 0.21 + 0.6) * math.cos(y * 0.17 - 0.3)
    height += 0.045 * math.sin(x * 1.31 + y * 0.77)
    return height


def _gentle(x, y):
    """The always-on undulation, play area included. Long and shallow."""
    return GENTLE * (0.60 * math.sin(x * 0.42 + 0.9) * math.cos(y * 0.37 - 0.5)
                     + 0.40 * math.sin(x * 0.78 - 1.4) * math.cos(y * 0.66 + 0.8))


def landform(x, y):
    """The shape of the LAND, before anything was cut into it.

    `local_relief` asks this rather than `terrain_height` for two reasons.
    It is correct -- relief describes the landform, and a hollow way and a
    building pad are man-made cuts that should not read as damp ground -- and
    it keeps `path_distance` out of a loop that runs nine times per vertex on
    a 7,700-vertex grid.
    """
    return (_raw_height(x, y) * (PLAY_RELIEF + (1.0 - PLAY_RELIEF)
                                 * _play_mask(x, y))
            + _gentle(x, y))


def terrain_height(x, y):
    """The finished ground height, pad and hollow way included.

    Exported so the render script can SIT objects on the terrain instead of
    assuming z = 0. An object floating two centimetres above a field is most
    of what "disconnected" means.
    """
    height = landform(x, y)

    # Level a pad under the cottage. A building standing on a slope at this
    # scale reads as a mistake, not as terrain.
    (cx, cy), _ = SCENE["cottage"]
    distance = math.hypot(x - cx, y - cy)
    if distance < 3.4:
        # A building still gets a LEVEL pad. Chuck can walk a slope; a
        # cottage standing on one reads as a mistake, and anything with the
        # pedestal's stretch-a-fixed-base trick needs level footing too.
        pad = landform(cx, cy)
        blend = 1.0 - min(max((distance - 2.1) / 1.3, 0.0), 1.0)
        height += (pad - height) * blend

    # ⛔ No hollow way. A 75 mm dip is invisible as relief and visible as a
    # block sitting lower than the one beside it.
    return height


# ------------------------------------------------------------------- edges
#
# The ground had CAUSE after the last pass but no EDGES, and a field is read
# by its edges: the line a mower left, the track feet wore off the path, the
# strip along a wall nothing ever reaches. Every one of those is a boundary,
# not a gradient, and a gradient is all the previous field could produce.

# The kept ground: what somebody actually mows, round the house and garden.
MOWN = [(-5.05, 0.55), (-4.70, 5.25), (-1.60, 6.15), (1.90, 5.70),
        (3.30, 3.60), (3.15, 1.15), (0.60, 0.05), (-2.40, -0.45)]

# Desire lines. A track is not a path: nobody laid it, feet made it, so it is
# narrow, it is scuffed rather than bare, and it goes somewhere specific.
TRACKS = [
    [(-2.25, -0.20), (-1.20, 0.40), (-0.10, 1.05), (0.20, 1.34)],   # to the gate
    [(1.30, -2.00), (2.35, -1.20), (3.25, -0.30), (3.80, 0.35)],    # to the tree
]


def _poly_distance(x, y, poly):
    """Distance to a closed polygon's EDGE, and whether the point is inside.

    Returns (distance, inside). Distance to the edge rather than to the
    vertices, so a long straight run of boundary does not bulge.
    """
    best = 1e9
    inside = False
    count = len(poly)
    for index in range(count):
        ax, ay = poly[index]
        bx, by = poly[(index + 1) % count]
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        t = 0.0 if length_sq < 1e-9 else max(0.0, min(
            1.0, ((x - ax) * dx + (y - ay) * dy) / length_sq))
        best = min(best, math.hypot(x - (ax + dx * t), y - (ay + dy * t)))
        if (ay > y) != (by > y) and x < ax + (y - ay) / (by - ay) * dx:
            inside = not inside
    return best, inside


_TRACKS_DENSE = [_densify(track, 10) for track in TRACKS]


def track_distance(x, y):
    best = 1e9
    for dense in _TRACKS_DENSE:
        for px, py in dense:
            best = min(best, (px - x) ** 2 + (py - y) ** 2)
    return math.sqrt(best)


def _edge(value, at, width):
    """0 below `at`, 1 above `at + width`, smooth between. One boundary."""
    t = min(max((value - at) / max(width, 1e-6), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def local_relief(x, y, radius=2.8):
    """How high this point sits against the ground AROUND it.

    The thing that was wrong with the first colour field. It used absolute
    height, which in a play area deliberately kept within 0.35 m of level
    means every point gets the same answer -- so the only variation left came
    from sine waves, and smooth noise over a whole field reads as smoke.

    Relief measured against the LOCAL average is what actually drives a
    field's colour: the crown of a swell drains and burns off pale, the
    hollow beside it holds water and stays dark, and they can be a metre
    apart on ground that is level overall.
    """
    here = landform(x, y)
    around = 0.0
    for step in range(8):
        angle = math.tau * step / 8
        around += landform(x + math.cos(angle) * radius,
                           y + math.sin(angle) * radius)
    return here - around / 8.0


# Things that keep the ground beside them damp and dark: a wall, a hedge, a
# building, a canopy. x, y, radius.
def _shade_sources():
    sources = [(SCENE["cottage"][0][0], SCENE["cottage"][0][1], 3.0),
               (SCENE["tree"][0][0], SCENE["tree"][0][1], 1.9)]
    for index in range(0, len(WALL)):
        sources.append((WALL[index][0], WALL[index][1], 1.0))
    for (hx, hy) in ((5.30, 3.90), (6.60, 2.40), (-5.40, 4.60), (-6.90, 3.10)):
        sources.append((hx, hy, 1.9))
    return sources


def _grass_position(x, y, z, nz, relief, shade):
    """Where a point sits on the earth-to-sunlit-grass ramp.

    ⛔⛔ RE-WEIGHTED FOR A FLAT FLOOR, and this is a consequence of flattening
    that is easy to miss. The field used to be driven mostly by
    `local_relief` and by slope -- a crown burns pale, a bank has thin soil.
    On a dead-flat floor BOTH OF THOSE ARE EXACTLY ZERO, so the ground
    collapsed to one almost uniform green and all the work that went into
    giving it causes quietly stopped doing anything.

    What survives flattening is everything POSITIONAL: the mown line, the
    worn tracks, the path, the headland, the damp under a wall -- and
    patchiness, which now has to carry the variation the landform used to.
    Relief and slope are kept at small weights so the far field, which still
    rises beyond 9 m, is not flat-coloured.
    """
    steep = 1.0 - min(max(nz, 0.0), 1.0)
    patch = (0.52 * math.sin(x * 0.63 + 1.3) * math.sin(y * 0.51 - 0.7)
             + 0.30 * math.sin(x * 1.47 - 0.4) * math.sin(y * 1.21 + 2.1)
             + 0.18 * math.sin(x * 3.10 + 1.9) * math.sin(y * 2.70 - 1.1))
    return min(max(0.56
                   + 0.34 * patch       # the dominant term on flat ground
                   + 0.40 * relief      # still real out in the far field
                   + 0.18 * steep
                   - 0.24 * shade, 0.34), 0.88)


def build_terrain():
    """The land. One mesh, painted by a field rather than by its normals."""
    import bmesh
    import bpy
    from mathutils import Vector

    meshtools.reset_scene()
    half = GROUND_SIZE / 2
    count = int(GROUND_SIZE / GROUND_STEP)

    bm = bmesh.new()
    grid = []
    for row in range(count + 1):
        y = -half + row * GROUND_STEP
        line = []
        for column in range(count + 1):
            x = -half + column * GROUND_STEP
            line.append(bm.verts.new(Vector((x, y, terrain_height(x, y)))))
        grid.append(line)
    for row in range(count):
        for column in range(count):
            bm.faces.new([grid[row][column], grid[row][column + 1],
                          grid[row + 1][column + 1], grid[row + 1][column]])
    # ⛔⛔ `recalc_face_normals` POINTS THIS GRID DOWNWARDS. It makes normals
    # CONSISTENT, which for a closed volume also means outward -- but an open
    # heightfield has no outside, and it chose -Z. Measured: nz was -1.0 at
    # every vertex.
    #
    # That silently broke the colour field. `_grass_position` computes
    # `steep = 1 - max(nz, 0)`, so nz = -1 made steep = 1 EVERYWHERE and added
    # a flat +0.55 to every vertex, saturating the ramp at its palest stop.
    # The whole terrain baked as `f_grass_sun`: 23% of the texture was five
    # shades of one colour. The mown line, the tracks and the path edge still
    # read because those return or subtract absolutely -- which is exactly why
    # the bug survived three rounds of looking at renders and was only caught
    # by sampling the baked PNG.
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    flipped = [face for face in bm.faces if face.normal.z < 0.0]
    if flipped:
        bmesh.ops.reverse_faces(bm, faces=flipped)

    mesh = bpy.data.meshes.new("TerrainMesh")
    bm.to_mesh(mesh)
    bm.free()
    terrain = bpy.data.objects.new("Terrain", mesh)
    bpy.context.collection.objects.link(terrain)
    meshtools.set_part_color(terrain, "f_grass")

    sources = _shade_sources()

    def field(position, normal):
        x, y = position.x, position.y

        # 1. The dug bed. Bare earth, hard edged, because a spade made it.
        inside_bed = max(abs(x - BED[0]) / BED_HALF[0],
                         abs(y - BED[1]) / BED_HALF[1])
        if inside_bed < 0.95:
            return 0.04 + 0.10 * max(inside_bed - 0.55, 0.0) / 0.40

        shade = 0.0
        for sx, sy, radius in sources:
            distance = math.hypot(x - sx, y - sy)
            if distance < radius:
                shade = max(shade, 1.0 - distance / radius)
        grass = _grass_position(x, y, position.z, normal.z,
                                local_relief(x, y), shade)

        # 2. The mown line. Mowing does not change a field's colour so much
        # as REMOVE ITS VARIATION -- that is what the eye reads, and it is
        # why compressing the ramp toward the middle and nudging it lighter
        # gives a boundary you can see without a hard colour change across
        # it. Rough ground beyond keeps the full range.
        edge_distance, inside = _poly_distance(x, y, MOWN)
        if inside:
            # ⛔ Gently. At 0.62 compression and a 0.055 lift the kept ground
            # went flat and pale and read as a slab of lawn laid over the
            # field -- which is louder than the boundary it was meant to
            # create. Mown grass is EVENER, barely lighter; the eye finds it
            # by the change in texture, not by a change of colour.
            kept = _edge(edge_distance, 0.0, 0.55)
            grass = grass + (0.60 - grass) * 0.42 * kept + 0.030 * kept
        else:
            # And the line itself: the ragged fringe just outside the turn,
            # where the mower never quite reached. 0.5 m of darker, uncut
            # grass is what actually draws a mown edge.
            grass -= 0.115 * (1.0 - _edge(edge_distance, 0.05, 0.50))

        # 3. The headland: the strip along the wall a mower never reaches.
        #    Rougher, darker, and with its own edge rather than a falloff.
        wall = _poly_distance(x, y, WALL + WALL[::-1])[0]
        grass -= 0.13 * (1.0 - _edge(wall, 0.45, 0.55))

        # 4. Tracks worn off the path. Scuffed, not bare: feet thin the sward
        #    long before they strip it, so this lands between the deep grass
        #    and the earth and keeps a crisp edge either side.
        track = track_distance(x, y)
        if track < 0.80:
            scuff = 1.0 - _edge(track, 0.22, 0.46)
            grass = grass + (0.255 - grass) * scuff

        # 5. The way itself. ⛔ The transition is 0.30 m, not 0.85. A worn
        #    path has an EDGE -- the grass stops where the boots are -- and
        #    feathering it over most of a metre was the single biggest reason
        #    the ground read as gradient everywhere.
        distance = path_distance(x, y)
        if distance < 0.95:
            return 0.03 + 0.14 * (distance / 0.95)
        if distance < 1.25:
            blend = _edge(distance, 0.95, 0.30)
            return 0.17 + (grass - 0.17) * blend
        return grass

    paint_field(terrain, [
        (0.00, "e_earth_deep"),
        (0.12, "e_earth"),
        (0.26, "f_grass_deep"),
        (0.58, "f_grass"),
        # A hue step, not just a lighter green. Ramping value alone produced
        # soft grey-green cloud; a field varies in colour, not only in tone.
        (0.78, "f_grass_dry"),
        (0.95, "f_grass_sun"),
    ], field)
    return [terrain]


def _blade(root, lean, height, width, colour, seed):
    """One blade of grass, as a flat RIBBON.

    ⛔ Not a `sweep`. A sweep makes a thin tapering TUBE, and three of them in
    a clump occlude each other from every direction -- the gouache recipe's
    ao_strength 0.68 and edge_dark 0.20 then stack and crush the whole thing,
    which is why every tuft baked BLACK for three rounds of renders. There is
    one bake recipe per asset, so it cannot be fixed per object.

    A ribbon is two broad faces that mostly see the sky. It is also what a
    blade of grass actually is, which is the usual sign the generator is
    right.
    """
    rng = random.Random(seed)
    tip = (root[0] + lean[0] * height, root[1] + lean[1] * height,
           root[2] + height)
    mid = (root[0] + lean[0] * height * 0.30,
           root[1] + lean[1] * height * 0.30,
           root[2] + height * 0.62)
    blade = forms.ribbon("Blade", colour, [root, mid, tip],
                         [width, width * 0.72, width * 0.14],
                         thickness=0.007,
                         roll=rng.uniform(-0.5, 0.5))
    # ⛔⛔ AND IT IS EXCLUDED FROM THE BAKE. Lightening the colour twice did
    # not fix the black grass because the colour was never the problem.
    # `atlas_unwrap` packs islands by SURFACE AREA, and a blade of grass has
    # almost none -- on a 1024 sheet shared with a wall and sixty stones its
    # island lands a few pixels across, which is SMALLER THAN the bake's
    # 10-pixel margin. What got baked into those pixels was margin bleed and
    # ambient occlusion from its neighbours, every time, whatever colour the
    # vertices were.
    #
    # Tagging it sends it out of the atlas entirely and onto a flat material,
    # the same mechanism that keeps the block's letter faces perfectly cream.
    # Grass at 142 px per metre wants a flat colour anyway.
    blade["flat_grass"] = colour
    return blade


def _split_flat_grass(parts, name):
    """Pull the tagged blades out, give them ONE flat material each colour.

    `asset.produce` skips an object whose every material is a flat colour, so
    these never reach `atlas_unwrap` or the bake. Returned alongside the main
    mesh, which is exactly how the alphabet block ships a baked body and five
    flat letter faces.
    """
    solid = [p for p in parts if "flat_grass" not in p]
    groups = {}
    for part in parts:
        if "flat_grass" in part:
            groups.setdefault(part["flat_grass"], []).append(part)
    out = []
    for colour, blades in sorted(groups.items()):
        clump = meshtools.join(blades, "%s_%s" % (name, colour))
        meshtools.merge_doubles(clump)
        painter.assign([clump], painter.flat_material(
            "foundation_%s_%s" % (name, colour), colour, roughness=0.97))
        out.append(clump)
    return solid, out


def _tuft(at, height=0.17, blades=3, colour="f_grass_deep", seed=0):
    """A clump of grass. Kept for the few places that want one on its own."""
    rng = random.Random(seed)
    parts = []
    for _ in range(blades):
        angle = rng.uniform(0, math.tau)
        out = rng.uniform(0.30, 0.65)
        parts.append(_blade(at, (math.cos(angle) * out, math.sin(angle) * out),
                            height * rng.uniform(0.8, 1.25),
                            rng.uniform(0.038, 0.052), colour,
                            seed + int(angle * 97)))
    return parts


def _grass_fringe(points, offsets, spacing=0.62, height=0.22, seed=0,
                  jitter=0.16, blades=2):
    """A CONTINUOUS fringe of grass along a line, offset to either side.

    ⛔ This replaces a scatter, and the difference is the whole note. Grass
    was being dropped three-at-a-time around whatever object happened to be
    nearby, at arbitrary angles -- which is not a rule, it is a sprinkle, and
    it read as exactly that.
    
    The rule is: GRASS IS LONG WHERE NOTHING CUTS IT. A boot wears the middle
    of a path and not its verge; nothing mows hard against a wall, a fence or
    a plinth. So long grass goes in continuous lines just outside the things
    that keep it short, and NOWHERE in the open field. That is both why a real
    field looks the way it does and why this now reads as deliberate.
    """
    rng = random.Random(seed)
    parts = []
    dense = _densify(points, 14)
    run = 0.0
    last = -1e9
    for index in range(len(dense) - 1):
        (ax, ay), (bx, by) = dense[index], dense[index + 1]
        step = math.hypot(bx - ax, by - ay)
        if step < 1e-6:
            continue
        run += step
        if run - last < spacing:
            continue
        last = run
        across = (-(by - ay) / step, (bx - ax) / step)
        for offset in offsets:
            x = ax + across[0] * offset + rng.uniform(-jitter, jitter)
            y = ay + across[1] * offset + rng.uniform(-jitter, jitter)
            ground = terrain_height(x, y)
            for _ in range(blades):
                # Blades lean AWAY from the thing they grow against: into the
                # light, which is also where there is room.
                swing = rng.uniform(-0.8, 0.8)
                lean = (across[0] * math.copysign(1, offset) * 0.42
                        + math.cos(swing) * 0.22,
                        across[1] * math.copysign(1, offset) * 0.42
                        + math.sin(swing) * 0.22)
                parts.append(_blade(
                    (x, y, ground), lean, height * rng.uniform(0.75, 1.3),
                    rng.uniform(0.038, 0.055), "f_grass",
                    seed + index * 13 + int(offset * 10)))
    return parts


def build_props():
    """Everything standing on the land: the way, the wall, hedges, the row.

    Deliberately NOT a scatter of decorative objects. Every item here is doing
    one of four jobs -- marking the way, enclosing the field, saying the place
    is cultivated, or hiding a contact line.
    """
    meshtools.reset_scene()
    parts = []
    rng = random.Random(17)

    # --- the way. Stones sunk into the hollow, not laid on the grass.
    stones = _densify(PATH, 3)
    for index in range(0, len(stones) - 4, 2):
        x, y = stones[index]
        x += rng.uniform(-0.12, 0.12)
        y += rng.uniform(-0.12, 0.12)
        size = rng.uniform(0.34, 0.52)
        stone = forms.superform(
            "PathStone", "e_stone", exponent=4.4, segments=12, rings=8,
            size=(size, size * rng.uniform(0.72, 0.95), 0.17),
            at=(x, y, terrain_height(x, y) - 0.015))
        forms.jitter_verts(stone, 0.010, seed=index)
        meshtools.paint_by_normal(stone, "e_stone_sun", "e_stone",
                                  "e_stone_deep", up_at=0.6, down_at=-0.3)
        parts.append(stone)

    # --- the wall. ⛔ Built from STONES, not from a swept band. The first
    # version ran two `ribbon` courses along the line, which is cheap and
    # correct in plan and rendered as a smooth white snake lying in the field:
    # a drystone wall is read entirely by the joints between its stones, and a
    # continuous surface has none. Individual stones cost about 2,400 extra
    # triangles and are the whole difference.
    # Fewer, bigger stones: at 7 samples per span the wall cost 10,400
    # triangles on its own and the stones were too small to read as stones
    # anyway. A drystone wall wants a dozen big ones per span, not fifty.
    wall_path = _densify(WALL, 4)
    for index in range(len(wall_path) - 1):
        x, y = wall_path[index]
        ground = terrain_height(x, y)
        nx, ny = wall_path[index + 1]
        length = math.hypot(nx - x, ny - y) or 1e-6
        across = (-(ny - y) / length, (nx - x) / length)
        for course, (lift, scale) in enumerate(((0.16, 1.00), (0.40, 0.92),
                                                (0.60, 0.80))):
            # Stagger alternate courses so no joint runs straight up the wall,
            # which is the one thing that would still say "extruded band".
            stagger = 0.16 if (index + course) % 2 else -0.16
            sx = x + across[0] * stagger * 0.4
            sy = y + across[1] * stagger * 0.4
            stone = forms.superform(
                "WallStone", "e_stone", exponent=3.0, segments=7, rings=5,
                size=(rng.uniform(0.40, 0.58) * scale,
                      rng.uniform(0.42, 0.58) * scale,
                      rng.uniform(0.20, 0.27)),
                at=(sx, sy, ground + lift))
            forms.jitter_verts(stone, 0.014, seed=40 + index * 3 + course)
            meshtools.paint_by_normal(stone, "e_stone_sun", "e_stone",
                                      "e_stone_deep", up_at=0.55,
                                      down_at=-0.30)
            parts.append(stone)


    # --- the hedge. Long, low, overlapping cushions: the same generator as
    # the tree canopy, squashed, which is why it belongs to the same world.
    for centre, radius, squash, lobes in (
            ((5.30, 3.90), 1.40, 0.40, 9),
            ((6.60, 2.40), 1.15, 0.42, 8),
            ((-5.40, 4.60), 1.55, 0.38, 10),
            ((-6.90, 3.10), 1.20, 0.44, 8)):
        x, y = centre
        # amount 0.15 made a smooth pillow. A hedge is read by its broken
        # top edge, so the lobes have to be deep enough to cut the silhouette.
        hedge = cushion("Hedge", "f_hedge", radius, 1.05,
                        (x, y, terrain_height(x, y) + 0.34),
                        lobes=lobes, amount=0.26, squash=squash,
                        twist=22, points=28)
        forms.jitter_verts(hedge, 0.022, seed=int(abs(x) * 17))
        meshtools.paint_by_normal(hedge, "f_hedge_sun", "f_hedge",
                                  "g_leaf_deep", up_at=0.55, down_at=-0.3)
        parts.append(hedge)

    # --- the vegetable row. ⛔ THE BED IS PAINTED INTO THE TERRAIN, not laid
    # on top of it. Two attempts at a `ribbon` of earth both rendered as a
    # wooden boardwalk with shrubs standing on it, because a strip of geometry
    # over grass has an EDGE and a dug bed does not. `build_terrain` paints
    # the earth into the ground itself; only the plants are objects.
    for index in range(7):
        x = BED[0] - 1.25 + index * 0.42
        plant = cushion("Crop", "f_hedge_sun", 0.20, 0.30,
                        (x, BED[1] + rng.uniform(-0.14, 0.14),
                         terrain_height(x, BED[1]) + 0.16),
                        lobes=6, amount=0.26, points=16, twist=24)
        meshtools.paint_by_normal(plant, "f_grass_sun", "f_hedge_sun",
                                  "f_hedge", up_at=0.5, down_at=-0.3)
        parts.append(plant)

    # --- grass, where nothing cuts it. Three continuous fringes and no
    # scatter at all: the verges of the worn way, the foot of the wall on
    # both sides, and the base of the cottage plinth.
    parts += _grass_fringe(PATH[:-2], (-0.92, 0.92), spacing=0.70,
                           height=0.21, seed=500)
    parts += _grass_fringe(WALL, (-0.52, 0.52), spacing=0.62, height=0.26,
                           seed=600)
    (cx, cy), _ = SCENE["cottage"]
    parts += _grass_fringe(
        [(cx - 1.95, cy - 1.80), (cx + 1.95, cy - 1.80),
         (cx + 1.95, cy + 1.80)], (0.22,), spacing=0.58, height=0.19,
        seed=700, jitter=0.09)

    # --- wildflowers, in CLUMPS. A field is not evenly sprinkled: flowers go
    # where the mower and the feet do not, so these cluster, and every clump
    # is rejected if it lands on the path or inside the garden fence.
    placed = 0
    attempt = 0
    while placed < 14 and attempt < 400:
        attempt += 1
        x = rng.uniform(-9.5, 9.5)
        y = rng.uniform(-8.5, 8.5)
        if path_distance(x, y) < 1.9:
            continue
        if (abs(x - BED[0]) < BED_HALF[0] + 0.8
                and abs(y - BED[1]) < BED_HALF[1] + 0.8):
            continue
        if math.hypot(x - SCENE["cottage"][0][0],
                      y - SCENE["cottage"][0][1]) < 3.2:
            continue
        if math.hypot(x - SCENE["tree"][0][0],
                      y - SCENE["tree"][0][1]) < 1.3:
            continue
        placed += 1
        for _ in range(rng.randint(3, 6)):
            fx = x + rng.uniform(-0.45, 0.45)
            fy = y + rng.uniform(-0.45, 0.45)
            ground = terrain_height(fx, fy)
            colour = rng.choice(("f_bloom", "f_bloom_sun", "f_bloom_pale"))
            # ⛔ Flat and SCALLOPED, sitting low in the grass. The first set
            # were domed pads on visible stems and read as a scatter of
            # toadstools across the meadow -- a flower head is a disc of
            # petals, so the dome goes nearly to nothing and the lobe
            # amplitude goes up until the petals are the silhouette.
            parts.append(forms.sweep(
                "Stem", "f_grass_deep",
                [(fx, fy, ground), (fx, fy, ground + 0.075)],
                [0.010, 0.008], segments=4))
            parts.append(forms.pad(
                "Wildflower", colour, radius=0.072, lobes=6, amplitude=0.46,
                dome=0.010, underside=0.008, points=12,
                at=(fx, fy, ground + 0.098),
                tilt=(rng.uniform(-20, 20), rng.uniform(-20, 20))))
            # Grass around every head, so they read as a flowering clump in
            # the sward rather than as objects standing on a lawn.
            if rng.random() < 0.6:
                parts += _tuft((fx + rng.uniform(-0.12, 0.12),
                                fy + rng.uniform(-0.12, 0.12), ground),
                               height=rng.uniform(0.12, 0.18), blades=2,
                               seed=400 + placed * 11 + int(fx * 7))

        parts += _tuft((x + rng.uniform(-0.5, 0.5),
                        y + rng.uniform(-0.5, 0.5),
                        terrain_height(x, y)), height=0.21,
                       seed=300 + placed)

    solid, grass = _split_flat_grass(parts, "props")
    props = meshtools.join(solid, "Props")
    meshtools.merge_doubles(props)
    return [props] + grass


# ------------------------------------------------------------- SMALLHOLDING
#
# "Does this look like the Shire?" was the test for the land. For the things
# standing ON it the test is narrower: does it look like somebody LIVES here
# and grows things. Every item below answers that and nothing else -- a fence
# encloses, a row is planted, a barrel catches water off a roof, a scarecrow
# is there because the crops are worth defending. None of it is scatter.

def _picket_fence(points, post_every=1.35, spacing=0.255, height=0.66):
    """Posts, two rails and pointed pickets along a drawn line.

    Low on purpose: 0.66 m against a 1.35 m Chuck. A fence that reaches his
    shoulder walls the garden off visually; one at his hip encloses it and
    still lets the rows read over the top, which is the whole point of
    putting a garden where the camera can see it.
    """
    parts = []
    dense = _densify(points, 24)
    # Walk the line by arc length so pickets are evenly spaced regardless of
    # how the corners were drawn.
    run, last_picket, last_post = 0.0, -1e9, -1e9
    for index in range(len(dense) - 1):
        (ax, ay), (bx, by) = dense[index], dense[index + 1]
        step = math.hypot(bx - ax, by - ay)
        if step < 1e-6:
            continue
        run += step
        along = ((bx - ax) / step, (by - ay) / step)
        turn = math.degrees(math.atan2(along[1], along[0]))
        ground = terrain_height(ax, ay)

        if run - last_post >= post_every:
            last_post = run
            post = forms.loft("Post", "w_rail", [
                (ground - 0.08, RR(0.115, 0.115, 0.016, 2)),
                (ground + height + 0.04, RR(0.105, 0.105, 0.015, 2)),
                (ground + height + 0.10, RR(0.072, 0.072, 0.012, 2)),
            ], at=(ax, ay, 0.0))
            _spin_z(post, turn, (ax, ay))
            parts.append(post)
        elif run - last_picket >= spacing:
            last_picket = run
            picket = forms.loft("Picket", "w_picket", [
                (ground - 0.05, RR(0.082, 0.028, 0.009, 2)),
                (ground + height - 0.11, RR(0.082, 0.028, 0.009, 2)),
                (ground + height - 0.03, RR(0.058, 0.028, 0.008, 2)),
                (ground + height, RR(0.014, 0.026, 0.006, 2)),
            ], at=(ax, ay, 0.0))
            _spin_z(picket, turn + 90.0, (ax, ay))
            meshtools.paint_by_normal(picket, "w_picket", "w_picket",
                                      "w_picket_sh", up_at=0.8, down_at=-0.4)
            parts.append(picket)

    for lift, width in ((0.19, 0.055), (0.46, 0.055)):
        rail = forms.ribbon(
            "Rail", "w_rail",
            [(x, y, terrain_height(x, y) + lift) for x, y in _densify(points, 6)],
            width, thickness=0.075)
        parts.append(rail)
    return parts


def _spin_z(obj, degrees, pivot):
    """Rotate an object about a WORLD pivot on Z.

    ⛔ It bakes the object transform first, and that is load-bearing. Every
    `forms` generator writes world coordinates straight into the mesh and
    leaves the object at the origin, so rotating raw `vert.co` about a world
    pivot is correct for those. `meshtools.torus` does NOT: it keeps its
    offset in `obj.location`. Spinning one of those about a pivot five
    metres away treats near-origin LOCAL coordinates as if they were world
    ones and flings the object five metres the opposite way.

    That is exactly what happened to the mill mound's cellar-door ring,
    which ended up 5 m underground and took the whole asset's bounding box
    with it -- it reported base_z = -4.995 while every render looked fine,
    because the thing that moved was far too small to notice.
    """
    from mathutils import Matrix
    bpy.context.view_layer.update()
    if obj.matrix_world != Matrix.Identity(4):
        world = obj.matrix_world.copy()
        for vert in obj.data.vertices:
            vert.co = world @ vert.co
        obj.matrix_world = Matrix.Identity(4)
    rad = math.radians(degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    for vert in obj.data.vertices:
        x = vert.co.x - pivot[0]
        y = vert.co.y - pivot[1]
        vert.co.x = pivot[0] + x * cos_a - y * sin_a
        vert.co.y = pivot[1] + x * sin_a + y * cos_a


def _barrel(at, scale=1.0, planted=True, seed=0):
    """A rain barrel: a lathed stave silhouette with painted iron hoops.

    The hoops are PAINTED, not modelled. `repaint_faces` stamps whole faces,
    which is usually the trap -- here it is the feature: the profile carries
    two deliberately short steps, so a height test paints exactly those rings
    and an iron band costs nothing at all.
    """
    parts = []
    ground = terrain_height(at[0], at[1])
    # radius, z -- bulged at the waist, drawn in at both ends, with a rim and
    # a recessed top so the barrel reads as OPEN.
    profile = [(0.000, 0.00), (0.250, 0.00),
               (0.278, 0.085), (0.288, 0.125),          # lower hoop step
               (0.300, 0.175), (0.300, 0.330),
               (0.288, 0.380), (0.278, 0.420),          # upper hoop step
               (0.248, 0.520), (0.232, 0.545),
               (0.214, 0.512), (0.000, 0.500)]
    profile = [(r * scale, z * scale) for r, z in profile]
    barrel = forms.lathe("Barrel", "w_barrel", profile, segments=16,
                         at=(at[0], at[1], ground))
    meshtools.paint_by_normal(barrel, "w_barrel_sun", "w_barrel",
                              "w_wood_shade" if False else "w_barrel",
                              up_at=0.75, down_at=-0.4)
    for low, high in ((0.085, 0.125), (0.380, 0.420)):
        meshtools.repaint_faces(
            barrel,
            lambda c, n, lo=ground + low * scale, hi=ground + high * scale:
                lo - 0.004 <= c.z <= hi + 0.004,
            "w_iron")
    forms.jitter_verts(barrel, 0.004, seed=seed)
    parts.append(barrel)

    # The water, a disc just below the rim. Dark and flat: it is the only
    # thing in the palette below the ink, so a barrel reads as full.
    parts.append(forms.lathe("Water", "w_water",
                             [(0.0, 0.0), (0.205 * scale, 0.0)], segments=16,
                             at=(at[0], at[1], ground + 0.492 * scale)))

    if planted:
        parts += _barrel_flowers(at, ground, scale, seed + 5)
    return parts


def _flower(at, petal, centre, size=1.0, tilt=(0.0, 0.0), stem=0.0):
    """A flower that is unmistakably a flower: petals, a centre, a stem.

    ⛔ The first barrels held a green cushion with five small coloured
    cushions sitting in it, and at every size that matters they read as a
    leafy blob with pink lumps on top. A cushion is a MASS; a flower head is
    a disc of petals with a different-coloured middle, and it only reads if
    all three of those are present and the head clears the foliage.
    """
    parts = []
    if stem > 0.0:
        parts.append(forms.sweep(
            "Stem", "f_crop_deep",
            [(at[0], at[1], at[2] - stem), (at[0], at[1], at[2] - 0.012)],
            [0.014 * size, 0.011 * size], segments=5))
    parts.append(forms.pad("Petals", petal, radius=0.092 * size, lobes=6,
                           amplitude=0.40, dome=0.016 * size,
                           underside=0.012 * size, points=18, at=at,
                           tilt=tilt))
    parts.append(forms.superform(
        "Eye", centre, size=(0.036 * size, 0.036 * size, 0.026 * size),
        exponent=2.4, segments=9, rings=7,
        at=(at[0], at[1], at[2] + 0.016 * size)))
    return parts


def _barrel_flowers(at, ground, scale, seed):
    """Foliage low in the barrel, flower heads standing clear above it."""
    rng = random.Random(seed)
    parts = []
    skirt = cushion("Spill", "f_crop", 0.23 * scale, 0.20 * scale,
                    (at[0], at[1], ground + 0.555 * scale),
                    lobes=7, amount=0.30, points=16, twist=26)
    meshtools.paint_by_normal(skirt, "f_crop", "f_crop", "f_crop_deep",
                              up_at=0.5, down_at=-0.3)
    parts.append(skirt)
    pairs = (("f_bloom", "f_bloom_sun"), ("f_bloom_sun", "w_cloth"),
             ("f_bloom_pale", "f_bloom"), ("f_bloom", "f_bloom_pale"),
             ("f_bloom_sun", "f_bloom"))
    for index, (petal, centre) in enumerate(pairs):
        angle = math.tau * index / len(pairs) + rng.uniform(-0.25, 0.25)
        reach = rng.uniform(0.07, 0.19) * scale
        lift = rng.uniform(0.70, 0.86) * scale
        parts += _flower(
            (at[0] + math.cos(angle) * reach,
             at[1] + math.sin(angle) * reach, ground + lift),
            petal, centre, size=scale * rng.uniform(0.92, 1.12),
            tilt=(rng.uniform(-26, 26), rng.uniform(-26, 26)),
            stem=lift - 0.52 * scale)
    return parts


def _scarecrow(at, facing=-30.0):
    """Post, cross-arm, stuffed shirt, sack head, ragged hat, straw cuffs.

    1.62 m, which is deliberately taller than Chuck's 1.35: a scarecrow that
    does not stand over the crops is a doll. It is the one figure in the
    scene besides Chuck, so its silhouette has to be read-at-a-glance
    different from his -- hence arms out straight and a slumped sack head
    where his are down and his head is round.
    """
    parts = []
    ground = terrain_height(at[0], at[1])
    x, y = at

    post = forms.sweep("Post", "s_wood", [(x, y, ground - 0.05),
                                          (x, y, ground + 1.34)],
                       [0.060, 0.046], segments=7, profile_squash=0.9)
    meshtools.paint_by_normal(post, "s_wood", "s_wood", "s_wood_deep",
                              up_at=0.7, down_at=-0.4)
    parts.append(post)
    arm = forms.sweep("Arm", "s_wood",
                      [(x - 0.46, y + 0.04, ground + 1.00),
                       (x + 0.46, y - 0.04, ground + 0.97)],
                      [0.046, 0.044], segments=6, profile_squash=0.9)
    parts.append(arm)

    body = forms.loft("Shirt", "w_cloth", [
        (ground + 0.56, RR(0.30, 0.22, 0.07, 4)),
        (ground + 0.74, RR(0.40, 0.28, 0.10, 4)),
        (ground + 0.96, RR(0.46, 0.32, 0.12, 4)),
        (ground + 1.08, RR(0.38, 0.27, 0.10, 4)),
    ], at=(x, y, 0.0))
    meshtools.wobble(body, amount=0.014, scale=4.0, seed=9)
    meshtools.paint_by_normal(body, "w_cloth", "w_cloth", "h_vest_deep",
                              up_at=0.8, down_at=-0.45)
    parts.append(body)
    for side in (-1, 1):
        parts.append(forms.sweep(
            "Sleeve", "w_cloth",
            [(x + side * 0.18, y, ground + 0.99),
             (x + side * 0.40, y + 0.02, ground + 0.985)],
            [0.105, 0.082], segments=8, profile_squash=0.9))
        # Straw bursting out of the cuffs, which is the detail that says
        # STUFFED rather than dressed.
        for blade in range(3):
            angle = math.tau * blade / 3 + side
            parts.append(forms.sweep(
                "Cuff", "h_straw",
                [(x + side * 0.42, y, ground + 0.98),
                 (x + side * 0.56 + math.cos(angle) * 0.04,
                  y + math.sin(angle) * 0.05,
                  ground + 0.96 + math.sin(angle) * 0.05)],
                [0.022, 0.004], segments=5))
    for blade in range(4):
        angle = math.tau * blade / 4 + 0.4
        parts.append(forms.sweep(
            "Hem", "h_straw",
            [(x + math.cos(angle) * 0.10, y + math.sin(angle) * 0.08,
              ground + 0.60),
             (x + math.cos(angle) * 0.20, y + math.sin(angle) * 0.16,
              ground + 0.44)],
            [0.026, 0.004], segments=5))

    head = forms.superform("Head", "w_sack", size=(0.34, 0.31, 0.35),
                           exponent=2.6, segments=16, rings=12,
                           at=(x + 0.03, y - 0.01, ground + 1.27))
    # ⛔ `press` works on a WORLD plane. Passing -0.13 pressed the face toward
    # world y = -0.13 rather than toward the head's own front, so a scarecrow
    # standing anywhere but x = y = 0 had its face flattened off-axis -- which
    # is what turned the sack head into a cone.
    forms.press(head, "Y", plane=y - 0.145, amount=0.30, radius=0.21,
                centre=(x, y - 0.19, ground + 1.27))
    rotate_x(head, 9.0, pivot=(0.0, y, ground + 1.16))   # a slumped head
    parts.append(head)
    # A tied neck: the twist of twine under the sack head.
    parts.append(forms.lathe("Tie", "h_straw",
                             [(0.0, 0.0), (0.075, 0.0), (0.082, 0.045),
                              (0.060, 0.070), (0.0, 0.066)],
                             segments=10, at=(x + 0.02, y, ground + 1.09)))
    for side in (-1, 1):
        parts.append(forms.superform(
            "Eye", "s_ink", size=(0.068, 0.034, 0.068), exponent=2.2,
            segments=10, rings=8,
            at=(x + 0.03 + side * 0.072, y - 0.163, ground + 1.31)))
    parts.append(forms.sweep(
        "Stitch", "s_ink",
        [(x - 0.048, y - 0.155, ground + 1.21),
         (x + 0.03, y - 0.166, ground + 1.195),
         (x + 0.108, y - 0.155, ground + 1.21)],
        [0.013, 0.016, 0.013], segments=6, samples=4, profile_squash=0.6))

    hat = forms.lathe("Hat", "h_straw_deep", [
        (0.000, 0.108), (0.070, 0.102), (0.118, 0.074),
        (0.146, 0.026), (0.152, 0.004),
        (0.214, -0.014), (0.268, -0.026), (0.282, -0.006),
    ], segments=14, at=(x + 0.03, y + 0.01, ground + 1.34))
    meshtools.wobble(hat, amount=0.014, scale=6.0, seed=3)   # battered
    rotate_x(hat, -14.0, pivot=(0.0, y, ground + 1.34))
    parts.append(hat)

    for part in parts:
        _spin_z(part, facing, (x, y))
    return parts


def _crop_row(y_pos, x_from, x_to, count, kind, seed):
    """One planted row, LOW and dead straight.

    ⛔ The first garden put big round cabbage cushions down the middle and it
    dominated everything -- the rows stopped reading as rows and became a
    hedge. Two changes fix it and both are about restraint: nothing but the
    bean frame now stands over 0.26 m, and there is BARE EARTH visible
    between every row. A row is read from the gaps as much as the plants.

    The spacing is also exactly even and the line is exactly straight. A
    kitchen garden is the one place in this whole scene that is allowed to be
    regular -- it is the only thing a person measured out.
    """
    rng = random.Random(seed)
    parts = []
    for index in range(count):
        t = index / max(count - 1, 1)
        x = x_from + (x_to - x_from) * t
        ground = terrain_height(x, y_pos)

        if kind == "carrot":
            # The shoulder of the root, just breaking the soil. It is two
            # centimetres of orange and it is the entire reason anyone can
            # tell what the row is.
            shoulder = forms.superform(
                "Carrot", "c_carrot", size=(0.085, 0.085, 0.075),
                exponent=2.3, segments=9, rings=7,
                at=(x, y_pos, ground + 0.012))
            parts.append(shoulder)
            for frond in range(5):
                angle = math.tau * frond / 5 + rng.uniform(-0.3, 0.3)
                out = rng.uniform(0.045, 0.085)
                parts.append(_blade(
                    (x, y_pos, ground + 0.03),
                    (math.cos(angle) * out * 4.0, math.sin(angle) * out * 4.0),
                    rng.uniform(0.13, 0.19), 0.030, "f_crop",
                    seed + index * 7 + frond))

        elif kind == "onion":
            parts.append(forms.superform(
                "Bulb", "f_crop_pale", size=(0.105, 0.105, 0.070),
                exponent=2.4, segments=10, rings=7,
                at=(x, y_pos, ground + 0.028)))
            for strap in range(4):
                angle = math.tau * strap / 4 + rng.uniform(-0.2, 0.2)
                parts.append(_blade(
                    (x, y_pos, ground + 0.05),
                    (math.cos(angle) * 0.26, math.sin(angle) * 0.26),
                    rng.uniform(0.17, 0.24), 0.034, "f_crop",
                    seed + 40 + index * 5 + strap))

        else:   # a few small cabbages, at the BACK and half the old size
            plant = cushion("Cabbage", "f_crop", rng.uniform(0.125, 0.155),
                            0.19, (x, y_pos + rng.uniform(-0.04, 0.04),
                                   ground + 0.085),
                            lobes=7, amount=0.30, points=12, twist=30)
            meshtools.paint_by_normal(plant, "f_crop_pale", "f_crop",
                                      "f_crop_deep", up_at=0.5, down_at=-0.3)
            parts.append(plant)
    return parts


def _bean_frame(y_pos, x_from, x_to, pairs=3):
    """Crossed poles with a ridge, and beans climbing them.

    The tallest thing in the garden and the only diagonal in the whole scene,
    which is exactly why it is here: everything else is upright or lying down.
    """
    parts = []
    top = []
    for index in range(pairs):
        t = index / max(pairs - 1, 1)
        x = x_from + (x_to - x_from) * t
        ground = terrain_height(x, y_pos)
        apex = (x, y_pos, ground + 1.12)
        top.append(apex)
        for side in (-1, 1):
            foot = (x, y_pos + side * 0.40, terrain_height(x, y_pos + side * 0.40))
            parts.append(forms.sweep("Pole", "s_wood",
                                     [foot, apex], [0.030, 0.022], segments=5))
            for step in range(3):
                k = 0.22 + step * 0.26
                parts.append(cushion(
                    "Bean", "f_crop", 0.115 - step * 0.012, 0.14,
                    (x + (0.03 if step % 2 else -0.03),
                     foot[1] + (apex[1] - foot[1]) * k,
                     foot[2] + (apex[2] - foot[2]) * k),
                    lobes=5, amount=0.30, points=9, twist=24))
    # 0.022 rendered as a dark WIRE strung between the poles. A ridge pole is
    # the same stick as the legs, so it gets the same radius.
    parts.append(forms.sweep("Ridge", "s_wood", [top[0], top[-1]],
                             [0.032, 0.032], segments=6))
    return parts


def build_garden():
    """The smallholding: fence, rows, bean frame, scarecrow, barrels.

    A second asset rather than more of `props` for a texture reason, not an
    organisational one. `atlas_unwrap` packs everything into ONE 1024 sheet by
    surface area, so folding a garden into the props atlas would halve the
    texel density of the wall and the path stones along with it.
    """
    meshtools.reset_scene()
    parts = []
    gx, gy = BED
    hx, hy = BED_HALF

    # The enclosure, with a gap at the front-left for a gateway onto the path.
    parts += _picket_fence([
        (gx - hx, gy - hy + 0.55), (gx - hx, gy + hy), (gx + hx, gy + hy),
        (gx + hx, gy - hy), (gx - hx + 0.95, gy - hy),
    ])
    # ⛔ A second, shorter run beside the cottage -- and it has to stay EAST
    # of the way. Drawn first as a dogleg down to (-2.05, 0.08) it ran
    # straight across the path stones outside the front door, fencing Chuck
    # out of his own house.
    parts += _picket_fence([(-1.12, 1.62), (-1.12, 0.34), (-0.52, -0.34)])

    # Front to back, low to tall, with bare earth between every one.
    parts += _crop_row(gy - 0.88, gx - 1.28, gx + 1.24, 11, "carrot", 11)
    parts += _crop_row(gy - 0.30, gx - 1.28, gx + 1.24, 9, "onion", 12)
    parts += _crop_row(gy + 0.28, gx - 1.10, gx + 1.10, 6, "cabbage", 13)
    parts += _bean_frame(gy + 1.02, gx - 1.05, gx + 0.70, pairs=3)

    # ⛔ Not at the far corner. There it stood behind the tree canopy from the
    # gameplay camera and was completely hidden -- the one figure in the scene
    # besides Chuck, invisible. Back-LEFT of the garden puts it clear of both
    # the tree and the cottage, and it still looks over the rows.
    # ⛔ Third siting. Behind the tree it vanished; against the cottage wall
    # it merged with the plaster. Left of centre and forward of the bean
    # frame puts open grass behind it from the gameplay camera, which is the
    # only place a 1.62 m figure reads.
    parts += _scarecrow((gx - 0.78, gy + 0.26), facing=-24.0)
    # One barrel under the cottage eave where the water would actually come
    # off, one inside the garden gate where it would actually be used.
    parts += _barrel((-1.02, 1.74), scale=1.0, seed=2)
    parts += _barrel((gx - hx + 0.34, gy - hy + 0.30), scale=0.86, seed=7)

    solid, tops = _split_flat_grass(parts, "garden")
    garden = meshtools.join(solid, "Garden")
    meshtools.merge_doubles(garden)
    return [garden] + tops


# -------------------------------------------------------------------- run

SUBJECTS = {
    "chuck": lambda: produce("chuck", build_chuck(), budget_tris=6500,
                             with_animation=True,
                             animation_names=["idle", "walk"]),
    "tree": lambda: produce("tree", build_tree(), budget_tris=6500),
    "cottage": lambda: produce("cottage", build_cottage(), budget_tris=7000),
    "block": lambda: produce("block", build_block(), texture=512,
                             budget_tris=4000, bake_samples=28),
    "terrain": lambda: produce("terrain", build_terrain(), budget_tris=18000,
                               texture=asset.TEXTURE_MEDIUM,
                               surface=TERRAIN_SURFACE, bake_samples=20),
    "props": lambda: produce("props", build_props(), budget_tris=24000),
    "garden": lambda: produce("garden", build_garden(), budget_tris=22000),
}


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    wanted = [a for a in args if a in SUBJECTS] or list(SUBJECTS)
    for name in wanted:
        print("[foundation] building", name)
        SUBJECTS[name]()
