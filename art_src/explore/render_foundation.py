"""The five review renders for the foundation pass.

    blender --background --python art_src/explore/render_foundation.py
    blender --background --python art_src/explore/render_foundation.py -- scene chuck

Imports the EXPORTED GLBs, so what is judged is exactly what Godot would
receive: baked texture, final material, final triangle count.

Two things are deliberate and worth knowing before reading the images.

EVERY VIEW IS IN SITU. The close-ups are not studio turntables -- they are the
same world, the same terrain and the same light as the wide shot, with the
camera moved in. "The overall scene feels a little disconnected" is not a
question a beauty shot on a grey backdrop can answer.

THE LIGHT CHANGED, and that is a result rather than a presentation choice. The
study rig was a 5-degree sun at energy 3.1 against a flat grey background,
which is a point light in all but name: hard-edged shadows, nothing in the
sky, and no light at all coming back out of the shadows. Here:

  * the sun is 10 degrees wide instead of 5, which is what softens the
    shadow edges -- the single biggest fix, and it costs nothing;
  * the world is a real sky model rather than a grey constant, so the shadows
    fill with blue from above and the lit faces stay warm. That colour
    difference between light and shade is most of what "connected" means;
  * a broad cool fill from behind the camera's left lifts the shadow interiors
    just enough to keep detail in them.

The game's own lighting needs the same three moves in Godot --
`DirectionalLight3D.light_angular_distance`, a `WorldEnvironment` with a sky
and ambient, and one low-energy fill -- and none of them are in the engine
yet. These renders show the ASSETS under correct light; they are not a claim
about the shipping scene.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import common  # noqa: E402,F401
import foundation  # noqa: E402
from foundation import BLOCKS, SCENE, terrain_height  # noqa: E402
from sb_lib import palette  # noqa: E402

PROJECT = os.path.dirname(os.path.dirname(HERE))
GLB_DIR = os.path.join(PROJECT, "assets", "storybook", "explore")
OUT_DIR = os.path.join(PROJECT, "art_src", "review")
FONT = os.path.join(PROJECT, "assets", "fonts", "Fredoka.ttf")

# The letters are runtime Label3D nodes in Godot, so the GLB ships with blank
# cream plaques. A review render of a LETTER block has to put them back or it
# is reviewing a blank toy. `em` here is the engine's own arithmetic:
# font_size 83 at pixel_size 0.008 is a 0.664 m em.
LETTER_EM = foundation.LETTER_FONT_SIZE * foundation.LETTER_PIXEL_SIZE
BLOCK_LETTERS = ["g", "a", "p"]   # 'g' first: it is the glyph that used to
                                  # hang off the plaque onto the frame


def sky_world(strength=0.34):
    """A real sky, not a grey constant.

    The shadows in the study renders were dead because nothing was lighting
    them. A sky model puts cool light into every upward-facing surface, which
    is both physically what happens outdoors and the cheapest way to make a
    set of separately-baked objects look like they are in one place.
    """
    world = bpy.data.worlds.new("Foundation")
    world.use_nodes = True
    tree = world.node_tree
    background = tree.nodes["Background"]
    background.inputs[1].default_value = strength

    sky = tree.nodes.new("ShaderNodeTexSky")
    # Blender 5 renamed the physical sky models: what the docs and every
    # tutorial still call "Nishita" is MULTIPLE_SCATTERING here, and the old
    # string is not an alias -- it raises.
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(34.0)
    sky.sun_rotation = math.radians(-52.0)
    sky.altitude = 220.0
    sky.air_density = 1.25      # a little haze: warms the horizon, softens blue
    sky.ozone_density = 1.0
    # The disc would be a blown-out hot spot in any frame that caught it, and
    # the SUN lamp is what actually lights the scene.
    sky.sun_disc = False
    tree.links.new(sky.outputs[0], background.inputs[0])
    return world


def light(scene):
    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 2.80
    # 10 degrees, not 5. This one number is the "shadows are quite hard" fix.
    sun_data.angle = math.radians(7.0)
    sun_data.color = (1.0, 0.945, 0.855)
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    # 34 degrees of elevation rather than 40, and swung further round: a
    # lower, more lateral sun rakes across the tile courses, the wall joints
    # and the terrain, which is what makes relief visible at all. It also
    # matches the shipping game's late-afternoon key.
    sun.rotation_euler = (math.radians(34.0), 0.0, math.radians(52.0))

    fill_data = bpy.data.lights.new("Fill", type="AREA")
    # ⛔ 88 was far too much. Softening the shadows by flooding them with a
    # big cool source removed the shadows instead, and took the warmth of the
    # whole frame with it. The sun angle is what softens an edge; the fill is
    # only there to keep DETAIL in the shade.
    fill_data.energy = 24.0
    fill_data.size = 14.0
    # Cool, but not as cool as the first pass: at 0.80 blue the block's
    # 0.90-value letter face picked up a grey-blue cast and stopped reading
    # as cream, which is the one colour relationship the palette protects.
    fill_data.color = (0.88, 0.92, 1.0)
    fill = bpy.data.objects.new("Fill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = (-11.0, -13.0, 7.5)
    fill.rotation_euler = (math.radians(52.0), 0.0, math.radians(-40.0))


def studio(res, samples=72):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.film_transparent = False
    # The block's letter face is the lightest thing in the palette by design
    # (0.90, where nothing else is allowed above 0.84). Under the study's
    # energy it clipped to pure white and stopped being cream, which also
    # threw away the shadow line in the new bezel. AgX holds the highlight;
    # the exposure trim is what keeps the cream reading as a COLOUR.
    scene.view_settings.view_transform = "AgX"
    # ⛔ "Base Contrast" is where the first pass over-corrected. AgX desaturates
    # by design, and on top of a cool fill it turned terracotta into salmon,
    # straw into khaki and a warm plaster wall into grey -- the palette's own
    # value relationships survived, its HUES did not. Punchy restores the
    # chroma without giving back the clipped highlight.
    scene.view_settings.look = "AgX - Punchy"
    scene.view_settings.exposure = -0.10
    scene.world = sky_world()
    light(scene)
    return scene


def camera(look, scale, pitch=30.0, yaw=30.0):
    data = bpy.data.cameras.new("Review")
    data.type = "ORTHO"
    data.ortho_scale = scale
    cam = bpy.data.objects.new("Review", data)
    bpy.context.collection.objects.link(cam)
    pitch_r, yaw_r = math.radians(pitch), math.radians(yaw)
    direction = Vector((math.sin(yaw_r) * math.cos(pitch_r),
                        -math.cos(yaw_r) * math.cos(pitch_r),
                        math.sin(pitch_r)))
    cam.location = Vector(look) + direction * 50.0
    cam.rotation_euler = (math.radians(90.0) - pitch_r, 0.0, yaw_r)
    bpy.context.scene.camera = cam


def place(subject, at=(0.0, 0.0, 0.0), spin=0.0):
    path = os.path.join(GLB_DIR, "foundation_%s.glb" % subject)
    if not os.path.exists(path):
        print("[review] MISSING", os.path.basename(path))
        return []
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    imported = [o for o in bpy.data.objects if o not in before]
    for root in [o for o in imported if o.parent is None]:
        root.location = Vector(at)
        root.rotation_euler = (0.0, 0.0, math.radians(spin))
    return imported


_INK_BAND = None


def ink_band():
    """The a-z ink band of Fredoka, measured off the font, relative to the
    baseline and in em.

    This is the same measurement `block.tscn` is built on, taken from the
    other end. Label3D centres the LINE BOX -- ascent plus descent -- and the
    ink inside that box is not centred on it, which is why every descender
    used to hang 0.062 units below the plaque onto the wooden frame.

    ⛔ Do NOT centre each glyph on its OWN ink instead. It looks better in a
    single render and it is a lie: the engine applies ONE fixed offset to
    every letter, so 'a' and 'g' share a baseline. Per-glyph centring would
    float 'a' upward and hide exactly the defect this render exists to check.
    """
    global _INK_BAND
    if _INK_BAND is not None:
        return _INK_BAND
    low, high = 1e9, -1e9
    for code in range(ord("a"), ord("z") + 1):
        curve = bpy.data.curves.new("Probe", type="FONT")
        curve.body = chr(code)
        curve.size = 1.0
        curve.align_x = "CENTER"
        curve.align_y = "BOTTOM_BASELINE"
        if os.path.exists(FONT):
            curve.font = bpy.data.fonts.load(FONT)
        probe = bpy.data.objects.new("Probe", curve)
        bpy.context.collection.objects.link(probe)
        bpy.context.view_layer.objects.active = probe
        bpy.ops.object.select_all(action="DESELECT")
        probe.select_set(True)
        bpy.ops.object.convert(target="MESH")
        # Blender lays a text object out in its own XY plane: the glyph's
        # HEIGHT is local Y, and local Z is zero until it is extruded. Reading
        # the height off Z returns 0 for every letter and silently centres
        # nothing, which put the first render's 'g' half inside the block.
        for vert in probe.data.vertices:
            low = min(low, vert.co.y)
            high = max(high, vert.co.y)
        bpy.data.objects.remove(probe, do_unlink=True)
    _INK_BAND = (low, high)
    print("[review] Fredoka a-z ink band %.3f .. %.3f em (span %.3f)"
          % (low, high, high - low))
    return _INK_BAND


def letter(character, at, rotation_z, flat=False, size=LETTER_EM):
    """One Label3D's worth of type, as geometry, on the engine's own offset."""
    low, high = ink_band()
    curve = bpy.data.curves.new("Letter", type="FONT")
    curve.body = character
    curve.size = size
    curve.align_x = "CENTER"
    curve.align_y = "BOTTOM_BASELINE"
    if os.path.exists(FONT):
        curve.font = bpy.data.fonts.load(FONT)
    curve.extrude = 0.004
    obj = bpy.data.objects.new("Letter_" + character, curve)
    bpy.context.collection.objects.link(obj)

    material = bpy.data.materials.new("Ink_" + character)
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = palette.linear("s_ink")
    bsdf.inputs["Roughness"].default_value = 0.95
    obj.data.materials.append(material)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    # Shift the baseline so the a-z BAND centres on the plaque. Every glyph
    # gets the same shift, which is what the engine does.
    drop = (low + high) / 2.0 * size
    for vert in obj.data.vertices:
        vert.co.y -= drop

    # Rx(90) sends the glyph's local +Y to world +Z and its extrusion to -Y,
    # which is the direction the Front plaque faces before the block is spun.
    # The Top plaque needs no tilt at all: a text object already lies in XY
    # facing +Z with its reading direction up the +Y axis, which is exactly
    # how `block.tscn` lays its Top label out.
    tilt = 0.0 if flat else math.radians(90.0)
    obj.rotation_euler = (tilt, 0.0, math.radians(rotation_z))
    obj.location = Vector(at)
    return obj


def build_world(letters=True):
    """The whole scene, once. Every view renders this same set."""
    place("terrain")
    place("props")
    place("garden")

    (cx, cy), spin = SCENE["cottage"]
    place("cottage", (cx, cy, terrain_height(cx, cy)), spin)
    (tx, ty), spin = SCENE["tree"]
    place("tree", (tx, ty, terrain_height(tx, ty)), spin)
    (hx, hy), spin = SCENE["chuck"]
    place("chuck", (hx, hy, terrain_height(hx, hy)), spin)

    for index, ((bx, by), spin) in enumerate(BLOCKS):
        base = terrain_height(bx, by)
        place("block", (bx, by, base), spin)
        if not letters:
            continue
        letters_on(BLOCK_LETTERS[index % len(BLOCK_LETTERS)],
                   (bx, by, base), spin)


# The engine letters ALL FIVE plaques -- `update_letter()` walks every child
# of $Letters -- so a review render that letters only the front one shows a
# block the game never displays, and the first attempt put the single letter
# on the face pointing away from the camera. Offsets and rotations below are
# read straight out of `storybook/hybrid/block.tscn`, converted from Godot's
# Y-up/+Z-forward to Blender's Z-up/-Y-forward.
SIDE_OUT = 0.417792
TOP_OUT = 0.822
PLAQUE_Z = 0.40

FACES = [
    # local outward direction, extra spin, lying flat?
    ((0.0, -1.0, 0.0), 0.0, False),     # Front
    ((1.0, 0.0, 0.0), 90.0, False),     # Right
    ((0.0, 1.0, 0.0), 180.0, False),    # Back
    ((-1.0, 0.0, 0.0), 270.0, False),   # Left
    ((0.0, 0.0, 1.0), 0.0, True),       # Top
]


def letters_on(character, base, spin):
    angle = math.radians(spin)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    for (nx, ny, nz), turn, flat in FACES:
        if flat:
            at = (base[0], base[1], base[2] + TOP_OUT)
        else:
            ox, oy = nx * SIDE_OUT, ny * SIDE_OUT
            at = (base[0] + ox * cos_a - oy * sin_a,
                  base[1] + ox * sin_a + oy * cos_a,
                  base[2] + PLAQUE_Z)
        letter(character, at, rotation_z=spin + turn, flat=flat)


VIEWS = {
    # name: look-at, ortho width in metres, resolution, pitch, yaw
    # 9.0 m across is the game's own framing: 1280 px over size 9 is the
    # 142 px per metre the whole texture budget is sized against.
    # 15.5 m, not the game's 9. The gameplay framing is honest and it is also
    # useless for this review: at 9 m the cottage roof is cropped and none of
    # the land is in frame, so the one question being asked -- does this read
    # as a world -- cannot be answered from it. The angle, the lens and the
    # lighting are the game's; only the distance is not.
    "scene": dict(look=(0.10, 0.50, 1.15), scale=15.5, res=(1700, 956),
                  pitch=30.0, yaw=30.0, samples=110),
    # Chuck at pitch 24 rather than 30. The gameplay camera is the honest one
    # for the wide shot; for a character whose face is the whole point of the
    # pass, six degrees lower is the difference between reading an expression
    # and reading the top of a hat.
    "chuck": dict(look=(-0.45, -1.85, 0.74), scale=2.10, res=(1050, 1250),
                  pitch=24.0, yaw=30.0, samples=110),
    "cottage": dict(look=(-2.60, 2.90, 1.95), scale=5.60, res=(1400, 1050),
                    pitch=28.0, yaw=30.0, samples=96),
    "block": dict(look=(1.35, -2.45, 0.40), scale=1.35, res=(1100, 1100),
                  pitch=26.0, yaw=36.0, samples=110),
    "tree": dict(look=(3.95, 0.75, 1.55), scale=4.00, res=(1050, 1300),
                 pitch=28.0, yaw=30.0, samples=96),
    # A sixth view. The smallholding is the answer to "get that world
    # environment lush", and none of the other five frames it.
    "garden": dict(look=(0.45, 2.55, 0.78), scale=4.90, res=(1500, 1050),
                   pitch=26.0, yaw=30.0, samples=96),
}


def render(name):
    spec = VIEWS[name]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    studio(spec["res"], samples=spec.get("samples", 72))
    build_world()
    camera(spec["look"], spec["scale"], spec["pitch"], spec["yaw"])
    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.context.scene.render.filepath = os.path.join(
        OUT_DIR, "foundation_%s.png" % name)
    bpy.ops.render.render(write_still=True)
    print("[review] wrote", bpy.context.scene.render.filepath)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    wanted = [a for a in args if a in VIEWS] or list(VIEWS)
    for name in wanted:
        render(name)
