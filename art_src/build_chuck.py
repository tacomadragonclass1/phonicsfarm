"""Chuck -- the player character.

    blender --background --python art_src/build_chuck.py

An ORIGINAL design, not a reskin of the Kenney model. What carries over from
the old Chuck is his identity, because kindergarteners already know him: a
brown-skinned boy in round glasses, a striped top, blue shorts and yellow
boots. The silhouette, construction and proportions are all new.

Engine contract, from `player/player.gd`:

  * 1.21 m tall -- the same height the Kenney model reached at its 1.8 scale,
    so the existing 0.3 x 1.16 collision capsule and the CarryAnchor at
    (0, 0.8, 0.62) still fit without touching the controller.
  * Faces local +Z in Godot. Godot's +Z is Blender's -Y, so he is built
    facing -Y and the exporter's Y-up conversion does the rest.
  * Animations named exactly `idle` and `walk`, both looping.

Art direction:

  * 3.3 heads tall. Storybook children are big-headed; it reads as young
    without reading as a bobblehead, and it keeps the FACE large, which is
    what makes him expressive at a 1.2 m-tall character on an orthographic
    camera.
  * The glasses are the silhouette. They are the one piece of high-contrast
    dark against his skin, they survive being shrunk to thumbnail size, and
    they are what a five-year-old draws when asked to draw Chuck.
  * Clothing is blocked in three values -- dark boots, mid jumper, light
    collar -- so he separates from the meadow behind him at any distance.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sb_lib import asset, meshtools, rig  # noqa: E402

NAME = "chuck"
HEIGHT = 1.21

# Landmarks, so the rig and the mesh cannot drift apart.
HIP_Z = 0.455
CHEST_Z = 0.680
NECK_Z = 0.800
HEAD_Z = 0.985          # centre of the skull
SHOULDER = (0.148, 0.0, 0.745)
ELBOW = (0.176, 0.0, 0.572)
HAND = (0.184, -0.022, 0.408)
HIP_X = 0.082
KNEE_Z = 0.260
ANKLE_Z = 0.105


def build_body():
    parts = []

    # ---------------------------------------------------------------- boots
    for side in (-1, 1):
        boot = meshtools.box("Boot", "butter", size=(0.118, 0.215, 0.105),
                             at=(side * HIP_X, -0.028, 0.052))
        meshtools.bevel(boot, 0.030, segments=2)
        # Toes lift: a boot that sits flat on the ground reads as a brick.
        meshtools.taper(boot, top_scale=0.86, bottom_z=0.0, top_z=0.105)
        parts.append(boot)
        cuff = meshtools.cylinder("BootCuff", "butter", radius=0.058,
                                  depth=0.055, at=(side * HIP_X, -0.006, 0.118),
                                  segments=14)
        meshtools.bevel(cuff, meshtools.BEVEL_TOY, segments=2)
        parts.append(cuff)

    # ----------------------------------------------------------------- legs
    for side in (-1, 1):
        # One clean tapered tube from boot cuff to hem. An explicit knee ball
        # only produced a lump; a calf that swells slightly reads better and
        # costs nothing.
        leg = meshtools.cone("Leg", "skin", r1=0.052, r2=0.046, depth=0.30,
                             at=(side * HIP_X, 0.0, 0.270), segments=12)
        parts.append(leg)

    # -------------------------------------------------------------- dungarees
    shorts = meshtools.box("Shorts", "sky_blue", size=(0.255, 0.195, 0.215),
                           at=(0.0, 0.0, 0.470))
    meshtools.taper(shorts, top_scale=0.88, bottom_z=0.36, top_z=0.58)
    meshtools.bevel(shorts, 0.034, segments=2)
    parts.append(shorts)
    # The notch between the legs. Without it the shorts read as a bucket.
    for side in (-1, 1):
        hem = meshtools.cylinder("Hem", "sky_blue", radius=0.070, depth=0.055,
                                 at=(side * HIP_X, 0.0, 0.372), segments=14)
        meshtools.bevel(hem, meshtools.BEVEL_TOY, segments=2)
        parts.append(hem)

    # ---------------------------------------------------------------- jumper
    jumper = meshtools.box("Jumper", "teal", size=(0.268, 0.205, 0.300),
                           at=(0.0, 0.0, 0.645))
    meshtools.taper(jumper, top_scale=0.90, bottom_z=0.50, top_z=0.80)
    # Subdivide BEFORE painting. A plain box has one face per side spanning
    # the whole garment, so a stripe predicate can only ever repaint all of it
    # or none of it -- the first attempt at this silently produced no stripes.
    # Simple subdivision puts four rows on each side, which is exactly the
    # stripe pitch, and the 48-degree bevel limit leaves the new coplanar
    # edges alone.
    meshtools.subdivide(jumper, levels=2, smooth=False)
    meshtools.bevel(jumper, 0.038, segments=2)
    for low, high in ((0.570, 0.645), (0.720, 0.796)):
        meshtools.repaint_faces(
            jumper, lambda c, n, lo=low, hi=high: lo <= c.z <= hi, "teal_light")
    parts.append(jumper)

    # Dungaree straps and a belt were both tried and both dropped. The jumper
    # tapers, so anything wrapped round it is buried at one end and proud at
    # the other, and reads as an intersection smear. The jumper hem already
    # separates top from shorts by value; nothing else is needed.

    collar = meshtools.cylinder("Collar", "paper", radius=0.082, depth=0.042,
                                at=(0.0, 0.0, 0.786), segments=16)
    meshtools.bevel(collar, 0.012, segments=2)
    parts.append(collar)

    # ----------------------------------------------------------------- arms
    for side in (-1, 1):
        upper = _limb("Sleeve", "teal", (side * SHOULDER[0], SHOULDER[1], SHOULDER[2]),
                      (side * ELBOW[0], ELBOW[1], ELBOW[2]), 0.052, 0.044)
        parts.append(upper)
        lower = _limb("Forearm", "skin", (side * ELBOW[0], ELBOW[1], ELBOW[2]),
                      (side * HAND[0], HAND[1], HAND[2]), 0.042, 0.038)
        parts.append(lower)
        shoulder = meshtools.blob("Shoulder", "teal", radius=0.056,
                                  at=(side * SHOULDER[0], SHOULDER[1],
                                      SHOULDER[2]))
        parts.append(shoulder)
        hand = meshtools.blob("Hand", "skin", radius=0.049,
                              at=(side * HAND[0], HAND[1], HAND[2]))
        hand.scale = (1.0, 1.15, 0.85)
        meshtools.apply_transform(hand)
        parts.append(hand)

    # ----------------------------------------------------------------- head
    neck = meshtools.cylinder("Neck", "skin_shade", radius=0.052, depth=0.070,
                              at=(0.0, 0.0, 0.805), segments=14)
    parts.append(neck)

    skull = meshtools.uvball("Skull", "skin", radius=0.176,
                             at=(0.0, 0.0, HEAD_Z), segments=18, rings=11)
    skull.scale = (0.97, 0.93, 1.02)
    meshtools.apply_transform(skull)
    # Press the front back toward a plane. This is what gives the glasses,
    # nose and mouth a surface to sit ON; without it they float off a ball
    # and the face reads as decoration rather than as a face.
    meshtools.clamp_axis(skull, "Y", limit=-0.118, softness=0.42)
    meshtools.wobble(skull, amount=0.007, scale=3.4, seed=12)
    parts.append(skull)

    for side in (-1, 1):
        ear = meshtools.blob("Ear", "skin_shade", radius=0.040,
                             at=(side * 0.166, 0.006, HEAD_Z - 0.012))
        ear.scale = (0.55, 0.95, 1.05)
        meshtools.apply_transform(ear)
        parts.append(ear)

    nose = meshtools.blob("Nose", "skin", radius=0.026,
                          at=(0.0, -0.152, HEAD_Z - 0.056), segments=9, rings=6)
    nose.scale = (0.9, 0.95, 0.8)
    meshtools.apply_transform(nose)
    parts.append(nose)

    # The smile is three overlapping lozenges on a downward arc. A torus was
    # tried first and read as a ring stuck to his face: a ring is a closed
    # shape and a mouth is an open one, so no amount of rotating it helped.
    for offset, drop in ((-0.048, 0.019), (0.0, 0.0), (0.048, 0.019)):
        piece = meshtools.blob("Smile", "ink", radius=0.0235,
                               at=(offset, -0.142, HEAD_Z - 0.106 + drop),
                               segments=9, rings=6)
        piece.scale = (1.25, 0.50, 0.68)
        meshtools.apply_transform(piece)
        parts.append(piece)

    # ---------------------------------------------------------------- glasses
    lens_z = HEAD_Z + 0.004
    for side in (-1, 1):
        lens = meshtools.cylinder("Lens", "lens", radius=0.048, depth=0.007,
                                  at=(side * 0.070, -0.141, lens_z),
                                  rot=(math.radians(90), 0, 0), segments=16)
        parts.append(lens)
        rim = meshtools.torus("Rim", "soot", major=0.052, minor=0.0098,
                              at=(side * 0.070, -0.145, lens_z),
                              rot=(math.radians(90), 0, 0),
                              major_seg=16, minor_seg=5)
        parts.append(rim)
        # In FRONT of the lens, not behind it. The lens is opaque -- no
        # transparent surfaces in this game -- so an eye placed behind it is
        # simply invisible, and the glasses read as two blank white discs.
        eye = meshtools.blob("Eye", "eye", radius=0.022,
                             at=(side * 0.070, -0.148, lens_z),
                             segments=10, rings=7)
        eye.scale = (1.0, 0.5, 1.12)
        meshtools.apply_transform(eye)
        parts.append(eye)
        spark = meshtools.blob("Spark", "eye_white", radius=0.0088,
                               at=(side * 0.077, -0.157, lens_z + 0.012),
                               segments=7, rings=5)
        parts.append(spark)
        temple = meshtools.box("Temple", "soot", size=(0.011, 0.095, 0.009),
                               at=(side * 0.120, -0.094, lens_z + 0.006))
        parts.append(temple)
    bridge = meshtools.box("Bridge", "soot", size=(0.042, 0.011, 0.009),
                           at=(0.0, -0.143, lens_z + 0.018))
    parts.append(bridge)

    # ------------------------------------------------------------------ hair
    parts.append(_hair())
    return parts


def _limb(name, color, start, end, r_start, r_end):
    """A tapered tube between two points -- an arm or a leg segment."""
    start, end = meshtools.Vector(start), meshtools.Vector(end)
    span = end - start
    length = span.length
    obj = meshtools.cone(name, color, r1=r_start, r2=r_end, depth=length,
                         at=(0, 0, 0), segments=14)
    quat = span.normalized().to_track_quat("Z", "Y")
    obj.rotation_euler = quat.to_euler()
    obj.location = (start + end) * 0.5
    meshtools.apply_transform(obj, rotation=True, scale=True)
    meshtools.set_origin(obj, (0, 0, 0))
    return obj


def _hair():
    """A soft cap of curls.

    Built as overlapping lumps and then voxel-remeshed, so the curls merge
    into ONE organic skin with a scalloped silhouette instead of reading as
    a pile of separate balls.
    """
    lumps = []
    # The cap MUST sit outside the skull's crown. At radius 0.186 it did not,
    # and the voxel remesh shrank it further, so the scalp poked through as a
    # bald patch at the hairline.
    cap = meshtools.uvball("HairCap", "hair", radius=0.192,
                           at=(0.0, 0.018, HEAD_Z + 0.016), segments=18,
                           rings=12)
    cap.scale = (1.0, 0.98, 0.95)
    meshtools.apply_transform(cap)
    lumps.append(cap)

    # Six low curls, kept under the 1.21 m total height. The first pass used
    # eight larger ones including a tall crown lump; it pushed him to 1.25 m
    # and read as a brain rather than hair.
    curls = [
        (-0.112, -0.038, 0.100, 0.062),
        (0.112, -0.038, 0.100, 0.062),
        (-0.148, 0.052, 0.058, 0.062),
        (0.148, 0.052, 0.058, 0.062),
        (-0.062, 0.112, 0.092, 0.066),
        (0.062, 0.112, 0.092, 0.066),
    ]
    for x, y, z, radius in curls:
        lumps.append(meshtools.blob("Curl", "hair", radius=radius,
                                    at=(x, y, HEAD_Z + z)))

    hair = meshtools.join(lumps, "Hair")
    meshtools.remesh_organic(hair, voxel=0.019)
    _clip_hairline(hair, HEAD_Z + 0.018, slope=0.50)
    meshtools.shrink_to_budget(hair, 620)
    meshtools.set_part_color(hair, "hair")
    return hair


def _clip_hairline(obj, base_z, slope=0.55):
    """Cut the hair along a plane that is HIGH at the brow and LOW at the nape.

    Deliberately written as an explicit face test rather than as a bisect with
    `clear_inner`: which side of the plane that flag clears is easy to get
    backwards, and getting it backwards silently removes the crown instead of
    the fringe. A predicate states the intent directly.

    `slope` is how much the hairline drops per metre travelled backwards.
    Chuck's eyes sit at the vertical centre of his head, so the brow line has
    to clear them by a real margin or the hair becomes a helmet.
    """
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    # WORLD space. Face centres come back in the object's local frame, and
    # this object's origin is up at head height, so testing them against a
    # world Z threshold deletes either everything or nothing.
    to_world = obj.matrix_world
    doomed = []
    for face in bm.faces:
        centre = to_world @ face.calc_center_median()
        if centre.z < base_z - slope * centre.y:
            doomed.append(face)
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    bmesh.ops.holes_fill(bm, edges=bm.edges[:])
    bm.to_mesh(obj.data)
    bm.free()


def build_rig(mesh):
    skeleton = rig.Rig("ChuckRig")
    skeleton.bone("root", (0, 0, 0), (0, 0, 0.12))
    skeleton.bone("hips", (0, 0, HIP_Z), (0, 0, CHEST_Z), parent="root")
    skeleton.bone("chest", (0, 0, CHEST_Z), (0, 0, NECK_Z), parent="hips",
                  connected=True)
    skeleton.bone("head", (0, 0, NECK_Z), (0, 0, HEIGHT), parent="chest",
                  connected=True)
    for side, tag in ((-1, "L"), (1, "R")):
        skeleton.bone("arm_" + tag, (side * SHOULDER[0], 0, SHOULDER[2]),
                      (side * ELBOW[0], 0, ELBOW[2]), parent="chest")
        skeleton.bone("hand_" + tag, (side * ELBOW[0], 0, ELBOW[2]),
                      (side * HAND[0], HAND[1], HAND[2]), parent="arm_" + tag,
                      connected=True)
        skeleton.bone("thigh_" + tag, (side * HIP_X, 0, HIP_Z - 0.03),
                      (side * HIP_X, 0, KNEE_Z), parent="hips")
        skeleton.bone("shin_" + tag, (side * HIP_X, 0, KNEE_Z),
                      (side * HIP_X, 0, ANKLE_Z), parent="thigh_" + tag,
                      connected=True)
        skeleton.bone("foot_" + tag, (side * HIP_X, 0, ANKLE_Z),
                      (side * HIP_X, -0.11, 0.03), parent="shin_" + tag,
                      connected=True)

    # Everything above the brow belongs to the head, full stop. Without this
    # the hair and glasses get partly claimed by the chest bone and shear.
    skeleton.bind(mesh, falloff=5.5, influences=3, prefer={
        "head": lambda p: p.z > NECK_Z + 0.015,
    }, prefer_weight=0.97)
    return skeleton


# ------------------------------------------------------------------ motion

def idle_action(skeleton):
    """Two seconds of breathing. Nothing travels; he just occupies the world."""
    frames = {}
    for frame, phase in ((1, 0.0), (25, 1.0), (49, 0.0)):
        rise = 0.010 * phase
        frames[frame] = {
            "root": {"loc": (0, 0, rise * 0.5)},
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


def walk_action(skeleton):
    """One second, two steps. Contacts at 1 and 13, passes at 7 and 19."""

    def step(lead, trail, bob, lean, twist):
        return {
            "root": {"loc": (0, 0, bob)},
            "hips": {"rot": (lean, twist, 0)},
            "chest": {"rot": (lean * 0.4, -twist * 0.8, 0)},
            "head": {"rot": (-lean * 0.6, -twist * 0.3, 0)},
            "thigh_" + lead: {"rot": (-26, 0, 0)},
            "shin_" + lead: {"rot": (6, 0, 0)},
            "foot_" + lead: {"rot": (14, 0, 0)},
            "thigh_" + trail: {"rot": (20, 0, 0)},
            "shin_" + trail: {"rot": (26, 0, 0)},
            "foot_" + trail: {"rot": (-8, 0, 0)},
            "arm_" + lead: {"rot": (24, 0, 0)},
            "arm_" + trail: {"rot": (-28, 0, 0)},
            "hand_" + lead: {"rot": (-16, 0, 0)},
            "hand_" + trail: {"rot": (-24, 0, 0)},
        }

    def pass_pose(planted, lifted, twist):
        return {
            "root": {"loc": (0, 0, 0.022)},
            "hips": {"rot": (1.0, twist * 0.4, 0)},
            "chest": {"rot": (0.5, -twist * 0.3, 0)},
            "head": {"rot": (-0.5, 0, 0)},
            "thigh_" + planted: {"rot": (-4, 0, 0)},
            "shin_" + planted: {"rot": (2, 0, 0)},
            "foot_" + planted: {"rot": (0, 0, 0)},
            "thigh_" + lifted: {"rot": (-2, 0, 0)},
            "shin_" + lifted: {"rot": (44, 0, 0)},
            "foot_" + lifted: {"rot": (-16, 0, 0)},
            "arm_" + planted: {"rot": (2, 0, 0)},
            "arm_" + lifted: {"rot": (-2, 0, 0)},
            "hand_" + planted: {"rot": (-18, 0, 0)},
            "hand_" + lifted: {"rot": (-18, 0, 0)},
        }

    frames = {
        1: step("L", "R", -0.016, 2.5, 5.0),
        7: pass_pose("L", "R", 2.0),
        13: step("R", "L", -0.016, 2.5, -5.0),
        19: pass_pose("R", "L", -2.0),
        25: step("L", "R", -0.016, 2.5, 5.0),
    }
    return skeleton.action("chuck_walk", frames)


def build():
    meshtools.reset_scene()
    parts = build_body()
    body = meshtools.join(parts, "ChuckBody")
    meshtools.merge_doubles(body, 0.0004)
    skeleton = build_rig(body)
    idle_action(skeleton)
    walk_action(skeleton)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 49
    return [body, skeleton.object]


if __name__ == "__main__":
    import bpy  # noqa: E402  (needed by build(); imported late for clarity)
    objects = build()
    asset.produce(NAME, objects, texture=asset.TEXTURE_MEDIUM,
                  # One Chuck and one Annette are ever on screen, so the hero
                  # character is allowed roughly twice a scenery prop's
                  # budget. Kenney's character was about 2,000 triangles.
                  roughness=0.93, budget_tris=5200, bake_samples=28,
                  smooth_angle=36.0, with_animation=True,
                  animation_names=["idle", "walk"],
                  gouache=dict(wash=0.17, wash_scale=6.0, grain=0.06,
                               grain_scale=80.0, streak=0.09,
                               ao_strength=0.52, ao_distance=0.095,
                               edge_light=0.15, edge_dark=0.12))
