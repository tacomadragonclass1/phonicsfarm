"""Direction 1 — Handcrafted sculpted miniature.

    blender --background --python art_src/explore/d1_handcrafted.py

The premise: somebody made this world on a table, out of clay and carved wood,
and we are photographing it. Everything is a bit squat and a bit heavy because
clay sags. Nothing is symmetrical because hands are not. Edges are soft,
creases hold deep shadow, and there is no sheen anywhere.

How the geometry differs from phase 1:

  * The trunk is a REVOLVED SILHOUETTE, not a cone. It swells at the foot,
    pinches above the roots, carries a knot at mid-height and tapers out --
    seven drawn numbers that a cone cannot express.
  * The canopy is four pressed PADS on visible branches, arranged like a
    cloud-pruned bonsai, not a cluster of spheres. Each pad has a scalloped
    drawn edge and a flattened top.
  * The cottage walls are LOFTED: the plan bulges outward at waist height and
    pulls back in under the eaves, the way a coil-built pot does.
  * The roof is a scalloped thatch that droops past the walls, built as a
    stack of wavy outlines rather than as two flat slabs.
  * The block is a SUPERELLIPSOID with knuckle dents, not a bevelled cube.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (BLOCK_FACES, BLOCK_SIZE, CHUCK_HEIGHT, plaque_centre,  # noqa
                    produce)
from sb_lib import forms, meshtools, painter  # noqa: E402

D = "d1"


# ------------------------------------------------------------------- tree

def build_tree():
    meshtools.reset_scene()
    parts = []

    trunk = forms.lathe("Trunk", "c_wood", [
        (0.34, 0.00),   # root flare spreading into the ground
        (0.24, 0.12),
        (0.182, 0.32),
        (0.152, 0.62),
        (0.166, 0.88),  # a knot, where a branch was lost
        (0.132, 1.14),
        (0.124, 1.40),
        (0.098, 1.62),
    ], segments=14, smooth_profile=5)
    meshtools.bend(trunk, degrees=19.0, bottom_z=0.0, top_z=1.62, axis="Y")
    forms.dents(trunk, [(0.14, 0.05, 0.55), (-0.12, -0.1, 0.95),
                        (0.05, 0.16, 1.25)], depth=0.030, radius=0.20)
    forms.jitter_verts(trunk, 0.004, seed=3)
    meshtools.paint_by_normal(trunk, "c_wood", "c_wood", "c_wood_deep",
                              down_at=-0.5)
    parts.append(trunk)

    # Pads sit on branches that can be SEEN. A canopy floating on a bare stick
    # is the asset-pack tell; a visible armature is what makes it sculpted.
    pads = [
        ((-0.60, 0.12, 1.30), 0.62, 5, 17.0, -8.0),
        ((0.56, -0.24, 1.58), 0.56, 4, -12.0, 10.0),
        ((0.02, 0.40, 1.94), 0.66, 6, 7.0, 4.0),
        ((-0.44, -0.30, 2.14), 0.48, 5, -9.0, -10.0),
        ((0.34, 0.08, 2.36), 0.42, 4, 10.0, 6.0),
    ]
    for index, (centre, radius, lobes, tilt_x, tilt_y) in enumerate(pads):
        branch_from = (centre[0] * 0.18, centre[1] * 0.18,
                       centre[2] - 0.34 + index * 0.02)
        branch = forms.sweep(
            "Branch", "c_wood",
            [branch_from,
             (centre[0] * 0.55, centre[1] * 0.55, centre[2] - 0.20),
             (centre[0] * 0.85, centre[1] * 0.85, centre[2] - 0.06)],
            [0.072, 0.052, 0.034], segments=7, samples=5)
        parts.append(branch)

        # Amplitude stays LOW. At 0.17 with seven lobes the pads read as
        # cut-out oak leaves; clay pressed into a pad has a soft wavy rim, not
        # a die-cut one.
        leaf = forms.pad("Pad", "c_leaf", radius=radius, lobes=lobes,
                         amplitude=0.095, dome=0.26, underside=0.17,
                         points=30, at=centre, tilt=(tilt_x, tilt_y))
        # A thumb across the top. Clay foliage is pressed, never inflated.
        forms.press(leaf, "Z", plane=centre[2] + 0.16, amount=0.30,
                    radius=radius * 0.75, centre=centre)
        forms.jitter_verts(leaf, 0.010, seed=40 + index)
        meshtools.paint_by_normal(leaf, "c_leaf_light", "c_leaf",
                                  "c_leaf_deep", up_at=0.80, down_at=-0.35)
        parts.append(leaf)

    tree = meshtools.join(parts, "Tree")
    meshtools.merge_doubles(tree)
    meshtools.drop_to_floor(tree)
    return [tree]


# ---------------------------------------------------------------- cottage

def build_cottage():
    meshtools.reset_scene()
    parts = []

    # Coil-built walls: the plan BULGES at waist height and draws back in
    # under the eaves. A lofted stack of outlines can say that; a box cannot.
    walls = forms.loft("Walls", "c_oat", [
        (0.00, forms.rounded_rect(3.30, 2.78, 0.50, 5)),
        (0.16, forms.rounded_rect(3.14, 2.62, 0.47, 5)),
        (0.70, forms.rounded_rect(3.26, 2.74, 0.50, 5)),
        (1.28, forms.rounded_rect(3.18, 2.66, 0.48, 5)),
        (1.78, forms.rounded_rect(2.96, 2.46, 0.44, 5)),
    ])
    forms.jitter_verts(walls, 0.008, seed=11)
    meshtools.paint_by_normal(walls, "c_oat", "c_oat", "c_oat_deep",
                              down_at=-0.6)
    parts.append(walls)

    plinth = forms.loft("Plinth", "c_stone", [
        (-0.02, forms.rounded_rect(3.56, 3.02, 0.56, 5)),
        (0.17, forms.rounded_rect(3.34, 2.82, 0.52, 5)),
    ])
    forms.jitter_verts(plinth, 0.010, seed=12)
    parts.append(plinth)

    # Thatch: a stack of wavy outlines that droops past the walls. The scallop
    # is the eave, so the roof ends in a soft hand-cut fringe.
    thatch_stations = [
        (1.46, forms.scallop_ring(2.18, 9, 0.052, 34, squash=0.86)),
        (1.86, forms.scallop_ring(2.04, 9, 0.046, 34, squash=0.86)),
        (2.34, forms.scallop_ring(1.62, 9, 0.040, 34, squash=0.86)),
        (2.80, forms.scallop_ring(1.02, 9, 0.034, 34, squash=0.86)),
        (3.14, forms.scallop_ring(0.44, 9, 0.028, 34, squash=0.86)),
        (3.28, forms.scallop_ring(0.12, 9, 0.020, 34, squash=0.86)),
    ]
    thatch = forms.loft("Thatch", "c_straw", thatch_stations,
                        close_bottom=False)
    forms.jitter_verts(thatch, 0.012, seed=13)
    meshtools.paint_by_normal(thatch, "c_straw", "c_straw", "c_straw_deep",
                              up_at=0.75, down_at=-0.25)
    parts.append(thatch)

    chimney = forms.lathe("Chimney", "c_stone", [
        (0.27, 0.00), (0.24, 0.42), (0.215, 0.92),
        (0.30, 1.04), (0.275, 1.16),
    ], segments=12, smooth_profile=4, at=(0.95, 0.52, 2.05))
    meshtools.bend(chimney, degrees=11.0, bottom_z=2.05, top_z=3.21, axis="X")
    forms.jitter_verts(chimney, 0.009, seed=14)
    parts.append(chimney)

    # Door: a pressed slab with a lens arch on top.
    front = -1.34
    door = forms.superform("Door", "c_red", size=(0.80, 0.16, 1.18),
                           exponent=5.5, segments=16, rings=12,
                           at=(-0.46, front, 0.61))
    forms.press(door, "Y", plane=front - 0.07, amount=0.5, radius=0.8,
                centre=(-0.46, front, 0.61))
    parts.append(door)
    arch = forms.pad("DoorArch", "c_red", radius=0.405, lobes=1,
                     amplitude=0.0, dome=0.075, underside=0.075, points=22,
                     at=(-0.46, front - 0.001, 1.18), tilt=(90.0, 0.0))
    parts.append(arch)
    knob = forms.superform("Knob", "c_butter", size=(0.10, 0.09, 0.10),
                           exponent=3.0, segments=10, rings=8,
                           at=(-0.17, front - 0.10, 0.70))
    parts.append(knob)

    step = forms.loft("Step", "c_stone", [
        (0.00, forms.rounded_rect(1.34, 0.62, 0.22, 4)),
        (0.13, forms.rounded_rect(1.22, 0.52, 0.20, 4)),
    ], at=(-0.46, front - 0.30, 0.0))
    forms.jitter_verts(step, 0.009, seed=15)
    parts.append(step)

    for x_pos, y_pos, rot in ((0.86, front, 0.0), (-1.52, -0.30, 90.0)):
        parts += _window(x_pos, y_pos, 1.02, rot)

    cottage = meshtools.join(parts, "Cottage")
    meshtools.merge_doubles(cottage)
    meshtools.drop_to_floor(cottage)
    return [cottage]


def _window(x_pos, y_pos, z_pos, rot_deg):
    rot = math.radians(rot_deg)
    out_x, out_y = -math.sin(rot) * 1.0, math.cos(rot) * 1.0
    normal = (out_x if abs(out_x) > abs(out_y) else 0.0,
              out_y if abs(out_y) >= abs(out_x) else 0.0)
    nx, ny = (normal[0], normal[1])
    if abs(nx) > abs(ny):
        frame_size, pane_size = (0.14, 0.74, 0.74), (0.08, 0.56, 0.56)
    else:
        frame_size, pane_size = (0.74, 0.14, 0.74), (0.56, 0.08, 0.56)
    base = (x_pos, y_pos, z_pos)
    frame = forms.superform("WindowFrame", "c_teal", size=frame_size,
                            exponent=4.5, segments=14, rings=10, at=base)
    pane = forms.superform("Pane", "c_wood_deep", size=pane_size,
                           exponent=4.0, segments=12, rings=9,
                           at=(base[0] - nx * 0.05, base[1] - ny * 0.05,
                               base[2]))
    return [frame, pane]


# ------------------------------------------------------------------ chuck

def build_chuck():
    meshtools.reset_scene()
    parts = []
    head_z = 1.135

    for side in (-1, 1):
        boot = forms.superform("Boot", "c_butter",
                               size=(0.185, 0.285, 0.155), exponent=3.4,
                               segments=14, rings=10,
                               at=(side * 0.112, -0.035, 0.077))
        forms.press(boot, "Z", plane=0.0, amount=0.55, radius=0.16,
                    centre=(side * 0.112, -0.035, 0.0))
        parts.append(boot)
        leg = forms.sweep("Leg", "c_skin",
                          [(side * 0.112, -0.01, 0.10),
                           (side * 0.108, 0.0, 0.30),
                           (side * 0.104, 0.0, 0.52)],
                          [0.094, 0.084, 0.086], segments=10, samples=5)
        parts.append(leg)

    # One continuous revolved silhouette from hips to neck -- a thrown pot,
    # not a stack of boxes. The belly is where clay would settle.
    torso = forms.lathe("Torso", "c_teal", [
        (0.00, 0.40), (0.196, 0.42), (0.232, 0.54), (0.240, 0.66),
        (0.220, 0.80), (0.186, 0.90), (0.134, 0.97), (0.088, 1.005),
        (0.00, 1.01),
    ], segments=18, smooth_profile=4)
    forms.swell(torso, (0.0, -0.17, 0.60), radius=0.22, amount=0.022)
    parts.append(torso)

    hem = forms.pad("Hem", "c_red", radius=0.215, lobes=5, amplitude=0.05,
                    dome=0.035, underside=0.045, points=24, at=(0, 0, 0.455))
    parts.append(hem)

    for side in (-1, 1):
        arm = forms.sweep("Arm", "c_teal",
                          [(side * 0.16, 0.0, 0.88),
                           (side * 0.225, -0.02, 0.72),
                           (side * 0.238, -0.05, 0.56)],
                          [0.082, 0.072, 0.064], segments=10, samples=5)
        parts.append(arm)
        hand = forms.superform("Hand", "c_skin", size=(0.115, 0.125, 0.105),
                               exponent=3.0, segments=12, rings=9,
                               at=(side * 0.240, -0.062, 0.515))
        parts.append(hand)

    head = forms.superform("Head", "c_skin", size=(0.405, 0.375, 0.425),
                           exponent=3.3, segments=22, rings=16,
                           at=(0, 0, head_z))
    # The face is pressed back to a plane so features sit ON something.
    forms.press(head, "Y", plane=-0.155, amount=0.46, radius=0.26,
                centre=(0, -0.19, head_z))
    forms.press(head, "Z", plane=head_z + 0.205, amount=0.22, radius=0.22,
                centre=(0, 0.02, head_z + 0.21))
    forms.jitter_verts(head, 0.004, seed=21)
    parts.append(head)

    neck = forms.sweep("Neck", "c_skin", [(0, 0, 0.955), (0, 0, 1.02)],
                       [0.088, 0.082], segments=12)
    parts.append(neck)

    # Hair as a pressed clay cap. A flat PAD was tried first and hung over the
    # brow like a fringe, hiding the glasses -- a pad's rim is its widest part,
    # so it always overhangs. A solid cap pressed BACK in Y sits on the skull
    # and leaves the face clear.
    hair = forms.superform("Hair", "c_hair", size=(0.445, 0.415, 0.300),
                           exponent=3.0, segments=20, rings=14,
                           at=(0.0, 0.040, head_z + 0.145))
    forms.press(hair, "Y", plane=-0.085, amount=0.42, radius=0.26,
                centre=(0, -0.18, head_z + 0.10))
    forms.press(hair, "Z", plane=head_z + 0.300, amount=0.26, radius=0.22,
                centre=(0, 0.03, head_z + 0.30))
    forms.jitter_verts(hair, 0.006, seed=23)
    parts.append(hair)

    for side in (-1, 1):
        ear = forms.superform("Ear", "c_skin", size=(0.075, 0.105, 0.125),
                              exponent=2.6, segments=10, rings=8,
                              at=(side * 0.192, 0.012, head_z - 0.015))
        parts.append(ear)
        # The glasses ARE the character. At the first size they read as two
        # dark smudges from any distance, so the rims and lenses are both
        # pushed up until they survive being small on screen.
        rim = meshtools.torus("Rim", "c_ink", major=0.094, minor=0.019,
                              at=(side * 0.098, -0.158, head_z + 0.014),
                              rot=(math.radians(90), 0, 0),
                              major_seg=16, minor_seg=6)
        parts.append(rim)
        lens = forms.superform("Lens", "c_cream", size=(0.168, 0.024, 0.168),
                               exponent=2.2, segments=14, rings=8,
                               at=(side * 0.098, -0.152, head_z + 0.014))
        parts.append(lens)
        eye = forms.superform("Eye", "c_ink", size=(0.070, 0.032, 0.078),
                              exponent=2.4, segments=10, rings=8,
                              at=(side * 0.098, -0.168, head_z + 0.014))
        parts.append(eye)
    bridge = forms.sweep("Bridge", "c_ink",
                         [(-0.060, -0.160, head_z + 0.032),
                          (0.060, -0.160, head_z + 0.032)],
                         [0.015, 0.015], segments=7)
    parts.append(bridge)

    nose = forms.superform("Nose", "c_skin", size=(0.065, 0.060, 0.055),
                           exponent=2.8, segments=10, rings=8,
                           at=(0, -0.172, head_z - 0.055))
    parts.append(nose)
    # A WIDE, THIN lozenge sunk into the face. A small round pad standing proud
    # of the chin read as a smudge at every size that matters.
    mouth = forms.superform("Mouth", "c_ink", size=(0.150, 0.030, 0.042),
                            exponent=2.6, segments=14, rings=8,
                            at=(0, -0.162, head_z - 0.128))
    parts.append(mouth)

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

    body = forms.superform("Cube", "c_wood", size=(BLOCK_SIZE,) * 3,
                           exponent=4.6, segments=26, rings=18,
                           at=(0, 0, half))
    # Knuckle marks on the corners: a block that has been handled.
    forms.dents(body, [(half, half, half * 1.9), (-half, half, half * 0.3),
                       (half, -half, half * 0.4)], depth=0.022, radius=0.30)
    forms.jitter_verts(body, 0.0035, seed=31)
    meshtools.paint_by_normal(body, "c_wood", "c_wood", "c_wood_deep",
                              up_at=0.9, down_at=-0.7)

    plaques = []
    thickness = 0.052
    for name, normal in BLOCK_FACES:
        centre = plaque_centre(normal, thickness)
        if normal[2] > 0.5:
            size = (0.575, 0.575, thickness)
        elif abs(normal[0]) > 0.5:
            size = (thickness, 0.575, 0.575)
        else:
            size = (0.575, thickness, 0.575)
        plaque = forms.superform(name, "c_cream", size=size, exponent=5.0,
                                 segments=16, rings=12, at=centre)
        plaques.append(plaque)

    cream = painter.flat_material("d1_block_face", "c_cream", roughness=0.97)
    painter.assign(plaques, cream)
    return [body] + plaques


# -------------------------------------------------------------------- run

if __name__ == "__main__":
    produce(D, "tree", build_tree(), budget_tris=3000, bake_samples=22)
    produce(D, "cottage", build_cottage(), budget_tris=5200, bake_samples=24)
    produce(D, "chuck", build_chuck(), budget_tris=5200, bake_samples=24)
    produce(D, "block", build_block(), texture=512, budget_tris=2600,
            bake_samples=28)
