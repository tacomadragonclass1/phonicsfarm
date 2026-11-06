"""CVC Land's own assets: the troll, the pedestals, the bell.

    blender --background --python art_src/explore/cvcland.py -- troll

⛔ ABSOLUTE PATHS for --python. A relative one doubles when run from inside
art_src/explore and dies with OSError.

These are the objects CVC Land needs that the storybook set does not already
have. Everything else -- trees, undergrowth, blocks, Chuck, the cottage -- is
adopted from `foundation.py` and `village.py` unchanged.

⛔⛔ THE PEDESTAL AND THE LEVER WERE GODOT PRIMITIVES, and that is worse than
being Kenney. The pedestal was two stacked CylinderMesh at 12 radial segments
with a flat albedo; the lever was three BoxMesh, two cylinders and a torus.
They are also the two things a child actually touches -- the pedestal is where
a letter goes and the lever is what makes the word happen -- so they were the
placeholder objects carrying the most meaning in the game. A 12-segment
cylinder outlines as a visible dodecagon under ink.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import world_plan as P  # noqa: E402
import foundation as F  # noqa: E402
from sb_lib import asset, forms, meshtools, painter, palette  # noqa: E402

D = "cvc"

# ⛔ The game's own face. A statue lettered in anything else would quietly
# teach a different letterform from the blocks a child is holding.
FONT = os.path.join(asset.PROJECT, "assets", "fonts", "Fredoka.ttf")

palette.extend({
    # Granite, for a troll who has been sitting here since sunrise. Warm
    # rather than blue -- a cold grey statue in a meadow reads as municipal.
    "k_stone":      ("#9A9086", 0.52, "troll granite, lit face"),
    "k_stone_deep": ("#6A6158", 0.34, "granite in shadow and in the crevices"),
    "k_stone_pale": ("#B8AEA0", 0.66, "the crown of a boulder, sun-bleached"),
    "k_moss":       ("#6E8450", 0.44, "moss on his shoulders and knees"),
    "k_moss_deep":  ("#485C34", 0.30, "moss in the shade of him"),
    # The pedestal. ⭐ THE CUT FACE IS THE SECOND LIGHTEST THING IN THE GAME,
    # after the letter plaque itself. That is the whole design: a pale sawn
    # disc against dark bark says PUT IT HERE without a label on it.
    "k_cut":        ("#E0CFA6", 0.80, "the sawn face of a stump -- the target"),
    "k_cut_ring":   ("#C3AC7E", 0.66, "growth rings in the cut"),
    "k_bark":       ("#6B4A32", 0.30, "stump bark"),
    "k_bark_deep":  ("#4A3222", 0.20, "the shaded side of bark"),
    # The bell.
    # ⛔ DEEPER THAN IT LOOKS ON PAPER. The first bronze was #B08A42 at value
    # 0.50 and it rendered as pale cream -- the patina lightens, the grade
    # lifts value, and a metal that starts mid ends up looking like canvas.
    # Metal has to be authored DARK to survive a pipeline built for a sunny
    # meadow.
    "k_bronze":     ("#8A6626", 0.38, "the bell"),
    "k_bronze_deep":("#5A4017", 0.22, "inside the bell, and its shadow side"),
    "k_bronze_lip": ("#C09A46", 0.56, "the worn lip where the clapper strikes"),
    "k_rope":       ("#C9B288", 0.70, "the bell rope"),
    # Worked timber -- posts, planks, cart. Warmer and lighter than bark,
    # because somebody cut it, dressed it and put it up.
    "k_timber":     ("#9A6E42", 0.46, "posts and beams"),
    "k_timber_deep":("#6E4C2B", 0.30, "the shaded face of a beam"),
    "k_plank":      ("#B99060", 0.58, "sawn boards -- roof, cart bed"),
    "k_iron":       ("#4A4440", 0.24, "tyres, straps, the clapper"),
})

# ⛔ Worked timber keeps a LOW angle so its chamfers stay crisp -- that
# crispness is the difference between "a post somebody squared up" and "a
# cylinder". Bark and bell go higher because both are round by nature.
# ⛔⛔ THE GROUND WAS DESIGNED BLURRY, and it was not a resolution problem.
# `foundation.TERRAIN_SURFACE` sets grain=0.0 and streak=0.0 and drops wash
# to 0.09 and ao_strength to 0.30 -- every texel-resolution detail the gouache
# recipe provides, switched off on purpose. No amount of extra texture would
# have fixed that, because there was nothing in the material to resolve.
#
# The detail comes back here, at a scale chosen against THIS ground rather
# than inherited: grain is the tooth of the field, streak is the direction a
# mower and a hundred pairs of feet leave in it.
GROUND_SURFACE = dict(F.SURFACE, grain=0.055, grain_scale=96.0,
                      streak=0.075, streak_scale=3.4,
                      wash=0.13, wash_scale=2.4,
                      ao_strength=0.34, ao_distance=0.90,
                      edge_light=0.07, edge_dark=0.09)

SMOOTH = {"ground": 46.0, "troll": 44.0, "pedestal_post": 34.0, "pedestal_cap": 24.0,
          "bell": 40.0, "bell_frame": 12.0, "woodshed": 12.0,
          "handcart": 16.0}


def timber(name, colour, centre, width, depth, height, taper=0.0):
    """A squared-up baulk of wood: a lofted rounded rectangle.

    ⛔ Not a `sweep`, which makes round stock. A post a carpenter made has
    FOUR FACES and a chamfer, and at this camera the chamfer catching the key
    light along one edge is most of what says "worked" rather than "grown".
    """
    low = forms.rounded_rect(width, depth, min(width, depth) * 0.16)
    top = forms.rounded_rect(width * (1.0 - taper), depth * (1.0 - taper),
                             min(width, depth) * 0.16)
    return forms.loft(name, colour,
                      [(centre[2] - height * 0.5, low),
                       (centre[2] + height * 0.5, top)],
                      at=(centre[0], centre[1], 0.0))


def produce(subject, objects, budget_tris=None, texture=512, surface=None):
    return asset.produce("%s/%s" % (D, subject), objects, texture=texture,
                         roughness=0.93, budget_tris=budget_tris,
                         bake_samples=24, smooth_angle=SMOOTH[subject],
                         gouache=surface or F.SURFACE)


# ===================================================================== GROUND
#
# ⭐⭐ THE PATHS TEACH THE GAME. Three worn tracks run from the pedestal row
# out to the three letter zones. A child walking into this clearing can see
# where to go before anybody says a word to them, and the marks are exactly
# what feet would really leave. It is the cheapest piece of teaching in the
# build and it costs nothing but a colour field.
#
# ⛔ 44 m, not 64. The preview world was sized for a village AND a home field
# and carried 16 texels per metre against a 142 px/m camera. CVC Land is one
# clearing; at 44 m the same 1024 sheet carries 23, and the grid step drops
# to 0.28 so the colour field can hold a 0.56 m edge.

def _edge(value, at, width):
    """0 below `at`, 1 above `at + width`, smooth between. One boundary."""
    t = min(max((value - at) / max(width, 1e-6), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def _hash2(i, j, seed):
    h = (i * 374761393 + j * 668265263 + seed * 2654435761) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / float(0xFFFFFF)


def _vnoise(x, y, freq, seed):
    gx, gy = x * freq, y * freq
    i, j = math.floor(gx), math.floor(gy)
    fx, fy = gx - i, gy - j
    sx = fx * fx * (3.0 - 2.0 * fx)
    sy = fy * fy * (3.0 - 2.0 * fy)
    i, j = int(i), int(j)
    a = _hash2(i, j, seed)
    b = _hash2(i + 1, j, seed)
    c = _hash2(i, j + 1, seed)
    d = _hash2(i + 1, j + 1, seed)
    low = a + (b - a) * sx
    high = c + (d - c) * sx
    return low + (high - low) * sy


def _fbm(x, y, seed=0):
    """Rotated-lattice fBm in -0.5..0.5.

    ⛔ NOT a product of sines. `sin(x*a) * sin(y*b)` is separable, which makes
    it a GRID by construction -- the previous ground was three octaves of
    exactly that and read as tartan from above. Rotating each octave means no
    two share an axis.
    ⭐ And the octaves run FINER here than before. On a 44 m clearing the
    coarsest feature wants to be a few metres, not fifteen, or the whole
    field is one slow drift and the eye reads it as blur.
    """
    total, norm, angle = 0.0, 0.0, 0.0
    for index, (freq, amp) in enumerate(((0.16, 1.0), (0.41, 0.52),
                                         (0.97, 0.27), (2.30, 0.13))):
        ca, sa = math.cos(angle), math.sin(angle)
        total += amp * _vnoise(x * ca - y * sa, x * sa + y * ca,
                               freq, seed + index * 17)
        norm += amp
        angle += 0.9
    return total / norm - 0.5


def build_ground():
    """The whole world's ground: clearing, vale, village and mill hill.

    ⛔⛔ THE GRID IS BUILT IN THE PICTURE'S AXES. The world is composed for a
    camera at yaw 30 that never turns, so an axis-aligned box big enough to
    hold it is 76 x 85 m -- a third of it corner that can never be looked at,
    and a texel density wrecked by covering ground that does not exist.
    Generating in (row, away) and transforming each vertex gives the same
    coverage in 40 x 88 and puts every triangle somewhere visible.
    """
    import bmesh
    import bpy
    from mathutils import Vector

    meshtools.reset_scene()
    rows = int(round((P.WORLD_AWAY[1] - P.WORLD_AWAY[0]) / P.GROUND_STEP))
    cols = int(round((P.WORLD_ROW[1] - P.WORLD_ROW[0]) / P.GROUND_STEP))

    bm = bmesh.new()
    grid = []
    for r in range(rows + 1):
        away = P.WORLD_AWAY[0] + r * P.GROUND_STEP
        line = []
        for c in range(cols + 1):
            row = P.WORLD_ROW[0] + c * P.GROUND_STEP
            x, y = P.along(row, away)
            line.append(bm.verts.new(Vector((x, y, P.ground_height(x, y)))))
        grid.append(line)
    for r in range(rows):
        for c in range(cols):
            bm.faces.new([grid[r][c], grid[r][c + 1],
                          grid[r + 1][c + 1], grid[r + 1][c]])
    # ⛔⛔ `recalc_face_normals` POINTS AN OPEN HEIGHTFIELD DOWNWARDS -- it
    # makes normals CONSISTENT, and a grid has no outside, so it picks -Z.
    # That went unnoticed through three rounds of looking at renders once and
    # was only caught by sampling the baked PNG.
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    flipped = [f for f in bm.faces if f.normal.z < 0.0]
    if flipped:
        bmesh.ops.reverse_faces(bm, faces=flipped)

    mesh = bpy.data.meshes.new("GroundMesh")
    bm.to_mesh(mesh)
    bm.free()
    ground = bpy.data.objects.new("Ground", mesh)
    bpy.context.collection.objects.link(ground)
    meshtools.set_part_color(ground, "f_grass")

    def field(position, normal):
        x, y = position.x, position.y
        grass = 0.60 + 0.30 * _fbm(x, y, seed=5)

        # 1. THE BEATEN STAGE. Where a child stands to place three letters,
        #    over and over. Hard-edged, because the wear stops where the
        #    standing stops.
        stage = P.stage_distance(x, y)
        if stage < 2.9:
            grass += (0.21 - grass) * (1.0 - _edge(stage, 1.05, 1.75))

        # 2. THE THREE TRACKS out to the letter zones. Scuffed, not bare --
        #    feet thin a sward long before they strip it.
        track = P.track_distance(x, y)
        if track < 1.35:
            grass += (0.27 - grass) * (1.0 - _edge(track, 0.34, 0.92))

        # 3. The zones' own worn patches, at the far end of each track.
        zone = P.zone_distance(x, y)
        if zone < P.ZONE_RADIUS + 1.1:
            grass += ((0.30 - grass) * 0.82
                      * (1.0 - _edge(zone, P.ZONE_RADIUS - 1.2, 2.2)))

        # 4. THE VILLAGE GREEN. ⭐ A green is the one piece of ground in a
        #    village that everybody keeps, and that is exactly why it reads
        #    as a village rather than as a gap between houses: it is EVENER
        #    than the ground around it, not greener. Compress the range,
        #    barely lift the value, and let the edge do the talking.
        green = P.village_distance(x, y)
        if green < P.VILLAGE_GREEN_R + 1.2:
            kept = 1.0 - _edge(green, P.VILLAGE_GREEN_R - 0.9, 1.9)
            grass = grass + (0.61 - grass) * 0.50 * kept + 0.028 * kept

        # 5. Trodden ground at every doorway. A building with pristine grass
        #    to its threshold has nobody living in it.
        door = P.building_distance(x, y)
        if door < 3.4:
            grass += (0.30 - grass) * 0.7 * (1.0 - _edge(door, 1.6, 1.8))

        # 6. THE CART TRACK up the hill. Earth, because a loaded cart keeps
        #    it open -- with ruts, not one flat chocolate band. A way that is
        #    uniformly dark across its whole width is a trench.
        climb = P.track_climb(x, y)[0]
        if climb < P.CART_W + 0.8:
            if climb < P.CART_W:
                rut = abs(climb / P.CART_W - 0.62)
                return 0.19 - 0.075 * (1.0 - min(rut / 0.26, 1.0))
            grass = min(grass, 0.42)
            return 0.21 + (grass - 0.21) * _edge(climb, P.CART_W, 0.50)

        # 7. The lane. ⛔ Narrow and PALE. A cart is 1.4 m wide and the
        #    ground it runs on is dry buff, not chocolate; the dark end of
        #    the earth ramp belongs in ruts, which are centimetres across.
        lane = P.approach_distance(x, y)
        if lane < 0.68:
            rut = abs(lane / 0.68 - 0.58)
            return 0.20 - 0.085 * (1.0 - min(rut / 0.24, 1.0))
        if lane < 1.02:
            return 0.22 + (grass - 0.22) * _edge(lane, 0.68, 0.34)

        # 8. The verge: a hand's width of rough, darker grass outside every
        #    way. Nobody walks it and nobody cuts it, and it is what stops a
        #    path from looking painted on.
        verge = min(lane, track + 0.35)
        if verge < 1.95:
            grass -= 0.075 * (1.0 - _edge(verge, 1.02, 0.80))

        # 9. Slope, which exists only on the hill and the rim.
        grass += 0.22 * (1.0 - min(max(normal.z, 0.0), 1.0))
        return min(max(grass, 0.0), 1.0)

    F.paint_field(ground, [
        (0.00, "e_earth_deep"),
        (0.12, "e_earth"),
        (0.26, "f_grass_deep"),
        (0.58, "f_grass"),
        (0.78, "f_grass_dry"),
        (0.95, "f_grass_sun"),
    ], field)
    return [ground]


SUBJECTS = {
    # ⛔ 2048 for the ground ALONE. It is 40 x 88 m where everything else is
    # metres across, so at 1024 it would carry 12 texels per metre against a
    # 142 px/m camera -- worse than the blur this pass was fixing. 16 MB of
    # texture, and the only asset in the game that earns it.
    "ground": lambda: produce("ground", build_ground(), budget_tris=90000,
                              texture=2048,
                              # ⭐ A/B SWITCH, kept deliberately. `OLD_SURFACE=1` rebuilds the
                              # ground on the old smoothed recipe so the two
                              # bakes can be compared directly. Measured that
                              # way: high-pass sigma on the BAKED texture goes
                              # 4.550 -> 5.122, and the PNG grows 23%.
                              # ⛔ Compare the GLBs, not the sidecar
                              # `*_albedo.png` -- those are written by GODOT's
                              # import, so two Blender builds in a row leave
                              # the same stale file and the A/B reads as
                              # "no change".
                              surface=(F.TERRAIN_SURFACE
                                       if os.environ.get("OLD_SURFACE")
                                       else GROUND_SURFACE)),
    "troll": lambda: produce("troll", build_troll(), budget_tris=13000),
    "pedestal_post": lambda: produce("pedestal_post", build_pedestal_post(),
                                     budget_tris=1800),
    "pedestal_cap": lambda: produce("pedestal_cap", build_pedestal_cap(),
                                    budget_tris=1200),
    "bell_frame": lambda: produce("bell_frame", build_bell_frame(),
                                  budget_tris=2600),
    "bell": lambda: produce("bell", build_bell(), budget_tris=2600),
    "woodshed": lambda: produce("woodshed", build_woodshed(),
                                budget_tris=4200),
    "handcart": lambda: produce("handcart", build_handcart(),
                                budget_tris=5200),
}


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    wanted = [a for a in args if a in SUBJECTS] or list(SUBJECTS)
    for name in wanted:
        print("[cvcland] building", name)
        SUBJECTS[name]()
