#!/usr/bin/env python3
"""openD3's retained start-up screen, which is also the fallback level
loading screen.

Section 10.15 of docs/dev/ui-visual-design.md: the stock start-up screen is
one picture (guis/assets/splash/launch) with a status line. The picture is
taken apart here and each element rebuilt on its own, back to front, with
the picture's own measures (fitted against the installed picture):

    space        the band's dark teal, with glowing clouds and darker gaps
                 where the picture has them, lighter horizontal strips, and
                 thin light lines that run across everything, the planet too
    stars        a seeded field of warm specks
    planet       Mars as the main menu has it: its model
                 (models/wipes/planet2.lwo) under the menu's light turned to
                 come from the leading side, and the menu's lit-crescent
                 highlight turned to match, turning slowly (the engine gives
                 the document a clock, in seconds on screen), with a red
                 rim on its night limb
    fire         the night side's fires, on the ground: the planet drawn a
                 second time under a skin of Doom 3's own lava fissures and
                 embers, gathered into patches and lowlands over the whole
                 globe (skins/ and materials/startup_opend3.*), turning with
                 it and shown only where it is in shade, the more the deeper
    honeycomb    the fine grid: pointy-topped cells of side 10.4 u, every
                 edge drawn once, so neighbouring cells share their lines
    cells        cells and small clusters of that grid that light and fade at
                 random, drawn on the grid's own lines
    loose hexes  the translucent hexagonal plates that float off the grid in
                 a stream from the planet's lower trailing side up and out of
                 the band, leaning alike, each tilted in depth with its back
                 face, edges and a fading trail, pulsing on its
                 own period; a few large faint ones lie across the planet
    letterbox    the black bars and their cyan rules
    id mark      the one bitmap: the mark's block cropped from the installed
                 picture (a logo is a bitmap exception, section 6)
    status       the start-up status line, BigChars small cells

The engine presents guis/loading/initialization.rui while it starts
(RetainedUI_DrawInitialization): it raises onInit, then onEnter once the
first frame is on screen, sets `message` and `step` and raises stepChanged
as start-up moves on, and sets `clock` each frame. The stock loading screen
for a level with no screen of its own (guis/map/loading.gui) is the same
picture without the status line, so the session presents this document for
it too (idSessionLocal::SelectRetainedLoadingGui): no message, onEnter when
the load begins, and `clock` each frame.

Layout: the letterbox's opening is 68.75 % of the view's height, as in the
picture, on any view; on a view taller than 4:3 it grows with the height to
at most BAND_MAX u, so a portrait screen sees the whole planet. The opening
is centred and the bars fill the rest. Everything in the opening is placed on
the centred canvas, measured from the opening's middle; the honeycomb, the
stars, the clouds and the stream run on to the view's edges at any width up
to 32:9; the rules run edge to edge; the id mark keeps its distance from the
trailing edge and its place across the opening's bottom edge; the status
line sits under the opening.

build_doom3_menus.py writes the document.
"""

from __future__ import annotations

import math
import random

from doom3_menu_kit import (
    FULL, NO_POINTER, U, Document, absolute, colour, font, group, held, keyword, label, length, number, picture,
    rgb, track, transform, vector,
)

PLACEHOLDER = "#str_04339"   # OK: the engine supplies the text
LAUNCH = "guis/assets/splash/launch"
HIGHLIGHT = "guis/assets/mainmenu/marshighlight"

# The stock picture's measures, in canvas u (640 x 480).
BAND_TOP, BAND_BOTTOM = 75.0, 405.0          # the letterbox opening
BAND_H = BAND_BOTTOM - BAND_TOP
BAND_SHARE = BAND_H / 480                     # of the view's height
BAND_MAX = 520.0                              # u: the tallest opening, on a portrait view
REACH_TOP, REACH_BOTTOM = 240 - BAND_MAX / 2, 240 + BAND_MAX / 2
PLANET_X, PLANET_Y, PLANET_R = 234.0, 240.0, 190.0
ID_BLOCK = (507.5, 336.3, 98.8, 115.0)       # the id mark's block in the picture
STATUS_GAP = 5.0                              # u: the status line under the opening

# Tokens, sampled from the picture.
RULE = "#2F92AC"
BASE = "#041A22"
CLOUD = "#127089"
LINE = "#1B8EA0"
LIT = "#4FC4E0"
PLATE = "#2A9CBC"
STATUS = "#00CFF0"

# The honeycomb: pointy-topped cells, fitted to the picture. Cell (0, 0)'s
# centre is at (GRID_X, GRID_Y); odd rows sit half a cell to the trailing side.
SIDE = 10.4
CELL_W = math.sqrt(3) * SIDE
ROW_H = 1.5 * SIDE
GRID_X, GRID_Y = 1.75, 21.25
FIELD_W = 1800.0             # u: wide enough for a 32:9 view, centred on the canvas
FIELD_LEFT, FIELD_RIGHT = 320 - FIELD_W / 2, 320 + FIELD_W / 2
FIELD_TOP, FIELD_BOTTOM = REACH_TOP - 12, REACH_BOTTOM + 12

# The stream of loose hexes: from the planet's lower trailing side up and out.
STREAM = ((372, 392), (430, 330), (500, 262), (565, 190), (625, 118), (690, 50), (760, -20))


# -------------------------------------------------------------------- geometry
#
# Shapes are built in canvas u and placed by piece(), which gives each its own
# small vector node on the centred canvas.

def poly_path(ident: str, polys: list, *, fill=None, stroke_paint=None, width: float = 0.0, closed: bool = True,
              blend: str | None = None, minimum: float = 1, smooth: bool = True) -> dict:
    """One path of many polygons or polylines, in canvas u."""
    commands = []
    for poly in polys:
        for index, (x, y) in enumerate(poly):
            commands.append({"id": f"p{len(commands)}", "op": "line" if index else "move", "points": [[x, y]]})
        if closed:
            commands.append({"id": f"p{len(commands)}", "op": "close"})
    result = {"id": ident, "commands": commands}
    if fill is not None:
        result["fill"] = fill
    if stroke_paint is not None:
        result["stroke"] = {"paint": stroke_paint, "widthDp": round(U * width, 3), "minimumPixels": minimum, "join": "miter", "cap": "butt"}
    if blend:
        result["blend"] = blend
    if not smooth:
        # Triangles rather than per-pixel coverage: for fills whose edges an
        # anti-aliased outline covers.
        result["antialias"] = False
    return result


def flat(value: list) -> dict:
    return {"type": "solid", "color": colour(value)}


def checked(stops: list) -> list:
    """Gradient stops, which the runtime refuses (and with them the whole
    document) unless their positions increase strictly from 0 to 1."""
    places = [a for a, _c in stops]
    if places[0] < 0 or places[-1] > 1 or any(b <= a for a, b in zip(places, places[1:])):
        raise ValueError(f"gradient stops at {places}")
    return [{"at": a, "color": colour(c)} for a, c in stops]


def ramp(start: tuple, end: tuple, stops: list) -> dict:
    return {"type": "linear", "from": list(start), "to": list(end), "stops": checked(stops)}


def glow(centre: tuple, reach: float, stops: list) -> dict:
    return {"type": "radial", "from": list(centre), "to": [centre[0] + reach, centre[1]], "stops": checked(stops)}


def _paint_points(paint: dict):
    if paint and paint.get("type") in ("linear", "radial"):
        yield paint, "from"
        yield paint, "to"


def piece(ident: str, paths: list, pad: float = 2.0, bounds: tuple | None = None, *, doc: Document | None = None,
          symbol: str | None = None, **more) -> dict:
    """A vector just large enough for `paths` (canvas u), on the centred
    canvas: a piece that is animated on its own is its own small node. With
    `symbol`, the paths become the document's symbol of that name, which
    other nodes can draw at other places (placed())."""
    points = [p for item in paths for command in item["commands"] for p in command.get("points", ())]
    if bounds is None:
        x0, y0 = min(x for x, _ in points) - pad, min(y for _, y in points) - pad
        x1, y1 = max(x for x, _ in points) + pad, max(y for _, y in points) + pad
    else:
        x0, y0, x1, y1 = bounds
    local = lambda x, y: [round(U * (x - x0), 1), round(U * (y - y0), 1)]
    for item in paths:
        for command in item["commands"]:
            if "points" in command:
                command["points"] = [local(x, y) for x, y in command["points"]]
        for paint in (item.get("fill"), (item.get("stroke") or {}).get("paint")):
            for owner, key in _paint_points(paint):
                owner[key] = local(*owner[key])
    if symbol:
        doc.symbols[symbol] = paths
        return placed(ident, symbol, (x0, y0, x1, y1), **more)
    return vector(ident, place(x0, y0, x1 - x0, y1 - y0, **more), paths)


def placed(ident: str, symbol: str, bounds: tuple, dx: float = 0.0, **more) -> dict:
    """A vector node drawing the symbol `symbol`, made for `bounds` (canvas u),
    moved `dx` u along."""
    x0, y0, x1, y1 = bounds
    return {"id": ident, "type": "vector", "properties": place(x0 + dx, y0, x1 - x0, y1 - y0, **more), "symbol": symbol}


def place(x: float, y: float, w: float, h: float, **more) -> dict:
    """A box in canvas u on the centred canvas."""
    return {"position": keyword("absolute"), "left": length(50, "%"), "margin-left": length(round(U * (x - 320), 2)),
            "top": length(round(U * y, 2)), "width": length(round(U * w, 2)), "height": length(round(U * h, 2)), **NO_POINTER, **more}


def circle(cx: float, cy: float, r: float, start: float = 0, end: float = 360, steps: int = 96) -> list:
    """Points on a circle, angles in degrees anticlockwise from the trailing
    side as seen on screen (y grows downward)."""
    count = max(2, int(steps * abs(end - start) / 360))
    return [(round(cx + r * math.cos(math.radians(start + (end - start) * i / count)), 2),
             round(cy - r * math.sin(math.radians(start + (end - start) * i / count)), 2)) for i in range(count + 1)]


def cell_centre(column: int, row: int) -> tuple:
    return (GRID_X + CELL_W * (column + (0.5 if row % 2 else 0.0)), GRID_Y + ROW_H * row)


def corners(column: int, row: int) -> list:
    """A cell's corners clockwise from its top: top, upper trailing, lower
    trailing, bottom, lower leading, upper leading."""
    x, y = cell_centre(column, row)
    h = CELL_W / 2
    return [(x, y - SIDE), (x + h, y - SIDE / 2), (x + h, y + SIDE / 2), (x, y + SIDE), (x - h, y + SIDE / 2), (x - h, y - SIDE / 2)]


def neighbours(column: int, row: int) -> list:
    shift = 1 if row % 2 else 0
    return [(column - 1, row), (column + 1, row), (column - 1 + shift, row - 1), (column + shift, row - 1),
            (column - 1 + shift, row + 1), (column + shift, row + 1)]


def edge_key(a: tuple, b: tuple) -> tuple:
    a, b = (round(a[0], 2), round(a[1], 2)), (round(b[0], 2), round(b[1], 2))
    return (a, b) if a <= b else (b, a)


def grid_range() -> tuple:
    columns = range(int((FIELD_LEFT - GRID_X) / CELL_W) - 1, int((FIELD_RIGHT - GRID_X) / CELL_W) + 2)
    rows = range(int((FIELD_TOP - GRID_Y) / ROW_H) - 1, int((FIELD_BOTTOM - GRID_Y) / ROW_H) + 2)
    return columns, rows


def pulse(rng: random.Random, low: float, high: float, period: int, beats: int) -> list:
    """Opacity keys for one loop of `period` ms: rest at a level of its own
    and move to another and back `beats` times, at moments of its own. The
    loop ends where it starts."""
    rest = round(rng.uniform(low, high), 3)
    keys = [(0, number(rest))]
    cursor = 0
    for _beat in range(beats):
        room = period - cursor - 700
        if room < 900:
            break
        start = cursor + rng.randint(200, max(201, room - 600))
        rise, fall = rng.randint(350, 900), rng.randint(500, 1300)
        if start + rise + fall >= period - 100:
            break
        peak = round(rng.uniform(low, high), 3)
        keys += [(start, number(rest)), (start + rise, number(peak)), (start + rise + fall, number(rest))]
        cursor = start + rise + fall
    keys.append((period, number(rest)))
    return keys


def blink(rng: random.Random, period: int, peak: float) -> list:
    """Dark most of the loop, lit once at a moment of its own."""
    start = rng.randint(100, period - 2300)
    rise, hold, fall = rng.randint(250, 600), rng.randint(80, 500), rng.randint(600, 1300)
    end = max(start + rise + hold + 100, min(period - 50, start + rise + hold + fall))
    return [(0, number(0)), (start, number(0)), (start + rise, number(peak)), (start + rise + hold, number(peak)), (end, number(0)),
            (period, number(0))]


# ----------------------------------------------------------------- the layers

def space(rng: random.Random) -> list:
    """The band's dark teal: glowing clouds where the picture is lighter
    (left of the planet, along the stream, top trailing), darker gaps
    between, and lighter horizontal strips."""
    nodes = []
    clouds = [  # (x, y, reach, alpha): light
        (10, 200, 125, 0.75), (70, 125, 85, 0.35), (-60, 300, 110, 0.35), (610, 112, 95, 0.55), (540, 205, 95, 0.40),
        (470, 290, 105, 0.42), (410, 365, 80, 0.30), (680, 150, 110, 0.30), (330, 60, 120, 0.22), (140, 440, 120, 0.25),
        (-230, 170, 160, 0.40), (-420, 300, 170, 0.35), (-560, 140, 130, 0.30), (840, 260, 170, 0.38), (1010, 140, 150, 0.32),
        (1150, 320, 140, 0.30), (520, 460, 120, 0.22), (560, 10, 130, 0.25),
    ]
    for index, (x, y, reach, alpha) in enumerate(clouds):
        x, y = x + rng.uniform(-6, 6), y + rng.uniform(-6, 6)
        box = [(x - reach, y - reach), (x + reach, y - reach), (x + reach, y + reach), (x - reach, y + reach)]
        paint = glow((x, y), reach, [(0, rgb(CLOUD, alpha)), (0.45, rgb(CLOUD, alpha * 0.55)), (1, rgb(CLOUD, 0))])
        nodes.append(piece(f"init-cloud-{index}", [poly_path("cloud", [box], fill=paint)], pad=0))
    gaps = [(40, 330, 85, 0.60), (585, 262, 80, 0.7), (470, 125, 55, 0.5), (640, 330, 75, 0.6), (-150, 90, 110, 0.45), (520, 380, 60, 0.45),
            (930, 300, 120, 0.40), (-330, 360, 120, 0.40)]
    for index, (x, y, reach, alpha) in enumerate(gaps):
        box = [(x - reach, y - reach), (x + reach, y - reach), (x + reach, y + reach), (x - reach, y + reach)]
        paint = glow((x, y), reach, [(0, [0, 0, 0, alpha]), (0.5, [0, 0, 0, alpha * 0.6]), (1, [0, 0, 0, 0])])
        nodes.append(piece(f"init-gap-{index}", [poly_path("gap", [box], fill=paint)], pad=0))

    def strip(ident: str, top: float, bottom: float, alpha: float, tint: str = "#5A7480") -> dict:
        edge = min(5.0, (bottom - top) * 0.4)
        span = bottom - top
        shape = [(FIELD_LEFT, top), (FIELD_RIGHT, top), (FIELD_RIGHT, bottom), (FIELD_LEFT, bottom)]
        paint = ramp((0, top), (0, bottom), [(0, rgb(tint, 0)), (round(edge / span, 3), rgb(tint, alpha)),
                                             (round(1 - edge / span, 3), rgb(tint, alpha)), (1, rgb(tint, 0))])
        return poly_path(ident, [shape], fill=paint)

    def glint(ident: str, y: float, alpha: float) -> dict:
        shape = [(FIELD_LEFT, y), (FIELD_RIGHT, y), (FIELD_RIGHT, y + 0.9), (FIELD_LEFT, y + 0.9)]
        stops, x = [], FIELD_LEFT
        while x < FIELD_RIGHT - 20:
            stops.append((round((x - FIELD_LEFT) / FIELD_W, 4), rgb("#7FD0E4", round(alpha * rng.choice((0, 0.3, 0.7, 1.0)), 3))))
            x += rng.uniform(60, 200)
        stops.append((1, rgb("#7FD0E4", 0)))
        return poly_path(ident, [shape], fill=ramp((FIELD_LEFT, 0), (FIELD_RIGHT, 0), stops), blend="additive")

    nodes.append(piece("init-strips", [strip("s0", 91, 108, 0.16), strip("s1", 245, 252, 0.10), strip("s2", 363, 401, 0.11),
                                       strip("s3", 176, 205, 0.06, CLOUD)],
                       bounds=(FIELD_LEFT, 80, FIELD_RIGHT, 410)))
    # The picture's thin light lines run across everything, the planet too.
    glints = piece("init-glints", [glint("g0", 83, 0.10), glint("g1", 253, 0.16), glint("g2", 270, 0.12), glint("g3", 374, 0.12),
                                   glint("g4", 162, 0.08)], bounds=(FIELD_LEFT, 78, FIELD_RIGHT, 380))
    return nodes, glints


STAR_TILE = FIELD_W / 5


def stars(doc: Document, rng: random.Random) -> list:
    """A field of stars: warm specks under 1.5 u, most of them faint. One
    tile of them, a fifth of the field wide, is a symbol drawn five times
    across it, each copy turned another way so no two look alike. They hold
    still: a twinkle would put the whole tile through a composition layer
    every frame."""
    by_paint: dict = {}
    for _index in range(330):
        x, y = rng.uniform(FIELD_LEFT, FIELD_LEFT + STAR_TILE), rng.uniform(FIELD_TOP, FIELD_BOTTOM)
        size = rng.choice((0.7, 0.8, 0.9, 0.9, 1.1, 1.4))
        tint = rng.choice(("#E8A060", "#F0D4A8", "#E8A060"))
        alpha = rng.choice((0.35, 0.35, 0.6, 0.6, 0.95))
        by_paint.setdefault((tint, alpha), []).append([(x, y), (x + size, y), (x + size, y + size), (x, y + size)])
    bounds = (FIELD_LEFT, FIELD_TOP, FIELD_LEFT + STAR_TILE, FIELD_BOTTOM)
    paths = [poly_path(f"s{n}", shapes, fill=flat(rgb(tint, alpha))) for n, ((tint, alpha), shapes) in enumerate(sorted(by_paint.items()))]
    piece("init-stars", paths, bounds=bounds, doc=doc, symbol="init-stars")
    flips = ((1, 1), (-1, 1), (1, -1), (-1, -1), (-1, 1))
    return [placed(f"init-stars-{tile}", "init-stars", bounds, dx=tile * STAR_TILE, transform=transform(sx=sx, sy=sy))
            for tile, (sx, sy) in enumerate(flips)]


def planet(doc: Document) -> list:
    """Mars as the main menu has it (guis/mainmenu.gui, MarsRender and
    MarsHighlight): its model, models/wipes/planet2.lwo (the bump-mapped
    surface under a drifting dust shell), under one white light placed as
    the menu places it, a quarter-turn round so it comes from the leading
    side as in the start-up picture, and the menu's lit-crescent highlight,
    guis/assets/mainmenu/marshighlight, added over it at the menu's 0.7,
    turned the same quarter. The planet turns a third of a degree a second;
    a thin red rim lies on its night limb, as the picture has it."""
    doc.state["clock"] = {"type": "number", "initial": 0}
    size = 2 * PLANET_R + 20
    # The menu's light, relative to the planet's centre: 48 toward the
    # camera, 151 to the side (the menu has it above) and 10 along.
    model = {"id": "init-planet", "type": "model",
             "properties": place(PLANET_X - size / 2, PLANET_Y - size / 2, size, size),
             "scene": {"parts": [{"model": "models/wipes/planet2.lwo"}],
                       # The model is a sphere of radius 23.7 standing on its origin: lowered by its
                       # radius it turns about its own centre, and from 72.5 away under a 40 degree
                       # view it fills the node but for 10 u all round.
                       "origin": [0, 0, -23.9], "rotation": [0, {"op": "+", "args": [40, {"op": "*", "args": [{"state": "clock"}, 0.33]}]}, 0],
                       "camera": [-72.5, 0, 0], "fov": 40,
                       "lights": [{"origin": list(LIGHT), "colour": [1, 1, 1]}]}}
    # The model's render fills its square box: only its disc shows.
    centre = U * size / 2
    model["mask"] = {"paths": [{"id": "disc", "commands": [
        {"id": f"p{i}", "op": "line" if i else "move", "points": [[round(centre + U * (x - PLANET_X), 2), round(centre + U * (y - PLANET_Y), 2)]]}
        for i, (x, y) in enumerate(circle(PLANET_X, PLANET_Y, PLANET_R + 0.8, steps=160))] + [{"id": "close", "op": "close"}],
        "fill": {"type": "solid", "color": colour([1, 1, 1, 1])}}]}
    # The highlight: in its 256-texel picture the disc is centred at
    # (128, 126.5) with a radius of 123.7, lit along its top. Scaled to the
    # planet and turned a quarter anticlockwise, its lit edge leads, and its
    # disc's centre lies 2.3 u to the leading side of the picture's.
    across = 256 * PLANET_R / 123.7
    shift = 1.5 * across / 256
    highlight = picture("init-planet-highlight", HIGHLIGHT, {
        **place(PLANET_X + shift - across / 2, PLANET_Y - across / 2, across, across), "image-blend": keyword("additive"),
        "image-color": colour([0.85, 0.85, 0.85, 1]), "transform": {"type": "transform", "unit": "dp", "value": [0, 0, 1, 1, -90]}})
    top, bottom = (PLANET_X, PLANET_Y - PLANET_R), (PLANET_X, PLANET_Y + PLANET_R)
    taper = lambda tint, alpha: ramp(top, bottom, [(0, rgb(tint, 0)), (0.18, rgb(tint, alpha)), (0.62, rgb(tint, alpha)),
                                                   (0.92, rgb(tint, alpha * 0.4)), (1, rgb(tint, 0))])
    rim = poly_path("rim", [circle(PLANET_X, PLANET_Y, PLANET_R - 4, -78, 78)], closed=False,
                    stroke_paint=taper("#B84A3C", 0.2), width=7, blend="additive")
    rim_edge = poly_path("rim-edge", [circle(PLANET_X, PLANET_Y, PLANET_R - 1.2, -70, 70)], closed=False,
                         stroke_paint=taper("#E85A3C", 0.26), width=1.4, blend="additive")
    return [model, highlight, piece("init-planet-rim", [rim, rim_edge], pad=2)]


# The planet's light, from its centre, in the menu's place turned a quarter
# round (see planet()), and as seen from the camera: x to the trailing side,
# y up, z toward the camera.
LIGHT = (-48.0, 151.0, 10.0)
_reach = math.sqrt(sum(v * v for v in LIGHT))
LIGHT_SCREEN = (-LIGHT[1] / _reach, LIGHT[2] / _reach, -LIGHT[0] / _reach)
# Where the fires show: from nothing where the ground's lighting N.L is
# FIRE_FROM to full where it is FIRE_FULL, smoothly.
FIRE_FROM, FIRE_FULL = 0.12, -0.42


def lit(sx: float, sy: float) -> float:
    """N.L at a point of the disc, (sx, sy) in planet radii from its centre,
    x to the trailing side and y up (the view is nearly orthographic)."""
    lx, ly, lz = LIGHT_SCREEN
    return lx * sx + ly * sy + lz * math.sqrt(max(0.0, 1 - sx * sx - sy * sy))


def shaded(level: float, rows: int = 72) -> list:
    """The part of the disc where N.L is below `level`, in canvas u: on each
    row it runs from where N.L falls through `level` to the trailing limb
    (N.L falls monotonically toward that limb wherever it is that low)."""
    leading, trailing = [], []
    for k in range(rows + 1):
        sy = 1 - 2 * k / rows
        width = math.sqrt(max(0.0, 1 - sy * sy))
        if width < 1e-3 or lit(width, sy) >= level:
            continue
        low, high = -width, width
        if lit(low, sy) < level:
            cross = low
        else:
            for _step in range(40):
                mid = (low + high) / 2
                low, high = (mid, high) if lit(mid, sy) >= level else (low, mid)
            cross = high
        leading.append((PLANET_X + PLANET_R * cross, PLANET_Y - PLANET_R * sy))
        trailing.append((PLANET_X + PLANET_R * width, PLANET_Y - PLANET_R * sy))
    return leading + trailing[::-1]


def fire(doc: Document) -> list:
    """The night side's fires, on the ground itself. The planet is drawn a
    second time, turning with the first, under the skin
    opend3/startup/planetfire (materials/startup_opend3.mtr): Doom 3's own
    lava fissures and embers, gathered into patches over the whole globe and
    into its dark lowlands, flickering, and added to the planet as light. A
    mask lets that drawing through only where the planet is in shade, and
    the more the deeper the shade, so the fires never burn on the lit side,
    and turn out of the light and into it as the planet turns."""
    size = 2 * PLANET_R + 20
    centre = U * size / 2
    node = {"id": "init-fire", "type": "model",
            "properties": place(PLANET_X - size / 2, PLANET_Y - size / 2, size, size),
            "scene": {"parts": [{"model": "models/wipes/planet2.lwo", "skin": "opend3/startup/planetfire"}],
                      "origin": [0, 0, -23.9], "rotation": [0, {"op": "+", "args": [40, {"op": "*", "args": [{"state": "clock"}, 0.33]}]}, 0],
                      "camera": [-72.5, 0, 0], "fov": 40}}
    # Nested regions of deepening shade, each adding opacity so that the
    # whole reaches smoothstep(FIRE_FROM, FIRE_FULL) of N.L at its edge.
    local = lambda x, y: [round(centre + U * (x - PLANET_X), 1), round(centre + U * (y - PLANET_Y), 1)]
    paths, before = [], 0.0
    steps = 14
    for k in range(1, steps + 1):
        level = FIRE_FROM + (FIRE_FULL - FIRE_FROM) * k / steps
        t = (k / steps) ** 2 * (3 - 2 * k / steps)
        alpha = 1.0 if t >= 0.999 else 1 - (1 - t) / (1 - before)
        before = t
        region = shaded(level)
        if len(region) < 3:
            continue
        paths.append({"id": f"shade{k}", "commands": [{"id": f"p{i}", "op": "line" if i else "move", "points": [local(*pt)]}
                                                       for i, pt in enumerate(region)] + [{"id": "close", "op": "close"}],
                      "fill": {"type": "solid", "color": colour([1, 1, 1, round(alpha, 4)])}})
    node["mask"] = {"paths": paths}
    return [node]


def honeycomb(doc: Document) -> list:
    """The fine grid. Each cell draws its two upper edges and its trailing
    side; its other three belong to its neighbours, so every edge of the
    honeycomb is drawn once and neighbours share it. Lines are blended, not
    added, so over the planet they stay as quiet as the picture's, and drawn without
    anti-aliasing: start-up keeps no raster cache, and the grid's coverage
    would be some 400,000 vertices a frame; the picture's lines are hard
    too. The grid is drawn in strips four columns wide (one vector's
    coverage has a budget), and as every strip is the same, one strip is a
    symbol the others draw."""
    columns, rows = grid_range()
    first = columns[0]
    lines = []
    for column in range(first, first + 4):
        for row in rows:
            top, upper_trail, lower_trail, _bottom, _lower_lead, upper_lead = corners(column, row)
            lines.append([upper_lead, top, upper_trail, lower_trail])
    x0 = cell_centre(first, 0)[0] - CELL_W / 2 - 1.5
    bounds = (x0, GRID_Y + ROW_H * rows[0] - SIDE - 1.5, x0 + 4.5 * CELL_W + 3, GRID_Y + ROW_H * rows[-1] + SIDE + 1.5)
    strip = poly_path("cells", lines, stroke_paint=flat(rgb(LINE, 0.46)), width=0.8, closed=False, smooth=False)
    nodes = [piece("init-honeycomb-0", [strip], bounds=bounds, doc=doc, symbol="init-honeycomb")]
    count = math.ceil(len(columns) / 4)
    nodes += [placed(f"init-honeycomb-{index}", "init-honeycomb", bounds, dx=4 * CELL_W * index) for index in range(1, count)]
    return nodes


def lit_cells(doc: Document, rng: random.Random) -> list:
    """Cells of the fine grid that light and fade, alone or a few together:
    each lights its cells' faces and the edges round them, which are the
    grid's own lines. Each has a period and a moment of its own and is dark
    most of the time."""
    columns, rows = grid_range()
    candidates = [(c, r) for c in columns for r in rows
                  if abs(cell_centre(c, r)[0] - 320) < 760 and REACH_TOP + 12 < cell_centre(c, r)[1] < REACH_BOTTOM - 12]
    nodes = []
    for index, (column, row) in enumerate(rng.sample(candidates, 44)):
        cells = {(column, row)}
        for _grow in range(rng.choice((0, 0, 0, 1, 2, 2, 3, 5))):
            cells.add(rng.choice(neighbours(*rng.choice(sorted(cells)))))
        counts: dict = {}
        for cell in cells:
            ring = corners(*cell)
            for k in range(6):
                key = edge_key(ring[k], ring[(k + 1) % 6])
                counts[key] = counts.get(key, 0) + 1
        outline = [list(key) for key, count in counts.items() if count == 1]
        inner = [list(key) for key, count in counts.items() if count > 1]
        ident = f"init-cell-{index}"
        paths = [poly_path("face", [corners(*cell) for cell in sorted(cells)], fill=flat(rgb(LIT, 0.13)), blend="additive"),
                 poly_path("edge", outline, stroke_paint=flat(rgb(LIT, 0.55)), width=0.9, closed=False, blend="additive")]
        if inner:
            paths.append(poly_path("inner", inner, stroke_paint=flat(rgb(LIT, 0.22)), width=0.8, closed=False, blend="additive"))
        nodes.append(piece(ident, paths, opacity=number(0)))
        period = rng.randint(4200, 11000)
        doc.timeline(f"{ident}.blink", period, [track(ident, "opacity", blink(rng, period, round(rng.uniform(0.45, 1.0), 3)))],
                     iterations=0)
    return nodes


def plate(rng: random.Random, cx: float, cy: float, side: float, depth: tuple, tilt: tuple) -> list:
    """A hexagonal plate in depth: its front face, the back face `depth`
    behind it, and the edges between, projected flat. `tilt` is (yaw,
    pitch, roll) in degrees."""
    yaw, pitch, roll = (math.radians(a) for a in tilt)
    face = []
    for k in range(6):
        angle = math.radians(60 * k) + roll
        x, y, z = side * math.cos(angle), side * math.sin(angle), 0.0
        x, z = x * math.cos(yaw), x * math.sin(yaw)                       # turn about the vertical
        y, z = y * math.cos(pitch) - z * math.sin(pitch), y * math.sin(pitch) + z * math.cos(pitch)
        face.append((round(cx + x, 2), round(cy + y, 2)))
    back = [(round(x + depth[0], 2), round(y + depth[1], 2)) for x, y in face]
    sides = [[face[k], back[k]] for k in range(6)]
    return [face, back, sides]


def loose_hexes(doc: Document, rng: random.Random) -> list:
    """The loose hexes: translucent plates that float off the grid. Most
    stream from the planet's lower trailing side up and out of the band;
    a few float over the leading side and very large faint ones lie over
    the planet. Each is tilted in depth and added in light, so where they
    overlap they glow; each pulses on its own period."""
    nodes = []

    def along(t: float) -> tuple:
        """A point and direction on the stream, t from 0 to 1."""
        span = t * (len(STREAM) - 1)
        i = min(int(span), len(STREAM) - 2)
        f = span - i
        (ax, ay), (bx, by) = STREAM[i], STREAM[i + 1]
        length_ = math.hypot(bx - ax, by - ay)
        return (ax + (bx - ax) * f, ay + (by - ay) * f), ((bx - ax) / length_, (by - ay) / length_)

    placed = []
    for _n in range(56):
        t = rng.random() ** 0.85
        (x, y), (dx, dy) = along(t)
        spread = rng.gauss(0, 34)
        x, y = x - dy * spread, y + dx * spread
        side = rng.uniform(12, 27) * (1.2 if 0.15 < t < 0.6 else 1.0)
        placed.append((x, y, side, (dx, dy), rng.uniform(0.55, 1.0)))
    for x, y, side in ((40, 112, 19), (95, 96, 14), (150, 108, 17), (-20, 160, 22), (8, 236, 15), (-70, 255, 18), (215, 90, 13),
                       (-160, 120, 20), (-300, 210, 17), (-470, 150, 19), (850, 230, 21), (960, 160, 17), (1080, 280, 20), (40, 450, 17),
                       (575, 475, 18), (300, 15, 16), (470, 0, 14), (590, 96, 24), (628, 150, 20), (556, 128, 17), (650, 92, 22)):
        placed.append((x, y, side, (0.74, -0.67), rng.uniform(0.4, 0.75)))
    for x, y, side in ((262, 165, 58), (318, 300, 64), (150, 335, 52), (372, 196, 46), (300, 108, 42), (196, 250, 48)):
        placed.append((x, y, side, (0.74, -0.67), 0.42))

    # A node whose opacity moves is drawn through a composition layer of its
    # own, and start-up keeps no raster cache, so the plates pulse in six
    # groups (four along the stream, two elsewhere) whose members are mixed
    # through one another; the large ones across the planet are still.
    groups: dict = {}
    # Paths are many shapes of one paint: a group's plates are merged by
    # part and by weight (three steps), so a group is a few dozen paths.
    # Fills draw as triangles under their anti-aliased outlines.
    shapes: dict = {}

    def add(group_key, part: str, level: float, polys: list) -> None:
        shapes.setdefault(group_key, {}).setdefault((part, level), []).extend(polys)

    for index, (x, y, side, (dx, dy), weight) in enumerate(placed):
        large = side > 40
        depth = (dx * side * rng.uniform(0.3, 0.6), dy * side * rng.uniform(0.3, 0.6)) if not large else (6.0, -5.0)
        # The stream's plates lean alike, as the picture's do.
        tilt = (rng.gauss(36, 8), rng.gauss(-12, 9), rng.gauss(4, 5)) if not large else (rng.uniform(0, 20), 0, rng.uniform(-6, 6))
        face, back, sides = plate(rng, x, y, side, depth, tilt)
        level = max(0.5, round(weight * 4) / 4)
        group_key = "still" if large else rng.randrange(4) if index < 56 else 4 + rng.randrange(2)
        add(group_key, "back", level, [back])
        add(group_key, "sides", level, sides)
        add(group_key, "face-large" if large else "face", level, [face])
        if not large:
            # A trail: the plate's outline once or twice more, fainter, back down the stream.
            for copy in range(rng.choice((0, 1, 1, 2))):
                step = side * rng.uniform(0.5, 0.9) * (copy + 1)
                add(group_key, f"trail{copy}", level, [[(round(px - dx * step, 2), round(py - dy * step, 2)) for px, py in face]])
    for key, parts in sorted(shapes.items(), key=lambda item: str(item[0])):
        paths = []
        for (part, level), polys in sorted(parts.items()):
            a = lambda alpha: round(alpha * level, 3)
            name = f"{part}-{int(level * 100)}"
            if part == "back":
                paths += [poly_path(f"{name}-fill", polys, fill=flat(rgb(PLATE, a(0.05))), blend="additive", smooth=False),
                          poly_path(f"{name}-edge", polys, stroke_paint=flat(rgb(LIT, a(0.2))), width=0.8, blend="additive", smooth=False)]
            elif part == "sides":
                paths.append(poly_path(name, polys, stroke_paint=flat(rgb(LIT, a(0.1))), width=0.7, closed=False, blend="additive", smooth=False))
            elif part.startswith("face"):
                large = part == "face-large"
                paths += [poly_path(f"{name}-fill", polys, fill=flat(rgb(PLATE, a(0.05 if large else 0.15))), blend="additive", smooth=False),
                          poly_path(f"{name}-edge", polys, stroke_paint=flat(rgb(LIT, a(0.3 if large else 0.55))), width=1.0, blend="additive")]
            else:
                copy = int(part[-1])
                paths += [poly_path(f"{name}-fill", polys, fill=flat(rgb(PLATE, a(0.05 / (copy + 1)))), blend="additive", smooth=False),
                          poly_path(f"{name}-edge", polys, stroke_paint=flat(rgb(LIT, a(0.2 / (copy + 1)))), width=0.8, blend="additive", smooth=False)]
        ident = f"init-hexes-{key}"
        if key == "still":
            nodes.append(piece(ident, paths))
            continue
        nodes.append(piece(ident, paths, opacity=number(1)))
        period = (5300, 3700, 6900, 4500, 6100, 3900)[key]
        doc.timeline(f"{ident}.pulse", period, [track(ident, "opacity", pulse(rng, 0.45, 1.0, period, 3))], iterations=0)
    return nodes


def rules() -> list:
    """The letterbox's rules: a cyan line on the opening's edge that fades
    into it over 8 u, as in the picture. They run edge to edge."""
    w = {"fraction": 1}

    def rule(ident: str, at_top: bool) -> dict:
        lit, clear = rgb(RULE, 0.55), rgb(RULE, 0)
        if at_top:
            fade = [(0, U * 1.2), (w, U * 1.2), (w, U * 9), (0, U * 9)]
            paint = {"type": "linear", "from": [0, U * 1.2], "to": [0, U * 9], "stops": [{"at": 0, "color": colour(lit)}, {"at": 1, "color": colour(clear)}]}
            line = [(0, 0), (w, 0), (w, U * 1.4), (0, U * 1.4)]
            props = {**absolute(left=0, top=0, height=U * 9)}
        else:
            fade = [(0, 0), (w, 0), (w, U * 7.8), (0, U * 7.8)]
            paint = {"type": "linear", "from": [0, U * 7.8], "to": [0, 0], "stops": [{"at": 0, "color": colour(lit)}, {"at": 1, "color": colour(clear)}]}
            line = [(0, U * 7.6), (w, U * 7.6), (w, U * 9), (0, U * 9)]
            props = {**absolute(left=0, bottom=0, height=U * 9)}
        shape = lambda name, points, fill: {"id": name, "commands": [{"id": f"p{i}", "op": "line" if i else "move", "points": [list(p)]}
                                                                    for i, p in enumerate(points)] + [{"id": "close", "op": "close"}], "fill": fill}
        return vector(ident, {**props, "width": length(100, "%"), **NO_POINTER},
                      [shape("glow", fade, paint), shape("rule", line, flat(rgb(RULE)))])

    return [rule("init-rule-top", True), rule("init-rule-bottom", False)]


def id_mark() -> dict:
    """The id mark, the picture's one piece that stays a bitmap: its block
    cropped from the installed picture, at its distance from the trailing
    edge and across the opening's bottom edge as in the picture."""
    x, y, w, h = ID_BLOCK
    whole = picture("init-id-picture", LAUNCH, {**absolute(left=-U * x, top=-U * y, width=U * 640, height=U * 480), **NO_POINTER})
    return group("init-id", {**absolute(right=U * (640 - x - w), bottom=-U * (y + h - BAND_BOTTOM), width=U * w, height=U * h),
                             "overflow": keyword("hidden"), **NO_POINTER}, [whole])


# -------------------------------------------------------------------- the scene

def initialization_document() -> dict:
    """The start-up screen: the stock picture's elements rebuilt one by one
    behind the status line, with the planet turning, the fires flickering,
    the cells lighting and the loose hexes pulsing each on its own. The
    document is black, with the letterbox's opening centred in it."""
    doc = Document("opend3.initialization")
    doc.state.update({"message": {"type": "string", "initial": ""}, "step": {"type": "number", "initial": 0}})
    rng = random.Random(20261121)
    backdrop, glints = space(rng)
    canvas = group("init-canvas", {**absolute(left=0, top=0, height=720), "top": length(50, "%"), "margin-top": length(-360),
                                   "width": length(100, "%"), **NO_POINTER}, [
        *backdrop,
        *stars(doc, rng),
        *planet(doc),
        *fire(doc),
        glints,
        *honeycomb(doc),
        *lit_cells(doc, rng),
        *loose_hexes(doc, rng),
    ])
    band = group("init-band", {**FULL, "overflow": keyword("hidden"), "background-color": colour(rgb(BASE)), **NO_POINTER}, [canvas])
    # The status line under the opening: BigChars small cells (8 x 16 u),
    # which are the face's cells at half their width.
    status = label("init-status", PLACEHOLDER, {
        **absolute(left=0, height=U * 16), "top": length(100, "%"), "margin-top": length(U * STATUS_GAP), "width": length(100, "%"),
        "font-family": font("bigchars"), "font-size": length(U * 16), "line-height": length(U * 16), "color": colour(rgb(STATUS)),
        "text-align": keyword("center"), "white-space": keyword("nowrap"), "transform": transform(sx=0.5), **NO_POINTER})
    doc.bind("init-status.text", "init-status", "text", {"state": "message"})
    # The opening: its share of the view's height, up to BAND_MAX u, centred
    # by the column it stands in.
    frame = group("init-frame", {"position": keyword("relative"), "width": length(100, "%"), "height": length(round(100 * BAND_SHARE, 4), "%"),
                                 "max-height": length(U * BAND_MAX), "flex-shrink": number(0), **NO_POINTER, "opacity": number(0)},
                  [band, *rules(), id_mark(), status])
    root = group("screen", {**FULL, "display": keyword("flex"), "flex-direction": keyword("column"), "justify-content": keyword("center"),
                            "background-color": colour([0, 0, 0, 1]), "font-family": font("bigchars"), "font-size": length(18),
                            "color": colour([1, 1, 1, 1])}, [frame])
    loops = [timeline["id"] for timeline in doc.timelines if timeline.get("iterations") == 0]
    # The picture arrives out of black in 400 ms; each step of start-up
    # lights the status line white for a moment (the menus' flash).
    doc.timeline("initEnter", 400, [track("init-frame", "opacity", held([(0, number(0)), (400, number(1))]))])
    doc.timeline("initStep", 250, [track("init-status", "color", held([(0, colour([1, 1, 1, 1])), (250, colour(rgb(STATUS)))]))])
    doc.events["onInit"] = [{"op": "setState", "values": {"step": 0}}]
    doc.events["onEnter"] = [{"op": "playTimeline", "timeline": "initEnter"}, *[{"op": "playTimeline", "timeline": loop} for loop in loops]]
    doc.events["stepChanged"] = [{"op": "playTimeline", "timeline": "initStep"}]
    return doc.build(root)
