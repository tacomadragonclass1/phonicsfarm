"""The chosen set: D2 tree, D3 cottage, D1 block, D3 Chuck -- one world.

    blender --background --python art_src/explore/hybrid.py

The subjects were picked across all three studies, which is fine for FORM and
fatal for SURFACE. A flat-shaded faceted cottage, a painterly layered tree and
a soft clay block, each carrying its own study's palette and its own bake
recipe, would read as three games sharing a field.

So the forms are kept exactly as chosen and everything else is unified:

  * ONE palette. The study palettes are re-pointed onto a single family here,
    so the builders need no edits -- `palette.extend` overwrites the entries
    they already ask for by name.
  * ONE bake recipe, sitting between D3's clean flat fields and D2's painterly
    wash: a real wash, little grain, and an `edge_dark` of 0.20 that keeps
    some of D2's drawn line without D2's 0.38 ink.
  * Shading angle still varies, because that is a property of what a thing IS
    rather than of the art direction: a cottage is CUT (10 degrees, faceted),
    a toy block is MOULDED (18), foliage is somewhere between (30).

The block is the one form that is re-authored rather than imported, because
"the largest lettering possible" turned out to be a measurable requirement
rather than a stylistic one. See LETTER_* below.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common  # noqa: E402  -- registers the study palettes first
from common import BLOCK_FACES, BLOCK_SIZE, plaque_centre  # noqa: E402
from sb_lib import asset, forms, meshtools, painter, palette  # noqa: E402

import d2_storybook  # noqa: E402
import d3_sculptural  # noqa: E402

D = "hybrid"

# --------------------------------------------------------------- lettering
#
# Measured from Fredoka rather than guessed. Across a-z the glyph ink spans
# 0.894 em and is NOT centred on the text origin: it runs from +0.320 em at
# the top of 'f' to -0.575 em at the bottom of 'y', because Label3D centres
# the LINE BOX (ascent + descent) and not the ink.
#
# At the shipping font_size 76 that put the ink 0.544 units tall on a 0.575
# plaque -- 95% of it -- and dropped every descender 0.062 units BELOW the
# plaque, onto the wooden frame. The letters were both too big for their
# ground and sitting off-centre on it.
#
# Fixing the offset is what buys the size. Re-centred on the ink and on a
# wider plaque, the x-height goes from 0.287 to 0.325 units, 13% larger, with
# the tallest and lowest glyphs still clearing the edge.
LETTER_INK_SPAN = 0.894      # em, 'f' top to 'y' bottom
LETTER_INK_CENTRE = -0.1275  # em, where that ink sits relative to the origin
# 0.660 was tried and the wooden frame that survived it was 0.07 wide, which
# at gameplay size read as a sugar cube rather than as a wooden block. 0.640
# keeps a frame that still says "toy" and still buys 9% more x-height than the
# shipping block. Going back to 0.660 / font 86 is a two-line change if the
# lettering matters more than the frame.
LETTER_PLAQUE = 0.640
LETTER_MARGIN = 0.022
LETTER_FONT_SIZE = 83
LETTER_PIXEL_SIZE = 0.008


def letter_offset():
    """How far to lift each Label3D so its INK centres on the plaque."""
    return -LETTER_INK_CENTRE * LETTER_FONT_SIZE * LETTER_PIXEL_SIZE


# ----------------------------------------------------------------- palette
#
# One family. The study names are overwritten in place, so d2_storybook and
# d3_sculptural keep asking for "g_leaf" and "s_roof" and quietly get the
# house colours instead.

HOUSE = {
    # structure
    "s_wall":       ("#EBDCC2", 0.84, "plaster"),
    "s_wall_shade": ("#C9B597", 0.69, "plaster plane in shade"),
    "s_roof":       ("#C4564A", 0.40, "roof"),
    "s_roof_deep":  ("#98393A", 0.27, "roof under-plane"),
    "s_stone":      ("#A79C8D", 0.60, "stone"),
    "s_blue":       ("#4A7FA6", 0.45, "painted door"),
    "s_accent":     ("#E8B24A", 0.68, "painted trim, boots"),
    "s_wood":       ("#8E6244", 0.41, "timber"),
    "s_wood_deep":  ("#5C3F2B", 0.26, "timber shadow, window reveal"),
    # planting -- the tree keeps D2's forms and loses D2's greens
    "g_leaf_light": ("#7FA056", 0.53, "canopy lit"),
    "g_leaf":       ("#557A42", 0.39, "canopy body"),
    "g_leaf_deep":  ("#33502F", 0.24, "canopy shadow"),
    "g_timber":     ("#8E6244", 0.41, "trunk"),
    "g_ink":        ("#2A211C", 0.12, "the darkest accent"),
    # the toy
    # Deliberately DARK for a toy: the frame is only 0.08 wide, so it has to
    # win on value contrast against the cream face rather than on width.
    "c_wood":       ("#A3703F", 0.45, "block body"),
    "c_wood_deep":  ("#6E4628", 0.29, "block chamfer"),
    "c_cream":      ("#F6ECD6", 0.90, "block letter face"),
    # character
    "s_skin":       ("#BE7E4F", 0.50, "skin"),
    "s_hair":       ("#2E2420", 0.14, "hair"),
    "s_cream":      ("#F6ECD6", 0.90, "collar, jumper band"),
    "s_leaf":       ("#557A42", 0.39, "jumper"),
    "s_ink":        ("#2A211C", 0.12, "lettering, eyes"),
    "hb_ground":    ("#8C9C66", 0.57, "study ground"),
}
palette.extend(HOUSE)


SURFACE = dict(wash=0.16, wash_scale=3.2, grain=0.045, grain_scale=48.0,
               streak=0.09, streak_scale=3.0,
               ao_strength=0.68, ao_distance=0.28,
               edge_light=0.16, edge_dark=0.20)

# A cottage is cut, a block is moulded, foliage is in between.
SMOOTH = {"cottage": 10.0, "block": 18.0, "tree": 30.0, "chuck": 16.0}


def produce(subject, objects, texture=asset.TEXTURE_MEDIUM, budget_tris=None):
    return asset.produce("explore/hybrid_%s" % subject, objects,
                         texture=texture, roughness=0.93,
                         budget_tris=budget_tris, bake_samples=24,
                         smooth_angle=SMOOTH[subject], gouache=SURFACE)


# ------------------------------------------------------------------ block

def build_block():
    """D1's superellipsoid, re-proportioned around the lettering.

    Two changes from the study version, both of them in service of the
    letters: the body exponent goes 4.6 -> 5.2 so the faces are flat enough to
    carry a wider plaque without its corners lifting off, and the plaque goes
    0.575 -> 0.660. The wooden frame that remains is 0.07 at its widest, which
    is still enough to read as an inlay rather than a sticker.
    """
    meshtools.reset_scene()
    half = BLOCK_SIZE / 2

    body = forms.superform("Cube", "c_wood", size=(BLOCK_SIZE,) * 3,
                           exponent=5.2, segments=26, rings=18,
                           at=(0, 0, half))
    forms.dents(body, [(half, half, half * 1.9), (-half, half, half * 0.3),
                       (half, -half, half * 0.4)], depth=0.018, radius=0.28)
    forms.jitter_verts(body, 0.0030, seed=31)
    meshtools.paint_by_normal(body, "c_wood", "c_wood", "c_wood_deep",
                              up_at=0.9, down_at=-0.7)

    plaques = []
    thickness = 0.048
    for name, normal in BLOCK_FACES:
        centre = plaque_centre(normal, thickness)
        if normal[2] > 0.5:
            size = (LETTER_PLAQUE, LETTER_PLAQUE, thickness)
        elif abs(normal[0]) > 0.5:
            size = (thickness, LETTER_PLAQUE, LETTER_PLAQUE)
        else:
            size = (LETTER_PLAQUE, thickness, LETTER_PLAQUE)
        plaques.append(forms.superform(name, "c_cream", size=size,
                                       exponent=6.0, segments=16, rings=12,
                                       at=centre))

    cream = painter.flat_material("hybrid_block_face", "c_cream",
                                  roughness=0.96)
    painter.assign(plaques, cream)
    return [body] + plaques


# -------------------------------------------------------------------- run

if __name__ == "__main__":
    produce("tree", d2_storybook.build_tree(), budget_tris=3400)
    produce("cottage", d3_sculptural.build_cottage(), budget_tris=4000)
    produce("chuck", d3_sculptural.build_chuck(), budget_tris=5000)
    produce("block", build_block(), texture=512, budget_tris=3000)
