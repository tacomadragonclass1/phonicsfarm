"""Shared harness for the three direction studies.

Each direction is a different WORLD, not a different skin. They do not share a
palette, a surfacing recipe, a shading angle or a construction method -- that
is the whole point of the exercise, and sharing any of those would collapse
the comparison back into "three material presets on the same models".

What IS shared: the subjects (cottage, tree, Chuck, alphabet block), the scale
they are built at, the engine contracts they have to satisfy, and the camera
they are judged under.
"""

import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from sb_lib import asset, palette  # noqa: E402

# Subjects are built at the same real scale in all three directions, so the
# comparison is about design rather than about who drew bigger.
CHUCK_HEIGHT = 1.35     # up from 1.18; see the note in the study README
BLOCK_SIZE = 0.80       # engine contract, identical everywhere
FACE_OUT = 0.413        # outer surface of a letter plaque, from block centre
TOP_OUT = 0.813
TREE_HEIGHT = 2.70
COTTAGE_HEIGHT = 3.30


# --------------------------------------------------------------- palettes

palette.extend({
    # --- D1 handcrafted: pressed clay and carved wood, oxide pigments ------
    "c_oat":      ("#E0CDB0", 0.80, "D1 limewashed clay wall"),
    "c_oat_deep": ("#C3A984", 0.66, "D1 wall in shade"),
    "c_straw":    ("#C2A169", 0.63, "D1 thatch"),
    "c_straw_deep": ("#96764A", 0.46, "D1 thatch underside"),
    "c_wood":     ("#8A6244", 0.40, "D1 carved timber"),
    "c_wood_deep": ("#593F2B", 0.26, "D1 timber shadow, bark"),
    "c_leaf":     ("#6E8558", 0.46, "D1 foliage"),
    "c_leaf_light": ("#8CA06C", 0.57, "D1 foliage crown"),
    "c_leaf_deep": ("#46583A", 0.30, "D1 foliage underside"),
    "c_stone":    ("#9E978A", 0.56, "D1 stone"),
    "c_red":      ("#B8604A", 0.42, "D1 painted door"),
    "c_teal":     ("#5E8A84", 0.48, "D1 painted shutters"),
    "c_butter":   ("#E0B45E", 0.68, "D1 boots, lamp"),
    "c_skin":     ("#B5764A", 0.48, "D1 skin"),
    "c_hair":     ("#3A2A22", 0.17, "D1 hair"),
    "c_cream":    ("#F4E9D2", 0.89, "D1 block letter face"),
    "c_ink":      ("#2A211C", 0.12, "D1 lettering, eyes"),
    "c_ground":   ("#9A9E74", 0.60, "D1 study ground"),

    # --- D2 storybook: ink line over gouache on warm paper -----------------
    "g_paper":    ("#F3E7CC", 0.87, "D2 paper, block face"),
    "g_wall":     ("#E8D3A8", 0.79, "D2 washed plaster"),
    "g_wall_shade": ("#C7A87A", 0.63, "D2 plaster in shade"),
    "g_roof":     ("#C0503A", 0.37, "D2 tile wash"),
    "g_roof_deep": ("#8B3123", 0.25, "D2 tile shadow"),
    "g_timber":   ("#6B452C", 0.30, "D2 drawn timber"),
    "g_leaf":     ("#4F7247", 0.38, "D2 foliage wash"),
    "g_leaf_light": ("#7FA055", 0.53, "D2 foliage lit"),
    "g_leaf_deep": ("#2F4A32", 0.23, "D2 foliage shadow"),
    "g_teal":     ("#2F7D78", 0.37, "D2 painted door, jumper"),
    "g_mustard":  ("#DFA73C", 0.63, "D2 accent"),
    "g_rose":     ("#CE7E72", 0.54, "D2 accent"),
    "g_skin":     ("#BE7D4E", 0.50, "D2 skin"),
    "g_hair":     ("#2B2019", 0.12, "D2 hair"),
    "g_ink":      ("#1E1813", 0.08, "D2 the drawn line"),
    "g_ground":   ("#C3B88E", 0.71, "D2 study ground"),

    # --- D3 sculptural: moulded contemporary, bold flat fields -------------
    "s_wall":     ("#EFE2CC", 0.86, "D3 wall"),
    "s_wall_shade": ("#CDB99C", 0.70, "D3 wall plane in shade"),
    "s_roof":     ("#D9564A", 0.43, "D3 roof"),
    "s_roof_deep": ("#A6393A", 0.29, "D3 roof under-plane"),
    "s_wood":     ("#9A6A45", 0.43, "D3 timber"),
    "s_wood_deep": ("#6A452B", 0.28, "D3 timber shadow"),
    "s_leaf":     ("#4E8761", 0.46, "D3 canopy"),
    "s_leaf_light": ("#74AE7C", 0.61, "D3 canopy lit plane"),
    "s_leaf_deep": ("#2F5C47", 0.30, "D3 canopy under-plane"),
    "s_accent":   ("#F2B23C", 0.70, "D3 bold yellow"),
    "s_blue":     ("#3E7CA8", 0.45, "D3 bold blue"),
    "s_stone":    ("#B4ABA0", 0.66, "D3 stone"),
    "s_skin":     ("#C08055", 0.51, "D3 skin"),
    "s_hair":     ("#2E2420", 0.14, "D3 hair"),
    "s_cream":    ("#FBF2DF", 0.93, "D3 block letter face"),
    "s_ink":      ("#241F1C", 0.11, "D3 lettering"),
    "s_ground":   ("#8FA98C", 0.63, "D3 study ground"),
})


# ------------------------------------------------------------- surfacing

DIRECTIONS = {
    # Pressed clay: light scatters, edges are soft, creases hold deep shadow
    # and there is no sheen anywhere. Texture is fine and even, like the tooth
    # of unglazed earthenware.
    "d1": dict(
        label="Handcrafted sculpted miniature",
        roughness=1.0, smooth_angle=54.0,
        gouache=dict(wash=0.14, wash_scale=4.5, grain=0.10, grain_scale=110.0,
                     streak=0.03, streak_scale=8.0,
                     ao_strength=0.86, ao_distance=0.20,
                     edge_light=0.09, edge_dark=0.18)),

    # Gouache on paper: broad uneven washes, visible brush direction, and a
    # dark line wherever a form turns away -- the ink outline of the drawing,
    # produced by pushing edge_dark far further than anything else here.
    "d2": dict(
        label="Dimensional painted storybook",
        roughness=0.96, smooth_angle=33.0,
        gouache=dict(wash=0.30, wash_scale=2.4, grain=0.07, grain_scale=42.0,
                     streak=0.24, streak_scale=2.6,
                     ao_strength=0.52, ao_distance=0.40,
                     edge_light=0.10, edge_dark=0.38)),

    # Moulded and painted: almost no surface noise at all. The form does the
    # work, so the texture stays out of its way and only ambient occlusion and
    # a crisp edge highlight describe the planes.
    "d3": dict(
        label="Expressive sculptural contemporary",
        roughness=0.86, smooth_angle=10.0,
        gouache=dict(wash=0.07, wash_scale=3.0, grain=0.022, grain_scale=60.0,
                     streak=0.0, streak_scale=4.0,
                     ao_strength=0.74, ao_distance=0.30,
                     edge_light=0.22, edge_dark=0.07)),
}


def produce(direction, subject, objects, texture=asset.TEXTURE_MEDIUM,
            budget_tris=None, bake_samples=24, smooth_angle=None):
    """Surface, bake and export one subject of one direction."""
    spec = DIRECTIONS[direction]
    return asset.produce(
        "explore/%s_%s" % (direction, subject), objects,
        texture=texture, roughness=spec["roughness"],
        budget_tris=budget_tris, bake_samples=bake_samples,
        smooth_angle=smooth_angle if smooth_angle is not None
        else spec["smooth_angle"],
        gouache=spec["gouache"])


# The five letter plaques every direction's block must expose, so the chosen
# one drops straight into alphabet_block.gd without touching the script.
BLOCK_FACES = [
    ("Front", (0.0, -1.0, 0.0)),
    ("Right", (1.0, 0.0, 0.0)),
    ("Back", (0.0, 1.0, 0.0)),
    ("Left", (-1.0, 0.0, 0.0)),
    ("Top", (0.0, 0.0, 1.0)),
]


def plaque_centre(normal, thickness):
    """Where a letter plaque sits so its OUTER face lands on the contract."""
    out = TOP_OUT if normal[2] > 0.5 else FACE_OUT
    inset = out - thickness * 0.5
    if normal[2] > 0.5:
        return (0.0, 0.0, inset)
    return (normal[0] * inset, normal[1] * inset, BLOCK_SIZE / 2)
