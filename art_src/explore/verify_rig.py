#!/usr/bin/env python3
"""Check a character GLB's skeleton, skinning and animation. No Blender.

    python3 art_src/explore/verify_rig.py

⛔ This exists because the obvious check does not work. Re-importing the GLB
into Blender and reading pose bones reported every rotation as 0.0 at every
frame, and rendering a strip from it produced six identical standing figures
-- which looks exactly like "the animation did not export" and is not. In
Blender 5 an action has to be bound to an action SLOT as well as assigned,
and without that it silently does nothing.

Reading the glTF buffers directly has no such failure mode, and it checks the
file Godot is actually handed. `chuck.glb` -- the phase-1 character that has
been walking around on real hardware since September -- is used as the
CONTROL: a new rig is right if its channels move like that one's do.
"""

import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONTROL = os.path.join(ROOT, "assets", "storybook", "chuck.glb")
SUBJECT = os.path.join(ROOT, "assets", "storybook", "explore",
                       "foundation_chuck.glb")
REQUIRED = ("idle", "walk")


def load(path):
    with open(path, "rb") as handle:
        handle.read(12)
        json_length, _ = struct.unpack("<II", handle.read(8))
        gltf = json.loads(handle.read(json_length))
        buffer_length, _ = struct.unpack("<II", handle.read(8))
        return gltf, handle.read(buffer_length)


def samples(gltf, blob, index):
    accessor = gltf["accessors"][index]
    view = gltf["bufferViews"][accessor["bufferView"]]
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    return [struct.unpack_from("<" + "f" * width, blob,
                               offset + i * width * 4)
            for i in range(accessor["count"])]


def report(path, label):
    gltf, blob = load(path)
    print("%s  %s" % (label, os.path.basename(path)))
    names = [a.get("name") for a in gltf.get("animations", [])]
    skins = gltf.get("skins", [])
    joints = len(skins[0]["joints"]) if skins else 0
    attributes = gltf["meshes"][0]["primitives"][0]["attributes"]
    skinned = "JOINTS_0" in attributes and "WEIGHTS_0" in attributes
    print("   animations %-18s joints %-4d skinned %s"
          % (names, joints, skinned))

    problems = []
    for required in REQUIRED:
        if required not in names:
            problems.append("missing animation %r (player.gd looks it up by "
                            "name)" % required)
    if not skinned:
        problems.append("mesh has no JOINTS_0/WEIGHTS_0 -- it is not skinned")

    moving = {}
    for animation in gltf.get("animations", []):
        count = 0
        for channel in animation["channels"]:
            if channel["target"]["path"] != "rotation":
                continue
            values = samples(gltf, blob,
                             animation["samplers"][channel["sampler"]]["output"])
            spread = max(max(abs(v[i] - values[0][i]) for i in range(4))
                         for v in values)
            if spread > 1e-4:
                count += 1
        moving[animation["name"]] = count
        print("   %-6s rotation channels that MOVE: %d" % (animation["name"],
                                                           count))
        if count == 0:
            problems.append("%r has no moving rotation channel -- the action "
                            "was not applied at export" % animation["name"])
    return moving, problems


if __name__ == "__main__":
    control, _ = report(CONTROL, "CONTROL ")
    subject, problems = report(SUBJECT, "SUBJECT ")
    for name, count in subject.items():
        reference = control.get(name)
        if reference and count < reference * 0.5:
            problems.append("%r moves %d channels where the shipping Chuck "
                            "moves %d" % (name, count, reference))
    print()
    if problems:
        for problem in problems:
            print("FAIL:", problem)
        sys.exit(1)
    print("OK: skeleton, skinning and both animations match the shipping rig.")
