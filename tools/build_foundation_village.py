#!/usr/bin/env python3
"""Generate `village/foundation_village.tscn`: the re-planned village.

    python3 tools/build_foundation_village.py

⛔ THIS WRITES A NEW SCENE. It does not touch `village/phoneme_village.tscn`,
which is the shipping village, is the owner's source of truth, is edited by
hand in the editor, and which CLAUDE.md says not to regenerate. The shipping
village and the `tests/village.gd` run against it are unaffected.

⛔ Like `tools/build_phoneme_village.py` before it, this is a SCAFFOLD and not
a build step. Once the generated scene has been edited in the editor, the
scene becomes the truth and this script becomes history.

The contract the generated scene satisfies, read out of `phoneme_village.gd`
and `tests/village.gd`:

  * root carries `phoneme_village.gd` and is in group `phoneme_village`
  * `$Annette` is a VillageGuide with an `$Annette/Touch` Area3D
  * `$SpawnPoints` holds the markers; `$Blocks` is the container
  * `$Trigger` is an Area3D covering the village
  * the visibility rule walks the groups Buildings / Props / Terrain /
    Trees / Path / Annette, so those node names are kept
  * spawn markers must exist at THREE heights snapped to 0.5 -- the green,
    the mound's shelf and the mill yard
"""

import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "village", "foundation_village.tscn")

# Godot: X right, Y up, Z toward the camera. The gameplay camera looks from
# +X/-Z, so the village opens toward -Z and the mound sits back and left
# where it can be climbed without standing in front of anything.
# ⛔ THE CAMERA DECIDES WHERE THE BUILDINGS GO. It is orthographic and never
# turns, looking from +X/+Y/+Z, so anything at higher X and Z stands between
# the viewer and everything behind it. The first layout put the flower shop
# and the workshop on the +Z side and 15 of 35 spawn markers failed the
# no-hidden-letter rule outright.
#
# So the village sits on the FAR half (-X/-Z) and the green -- where the
# letters are -- is the near half. That is also simply the better picture:
# you look across an open green AT the village.
GREEN = (1.5, 3.2)
MOUND = (-11.5, 0.0, -5.5)
# ⛔ The mound is TURNED, and that is a visibility fix not a styling one.
# Its shelf and its steps are built on one side of the asset; left unrotated
# that side faced -Z, which is the FAR side from a camera at +X/+Z, so the
# mound hid its own middle level and all seven shelf markers failed. 200
# degrees swings the shelf and the flight round to face the viewer.
MOUND_YAW = 200.0


def rot_xz(lx, lz, yaw_deg):
    """Local offset -> world offset, matching `xform`'s basis exactly."""
    rad = math.radians(yaw_deg)
    c, s = math.cos(rad), math.sin(rad)
    return (lx * c + lz * s, -lx * s + lz * c)


# Where the shelf and the yard sit inside the asset, in its own local frame.
# Blender +Y becomes Godot -Z, which is why these are negative.
SHELF_LOCAL = (-0.19, -5.45)
MOUND_H, SHELF_H = 2.15, 1.05

BUILDINGS = [
    # scene, x, z, yaw degrees, collision half-extents (x, y, z)
    ("bakery",      -4.6, -10.4,  28.0, (1.70, 1.80, 1.45)),
    ("bookshop",     0.6, -11.6,   6.0, (1.55, 2.10, 1.40)),
    ("clock_house",  6.0, -10.2, -18.0, (1.25, 2.80, 1.20)),
    ("flower_shop",  9.8,  -5.4, -46.0, (1.60, 1.50, 1.40)),
    ("workshop",    11.0,   0.8, -78.0, (2.40, 1.50, 1.60)),
]

# Where letters may stand. Rings on the green, plus the two raised levels.
GREEN_R = (3.2, 5.2, 7.2, 9.0)



# ⭐ THE GENERATOR CHECKS VISIBILITY ITSELF. Nudging marker positions by hand
# until the Godot check passes is the wrong loop: it is slow, and the next
# person to move a building silently breaks it again. The same occlusion rule
# the engine applies is implemented here, so the layout is correct BY
# CONSTRUCTION and the Godot check is a confirmation rather than a search.
#
# The camera is orthographic at pitch 30 / yaw 30 and never turns, so the
# direction from a block back to the viewer is one fixed vector for the whole
# board.
CAMERA = (0.433, 0.500, 0.750)


def _occluders(trees):
    """Everything tall enough to hide a letter: x, z, half_x, half_z, top."""
    mill = rot_xz(-1.1, -0.5, MOUND_YAW)
    out = [(MOUND[0], MOUND[2], 8.4, 8.4, 2.15),
           (MOUND[0] + mill[0], MOUND[2] + mill[1], 2.3, 2.3, 8.9),  # the mill
           # ⛔ The FIXED props belong here too. The Godot check walks
           # Buildings / Props / Terrain / Trees / Path / Annette, so
           # anything standing still and taller than a block is an occluder,
           # and leaving them out is why five markers kept failing a test
           # the generator thought it had passed.
           (GREEN[0], GREEN[1], 1.0, 1.0, 2.45),              # the well
           (GREEN[0] - 3.0, GREEN[1] + 1.8, 0.95, 0.75, 2.32),   # fingerpost
           (GREEN[0] + 2.6, GREEN[1] + 1.4, 1.05, 0.45, 0.83),   # bench
           (GREEN[0] - 2.4, GREEN[1] + 3.0, 0.45, 0.45, 1.58),   # Annette
           (-2.0, -11.0, 3.25, 0.30, 2.30)]                      # bunting
    # ⛔ MARGIN. These halves are the COLLISION extents; the Godot check uses
    # real mesh AABBs, which are bigger -- a roof overhangs its walls and a
    # canopy overhangs its trunk. Modelling the collider and testing the mesh
    # leaves a thin band where the generator believes a marker is clear and
    # the engine does not, which is exactly where the last stragglers sat.
    for name, x, z, _, half in BUILDINGS:
        out.append((x, z, half[0] + 1.35, half[2] + 1.35, half[1] * 2.2))
    for x, z, scale in trees:
        out.append((x, z, 1.70 * scale, 1.70 * scale, 3.4 * scale))
    return out


def visible(x, y, z, occluders):
    """Does the ray from this point back to the camera clear every occluder?

    ⛔ An occluder the point is STANDING INSIDE is skipped, exactly as the
    Godot check skips a box containing the sample. Without it the mound's own
    8.4 m footprint rejects every marker on its shelf -- the middle level
    disappeared entirely and the three-level rule failed.
    """
    inside = [(abs(x - o[0]) < o[2] and abs(z - o[1]) < o[3]) for o in occluders]
    step = 0.30
    for index in range(1, 140):
        t = index * step
        px = x + CAMERA[0] * t
        py = y + CAMERA[1] * t
        pz = z + CAMERA[2] * t
        if py > 9.0:
            return True
        for slot, (ox, oz, hx, hz, top) in enumerate(occluders):
            if inside[slot] or top < y - 0.05:
                continue
            if py < top and abs(px - ox) < hx and abs(pz - oz) < hz:
                return False
    return True


def spawns(occluders):
    """Markers on all three levels, clear of every building footprint.

    ⛔ A marker is rejected if it lands within a building's footprint PLUS a
    margin, because the no-hidden-letter rule is about the block being seen
    and a letter tucked against a wall fails it even when it is technically
    outside.
    """
    points = []
    for radius, count, phase in zip(GREEN_R, (10, 13, 14, 12),
                                    (0.0, 0.22, 0.44, 0.66)):
        for index in range(count):
            angle = math.tau * (index / count + phase)
            x = GREEN[0] + math.cos(angle) * radius
            z = GREEN[1] + math.sin(angle) * radius
            if _blocked(x, z) or not visible(x, 0.45, z, occluders):
                continue
            points.append((round(x, 2), 0.0, round(z, 2)))
    # The mound's shelf and its yard: the middle and top levels.
    # The two raised levels. These are tested too -- the mill itself is a
    # 9 m tower and will happily hide a letter on its own yard.
    shelf = rot_xz(SHELF_LOCAL[0], SHELF_LOCAL[1], MOUND_YAW)
    for index in range(9):
        angle = math.radians(-60.0 + index * 15.0)
        x = MOUND[0] + shelf[0] + math.cos(angle) * 1.25
        z = MOUND[2] + shelf[1] + math.sin(angle) * 1.05
        if visible(x, SHELF_H + 0.45, z, occluders):
            points.append((round(x, 2), SHELF_H, round(z, 2)))
    for index in range(11):
        angle = math.radians(-150.0 + index * 22.0)
        x = MOUND[0] + math.cos(angle) * 2.7
        z = MOUND[2] + math.sin(angle) * 2.7
        if visible(x, MOUND_H + 0.45, z, occluders):
            points.append((round(x, 2), MOUND_H, round(z, 2)))
    return points


def _blocked(x, z):
    if math.hypot(x - MOUND[0], z - MOUND[2]) < 9.2:
        return True            # the mound's own footprint and its track
    for _, bx, bz, _, half in BUILDINGS:
        if abs(x - bx) < half[0] + 1.5 and abs(z - bz) < half[2] + 1.5:
            return True
    if math.hypot(x - GREEN[0], z - GREEN[1]) < 2.2:
        return True            # the well stands on the middle of the green
    return False


def occludes(px, pz, top, markers):
    """Would a prop of this height here hide any letter from the camera?

    ⭐ The visibility rule run the OTHER WAY ROUND. Markers are fixed first,
    then every scattered prop is offered a position and refused it if it
    would stand on somebody's sight-line. It is the same arithmetic, and it
    means a bush can never be dropped in front of a letter.
    """
    for mx, my, mz in markers:
        for height in (0.14, 0.42, 0.70):
            sy = my + height
            if top < sy - 0.05:
                continue
            for index in range(1, 90):
                t = index * 0.30
                ry = sy + CAMERA[1] * t
                if ry > top:
                    break
                if (abs(mx + CAMERA[0] * t - px) < 1.1
                        and abs(mz + CAMERA[2] * t - pz) < 1.1):
                    return True
    return False


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


def xform(x, y, z, yaw_deg=0.0, scale=1.0):
    rad = math.radians(yaw_deg)
    c, s = math.cos(rad) * scale, math.sin(rad) * scale
    return ("Transform3D(%.5f, 0, %.5f, 0, %.5f, 0, %.5f, 0, %.5f, "
            "%.3f, %.3f, %.3f)" % (c, -s, scale, s, c, x, y, z))


def main():
    rng = random.Random(20261103)
    assets = {
        "mill_mound": "mill_mound", "windmill": "windmill",
        "bakery": "bakery", "bookshop": "bookshop",
        "clock_house": "clock_house", "flower_shop": "flower_shop",
        "workshop": "workshop", "well": "well", "bench": "bench",
        "fingerpost": "fingerpost", "planter": "planter",
        "bunting": "bunting", "tree_b": "tree_b", "bush": "bush",
        "mushrooms": "mushrooms", "blossom": "blossom",
        "lane_stone": "lane_stone", "wall_run": "wall_run",
    }
    ext = []
    ids = {}
    for index, (key, name) in enumerate(sorted(assets.items())):
        ids[key] = "a%d" % index
        ext.append('[ext_resource type="PackedScene" '
                   'path="res://storybook/village/%s.tscn" id="%s"]'
                   % (name, ids[key]))
    ids["tree"] = "tA"
    ext.append('[ext_resource type="PackedScene" '
               'path="res://storybook/foundation/tree.tscn" id="tA"]')
    ids["annette"] = "an"
    ext.append('[ext_resource type="PackedScene" '
               'path="res://storybook/village/annette.tscn" id="an"]')
    ext.append('[ext_resource type="Script" '
               'path="res://village/phoneme_village.gd" id="vs"]')
    ext.append('[ext_resource type="Script" '
               'path="res://village/annette.gd" id="as"]')
    ext.append('[ext_resource type="Script" '
               'path="res://storybook/foundation/terrain_collision.gd" '
               'id="col"]')

    # Trees first: the spawn test needs to know where they stand.
    tree_spots = []
    attempt = 0
    while len(tree_spots) < 26 and attempt < 600:
        attempt += 1
        angle = math.radians(rng.uniform(0, 360))
        radius = rng.uniform(13.5, 19.0)
        x, z = math.cos(angle) * radius, math.sin(angle) * radius
        if math.hypot(x - MOUND[0], z - MOUND[2]) < 10.0:
            continue
        if x > GREEN[0] + 2.0 and z > GREEN[1] + 2.0:
            continue
        tree_spots.append((x, z, rng.uniform(0.86, 1.14)))
    occluders = _occluders(tree_spots)
    markers = spawns(occluders)

    body = []
    body.append('[node name="PhonemeVillage" type="Node3D" '
                'groups=["phoneme_village"]]\nscript = ExtResource("vs")\n\n')

    # --- Terrain: the mound, and a flat green under everything else.
    body.append(node("Terrain", "Node3D", "."))
    body.append(instance("MillMound", ids["mill_mound"], "Terrain",
                         xform(MOUND[0], MOUND[1], MOUND[2], MOUND_YAW)))
    body.append(node("MoundCollision", "Node", "Terrain/MillMound",
                     script='ExtResource("col")'))
    body.append(node("GreenBody", "StaticBody3D", "Terrain"))
    body.append(node("GreenShape", "CollisionShape3D", "Terrain/GreenBody",
                     shape='SubResource("Green")',
                     position="Vector3(0, -0.5, 0)"))

    # --- Buildings, each with a box collider sized to its footprint.
    body.append(node("Buildings", "Node3D", "."))
    for name, x, z, yaw, half in BUILDINGS:
        body.append(instance(name.title().replace("_", ""), ids[name],
                             "Buildings", xform(x, 0.0, z, yaw)))
        # ⛔ A StaticBody3D with no CollisionShape child is not collision,
        # it is an empty node. The first generated scene had six of them and
        # Chuck walked straight through every building.
        tag = name.title().replace("_", "")
        body.append(node(tag + "Body", "StaticBody3D", "Buildings",
                         transform=xform(x, 0.0, z, yaw)))
        body.append(node(tag + "Shape", "CollisionShape3D",
                         "Buildings/" + tag + "Body",
                         shape='SubResource("Box_%s")' % tag,
                         position="Vector3(0, %.2f, 0)" % half[1]))
    mill = rot_xz(-1.1, -0.5, MOUND_YAW)
    body.append(instance("Windmill", ids["windmill"], "Buildings",
                         xform(MOUND[0] + mill[0], MOUND_H,
                               MOUND[2] + mill[1], 28.0)))

    # --- Props. The well is the centre the obelisk was pretending to be.
    body.append(node("Props", "Node3D", "."))
    body.append(instance("Well", ids["well"], "Props",
                         xform(GREEN[0], 0, GREEN[1])))
    body.append(instance("Bench", ids["bench"], "Props",
                         xform(MOUND[0] + rot_xz(2.0, -2.5, MOUND_YAW)[0], MOUND_H,
                               MOUND[2] + rot_xz(2.0, -2.5, MOUND_YAW)[1], 152.0)))
    body.append(instance("BenchGreen", ids["bench"], "Props",
                         xform(GREEN[0] + 2.6, 0, GREEN[1] + 1.4, -38.0)))
    body.append(instance("Fingerpost", ids["fingerpost"], "Props",
                         xform(GREEN[0] - 3.0, 0, GREEN[1] + 1.8, 16.0)))
    # ⛔ The planters are SEARCHED, not placed. Two of them sat on a
    # sight-line and the Godot check named one as the culprit after three
    # rounds of widening occluder boxes that were not the problem. Anything
    # decorative whose exact spot does not matter should be offered
    # positions and refused the bad ones, rather than modelled and hoped for.
    planted = 0
    for step in range(24):
        angle = math.radians(step * 15.0)
        x = GREEN[0] + math.cos(angle) * 2.3
        z = GREEN[1] + math.sin(angle) * 2.3
        if occludes(x, z, 0.95, markers):
            continue
        body.append(instance("Planter%d" % planted, ids["planter"], "Props",
                             xform(x, 0, z, rng.uniform(0, 360))))
        planted += 1
        if planted == 2:
            break
    body.append(instance("Bunting", ids["bunting"], "Props",
                         xform(-2.0, 1.1, -11.0, 8.0)))
    for index in range(7):
        angle = math.radians(128.0 + index * 34.0)
        radius = 12.0 + rng.uniform(-0.8, 1.4)
        x, z = math.cos(angle) * radius, math.sin(angle) * radius
        if not occludes(x, z, 0.31, markers):
            body.append(instance("Mushrooms%d" % index, ids["mushrooms"],
                                 "Props", xform(x, 0, z, rng.uniform(0, 360))))
    for index in range(20):
        angle = math.radians(rng.uniform(0, 360))
        radius = rng.uniform(4.0, 10.5)
        x = GREEN[0] + math.cos(angle) * radius
        z = GREEN[1] + math.sin(angle) * radius
        if _blocked(x, z):
            continue
        if not occludes(x, z, 0.37, markers):
            body.append(instance("Blossom%d" % index, ids["blossom"], "Props",
                             xform(x, 0, z, rng.uniform(0, 360))))
    for index in range(10):
        angle = math.radians(106.0 + index * 26.0)
        radius = 16.2
        x, z = math.cos(angle) * radius, math.sin(angle) * radius
        if not occludes(x, z, 0.73, markers):
            body.append(instance("Wall%d" % index, ids["wall_run"], "Props",
                                 xform(x, 0, z, math.degrees(angle) + 90.0)))
    for index in range(6):
        angle = math.radians(rng.uniform(0, 360))
        radius = rng.uniform(12.0, 15.0)
        x, z = math.cos(angle) * radius, math.sin(angle) * radius
        if not occludes(x, z, 0.96, markers):
            body.append(instance("Bush%d" % index, ids["bush"], "Props",
                                 xform(x, 0, z, rng.uniform(0, 360))))

    # --- Trees. ⛔ The two silhouettes ALTERNATE. One tree 26 times is
    # wallpaper; `tree_b` exists for exactly this.
    body.append(node("Trees", "Node3D", "."))
    for index, (x, z, scale) in enumerate(tree_spots):
        key = "tree" if index % 2 == 0 else "tree_b"
        body.append(instance("Tree%02d" % index, ids[key], "Trees",
                             xform(x, 0, z, rng.uniform(0, 360), scale=scale)))
    placed = len(tree_spots)

    # --- The lanes. ⛔ Every stone gets its own yaw and size: 51 identical
    # flags laid in a line is a zip fastener.
    body.append(node("Path", "Node3D", "."))
    gx, gz = GREEN
    lanes = [[(gx, gz - 2.4), (gx - 1.8, gz - 6.0), (gx - 4.0, gz - 10.0)],
             [(gx, gz - 2.4), (gx + 1.2, gz - 6.4), (gx + 1.0, gz - 11.0)],
             [(gx + 2.0, gz - 1.2), (gx + 5.0, gz - 4.0), (gx + 6.8, gz - 8.0)],
             [(gx + 2.2, gz + 0.6), (gx + 6.2, gz - 0.6), (gx + 9.0, gz - 2.2)],
             [(gx - 2.2, gz - 0.8), (gx - 6.4, gz - 2.2), (gx - 10.0, gz - 4.6)],
             [(gx - 1.0, gz + 2.2), (gx - 1.6, gz + 5.6), (gx - 2.0, gz + 8.4)]]
    stone = 0
    for lane in lanes:
        for seg in range(len(lane) - 1):
            ax, az = lane[seg]
            bx, bz = lane[seg + 1]
            steps = max(2, int(math.hypot(bx - ax, bz - az) / 0.85))
            for k in range(steps):
                t = k / float(steps)
                x = ax + (bx - ax) * t + rng.uniform(-0.1, 0.1)
                z = az + (bz - az) * t + rng.uniform(-0.1, 0.1)
                # Even a 0.16 m flag can hide the lowest sample on a block,
                # and there are fifty of them. A gap in a lane reads as a
                # missing stone, which is what an old path looks like anyway.
                if occludes(x, z, 0.17, markers):
                    continue
                body.append(instance(
                    "Stone%02d" % stone, ids["lane_stone"], "Path",
                    xform(x, 0, z, rng.uniform(0, 360),
                          scale=rng.uniform(0.82, 1.18))))
                stone += 1

    # --- Annette, on her mark by the green, facing it.
    body.append('[node name="Annette" type="Node3D" parent="."]\n'
                'transform = %s\nscript = ExtResource("as")\n\n'
                % xform(GREEN[0] - 2.4, 0.0, GREEN[1] + 3.0, 196.0))
    body.append(instance("Model", ids["annette"], "Annette"))
    body.append(node("Touch", "Area3D", "Annette", collision_layer="0",
                     collision_mask="2"))
    body.append(node("Shape", "CollisionShape3D", "Annette/Touch",
                     shape='SubResource("Touch")',
                     position="Vector3(0, 0.8, 0)"))

    # --- Trigger and containers.
    body.append(node("Trigger", "Area3D", ".", collision_layer="0",
                     collision_mask="2"))
    body.append(node("Shape", "CollisionShape3D", "Trigger",
                     shape='SubResource("Trigger")',
                     position="Vector3(0, 2.0, 0)"))
    body.append(node("SpawnPoints", "Node3D", "."))
    for index, (x, y, z) in enumerate(markers):
        body.append(node("Spawn%02d" % (index + 1), "Node3D", "SpawnPoints",
                         position="Vector3(%.2f, %.2f, %.2f)" % (x, y, z)))
    body.append(node("Blocks", "Node3D", "."))

    subs = ['[sub_resource type="BoxShape3D" id="Box_%s"]\nsize = Vector3(%.2f, %.2f, %.2f)\n'
            % (n.title().replace("_", ""), h[0] * 2, h[1] * 2, h[2] * 2)
            for n, _, _, _, h in BUILDINGS] + [
        '[sub_resource type="BoxShape3D" id="Green"]\nsize = Vector3(44, 1, 44)\n',
        '[sub_resource type="SphereShape3D" id="Touch"]\nradius = 0.95\n',
        '[sub_resource type="BoxShape3D" id="Trigger"]\nsize = Vector3(40, 6, 40)\n',
    ]
    steps = len(ext) + len(subs)
    text = ("[gd_scene load_steps=%d format=3]\n\n" % (steps + 1)
            + "\n".join(ext) + "\n\n" + "\n".join(subs) + "\n"
            + "".join(body))
    with open(OUT, "w") as handle:
        handle.write(text)
    print("[village] wrote %s" % OUT)
    print("[village] %d spawn markers, %d lane stones, %d trees"
          % (len(markers), stone, placed))
    levels = sorted({round(p[1] * 2) / 2 for p in markers})
    print("[village] spawn levels:", levels)


if __name__ == "__main__":
    main()
