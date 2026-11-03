"""Phoneme Village, rebuilt in the foundation language.

    blender --background --python art_src/explore/village.py
    blender --background --python art_src/explore/village.py -- windmill bakery

⛔ THE VILLAGE IS THE PUREST CASE OF THE PROBLEM PHASE 1 WAS REJECTED FOR.
Every one of its six buildings is `assets/toy_village/beveled_cube.obj`,
instanced over and over with flat colour materials -- a windmill, a bakery and
a clock tower all made of the same box. That is the asset-pack vocabulary in
its most literal form, and no amount of retexturing touches it. Each building
here is rebuilt out of `sb_lib/forms`: a lathed mill tower, a lofted jettied
bookshop, swept sails, roofs made of real tile COURSES.

The six identities are kept exactly -- windmill, bakery, clock house,
bookshop, flower shop, workshop -- because a child learns the village by them
and they are how he describes the place.

Palette, bake recipe and shading language are imported from `foundation`
rather than restated, which is what stops the village reading as a second
game pinned to the side of the first.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common  # noqa: E402,F401
from sb_lib import asset, forms, meshtools, painter, palette, rig  # noqa: E402

import foundation as F  # noqa: E402

RR = forms.rounded_rect
D = "village"

# Scale reference. The foundation cottage is 3.95 m to its ridge and Chuck is
# 1.35 m; every building here is authored against those two numbers so the
# village and the home field are one world at one size.
DOOR_H = 1.62


# ----------------------------------------------------------------- palette

palette.extend({
    "v_mill":       ("#D8C8A8", 0.72, "mill tower limewash"),
    "v_mill_shade": ("#B3A384", 0.56, "mill tower in shade"),
    "v_sail":       ("#C8B48C", 0.66, "sail canvas"),
    "v_slate":      ("#6E7276", 0.37, "slate cap, clock face surround"),
    "v_slate_sun":  ("#8A8E92", 0.50, "a slate catching light"),
    "v_brick":      ("#B06A52", 0.42, "the bakery's oven brick"),
    "v_brick_deep": ("#84452F", 0.27, "brick in the arch"),
    "v_green":      ("#3F6B55", 0.33, "shopfront paint, bookshop"),
    "v_plum":       ("#7B4A63", 0.31, "shopfront paint, flower shop"),
    "v_teal":       ("#3A6E78", 0.35, "shopfront paint, workshop"),
    "v_gold":       ("#D9A441", 0.62, "signwriting, clock hands, weathervane"),
    "v_awning":     ("#C65B4A", 0.40, "the striped awning"),
    "v_awning_alt": ("#EFE3C8", 0.84, "the awning's other stripe"),
    "v_clock":      ("#F2E7CE", 0.88, "the clock dial"),
    # ⛔ A village of six cream buildings is one building six times. Each
    # trade gets its own render, which is also how a real street works --
    # the limewash a shop can afford is part of what it is.
    "v_ochre":      ("#D9BD86", 0.69, "the bakery, warm from the oven"),
    "v_ochre_sh":   ("#B2975F", 0.52, "ochre in shade"),
    "v_sage":       ("#C6CAB0", 0.73, "the bookshop, cool and faded"),
    "v_sage_sh":    ("#A0A58A", 0.57, "sage in shade"),
    "v_rose":       ("#DFC3B2", 0.72, "the flower shop"),
    "v_rose_sh":    ("#B99A88", 0.56, "rose in shade"),
    "v_hair":       ("#6B6158", 0.33, "Annette's hair -- grey, but WARM"),
    "v_hair_sun":   ("#8B7E71", 0.46, "her hair, lit"),
    "v_brass":      ("#8A6A32", 0.36, "spectacle rims -- brass, not gold"),
})


SMOOTH = 11.0


def produce(subject, objects, texture=asset.TEXTURE_MEDIUM, budget_tris=None):
    return asset.produce("village/%s" % subject, objects, texture=texture,
                         roughness=0.93, budget_tris=budget_tris,
                         bake_samples=24, smooth_angle=SMOOTH,
                         gouache=F.SURFACE)


# ----------------------------------------------------------------- helpers

def tiled_roof(name, colour, courses, pts=7, lip=0.052, scallop=0.040,
               at=(0.0, 0.0, 0.0), sun="t_tile_sun", deep="t_tile_deep"):
    """Terracotta pantiles as real COURSES, the cottage's recipe reused.

    Each course emits two loft stations -- its own plan, then the same plan
    lifted by the lap -- so there is a riser and a shadow line all the way
    round at every course. The eave course is scalloped into pantile ends.

    ⛔ Keep the corner radius TINY and the depth nearly constant. Shrinking
    width and depth together, with lozenge-shaped stations, makes a dome and
    not a roof. That cost the cottage a whole build.
    """
    stations = []
    for index, (z, width, depth, corner, dx) in enumerate(courses):
        outline = RR(width, depth, corner, pts)
        if index == 0 and scallop:
            outline = F.wavy(outline, lobes=pts, amount=scallop)
        outline = F.shift(outline, dx)
        stations.append((z, outline))
        if index < len(courses) - 1:
            stations.append((z + lip, outline))
    roof = forms.loft(name, colour, stations, close_bottom=False, at=at)
    meshtools.paint_by_normal(roof, sun, colour, deep, up_at=0.70,
                              down_at=-0.15)
    return roof


def plinth(name, width, depth, height=0.30, at=(0.0, 0.0, 0.0)):
    """A stone footing. A building that meets grass in plaster looks dropped."""
    block = forms.loft(name, "e_stone", [
        (0.00, RR(width + 0.16, depth + 0.16, 0.14, 5)),
        (height, RR(width + 0.09, depth + 0.09, 0.13, 5)),
        (height + 0.05, RR(width - 0.04, depth - 0.04, 0.12, 5)),
    ], at=at)
    meshtools.paint_by_normal(block, "e_stone_sun", "e_stone", "e_stone_deep",
                              up_at=0.8, down_at=-0.4)
    return block


def casement(x, z, width, height, face_y, colour="s_cream", depth=0.14):
    """A framed window with glazing bars and a stone lintel and sill.

    Without the bars a window is a dark rectangle, which reads as a hole
    punched in a wall rather than as glass.
    """
    parts = []
    parts.append(forms.loft("WinFrame", colour, [
        (z - height / 2, RR(width, depth, 0.04, 4)),
        (z + height / 2, RR(width, depth, 0.04, 4)),
    ], at=(x, face_y, 0.0)))
    parts.append(forms.loft("Pane", "s_wood_deep", [
        (z - height / 2 + 0.09, RR(width - 0.17, depth * 0.55, 0.03, 4)),
        (z + height / 2 - 0.09, RR(width - 0.17, depth * 0.55, 0.03, 4)),
    ], at=(x, face_y - 0.05, 0.0)))
    parts.append(forms.sweep("BarV", colour,
                             [(x, face_y - 0.10, z - height / 2 + 0.08),
                              (x, face_y - 0.10, z + height / 2 - 0.08)],
                             [0.019, 0.019], segments=5, profile_squash=0.5))
    parts.append(forms.sweep("BarH", colour,
                             [(x - width * 0.42, face_y - 0.10, z),
                              (x + width * 0.42, face_y - 0.10, z)],
                             [0.019, 0.019], segments=5, profile_squash=0.5))
    for offset, thickness in ((height * 0.56, 0.11), (-height * 0.60, 0.13)):
        parts.append(forms.loft("Lintel", "e_stone", [
            (z + offset, RR(width + 0.24, depth + 0.08, 0.05, 4)),
            (z + offset + thickness, RR(width + 0.24, depth + 0.08, 0.05, 4)),
        ], at=(x, face_y, 0.0)))
    return parts


def arched_door(x, face_y, width=0.82, height=DOOR_H, colour="s_blue",
                knob="s_accent"):
    """A round-headed door. The one shape allowed to be perfectly drawn."""
    parts = []
    jamb = 0.22
    springing = height - 0.42
    arch = [(0.0, 1.0), (springing, 1.0), (springing + 0.13, 0.985),
            (springing + 0.24, 0.94), (springing + 0.33, 0.86),
            (springing + 0.39, 0.74)]
    parts.append(forms.loft("Door", colour,
                            [(z, RR(width * f, jamb, 0.05, 4)) for z, f in arch]
                            + [(height, RR(width * 0.30, jamb, 0.04, 4))],
                            at=(x, face_y - 0.065, 0.0)))
    surround = [(z, RR((width + 0.16) * f, jamb * 0.74, 0.05, 4))
                for z, f in arch] + \
               [(height + 0.10, RR((width + 0.16) * 0.28, jamb * 0.74, 0.04, 4))]
    parts.append(forms.loft("DoorArch", "e_stone", surround,
                            at=(x, face_y + 0.010, 0.0)))
    parts.append(forms.superform("Knob", knob, size=(0.09, 0.09, 0.09),
                                 exponent=2.7, segments=11, rings=9,
                                 at=(x, face_y - 0.175, height * 0.50)))
    for step_z, size in ((0.0, (1.30, 0.80)), (0.085, (1.14, 0.66))):
        parts.append(forms.loft("Step", "e_stone", [
            (step_z, RR(size[0], size[1], 0.09, 4)),
            (step_z + 0.09, RR(size[0] - 0.10, size[1] - 0.08, 0.08, 4)),
        ], at=(x, face_y - 0.42, 0.0)))
    return parts


def awning(name, x, face_y, width, z, colour="v_awning",
           alt="v_awning_alt", stripes=7, reach=0.78):
    """A striped shop awning: a ribbon with a scalloped valance.

    Stripes are PAINTED per face on a subdivided slope, not modelled -- an
    awning is the one place in the village where a flat repeating pattern is
    the correct answer and geometry would be silly.
    """
    parts = []
    slope = forms.loft(name, colour, [
        (z, RR(width, 0.06, 0.02, 3)),
        (z - 0.34, RR(width, 0.06, 0.02, 3)),
    ], at=(x, face_y - reach / 2, 0.0), close_bottom=False, close_top=False)
    meshtools.subdivide(slope, levels=3, smooth=False)
    step = width / float(stripes)

    def striped(centre, _normal):
        index = int(math.floor((centre.x - x + width / 2) / step))
        return index % 2 == 1

    meshtools.repaint_faces(slope, striped, alt)
    parts.append(slope)
    # The valance: a scalloped lip along the front edge, which is what makes
    # a canopy read as cloth rather than as a wedge of plywood.
    valance = forms.loft(name + "Valance", colour, [
        (z - 0.34, F.wavy(RR(width, 0.07, 0.02, 9), lobes=stripes,
                          amount=0.0)),
        (z - 0.46, F.wavy(RR(width, 0.07, 0.02, 9), lobes=stripes,
                          amount=0.055)),
    ], at=(x, face_y - reach, 0.0), close_bottom=False)
    meshtools.repaint_faces(valance, striped, alt)
    parts.append(valance)
    for side in (-1, 1):
        parts.append(forms.sweep(
            "AwningStay", "s_wood_deep",
            [(x + side * width * 0.46, face_y, z),
             (x + side * width * 0.46, face_y - reach, z - 0.44)],
            [0.030, 0.026], segments=6))
    return parts


def sign(name, x, face_y, z, colour, width=0.86):
    """A hanging shop sign on a bracket. Every shop in the village has one."""
    parts = []
    parts.append(forms.sweep("Bracket", "s_wood_deep",
                             [(x, face_y, z + 0.30),
                              (x, face_y - 0.52, z + 0.30)],
                             [0.034, 0.028], segments=6))
    for side in (-1, 1):
        parts.append(forms.sweep("Hanger", "w_iron",
                                 [(x + side * width * 0.32, face_y - 0.46,
                                   z + 0.28),
                                  (x + side * width * 0.32, face_y - 0.46,
                                   z + 0.06)],
                                 [0.013, 0.013], segments=5))
    board = forms.loft(name, colour, [
        (z - 0.34, RR(width, 0.08, 0.05, 4)),
        (z + 0.08, RR(width, 0.08, 0.05, 4)),
    ], at=(x, face_y - 0.46, 0.0))
    parts.append(board)
    parts.append(forms.loft(name + "Edge", "v_gold", [
        (z - 0.30, RR(width - 0.10, 0.10, 0.04, 4)),
        (z + 0.04, RR(width - 0.10, 0.10, 0.04, 4)),
    ], at=(x, face_y - 0.465, 0.0)))
    return parts


# --------------------------------------------------------------- WINDMILL
#
# The one building in the village that is genuinely a SOLID OF REVOLUTION, and
# the clearest case of why `lathe` exists: a tapered round tower drawn as a
# silhouette is six numbers, and is flatly impossible out of a beveled cube.

def build_windmill():
    meshtools.reset_scene()
    parts = []
    parts.append(plinth("Plinth", 2.55, 2.55, 0.34))

    # radius, z -- battered at the foot, pinched under the gallery, flaring
    # again to carry the cap.
    tower = forms.lathe("Tower", "v_mill", [
        (0.000, 0.30), (1.320, 0.30), (1.240, 0.95), (1.150, 1.75),
        (1.080, 2.60), (1.055, 3.30), (1.125, 3.42), (1.105, 3.58),
        (1.020, 3.72), (0.980, 4.30), (0.000, 4.34),
    ], segments=22, smooth_profile=0)
    meshtools.paint_by_normal(tower, "v_mill", "v_mill", "v_mill_shade",
                              up_at=0.8, down_at=-0.45)
    meshtools.wobble(tower, amount=0.016, scale=2.4, seed=5)
    parts.append(tower)

    # The gallery: a walkway with a rail, which is the detail that gives a
    # mill its scale and tells you a person works up there.
    parts.append(forms.lathe("Gallery", "s_wood", [
        (1.020, 3.40), (1.400, 3.40), (1.400, 3.48), (1.020, 3.48),
    ], segments=22))
    for step in range(16):
        angle = math.tau * step / 16
        parts.append(forms.sweep(
            "Rail", "s_wood_deep",
            [(math.cos(angle) * 1.33, math.sin(angle) * 1.33, 3.48),
             (math.cos(angle) * 1.33, math.sin(angle) * 1.33, 3.86)],
            [0.030, 0.026], segments=5))
    parts.append(forms.lathe("RailTop", "s_wood_deep", [
        (1.280, 3.86), (1.380, 3.86), (1.380, 3.94), (1.280, 3.94),
    ], segments=22))

    # A slate cap, lathed, with a weathervane. Not a cone: the profile bulges.
    cap = forms.lathe("Cap", "v_slate", [
        (0.000, 5.46), (0.250, 5.36), (0.560, 5.05), (0.790, 4.62),
        (0.930, 4.30), (1.010, 4.18), (0.980, 4.10), (0.000, 4.12),
    ], segments=22, smooth_profile=0)
    meshtools.paint_by_normal(cap, "v_slate_sun", "v_slate", "s_wood_deep",
                              up_at=0.55, down_at=-0.3)
    parts.append(cap)
    parts.append(forms.sweep("Vane", "v_gold", [(0, 0, 5.44), (0, 0, 5.92)],
                             [0.028, 0.020], segments=6))
    parts.append(forms.ribbon("VaneFlag", "v_gold",
                              [(0.02, 0, 5.80), (0.34, 0, 5.84)], 0.22,
                              thickness=0.025))

    # FOUR SAILS on a hub. Each is a swept spar carrying a lattice of bars and
    # a canvas ribbon down one side only, which is what a real sail looks like
    # and what makes the cross read as machinery rather than as a plus sign.
    hub_y = -1.05
    parts.append(forms.lathe("Hub", "s_wood_deep", [
        (0.000, 0.00), (0.200, 0.00), (0.215, -0.26), (0.000, -0.30),
    ], segments=12, at=(0, hub_y, 4.55)))
    for blade in range(4):
        angle = math.tau * blade / 4 + math.radians(18.0)
        tip = (math.cos(angle) * 2.32, 0.0, math.sin(angle) * 2.32)
        spar = forms.sweep(
            "Spar", "s_wood",
            [(math.cos(angle) * 0.18, hub_y - 0.16,
              4.55 + math.sin(angle) * 0.18),
             (tip[0], hub_y - 0.22, 4.55 + tip[2])],
            [0.062, 0.034], segments=6)
        parts.append(spar)
        for rung in range(1, 6):
            k = rung / 6.0
            across = (-math.sin(angle), math.cos(angle) * 0.0, math.cos(angle))
            cx = math.cos(angle) * 2.32 * k
            cz = math.sin(angle) * 2.32 * k
            parts.append(forms.sweep(
                "Bar", "s_wood_deep",
                [(cx - across[0] * 0.05, hub_y - 0.22, 4.55 + cz - across[2] * 0.05),
                 (cx + across[0] * 0.40, hub_y - 0.22, 4.55 + cz + across[2] * 0.40)],
                [0.020, 0.016], segments=4))
        canvas = forms.ribbon(
            "Canvas", "v_sail",
            [(math.cos(angle) * 0.42 + -math.sin(angle) * 0.20, hub_y - 0.25,
              4.55 + math.sin(angle) * 0.42 + math.cos(angle) * 0.20),
             (math.cos(angle) * 2.10 + -math.sin(angle) * 0.20, hub_y - 0.25,
              4.55 + math.sin(angle) * 2.10 + math.cos(angle) * 0.20)],
            0.34, thickness=0.022)
        parts.append(canvas)

    parts += arched_door(0.0, -1.22, width=0.80, colour="v_teal")
    parts += casement(-0.78, 2.15, 0.56, 0.72, -0.98, depth=0.13)
    parts += casement(0.78, 2.15, 0.56, 0.72, -0.98, depth=0.13)
    parts += casement(0.0, 1.30, 0.56, 0.68, -1.14, depth=0.13)

    mill = meshtools.join(parts, "Windmill")
    meshtools.merge_doubles(mill)
    forms.facet(mill, angle=9.0)
    meshtools.drop_to_floor(mill)
    return [mill]


# ----------------------------------------------------------------- BAKERY
#
# Read from the OVEN. A bakery is a fire in a brick vault with a shop in front
# of it, so the brick chimney is the biggest thing on the building and the
# arch of the oven mouth is repeated in the door.

def build_bakery():
    meshtools.reset_scene()
    parts = []
    parts.append(plinth("Plinth", 3.30, 2.70, 0.28))

    walls = forms.loft("Walls", "v_ochre", [
        (0.00, RR(3.26, 2.66, 0.14, 5)),
        (0.22, RR(3.10, 2.52, 0.13, 5)),
        (2.20, RR(3.04, 2.47, 0.13, 5)),
    ])
    meshtools.wobble(walls, amount=0.015, scale=2.6, seed=11,
                     axis_bias=(1, 1, 0.3))
    meshtools.paint_by_normal(walls, "v_ochre", "v_ochre", "v_ochre_sh",
                              up_at=0.8, down_at=-0.55)
    parts.append(walls)

    # ⛔ A STEEP roof, and a crisp ridge. Six buildings with the same course
    # table came out as six copies of one barrel-vaulted hut -- the pitch has
    # to differ per building or the street reads as a tiling. The last two
    # courses collapse fast here, which is what makes a sharp ridge rather
    # than a rounded-over one.
    parts.append(tiled_roof("Roof", "t_tile", [
        (2.10, 3.72, 3.04, 0.05, -0.06),
        (2.52, 3.24, 3.00, 0.05, 0.08),
        (2.96, 2.58, 2.95, 0.05, 0.24),
        (3.42, 1.80, 2.90, 0.04, 0.38),
        (3.84, 0.86, 2.85, 0.04, 0.48),
        (4.06, 0.14, 2.82, 0.03, 0.52),
    ]))

    # The oven stack: brick, coursed, and deliberately oversized.
    stack = []
    z = 1.10
    for index in range(7):
        width = 1.16 - index * 0.030
        outline = RR(width, width * 0.86, 0.05, 4)
        stack.append((z, outline))
        stack.append((z + 0.26, outline))
        z += 0.30
    stack.append((z + 0.03, RR(1.18, 1.04, 0.06, 4)))
    stack.append((z + 0.20, RR(1.12, 0.98, 0.06, 4)))
    chimney = forms.loft("Oven", "v_brick", stack, at=(-1.46, 0.46, 0.0))
    meshtools.paint_by_normal(chimney, "t_tile_sun", "v_brick", "v_brick_deep",
                              up_at=0.75, down_at=-0.35)
    parts.append(chimney)

    front = -1.26
    parts += arched_door(0.72, front, width=0.80, colour="v_brick_deep",
                         knob="v_gold")
    # The oven mouth, echoed on the front as a bread window.
    parts += casement(-0.60, 1.26, 1.10, 0.92, front)
    parts += awning("Awning", -0.60, front - 0.06, 1.42, 1.96)
    parts += sign("Sign", 1.12, front - 0.04, 2.00, "v_brick_deep")
    parts += casement(-1.52, 1.30, 0.62, 0.74, 0.0)

    # Three loaves on the sill, which is the whole shopfront in one detail.
    for index in range(3):
        loaf = forms.superform(
            "Loaf", "h_straw", size=(0.26, 0.17, 0.15), exponent=2.6,
            segments=11, rings=8, at=(-0.92 + index * 0.33, front - 0.14, 0.90))
        forms.dents(loaf, [(-0.92 + index * 0.33, front - 0.14, 0.98)],
                    depth=0.022, radius=0.10)
        parts.append(loaf)

    bakery = meshtools.join(parts, "Bakery")
    meshtools.merge_doubles(bakery)
    forms.facet(bakery, angle=10.0)
    meshtools.drop_to_floor(bakery)
    return [bakery]


# ------------------------------------------------------------ CLOCK HOUSE
#
# Read from the DIAL, so the dial is big, pale and high, and the tower is
# narrow enough that it is the tallest thing in the village after the mill.
# A clock is also the one object here allowed to be perfectly circular.

def build_clock_house():
    meshtools.reset_scene()
    parts = []
    parts.append(plinth("Plinth", 2.42, 2.30, 0.32))

    tower = forms.loft("Tower", "s_wall", [
        (0.00, RR(2.36, 2.24, 0.12, 5)),
        (0.26, RR(2.20, 2.08, 0.11, 5)),
        (2.60, RR(2.06, 1.96, 0.11, 5)),
        (3.90, RR(1.98, 1.88, 0.10, 5)),
        (4.02, RR(2.22, 2.12, 0.11, 5)),   # a corbelled band under the belfry
        (4.26, RR(2.16, 2.06, 0.11, 5)),
    ])
    meshtools.wobble(tower, amount=0.013, scale=2.2, seed=7,
                     axis_bias=(1, 1, 0.25))
    meshtools.paint_by_normal(tower, "s_wall", "s_wall", "s_wall_shade",
                              up_at=0.8, down_at=-0.5)
    parts.append(tower)

    # The belfry: an open stage with four posts, so the tower reads hollow at
    # the top rather than as a solid stump with a hat.
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(forms.loft("Post", "s_wood", [
                (4.26, RR(0.22, 0.22, 0.03, 3)),
                (5.12, RR(0.20, 0.20, 0.03, 3)),
            ], at=(sx * 0.86, sy * 0.80, 0.0)))
    parts.append(forms.loft("BelfryFloor", "s_wood_deep", [
        (4.26, RR(2.10, 2.00, 0.10, 5)),
        (4.36, RR(2.04, 1.94, 0.10, 5)),
    ]))
    bell = forms.lathe("Bell", "v_gold", [
        (0.000, 4.98), (0.120, 4.96), (0.230, 4.84), (0.300, 4.62),
        (0.330, 4.50), (0.300, 4.46), (0.000, 4.50),
    ], segments=14)
    parts.append(bell)

    parts.append(tiled_roof("Spire", "t_tile", [
        (5.08, 2.56, 2.44, 0.05, 0.0),
        (5.34, 2.10, 2.00, 0.05, 0.0),
        (5.66, 1.56, 1.48, 0.04, 0.0),
        (5.98, 0.96, 0.92, 0.04, 0.0),
        (6.26, 0.34, 0.32, 0.03, 0.0),
    ], scallop=0.034))
    parts.append(forms.sweep("Finial", "v_gold",
                             [(0, 0, 6.24), (0, 0, 6.62)],
                             [0.034, 0.016], segments=7))

    # The dial. A lathed disc set into the wall, a ring, twelve marks and two
    # hands reading ten past ten -- the angle every clock in every shop window
    # is set to, because it frames the face and looks awake.
    front = -1.05
    parts.append(forms.lathe("DialSurround", "v_slate", [
        (0.000, 0.00), (0.780, 0.00), (0.760, -0.10), (0.000, -0.10),
    ], segments=26, at=(0.0, front, 0.0)))
    dial = forms.lathe("Dial", "v_clock", [
        (0.000, -0.10), (0.700, -0.10), (0.690, -0.16), (0.000, -0.16),
    ], segments=26, at=(0.0, front, 0.0))
    parts.append(dial)
    for hour in range(12):
        angle = math.tau * hour / 12
        parts.append(forms.sweep(
            "Mark", "s_ink",
            [(math.cos(angle) * 0.46, front - 0.17, 3.00 + math.sin(angle) * 0.46),
             (math.cos(angle) * 0.58, front - 0.17, 3.00 + math.sin(angle) * 0.58)],
            [0.030 if hour % 3 == 0 else 0.018] * 2, segments=4))
    for length, radius, hour_angle in ((0.36, 0.034, 60.0), (0.54, 0.026, 170.0)):
        a = math.radians(hour_angle)
        parts.append(forms.sweep(
            "Hand", "s_ink",
            [(0.0, front - 0.19, 3.00),
             (math.cos(a) * length, front - 0.19, 3.00 + math.sin(a) * length)],
            [radius, radius * 0.5], segments=5))
    parts.append(forms.superform("Boss", "v_gold", size=(0.10, 0.07, 0.10),
                                 exponent=2.4, segments=10, rings=8,
                                 at=(0.0, front - 0.20, 3.00)))
    # Lift the whole dial assembly to the tower's upper storey.
    for part in parts[-(12 + 2 + 1 + 2):]:
        for vert in part.data.vertices:
            vert.co.z += 0.0

    parts += arched_door(0.0, front - 0.18, width=0.84, colour="v_slate")
    parts += casement(0.0, 1.95, 0.62, 0.80, front - 0.14)

    clock = meshtools.join(parts, "ClockHouse")
    meshtools.merge_doubles(clock)
    forms.facet(clock, angle=10.0)
    meshtools.drop_to_floor(clock)
    return [clock]


# --------------------------------------------------------------- BOOKSHOP
#
# Read from the JETTY -- the upper storey overhanging the street -- and from a
# bay window big enough to put books in. Tall, narrow and leaning, because a
# bookshop should look like it has been there longest.

def build_bookshop():
    meshtools.reset_scene()
    parts = []
    parts.append(plinth("Plinth", 2.70, 2.40, 0.26))

    walls = forms.loft("Walls", "v_sage", [
        (0.00, RR(2.64, 2.34, 0.12, 5)),
        (0.22, RR(2.50, 2.22, 0.11, 5)),
        (1.86, RR(2.44, 2.17, 0.11, 5)),
        (1.98, RR(2.92, 2.56, 0.13, 5)),   # the jetty
        (3.30, RR(2.84, 2.50, 0.13, 5)),
    ])
    meshtools.wobble(walls, amount=0.016, scale=2.5, seed=3,
                     axis_bias=(1, 1, 0.3))
    meshtools.paint_by_normal(walls, "v_sage", "v_sage", "v_sage_sh",
                              up_at=0.8, down_at=-0.55)
    parts.append(walls)
    # A jetty needs a drawn line under it or it reads as a modelling glitch.
    parts.append(forms.loft("JettyBressummer", "s_wood_deep", [
        (1.88, RR(2.52, 2.24, 0.11, 5)),
        (2.00, RR(2.96, 2.60, 0.13, 5)),
    ], close_bottom=False, close_top=False))
    for x in (-0.92, 0.0, 0.92):
        parts.append(forms.sweep("Bracket", "s_wood_deep",
                                 [(x, -1.22, 1.62), (x, -1.46, 1.98)],
                                 [0.054, 0.044], segments=5))

    parts.append(tiled_roof("Roof", "t_tile", [
        (3.20, 3.46, 2.98, 0.05, -0.06),
        (3.62, 2.92, 2.94, 0.05, 0.14),
        (4.06, 2.16, 2.90, 0.04, 0.32),
        (4.48, 1.20, 2.86, 0.04, 0.46),
        (4.72, 0.16, 2.82, 0.03, 0.52),
    ]))

    front = -1.22
    # The bay: a three-sided shop window, which is the whole ground floor.
    bay = forms.loft("Bay", "v_green", [
        (0.10, [(-0.86, 0.0), (-0.62, -0.46), (0.62, -0.46), (0.86, 0.0)]),
        (1.52, [(-0.86, 0.0), (-0.62, -0.46), (0.62, -0.46), (0.86, 0.0)]),
    ], at=(-0.42, front, 0.0), close_bottom=False)
    parts.append(bay)
    parts.append(forms.loft("BayGlass", "s_wood_deep", [
        (0.32, [(-0.74, -0.06), (-0.54, -0.50), (0.54, -0.50), (0.74, -0.06)]),
        (1.32, [(-0.74, -0.06), (-0.54, -0.50), (0.54, -0.50), (0.74, -0.06)]),
    ], at=(-0.42, front, 0.0), close_bottom=False))
    parts.append(forms.loft("BayRoof", "v_slate", [
        (1.52, [(-0.98, 0.10), (-0.70, -0.60), (0.70, -0.60), (0.98, 0.10)]),
        (1.64, [(-0.86, 0.04), (-0.62, -0.48), (0.62, -0.48), (0.86, 0.04)]),
    ], at=(-0.42, front, 0.0), close_bottom=False))
    # Books in the window: five coloured slabs, leaning.
    for index, colour in enumerate(("v_brick", "v_green", "v_gold", "v_plum",
                                    "v_teal")):
        slab = forms.loft("Book", colour, [
            (0.52, RR(0.11, 0.26, 0.02, 3)),
            (0.96, RR(0.11, 0.26, 0.02, 3)),
        ], at=(-0.82 + index * 0.20, front - 0.26, 0.0))
        meshtools.lean(slab, degrees=4.0 - index * 2.0, axis="Y",
                       pivot_z=0.52)
        parts.append(slab)

    parts += arched_door(0.82, front, width=0.74, colour="v_green",
                         knob="v_gold")
    parts += sign("Sign", -0.42, front - 0.52, 2.10, "v_green")
    parts += casement(-0.70, 2.56, 0.74, 0.88, front - 0.24)
    parts += casement(0.78, 2.56, 0.62, 0.78, front - 0.24)

    shop = meshtools.join(parts, "Bookshop")
    meshtools.merge_doubles(shop)
    meshtools.lean(shop, degrees=1.3, axis="Y", pivot_z=0.0)
    forms.facet(shop, angle=10.0)
    meshtools.drop_to_floor(shop)
    return [shop]


# ------------------------------------------------------------ FLOWER SHOP
#
# Read from the STOCK, not the building. The shop itself is the smallest and
# plainest of the six on purpose: everything that makes it legible -- the
# awning, the buckets, the trough, the window boxes, the climbing rose -- is
# the flowers piled outside it.

BLOOMS = ("f_bloom", "f_bloom_sun", "f_bloom_pale", "v_plum", "v_awning")


def _bunch(at, count=7, spread=0.17, lift=0.20, size=1.0, seed=0):
    """A fistful of flowers. `_flower` from the smallholding, clustered."""
    import random
    rng = random.Random(seed)
    parts = []
    foliage = F.cushion("Leaves", "f_crop", 0.19 * size, 0.17 * size,
                        (at[0], at[1], at[2] + 0.03), lobes=7, amount=0.30,
                        points=14, twist=22)
    meshtools.paint_by_normal(foliage, "f_crop", "f_crop", "f_crop_deep",
                              up_at=0.5, down_at=-0.3)
    parts.append(foliage)
    for index in range(count):
        angle = math.tau * index / count + rng.uniform(-0.3, 0.3)
        reach = rng.uniform(0.04, spread) * size
        height = at[2] + lift * rng.uniform(0.75, 1.25) * size
        parts += F._flower(
            (at[0] + math.cos(angle) * reach,
             at[1] + math.sin(angle) * reach, height),
            BLOOMS[index % len(BLOOMS)],
            BLOOMS[(index + 2) % len(BLOOMS)],
            size=0.78 * size,
            tilt=(rng.uniform(-28, 28), rng.uniform(-28, 28)),
            stem=height - at[2])
    return parts


def build_flower_shop():
    meshtools.reset_scene()
    parts = []
    parts.append(plinth("Plinth", 2.90, 2.40, 0.24))

    walls = forms.loft("Walls", "v_rose", [
        (0.00, RR(2.84, 2.34, 0.13, 5)),
        (0.20, RR(2.70, 2.22, 0.12, 5)),
        (2.06, RR(2.64, 2.18, 0.12, 5)),
    ])
    meshtools.wobble(walls, amount=0.014, scale=2.6, seed=21,
                     axis_bias=(1, 1, 0.3))
    meshtools.paint_by_normal(walls, "v_rose", "v_rose", "v_rose_sh",
                              up_at=0.8, down_at=-0.55)
    parts.append(walls)
    # Shallow and wide, with a long overhang: the lowest roof in the village.
    parts.append(tiled_roof("Roof", "t_tile", [
        (1.96, 3.52, 2.96, 0.05, -0.05),
        (2.18, 3.06, 2.92, 0.05, 0.10),
        (2.40, 2.48, 2.88, 0.05, 0.26),
        (2.62, 1.78, 2.84, 0.04, 0.40),
        (2.80, 0.96, 2.80, 0.04, 0.50),
        (2.94, 0.18, 2.76, 0.03, 0.54),
    ]))

    front = -1.14
    parts += arched_door(0.84, front, width=0.74, colour="v_plum",
                         knob="v_gold")
    parts += casement(-0.56, 1.22, 1.16, 0.94, front)
    parts += awning("Awning", -0.30, front - 0.04, 2.20, 1.92, reach=0.92,
                    stripes=9, colour="v_plum")
    parts += sign("Sign", 1.26, front - 0.02, 1.92, "v_plum")

    # A tiered trough of buckets under the window -- the thing a child sees.
    parts.append(forms.loft("Trough", "s_wood", [
        (0.00, RR(2.10, 0.62, 0.06, 4)),
        (0.42, RR(2.22, 0.70, 0.07, 4)),
    ], at=(-0.40, front - 0.74, 0.0)))
    for index in range(5):
        x = -1.22 + index * 0.41
        bucket = forms.lathe("Bucket", "v_teal", [
            (0.000, 0.42), (0.175, 0.42), (0.205, 0.74), (0.195, 0.78),
            (0.165, 0.74), (0.000, 0.72),
        ], segments=12, at=(x, front - 0.74, 0.0))
        parts.append(bucket)
        parts += _bunch((x, front - 0.74, 0.80), count=6, seed=40 + index)

    # A rose climbing the front, trained up past the sign.
    for index in range(7):
        k = index / 6.0
        parts += _bunch((1.22 + math.sin(k * 5.0) * 0.14, front - 0.08,
                         0.42 + k * 1.30), count=3, spread=0.09,
                        lift=0.10, size=0.62, seed=70 + index)

    shop = meshtools.join(parts, "FlowerShop")
    meshtools.merge_doubles(shop)
    forms.facet(shop, angle=11.0)
    meshtools.drop_to_floor(shop)
    return [shop]


# --------------------------------------------------------------- WORKSHOP
#
# Read from being OPEN. The other five are closed boxes with holes in them;
# this one has a whole wall missing, a bench under the opening and a lean-to
# full of timber beside it. It is the only building you can see INTO, which is
# what makes it the workshop.

def build_workshop():
    meshtools.reset_scene()
    parts = []
    parts.append(plinth("Plinth", 3.60, 2.80, 0.26))

    # Three walls and a header over the opening, rather than a loft ring: the
    # front is deliberately absent.
    for name, size, at in (
            ("WallBack", (3.54, 0.30), (0.0, 1.22)),
            ("WallLeft", (0.30, 2.74), (-1.62, 0.0)),
            ("WallRight", (0.30, 2.74), (1.62, 0.0))):
        wall = forms.loft(name, "s_wall", [
            (0.00, RR(size[0] + 0.10, size[1] + 0.10, 0.08, 4)),
            (0.20, RR(size[0], size[1], 0.07, 4)),
            (2.18, RR(size[0] - 0.04, size[1] - 0.04, 0.07, 4)),
        ], at=(at[0], at[1], 0.0))
        meshtools.wobble(wall, amount=0.012, scale=2.8, seed=31,
                         axis_bias=(1, 1, 0.25))
        meshtools.paint_by_normal(wall, "s_wall", "s_wall", "s_wall_shade",
                                  up_at=0.8, down_at=-0.55)
        parts.append(wall)
    parts.append(forms.loft("Header", "s_wood", [
        (1.86, RR(3.36, 0.34, 0.05, 4)),
        (2.18, RR(3.36, 0.34, 0.05, 4)),
    ], at=(0.0, -1.22, 0.0)))
    for x in (-1.12, 1.12):
        parts.append(forms.loft("OpenPost", "s_wood", [
            (0.18, RR(0.26, 0.30, 0.04, 3)),
            (1.90, RR(0.24, 0.28, 0.04, 3)),
        ], at=(x, -1.22, 0.0)))

    parts.append(tiled_roof("Roof", "t_tile", [
        (2.08, 4.08, 3.34, 0.05, -0.07),
        (2.34, 3.64, 3.30, 0.05, 0.06),
        (2.62, 3.06, 3.26, 0.05, 0.20),
        (2.90, 2.34, 3.22, 0.04, 0.32),
        (3.14, 1.48, 3.18, 0.04, 0.40),
        (3.34, 0.46, 3.14, 0.03, 0.44),
    ]))

    # The bench in the opening, with its vice and a scatter of tools.
    parts.append(forms.loft("Bench", "s_wood", [
        (0.78, RR(2.70, 0.78, 0.05, 4)),
        (0.92, RR(2.78, 0.84, 0.05, 4)),
    ], at=(0.0, -0.68, 0.0)))
    for x in (-1.16, 1.16):
        for y in (-0.96, -0.40):
            parts.append(forms.loft("BenchLeg", "s_wood_deep", [
                (0.0, RR(0.16, 0.16, 0.03, 3)),
                (0.80, RR(0.14, 0.14, 0.03, 3)),
            ], at=(x, y, 0.0)))
    parts.append(forms.loft("Vice", "w_iron", [
        (0.70, RR(0.36, 0.30, 0.04, 3)),
        (1.04, RR(0.34, 0.28, 0.04, 3)),
    ], at=(-1.02, -0.92, 0.0)))
    for index, (x, length) in enumerate(((0.10, 0.52), (0.52, 0.40),
                                         (0.96, 0.46))):
        parts.append(forms.sweep(
            "Tool", "s_wood_deep",
            [(x, -0.62, 0.96), (x + length, -0.56, 0.96)],
            [0.030, 0.022], segments=5))
        parts.append(forms.superform(
            "ToolHead", "w_iron", size=(0.14, 0.09, 0.09), exponent=3.0,
            segments=9, rings=7, at=(x + length + 0.06, -0.555, 0.97)))

    # A lean-to of stacked timber: the subordinate mass, and the reason the
    # workshop is the widest building in the village.
    parts.append(forms.loft("LeanRoof", "t_tile_deep", [
        (1.52, RR(1.70, 2.90, 0.09, 4)),
        (1.60, RR(1.70, 2.90, 0.09, 4)),
        (2.04, RR(1.10, 2.84, 0.08, 4)),
    ], at=(2.44, 0.10, 0.0), close_bottom=False))
    for x in (1.76, 3.12):
        for y in (-1.18, 1.26):
            parts.append(forms.loft("LeanPost", "s_wood", [
                (0.0, RR(0.20, 0.20, 0.03, 3)),
                (1.56, RR(0.18, 0.18, 0.03, 3)),
            ], at=(x, y, 0.0)))
    for row in range(3):
        for index in range(4):
            log = forms.sweep(
                "Timber", "s_wood" if (row + index) % 2 else "s_wood_deep",
                [(1.78, -0.90 + index * 0.22, 0.16 + row * 0.23),
                 (3.10, -0.90 + index * 0.22, 0.16 + row * 0.23)],
                [0.105, 0.098], segments=7)
            parts.append(log)

    parts += sign("Sign", -1.24, -1.32, 2.00, "v_teal")

    shop = meshtools.join(parts, "Workshop")
    meshtools.merge_doubles(shop)
    forms.facet(shop, angle=10.0)
    meshtools.drop_to_floor(shop)
    return [shop]


def _annette_face():
    """Round spectacles, a soft smile, eyes that are KIND rather than big.

    ⛔ Not Chuck's face at a different scale. His eyes are huge and wide-set
    with a highlight because he is five; hers are smaller, closer and sit
    behind glass, because the read has to be ADULT at a glance. Over-sizing
    an adult's eyes is the single fastest way to make two characters look
    like siblings.
    """
    parts = []
    eye_z = A_HEAD_Z + 0.016
    for side in (-1, 1):
        parts.append(forms.superform(
            "Eye", "h_hair", size=(0.056, 0.030, 0.062), exponent=2.2,
            segments=11, rings=8,
            at=(side * 0.082, A_FACE_Y - 0.010, eye_z)))
        parts.append(forms.superform(
            "Spark", "h_tooth", size=(0.020, 0.014, 0.022), exponent=2.2,
            segments=8, rings=6,
            at=(side * 0.090, A_FACE_Y - 0.024, eye_z + 0.018)))
        parts.append(forms.sweep(
            "Brow", "v_hair",
            [(side * 0.044, A_FACE_Y - 0.010, eye_z + 0.060),
             (side * 0.118, A_FACE_Y - 0.006, eye_z + 0.066)],
            [0.009, 0.007], segments=6, samples=4, profile_squash=0.55))
        # The spectacles. Chuck's old rims, inherited.
        parts.append(meshtools.torus(
            "Rim", "v_brass", major=0.058, minor=0.0085,
            at=(side * 0.082, A_FACE_Y - 0.030, eye_z),
            rot=(math.radians(90), 0, 0), major_seg=18, minor_seg=6))
        parts.append(forms.sweep(
            "Temple", "v_brass",
            [(side * 0.128, A_FACE_Y - 0.030, eye_z),
             (side * 0.158, A_FACE_Y + 0.110, eye_z + 0.020)],
            [0.0075, 0.0065], segments=5))
    parts.append(forms.sweep(
        "Bridge", "v_brass",
        [(-0.024, A_FACE_Y - 0.030, eye_z + 0.010),
         (0.024, A_FACE_Y - 0.030, eye_z + 0.010)],
        [0.0075, 0.0075], segments=6))
    parts.append(forms.superform(
        "Nose", "h_skin", size=(0.042, 0.046, 0.040), exponent=2.7,
        segments=10, rings=8,
        at=(0, A_FACE_Y - 0.016, A_HEAD_Z - 0.052)))
    # A closed, warm smile -- an open grin would read as Chuck.
    parts.append(forms.sweep(
        "Smile", "h_vest_deep",
        [(-0.058, A_FACE_Y + 0.006, A_HEAD_Z - 0.112),
         (0.0, A_FACE_Y - 0.012, A_HEAD_Z - 0.126),
         (0.058, A_FACE_Y + 0.006, A_HEAD_Z - 0.112)],
        [0.009, 0.015, 0.009], segments=8, samples=5, profile_squash=0.7))
    return parts


def _annette_hair():
    """A smooth cap and a BUN. One silhouette, and the whole read from behind.

    Chuck's hair is six spikes breaking his outline; hers closes it. A bun
    also puts a distinctive bump on her profile at exactly the height the
    gameplay camera looks down on.
    """
    parts = []
    cap = forms.superform("Hair", "v_hair", size=(0.362, 0.344, 0.300),
                          exponent=3.0, segments=20, rings=14,
                          at=(0.0, 0.020, A_HEAD_Z + 0.098))
    forms.press(cap, "Y", plane=A_FACE_Y + 0.052, amount=0.42, radius=0.21,
                centre=(0, -0.165, A_HEAD_Z + 0.072))
    meshtools.paint_by_normal(cap, "v_hair_sun", "v_hair", "h_hair",
                              up_at=0.6, down_at=-0.35)
    parts.append(cap)
    bun = forms.superform("Bun", "v_hair", size=(0.176, 0.172, 0.158),
                          exponent=2.5, segments=14, rings=11,
                          at=(0.0, 0.200, A_HEAD_Z + 0.108))
    meshtools.paint_by_normal(bun, "v_hair_sun", "v_hair", "h_hair",
                              up_at=0.6, down_at=-0.35)
    parts.append(bun)
    # The pin through it, and two strands escaping at the temples -- without
    # them a bun is a doorknob.
    parts.append(forms.sweep("Pin", "v_gold",
                             [(-0.10, 0.232, A_HEAD_Z + 0.136),
                              (0.10, 0.182, A_HEAD_Z + 0.100)],
                             [0.008, 0.006], segments=5))
    # ⛔ Thin, and swept DOWN the cheek. At radius 0.030 on a 6-sided sweep
    # these read as two grey bolts screwed into the sides of her head --
    # chunky enough to look like headphones. A loose strand of hair is a
    # hair's width at the end and hugs the face.
    for side in (-1, 1):
        parts.append(forms.sweep(
            "Strand", "v_hair",
            [(side * 0.150, -0.046, A_HEAD_Z + 0.086),
             (side * 0.158, -0.082, A_HEAD_Z + 0.010),
             (side * 0.146, -0.100, A_HEAD_Z - 0.066)],
            [0.017, 0.012, 0.003], segments=7, samples=5,
            profile_squash=0.55))
    return parts


def _annette_rig(mesh, factor):
    """Same skeleton as Chuck, so one set of motion ideas serves both.

    ⛔ The LEGS are bound but barely move: she is in a long skirt, and a
    skirt that counter-swings with the thighs underneath it reads as
    trousers. The walk below rotates the hips and lets the hem follow.
    """
    def at(x, z, y=0.0):
        return (x * factor, y * factor, z * factor)

    skeleton = rig.Rig("AnnetteRig")
    skeleton.bone("root", at(0, 0), at(0, 0.14))
    skeleton.bone("hips", at(0, A_HIP_Z), at(0, A_CHEST_Z), parent="root")
    skeleton.bone("chest", at(0, A_CHEST_Z), at(0, A_NECK_Z), parent="hips",
                  connected=True)
    skeleton.bone("head", at(0, A_NECK_Z), at(0, A_HEAD_TOP), parent="chest",
                  connected=True)
    for side, tag in ((-1, "L"), (1, "R")):
        skeleton.bone("arm_" + tag, at(side * A_SHOULDER[0], A_SHOULDER[1]),
                      at(side * A_ELBOW[0], A_ELBOW[1]), parent="chest")
        skeleton.bone("hand_" + tag, at(side * A_ELBOW[0], A_ELBOW[1]),
                      at(side * A_HAND[0], A_HAND[2], A_HAND[1]),
                      parent="arm_" + tag, connected=True)
        skeleton.bone("thigh_" + tag, at(side * 0.086, A_HIP_Z - 0.04),
                      at(side * 0.086, 0.34), parent="hips")
        skeleton.bone("shin_" + tag, at(side * 0.086, 0.34),
                      at(side * 0.086, 0.09), parent="thigh_" + tag,
                      connected=True)
        skeleton.bone("foot_" + tag, at(side * 0.086, 0.09),
                      at(side * 0.088, 0.03, -0.12), parent="shin_" + tag,
                      connected=True)
    neck = (A_NECK_Z + 0.015) * factor
    skeleton.bind(mesh, falloff=5.5, influences=3, prefer={
        "head": lambda p: p.z > neck,
    }, prefer_weight=0.97)
    return skeleton


def _annette_idle(skeleton):
    """Standing and breathing, with a slow look to either side."""
    frames = {}
    for frame, phase in ((1, 0.0), (25, 1.0), (49, 0.0)):
        frames[frame] = {
            "root": {"loc": (0, 0, 0.004 * phase)},
            "hips": {"rot": (-0.9 * phase, 0, 0.5 * phase)},
            "chest": {"rot": (1.6 * phase, 0, -0.4 * phase),
                      "scale": (1.0, 1.0 + 0.014 * phase, 1.0)},
            "head": {"rot": (-1.1 * phase, 1.8 * phase, 0)},
            "arm_L": {"rot": (0, 0, -2.2 * phase)},
            "arm_R": {"rot": (0, 0, 2.2 * phase)},
        }
    frames[13] = dict(frames[1])
    frames[13]["head"] = {"rot": (-0.6, -2.6, 0.8)}
    frames[37] = dict(frames[25])
    frames[37]["head"] = {"rot": (-1.4, 3.2, -0.8)}
    return skeleton.action("annette_idle", frames)


def _annette_walk(skeleton):
    """An unhurried walk in a long skirt.

    Half Chuck's leg swing and twice his hip sway. His walk is a child's
    bounce; hers has to be a measured adult stride, and almost all of the
    motion a viewer actually reads is in the hips and the hem.
    """
    def step(lead, trail, bob, twist):
        return {
            "root": {"loc": (0, 0, bob)},
            "hips": {"rot": (1.2, twist, 0)},
            "chest": {"rot": (0.4, -twist * 0.7, 0)},
            "head": {"rot": (-0.5, -twist * 0.25, 0)},
            "thigh_" + lead: {"rot": (-11, 0, 0)},
            "shin_" + lead: {"rot": (4, 0, 0)},
            "thigh_" + trail: {"rot": (9, 0, 0)},
            "shin_" + trail: {"rot": (13, 0, 0)},
            "arm_" + lead: {"rot": (11, 0, 0)},
            "arm_" + trail: {"rot": (-13, 0, 0)},
        }

    def pass_pose(planted, lifted, twist):
        return {
            "root": {"loc": (0, 0, 0.012)},
            "hips": {"rot": (0.6, twist * 0.4, 0)},
            "chest": {"rot": (0.3, -twist * 0.3, 0)},
            "thigh_" + planted: {"rot": (-2, 0, 0)},
            "thigh_" + lifted: {"rot": (-1, 0, 0)},
            "shin_" + lifted: {"rot": (22, 0, 0)},
            "arm_" + planted: {"rot": (1, 0, 0)},
            "arm_" + lifted: {"rot": (-1, 0, 0)},
        }

    frames = {
        1: step("L", "R", -0.008, 6.0),
        7: pass_pose("L", "R", 2.5),
        13: step("R", "L", -0.008, -6.0),
        19: pass_pose("R", "L", -2.5),
        25: step("L", "R", -0.008, 6.0),
    }
    return skeleton.action("annette_walk", frames)




# --------------------------------------------------------------- ANNETTE
#
# The village guide, redesigned as a CLASSIC LIBRARIAN.
#
# She has one hard job in the design: she must never be mistaken for Chuck at
# gameplay distance. So every silhouette decision is the opposite of his --
#
#   he is 1.35 m and 2.9 heads;      she is 1.58 m and nearer 4.5, an adult.
#   he is widest at a hat brim;      she is widest at the hem of a long skirt.
#   his legs are bare and apart;     her skirt is a single unbroken cone.
#   his hair is a wild black spray;  hers is a smooth bun, one silhouette.
#   he LOST his glasses in the
#   redesign;                        she wears them. They are now HERS.
#
# ⭐ That last one is the useful accident. Round spectacles were the old
# Chuck's only distinguishing feature and dropping them was the risk in his
# pass; moving them to Annette spends the idea instead of wasting it, and
# gives the two characters one shared piece of visual language.
#
# Warm, not stern. The brief is a librarian a five-year-old likes: soft smile,
# head tipped slightly, a book held against her, no pointing finger.

A_HEIGHT = 1.58          # annette.gd's step_length of 0.55 is a stride at this
A_HEAD_Z = 1.330
A_FACE_Y = -0.138
A_HIP_Z = 0.760
A_CHEST_Z = 1.040
A_NECK_Z = 1.150
A_HEAD_TOP = 1.520
A_SHOULDER = (0.168, 1.090)
A_ELBOW = (0.212, 0.930)
A_HAND = (0.206, -0.120, 0.800)


def build_annette():
    meshtools.reset_scene()
    parts = []

    # --- the skirt. ⭐ A LATHE, which is what an A-line skirt literally is:
    # one drawn silhouette revolved. It is also the single strongest reason
    # she cannot be confused with Chuck -- an unbroken cone from waist to hem
    # where he has two bare legs.
    skirt = forms.lathe("Skirt", "v_plum", [
        (0.000, 0.055), (0.330, 0.045), (0.352, 0.100), (0.330, 0.190),
        (0.296, 0.330), (0.252, 0.500), (0.214, 0.640), (0.196, 0.730),
        (0.190, 0.775), (0.000, 0.782),
    ], segments=22, smooth_profile=0)
    meshtools.paint_by_normal(skirt, "v_plum", "v_plum", "h_vest_deep",
                              up_at=0.75, down_at=-0.4)
    # Soft vertical folds: a skirt that is a perfect solid of revolution reads
    # as a lampshade, and four shallow dents is all it takes to deny that.
    forms.dents(skirt, [(math.cos(a) * 0.33, math.sin(a) * 0.33, 0.30)
                        for a in (0.6, 2.0, 3.6, 5.1)],
                depth=0.030, radius=0.19)
    meshtools.wobble(skirt, amount=0.008, scale=4.0, seed=12)
    parts.append(skirt)

    for side in (-1, 1):
        parts.append(forms.superform(
            "Shoe", "s_wood_deep", size=(0.125, 0.235, 0.105), exponent=3.2,
            segments=12, rings=9, at=(side * 0.088, -0.030, 0.052)))
        parts.append(forms.sweep(
            "Leg", "h_skin",
            [(side * 0.086, 0.0, 0.085), (side * 0.090, 0.0, 0.300)],
            [0.062, 0.058], segments=9))

    # --- the cardigan. Buttoned, with a collar and patch pockets: the
    # closed, tidy counterpart to Chuck's open vest.
    body = forms.loft("Blouse", "s_cream", [
        (0.700, RR(0.330, 0.228, 0.085, 4)),
        (0.880, RR(0.352, 0.242, 0.092, 4)),
        (1.055, RR(0.386, 0.262, 0.100, 4)),
        (1.140, RR(0.316, 0.228, 0.082, 4)),
    ])
    meshtools.paint_by_normal(body, "s_cream", "s_cream", "s_wall_shade",
                              up_at=0.85, down_at=-0.4)
    parts.append(body)
    cardigan = forms.loft("Cardigan", "v_green", [
        (0.690, RR(0.356, 0.252, 0.092, 4)),
        (0.900, RR(0.378, 0.266, 0.098, 4)),
        (1.060, RR(0.408, 0.284, 0.106, 4)),
        (1.128, RR(0.350, 0.250, 0.090, 4)),
    ])
    # Opened down the FRONT only: the centre strip is cut back to the blouse,
    # so the cream shows as a V and the cardigan reads as a garment.
    meshtools.repaint_faces(
        cardigan,
        lambda c, n: c.y < -0.085 and abs(c.x) < 0.072 and c.z > 0.74,
        "s_cream")
    meshtools.paint_by_normal(cardigan, "v_green", "v_green", "f_hedge",
                              up_at=0.85, down_at=-0.4)
    parts.append(cardigan)
    for index in range(3):
        parts.append(forms.superform(
            "Button", "v_gold", size=(0.036, 0.022, 0.036), exponent=2.4,
            segments=9, rings=7, at=(0.0, -0.148, 0.800 + index * 0.098)))
    parts.append(forms.loft("Collar", "v_green", [
        (1.108, RR(0.250, 0.200, 0.070, 4)),
        (1.168, RR(0.214, 0.176, 0.062, 4)),
    ]))

    # ⛔ THE HANDS HAVE TO REACH THE BOOK. First pass ran the arms straight
    # down at +/-0.206 and put the book on the centre line, and she stood
    # with a hardback floating in front of her stomach that neither hand
    # touched. A held prop is only a held prop if the forearms come IN.
    book_x, book_y, book_z = 0.0, -0.188, 0.880
    for side in (-1, 1):
        parts.append(forms.sweep(
            "Arm", "v_green",
            [(side * A_SHOULDER[0], 0.0, A_SHOULDER[1]),
             (side * A_ELBOW[0], -0.040, A_ELBOW[1]),
             (side * 0.182, -0.150, 0.905)],
            [0.072, 0.062, 0.052], segments=9, samples=5))
        parts.append(forms.superform(
            "Hand", "h_skin", size=(0.092, 0.098, 0.082), exponent=2.9,
            segments=11, rings=8,
            at=(side * 0.166, book_y - 0.016, book_z)))

    # --- the book. The prop that does the most work for the least geometry:
    # it says librarian before the glasses or the bun get a chance to.
    book = forms.loft("Book", "v_brick", [
        (book_z - 0.112, RR(0.286, 0.082, 0.014, 3)),
        (book_z + 0.112, RR(0.286, 0.082, 0.014, 3)),
    ], at=(book_x, book_y, 0.0))
    meshtools.lean(book, degrees=-11.0, axis="X", pivot_z=book_z - 0.112)
    parts.append(book)
    parts.append(forms.loft("Pages", "v_clock", [
        (book_z - 0.100, RR(0.258, 0.064, 0.011, 3)),
        (book_z + 0.100, RR(0.258, 0.064, 0.011, 3)),
    ], at=(book_x, book_y - 0.016, 0.0)))
    # A ribbon marker, because a closed book with nothing in it is a brick.
    parts.append(forms.ribbon(
        "Marker", "v_awning",
        [(0.052, book_y - 0.026, book_z + 0.090),
         (0.060, book_y - 0.034, book_z - 0.150)], 0.030, thickness=0.006))

    parts.append(forms.sweep("Neck", "h_skin",
                             [(0, 0.004, 1.128), (0, 0.004, 1.196)],
                             [0.064, 0.060], segments=10))

    # --- the head. Narrower and longer than Chuck's round one, with a chin.
    head = forms.superform("Head", "h_skin", size=(0.340, 0.320, 0.400),
                           exponent=2.9, segments=22, rings=17,
                           at=(0, 0, A_HEAD_Z))
    forms.press(head, "Y", plane=A_FACE_Y, amount=0.46, radius=0.24,
                centre=(0, -0.17, A_HEAD_Z + 0.01))
    for vert in head.data.vertices:
        drop = A_HEAD_Z - vert.co.z
        if drop > 0.0:
            factor = 1.0 - 0.26 * min(drop / 0.20, 1.0) ** 1.6
            vert.co.x *= factor
            vert.co.y *= factor
    parts.append(head)
    parts += _annette_face()
    parts += _annette_hair()

    annette = meshtools.join(parts, "Annette")
    meshtools.merge_doubles(annette, 0.0004)
    forms.facet(annette, angle=7.0)
    meshtools.drop_to_floor(annette)
    factor = F._scale_to_height(annette, A_HEIGHT)
    skeleton = _annette_rig(annette, factor)
    _annette_idle(skeleton)
    _annette_walk(skeleton)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 49
    return [annette, skeleton.object]


# ---------------------------------------------------------------- PROPS
#
# De-Kennifying the village, with a judgement about each asset rather than a
# one-for-one swap. 144 Kenney instances across 17 assets; 35 of them are
# CUT because they are the wrong register for this place, not because they
# are the wrong style:
#
#   campfire x2, tent x1, seat logs x2  -- a campsite says "adventurer
#       passing through". This is a settled village; it has hearths and
#       benches, not a fire ring on the green.
#   statue obelisk x1                   -- a standing stone is
#       fantasy-adventure furniture. A WELL does the same job of giving the
#       green a centre, and is the thing a village actually gathers at.
#   rocks x29                           -- a ring of boulders is the
#       asset-pack answer to "edge of the world". A field is enclosed by
#       hedge and drystone wall, which the foundation set already speaks.
#
# Kept and rebuilt: the signpost (a fingerpost at a lane junction is as Shire
# as it gets), the pots as planters, the MUSHROOMS -- hobbits prize them and
# seven clumps is exactly right -- bushes, flowers, path stones and trees.


def produce_prop(subject, parts, budget_tris=2500, texture=512):
    """Finish a prop, splitting any tagged grass onto a flat material.

    Props are their own small GLBs rather than one joined sheet, because the
    village places them individually -- 51 path stones and 26 trees cannot
    come out of a single mesh.
    """
    solid, grass = F._split_flat_grass(parts, "v_" + subject)
    body = meshtools.join(solid, subject.title().replace("_", ""))
    meshtools.merge_doubles(body)
    return produce(subject, [body] + grass, texture=texture,
                   budget_tris=budget_tris)


def build_well():
    """The village well: the green's centre, and what replaces the obelisk.

    A drum of coursed stone, two timber posts, a little tiled roof and a
    bucket on a rope. Every part of it is a thing a person built for a
    reason, which is the whole difference from a standing stone.
    """
    meshtools.reset_scene()
    parts = []
    # Coursed stone drum. The lathe profile steps in and out per course, so
    # a height test paints the joints for nothing -- the barrel's trick.
    drum = forms.lathe("Drum", "e_stone", [
        (0.000, 0.00), (0.760, 0.00), (0.775, 0.12), (0.760, 0.20),
        (0.775, 0.32), (0.760, 0.40), (0.775, 0.52), (0.755, 0.60),
        (0.730, 0.66), (0.690, 0.64), (0.000, 0.62),
    ], segments=20, smooth_profile=0)
    meshtools.paint_by_normal(drum, "e_stone_sun", "e_stone", "e_stone_deep",
                              up_at=0.7, down_at=-0.35)
    forms.jitter_verts(drum, 0.012, seed=9)
    parts.append(drum)
    # The water, dark and flat, well down inside.
    parts.append(forms.lathe("Water", "w_water",
                             [(0.0, 0.0), (0.66, 0.0)], segments=20,
                             at=(0, 0, 0.30)))
    for side in (-1, 1):
        parts.append(forms.loft("Post", "s_wood", [
            (0.52, RR(0.17, 0.17, 0.03, 3)),
            (1.86, RR(0.15, 0.15, 0.03, 3)),
        ], at=(side * 0.62, 0.0, 0.0)))
    parts.append(forms.sweep("Windlass", "s_wood_deep",
                             [(-0.58, 0, 1.62), (0.58, 0, 1.62)],
                             [0.075, 0.075], segments=9))
    parts.append(forms.sweep("Handle", "s_wood_deep",
                             [(0.62, 0, 1.62), (0.78, 0, 1.62),
                              (0.78, -0.22, 1.62)],
                             [0.028, 0.026, 0.024], segments=6, samples=4))
    parts.append(tiled_roof("WellRoof", "t_tile", [
        (1.82, 1.86, 1.34, 0.05, 0.0),
        (2.06, 1.36, 1.28, 0.04, 0.0),
        (2.28, 0.78, 1.22, 0.04, 0.0),
        (2.44, 0.18, 1.18, 0.03, 0.0),
    ], lip=0.045, scallop=0.034))
    # Rope and bucket, hanging slightly off centre so it reads as used.
    parts.append(forms.sweep("Rope", "h_straw_deep",
                             [(0.14, 0.02, 1.58), (0.15, 0.02, 1.02)],
                             [0.014, 0.014], segments=5))
    bucket = forms.lathe("Bucket", "s_wood", [
        (0.000, 0.62), (0.145, 0.62), (0.168, 0.94), (0.158, 0.98),
        (0.134, 0.94), (0.000, 0.92),
    ], segments=12, at=(0.14, 0.02, 0.0))
    parts.append(bucket)
    parts.append(meshtools.torus("Hoop", "w_iron", major=0.160, minor=0.013,
                                 at=(0.14, 0.02, 0.72), major_seg=12,
                                 minor_seg=5))
    for index in range(3):
        angle = math.tau * index / 3
        parts += F._tuft((math.cos(angle) * 0.95, math.sin(angle) * 0.95, 0.0),
                         height=0.18, seed=300 + index)
    return parts


def build_fingerpost():
    """A lane-junction fingerpost. Three arms, none of them level."""
    meshtools.reset_scene()
    parts = []
    parts.append(forms.loft("Post", "s_wood", [
        (0.00, RR(0.20, 0.20, 0.03, 3)),
        (0.16, RR(0.17, 0.17, 0.03, 3)),
        (2.08, RR(0.145, 0.145, 0.03, 3)),
        (2.20, RR(0.185, 0.185, 0.03, 3)),
        (2.32, RR(0.10, 0.10, 0.02, 3)),
    ]))
    for index, (z, yaw, length, colour) in enumerate((
            (1.92, 24.0, 0.86, "v_green"),
            (1.62, -112.0, 0.74, "v_plum"),
            (1.34, 148.0, 0.80, "v_teal"))):
        angle = math.radians(yaw)
        arm = forms.loft("Arm", colour, [
            (z - 0.11, [(0.0, -0.045), (length, -0.035),
                        (length + 0.13, 0.0), (length, 0.035), (0.0, 0.045)]),
            (z + 0.11, [(0.0, -0.045), (length, -0.035),
                        (length + 0.13, 0.0), (length, 0.035), (0.0, 0.045)]),
        ])
        F._spin_z(arm, yaw, (0.0, 0.0))
        parts.append(arm)
        # A pale band along the arm: the lettering, without letters. At this
        # size a word would be mush; a written-looking stripe reads better.
        band = forms.loft("Words", "v_clock", [
            (z - 0.035, [(0.10, -0.030), (length - 0.04, -0.024),
                         (length + 0.02, 0.0), (length - 0.04, 0.024),
                         (0.10, 0.030)]),
            (z + 0.035, [(0.10, -0.030), (length - 0.04, -0.024),
                         (length + 0.02, 0.0), (length - 0.04, 0.024),
                         (0.10, 0.030)]),
        ])
        F._spin_z(band, yaw, (0.0, 0.0))
        parts.append(band)
    meshtools.lean(parts[0], degrees=2.2, axis="Y", pivot_z=0.0)
    parts += F._tuft((0.26, 0.14, 0.0), height=0.19, seed=11)
    parts += F._tuft((-0.22, -0.18, 0.0), height=0.16, seed=12)
    return parts


def build_bench():
    """A plank bench on two sawn trestles. Replaces the camp seat-logs."""
    meshtools.reset_scene()
    parts = []
    for z, depth in ((0.46, 0.40), (0.74, 0.14)):
        plank = forms.loft("Plank", "s_wood", [
            (z, RR(1.72, depth, 0.03, 3)),
            (z + 0.075, RR(1.72, depth, 0.03, 3)),
        ], at=(0.0, 0.0 if z < 0.5 else 0.19, 0.0))
        meshtools.wobble(plank, amount=0.006, scale=5.0, seed=4)
        meshtools.paint_by_normal(plank, "s_wood", "s_wood", "s_wood_deep",
                                  up_at=0.75, down_at=-0.4)
        parts.append(plank)
    for side in (-1, 1):
        parts.append(forms.loft("Leg", "s_wood_deep", [
            (0.0, RR(0.14, 0.34, 0.03, 3)),
            (0.48, RR(0.12, 0.30, 0.03, 3)),
        ], at=(side * 0.68, -0.02, 0.0)))
        parts.append(forms.loft("Back", "s_wood_deep", [
            (0.40, RR(0.11, 0.11, 0.02, 3)),
            (0.82, RR(0.10, 0.10, 0.02, 3)),
        ], at=(side * 0.68, 0.19, 0.0)))
    parts += F._tuft((0.86, -0.12, 0.0), height=0.20, seed=21)
    parts += F._tuft((-0.90, 0.10, 0.0), height=0.17, seed=22)
    return parts


def build_planter():
    """A half-barrel planter. Replaces the generic pot, twice over."""
    meshtools.reset_scene()
    parts = []
    tub = forms.lathe("Tub", "w_barrel", [
        (0.000, 0.00), (0.300, 0.00), (0.330, 0.10), (0.345, 0.17),
        (0.352, 0.28), (0.336, 0.44), (0.312, 0.56), (0.292, 0.58),
        (0.272, 0.54), (0.000, 0.52),
    ], segments=16, smooth_profile=0)
    meshtools.paint_by_normal(tub, "w_barrel_sun", "w_barrel", "s_wood_deep",
                              up_at=0.7, down_at=-0.35)
    for low, high in ((0.10, 0.17), (0.44, 0.56)):
        meshtools.repaint_faces(
            tub, lambda c, n, lo=low, hi=high: lo - 0.005 <= c.z <= hi + 0.005,
            "w_iron")
    parts.append(tub)
    parts += _bunch((0.0, 0.0, 0.56), count=9, spread=0.22, lift=0.26,
                    size=1.05, seed=55)
    return parts


def build_bunting():
    """Triangular flags on a slack line. A village fete, not a box of cubes.

    ⛔ The old one was `beveled_cube.obj` again. A flag is a TRIANGLE and the
    line it hangs on is a CATENARY -- both are three lines of maths and
    neither is a box. The sag is the whole charm.
    """
    meshtools.reset_scene()
    parts = []
    span, sag, flags = 6.40, 0.78, 13
    path = []
    for step in range(25):
        k = step / 24.0
        x = -span / 2 + span * k
        path.append((x, 0.0, 2.40 - sag * math.sin(math.pi * k)))
    parts.append(forms.sweep("Line", "s_wood_deep", path,
                             [0.018] * len(path), segments=5))
    colours = ("v_awning", "v_gold", "v_teal", "v_plum", "v_green")
    for index in range(flags):
        k = (index + 0.5) / flags
        x = -span / 2 + span * k
        z = 2.40 - sag * math.sin(math.pi * k)
        flag = forms.loft("Flag", colours[index % len(colours)], [
            (z - 0.02, [(-0.145, -0.012), (0.145, -0.012),
                        (0.145, 0.012), (-0.145, 0.012)]),
            (z - 0.40, [(-0.016, -0.010), (0.016, -0.010),
                        (0.016, 0.010), (-0.016, 0.010)]),
        ], at=(x, 0.0, 0.0))
        # Each flag hangs at its own angle: a row of identical pennants is a
        # printed border, not cloth.
        meshtools.lean(flag, degrees=(index % 5 - 2) * 3.5, axis="Y",
                       pivot_z=z)
        parts.append(flag)
    return parts


# --------------------------------------------------------------- NATURE
#
# The 97 remaining Kenney instances: 51 path stones, 26 trees, 20 flowers,
# 7 mushroom clumps, 2 bushes. All rebuilt, and all placed MANY times, so
# each is its own small GLB at a 512 texture rather than part of a sheet.
#
# ⛔ The trap with a prop used 26 times is that it is ONE prop used 26 times.
# `tree_b` exists for that reason alone -- two silhouettes alternating read
# as a wood; one silhouette repeated reads as wallpaper.


def build_tree_b():
    """A second tree: narrower, taller, with a leaning trunk.

    Deliberately NOT a tweak of the foundation tree. That one is a broad
    fanned crown on an S-curve; this is a tall upright cone of smaller
    cushions on a trunk that leans one way and recovers. From the gameplay
    camera the two read as different species, which is the whole point.
    """
    meshtools.reset_scene()
    parts = []
    stroke = [(0.00, 0.00, 0.00), (-0.09, 0.02, 0.62), (-0.14, -0.01, 1.28),
              (-0.05, 0.03, 1.92), (0.08, 0.01, 2.48), (0.11, 0.0, 2.84)]
    trunk = forms.sweep("Trunk", "g_timber", stroke,
                        [0.185, 0.132, 0.098, 0.074, 0.052, 0.034],
                        segments=10, samples=8, profile_squash=0.86)
    meshtools.flare_base(trunk, height=0.26, strength=0.50)
    forms.dents(trunk, [(-0.05, -0.15, 0.46), (-0.16, 0.12, 1.02),
                        (0.02, -0.12, 1.64)], depth=0.018, radius=0.11)
    meshtools.paint_by_normal(trunk, "g_timber", "g_timber", "g_ink",
                              up_at=0.7, down_at=-0.45)
    parts.append(trunk)
    for origin, tip, radius in ((( -0.12, 0.0, 1.34), (-0.52, -0.10, 1.74), 0.044),
                                ((0.00, 0.0, 1.98), (0.46, 0.12, 2.30), 0.040)):
        middle = tuple((origin[i] + tip[i]) / 2 for i in range(3))
        parts.append(forms.sweep("Branch", "g_timber",
                                 [origin, (middle[0], middle[1], middle[2] + 0.06), tip],
                                 [radius, radius * 0.66, radius * 0.36],
                                 segments=7, samples=5, profile_squash=0.84))
    layers = [
        ((-0.24, 0.08, 1.52), 0.44, 0.46, ("g_leaf", "g_leaf_deep", "g_leaf_deep"), 6, 0.22, 24),
        ((0.18, -0.10, 1.88), 0.42, 0.44, ("g_leaf", "g_leaf", "g_leaf_deep"), 7, 0.20, -28),
        ((-0.14, 0.06, 2.22), 0.50, 0.50, ("g_leaf_light", "g_leaf", "g_leaf_deep"), 7, 0.21, 20),
        ((0.14, -0.06, 2.56), 0.42, 0.44, ("g_leaf_light", "g_leaf", "g_leaf_deep"), 6, 0.23, -18),
        ((0.02, 0.04, 2.86), 0.32, 0.34, ("g_leaf_light", "g_leaf_light", "g_leaf"), 5, 0.26, 26),
        ((0.10, -0.02, 3.08), 0.22, 0.26, ("g_leaf_light", "g_leaf_light", "g_leaf"), 5, 0.28, -14),
    ]
    for index, (centre, radius, height, greens, lobes, amount, twist) in enumerate(layers):
        mass = F.cushion("Leaf", greens[1], radius, height, centre,
                         lobes=lobes, amount=amount, squash=0.94, twist=twist,
                         points=22)
        forms.jitter_verts(mass, 0.007, seed=61 + index)
        meshtools.paint_by_normal(mass, greens[0], greens[1], greens[2],
                                  up_at=0.50, down_at=-0.28)
        parts.append(mass)
    tree = meshtools.join(parts, "TreeB")
    meshtools.merge_doubles(tree)
    meshtools.drop_to_floor(tree)
    F._scale_to_height(tree, 3.35)
    return [tree]


def build_bush():
    """A hedge bush: the foundation cushion, at shrub size, with berries."""
    meshtools.reset_scene()
    parts = []
    import random
    rng = random.Random(17)
    for centre, radius, height, lobes in (((0.0, 0.0, 0.40), 0.62, 0.78, 9),
                                          ((0.34, 0.22, 0.30), 0.42, 0.58, 7),
                                          ((-0.30, -0.18, 0.26), 0.38, 0.52, 7)):
        mass = F.cushion("Bush", "f_hedge", radius, height, centre,
                         lobes=lobes, amount=0.26, twist=20, points=22)
        forms.jitter_verts(mass, 0.012, seed=int(radius * 100))
        meshtools.paint_by_normal(mass, "f_hedge_sun", "f_hedge",
                                  "g_leaf_deep", up_at=0.55, down_at=-0.3)
        parts.append(mass)
    for _ in range(9):
        angle = rng.uniform(0, math.tau)
        reach = rng.uniform(0.18, 0.56)
        parts.append(forms.superform(
            "Berry", "f_bloom", size=(0.055, 0.055, 0.055), exponent=2.2,
            segments=8, rings=6,
            at=(math.cos(angle) * reach, math.sin(angle) * reach,
                rng.uniform(0.34, 0.74))))
    return parts


def build_mushrooms():
    """A clump of mushrooms. ⭐ KEPT on purpose: hobbits prize them, and
    seven clumps tucked at tree roots is exactly the right amount of them."""
    meshtools.reset_scene()
    parts = []
    import random
    rng = random.Random(5)
    for index, (x, y, scale) in enumerate(((0.0, 0.0, 1.0), (0.21, 0.11, 0.72),
                                           (-0.16, 0.14, 0.58),
                                           (0.09, -0.20, 0.44))):
        height = 0.22 * scale
        parts.append(forms.lathe("Stalk", "v_clock", [
            (0.000, 0.00), (0.055 * scale, 0.00), (0.044 * scale, height * 0.5),
            (0.050 * scale, height), (0.000, height),
        ], segments=10, at=(x, y, 0.0)))
        cap = forms.lathe("Cap", "v_awning", [
            (0.000, height + 0.085 * scale), (0.070 * scale, height + 0.080 * scale),
            (0.120 * scale, height + 0.052 * scale),
            (0.142 * scale, height + 0.014 * scale),
            (0.136 * scale, height - 0.004 * scale), (0.000, height - 0.010 * scale),
        ], segments=12, at=(x, y, 0.0))
        meshtools.paint_by_normal(cap, "v_awning", "v_awning", "v_brick_deep",
                                  up_at=0.6, down_at=-0.3)
        parts.append(cap)
        # The spots. A red cap without them is a thimble.
        for _ in range(3):
            angle = rng.uniform(0, math.tau)
            reach = rng.uniform(0.02, 0.085) * scale
            parts.append(forms.pad(
                "Spot", "v_clock", radius=0.026 * scale, lobes=5,
                amplitude=0.12, dome=0.004, underside=0.003, points=8,
                at=(x + math.cos(angle) * reach, y + math.sin(angle) * reach,
                    height + 0.082 * scale)))
    parts += F._tuft((0.26, -0.18, 0.0), height=0.13, blades=2, seed=31)
    return parts


def build_blossom():
    """A clump of wildflowers, standing in for three Kenney flower colours.

    One asset instanced twenty times with its own random yaw beats three
    assets placed seven times each -- and the colours vary WITHIN the clump,
    which neither of the originals did.
    """
    meshtools.reset_scene()
    parts = _bunch((0.0, 0.0, 0.08), count=8, spread=0.21, lift=0.22,
                   size=0.95, seed=88)
    parts += F._tuft((0.16, 0.12, 0.0), height=0.17, seed=41)
    parts += F._tuft((-0.14, -0.10, 0.0), height=0.14, seed=42)
    return parts


def build_lane_stone():
    """One worn flag for the lanes. 51 of these make the village's paths.

    ⛔ It gets a yaw and a size per instance in the layout, never a bare
    repeat: a path of 51 identical stones is a zip fastener.
    """
    meshtools.reset_scene()
    stone = forms.superform("LaneStone", "e_stone", exponent=4.2,
                            segments=11, rings=8, size=(0.52, 0.44, 0.14),
                            at=(0, 0, 0.055))
    forms.jitter_verts(stone, 0.013, seed=3)
    forms.dents(stone, [(0.12, -0.08, 0.12), (-0.15, 0.10, 0.11)],
                depth=0.012, radius=0.14)
    meshtools.paint_by_normal(stone, "e_stone_sun", "e_stone",
                              "e_stone_deep", up_at=0.6, down_at=-0.3)
    return [stone]


def build_wall_run():
    """A 4 m run of drystone wall. ⭐ THIS IS WHAT REPLACES THE 29 ROCKS.

    A ring of boulders is the asset-pack answer to "edge of the world"; a
    field is bounded by something somebody BUILT. Three staggered courses,
    stones sized and jittered per position, so a run laid end to end never
    shows a repeat.
    """
    meshtools.reset_scene()
    parts = []
    import random
    rng = random.Random(23)
    length = 4.0
    for index in range(9):
        x = -length / 2 + length * index / 8.0
        for course, (lift, scale) in enumerate(((0.16, 1.00), (0.40, 0.92),
                                                (0.60, 0.80))):
            stagger = 0.13 if (index + course) % 2 else -0.13
            stone = forms.superform(
                "WallStone", "e_stone", exponent=3.0, segments=7, rings=5,
                size=(rng.uniform(0.40, 0.58) * scale,
                      rng.uniform(0.40, 0.56) * scale,
                      rng.uniform(0.20, 0.27)),
                at=(x + stagger * 0.3, 0.0, lift))
            forms.jitter_verts(stone, 0.014, seed=40 + index * 3 + course)
            meshtools.paint_by_normal(stone, "e_stone_sun", "e_stone",
                                      "e_stone_deep", up_at=0.55, down_at=-0.3)
            parts.append(stone)
        if index % 3 == 0:
            parts += F._tuft((x, rng.uniform(0.34, 0.46), 0.0), height=0.22,
                             seed=70 + index)
    return parts


# ------------------------------------------------------------ MILL MOUND
#
# What replaces the terrace / lookout / two-ramps terrain.
#
# ⭐ THE WHOLE THING FOLLOWS FROM ONE FACT: a windmill needs wind. That is a
# real and legible reason for the ground to be raised exactly where the
# windmill stands, and once the mound has a reason, everything attached to
# it gets one too:
#
#   * The way up is the MILLER'S CART TRACK, and a loaded cart cannot take a
#     steep gradient. So the track cannot go straight up -- it has to WRAP
#     the mound. That is what makes this tight instead of a long diagonal
#     ramp eating the map, and it means the village turns below you as you
#     climb, which is the view the whole feature exists for.
#   * Nobody on foot walks the cart track. A short flight of STONE STEPS
#     cuts straight up the bank on the far side. Two routes up, which is
#     also simply better to play.
#   * A bank cut that steep has to be held, so it is REVETTED in drystone.
#   * And a dry bank with a door in it is a ROOT CELLAR.
#
# ⛔ GAMEPLAY CONSTRAINTS, which shaped the numbers rather than decorating
# them. The village scatters 23 letter blocks over its levels, so:
#   * the TOP must be flat -- a block on a slope reads as a mistake and
#     `drop_block` would roll it;
#   * the cart track is 6.3 degrees and the steps are 27, both well under
#     `move_and_slide`'s 45-degree floor limit, and Chuck has no jump;
#   * `can_reach()` raycasts on a mask that includes the ground, so nothing
#     is placed where the bank itself would sit between Chuck and a letter.

MOUND_TOP_R = 4.20
MOUND_BASE_R = 6.40
MOUND_H = 2.15          # Chuck is 1.35, so his eyeline clears a 2.05 m eave
# ⛔ A MIDDLE LEVEL IS A REQUIREMENT, not a flourish. `tests/village.gd`
# checks that spawn markers exist at three heights snapped to 0.5 -- 0, 1 and
# 2 -- because the village is meant to scatter its letters "across all three
# walkable levels". A mound with a top and a bottom only gives two. The step
# landing is therefore a real terrace with room to stand a block on, which is
# also what a flight of stairs that long would have anyway.
SHELF_H = 1.05
TRACK_W = 2.30
TRACK_R = 6.95
TRACK_FROM, TRACK_TO = -168.0, 6.0      # degrees; 174 of wrap


def _causeway(name, colour, stations, width, ground=0.0):
    """A built-up roadway: a deck with its own sides falling to the ground.

    `forms.ribbon` gives a flat strip with a fixed thickness, which floats
    where the land drops away under it. A causeway needs the skirt to reach
    the GROUND at every station, so this bridges four rings instead of two.
    """
    import bmesh
    from mathutils import Vector
    bm = bmesh.new()
    rings = []
    count = len(stations)
    for index, (x, y, z) in enumerate(stations):
        if index == 0:
            tx, ty = stations[1][0] - x, stations[1][1] - y
        elif index == count - 1:
            tx, ty = x - stations[-2][0], y - stations[-2][1]
        else:
            tx = stations[index + 1][0] - stations[index - 1][0]
            ty = stations[index + 1][1] - stations[index - 1][1]
        length = math.hypot(tx, ty) or 1e-6
        ax, ay = -ty / length, tx / length      # across the road
        half = width / 2.0
        rings.append([
            bm.verts.new(Vector((x - ax * half, y - ay * half, z))),
            bm.verts.new(Vector((x + ax * half, y + ay * half, z))),
            bm.verts.new(Vector((x + ax * half * 1.22,
                                 y + ay * half * 1.22, ground))),
            bm.verts.new(Vector((x - ax * half * 1.22,
                                 y - ay * half * 1.22, ground))),
        ])
    for index in range(count - 1):
        lower, upper = rings[index], rings[index + 1]
        for k in range(4):
            m = (k + 1) % 4
            bm.faces.new([lower[k], lower[m], upper[m], upper[k]])
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    meshtools.set_part_color(obj, colour)
    return obj


def build_mill_mound():
    meshtools.reset_scene()
    import random
    rng = random.Random(77)
    parts = []

    # --- the mound. A battered, grassed bank: steep enough that nobody
    # mistakes it for walkable, which is what makes the track and the steps
    # read as the only ways up.
    mound = forms.lathe("Mound", "f_grass", [
        (MOUND_BASE_R, 0.00), (MOUND_BASE_R - 0.22, 0.42),
        (MOUND_BASE_R - 0.78, 1.10), (MOUND_BASE_R - 1.52, 1.78),
        (MOUND_TOP_R + 0.16, 2.08), (MOUND_TOP_R, MOUND_H), (0.0, MOUND_H),
    ], segments=30, smooth_profile=0)
    meshtools.wobble(mound, amount=0.055, scale=1.6, seed=4,
                     axis_bias=(1, 1, 0.35))
    meshtools.paint_by_normal(mound, "f_grass_sun", "f_grass",
                              "f_grass_deep", up_at=0.80, down_at=-0.3)
    parts.append(mound)

    # --- the cart track, wrapping the bank at 6.3 degrees.
    stations = []
    steps = 46
    for index in range(steps + 1):
        k = index / float(steps)
        angle = math.radians(TRACK_FROM + (TRACK_TO - TRACK_FROM) * k)
        # Eases onto the bank at the bottom and flattens onto the yard at
        # the top, so neither junction is a crease Chuck can catch on.
        lift = MOUND_H * (k * k * (3.0 - 2.0 * k))
        radius = TRACK_R - 1.9 * max(k - 0.82, 0.0) / 0.18
        stations.append((math.cos(angle) * radius, math.sin(angle) * radius,
                         lift))
    track = _causeway("Track", "e_earth", stations, TRACK_W)
    meshtools.paint_by_normal(track, "e_earth", "e_earth", "e_earth_deep",
                              up_at=0.7, down_at=-0.4)
    parts.append(track)
    # Wheel ruts, PAINTED. Dents of 0.03 on a 2.3 m road are invisible at
    # 142 px per metre; two darker bands at wheel spacing are not.
    def _rut(centre, _normal):
        angle = math.atan2(centre.y, centre.x)
        across = math.hypot(centre.x, centre.y) - TRACK_R
        return 0.34 < abs(across) < 0.72
    meshtools.subdivide(track, levels=1, smooth=False)
    meshtools.repaint_faces(track, _rut, "e_earth_deep")

    # ⭐ The retaining wall, PAINTED onto the causeway's own outer skirt. It
    # is the face you see from the village, it costs nothing, and without it
    # the earth ran unbroken from road down to grass and the whole track read
    # as a flat brown apron skirting the mound rather than a road laid on it.
    def _outer_face(centre, normal):
        if abs(normal.z) > 0.55:
            return False
        length = math.hypot(centre.x, centre.y) or 1e-6
        return (centre.x * normal.x + centre.y * normal.y) / length > 0.45

    meshtools.repaint_faces(track, _outer_face, "e_stone")

    # --- the drystone revetment. ⛔ BOTH EDGES, and the outer one is the
    # one that matters. With stone only on the inside the track rendered as
    # a flat brown apron skirting the mound -- the earth skirt ran straight
    # down to the grass and read as part of the bank, not as a road laid on
    # it. A causeway is legible because it has a BUILT EDGE you can see from
    # outside it, and that edge is also what stops a cart going over.
    for index in range(0, steps + 1, 2):
        k = index / float(steps)
        angle = math.radians(TRACK_FROM + (TRACK_TO - TRACK_FROM) * k)
        lift = MOUND_H * (k * k * (3.0 - 2.0 * k))
        outer_r = TRACK_R + TRACK_W * 0.60
        # ⛔ ONE capping course, not a stack. Placing a column of stones at
        # each sampled angle gave free-standing pillars with daylight between
        # them, because the samples are half a metre apart and the stones are
        # not. The retaining FACE is painted onto the causeway's own outer
        # side below; all this adds is the coping you would actually see
        # along the top of it.
        if lift > 0.22:
            stone = forms.superform(
                "Coping", "e_stone_sun", exponent=3.0, segments=7, rings=5,
                size=(rng.uniform(0.42, 0.56), rng.uniform(0.34, 0.46),
                      rng.uniform(0.16, 0.21)),
                at=(math.cos(angle) * outer_r, math.sin(angle) * outer_r,
                    lift - 0.04))
            forms.jitter_verts(stone, 0.012, seed=400 + index)
            meshtools.paint_by_normal(stone, "e_stone_sun", "e_stone",
                                      "e_stone_deep", up_at=0.55,
                                      down_at=-0.3)
            parts.append(stone)
        radius = TRACK_R - TRACK_W * 0.60
        for course, (dz, scale) in enumerate(((0.17, 1.0), (0.44, 0.9),
                                              (0.66, 0.78))):
            if lift + dz > MOUND_H - 0.05:
                continue
            stone = forms.superform(
                "Revet", "e_stone", exponent=3.0, segments=7, rings=5,
                size=(rng.uniform(0.38, 0.54) * scale,
                      rng.uniform(0.38, 0.52) * scale,
                      rng.uniform(0.19, 0.25)),
                at=(math.cos(angle) * radius, math.sin(angle) * radius,
                    lift + dz))
            forms.jitter_verts(stone, 0.013, seed=index * 3 + course)
            meshtools.paint_by_normal(stone, "e_stone_sun", "e_stone",
                                      "e_stone_deep", up_at=0.55,
                                      down_at=-0.3)
            parts.append(stone)

    parts += _mound_shelf(rng)
    parts += _mound_steps(rng)
    parts += _cellar_door()
    parts += _mound_top(rng)
    return parts


def _mound_shelf(rng):
    """The middle level: a grassed bench cut into the bank at the landing.

    It is reached by the first half of the steps, it is flat enough to put a
    letter block down on, and it gives the long flight the pause it needs.
    Projecting out of the bank rather than cut into it, so it does not eat
    the mill yard above.
    """
    parts = []
    bearing = math.radians(92.0)          # the steps' side
    out = (math.cos(bearing), math.sin(bearing))
    centre = (out[0] * (MOUND_BASE_R - 0.95), out[1] * (MOUND_BASE_R - 0.95))

    shelf = forms.loft("Shelf", "f_grass", [
        (0.00, RR(4.30, 3.20, 0.55, 6)),
        (SHELF_H - 0.30, RR(4.10, 3.05, 0.52, 6)),
        (SHELF_H - 0.06, RR(3.80, 2.85, 0.48, 6)),
        (SHELF_H, RR(3.62, 2.70, 0.46, 6)),
    ], at=(centre[0], centre[1], 0.0))
    F._spin_z(shelf, math.degrees(bearing), centre)
    meshtools.wobble(shelf, amount=0.030, scale=2.2, seed=6,
                     axis_bias=(1, 1, 0.3))
    meshtools.paint_by_normal(shelf, "f_grass_sun", "f_grass",
                              "f_grass_deep", up_at=0.80, down_at=-0.3)
    parts.append(shelf)

    # A retaining lip of stone round the outer edge, matching the mound.
    for index in range(16):
        angle = math.radians(-96.0 + 192.0 * index / 15.0) + bearing
        radius = 1.86
        stone = forms.superform(
            "ShelfEdge", "e_stone", exponent=3.0, segments=7, rings=5,
            size=(rng.uniform(0.36, 0.48), rng.uniform(0.34, 0.44),
                  rng.uniform(0.18, 0.23)),
            at=(centre[0] + math.cos(angle) * radius,
                centre[1] + math.sin(angle) * radius * 0.78,
                SHELF_H - 0.10))
        forms.jitter_verts(stone, 0.012, seed=500 + index)
        meshtools.paint_by_normal(stone, "e_stone_sun", "e_stone",
                                  "e_stone_deep", up_at=0.55, down_at=-0.3)
        parts.append(stone)
    for index in range(3):
        angle = math.tau * index / 3 + 1.1
        parts += F._tuft((centre[0] + math.cos(angle) * 1.25,
                          centre[1] + math.sin(angle) * 0.95, SHELF_H),
                         height=0.18, seed=520 + index)
    return parts


def _mound_steps(rng):
    """A short flight cut up the bank, for people rather than carts.

    ⛔ 27 degrees, which is a decision and not a look. Cut straight INTO the
    bank the run is only 2.2 m for a 2.15 m rise -- 44 degrees, which Godot
    would technically let Chuck walk and which would feel like climbing a
    ladder. Projecting the flight OUT from the bank buys 3.8 m of run. The
    landing halfway is there for the same reason a real flight has one.
    """
    parts = []
    bearing = math.radians(92.0)      # the far side from the cart track
    out = (math.cos(bearing), math.sin(bearing))
    across = (-out[1], out[0])
    treads = 13
    start_r = MOUND_BASE_R + 1.65

    for index in range(treads + 1):
        k = index / float(treads)
        # A landing a third of the way up: the flight pauses, then goes on.
        if 0.34 <= k <= 0.44:
            depth, lift = 0.86, SHELF_H
        else:
            depth, lift = 0.34, MOUND_H * k
        radius = start_r - (start_r - MOUND_TOP_R + 0.30) * k
        cx, cy = out[0] * radius, out[1] * radius
        tread = forms.loft("Tread", "e_stone", [
            (max(lift - 0.34, 0.0), [
                (cx + across[0] * 0.78 - out[0] * depth * 0.5,
                 cy + across[1] * 0.78 - out[1] * depth * 0.5),
                (cx - across[0] * 0.78 - out[0] * depth * 0.5,
                 cy - across[1] * 0.78 - out[1] * depth * 0.5),
                (cx - across[0] * 0.78 + out[0] * depth * 0.5,
                 cy - across[1] * 0.78 + out[1] * depth * 0.5),
                (cx + across[0] * 0.78 + out[0] * depth * 0.5,
                 cy + across[1] * 0.78 + out[1] * depth * 0.5)]),
            (lift, [
                (cx + across[0] * 0.76 - out[0] * depth * 0.5,
                 cy + across[1] * 0.76 - out[1] * depth * 0.5),
                (cx - across[0] * 0.76 - out[0] * depth * 0.5,
                 cy - across[1] * 0.76 - out[1] * depth * 0.5),
                (cx - across[0] * 0.76 + out[0] * depth * 0.5,
                 cy - across[1] * 0.76 + out[1] * depth * 0.5),
                (cx + across[0] * 0.76 + out[0] * depth * 0.5,
                 cy + across[1] * 0.76 + out[1] * depth * 0.5)]),
        ])
        forms.jitter_verts(tread, 0.009, seed=90 + index)
        meshtools.paint_by_normal(tread, "e_stone_sun", "e_stone",
                                  "e_stone_deep", up_at=0.7, down_at=-0.35)
        parts.append(tread)
        # Cheek walls either side, stepping with the flight.
        if index % 2 == 0 and index < treads:
            for side in (-1, 1):
                stone = forms.superform(
                    "Cheek", "e_stone", exponent=3.0, segments=7, rings=5,
                    size=(rng.uniform(0.34, 0.44), rng.uniform(0.34, 0.44),
                          rng.uniform(0.20, 0.26)),
                    at=(cx + across[0] * side * 0.92,
                        cy + across[1] * side * 0.92, lift + 0.16))
                forms.jitter_verts(stone, 0.012, seed=120 + index + side)
                parts.append(stone)
    return parts


def _cellar_door():
    """A root cellar in the bank. The last reason the mound is a mound.

    Tucked under the flight, where a real one would be: the steps give it a
    dry lintel and the bank gives it a cold store.
    """
    parts = []
    bearing = math.radians(214.0)
    out = (math.cos(bearing), math.sin(bearing))
    radius = MOUND_BASE_R - 0.45
    cx, cy = out[0] * radius, out[1] * radius
    yaw = math.degrees(bearing) + 90.0

    surround = forms.loft("CellarArch", "e_stone", [
        (0.0, RR(1.30, 0.55, 0.07, 4)),
        (0.92, RR(1.30, 0.55, 0.07, 4)),
        (1.12, RR(1.14, 0.55, 0.06, 4)),
        (1.30, RR(0.76, 0.55, 0.05, 4)),
        (1.42, RR(0.22, 0.55, 0.04, 4)),
    ], at=(cx, cy, 0.0))
    F._spin_z(surround, yaw, (cx, cy))
    meshtools.paint_by_normal(surround, "e_stone_sun", "e_stone",
                              "e_stone_deep", up_at=0.7, down_at=-0.35)
    parts.append(surround)

    door = forms.loft("CellarDoor", "s_wood", [
        (0.05, RR(0.98, 0.16, 0.05, 4)),
        (0.88, RR(0.98, 0.16, 0.05, 4)),
        (1.08, RR(0.84, 0.16, 0.04, 4)),
        (1.24, RR(0.46, 0.16, 0.04, 4)),
        (1.32, RR(0.12, 0.16, 0.03, 4)),
    ], at=(cx - out[0] * 0.24, cy - out[1] * 0.24, 0.0))
    F._spin_z(door, yaw, (cx, cy))
    meshtools.paint_by_normal(door, "s_wood", "s_wood", "s_wood_deep",
                              up_at=0.75, down_at=-0.4)
    parts.append(door)
    # Strap hinges and a ring handle: the marks of a door somebody opens.
    for dz in (0.28, 0.98):
        strap = forms.loft("Strap", "w_iron", [
            (dz, RR(0.92, 0.19, 0.03, 3)),
            (dz + 0.08, RR(0.92, 0.19, 0.03, 3)),
        ], at=(cx - out[0] * 0.27, cy - out[1] * 0.27, 0.0))
        F._spin_z(strap, yaw, (cx, cy))
        parts.append(strap)
    ring = meshtools.torus("Ring", "w_iron", major=0.085, minor=0.014,
                           at=(cx - out[0] * 0.34, cy - out[1] * 0.34, 0.66),
                           rot=(math.radians(90), 0, 0), major_seg=12,
                           minor_seg=5)
    F._spin_z(ring, yaw, (cx, cy))
    parts.append(ring)
    return parts


def _mound_top(rng):
    """The mill yard: flat, with a parapet to lean on and a bench to sit on.

    ⛔ FLAT is a requirement, not a style. The village scatters letter blocks
    up here and a block on a slope reads as a mistake.
    """
    parts = []
    # A parapet round the view side only -- a full ring would wall the yard
    # in and hide the thing you climbed up to see.
    for index in range(26):
        angle = math.radians(-172.0 + 150.0 * index / 25.0)
        radius = MOUND_TOP_R - 0.22
        for course, (dz, scale) in enumerate(((0.16, 1.0), (0.38, 0.86))):
            stone = forms.superform(
                "Parapet", "e_stone", exponent=3.0, segments=7, rings=5,
                size=(rng.uniform(0.34, 0.48) * scale,
                      rng.uniform(0.34, 0.46) * scale,
                      rng.uniform(0.18, 0.24)),
                at=(math.cos(angle) * radius, math.sin(angle) * radius,
                    MOUND_H + dz))
            forms.jitter_verts(stone, 0.012, seed=200 + index * 2 + course)
            meshtools.paint_by_normal(stone, "e_stone_sun", "e_stone",
                                      "e_stone_deep", up_at=0.55,
                                      down_at=-0.3)
            parts.append(stone)

    # Grain sacks by the mill door, and a hand-cart. The yard is a place of
    # WORK, which is the last thing that makes the mound look inhabited
    # rather than landscaped.
    for index, (x, y, lean_deg) in enumerate(((-1.45, 1.05, 4.0),
                                              (-0.95, 1.35, -6.0),
                                              (-1.70, 1.62, 2.0))):
        sack = forms.lathe("Sack", "v_sail", [
            (0.000, 0.00), (0.210, 0.00), (0.245, 0.18), (0.230, 0.44),
            (0.150, 0.60), (0.105, 0.66), (0.000, 0.64),
        ], segments=12, at=(x, y, MOUND_H))
        meshtools.lean(sack, degrees=lean_deg, axis="Y", pivot_z=MOUND_H)
        forms.jitter_verts(sack, 0.010, seed=140 + index)
        meshtools.paint_by_normal(sack, "v_sail", "v_sail", "h_straw_deep",
                                  up_at=0.7, down_at=-0.35)
        parts.append(sack)

    for wheel_side in (-1, 1):
        parts.append(meshtools.torus(
            "CartWheel", "s_wood_deep", major=0.300, minor=0.055,
            at=(1.95, 0.40 + wheel_side * 0.46, MOUND_H + 0.30),
            rot=(math.radians(90), 0, 0), major_seg=16, minor_seg=6))
    parts.append(forms.loft("CartBed", "s_wood", [
        (MOUND_H + 0.36, RR(1.20, 0.84, 0.06, 4)),
        (MOUND_H + 0.46, RR(1.24, 0.88, 0.06, 4)),
    ], at=(1.95, 0.40, 0.0)))
    for shaft in (-1, 1):
        parts.append(forms.sweep(
            "Shaft", "s_wood",
            [(1.40, 0.40 + shaft * 0.34, MOUND_H + 0.40),
             (0.52, 0.40 + shaft * 0.30, MOUND_H + 0.30)],
            [0.045, 0.038], segments=5))

    for index in range(5):
        angle = math.tau * index / 5 + 0.7
        parts += F._tuft((math.cos(angle) * (MOUND_TOP_R - 0.75),
                          math.sin(angle) * (MOUND_TOP_R - 0.75), MOUND_H),
                         height=0.20, seed=260 + index)
    return parts


# -------------------------------------------------------------------- run

SUBJECTS = {
    "windmill": lambda: produce("windmill", build_windmill(), budget_tris=14000),
    "bakery": lambda: produce("bakery", build_bakery(), budget_tris=9000),
    "clock_house": lambda: produce("clock_house", build_clock_house(),
                                   budget_tris=11000),
    "bookshop": lambda: produce("bookshop", build_bookshop(), budget_tris=9000),
    "flower_shop": lambda: produce("flower_shop", build_flower_shop(),
                                   budget_tris=16000),
    "workshop": lambda: produce("workshop", build_workshop(), budget_tris=12000),
    "well": lambda: produce_prop("well", build_well(), budget_tris=4500,
                                 texture=512),
    "fingerpost": lambda: produce_prop("fingerpost", build_fingerpost(),
                                       budget_tris=2500, texture=512),
    "bench": lambda: produce_prop("bench", build_bench(), budget_tris=1800,
                                  texture=512),
    "planter": lambda: produce_prop("planter", build_planter(),
                                    budget_tris=3000, texture=512),
    "bunting": lambda: produce_prop("bunting", build_bunting(),
                                    budget_tris=2200, texture=512),
    "tree_b": lambda: produce_prop("tree_b", build_tree_b(),
                                   budget_tris=5000, texture=1024),
    "bush": lambda: produce_prop("bush", build_bush(), budget_tris=3000,
                                 texture=512),
    "mushrooms": lambda: produce_prop("mushrooms", build_mushrooms(),
                                      budget_tris=2200, texture=512),
    "blossom": lambda: produce_prop("blossom", build_blossom(),
                                    budget_tris=2200, texture=512),
    "lane_stone": lambda: produce_prop("lane_stone", build_lane_stone(),
                                       budget_tris=400, texture=256),
    "wall_run": lambda: produce_prop("wall_run", build_wall_run(),
                                     budget_tris=4000, texture=512),
    "mill_mound": lambda: produce_prop("mill_mound", build_mill_mound(),
                                       budget_tris=16000, texture=1024),
    "annette": lambda: asset.produce(
        "village/annette", build_annette(), texture=asset.TEXTURE_MEDIUM,
        roughness=0.93, budget_tris=9000, bake_samples=26, smooth_angle=18.0,
        with_animation=True, animation_names=["idle", "walk"],
        gouache=F.SURFACE),
}


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    wanted = [a for a in args if a in SUBJECTS] or list(SUBJECTS)
    for name in wanted:
        print("[village] building", name)
        SUBJECTS[name]()
