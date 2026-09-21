#!/usr/bin/env python3
"""One-time scaffold for village/phoneme_village.tscn.

Placing ~140 props, three walkable levels and 39 spawn markers by hand is
error-prone trigonometry, so the first version of the scene is emitted from
this script. Once written the .tscn is the source of truth and is meant to be
edited in the Godot editor -- rerunning this with --force DISCARDS those edits.

Everything walkable is native Godot geometry with hand-authored collision,
matching how the clearing and bridge already work: imported GLBs carry no
colliders, so props are decoration and the ground under them is a box.
"""

import argparse
import math
import random
from pathlib import Path

SEED = 20260920
UNIT = 2.0            # Kenney kits are 1x1 grids; the village builds at 2 units
RADIUS = 17.0         # clearing radius, tree ring just outside it

# --- walkable levels -------------------------------------------------------
# (name, centre x, centre z, size x, size z, top y)
TERRACE = dict(x=8.5, z=-4.0, sx=13.0, sz=14.0, base=0.0, top=1.0)
LOOKOUT = dict(x=11.0, z=-7.0, sx=6.0, sz=6.0, base=1.0, top=2.0)
RAMP_RISE, RAMP_RUN, RAMP_WIDTH, RAMP_THICK = 1.0, 3.0, 3.0, 0.4
RAMPS = [  # (x, z of the low edge, low y)
    dict(x=5.5, z_low=6.0, y_low=0.0),      # ground -> terrace
    dict(x=11.0, z_low=-1.0, y_low=1.0),    # terrace -> lookout
]

COTTAGES = [  # x, z, y, rotation
    (-11.0, -6.0, 0.0, 30), (-13.0, 2.5, 0.0, -20), (-8.5, 8.0, 0.0, 200),
    (-3.0, -12.0, 0.0, 160), (5.0, -13.0, 0.0, 190), (5.5, -8.0, 1.0, 250),
]

NATURE = "res://assets/kenney/nature/%s.glb"
FOREST = "res://assets/kenney/mini_forest/%s.glb"


def ramp_transform(ramp):
    """Place a tilted box so its TOP face runs from the low edge to the high
    edge. Rotating +X about the origin drops the +Z end, so the low edge is
    the +Z end and the slope climbs toward -Z."""
    angle = math.atan2(RAMP_RISE, RAMP_RUN)
    length = math.hypot(RAMP_RISE, RAMP_RUN)
    y_mid = ramp["y_low"] + RAMP_RISE / 2.0
    z_mid = ramp["z_low"] - RAMP_RUN / 2.0
    half = RAMP_THICK / 2.0
    return dict(
        pos=(ramp["x"], y_mid - half * math.cos(angle), z_mid - half * math.sin(angle)),
        deg=math.degrees(angle), length=length)


def on_terrace(x, z, pad=0.0):
    t = TERRACE
    return (abs(x - t["x"]) <= t["sx"] / 2 + pad and abs(z - t["z"]) <= t["sz"] / 2 + pad)


def on_lookout(x, z, pad=0.0):
    l = LOOKOUT
    return (abs(x - l["x"]) <= l["sx"] / 2 + pad and abs(z - l["z"]) <= l["sz"] / 2 + pad)


def build_spawn_points(blockers):
    """Reject-sample well-separated standing room on all three levels."""
    rng = random.Random(SEED)
    points = []

    def free(x, z, y, gap):
        for px, pz, py in points:
            if abs(py - y) < 0.5 and math.dist((x, z), (px, pz)) < gap:
                return False
        return all(math.dist((x, z), (bx, bz)) >= br for bx, bz, br in blockers)

    def fill(count, y, sampler, gap):
        added, tries = 0, 0
        while added < count and tries < 40000:
            tries += 1
            x, z = sampler(rng)
            if free(x, z, y, gap):
                points.append((round(x, 2), round(z, 2), y))
                added += 1
        if added < count:
            raise SystemExit(f"only placed {added}/{count} spawn points at y={y}")

    def ground(r):
        while True:
            a, d = r.uniform(0, math.tau), math.sqrt(r.random()) * 15.0
            x, z = math.cos(a) * d, math.sin(a) * d
            # Ground points must not sit inside the terrace or on its ramp.
            if on_terrace(x, z, 0.8) or (abs(x - 5.5) < 2.4 and 2.4 < z < 7.4):
                continue
            return x, z

    def terrace(r):
        t = TERRACE
        while True:
            x = r.uniform(t["x"] - t["sx"] / 2 + 1.2, t["x"] + t["sx"] / 2 - 1.2)
            z = r.uniform(t["z"] - t["sz"] / 2 + 1.2, t["z"] + t["sz"] / 2 - 1.2)
            if on_lookout(x, z, 0.8) or (abs(x - 11.0) < 2.2 and -4.6 < z < 0.6):
                continue
            return x, z

    def lookout(r):
        l = LOOKOUT
        return (r.uniform(l["x"] - 1.9, l["x"] + 1.9),
                r.uniform(l["z"] - 1.9, l["z"] + 1.9))

    fill(26, 0.0, ground, 2.4)
    fill(8, 1.0, terrace, 2.2)
    fill(5, 2.0, lookout, 1.7)
    return points


class Scene:
    """Minimal .tscn writer. Emits position/rotation/scale rather than packed
    Transform3D values so the numbers stay readable in a diff."""

    def __init__(self):
        self.ext, self.sub, self.nodes = {}, [], []

    def resource(self, path, kind="PackedScene"):
        if path not in self.ext:
            self.ext[path] = (f"r{len(self.ext)}", kind)
        return self.ext[path][0]

    def subresource(self, ident, kind, body):
        self.sub.append((ident, kind, body))
        return ident

    def node(self, line, props=()):
        self.nodes.append((line, [p for p in props if p]))

    def prop(self, model, parent, name, x, z, y=0.0, rot=0.0, scale=UNIT, folder=NATURE):
        ident = self.resource(folder % model)
        self.node(f'[node name="{name}" parent="{parent}" instance=ExtResource("{ident}")]', [
            f"position = Vector3({x:.3f}, {y:.3f}, {z:.3f})",
            f"rotation_degrees = Vector3(0, {rot:.2f}, 0)" if rot else None,
            (f"scale = Vector3({scale:.3f}, {scale:.3f}, {scale:.3f})"
             if not isinstance(scale, tuple)
             else "scale = Vector3(%.3f, %.3f, %.3f)" % scale),
        ])

    def render(self):
        steps = len(self.ext) + len(self.sub)
        out = [f"[gd_scene load_steps={steps + 1} format=3]", ""]
        for path, (ident, kind) in self.ext.items():
            out.append(f'[ext_resource type="{kind}" path="{path}" id="{ident}"]')
        out.append("")
        for ident, kind, body in self.sub:
            out.append(f'[sub_resource type="{kind}" id="{ident}"]')
            out.extend(body)
            out.append("")
        for line, props in self.nodes:
            out.append(line)
            out.extend(props)
            out.append("")
        return "\n".join(out).rstrip() + "\n"


def build():
    s = Scene()
    script = s.resource("res://village/phoneme_village.gd", "Script")
    props_script = s.resource("res://environment/kenney_props.gd", "Script")

    # Deliberately NOT the clearing's grass colour, and one shade per level:
    # a raised level skinned in the green below it reads as flat from the
    # game's fixed overhead camera, which is the only view the child gets.
    grass = s.subresource("TerraceGrass", "StandardMaterial3D",
                          ["albedo_color = Color(0.56, 0.73, 0.41, 1)", "roughness = 1.0"])
    grass_high = s.subresource("LookoutGrass", "StandardMaterial3D",
                               ["albedo_color = Color(0.66, 0.79, 0.45, 1)", "roughness = 1.0"])
    earth = s.subresource("Earth", "StandardMaterial3D",
                          ["albedo_color = Color(0.5, 0.38, 0.25, 1)", "roughness = 1.0"])
    dirt = s.subresource("Dirt", "StandardMaterial3D",
                         ["albedo_color = Color(0.55, 0.45, 0.31, 1)", "roughness = 1.0"])

    # --- root ---
    s.node('[node name="PhonemeVillage" type="Node3D" groups=["phoneme_village"]]',
           [f'script = ExtResource("{script}")'])

    # --- walkable terrain -------------------------------------------------
    s.node('[node name="Terrain" type="StaticBody3D" parent="."]',
           ["collision_layer = 1", "collision_mask = 2"])

    for key, plate in (("Terrace", TERRACE), ("Lookout", LOOKOUT)):
        height = plate["top"] - plate["base"]
        cap = 0.16
        body = s.subresource(f"{key}Body", "BoxMesh", [
            f'material = SubResource("{earth}")',
            f'size = Vector3({plate["sx"]:.2f}, {height - cap:.2f}, {plate["sz"]:.2f})'])
        top = s.subresource(f"{key}Cap", "BoxMesh", [
            'material = SubResource("%s")' % (grass if key == "Terrace" else grass_high),
            f'size = Vector3({plate["sx"]:.2f}, {cap:.2f}, {plate["sz"]:.2f})'])
        shape = s.subresource(f"{key}Shape", "BoxShape3D", [
            f'size = Vector3({plate["sx"]:.2f}, {height:.2f}, {plate["sz"]:.2f})'])
        mid = plate["base"] + height / 2.0
        s.node(f'[node name="{key}Body" type="MeshInstance3D" parent="Terrain"]', [
            f'position = Vector3({plate["x"]:.2f}, {plate["base"] + (height - cap) / 2.0:.3f}, {plate["z"]:.2f})',
            f'mesh = SubResource("{body}")'])
        s.node(f'[node name="{key}Cap" type="MeshInstance3D" parent="Terrain"]', [
            f'position = Vector3({plate["x"]:.2f}, {plate["top"] - cap / 2.0:.3f}, {plate["z"]:.2f})',
            f'mesh = SubResource("{top}")'])
        s.node(f'[node name="{key}Shape" type="CollisionShape3D" parent="Terrain"]', [
            f'position = Vector3({plate["x"]:.2f}, {mid:.3f}, {plate["z"]:.2f})',
            f'shape = SubResource("{shape}")'])

    for index, ramp in enumerate(RAMPS, start=1):
        placed = ramp_transform(ramp)
        mesh = s.subresource(f"Ramp{index}Mesh", "BoxMesh", [
            f'material = SubResource("{dirt}")',
            f"size = Vector3({RAMP_WIDTH:.2f}, {RAMP_THICK:.2f}, {placed['length']:.5f})"])
        shape = s.subresource(f"Ramp{index}Shape", "BoxShape3D", [
            f"size = Vector3({RAMP_WIDTH:.2f}, {RAMP_THICK:.2f}, {placed['length']:.5f})"])
        for suffix, resource, kind in (("Mesh", mesh, "MeshInstance3D"),
                                       ("Shape", shape, "CollisionShape3D")):
            key = "mesh" if suffix == "Mesh" else "shape"
            s.node(f'[node name="Ramp{index}{suffix}" type="{kind}" parent="Terrain"]', [
                "position = Vector3(%.3f, %.3f, %.3f)" % placed["pos"],
                f"rotation_degrees = Vector3({placed['deg']:.4f}, 0, 0)",
                f'{key} = SubResource("{resource}")'])

    # --- cottages ---------------------------------------------------------
    s.node('[node name="Buildings" type="Node3D" parent="."]')
    house_shape = s.subresource("HouseShape", "BoxShape3D", ["size = Vector3(2.0, 2.2, 2.0)"])
    blockers = []
    for index, (x, z, y, rot) in enumerate(COTTAGES, start=1):
        s.node(f'[node name="Cottage{index}" type="StaticBody3D" parent="Buildings"]', [
            f"position = Vector3({x:.2f}, {y:.2f}, {z:.2f})",
            f"rotation_degrees = Vector3(0, {rot}, 0)",
            "collision_layer = 1", "collision_mask = 2"])
        s.prop("building-platform", f"Buildings/Cottage{index}", "Base",
               0, 0, 0.0, 0, (UNIT, 0.3, UNIT), folder=FOREST)
        s.prop("building-structure", f"Buildings/Cottage{index}", "Walls",
               0, 0, 0.15, 0, UNIT, folder=FOREST)
        s.prop("building-roof", f"Buildings/Cottage{index}", "Roof",
               0, 0, 2.15, 0, UNIT, folder=FOREST)
        s.node(f'[node name="Shape" type="CollisionShape3D" parent="Buildings/Cottage{index}"]', [
            "position = Vector3(0, 1.1, 0)", f'shape = SubResource("{house_shape}")'])
        blockers.append((x, z, 2.6))

    # --- nature props (metallic materials softened by the group script) ----
    s.node('[node name="Props" type="Node3D" parent="."]',
           [f'script = ExtResource("{props_script}")'])

    # village green
    s.prop("campfire_stones", "Props", "Campfire", 0.0, 1.5, 0.0, 0, 3.4)
    for index, (x, z, rot) in enumerate([(-2.4, 2.4, 25), (2.4, 2.6, -40), (0.2, -1.0, 95)], 1):
        s.prop("log", "Props", f"SeatLog{index}", x, z, 0.0, rot, 2.6)
    s.prop("statue_obelisk", "Props", "Obelisk", -4.6, -2.0, 0.0, 15, 2.4)
    s.prop("sign", "Props", "Signpost", 1.8, 12.4, 0.0, 8, 2.6)
    s.prop("pot_large", "Props", "Pot1", -6.2, 4.4, 0.0, 0, 2.0)
    s.prop("pot_large", "Props", "Pot2", -5.4, 5.6, 0.0, 40, 1.7)
    blockers += [(0.0, 1.5, 2.0), (-4.6, -2.0, 1.6), (1.8, 12.4, 1.4)]

    # crop plot, west-south, ringed by a low fence
    for row in range(4):
        z = 8.0 + row * 1.4
        s.prop("crops_dirtRow", "Props", f"DirtRow{row}", -12.0, z, 0.0, 0, (4.6, 2.0, 2.2))
        for col in range(3):
            # Pumpkins, not wheat: the wheat model's largest surface is an
            # untextured "_defaultMat" at pure white and the patch read as a
            # glitch. Pumpkins are one readable orange shape each.
            s.prop("crop_pumpkin", "Props", f"Pumpkin{row}{col}",
                   -13.6 + col * 1.6, z, 0.06, (row * 53 + col * 29) % 360, 2.4)
    for index in range(6):
        s.prop("fence_simple", "Props", f"CropFenceN{index}", -14.6 + index * 2.0, 6.8, 0.0, 0, 2.0)
    for index in range(4):
        s.prop("fence_simple", "Props", f"CropFenceW{index}", -15.0, 7.8 + index * 2.0, 0.0, 90, 2.0)
    blockers.append((-12.5, 9.5, 5.4))

    # camp corner, east of the green
    s.prop("tent_smallOpen", "Props", "CampTent", 13.4, 7.0, 0.0, 205, 2.8)
    s.prop("campfire_stones", "Props", "CampFire", 11.2, 8.6, 0.0, 0, 2.6)
    blockers += [(13.4, 7.0, 2.4), (11.2, 8.6, 1.6)]

    # Boulders along each plateau rim. They sit ON the level so the edge reads
    # as a rocky outcrop from above, and they mark where the drop is.
    rim_rng = random.Random(SEED + 3)
    edge_count = 0
    for plate, ramp_gap, skip_lookout in ((TERRACE, (4.0, 7.0, 3.0), True),
                                          (LOOKOUT, (9.5, 12.5, -4.0), False)):
        x0, x1 = plate["x"] - plate["sx"] / 2, plate["x"] + plate["sx"] / 2
        z0, z1 = plate["z"] - plate["sz"] / 2, plate["z"] + plate["sz"] / 2
        rim = []
        step = 2.1
        n = max(2, int((x1 - x0) / step))
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            rim += [(x, z0), (x, z1)]
        n = max(2, int((z1 - z0) / step))
        for i in range(1, n):
            z = z0 + (z1 - z0) * i / n
            rim += [(x0, z), (x1, z)]
        for x, z in rim:
            # Leave the ramp landing clear, and do not wall in the lookout.
            if ramp_gap[0] - 0.6 <= x <= ramp_gap[1] + 0.6 and abs(z - ramp_gap[2]) < 1.2:
                continue
            if skip_lookout and on_lookout(x, z, 0.6):
                continue
            edge_count += 1
            s.prop(["rock_largeA", "rock_largeB", "rock_smallA"][edge_count % 3],
                   "Props", f"Rim{edge_count:02d}",
                   x + rim_rng.uniform(-0.25, 0.25), z + rim_rng.uniform(-0.25, 0.25),
                   plate["top"] - 0.15, rim_rng.uniform(0, 360), rim_rng.uniform(1.1, 1.9))

    # undergrowth
    rng = random.Random(SEED + 1)
    scatter = ["flower_redA", "flower_yellowA", "flower_purpleA",
               "mushroom_redGroup", "plant_bushDetailed"]
    placed = 0
    while placed < 34:
        angle, distance = rng.uniform(0, math.tau), math.sqrt(rng.random()) * 16.2
        x, z = math.cos(angle) * distance, math.sin(angle) * distance
        y = 0.0
        if on_lookout(x, z):
            y = 2.0
        elif on_terrace(x, z):
            if abs(x - 11.0) < 2.0 and -5.0 < z < 1.0:
                continue
            y = 1.0
        elif abs(x - 5.5) < 2.2 and 2.6 < z < 7.2:
            continue
        if any(math.dist((x, z), (bx, bz)) < br * 0.8 for bx, bz, br in blockers):
            continue
        placed += 1
        s.prop(scatter[placed % len(scatter)], "Props", f"Scatter{placed}",
               x, z, y, rng.uniform(0, 360), rng.uniform(1.8, 3.2))

    # --- stone path from the south gate to the green -----------------------
    s.node('[node name="Path" type="Node3D" parent="."]',
           [f'script = ExtResource("{props_script}")'])
    z = 16.4
    index = 0
    while z > 3.0:
        index += 1
        s.prop("path_stone", "Path", f"Stone{index}", 0.0, z, 0.01, 0, UNIT)
        z -= 1.16
    for index, offset in enumerate(range(0, 5), 1):  # branch east toward the ramp
        s.prop("path_stone", "Path", f"Branch{index}", 1.4 + offset * 1.16, 5.4, 0.01, 90, UNIT)

    # --- tree ring --------------------------------------------------------
    s.node('[node name="Trees" type="Node3D" parent="."]')
    tree_shape = s.subresource("TrunkShape", "CylinderShape3D",
                               ["radius = 0.26", "height = 2.2"])
    rng = random.Random(SEED + 2)
    count = 0
    for step in range(30):
        angle = math.tau * step / 30.0
        # Leave the south gate open so Chuck can walk in from CVC Land.
        if abs(math.sin(angle)) > 0.93 and math.sin(angle) > 0:
            continue
        distance = RADIUS + rng.uniform(1.0, 2.6)
        x, z = math.cos(angle) * distance, math.sin(angle) * distance
        count += 1
        scale = rng.uniform(1.5, 2.1)
        s.node(f'[node name="Tree{count:02d}" type="StaticBody3D" parent="Trees"]', [
            f"position = Vector3({x:.2f}, 0, {z:.2f})",
            "collision_layer = 1", "collision_mask = 2"])
        s.prop("tree-high" if count % 3 == 0 else "tree", f"Trees/Tree{count:02d}", "Model",
               0, 0, 0.0, rng.uniform(0, 360), scale, folder=FOREST)
        s.node(f'[node name="Trunk" type="CollisionShape3D" parent="Trees/Tree{count:02d}"]', [
            "position = Vector3(0, 1.1, 0)", f'shape = SubResource("{tree_shape}")'])

    # --- Annette, the village voice ---------------------------------------
    annette = s.resource("res://assets/kenney/mini_characters/character-female-a.glb")
    s.node('[node name="Annette" type="Node3D" parent="."]',
           ["position = Vector3(-2.2, 0, 12.6)", "rotation_degrees = Vector3(0, 8, 0)"])
    s.node(f'[node name="Model" parent="Annette" instance=ExtResource("{annette}")]',
           ["scale = Vector3(1.8, 1.8, 1.8)"])
    reach = s.subresource("AnnetteReach", "CylinderShape3D",
                          ["radius = 1.15", "height = 3.0"])
    # Walking into Annette makes her repeat the sound. She is not solid -- a
    # five-year-old should never be able to wedge Chuck against the teacher.
    s.node('[node name="Touch" type="Area3D" parent="Annette"]',
           ["collision_layer = 0", "collision_mask = 2", "monitoring = true"])
    s.node('[node name="Shape" type="CollisionShape3D" parent="Annette/Touch"]',
           ["position = Vector3(0, 1.1, 0)", f'shape = SubResource("{reach}")'])

    # --- entry trigger ----------------------------------------------------
    trigger = s.subresource("TriggerShape", "CylinderShape3D",
                            [f"radius = {RADIUS + 1.5:.1f}", "height = 8.0"])
    s.node('[node name="Trigger" type="Area3D" parent="."]',
           ["collision_layer = 0", "collision_mask = 2", "monitoring = true"])
    s.node('[node name="Shape" type="CollisionShape3D" parent="Trigger"]',
           ["position = Vector3(0, 3, 0)", f'shape = SubResource("{trigger}")'])

    # --- spawn markers and the round's block container --------------------
    s.node('[node name="SpawnPoints" type="Node3D" parent="."]')
    for index, (x, z, y) in enumerate(build_spawn_points(blockers), 1):
        s.node(f'[node name="Spawn{index:02d}" type="Marker3D" parent="SpawnPoints"]',
               [f"position = Vector3({x}, {y}, {z})"])
    s.node('[node name="Blocks" type="Node3D" parent="."]')
    return s.render()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path,
                    default=Path(__file__).resolve().parent.parent / "village/phoneme_village.tscn")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing scene, DISCARDING any editor changes")
    args = ap.parse_args()
    if args.output.exists() and not args.force:
        raise SystemExit(f"{args.output} exists; refusing to discard editor edits (--force)")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build())
    print(f"wrote {args.output}")
