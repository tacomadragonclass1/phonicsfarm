"""Direction 2 — Dimensional painted storybook.

    blender --background --python art_src/explore/d2_storybook.py

The premise: a page from a picture book, given depth. Every form comes from
DRAWING logic rather than modelling logic -- shapes are tall, they lean, they
taper the way a loaded brush tapers, and depth is deliberately shallow so each
object reads first as a silhouette on a page.

How the geometry differs from phase 1 AND from direction 1:

  * The trunk is one calligraphic STROKE: an S-curve swept with a radius that
    runs 0.21 down to 0.03, flattened across its depth so it reads like a
    brush mark rather than a pipe.
  * The canopy is six thin layered PADS fanned across the stroke, each a
    different green, like cut and painted paper stacked with the edges
    showing. Flat, not inflated.
  * The cottage is TALL and NARROW with a jettied upper storey that overhangs
    the ground floor, a battered base, and a concave roof with a flared eave.
    It leans 2.5 degrees. Nothing in it is square to anything else.
  * Dark trim pieces are modelled along the eaves and openings -- an actual
    drawn line in the geometry, backed by an edge_dark of 0.38 in the bake,
    which is four times anything else in the project.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (BLOCK_FACES, BLOCK_SIZE, CHUCK_HEIGHT, plaque_centre,  # noqa
                    produce)
from sb_lib import forms, meshtools, painter  # noqa: E402

D = "d2"
RR = forms.rounded_rect


# ------------------------------------------------------------------- tree

def build_tree():
    meshtools.reset_scene()
    parts = []

    # One stroke, drawn from the ground up: lean out, recover, whip thin.
    stroke = [(0.00, 0.00, 0.00), (0.10, 0.03, 0.55), (-0.02, -0.02, 1.05),
              (0.16, 0.05, 1.55), (0.34, 0.02, 1.95), (0.30, 0.0, 2.20)]
    trunk = forms.sweep("Trunk", "g_timber", stroke,
                        [0.215, 0.135, 0.098, 0.072, 0.045, 0.028],
                        segments=9, samples=7, profile_squash=0.72)
    meshtools.paint_by_normal(trunk, "g_timber", "g_timber", "g_ink",
                              down_at=-0.45)
    parts.append(trunk)

    for origin, tip, radius in (((0.02, 0.0, 1.10), (-0.62, -0.10, 1.52), 0.055),
                                ((0.20, 0.0, 1.70), (0.74, 0.12, 1.92), 0.048)):
        parts.append(forms.sweep(
            "Branch", "g_timber",
            [origin, ((origin[0] + tip[0]) / 2, (origin[1] + tip[1]) / 2,
                      (origin[2] + tip[2]) / 2 + 0.07), tip],
            [radius, radius * 0.7, radius * 0.4], segments=7, samples=5,
            profile_squash=0.8))

    # Layered painted paper. Thin, fanned, each layer its own green, edges
    # showing -- this is the opposite of a volume made of spheres.
    layers = [
        ((-0.58, 0.16, 1.52), 0.74, "g_leaf_deep", 7, (14.0, -16.0)),
        ((0.62, -0.10, 1.86), 0.66, "g_leaf", 6, (-10.0, 18.0)),
        ((-0.18, -0.26, 1.98), 0.80, "g_leaf", 8, (16.0, -6.0)),
        ((0.34, 0.26, 2.22), 0.70, "g_leaf_light", 7, (-12.0, 8.0)),
        ((-0.34, 0.06, 2.42), 0.56, "g_leaf", 6, (10.0, -10.0)),
        ((0.20, -0.12, 2.60), 0.46, "g_leaf_light", 5, (-8.0, 6.0)),
    ]
    for centre, radius, colour, lobes, tilt in layers:
        parts.append(forms.pad(
            "Leaf", colour, radius=radius, lobes=lobes, amplitude=0.20,
            dome=0.075, underside=0.055, points=34, at=centre, tilt=tilt))

    tree = meshtools.join(parts, "Tree")
    meshtools.merge_doubles(tree)
    meshtools.drop_to_floor(tree)
    return [tree]


# ---------------------------------------------------------------- cottage

def build_cottage():
    meshtools.reset_scene()
    parts = []

    # Tall, narrow, and JETTIED: the upper storey overhangs the lower one at
    # z = 1.32. A storybook house is drawn top-heavy on purpose.
    walls = forms.loft("Walls", "g_wall", [
        (0.00, RR(2.34, 2.04, 0.11, 4)),
        (0.20, RR(2.14, 1.86, 0.10, 4)),
        (1.24, RR(2.08, 1.80, 0.10, 4)),
        (1.34, RR(2.46, 2.14, 0.11, 4)),
        (2.22, RR(2.38, 2.06, 0.11, 4)),
    ])
    meshtools.paint_by_normal(walls, "g_wall", "g_wall", "g_wall_shade",
                              down_at=-0.6)
    parts.append(walls)

    # The jetty needs a drawn line under it or it reads as a modelling glitch.
    parts.append(forms.loft("Jetty", "g_timber", [
        (1.26, RR(2.14, 1.86, 0.10, 4)),
        (1.36, RR(2.50, 2.18, 0.11, 4)),
    ], close_bottom=False, close_top=False))

    parts.append(forms.loft("Sill", "g_timber", [
        (0.00, RR(2.52, 2.22, 0.12, 4)),
        (0.16, RR(2.34, 2.04, 0.11, 4)),
    ]))

    # Concave roof with a flared eave -- the line sweeps out before it turns up.
    roof = forms.loft("Roof", "g_roof", [
        (2.10, RR(3.44, 3.08, 0.16, 4)),
        (2.36, RR(3.02, 2.72, 0.14, 4)),
        (2.84, RR(2.36, 2.12, 0.12, 4)),
        (3.26, RR(1.58, 1.44, 0.10, 4)),
        (3.56, RR(0.78, 0.74, 0.08, 4)),
        (3.76, RR(0.20, 0.40, 0.05, 4)),
    ], close_bottom=False)
    meshtools.paint_by_normal(roof, "g_roof", "g_roof", "g_roof_deep",
                              up_at=0.85, down_at=-0.2)
    parts.append(roof)

    parts.append(forms.loft("Fascia", "g_roof_deep", [
        (2.06, RR(3.30, 2.98, 0.15, 4)),
        (2.20, RR(3.28, 2.96, 0.15, 4)),
    ], close_bottom=False, close_top=False))

    chimney = forms.loft("Chimney", "g_roof_deep", [
        (2.42, RR(0.42, 0.40, 0.05, 3)),
        (3.66, RR(0.38, 0.36, 0.05, 3)),
        (3.78, RR(0.52, 0.50, 0.06, 3)),
        (3.92, RR(0.48, 0.46, 0.06, 3)),
    ], at=(0.86, 0.52, 0.0))
    meshtools.lean(chimney, degrees=5.0, axis="Y", pivot_z=2.42)
    parts.append(chimney)

    front = -1.06
    door = forms.loft("Door", "g_teal", [
        (0.06, RR(0.62, 0.14, 0.04, 3)),
        (1.20, RR(0.62, 0.14, 0.04, 3)),
        (1.40, RR(0.44, 0.14, 0.04, 3)),
        (1.50, RR(0.12, 0.14, 0.03, 3)),
    ], at=(-0.46, front, 0.0))
    parts.append(door)
    parts.append(forms.loft("DoorTrim", "g_ink", [
        (0.0, RR(0.80, 0.16, 0.04, 3)),
        (1.26, RR(0.80, 0.16, 0.04, 3)),
        (1.50, RR(0.56, 0.16, 0.04, 3)),
        (1.62, RR(0.14, 0.16, 0.03, 3)),
    ], at=(-0.46, front + 0.035, 0.0)))
    parts.append(forms.superform("Knob", "g_mustard", size=(0.09, 0.09, 0.09),
                                 exponent=2.6, segments=10, rings=8,
                                 at=(-0.20, front - 0.06, 0.74)))

    for x_pos, z_pos in ((0.52, 0.78), (0.52, 1.80), (-0.48, 1.80)):
        parts += _window(x_pos, front - 0.02 if z_pos < 1.3 else front - 0.18,
                         z_pos)

    cottage = meshtools.join(parts, "Cottage")
    meshtools.merge_doubles(cottage)
    # The whole house leans. Drawn houses are never plumb.
    meshtools.lean(cottage, degrees=2.4, axis="Y", pivot_z=0.0)
    meshtools.drop_to_floor(cottage)
    return [cottage]


def _window(x_pos, y_pos, z_pos):
    parts = []
    parts.append(forms.loft("WinTrim", "g_ink", [
        (z_pos - 0.44, RR(0.52, 0.12, 0.03, 3)),
        (z_pos + 0.30, RR(0.52, 0.12, 0.03, 3)),
        (z_pos + 0.44, RR(0.30, 0.12, 0.03, 3)),
    ], at=(x_pos, y_pos, 0.0)))
    parts.append(forms.loft("Pane", "g_wall_shade", [
        (z_pos - 0.36, RR(0.38, 0.08, 0.02, 3)),
        (z_pos + 0.26, RR(0.38, 0.08, 0.02, 3)),
        (z_pos + 0.36, RR(0.22, 0.08, 0.02, 3)),
    ], at=(x_pos, y_pos - 0.045, 0.0)))
    for side in (-1, 1):
        parts.append(forms.loft("Shutter", "g_mustard", [
            (z_pos - 0.42, RR(0.22, 0.07, 0.02, 3)),
            (z_pos + 0.34, RR(0.22, 0.07, 0.02, 3)),
        ], at=(x_pos + side * 0.37, y_pos - 0.055, 0.0)))
    return parts


# ------------------------------------------------------------------ chuck

def build_chuck():
    meshtools.reset_scene()
    parts = []
    head_z = 1.055

    for side in (-1, 1):
        parts.append(forms.superform(
            "Shoe", "g_mustard", size=(0.165, 0.30, 0.135), exponent=3.0,
            segments=14, rings=10, at=(side * 0.095, -0.050, 0.068)))
        parts.append(forms.sweep(
            "Leg", "g_skin",
            [(side * 0.095, -0.005, 0.09), (side * 0.092, 0.0, 0.32),
             (side * 0.090, 0.0, 0.52)],
            [0.072, 0.063, 0.066], segments=9, samples=5))

    # A drawn body: a simple swinging shape, wider at the hem than the chest,
    # with the depth kept shallow so it reads as a shape on a page.
    body = forms.loft("Body", "g_teal", [
        (0.44, forms.ngon(18, 0.215, squash=0.78)),
        (0.56, forms.ngon(18, 0.212, squash=0.78)),
        (0.74, forms.ngon(18, 0.196, squash=0.78)),
        (0.88, forms.ngon(18, 0.168, squash=0.78)),
        (0.96, forms.ngon(18, 0.118, squash=0.78)),
    ])
    parts.append(body)
    parts.append(forms.pad("Hem", "g_ink", radius=0.228, lobes=1,
                           amplitude=0.0, dome=0.018, underside=0.030,
                           points=22, at=(0, 0, 0.45)))
    parts.append(forms.loft("Collar", "g_paper", [
        (0.93, forms.ngon(16, 0.132, squash=0.80)),
        (0.99, forms.ngon(16, 0.108, squash=0.80)),
    ]))

    for side in (-1, 1):
        parts.append(forms.sweep(
            "Arm", "g_teal",
            [(side * 0.165, 0.0, 0.90), (side * 0.224, -0.03, 0.70),
             (side * 0.236, -0.07, 0.50)],
            [0.068, 0.059, 0.053], segments=9, samples=5))
        parts.append(forms.superform(
            "Hand", "g_skin", size=(0.098, 0.106, 0.092), exponent=2.6,
            segments=11, rings=8, at=(side * 0.238, -0.080, 0.465)))

    # A big round drawn head, flattened front and back.
    head = forms.superform("Head", "g_skin", size=(0.415, 0.355, 0.430),
                           exponent=2.5, segments=22, rings=16,
                           at=(0, 0, head_z))
    forms.press(head, "Y", plane=-0.150, amount=0.40, radius=0.27,
                centre=(0, -0.18, head_z))
    parts.append(head)
    parts.append(forms.sweep("Neck", "g_skin", [(0, 0, 0.92), (0, 0, 0.99)],
                             [0.072, 0.068], segments=10))

    # Hair as a DRAWN SHAPE: one solid mass pressed back off the face, with
    # three tufts breaking the outline at the crown. A flat pad was tried and
    # hung over the brow, hiding the glasses -- its rim is its widest part.
    hair = forms.superform("Hair", "g_hair", size=(0.455, 0.400, 0.315),
                           exponent=2.7, segments=20, rings=14,
                           at=(0.0, 0.038, head_z + 0.150))
    forms.press(hair, "Y", plane=-0.082, amount=0.44, radius=0.26,
                centre=(0, -0.175, head_z + 0.10))
    parts.append(hair)
    for offset, lean_x, size in ((-0.145, -26.0, 0.105), (0.02, 6.0, 0.125),
                                 (0.155, 24.0, 0.098)):
        parts.append(forms.pad(
            "Tuft", "g_hair", radius=size, lobes=3, amplitude=0.26,
            dome=0.075, underside=0.085, points=16,
            at=(offset, 0.055, head_z + 0.295), tilt=(10.0, lean_x)))

    for side in (-1, 1):
        parts.append(meshtools.torus(
            "Rim", "g_ink", major=0.082, minor=0.0135,
            at=(side * 0.094, -0.152, head_z + 0.012),
            rot=(math.radians(90), 0, 0), major_seg=18, minor_seg=6))
        parts.append(forms.superform(
            "Lens", "g_paper", size=(0.146, 0.020, 0.146), exponent=2.1,
            segments=14, rings=8, at=(side * 0.094, -0.146, head_z + 0.012)))
        parts.append(forms.superform(
            "Eye", "g_ink", size=(0.052, 0.026, 0.062), exponent=2.2,
            segments=10, rings=8, at=(side * 0.094, -0.160, head_z + 0.012)))
    parts.append(forms.sweep(
        "Bridge", "g_ink", [(-0.056, -0.154, head_z + 0.030),
                            (0.056, -0.154, head_z + 0.030)],
        [0.012, 0.012], segments=7))
    parts.append(forms.superform(
        "Nose", "g_skin", size=(0.056, 0.055, 0.048), exponent=2.6,
        segments=10, rings=8, at=(0, -0.164, head_z - 0.062)))
    # A WIDE, THIN lozenge sunk into the face. A small round pad standing proud
    # of the chin read as a smudge at every size that matters.
    parts.append(forms.superform(
        "Mouth", "g_ink", size=(0.142, 0.028, 0.038), exponent=2.6,
        segments=14, rings=8, at=(0, -0.152, head_z - 0.134)))

    chuck = meshtools.join(parts, "Chuck")
    meshtools.merge_doubles(chuck)
    meshtools.drop_to_floor(chuck)
    _scale_to_height(chuck, CHUCK_HEIGHT)
    return [chuck]


def _scale_to_height(obj, height):
    low, high = meshtools.bounds(obj)
    factor = height / max(high.z - low.z, 1e-6)
    for vert in obj.data.vertices:
        vert.co *= factor
    meshtools.drop_to_floor(obj)


# ------------------------------------------------------------------ block

def build_block():
    meshtools.reset_scene()
    half = BLOCK_SIZE / 2

    # Crisp painted faces, worn corners: a printed block, not a carved one.
    body = forms.superform("Cube", "g_roof", size=(BLOCK_SIZE,) * 3,
                           exponent=7.0, segments=26, rings=18,
                           at=(0, 0, half))
    forms.jitter_verts(body, 0.0025, seed=51)
    meshtools.paint_by_normal(body, "g_roof", "g_roof", "g_roof_deep",
                              up_at=0.92, down_at=-0.6)

    plaques, trims = [], []
    thickness = 0.040
    for name, normal in BLOCK_FACES:
        centre = plaque_centre(normal, thickness)
        # The ink border has to sit BEHIND the label, not level with it.
        # Coplanar, the larger trim simply won the depth test and every face
        # of the block came out solid black.
        trim_centre = tuple(
            c - n * 0.016 for c, n in
            zip(plaque_centre(normal, thickness * 0.55), normal))
        if normal[2] > 0.5:
            size = (0.560, 0.560, thickness)
            trim = (0.640, 0.640, thickness * 0.55)
        elif abs(normal[0]) > 0.5:
            size = (thickness, 0.560, 0.560)
            trim = (thickness * 0.55, 0.640, 0.640)
        else:
            size = (0.560, thickness, 0.560)
            trim = (0.640, thickness * 0.55, 0.640)
        # An INK BORDER drawn round every label. The printed-block cue.
        trims.append(forms.superform(name + "Trim", "g_ink", size=trim,
                                     exponent=6.5, segments=14, rings=10,
                                     at=trim_centre))
        plaques.append(forms.superform(name, "g_paper", size=size,
                                       exponent=6.5, segments=14, rings=10,
                                       at=centre))

    paper = painter.flat_material("d2_block_face", "g_paper", roughness=0.98)
    painter.assign(plaques, paper)
    # Trims are baked with the body, so only the five plaques carry the flat
    # material alphabet_block.gd will duplicate.
    body = meshtools.join([body] + trims, "Cube")
    return [body] + plaques


# -------------------------------------------------------------------- run

if __name__ == "__main__":
    produce(D, "tree", build_tree(), budget_tris=3400, bake_samples=22)
    produce(D, "cottage", build_cottage(), budget_tris=5200, bake_samples=24)
    produce(D, "chuck", build_chuck(), budget_tris=5400, bake_samples=24)
    produce(D, "block", build_block(), texture=512, budget_tris=3200,
            bake_samples=28)
