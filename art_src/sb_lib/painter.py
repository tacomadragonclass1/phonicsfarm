"""Painterly surfacing: the gouache shader, the UV atlas, and the bake.

Why bake at all? Because a flat colour per face is exactly the "generic
low-poly asset-store" look we are getting away from. What makes hand-painted
game art read as painted is value variation that follows the FORM -- darker in
creases, lighter on edges, broad uneven washes across big surfaces. Cycles
knows the form, so we let it compute that once, into a texture, and ship a
texture the browser can draw for free.

The chain per asset is:

    parts coloured with `set_part_color`   (vertex colours)
        -> joined into as few objects as possible
        -> `atlas_unwrap()`                (one shared UV layout)
        -> `gouache_material()`            (procedural, Cycles-only)
        -> `bake_to_texture()`             (albedo x AO x pointiness x wash)
        -> `finalize_material()`           (plain image -> Principled)
        -> GLB

What lands in Godot is one material, one texture, no custom shader, no
transparency, metallic 0. That is as cheap as a textured mesh gets, and it
survives the Compatibility renderer unchanged.
"""

import math

import bmesh
import bpy

from . import palette


# ------------------------------------------------------------------ the look

def gouache_material(name, roughness=0.92, wash=0.16, grain=0.055,
                     ao_strength=0.55, ao_distance=0.40, edge_light=0.18,
                     edge_dark=0.13, streak=0.09, wash_scale=3.1,
                     grain_scale=48.0, streak_scale=7.0,
                     paint_attribute="Paint"):
    """A Cycles material that paints vertex colour the way a brush would.

    Every term is deliberately small. The whole point is that no single effect
    is visible as an effect -- together they stop a surface looking like a
    solid fill.

    wash        broad uneven value drift, as if colour were laid on in passes
    grain       the tooth of the paper, barely there
    ao_strength how much creases darken. The main "sculpted" cue
    edge_light  how much convex edges lighten. The other half of that cue
    edge_dark   how much concave creases darken, for shapes AO cannot see
    streak      faint directional brush marks

    Every noise is pushed through `_contrast` first. Raw Blender noise sits in
    a narrow band around 0.5, so without that step an amplitude of 0.10 lands
    as about 1% of actual variation -- which bakes out as a flat fill and
    throws away the entire point of the texture.
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (1400, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (1100, 0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    base = nodes.new("ShaderNodeAttribute")
    base.location = (-800, 300)
    base.attribute_name = paint_attribute

    coord = nodes.new("ShaderNodeTexCoord")
    coord.location = (-1200, -200)

    # --- broad wash: large soft noise, object space so it crosses UV seams ---
    wash_tex = nodes.new("ShaderNodeTexNoise")
    wash_tex.location = (-900, -100)
    wash_tex.inputs["Scale"].default_value = wash_scale
    wash_tex.inputs["Detail"].default_value = 4.0
    wash_tex.inputs["Roughness"].default_value = 0.55
    links.new(coord.outputs["Object"], wash_tex.inputs["Vector"])

    # --- paper tooth: fine noise, very low amplitude ------------------------
    grain_tex = nodes.new("ShaderNodeTexNoise")
    grain_tex.location = (-900, -400)
    grain_tex.inputs["Scale"].default_value = grain_scale
    grain_tex.inputs["Detail"].default_value = 2.0
    links.new(coord.outputs["Object"], grain_tex.inputs["Vector"])

    # --- brush streaks: noise stretched along one axis -----------------------
    streak_map = nodes.new("ShaderNodeMapping")
    streak_map.location = (-1000, -700)
    streak_map.inputs["Scale"].default_value = (1.0, 9.0, 1.4)
    links.new(coord.outputs["Object"], streak_map.inputs["Vector"])
    streak_tex = nodes.new("ShaderNodeTexNoise")
    streak_tex.location = (-800, -700)
    streak_tex.inputs["Scale"].default_value = streak_scale
    streak_tex.inputs["Detail"].default_value = 2.0
    links.new(streak_map.outputs["Vector"], streak_tex.inputs["Vector"])

    def contrast(src, loc, low=0.34, high=0.66):
        """Stretch a noise's useful band out to a full 0..1 swing."""
        node = nodes.new("ShaderNodeMapRange")
        node.location = loc
        node.inputs["From Min"].default_value = low
        node.inputs["From Max"].default_value = high
        node.clamp = True
        links.new(src, node.inputs["Value"])
        return node.outputs[0]

    def centred(src, amount, loc):
        """noise(0..1) -> 1 +/- amount, so it multiplies without shifting value."""
        sub = nodes.new("ShaderNodeMath")
        sub.operation = "SUBTRACT"
        sub.location = loc
        sub.inputs[1].default_value = 0.5
        links.new(src, sub.inputs[0])
        mul = nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.location = (loc[0] + 180, loc[1])
        mul.inputs[1].default_value = amount * 2.0
        links.new(sub.outputs[0], mul.inputs[0])
        add = nodes.new("ShaderNodeMath")
        add.operation = "ADD"
        add.location = (loc[0] + 360, loc[1])
        add.inputs[1].default_value = 1.0
        links.new(mul.outputs[0], add.inputs[0])
        return add.outputs[0]

    wash_f = centred(contrast(wash_tex.outputs["Fac"], (-760, -160)),
                     wash, (-700, -100))
    grain_f = centred(contrast(grain_tex.outputs["Fac"], (-760, -460), 0.38, 0.62),
                      grain, (-700, -400))
    streak_f = centred(contrast(streak_tex.outputs["Fac"], (-700, -760), 0.36, 0.64),
                       streak, (-600, -700))

    # --- creases darken (AO) -------------------------------------------------
    ao = nodes.new("ShaderNodeAmbientOcclusion")
    ao.location = (-900, 650)
    ao.samples = 16
    ao.only_local = True
    ao.inputs["Distance"].default_value = ao_distance

    ao_f = nodes.new("ShaderNodeMapRange")
    ao_f.location = (-650, 650)
    ao_f.inputs["From Min"].default_value = 0.0
    ao_f.inputs["From Max"].default_value = 1.0
    ao_f.inputs["To Min"].default_value = 1.0 - ao_strength
    ao_f.inputs["To Max"].default_value = 1.0
    links.new(ao.outputs["AO"], ao_f.inputs["Value"])

    # --- convex edges catch light (pointiness) -------------------------------
    geo = nodes.new("ShaderNodeNewGeometry")
    geo.location = (-900, 950)
    edge = nodes.new("ShaderNodeMapRange")
    edge.location = (-650, 950)
    edge.inputs["From Min"].default_value = 0.42
    edge.inputs["From Max"].default_value = 0.60
    edge.inputs["To Min"].default_value = 1.0 - edge_dark
    edge.inputs["To Max"].default_value = 1.0 + edge_light
    edge.clamp = True
    links.new(geo.outputs["Pointiness"], edge.inputs["Value"])

    # --- multiply everything into the vertex colour --------------------------
    chain = base.outputs["Color"]
    for factor, loc in ((ao_f.outputs[0], (-250, 500)),
                        (edge.outputs[0], (-50, 500)),
                        (wash_f, (150, 500)),
                        (grain_f, (350, 500)),
                        (streak_f, (550, 500))):
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.location = loc
        mix.inputs["Factor"].default_value = 1.0
        links.new(chain, mix.inputs[6])
        fac_to_rgb = nodes.new("ShaderNodeCombineColor")
        fac_to_rgb.location = (loc[0] - 150, loc[1] - 220)
        for i in range(3):
            links.new(factor, fac_to_rgb.inputs[i])
        links.new(fac_to_rgb.outputs["Color"], mix.inputs[7])
        chain = mix.outputs[2]

    links.new(chain, bsdf.inputs["Base Color"])
    mat.node_tree.nodes.active = bsdf
    return mat


def flat_material(name, color_name, roughness=0.95):
    """A deliberately plain material. Used where texture would hurt.

    The alphabet block's five letter faces use this. The letter is the thing
    being taught, so it gets the highest contrast available and a perfectly
    plain ground; any painterly variation behind a letterform is just noise
    competing with it.
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = palette.linear(color_name)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    mat["flat_color"] = color_name
    return mat


def assign(objects, material) -> None:
    for obj in objects:
        obj.data.materials.clear()
        obj.data.materials.append(material)


# ------------------------------------------------------------------- the UVs

def atlas_unwrap(objects, margin=0.012, fill=0.60) -> None:
    """Pack several objects into ONE shared 0-1 UV layout.

    Blender's cross-object island packing needs a UV editor context that a
    `--background` run does not have, so this does the packing itself: unwrap
    each object into its own 0-1 square, then shelf-pack those squares by
    surface area. Texel density varies a little between parts, which is
    invisible here because the painterly detail is generated in OBJECT space,
    not UV space -- seams and density simply do not show.
    """
    objects = [o for o in objects if o.type == "MESH" and o.data.polygons]
    if not objects:
        return

    for obj in objects:
        _unwrap_single(obj)

    if len(objects) == 1:
        # Nothing to pack around: give the whole sheet to the one object.
        _remap_uvs(objects[0], margin, margin, 1.0 - margin * 2.0)
        return

    areas = [max(_surface_area(o), 1e-6) for o in objects]
    sides = [math.sqrt(a) for a in areas]
    order = sorted(range(len(objects)), key=lambda i: -sides[i])

    scale = math.sqrt(fill / sum(s * s for s in sides))
    for _ in range(40):
        placed = _shelf_pack([sides[i] * scale for i in order], margin)
        if placed is not None:
            break
        scale *= 0.93
    else:
        raise RuntimeError("UV atlas packing did not converge")

    for slot, idx in enumerate(order):
        x, y, side = placed[slot]
        _remap_uvs(objects[idx], x, y, side)


def _shelf_pack(sides, margin):
    """Left-to-right rows of squares inside the unit square. None if it spills."""
    out = []
    cursor_x, cursor_y, row_h = margin, margin, 0.0
    for side in sides:
        if cursor_x + side + margin > 1.0:
            cursor_x = margin
            cursor_y += row_h + margin
            row_h = 0.0
        if cursor_y + side + margin > 1.0:
            return None
        out.append((cursor_x, cursor_y, side))
        cursor_x += side + margin
        row_h = max(row_h, side)
    return out


def _unwrap_single(obj) -> None:
    from . import meshtools
    meshtools.activate(obj)
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(64.0),
                             island_margin=0.02,
                             correct_aspect=True,
                             scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")


def _surface_area(obj) -> float:
    return sum(p.area for p in obj.data.polygons)


def _remap_uvs(obj, x, y, side) -> None:
    layer = obj.data.uv_layers.active.data
    for loop in layer:
        loop.uv[0] = x + loop.uv[0] * side
        loop.uv[1] = y + loop.uv[1] * side


# ------------------------------------------------------------------ the bake

def bake_to_texture(objects, image_name, size=1024, samples=24, margin=10):
    """Bake base colour (with AO and edge light folded in) to one image.

    `DIFFUSE` with direct and indirect lighting switched off bakes exactly the
    Base Color input of the Principled BSDF, which is where `gouache_material`
    put the whole painterly chain. No lights are needed and none are baked in,
    so the asset still lights correctly in Godot.
    """
    from . import meshtools

    image = bpy.data.images.new(image_name, width=size, height=size,
                                alpha=False, float_buffer=False)
    image.generated_color = (0.5, 0.5, 0.5, 1.0)
    image.colorspace_settings.name = "sRGB"

    targets = []
    for obj in objects:
        for mat in obj.data.materials:
            if mat is None or mat.get("flat_color"):
                continue
            node = mat.node_tree.nodes.new("ShaderNodeTexImage")
            node.image = image
            node.location = (600, -900)
            node.select = True
            mat.node_tree.nodes.active = node
            targets.append((mat, node))
    if not targets:
        return None

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.render.bake.use_pass_direct = False
    scene.render.bake.use_pass_indirect = False
    scene.render.bake.use_pass_color = True
    scene.render.bake.margin = margin
    scene.render.bake.margin_type = "ADJACENT_FACES"
    scene.render.bake.use_clear = True

    meshtools.deselect_all()
    bakeable = [o for o in objects
                if any(m and not m.get("flat_color") for m in o.data.materials)]
    for obj in bakeable:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = bakeable[0]
    bpy.ops.object.bake(type="DIFFUSE")

    for mat, node in targets:
        mat.node_tree.nodes.remove(node)
    image.pack()
    return image


def finalize_material(objects, image, name, roughness=0.92):
    """Swap the Cycles-only painterly tree for a plain textured material.

    Only this simple form is exportable and only this form is cheap. Shared
    across every object in the asset, so the whole asset is one draw call.
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.location = (-400, 0)
    tex.interpolation = "Smart"
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    for obj in objects:
        for i, existing in enumerate(obj.data.materials):
            if existing is not None and existing.get("flat_color"):
                continue
            obj.data.materials[i] = mat
    return mat
