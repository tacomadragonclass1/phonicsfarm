"""The Painted Storybook colour library.

One place for every colour in the art direction. Build scripts never write a
literal colour: they ask for a palette name, so a change here repaints the
whole game at once.

Colours are authored as sRGB hex because that is how they are picked and
compared; `linear()` converts to the scene-linear floats Blender shades with.
Anything that skips that conversion comes out visibly washed out.

The grouping below IS the art direction, so keep it:

  ink / soot      the darkest values. Lettering and ironwork only -- never a
                  large surface, or the warmth drains out of the scene.
  cream / paper   the lightest values. Reserved for surfaces that carry
                  information (block faces) and small plaster highlights, so
                  the letters are always the brightest thing in frame.
  plaster..stone  the mid-value body of the world. Everything large lives here
                  so that the darks and lights stay rare enough to mean
                  something.
  accents         terracotta, honey, rose, butter, teal. Used small and
                  deliberately: a roof, a door, a jumper, three flowers.

Value, not hue, is what makes a scene read at kindergarten scale. Every entry
notes roughly where it sits so a new asset can be placed by value first.
"""

# name -> (sRGB hex, approximate value 0-1, note)
_PALETTE = {
    # --- darks -------------------------------------------------------------
    "ink":            ("#241C18", 0.10, "letterforms, the darkest accent in the game"),
    "soot":           ("#3A2E28", 0.16, "hinges, chimney cap, glasses rims"),
    "bark_dark":      ("#4A3426", 0.22, "shadow side of trunks and beams"),
    # --- mid-dark ----------------------------------------------------------
    "timber_dark":    ("#5E3A24", 0.28, "exposed frame beams, door"),
    "foliage_dark":   ("#38502A", 0.24, "underside of canopy masses"),
    "slate":          ("#6E7A80", 0.40, "cool stone, lamp housing"),
    "grass_dark":     ("#74875C", 0.44, "ground in shadow, path edges"),
    # --- mids --------------------------------------------------------------
    "timber":         ("#8A5A38", 0.42, "pedestal column, window frames, toy wood"),
    "bark":           ("#7A5536", 0.40, "trunk light side"),
    "foliage":        ("#52713A", 0.36, "canopy body"),
    "foliage_light":  ("#6E8C46", 0.46, "canopy top, catching the sun"),
    "grass":          ("#96AC72", 0.60, "meadow body"),
    "stone":          ("#8C8275", 0.48, "flagstones"),
    "plaster_warm":   ("#D8BE93", 0.70, "shaded plaster, pedestal shaft"),
    # --- lights ------------------------------------------------------------
    "stone_light":    ("#C2BCAC", 0.70, "pedestal cap, path highlight"),
    "plaster":        ("#E3CFA8", 0.78, "cottage walls"),
    "paper":          ("#EADCC0", 0.84, "roof ridge trim, shutters"),
    "cream":          ("#F6EBD4", 0.90, "ALPHABET BLOCK FACES -- see note below"),
    # --- accents -----------------------------------------------------------
    "terracotta":     ("#C25B3C", 0.40, "roof tiles"),
    "terracotta_dark":("#9C4229", 0.28, "roof shadow course, ridge"),
    "honey":          ("#D9A441", 0.62, "block body, lamp glow, toggles"),
    "honey_deep":     ("#B9792C", 0.46, "block edge chamfers"),
    "rose":           ("#C97A74", 0.52, "window-box flowers, cheeks"),
    "butter":         ("#EDC56A", 0.76, "flowers, Chuck's boots"),
    "teal":           ("#3F8C87", 0.42, "Chuck's jumper, cottage door"),
    "teal_light":     ("#6FB3A8", 0.60, "jumper stripe"),
    "sky_blue":       ("#5E8CA8", 0.48, "Chuck's dungarees"),
    # --- character ---------------------------------------------------------
    "skin":           ("#B5764A", 0.48, "Chuck's skin -- he is a brown-skinned child"),
    "skin_shade":     ("#965D38", 0.38, "ears, under the chin"),
    "hair":           ("#2E231D", 0.12, "Chuck's hair"),
    "lens":           ("#CBD9DC", 0.80, "glasses lenses, opaque on purpose"),
    "eye":            ("#2A2320", 0.11, "eyes"),
    "eye_white":      ("#F2EDE4", 0.90, "eye highlight"),
}

# The meadow is deliberately LESS saturated than it first was. Measured in the
# browser, #93AC64 came out at (149, 203, 89) against the shipping game's
# (145, 190, 115) -- the same value, but far more chroma, and a 26 m field of
# it read as acid rather than as a meadow. Half the frame is ground, so its
# saturation sets the saturation of the whole game.
#
# The second most important relationship: FOLIAGE AGAINST GRASS. The first
# version of this palette had canopy at 0.52 and meadow at 0.55, and a tree
# simply vanished into the field behind it. Trees now sit a full 0.20 of value
# below the ground they stand on, which is what gives every scenery object a
# readable edge against the ground it stands on.
#
# The single most important colour relationship in the game: a cream face at
# value 0.90 carrying ink lettering at value 0.10. Keeping NOTHING else in the
# palette above 0.84 is what makes the letter faces the lightest thing on
# screen, so a five-year-old's eye lands on the letter first. This is ordinary
# legibility for young readers, not an accessibility requirement -- an earlier
# version of this comment claimed it was, and that was wrong.
LETTER_FACE = "cream"
LETTER_INK = "ink"


def extend(entries: dict) -> None:
    """Register a direction's own colours.

    The exploration directions are not variations on one palette -- a pressed
    clay world and an ink-and-gouache world do not share colours any more than
    they share geometry -- so each registers its own prefixed set here rather
    than bending the shipping palette.
    """
    _PALETTE.update(entries)


def srgb_hex(name: str) -> str:
    return _PALETTE[name][0]


def value(name: str) -> float:
    return _PALETTE[name][1]


def note(name: str) -> str:
    return _PALETTE[name][2]


def names() -> list:
    return list(_PALETTE)


def _channel_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear(name: str, alpha: float = 1.0) -> tuple:
    """Palette name -> scene-linear RGBA, which is what Blender shades with."""
    hexcode = _PALETTE[name][0].lstrip("#")
    rgb = tuple(int(hexcode[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return tuple(_channel_to_linear(c) for c in rgb) + (alpha,)


def godot_color(name: str) -> str:
    """Palette name -> a Godot `Color(r, g, b, 1)` literal.

    Godot's `albedo_color` is sRGB, not linear, so this deliberately does NOT
    go through `linear()`. Use it when writing .tscn files by hand so engine
    materials and baked textures agree.
    """
    hexcode = _PALETTE[name][0].lstrip("#")
    rgb = tuple(int(hexcode[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return "Color(%.3f, %.3f, %.3f, 1)" % rgb
