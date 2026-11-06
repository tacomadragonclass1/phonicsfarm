#!/usr/bin/env python3
"""Generate `scenes/cvc_land.tscn`: CVC Land, rebuilt on the new art.

    python3 tools/build_cvc_land.py

⛔ This writes a NEW scene. `scenes/main.tscn` -- the classroom game -- is not
touched. Nothing here reaches a child until the preview build is cut over.

⭐⭐ EVERY POSITION COMES FROM `art_src/explore/cvc_plan.py`, which also
shapes the ground. So the worn tracks run to where the blocks actually are,
and the pedestals stand on the beaten patch that exists because they stand
there. One source, two consumers, no second opinion -- which is exactly what
the last layout pass got wrong.

The routine is UNCHANGED and that is deliberate. `player.gd` finds blocks by
group and proximity, `pedestal.gd` holds one and lifts it, `sound_lever.gd`
reads the three slots left to right and checks the word. None of that cares
where anything is, so this is a layout change wearing no gameplay risk.
"""

import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "scenes", "cvc_land.tscn")
sys.path.insert(0, os.path.join(ROOT, "art_src", "explore"))

import world_plan as P  # noqa: E402

# ⭐ THE LETTERS ARE FROM THE WORD LIST, not from the alphabet. Counted over
# the 516 strict consonant-vowel-consonant words in `assets/words`: 21
# letters can start one and 20 can end one, but `q` and `x` start exactly one
# word each and `j` and `f` end two and three. Those four are dropped -- a
# child hunting for `q` among nineteen blocks is spending their attention on
# the rarest thing in the set.
#
# ⛔ 20 letters appear in BOTH positions, so they are DUPLICATED rather than
# shared. Two `d`s is the price of never making a five-year-old cross the
# clearing in the middle of a word.
# ⛔⛔ EIGHT AND EIGHT, NOT NINETEEN AND EIGHTEEN. The first cut put every
# usable letter out at once and the two consonant zones read as heaps of
# dice -- the woodshed and the cart disappeared behind their own contents.
# The vowel zone was the accidental control in that same frame: five blocks,
# every letter legible, landmark still visible. Five works; nineteen does not.
#
# ⭐ The cost is far smaller than it looks. These eight onsets and eight
# endings still build 192 of the 516 strict CVC words -- bad bag ban bat bed
# beg bet bib bid big bin bit bob bog bud bug bun and on -- which is more
# than a term's worth, and every vowel stays in play.
#
# 👉 The REST are not gone, they are waiting: `cvc_plan.BONUS` reserves a
# fourth site up the north lane for the rare letters and the digraphs, for a
# harder round where Annette names a word to build rather than the child
# choosing freely.
#
# ⛔ b and d sit in BOTH consonant zones on purpose. They are the classic
# reversal pair at this age, and a child who has to tell them apart to
# finish a word is doing the discrimination the game exists for.
ONSET = "bdhlmpst"                     # 8, the most productive openers
VOWEL = "aeiou"                        # 5, and there are only ever five
# ⛔⛔ SEVEN, NOT EIGHT: `w` IS NOT A CONSONANT ENDING. Every word it was
# buying is a vowel+w DIPHTHONG -- bow daw dew dow haw hew how law low maw
# mew mow paw pew pow saw sew sow taw tow -- where the w is part of the vowel
# sound, not a consonant to blend onto the end. Putting those in a
# sound-it-out game teaches the wrong thing, however valid the words are.
#
# ⛔ AND DO NOT PROMOTE THE NEXT ONE DOWN. The three candidates to fill the
# gap are all wrong for different reasons, which is why this stays at seven:
#   y  (+30 words) -- the same diphthong problem; bay day hay lay may pay say
#   r  (+27 words) -- r-controlled vowels, a separate phonics stage entirely
#   s  (+16 words) -- clean phonically, but 12 of the 16 are bis dis hes hos
#                     lis mas mes pas pes pis sis. Junk a five-year-old would
#                     be celebrated for building.
#
# 👉 `w` is BANKED for the reserve set at `cvc_plan.BONUS`, where digraphs
# live -- ow and ew belong there, taught as units, which is the only honest
# way to use it.
ENDING = "bdgmnpt"                     # 7, the most productive TRUE closers

# ⛔⛔ BLOCKS ARE SOLID AND THE PICK-UP IS A RAYCAST. They are StaticBody3D on
# layer 4 and `player.gd::can_reach` casts against mask 13, so a block
# standing behind another block cannot be picked up, and a pile cannot be
# walked into. Chuck's capsule is 0.6 m across and a block is 0.8, so the
# gap between two of them has to clear 0.6 or the zone becomes a maze.
BLOCK = 0.80
AISLE = 1.52


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


def stack_yard(centre, count, facing, rng):
    """Blocks laid out like split logs in a wood yard: rows with aisles.

    ⭐ Rows, not a heap. A heap is unreachable and unwalkable; rows give every
    block a clear line from an aisle, which is what `can_reach` needs, and
    they read as a STORE -- somebody stacked these -- rather than as spill.

    `facing` is the bearing the player arrives on, so the rows run ACROSS it
    and the aisles open toward the approach.
    """
    across = (math.cos(facing), math.sin(facing))
    along = (-across[1], across[0])
    per_row = 4
    rows = int(math.ceil(count / float(per_row)))
    spots = []
    for index in range(count):
        row, column = divmod(index, per_row)
        # ⛔ Offset alternate rows by half a pitch. Square-aligned rows let a
        # back block hide exactly behind a front one, which is the only
        # arrangement `can_reach` can never solve from any standing position.
        shift = 0.5 if row % 2 else 0.0
        a = (column - (per_row - 1) / 2.0 + shift) * (BLOCK + 0.55)
        b = (row - (rows - 1) / 2.0) * AISLE
        spots.append((centre[0] + along[0] * a + across[0] * b
                      + rng.uniform(-0.05, 0.05),
                      centre[1] + along[1] * a + across[1] * b
                      + rng.uniform(-0.05, 0.05)))
    return spots


def ring(centre, count, radius, rng):
    """The vowels, round the foot of the tree. Five is a shape, so use it."""
    return [(centre[0] + math.cos(math.tau * i / count + 0.4) * radius
             + rng.uniform(-0.06, 0.06),
             centre[1] + math.sin(math.tau * i / count + 0.4) * radius
             + rng.uniform(-0.06, 0.06)) for i in range(count)]


def bearing(frm, to):
    return math.atan2(to[1] - frm[1], to[0] - frm[0])


def main():
    rng = random.Random(20261105)
    ext = {
        "Ground": "res://storybook/cvc/ground.tscn",
        "Pedestal": "res://storybook/cvc/pedestal.tscn",
        "Bell": "res://storybook/cvc/bell_lever.tscn",
        "Shed": "res://storybook/cvc/woodshed.tscn",
        "Cart": "res://storybook/cvc/handcart.tscn",
        "Tree": "res://storybook/foundation/tree.tscn",
        "TreeB": "res://storybook/village/tree_b.tscn",
        "Bush": "res://storybook/village/bush.tscn",
        "Block": "res://storybook/foundation/block.tscn",
        "Player": "res://storybook/foundation/chuck.tscn",
        "UI": "res://ui/touch_controls.tscn",
    }
    lines = []
    for key, path in ext.items():
        lines.append('[ext_resource type="PackedScene" path="%s" id="%s"]'
                     % (path, key))
    lines.append('[ext_resource type="Script" '
                 'path="res://environment/fixed_camera.gd" id="Cam"]')
    lines.append('[ext_resource type="Script" '
                 'path="res://storybook/painted_surface.gd" id="Painted"]')
    lines.append('[ext_resource type="ConcavePolygonShape3D" '
                 'path="res://assets/storybook/collision/cvc_ground.res" '
                 'id="GroundShape"]')

    subs = ['''[sub_resource type="ProceduralSkyMaterial" id="SkyMaterial"]
sky_top_color = Color(0.62, 0.66, 0.70, 1)
sky_horizon_color = Color(0.80, 0.82, 0.82, 1)
sky_curve = 0.35
ground_bottom_color = Color(0.46, 0.47, 0.45, 1)
ground_horizon_color = Color(0.74, 0.75, 0.73, 1)
''', '''[sub_resource type="Sky" id="Sky"]
sky_material = SubResource("SkyMaterial")
''', '''; ⛔ THE GRADE IS MEASURED, not matched by eye. Sampled across the frame the
; old build sat at mean saturation 0.707 against a path-traced control's
; 0.304 -- 2.3x over, which is the acid green said as a number. These values
; land within a few percent of the control; `lookdev/measure.py` checks it.
[sub_resource type="Environment" id="Environment"]
background_mode = 2
sky = SubResource("Sky")
ambient_light_source = 2
ambient_light_color = Color(0.58, 0.66, 0.84, 1)
ambient_light_energy = 0.55
tonemap_mode = 4
tonemap_exposure = 1.22
tonemap_white = 2.0
adjustment_enabled = true
adjustment_saturation = 0.78
fog_enabled = true
fog_light_color = Color(0.78, 0.82, 0.86, 1)
fog_density = 0.0022
fog_aerial_perspective = 0.22
fog_sky_affect = 0.1
''']

    body = [node("CVCLand", "Node3D")]
    body.append(node("WorldEnvironment", "WorldEnvironment", ".",
                     environment='SubResource("Environment")'))
    body.append(node("Sun", "DirectionalLight3D", ".",
                     transform=xform((0.0, 0.0), 0.0, 11.0),
                     rotation_degrees="Vector3(-34, 38, 0)",
                     light_color="Color(1, 0.94, 0.83, 1)",
                     light_energy="1.15",
                     light_angular_distance="2.2",
                     shadow_enabled="true",
                     shadow_opacity="1.0",
                     shadow_blur="1.2"))

    # --- the ground, with BAKED collision. ⛔ Never create_trimesh_shape() at
    # load: the web build is single-threaded and 49,298 faces freezes the tab.
    body.append(instance("Ground", "Ground", ".", xform((0.0, 0.0))))
    body.append(node("GroundBody", "StaticBody3D", "."))
    body.append(node("GroundShape", "CollisionShape3D", "GroundBody",
                     shape='ExtResource("GroundShape")'))

    # --- the stage. ⛔ `pedestal_paths` must be SCREEN-left to SCREEN-right,
    # because the lever reads the word off that order. The plan lays the row
    # along its ROW axis, which is screen-horizontal by construction.
    body.append(node("Pedestals", "Node3D", "."))
    for index, point in enumerate(P.PEDESTALS):
        body.append(instance("Pedestal%d" % (index + 1), "Pedestal",
                             "Pedestals", xform(point)))
    # ⛔ THE FRAME'S POSTS RUN ACROSS THE SCREEN, which is a -30 degree yaw
    # against the plan's ROW axis, not a bearing toward the pedestals. Aimed
    # at the pedestals it stood edge-on and read as a sliver.
    #
    # ⛔ The swing is then toward and away from the camera rather than across
    # it, because `sound_lever.gd` rocks $Handle about X and the posts have
    # to lie on that axis. That is the right trade: a bell frame nobody can
    # recognise is worse than a swing that is slightly foreshortened, and
    # the expanding $Pulse ring carries most of the feedback anyway.
    body.append(instance("SoundLever", "Bell", ".",
                         xform(P.BELL, -30.0),
                         pedestal_paths='Array[NodePath]([NodePath('
                         '"../Pedestals/Pedestal1"), NodePath('
                         '"../Pedestals/Pedestal2"), NodePath('
                         '"../Pedestals/Pedestal3")])'))

    # --- the three zones, each with its landmark and its letters.
    body.append(node("Zones", "Node3D", "."))
    body.append(node("Blocks", "Node3D", "."))
    plan = (("onset", ONSET, "Shed"), ("vowel", VOWEL, "Tree"),
            ("ending", ENDING, "Cart"))
    counts = {}
    for name, letters, landmark in plan:
        centre = P.ZONES[name]
        pedestal = P.PEDESTALS[["onset", "vowel", "ending"].index(name)]
        face = bearing(centre, pedestal)
        # The landmark stands at the BACK of its zone, so the letters are
        # between it and the player and nothing is hidden behind it.
        back = (centre[0] - math.cos(face) * 3.3,
                centre[1] - math.sin(face) * 3.3)
        body.append(instance(name.title(), landmark, "Zones",
                             xform(back, math.degrees(face) + 90.0)))
        if name == "vowel":
            spots = ring(centre, len(letters), 1.95, rng)
        else:
            spots = stack_yard(centre, len(letters), face + math.pi / 2, rng)
        counts[name] = len(spots)
        for letter, spot in zip(letters, spots):
            body.append(instance(
                "Block_%s_%s" % (name[0], letter), "Block", "Blocks",
                xform(spot, rng.uniform(0, 360)), letter='"%s"' % letter))

    # --- scenery, kept OUT of the zones and off the tracks.
    body.append(node("Scenery", "Node3D", "."))
    placed = 0
    for attempt in range(400):
        if placed >= 14:
            break
        angle = rng.uniform(0, math.tau)
        radius = rng.uniform(11.0, 19.0)
        point = (P.WORLD_CENTRE[0] + math.cos(angle) * radius,
                 P.WORLD_CENTRE[1] + math.sin(angle) * radius)
        if P.zone_distance(*point) < P.ZONE_RADIUS + 3.4:
            continue
        # ⛔ Keep the reserved bonus site clear. Scenery planted there now
        # would have to be felled later, and the ground is baked.
        if math.hypot(point[0] - P.BONUS[0],
                      point[1] - P.BONUS[1]) < P.BONUS_RADIUS + 2.0:
            continue
        if P.track_distance(*point) < 3.0 or P.approach_distance(*point) < 3.0:
            continue
        if P.stage_distance(*point) < 7.0:
            continue
        # ⛔ And clear of the BELL. The first pass planted a tree two metres
        # off it -- the stage-distance test measures from the pedestals, and
        # the bell stands four metres off the end of that row, so it fell
        # into the gap between two exclusions and got a tree in front of it.
        if math.hypot(point[0] - P.BELL[0], point[1] - P.BELL[1]) < 6.0:
            continue
        if math.hypot(point[0] - P.START[0], point[1] - P.START[1]) < 5.0:
            continue
        kind = ("Tree", "TreeB", "Bush")[placed % 3]
        body.append(instance("Scenery%02d" % placed, kind, "Scenery",
                             xform(point, rng.uniform(0, 360))))
        placed += 1

    body.append(instance("Player", "Player", ".",
                         xform(P.START, math.degrees(
                             bearing(P.START, P.PEDESTALS[1])) * -1 + 90.0)))
    body.append(node("Camera3D", "Camera3D", ".",
                     projection="1", current="true", far="180.0",
                     script='ExtResource("Cam")',
                     pitch_degrees="16.0", yaw_degrees="30.0",
                     zoom="8.2", distance="26.0"))
    body.append(instance("TouchControls", "UI", "."))
    # ⛔⛔ LAST CHILD, AND NOT OPTIONAL. Without it the build renders raw
    # StandardMaterial3D and looks exactly like the asset pack this whole
    # pass was spent escaping -- which is what the first /preview/ export
    # shipped. It is last so every sibling is ready before it walks them.
    body.append(node("PaintedSurface", "Node", ".",
                     script='ExtResource("Painted")'))

    steps = len(lines) + len(subs)
    text = ("[gd_scene load_steps=%d format=3]\n\n" % (steps + 1)
            + "\n".join(lines) + "\n\n" + "\n".join(subs) + "\n"
            + "".join(body))
    with open(OUT, "w") as handle:
        handle.write(text)
    total = sum(counts.values())
    print("[cvc] wrote %s" % OUT)
    print("[cvc] %d blocks (onset %d, vowel %d, ending %d), %d scenery"
          % (total, counts["onset"], counts["vowel"], counts["ending"], placed))


if __name__ == "__main__":
    main()
