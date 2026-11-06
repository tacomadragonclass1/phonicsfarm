"""The world's plan: where everything stands, and the shape of the ground.

⭐ ONE PLAN FOR THE WHOLE WORLD -- the clearing AND the village. They are not
two places that happen to adjoin; CVC Land's north lane runs up into the
village street, and a child walks it. Two plans would mean two opinions about
where the ground is, which is the exact failure this project already paid
for once.

⛔⛔ THIS MODULE MUST NOT IMPORT bpy. That is the whole point of it. The
terrain is sculpted in Blender and the scene is laid out by a plain `python3`
script, and the last time those two held separate opinions about where the
ground was, the result was a village standing on a plane the terrain never
touched. One module, two consumers, no second opinion.

⭐⭐ THE PEDESTALS ARE THE WORD, and the clearing is a diagram of it. Each
of the three letter zones sits DIRECTLY BEHIND its own pedestal, so fetching
a sound is an out-and-back in the direction of the slot it fills. Onset on
the left, vowel in the middle, ending on the right -- the same order a child
reads them in. Nobody has to explain that; the geometry says it.
"""

import math

# ⛔ SCREEN AXES, NOT WORLD AXES. The camera is orthographic at yaw 30 and
# never turns, so world X is NOT screen-horizontal -- this is why the old
# board sits 15 degrees off axis and why CLAUDE.md warns about it. A row of
# pedestals laid along world X comes out as a diagonal.
#
# Camera sits toward Godot (+x, +z); in this module's (x, y) those are
# (+x, -y). ROW runs across the screen, AWAY runs into it.
ROW = (0.8660, 0.5000)
AWAY = (-0.5000, 0.8660)


def along(row_m, away_m, origin=(0.0, 0.0)):
    """Screen-relative placement: metres across, metres into the picture."""
    return (origin[0] + ROW[0] * row_m + AWAY[0] * away_m,
            origin[1] + ROW[1] * row_m + AWAY[1] * away_m)


# --- the stage -------------------------------------------------------------
PEDESTAL_SPACING = 1.70
PEDESTALS = [along(-PEDESTAL_SPACING, 0.0),
             along(0.0, 0.0),
             along(PEDESTAL_SPACING, 0.0)]
# The bell stands off the end of the row, where a child finishing a word
# turns to ring it. ⛔ Not between the pedestals: it would be reached by
# accident while carrying.
BELL = along(4.10, -0.60)
# Where Chuck starts: in front of the row, facing it.
START = along(0.30, -3.40)

# --- the three zones -------------------------------------------------------
# ⛔ The zones spread MUCH wider than the pedestals do. Fanning them at the
# pedestals' own 1.7 m spacing put all three within 3 m of each other, which
# is one zone with three labels.
ZONE_SPREAD = 7.40
ZONE_DEPTH = 7.60
ZONES = {
    "onset": along(-ZONE_SPREAD, ZONE_DEPTH),
    "vowel": along(0.0, ZONE_DEPTH + 0.9),
    "ending": along(ZONE_SPREAD, ZONE_DEPTH),
}
ZONE_RADIUS = 2.9

# ⭐ RESERVED, and deliberately empty. A later round is meant to open a fourth
# place holding the rare letters and the digraphs, for words the three zones
# cannot build. It is sited NOW -- rather than found later -- for one
# practical reason: the ground is a baked mesh, so anything the layout wants
# to leave room for has to be known before the sculpt. Scenery is kept off
# this spot, and no track runs to it, because nobody has walked there yet.
#
# ⛔ It sits BEYOND the vowel zone, up the north lane. A fourth zone fanned
# beside the other three would break the one thing the layout is for: three
# zones behind three pedestals, in the order a word is read.
BONUS = along(2.6, 19.5)
BONUS_RADIUS = 4.2

# --- the village -----------------------------------------------------------
#
# ⭐ UP THE LANE, not beside the clearing. The north lane already left the
# vowel zone heading nowhere; this is where it was always going. One
# continuous walk means the journey is the thing that separates free play
# from the village round, instead of a loading screen.
VILLAGE_GREEN = along(-1.0, 28.0)
VILLAGE_GREEN_R = 6.8

# ⛔ THE STREET IS AN ARC ON THE FAR SIDE OF THE GREEN. The camera never
# turns, so buildings on the NEAR side would stand between the viewer and
# every letter on the green. Same rule that put CVC Land's zones behind its
# pedestals, applied to a village.
VILLAGE = [
    ("bakery",      along(7.40, 31.42), 2.60),
    ("bookshop",    along(4.43, 35.66), 2.60),
    ("clock_house", along(-0.26, 37.85), 2.30),
    ("flower_shop", along(-5.42, 37.40), 2.50),
    ("workshop",    along(-9.66, 34.43), 2.90),
]

# --- the mill hill ---------------------------------------------------------
#
# ⭐⭐ A WINDMILL NEEDS WIND, so the ground rises where the mill stands. That
# reasoning was right the first time and was built wrong: as a 12 m grass
# cone set down on flat ground, with an earth apron round its foot that read
# as a mud halo. A hill you set down is not a hill. This one is IN THE LAND,
# and the cart track is cut into it rather than laid on it.
# ⛔ FAR ENOUGH BACK THAT NO BUILDING STANDS ON IT. At away 46 the flower
# shop sat 8.6 m from the centre on a 10 m base and came out 1.96 m in the
# air -- a shop halfway up a hillside, which nobody would build and nothing
# in the layout asked for. Measure building-to-hill distance whenever either
# moves.
MILL = along(-6.0, 52.0)
MILL_BASE_R = 10.0
MILL_H = 3.40
MILL_CROWN_R = 3.60
# The long gentle tail points back down toward the village, so the climb is
# the face the fixed camera can see.
MILL_AXIS = -62.0

# --- the ground ------------------------------------------------------------
#
# ⛔⛔ THE GRID IS BUILT IN THE PICTURE'S AXES, not in world X/Y. The world is
# composed for a camera at yaw 30 that never turns, so its extent runs along
# ROW and AWAY -- and an axis-aligned box big enough to contain that is 76 x
# 85 m, a third of which is corner nobody will ever see. Generating in
# (row, away) and transforming each vertex gives the same coverage in 40 x 82
# and puts every triangle somewhere it can be looked at.
WORLD_ROW = (-24.0, 16.0)
WORLD_AWAY = (-20.0, 68.0)
GROUND_STEP = 0.30

RIM_BAND = 9.0
RIM_H = 5.20


def world_centre():
    return along((WORLD_ROW[0] + WORLD_ROW[1]) / 2.0,
                 (WORLD_AWAY[0] + WORLD_AWAY[1]) / 2.0)


WORLD_CENTRE = world_centre()


def to_plan(x, y):
    """World (x, y) -> (row, away). ROW and AWAY are orthonormal, so this is
    just a projection onto each."""
    return (x * ROW[0] + y * ROW[1], x * AWAY[0] + y * AWAY[1])


def _soft_min(values, k=2.6):
    """A min with rounded corners, so a square world gets a round rim."""
    return -k * math.log(sum(math.exp(-v / k) for v in values))


def _edge_in(x, y):
    row, away = to_plan(x, y)
    return _soft_min([row - WORLD_ROW[0], WORLD_ROW[1] - row,
                      away - WORLD_AWAY[0], WORLD_AWAY[1] - away])


def rim(x, y):
    """Wooded shoulders. ⛔ Not scenery -- the reason the world has no edge.

    Everything inside the band is DEAD FLAT. A clearing that rolls fights
    every block put down on it, and three of those have to stand on pedestals.
    """
    k = min(max((RIM_BAND - _edge_in(x, y)) / RIM_BAND, 0.0), 1.0)
    lift = k * k * (3.0 - 2.0 * k)
    # Higher behind than in front, so the world has a back wall and an open
    # foreground instead of sitting in a bowl.
    away = to_plan(x, y)[1]
    depth = (away - WORLD_AWAY[0]) / (WORLD_AWAY[1] - WORLD_AWAY[0])
    return RIM_H * lift * (0.74 + 0.52 * depth)


def mill_hill(x, y):
    """The one hill. Flat on top for the mill yard, long tail toward the
    village so the climb faces the camera.

    ⛔ Asymmetric on purpose: a symmetric cone at this scale reads as a
    pimple. Real high ground has a long side and a short one, and the long
    side is where a cart can get up.
    """
    angle = math.radians(MILL_AXIS)
    dx, dy = x - MILL[0], y - MILL[1]
    down = dx * math.cos(angle) + dy * math.sin(angle)
    across = -dx * math.sin(angle) + dy * math.cos(angle)
    reach = MILL_BASE_R * (1.34 if down > 0.0 else 0.76)
    radius = math.hypot(down / reach, across / (MILL_BASE_R * 0.88))
    if radius >= 1.0:
        return 0.0
    crown = MILL_CROWN_R / MILL_BASE_R
    if radius <= crown:
        return MILL_H
    k = (radius - crown) / (1.0 - crown)
    return MILL_H * (1.0 - k * k * (3.0 - 2.0 * k))


def landform(x, y):
    """The shape of the LAND, before anything is cut into it.

    ⛔ The cart track and the building pads are deliberately NOT here. They
    are man-made cuts, and anything that averages the landform to decide a
    colour must not read a graded track as a natural hollow.
    """
    return rim(x, y) + mill_hill(x, y)


def ground_height(x, y):
    height = landform(x, y)

    # The cart track, graded into the bank. A track is a CUT: it takes its
    # own height and the ground either side meets it, which is what makes a
    # revetment necessary and a root cellar possible.
    distance, climb = track_climb(x, y)
    if distance < CART_W + 2.4:
        t = min(max((distance - CART_W * 0.62) / 2.2, 0.0), 1.0)
        blend = 1.0 - t * t * (3.0 - 2.0 * t)
        height += (climb - height) * blend

    # ⛔ LEVEL PADS UNDER EVERY BUILDING. One standing on a slope at this
    # scale reads as a mistake rather than as terrain, and `pedestal.gd`'s
    # trick of stretching a fixed base straight down needs level footing.
    for _, site, radius in VILLAGE:
        gap = math.hypot(x - site[0], y - site[1])
        if gap < radius + 1.3:
            pad = landform(site[0], site[1])
            t = min(max((gap - radius) / 1.3, 0.0), 1.0)
            height += (pad - height) * (1.0 - t * t * (3.0 - 2.0 * t))
    return height


# --- the paths -------------------------------------------------------------
#
# ⭐⭐ THE PATHS TEACH THE GAME. Three tracks run from the pedestal row out
# to the three zones, worn by a thousand trips. A child arriving in this
# clearing can see where to go before anybody says a word to them, and the
# marks are exactly what feet would actually leave. It is the cheapest piece
# of teaching in the whole build and it costs nothing but a colour field.

def _densify(points, samples=10):
    out = []
    for index in range(len(points) - 1):
        ax, ay = points[index]
        bx, by = points[index + 1]
        for step in range(samples):
            k = step / float(samples)
            out.append((ax + (bx - ax) * k, ay + (by - ay) * k))
    out.append(points[-1])
    return out


def _track(pedestal, zone):
    """A worn line from a pedestal to its zone, bowed slightly.

    ⛔ Bowed, not straight. Feet do not walk a ruled line, and three straight
    spokes out of one point read as a diagram of a clearing rather than as a
    clearing.
    """
    mx, my = (pedestal[0] + zone[0]) / 2.0, (pedestal[1] + zone[1]) / 2.0
    dx, dy = zone[0] - pedestal[0], zone[1] - pedestal[1]
    length = math.hypot(dx, dy) or 1.0
    bow = 0.10 * length
    return _densify([pedestal,
                     (mx - dy / length * bow, my + dx / length * bow),
                     zone], 14)


TRACKS = [_track(PEDESTALS[0], ZONES["onset"]),
          _track(PEDESTALS[1], ZONES["vowel"]),
          _track(PEDESTALS[2], ZONES["ending"])]
# --- the cart track --------------------------------------------------------
#
# ⭐ The miller's cart has to get up, and a cart cannot take a bank, so the
# way up WRAPS the hill instead of climbing it. That is what makes the climb
# tight rather than a long diagonal, and it turns the village below you as
# you go round.
#
# ⛔ The wrap runs CLOCKWISE from the tail, so the climb is on the faces the
# fixed camera can see. A track up the back of a hill is a feature nobody
# ever looks at.
CART_FROM = -50.0
CART_TO = -210.0
CART_W = 0.72


def _cart_track(samples=120):
    out = []
    for step in range(samples + 1):
        k = step / float(samples)
        angle = math.radians(CART_FROM + (CART_TO - CART_FROM) * k)
        radius = (MILL_BASE_R * 0.98
                  + (MILL_CROWN_R * 0.55 - MILL_BASE_R * 0.98) * k)
        ease = k * k * (3.0 - 2.0 * k)
        out.append((MILL[0] + math.cos(angle) * radius,
                    MILL[1] + math.sin(angle) * radius,
                    MILL_H * ease))
    return out


CART = _cart_track()


def track_climb(x, y):
    """(distance to the cart track, the track's height there)."""
    best_d2, best_h = 1e9, 0.0
    for tx, ty, th in CART:
        d2 = (tx - x) ** 2 + (ty - y) ** 2
        if d2 < best_d2:
            best_d2, best_h = d2, th
    return math.sqrt(best_d2), best_h


# The way in, from the south, and on north THROUGH the village to the mill.
#
# ⭐ ONE CONTINUOUS WAY. It leaves the clearing past the vowel tree, runs the
# length of the vale, skirts the green the way a lane does -- a green belongs
# to everybody and the lane is going somewhere -- fronts the houses, and ends
# at the foot of the cart track. A child can follow it without being told.
APPROACH = _densify([along(1.6, -14.0), along(0.9, -9.0), along(0.4, -5.2),
                     along(0.0, -2.4)], 14)
LANE_NORTH = _densify([ZONES["vowel"], along(1.2, 13.0), along(3.2, 18.5),
                       along(4.6, 23.0), along(5.4, 27.5),
                       along(3.6, 32.0), along(0.2, 34.6),
                       along(-4.4, 35.2), along(-8.8, 34.4),
                       # ⛔ The lane ENDS ON the cart track's first sample
                       # rather than near it. Typed by hand it stopped 6.3 m
                       # short, which reads as a way that gives up just
                       # before the thing it was going to.
                       (CART[0][0], CART[0][1])], 14)

def _nearest(x, y, dense):
    best = 1e9
    for px, py in dense:
        best = min(best, (px - x) ** 2 + (py - y) ** 2)
    return math.sqrt(best)


def track_distance(x, y):
    return min(_nearest(x, y, dense) for dense in TRACKS)


def approach_distance(x, y):
    return min(_nearest(x, y, APPROACH), _nearest(x, y, LANE_NORTH))


def village_distance(x, y):
    """Distance from the village green's centre."""
    return math.hypot(x - VILLAGE_GREEN[0], y - VILLAGE_GREEN[1])


def building_distance(x, y):
    return min(math.hypot(x - site[0], y - site[1])
               for _, site, _ in VILLAGE)


def stage_distance(x, y):
    """Distance from the beaten ground the pedestals stand on."""
    return min(math.hypot(x - px, y - py) for px, py in PEDESTALS)


def zone_distance(x, y):
    return min(math.hypot(x - zx, y - zy) for zx, zy in ZONES.values())
