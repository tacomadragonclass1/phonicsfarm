#!/usr/bin/env python3
"""Generate `scenes/village_quarter.tscn`: the village half of the world.

    python3 tools/build_village.py

⭐⭐ EVERY POSITION COMES FROM `art_src/explore/world_plan.py` -- the same
module that sculpts the ground. The green, the five building sites and the
mill are already in that plan and already in the baked terrain; this script
is the consumer that finally stands something on them. One plan, three
consumers (the sculpt, CVC Land, this), no second opinion.

⛔ A SEPARATE FILE, INSTANCED. `tools/build_cvc_land.py` regenerates
`scenes/cvc_land.tscn` wholesale, so two generators writing that one file
would overwrite each other. This emits its own scene and CVC Land instances
it, which keeps one owner per generated file and lets the village be
re-laid without touching the clearing.

⛔⛔ NO MILL MOUND. `storybook/village/mill_mound.tscn` and its baked
collision belong to the OLD foundation village, where the mill stood on a
12 m cone set down on flat ground. That was rejected -- "a hill you set down
is not a hill" -- and `world_plan.mill_hill` now sculpts the rise INTO the
terrain. Instancing the mound here would stack a second hill on the first.

⛔ THE FACADE IS THE ASSET'S LOCAL +Z, NOT ITS FORWARD. Every building is
modelled in Blender with its door and windows on the -Y face (`front` is
negative in `art_src/explore/village.py`), and the glTF conversion sends
Blender -Y to Godot +Z. So pointing a shop at the green means pointing its
BACK vector there, and a yaw derived from the usual -Z forward puts five
shops facing into the hedge.

⛔ NO LETTERS AND NO ROUND LOGIC. This is the village's fabric only.
Whether `cvc_land.tscn` becomes the game -- and what replaces the retired
no-hidden-letter rule -- is a separate decision that PROGRESS.md keeps
deliberately downstream of this one. Nothing here reaches a child.

👉 `lane_stone.tscn` and `wall_run.tscn` are built, exported and NOT used
here. The lane is currently carried by the ground's colour field alone.
Paving it and walling the street frontage are both taste calls, and they are
cheap to add once somebody has looked at this.
"""

import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "scenes", "village_quarter.tscn")
sys.path.insert(0, os.path.join(ROOT, "art_src", "explore"))

import world_plan as P  # noqa: E402

# ⛔⛔ COLLISION IS NOT EMITTED HERE ANY MORE. It used to be: this script
# wrote a StaticBody3D and a BoxShape3D beside each shop, sized from a table
# carried over from the old foundation village. Two things were wrong with
# that. The table was STALE -- it called the bakery 2.90 m deep where the
# mesh measures 3.68, so Chuck could walk into the gable -- and the village
# was the only place in the world where being solid was a property of the
# LAYOUT rather than of the thing.
#
# Collision now lives in `storybook/village/*.tscn`, put there by
# `tools/add_colliders.py` from footprints `tools/measure_footprints.gd`
# measured off the real meshes. Instancing a shop is enough to make it solid,
# here or anywhere else.

ASSETS = ("bakery", "bookshop", "clock_house", "flower_shop", "workshop",
          "windmill", "annette", "well", "bench", "fingerpost", "planter",
          "bunting", "tree_b", "bush", "blossom", "mushrooms")


def gd(point):
    """Plan (x, y) -> Godot (x, z). The plan's +y runs into the picture."""
    return point[0], -point[1]


def xform(point, yaw_deg=0.0, height=0.0):
    rad = math.radians(yaw_deg)
    c, s = math.cos(rad), math.sin(rad)
    x, z = gd(point)
    return ("Transform3D(%.5f, 0, %.5f, 0, 1, 0, %.5f, 0, %.5f, "
            "%.3f, %.3f, %.3f)" % (c, -s, s, c, x, height, z))


def node(name, kind, parent=None, **fields):
    head = '[node name="%s" type="%s"' % (name, kind)
    if parent:
        head += ' parent="%s"' % parent
    out = [head + "]"]
    for key, value in fields.items():
        out.append("%s = %s" % (key, value))
    return "\n".join(out) + "\n\n"


def instance(name, res, parent, transform=None, **fields):
    out = ['[node name="%s" parent="%s" instance=ExtResource("%s")]'
           % (name, parent, res)]
    if transform:
        out.append("transform = " + transform)
    for key, value in fields.items():
        out.append("%s = %s" % (key, value))
    return "\n".join(out) + "\n\n"


def facade_yaw(site, target):
    """Yaw in degrees that points the asset's FACADE (+Z) at `target`.

    After a yaw of t the local +Z axis points (-sin t, 0, cos t) in Godot,
    so aiming it down (dx, dz) is atan2(-dx, dz). See the module note: using
    the conventional -Z forward here turns every shop around.
    """
    sx, sz = gd(site)
    tx, tz = gd(target)
    return math.degrees(math.atan2(-(tx - sx), tz - sz))


def ground(point):
    """The sculpted height under a plan point, so nothing floats or sinks.

    ⭐ `world_plan.ground_height` includes the LEVEL PADS it cuts under each
    building site, so a shop and the dirt it stands on cannot disagree.
    """
    return P.ground_height(point[0], point[1])


def clear_of_works(point, lane=2.6, cart=2.2):
    """True when a decorative thing may stand here.

    Off the lane, off the cart track, off the building pads, and out of the
    reserved bonus site -- which the ground is baked around, so anything
    planted there now would have to be felled later.
    """
    x, y = point
    if P.approach_distance(x, y) < lane:
        return False
    if P.track_climb(x, y)[0] < cart:
        return False
    for _, site, radius in P.VILLAGE:
        if math.hypot(x - site[0], y - site[1]) < radius + 1.6:
            return False
    if math.hypot(x - P.BONUS[0], y - P.BONUS[1]) < P.BONUS_RADIUS + 2.0:
        return False
    return True


def main():
    rng = random.Random(20261109)

    ext = []
    ids = {}
    for index, name in enumerate(ASSETS):
        ids[name] = "a%d" % index
        ext.append('[ext_resource type="PackedScene" '
                   'path="res://storybook/village/%s.tscn" id="%s"]'
                   % (name, ids[name]))

    subs = []

    body = [node("VillageQuarter", "Node3D")]

    # --- the street. ⭐ An ARC on the FAR side of the green, so the camera
    # -- which never turns -- is never looking through a shop at the green.
    # Each shop faces the green's centre, which is what makes five separate
    # buildings read as one place that belongs to somebody.
    body.append(node("Buildings", "Node3D", "."))
    table = []
    for name, site, radius in P.VILLAGE:
        yaw = facade_yaw(site, P.VILLAGE_GREEN)
        height = ground(site)
        tag = name.title().replace("_", "")
        body.append(instance(tag, ids[name], "Buildings",
                             xform(site, yaw, height)))
        table.append((name, radius, yaw, height))

    # --- the mill, on the crown. ⛔ Height from the PLAN, not guessed: the
    # crown is flat at `MILL_H` for exactly this reason, and a windmill a
    # few centimetres into its own hill loses its plinth.
    mill_yaw = facade_yaw(P.MILL, P.VILLAGE_GREEN)
    body.append(instance("Windmill", ids["windmill"], "Buildings",
                         xform(P.MILL, mill_yaw, ground(P.MILL))))

    # --- the green's furniture. The well is the centre; everything else sits
    # off it on a ring, facing in, the way village furniture actually does.
    body.append(node("Props", "Node3D", "."))
    green = P.VILLAGE_GREEN
    body.append(instance("Well", ids["well"], "Props",
                         xform(green, 0.0, ground(green))))

    taken = [green]

    def spot(radius, spacing, tries=36, lane=2.2, cart=2.2):
        """Offer positions on a ring and take the first that is clear.

        ⛔ SEARCHED, not typed. The lane skirts this green and the pads sit
        just off it, so a hand-written offset lands on one or the other
        often enough that it is not worth the argument.
        """
        for step in range(tries):
            angle = math.tau * step / tries + 0.6
            point = (green[0] + math.cos(angle) * radius,
                     green[1] + math.sin(angle) * radius)
            if not clear_of_works(point, lane=lane, cart=cart):
                continue
            if any(math.hypot(point[0] - t[0], point[1] - t[1]) < spacing
                   for t in taken):
                continue
            taken.append(point)
            return point, angle
        return None, None

    # (node name, asset, ring radius, clearance from what is already down)
    for name, asset, radius, spacing in (("Bench", "bench", 3.1, 2.0),
                                         ("BenchEast", "bench", 3.1, 3.4),
                                         ("Fingerpost", "fingerpost",
                                          4.3, 3.0)):
        point, _ = spot(radius, spacing)
        if point is None:
            continue
        # Facing IN toward the well, which is what a bench on a green does.
        body.append(instance(name, ids[asset], "Props",
                             xform(point, facade_yaw(point, green),
                                   ground(point))))

    planted = 0
    for step in range(30):
        point, _ = spot(2.4, 1.5)
        if point is None:
            break
        body.append(instance("Planter%d" % planted, ids["planter"], "Props",
                             xform(point, rng.uniform(0, 360),
                                   ground(point))))
        planted += 1
        if planted == 2:
            break

    # Bunting over the green's south side, where the lane comes in.
    bunting = P.along(-1.0, 22.6)
    body.append(instance("Bunting", ids["bunting"], "Props",
                         xform(bunting, 14.0, ground(bunting) + 1.1)))

    # --- Annette, who runs the village round. ⛔ No script and no letters:
    # she is furniture until adoption is decided. She stands BY the well,
    # facing the way a child arrives from.
    annette = P.along(-1.0, 25.4)
    body.append(instance("Annette", ids["annette"], "Props",
                         xform(annette,
                               facade_yaw(annette, P.ZONES["vowel"]),
                               ground(annette))))

    # --- scenery, over the village half only. ⛔ Generated in PLAN axes: the
    # world is a 40 x 82 m strip laid at yaw 30, so a box in world X/Y wastes
    # a third of its candidates on corners that are not in the world.
    body.append(node("Scenery", "Node3D", "."))
    kinds = ("tree_b", "bush", "blossom", "mushrooms")
    counts = dict.fromkeys(kinds, 0)
    placed = 0
    for attempt in range(1200):
        if placed >= 34:
            break
        row = rng.uniform(P.WORLD_ROW[0] + 5.0, P.WORLD_ROW[1] - 5.0)
        away = rng.uniform(22.0, 62.0)
        point = P.along(row, away)
        if not clear_of_works(point, lane=3.0, cart=2.6):
            continue
        # The green stays OPEN. It is the one place in the village a child
        # is meant to cross freely.
        if P.village_distance(*point) < P.VILLAGE_GREEN_R:
            continue
        # And the mill's crown stays bare, so the mill stands alone on it.
        if math.hypot(point[0] - P.MILL[0],
                      point[1] - P.MILL[1]) < P.MILL_CROWN_R + 1.4:
            continue
        if any(math.hypot(point[0] - t[0], point[1] - t[1]) < 2.2
               for t in taken):
            continue
        taken.append(point)
        kind = kinds[placed % len(kinds)]
        counts[kind] += 1
        body.append(instance("Scenery%02d" % placed, ids[kind], "Scenery",
                             xform(point, rng.uniform(0, 360),
                                   ground(point))))
        placed += 1

    steps = len(ext) + len(subs)
    text = ("[gd_scene load_steps=%d format=3]\n\n" % (steps + 1)
            + "\n".join(ext) + "\n\n" + "\n".join(subs) + "\n"
            + "".join(body))
    with open(OUT, "w") as handle:
        handle.write(text)

    print("[village] wrote %s" % OUT)
    for name, radius, yaw, height in table:
        print("[village] %-12s r %.2f  yaw %+7.2f  y %.3f"
              % (name, radius, yaw, height))
    print("[village] windmill    yaw %+7.2f  y %.3f"
          % (mill_yaw, ground(P.MILL)))
    print("[village] %d planters, %d scenery (%s)"
          % (planted, placed,
             ", ".join("%s %d" % (k, counts[k]) for k in kinds)))


if __name__ == "__main__":
    main()
