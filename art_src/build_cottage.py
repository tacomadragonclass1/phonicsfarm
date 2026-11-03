"""The cottage -- the architectural voice of the village.

    blender --background --python art_src/build_cottage.py

This is the asset that has to carry "a children's picture book brought to
life", so its decisions are the ones the rest of the village will follow.

  * SCALE AGAINST CHUCK. He is 1.21 m. The door is 1.46 m, the eaves are at
    2.1 m and the ridge at 3.6 m, so the building is three Chucks tall and he
    can plainly walk through the door. The old village's houses read as
    dollhouses because nothing in them was sized against the player.
  * THE ROOF IS THE SILHOUETTE. It is deep, steeply pitched, deliberately
    sagged along the ridge, and overhangs the walls by 0.38 m on every side.
    That overhang is what casts the band of shade down the wall and gives a
    flat gable face something to be read against.
  * THE WALLS LEAN. 1.4 degrees, plus a small noise displacement, plus a
    plinth that is wider than the wall above it. None of it is visible as an
    effect; together it is the difference between "built by hand a long time
    ago" and "extruded this morning".
  * HALF-TIMBERING gives the big plaster planes a grid to break them up at
    reading distance, without the busy micro-detail the brief rules out.

Collision is NOT in this GLB. `storybook/cottage.tscn` wraps it in a
StaticBody3D with two box shapes, so the physics body stays a cheap convex
pair while the visual keeps its overhangs and chimney.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sb_lib import asset, meshtools  # noqa: E402

NAME = "cottage"

WALL_W, WALL_D = 3.00, 2.70
PLINTH_H = 0.20
EAVES_Z = 2.14
RIDGE_Z = 3.40
OVERHANG = 0.30
PITCH = math.radians(40.0)
DOOR_H, DOOR_W = 1.46, 0.80


def build():
    meshtools.reset_scene()
    parts = []

    # ------------------------------------------------------------- plinth
    plinth = meshtools.box("Plinth", "stone",
                           size=(WALL_W + 0.30, WALL_D + 0.30, PLINTH_H),
                           at=(0, 0, PLINTH_H / 2))
    meshtools.taper(plinth, top_scale=0.94, bottom_z=0.0, top_z=PLINTH_H)
    meshtools.wobble(plinth, amount=0.016, scale=1.6, seed=21)
    meshtools.bevel(plinth, meshtools.BEVEL_MASONRY, segments=2)
    parts.append(plinth)

    # -------------------------------------------------------------- walls
    walls = meshtools.box("Walls", "plaster",
                          size=(WALL_W, WALL_D, EAVES_Z - PLINTH_H),
                          at=(0, 0, (EAVES_Z + PLINTH_H) / 2))
    meshtools.subdivide(walls, levels=2, smooth=False)
    meshtools.taper(walls, top_scale=0.965, bottom_z=PLINTH_H, top_z=EAVES_Z)
    meshtools.wobble(walls, amount=0.018, scale=1.1, seed=5,
                     axis_bias=(1, 1, 0.3))
    meshtools.lean(walls, degrees=1.4, axis="Y", pivot_z=PLINTH_H)
    meshtools.bevel(walls, meshtools.BEVEL_MASONRY, segments=2)
    parts.append(walls)

    # The gable ends. The roof slopes down the Y axis, so the triangles close
    # the X ends of the building -- the first attempt put them on the sloping
    # sides, where they stabbed straight through the roof.
    gable_h = RIDGE_Z - EAVES_Z
    for side in (-1, 1):
        wall_end = meshtools.gable("Gable", "plaster_warm",
                                   width=0.17, depth=WALL_D * 0.98,
                                   height=gable_h, along="Y",
                                   at=(side * (WALL_W / 2 - 0.09), 0,
                                       EAVES_Z + gable_h / 2))
        meshtools.bevel(wall_end, 0.020, segments=2)
        parts.append(wall_end)

    # --------------------------------------------------- half-timbered frame
    beam = 0.145
    for x in (-1, 1):
        for y in (-1, 1):
            post = meshtools.box("Post", "timber_dark",
                                 size=(beam, beam, EAVES_Z - PLINTH_H + 0.06),
                                 at=(x * (WALL_W / 2 - 0.03),
                                     y * (WALL_D / 2 - 0.03),
                                     (EAVES_Z + PLINTH_H) / 2))
            meshtools.lean(post, degrees=1.4, axis="Y", pivot_z=PLINTH_H)
            meshtools.bevel(post, meshtools.BEVEL_CARPENTRY, segments=2)
            parts.append(post)

    rail = meshtools.box("Rail", "timber_dark",
                         size=(WALL_W + 0.03, WALL_D + 0.03, 0.13),
                         at=(0, 0, 1.30))
    meshtools.bevel(rail, meshtools.BEVEL_CARPENTRY, segments=2)
    parts.append(rail)

    # Two braces on the front wall. Diagonals are what make half-timbering
    # read as structure rather than as a painted grid.
    for sign in (-1, 1):
        brace = meshtools.box("Brace", "timber_dark",
                              size=(0.115, 0.10, 0.95),
                              at=(sign * 1.02, -(WALL_D / 2 + 0.01), 1.78),
                              rot=(0, math.radians(sign * 26), 0))
        meshtools.bevel(brace, meshtools.BEVEL_CARPENTRY, segments=2)
        parts.append(brace)

    # ---------------------------------------------------------------- roof
    # Derived from the ridge, not placed by eye. The eave point is where the
    # roof's top surface meets the overhang; everything that has to touch the
    # roof -- the rolled eave, the dark bottom course -- is positioned from
    # that point, which is why they now sit ON the roof instead of near it.
    eave_y = WALL_D / 2 + OVERHANG
    eave_z = RIDGE_Z - eave_y * math.tan(PITCH)
    thickness = 0.17
    slope_len = eave_y / math.cos(PITCH)
    for side in (-1, 1):
        centre_y = side * eave_y / 2
        centre_z = (RIDGE_Z + eave_z) / 2 - (thickness / 2) / math.cos(PITCH)
        slab = meshtools.box("Roof", "terracotta",
                             size=(WALL_W + OVERHANG * 2, slope_len, thickness),
                             at=(0, centre_y, centre_z))
        # Rotate AFTER the box helper has baked the slab's dimensions, never
        # by handing `box` a rotation: scale is applied first, so a rotation
        # passed in would be scaled rather than the slab.
        slab.rotation_euler = (side * -PITCH, 0, 0)
        meshtools.apply_transform(slab)
        meshtools.subdivide(slab, levels=1, smooth=False)
        # A roof that has carried snow for fifty years is not a flat plane.
        meshtools.sag(slab, depth=0.070, along="X", span=WALL_W / 2 + OVERHANG)
        meshtools.wobble(slab, amount=0.013, scale=1.4, seed=31 + side)
        meshtools.bevel(slab, 0.032, segments=2)
        # The lowest course sits in its own shade all day.
        meshtools.repaint_faces(
            slab, lambda c, n: c.z < eave_z + 0.34, "terracotta_dark")
        parts.append(slab)

        # Rolled eave: a half-round along the bottom edge, so the roof ends in
        # a soft lip instead of a cut sheet of card.
        roll = meshtools.cylinder("Eave", "terracotta_dark", radius=0.095,
                                  depth=WALL_W + OVERHANG * 2 + 0.04,
                                  at=(0, side * (eave_y - 0.055),
                                      eave_z + 0.015),
                                  rot=(0, math.radians(90), 0), segments=12)
        parts.append(roll)

        # Three course battens down each slope. A pitched roof with no
        # horizontal break reads as a folded sheet of card; these are the
        # cheapest possible cue that it is made of tiles.
        for course in (0.30, 0.54, 0.78):
            run_y = eave_y * course
            batten = meshtools.cylinder(
                "Course", "terracotta_dark", radius=0.030,
                depth=WALL_W + OVERHANG * 2 - 0.16,
                at=(0, side * run_y,
                    RIDGE_Z - run_y * math.tan(PITCH) + 0.018),
                rot=(0, math.radians(90), 0), segments=8)
            parts.append(batten)

    ridge = meshtools.cylinder("Ridge", "terracotta_dark", radius=0.115,
                               depth=WALL_W + OVERHANG * 1.4,
                               at=(0, 0, RIDGE_Z - 0.05),
                               rot=(0, math.radians(90), 0), segments=12)
    meshtools.sag(ridge, depth=0.055, along="X", span=WALL_W / 2)
    parts.append(ridge)

    # ------------------------------------------------------------- chimney
    stack = meshtools.box("Chimney", "stone", size=(0.42, 0.40, 2.25),
                          at=(0.92, 0.42, 2.38))
    meshtools.subdivide(stack, levels=1, smooth=False)
    meshtools.bend(stack, degrees=7.0, bottom_z=1.5, top_z=3.5, axis="X")
    meshtools.wobble(stack, amount=0.020, scale=2.0, seed=44)
    meshtools.bevel(stack, meshtools.BEVEL_MASONRY, segments=2)
    parts.append(stack)
    cap = meshtools.box("ChimneyCap", "slate", size=(0.56, 0.54, 0.11),
                        at=(1.00, 0.42, 3.54))
    meshtools.bevel(cap, 0.022, segments=2)
    parts.append(cap)
    for offset in (-0.11, 0.11):
        pot = meshtools.cylinder("Pot", "terracotta", radius=0.085,
                                 depth=0.24, at=(1.00, 0.42 + offset, 3.68),
                                 segments=12)
        meshtools.bevel(pot, 0.016, segments=2)
        parts.append(pot)

    # ---------------------------------------------------------------- door
    # A plank door under a timber lintel. A round-topped door was built first,
    # from two thin cylinders, and rendered as a black disc above the door in
    # Cycles -- the UVs and the baked texels there were both correct, so it
    # was the geometry. A lintel is fewer parts, stronger in silhouette and
    # more in keeping with the half-timbering, so the arch was abandoned
    # rather than debugged.
    front_y = -(WALL_D / 2) - 0.015
    door_x = -0.52
    frame = meshtools.box("DoorFrame", "paper",
                          size=(DOOR_W + 0.22, 0.09, DOOR_H + 0.06),
                          at=(door_x, front_y, PLINTH_H + (DOOR_H + 0.06) / 2))
    meshtools.bevel(frame, meshtools.BEVEL_CARPENTRY, segments=2)
    parts.append(frame)

    lintel = meshtools.box("Lintel", "timber_dark",
                           size=(DOOR_W + 0.52, 0.17, 0.19),
                           at=(door_x, front_y - 0.035, PLINTH_H + DOOR_H + 0.13))
    meshtools.wobble(lintel, amount=0.009, scale=3.0, seed=17)
    meshtools.bevel(lintel, meshtools.BEVEL_CARPENTRY, segments=2)
    parts.append(lintel)

    door = meshtools.box("Door", "teal", size=(DOOR_W, 0.08, DOOR_H),
                         at=(door_x, front_y - 0.030, PLINTH_H + DOOR_H / 2))
    meshtools.subdivide(door, levels=1, smooth=False)
    meshtools.bevel(door, meshtools.BEVEL_CARPENTRY, segments=2)
    parts.append(door)
    # Plank lines: two narrow darker bands down the door.
    for x_band in (door_x - 0.20, door_x + 0.20):
        plank = meshtools.box("Plank", "timber_dark",
                              size=(0.030, 0.035, DOOR_H - 0.10),
                              at=(x_band, front_y - 0.072,
                                  PLINTH_H + DOOR_H / 2))
        parts.append(plank)
    for z in (0.56, 1.34):
        hinge = meshtools.box("Hinge", "soot", size=(0.32, 0.035, 0.065),
                              at=(door_x - 0.19, front_y - 0.075, z))
        meshtools.bevel(hinge, 0.010, segments=2)
        parts.append(hinge)
    knob = meshtools.blob("Knob", "honey", radius=0.052,
                          at=(door_x + 0.28, front_y - 0.078, 0.94))
    parts.append(knob)

    step = meshtools.box("Step", "stone_light", size=(1.24, 0.46, 0.14),
                         at=(door_x, front_y - 0.22, 0.07))
    meshtools.wobble(step, amount=0.012, scale=2.2, seed=9)
    meshtools.bevel(step, meshtools.BEVEL_MASONRY, segments=2)
    parts.append(step)

    # --------------------------------------------------------------- lamp
    # Beside the door, not over it: over the door it fought with the lintel
    # and sat in the roof's shadow where nobody would ever see it.
    lamp_x = door_x + 0.60
    bracket = meshtools.box("Bracket", "soot", size=(0.19, 0.040, 0.040),
                            at=(lamp_x - 0.08, front_y - 0.06, 1.74))
    parts.append(bracket)
    stem = meshtools.box("Stem", "soot", size=(0.038, 0.038, 0.14),
                         at=(lamp_x, front_y - 0.06, 1.68))
    parts.append(stem)
    lamp = meshtools.cone("Lamp", "honey", r1=0.088, r2=0.058, depth=0.19,
                          at=(lamp_x, front_y - 0.06, 1.53), segments=10)
    meshtools.bevel(lamp, 0.014, segments=2)
    parts.append(lamp)
    hood = meshtools.cone("LampHood", "soot", r1=0.112, r2=0.035, depth=0.085,
                          at=(lamp_x, front_y - 0.06, 1.66), segments=10)
    parts.append(hood)

    # ------------------------------------------------------------- windows
    parts += _window(0.92, front_y, 1.32, box=True)
    parts += _window(-(WALL_W / 2) - 0.02, -0.55, 1.46, face="side")

    merged = meshtools.join(parts, "Cottage")
    meshtools.drop_to_floor(merged)
    return [merged]


def _window(x, y, z, box=False, face="front"):
    """A mullioned window, optionally with a flower box under the sill."""
    parts = []
    w, h, depth = 0.74, 0.66, 0.09
    if face == "front":
        size_frame = (w + 0.14, depth, h + 0.14)
        size_glass = (w, 0.05, h)
        pos = (x, y, z)
        mull_v = (0.040, 0.05, h)
        mull_h = (w, 0.05, 0.040)
        out = (0, -0.03, 0)
    else:
        size_frame = (depth, w + 0.14, h + 0.14)
        size_glass = (0.05, w, h)
        pos = (x, y, z)
        mull_v = (0.05, 0.040, h)
        mull_h = (0.05, w, 0.040)
        out = (-0.03, 0, 0)

    frame = meshtools.box("WindowFrame", "paper", size=size_frame, at=pos)
    meshtools.bevel(frame, meshtools.BEVEL_CARPENTRY, segments=2)
    parts.append(frame)
    glass = meshtools.box("Glass", "slate", size=size_glass,
                          at=(pos[0] + out[0], pos[1] + out[1], pos[2]))
    parts.append(glass)
    for size in (mull_v, mull_h):
        mull = meshtools.box("Mullion", "timber", size=size,
                             at=(pos[0] + out[0] * 1.6, pos[1] + out[1] * 1.6,
                                 pos[2]))
        parts.append(mull)

    if box:
        sill = meshtools.box("Sill", "timber", size=(w + 0.26, 0.26, 0.17),
                             at=(x, y - 0.12, z - h / 2 - 0.19))
        meshtools.bevel(sill, meshtools.BEVEL_CARPENTRY, segments=2)
        parts.append(sill)
        # Three flowers, not thirty. Enough to say "somebody lives here".
        for i, (dx, colour) in enumerate(((-0.24, "rose"), (0.0, "butter"),
                                          (0.24, "rose"))):
            bloom = meshtools.blob("Bloom", colour, radius=0.072,
                                   at=(x + dx, y - 0.14,
                                       z - h / 2 - 0.05 + (i % 2) * 0.03),
                                   segments=8, rings=6)
            parts.append(bloom)
            leaf = meshtools.blob("Leaf", "foliage_dark", radius=0.075,
                                  at=(x + dx, y - 0.13, z - h / 2 - 0.12),
                                  segments=8, rings=5)
            leaf.scale = (1.3, 1.0, 0.45)
            meshtools.apply_transform(leaf)
            parts.append(leaf)
    return parts


if __name__ == "__main__":
    asset.produce(NAME, build(), texture=asset.TEXTURE_LARGE,
                  roughness=0.95, budget_tris=5000, bake_samples=28,
                  smooth_angle=30.0,
                  gouache=dict(wash=0.19, wash_scale=1.5, grain=0.055,
                               grain_scale=26.0, streak=0.08, streak_scale=2.2,
                               ao_strength=0.52, ao_distance=0.30,
                               edge_light=0.16, edge_dark=0.12))
