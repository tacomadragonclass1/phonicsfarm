"""Direction 3 — Expressive sculptural contemporary.

    blender --background --python art_src/explore/d3_sculptural.py

The premise: moulded, confident, contemporary. Closer to a designed vinyl toy
or a modern mobile-game poster than to anything hand-made. Few shapes, each
one committed to. No fussy detail anywhere, because detail would weaken the
silhouette, and the silhouette is the whole point.

How the geometry differs from the other two:

  * Every surface is PLANAR-DECIMATED into facets and flat-shaded. Nothing is
    smooth. A form made of a dozen decided planes reads as carved and designed;
    the same form smooth-shaded reads as generic.
  * The tree is one sweeping arc of trunk carrying three big interlocking
    masses -- a graphic shape, nearly a logo, rather than a plant.
  * The cottage roof is ASYMMETRIC: the ridge is pushed off-centre so one
    plane runs long and shallow and the other is short and steep. That single
    decision does more than any amount of trim.
  * The block is a true squircle with a deep, crisply recessed panel.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (BLOCK_FACES, BLOCK_SIZE, CHUCK_HEIGHT, plaque_centre,  # noqa
                    produce)
from sb_lib import forms, meshtools, painter  # noqa: E402

D = "d3"
RR = forms.rounded_rect


def shift(outline, dx, dy=0.0):
    """Offset a loft station. Off-centre stations are what break symmetry."""
    return [(x + dx, y + dy) for x, y in outline]


# ------------------------------------------------------------------- tree

def build_tree():
    meshtools.reset_scene()
    parts = []

    # One decisive arc. The trunk is a gesture, not a post.
    trunk = forms.sweep("Trunk", "s_wood",
                        [(0.00, 0.00, 0.00), (0.06, 0.02, 0.45),
                         (0.22, 0.04, 0.95), (0.46, 0.04, 1.40),
                         (0.62, 0.02, 1.70)],
                        [0.26, 0.175, 0.125, 0.092, 0.072],
                        segments=9, samples=8)
    meshtools.paint_by_normal(trunk, "s_wood", "s_wood", "s_wood_deep",
                              down_at=-0.45)
    parts.append(trunk)

    # Three masses, deliberately different sizes, interlocking rather than
    # scattered. Faceted after joining so the planes cut across all three.
    # Built at LOW segment counts so each mass is already a polyhedron, and
    # NOT voxel-remeshed. Remeshing was tried and melted the three masses back
    # into one soft cloud -- the exact blob this direction exists to avoid.
    # Keeping the intersections visible is what makes it read as cut.
    canopy_parts = []
    for centre, size, exponent, segs, rngs in (
            ((0.44, 0.02, 2.00), (1.70, 1.38, 1.12), 2.5, 9, 6),
            ((-0.46, -0.20, 1.76), (1.10, 0.96, 0.86), 2.4, 8, 5),
            ((0.92, 0.28, 2.44), (0.96, 0.86, 0.80), 2.6, 7, 5)):
        canopy_parts.append(forms.superform(
            "Mass", "s_leaf", size=size, exponent=exponent,
            segments=segs, rings=rngs, at=centre))
    canopy = meshtools.join(canopy_parts, "Canopy")
    forms.facet(canopy, angle=6.0)
    meshtools.set_part_color(canopy, "s_leaf")
    meshtools.paint_by_normal(canopy, "s_leaf_light", "s_leaf", "s_leaf_deep",
                              up_at=0.62, down_at=-0.30)
    parts.append(canopy)

    tree = meshtools.join(parts, "Tree")
    meshtools.merge_doubles(tree)
    meshtools.drop_to_floor(tree)
    return [tree]


# ---------------------------------------------------------------- cottage

def build_cottage():
    meshtools.reset_scene()
    parts = []

    walls = forms.loft("Walls", "s_wall", [
        (0.00, RR(3.00, 2.50, 0.16, 4)),
        (1.86, RR(2.92, 2.44, 0.15, 4)),
    ])
    meshtools.paint_by_normal(walls, "s_wall", "s_wall", "s_wall_shade",
                              up_at=0.8, down_at=-0.6)
    parts.append(walls)

    # The ridge is pushed 0.62 off centre. One roof plane runs long and
    # shallow, the other short and steep, and the building stops being a box
    # with a hat on it.
    roof = forms.loft("Roof", "s_roof", [
        (1.74, shift(RR(3.52, 2.96, 0.14, 4), -0.10)),
        (1.96, shift(RR(3.34, 2.80, 0.13, 4), 0.06)),
        (2.66, shift(RR(2.26, 1.98, 0.11, 4), 0.52)),
        (3.30, shift(RR(1.10, 1.14, 0.09, 4), 0.92)),
        (3.78, shift(RR(0.22, 0.72, 0.06, 4), 1.14)),
    ], close_bottom=False)
    meshtools.paint_by_normal(roof, "s_roof", "s_roof", "s_roof_deep",
                              up_at=0.75, down_at=-0.2)
    parts.append(roof)

    chimney = forms.loft("Chimney", "s_stone", [
        (2.10, RR(0.46, 0.44, 0.07, 3)),
        (3.40, RR(0.42, 0.40, 0.07, 3)),
        (3.56, RR(0.60, 0.58, 0.08, 3)),
    ], at=(-1.02, 0.40, 0.0))
    parts.append(chimney)

    # A lean-to tucked under the long roof plane. One subordinate mass is what
    # stops the house reading as a single box, and it is cheaper in both
    # polygons and attention than any amount of applied trim.
    parts.append(forms.loft("LeanTo", "s_wall_shade", [
        (0.00, RR(1.30, 1.70, 0.12, 4)),
        (1.18, RR(1.26, 1.66, 0.12, 4)),
    ], at=(1.98, 0.22, 0.0)))
    parts.append(forms.loft("LeanRoof", "s_roof_deep", [
        (1.10, RR(1.60, 2.00, 0.14, 4)),
        (1.52, RR(1.12, 1.52, 0.11, 4)),
    ], at=(2.02, 0.22, 0.0), close_bottom=False))

    front = -1.26
    # One strong arch. Nothing else on the front wall competes with it.
    door = forms.loft("Door", "s_blue", [
        (0.0, RR(0.86, 0.22, 0.05, 3)),
        (1.00, RR(0.86, 0.22, 0.05, 3)),
        (1.34, RR(0.70, 0.22, 0.05, 3)),
        (1.52, RR(0.30, 0.22, 0.04, 3)),
    ], at=(-0.42, front, 0.0))
    parts.append(door)
    parts.append(forms.superform("Knob", "s_accent", size=(0.12, 0.12, 0.12),
                                 exponent=3.0, segments=10, rings=8,
                                 at=(-0.10, front - 0.10, 0.80)))
    parts.append(forms.loft("Step", "s_stone", [
        (0.0, RR(1.40, 0.70, 0.12, 3)),
        (0.16, RR(1.26, 0.58, 0.11, 3)),
    ], at=(-0.42, front - 0.34, 0.0)))

    # Two windows, same shape, different sizes: rhythm without clutter.
    for x_pos, z_pos, scale in ((0.86, 1.14, 1.0), (-1.50, 1.20, 0.78)):
        side = abs(x_pos) > 1.4
        parts += _window(x_pos, front if not side else -0.30, z_pos, scale,
                         side)

    cottage = meshtools.join(parts, "Cottage")
    meshtools.merge_doubles(cottage)
    forms.facet(cottage, angle=11.0)
    meshtools.drop_to_floor(cottage)
    return [cottage]


def _window(x_pos, y_pos, z_pos, scale, on_side):
    w, h = 0.72 * scale, 0.78 * scale
    if on_side:
        frame = RR(0.18, w, 0.04, 3)
        pane = RR(0.10, w - 0.20, 0.03, 3)
        at_frame = (-1.50, y_pos, 0.0)
        at_pane = (-1.56, y_pos, 0.0)
    else:
        frame = RR(w, 0.18, 0.04, 3)
        pane = RR(w - 0.20, 0.10, 0.03, 3)
        at_frame = (x_pos, y_pos, 0.0)
        at_pane = (x_pos, y_pos - 0.06, 0.0)
    return [
        forms.loft("WinFrame", "s_accent", [
            (z_pos - h / 2, frame), (z_pos + h / 2, frame)], at=at_frame),
        forms.loft("Pane", "s_wood_deep", [
            (z_pos - h / 2 + 0.09, pane), (z_pos + h / 2 - 0.09, pane)],
            at=at_pane),
    ]


# ------------------------------------------------------------------ chuck

def build_chuck():
    meshtools.reset_scene()
    parts = []
    head_z = 1.095

    for side in (-1, 1):
        parts.append(forms.superform(
            "Boot", "s_accent", size=(0.205, 0.30, 0.175), exponent=3.6,
            segments=14, rings=10, at=(side * 0.112, -0.040, 0.088)))
        parts.append(forms.sweep(
            "Leg", "s_blue",
            [(side * 0.112, 0.0, 0.12), (side * 0.108, 0.0, 0.36),
             (side * 0.104, 0.0, 0.56)],
            [0.088, 0.076, 0.080], segments=9, samples=5))

    # A bold wedge: wide shoulders falling to a narrow waist. Vinyl-toy
    # proportion, committed to rather than averaged.
    body = forms.loft("Body", "s_leaf", [
        (0.46, RR(0.34, 0.26, 0.10, 4)),
        (0.62, RR(0.40, 0.30, 0.11, 4)),
        (0.84, RR(0.50, 0.34, 0.13, 4)),
        (0.96, RR(0.46, 0.32, 0.12, 4)),
        (1.01, RR(0.26, 0.22, 0.08, 4)),
    ])
    parts.append(body)
    parts.append(forms.loft("Band", "s_cream", [
        (0.66, RR(0.42, 0.32, 0.11, 4)),
        (0.74, RR(0.42, 0.32, 0.11, 4)),
    ]))

    for side in (-1, 1):
        parts.append(forms.sweep(
            "Arm", "s_leaf",
            [(side * 0.215, 0.0, 0.92), (side * 0.272, -0.02, 0.74),
             (side * 0.282, -0.05, 0.56)],
            [0.078, 0.066, 0.060], segments=9, samples=5))
        parts.append(forms.superform(
            "Hand", "s_skin", size=(0.125, 0.130, 0.112), exponent=3.0,
            segments=11, rings=8, at=(side * 0.284, -0.062, 0.520)))

    head = forms.superform("Head", "s_skin", size=(0.430, 0.390, 0.455),
                           exponent=3.0, segments=22, rings=16,
                           at=(0, 0, head_z))
    forms.press(head, "Y", plane=-0.162, amount=0.48, radius=0.27,
                centre=(0, -0.20, head_z))
    parts.append(head)
    parts.append(forms.sweep("Neck", "s_skin", [(0, 0, 0.96), (0, 0, 1.03)],
                             [0.086, 0.082], segments=10))

    # Hair as one bold moulded cap with a hard front edge.
    hair = forms.superform("Hair", "s_hair", size=(0.452, 0.410, 0.330),
                           exponent=3.4, segments=20, rings=14,
                           at=(0.0, 0.030, head_z + 0.130))
    forms.press(hair, "Y", plane=-0.110, amount=0.36, radius=0.25,
                centre=(0, -0.19, head_z + 0.09))
    parts.append(hair)

    for side in (-1, 1):
        parts.append(meshtools.torus(
            "Rim", "s_ink", major=0.088, minor=0.016,
            at=(side * 0.100, -0.166, head_z + 0.010),
            rot=(math.radians(90), 0, 0), major_seg=16, minor_seg=6))
        parts.append(forms.superform(
            "Lens", "s_cream", size=(0.156, 0.022, 0.156), exponent=2.2,
            segments=14, rings=8, at=(side * 0.100, -0.160, head_z + 0.010)))
        parts.append(forms.superform(
            "Eye", "s_ink", size=(0.058, 0.028, 0.068), exponent=2.3,
            segments=10, rings=8, at=(side * 0.100, -0.174, head_z + 0.010)))
    parts.append(forms.sweep(
        "Bridge", "s_ink", [(-0.060, -0.168, head_z + 0.030),
                            (0.060, -0.168, head_z + 0.030)],
        [0.014, 0.014], segments=7))
    parts.append(forms.superform(
        "Nose", "s_skin", size=(0.062, 0.058, 0.052), exponent=2.8,
        segments=10, rings=8, at=(0, -0.176, head_z - 0.066)))
    # A WIDE, THIN lozenge sunk into the face. A small round pad standing proud
    # of the chin read as a smudge at every size that matters.
    parts.append(forms.superform(
        "Mouth", "s_ink", size=(0.156, 0.030, 0.042), exponent=2.6,
        segments=14, rings=8, at=(0, -0.164, head_z - 0.142)))

    chuck = meshtools.join(parts, "Chuck")
    meshtools.merge_doubles(chuck)
    forms.facet(chuck, angle=9.0)
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

    # A true squircle: one dial between a cube and a sphere, set where a
    # moulded toy sits. Not a cube with its edges filed off.
    body = forms.superform("Cube", "s_blue", size=(BLOCK_SIZE,) * 3,
                           exponent=3.6, segments=28, rings=20,
                           at=(0, 0, half))
    meshtools.paint_by_normal(body, "s_blue", "s_blue", "s_wood_deep",
                              up_at=0.95, down_at=-0.75)

    plaques, wells = [], []
    thickness = 0.070
    for name, normal in BLOCK_FACES:
        centre = plaque_centre(normal, thickness)
        # A deep, crisp WELL sunk into the squircle, with the label sitting in
        # the bottom of it. The shadow line round the rim is the whole look.
        well_centre = plaque_centre(normal, thickness * 2.1)
        if normal[2] > 0.5:
            size, well = (0.500, 0.500, thickness), (0.590, 0.590, thickness * 2.1)
        elif abs(normal[0]) > 0.5:
            size, well = (thickness, 0.500, 0.500), (thickness * 2.1, 0.590, 0.590)
        else:
            size, well = (0.500, thickness, 0.500), (0.590, thickness * 2.1, 0.590)
        wells.append(forms.superform(name + "Well", "s_wood_deep", size=well,
                                     exponent=8.0, segments=14, rings=10,
                                     at=well_centre))
        plaques.append(forms.superform(name, "s_cream", size=size,
                                       exponent=8.0, segments=14, rings=10,
                                       at=centre))

    cream = painter.flat_material("d3_block_face", "s_cream", roughness=0.90)
    painter.assign(plaques, cream)
    body = meshtools.join([body] + wells, "Cube")
    forms.facet(body, angle=7.0)
    return [body] + plaques


# -------------------------------------------------------------------- run

if __name__ == "__main__":
    produce(D, "tree", build_tree(), budget_tris=3200, bake_samples=22)
    produce(D, "cottage", build_cottage(), budget_tris=4000, bake_samples=24)
    produce(D, "chuck", build_chuck(), budget_tris=5000, bake_samples=24)
    produce(D, "block", build_block(), texture=512, budget_tris=3400,
            bake_samples=28)
