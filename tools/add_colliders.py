#!/usr/bin/env python3
"""Give every solid asset its own collider, from MEASURED footprints.

    python3 tools/add_colliders.py

⭐⭐ AN ASSET KNOWS ITS OWN COLLISION. The alternative -- emitting bodies
from the layout generators -- means every one of the 34 scenery instances
carries a duplicate body and shape in the generated scene, and the same prop
is solid in one scene and not in another. Putting it in the wrapper makes it
a property of the THING, so every consumer gets it, including the look-dev
scenes.

⭐ The numbers come from `tools/measure_footprints.gd`, which reads the real
meshes through Godot. ⛔ Re-run that after rebuilding an asset in Blender and
update this table; a collider invented by eye is either too small (Chuck's
shoulder goes through the wall) or too big (he stops a pace short of a tree),
and both read as the same bug to a child.

⛔ THE LAYER IS 1. `chuck.tscn` is layer 2 with mask 13 = world(1) +
blocks(4) + pedestals(8), so anything meant to stop him has to be on 1.
Pedestals and the bell lever are already solid on layer 8 -- and the lever
still works with a collider on it, which is the evidence that making a thing
solid does not cost its interaction.

⛔ DELIBERATELY NOT SOLID, each for a reason:
  * `blossom`, `mushrooms` -- ground decoration a few centimetres high.
    Stopping a five-year-old dead on a mushroom is worse than letting them
    walk over it.
  * `annette` -- she is TOUCHED to replay the prompt. A body between Chuck
    and her would turn a conversation into a wall.
  * `bunting` -- it is strung overhead.
  * trees are collided on the TRUNK, not the canopy. The measured box is the
    canopy, and a 1.3 m radius would stop Chuck well out in the open with
    nothing visibly in front of him. Walk under the branches, not through
    the trunk. Same for the windmill: the tower stops you, the sails do not.
"""

import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# name: (kind, dimensions, centre x, centre z)
#   box      -> (size_x, size_y, size_z), from the measured AABB
#   cylinder -> (radius, height), the solid CORE rather than the silhouette
SOLID = {
    "cvc/woodshed":        ("box", (3.29, 2.25, 2.34), 0.00, 0.00),
    "cvc/handcart":        ("box", (2.91, 1.17, 1.27), -0.44, 0.00),
    "village/bench":       ("box", (1.85, 0.83, 0.46), 0.00, -0.03),
    "village/bakery":      ("box", (3.88, 4.06, 3.68), -0.11, 0.30),
    "village/bookshop":    ("box", (3.52, 4.72, 3.77), 0.01, 0.37),
    "village/clock_house": ("box", (2.61, 6.78, 3.29), 0.00, 0.40),
    "village/flower_shop": ("box", (3.58, 2.94, 3.73), -0.05, 0.36),
    "village/workshop":    ("box", (5.43, 3.34, 3.53), 0.58, 0.07),
    # ⛔ The building boxes are the FULL measured AABB, which includes the
    # roof overhang, so Chuck stops at the eaves rather than at the wall.
    # That is the safe side of the error: a quarter-metre of air is
    # invisible, a shoulder inside a gable is not.
    "foundation/tree":     ("cylinder", (0.30, 3.10), 0.03, 0.05),
    "village/tree_b":      ("cylinder", (0.26, 3.35), 0.00, -0.04),
    "village/bush":        ("cylinder", (0.62, 0.93), 0.01, 0.03),
    "village/well":        ("cylinder", (0.85, 2.45), 0.02, 0.00),
    "village/fingerpost":  ("cylinder", (0.16, 2.32), 0.06, 0.16),
    "village/planter":     ("cylinder", (0.35, 0.93), 0.00, 0.00),
    "village/windmill":    ("cylinder", (1.40, 6.77), 0.00, 0.33),
}

BODY = '''[node name="Body" type="StaticBody3D" parent="."]
collision_layer = 1
collision_mask = 2

[node name="Hull" type="CollisionShape3D" parent="Body"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, %.3f, %.3f, %.3f)
shape = SubResource("Hull")
'''


def shape_block(kind, dims):
    if kind == "box":
        return ('[sub_resource type="BoxShape3D" id="Hull"]\n'
                'size = Vector3(%.2f, %.2f, %.2f)\n' % dims)
    return ('[sub_resource type="CylinderShape3D" id="Hull"]\n'
            'radius = %.2f\nheight = %.2f\n' % dims)


def main():
    changed = 0
    for name, (kind, dims, cx, cz) in sorted(SOLID.items()):
        path = os.path.join(ROOT, "storybook", name + ".tscn")
        text = io.open(path, encoding="utf-8").read()
        if 'type="StaticBody3D"' in text:
            print("[colliders] %-22s already solid, left alone" % name)
            continue

        # ⛔ load_steps counts sub_resources as well as ext_resources. Godot
        # tolerates a wrong count in a lot of cases and then fails to load in
        # exactly the ones that matter, so keep it honest.
        text = re.sub(r"load_steps=(\d+)",
                      lambda m: "load_steps=%d" % (int(m.group(1)) + 1),
                      text, count=1)

        # The shape goes after the ext_resources and before the first node.
        first_node = text.index("[node ")
        text = (text[:first_node] + shape_block(kind, dims) + "\n"
                + text[first_node:])

        height = dims[1] if kind == "box" else dims[1]
        text = text.rstrip("\n") + "\n\n" + BODY % (cx, height * 0.5, cz)
        io.open(path, "w", encoding="utf-8").write(text)
        print("[colliders] %-22s %-8s %s" % (name, kind, dims))
        changed += 1
    print("[colliders] %d wrappers given a body" % changed)


if __name__ == "__main__":
    main()
