"""GLB export, and the checks that keep an asset inside its budget.

Runtime assets are glTF 2.0 binary (.glb) with the texture embedded. That is
deliberate: GitHub Actions builds the web export and must never need Blender,
so the .glb in `assets/storybook/` is the contract and `art_src/` is only ever
run by hand on a workstation.

Two things here exist because of specific Godot behaviour:

* `export_yup` -- Blender is Z-up, Godot is Y-up. Build Z-up, ship Y-up.
* `rename_glb_animations` -- Blender names a glTF animation after the action,
  and prefixes it with the armature name when more than one object animates.
  `player.gd` looks up the animations "idle" and "walk" by exact name, so the
  names are rewritten in the container rather than hoped for.
"""

import json
import os
import struct

import bpy


def _filtered(op, kwargs):
    """Drop arguments this Blender version's exporter does not know about."""
    known = set(op.get_rna_type().properties.keys())
    return {k: v for k, v in kwargs.items() if k in known}


def export_glb(objects, path, with_animation=False, animation_names=None):
    from . import meshtools
    os.makedirs(os.path.dirname(path), exist_ok=True)

    meshtools.deselect_all()
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

    options = dict(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_texcoords=True,
        export_normals=True,
        export_tangents=False,
        # The bake already carries the colour. Shipping COLOR_0 as well would
        # make Godot multiply it in a second time and double-darken the asset.
        export_vertex_color="NONE",
        export_all_vertex_colors=False,
        export_attributes=False,
        export_cameras=False,
        export_lights=False,
        export_extras=False,
        export_skins=with_animation,
        export_animations=with_animation,
        export_animation_mode="ACTIONS",
        export_bake_animation=False,
        export_force_sampling=True,
        export_optimize_animation_size=False,
        export_nla_strips=False,
        export_def_bones=False,
        export_leaf_bone=False,
        export_morph=False,
        export_try_sparse_sk=False,
    )
    bpy.ops.export_scene.gltf(**_filtered(bpy.ops.export_scene.gltf, options))

    if with_animation and animation_names:
        rename_glb_animations(path, animation_names)
    return path


def rename_glb_animations(path, wanted):
    """Force the glTF animation names to exactly `wanted`.

    Blender does not guarantee the order it writes animations in, so each
    wanted name is matched against the exported names first (an action called
    "chuck_walk" becomes "walk"); only if that fails does this fall back to
    position.
    """
    with open(path, "rb") as handle:
        blob = handle.read()

    magic, version, _ = struct.unpack("<III", blob[:12])
    assert magic == 0x46546C67, "not a GLB"
    offset, chunks = 12, []
    while offset < len(blob):
        length, kind = struct.unpack("<II", blob[offset:offset + 8])
        chunks.append((kind, blob[offset + 8:offset + 8 + length]))
        offset += 8 + length

    gltf = json.loads(chunks[0][1].decode("utf-8"))
    present = [a.get("name", "?") for a in gltf.get("animations", [])]
    if len(present) != len(wanted):
        raise RuntimeError(
            "expected %d animations, the GLB has %d: %s" %
            (len(wanted), len(present), present))
    chosen = {}
    spare = list(range(len(present)))
    for name in wanted:
        hit = next((i for i in spare if name.lower() in present[i].lower()), None)
        if hit is None:
            hit = spare[0]
        chosen[name] = hit
        spare.remove(hit)
    for name, index in chosen.items():
        gltf["animations"][index]["name"] = name

    payload = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    payload += b" " * ((4 - len(payload) % 4) % 4)
    rebuilt = [(0x4E4F534A, payload)] + chunks[1:]
    body = b"".join(struct.pack("<II", len(data), kind) + data
                    for kind, data in rebuilt)
    with open(path, "wb") as handle:
        handle.write(struct.pack("<III", magic, version, 12 + len(body)) + body)
    return [a["name"] for a in gltf["animations"]]


def report(label, objects, path, budget_tris=None, image=None):
    """Print the numbers an art budget is actually judged on."""
    from . import meshtools
    tris = sum(meshtools.tri_count(o) for o in objects if o.type == "MESH")
    materials = {m.name for o in objects if o.type == "MESH"
                 for m in o.data.materials if m}
    size_kb = os.path.getsize(path) / 1024.0
    mn, mx = _combined_bounds(objects)
    print("[asset] %-14s tris=%-6d materials=%-2d glb=%6.1fkB  "
          "size=(%.2f, %.2f, %.2f)  base_z=%.3f%s" % (
              label, tris, len(materials), size_kb,
              mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2], mn[2],
              "  texture=%dx%d" % (image.size[0], image.size[1]) if image else ""))
    if budget_tris and tris > budget_tris:
        print("[asset] WARNING %s is over its %d-triangle budget" %
              (label, budget_tris))
    return tris


def _combined_bounds(objects):
    from . import meshtools
    pts = []
    for obj in objects:
        if obj.type != "MESH" or not obj.data.vertices:
            continue
        mn, mx = meshtools.bounds(obj)
        pts += [mn, mx]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return lo, hi


def save_blend(path):
    """Keep the editable source next to, but never inside, the game assets."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path, check_existing=False,
                                compress=True)
