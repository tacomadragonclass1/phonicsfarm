"""The asset-production template.

Every build script in `art_src/` is the same five lines of plumbing around a
`build()` that makes geometry. Keeping that plumbing here is what makes a
cottage, a character and a toy block come out looking related: they share a
palette, a bevel language, a surfacing recipe, a texture budget and an export
setting, and none of that is retyped per asset.

To add an asset, copy `art_src/template_asset.py`, change `build()`, and add it
to `art_src/build_all.sh`.
"""

import os

import bpy

from . import exporter, meshtools, painter

PROJECT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".."))
GLB_DIR = os.path.join(PROJECT, "assets", "storybook")
BLEND_DIR = os.path.join(PROJECT, "art_src", "blend")

# Texture sizes by how close the player ever gets, not by how big the asset is.
# The camera is orthographic at size 9 over a 1280-wide viewport, so one metre
# is about 142 px on screen. 512 across a 0.8 m block is already more texels
# than pixels; anything larger is wasted download.
TEXTURE_SMALL = 512    # props the size of a block or a stone
TEXTURE_MEDIUM = 1024  # characters, trees, pedestals
TEXTURE_LARGE = 1024   # buildings and ground -- still 1024; see note above


def produce(name, objects, *, texture=TEXTURE_MEDIUM, roughness=0.92,
            budget_tris=None, with_animation=False, animation_names=None,
            bake_samples=24, gouache=None, smooth_angle=38.0,
            save_source=True):
    """Surface, bake, export and measure a finished set of objects.

    `objects` are the exported nodes in order; `objects[0]` becomes the GLB's
    first node. Objects whose material was made by `painter.flat_material`
    keep it and are skipped by the bake, which is how the alphabet block's
    letter faces stay perfectly flat cream.
    """
    meshes = [o for o in objects if o.type == "MESH"]
    textured = [o for o in meshes
                if not (o.data.materials
                        and all(m is not None and m.get("flat_color")
                                for m in o.data.materials))]

    import math
    for obj in meshes:
        meshtools.merge_doubles(obj)
        # A low angle keeps chamfer facets flat and crisp (carved wood); a
        # high one rounds them off (moulded, organic). It is one of the main
        # dials separating a toy block from a tree canopy.
        meshtools.finish(obj, angle=math.radians(smooth_angle))

    if textured:
        painter.atlas_unwrap(textured)
        material = painter.gouache_material(name + "_paint",
                                            roughness=roughness,
                                            **(gouache or {}))
        for obj in textured:
            if not obj.data.materials:
                obj.data.materials.append(material)
            else:
                for i, existing in enumerate(obj.data.materials):
                    if existing is None or not existing.get("flat_color"):
                        obj.data.materials[i] = material
        image = painter.bake_to_texture(textured, name + "_albedo",
                                        size=texture, samples=bake_samples)
        painter.finalize_material(textured, image, name + "_surface",
                                  roughness=roughness)
    else:
        image = None

    path = os.path.join(GLB_DIR, name + ".glb")

    exporter.export_glb(objects, path, with_animation=with_animation,
                        animation_names=animation_names)
    exporter.report(name, meshes, path, budget_tris=budget_tris, image=image)
    if save_source:
        exporter.save_blend(os.path.join(BLEND_DIR, name + ".blend"))
    return path


def verify_contract(objects, required_names):
    """Fail loudly if a node name a Godot script depends on went missing.

    `alphabet_block.gd` and `player.gd` both reach into the model by node name.
    A rename in Blender would break the game silently at runtime, so it breaks
    the build here instead.
    """
    have = {o.name for o in objects}
    missing = [n for n in required_names if n not in have]
    if missing:
        raise RuntimeError("node names required by Godot are missing: %s "
                           "(present: %s)" % (missing, sorted(have)))
