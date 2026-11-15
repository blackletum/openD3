#!/usr/bin/env python3
"""openD3's retained start-up screen.

Section 10.15 of docs/dev/ui-visual-design.md: the stock start-up screen is
one picture (guis/assets/splash/launch) with a status line. The picture is
taken apart here and each element rebuilt on its own, back to front:

    space        black, with a seeded field of stars in the band
    planet       Mars as the main menu's own model (models/wipes/planet2.lwo),
                 lit from the leading side and turning slowly: the engine
                 gives the document a clock (seconds on screen)
    embers       the night side's fires: additive specks along a ring of
                 fissures, each cluster flickering on its own, over a glow
    wash         the band's teal tint and its lighter horizontal strips
    honeycomb    the fine teal hexagon grid, every edge drawn once
    cells        single cells of that grid that light and fade at random
    hexagons     the large translucent hexagons, three cells to the side,
                 each a node of its own whose transparency pulses on its own
                 period, so no two keep step
    bokeh        the few very large, soft hexagons at the trailing side
    letterbox    the black bars and their cyan rules
    id mark      the one bitmap: the mark's block cropped from the installed
                 picture (a logo is a bitmap exception, section 6)
    status       the start-up status line, BigChars small cells in load.status

The engine presents guis/loading/initialization.rui while it starts
(RetainedUI_DrawInitialization): it raises onInit, then onEnter once the
first frame is on screen, sets `message` and `step` and raises stepChanged
as start-up moves on, and sets `clock` each frame.

The layout is the Remastered one: the band, its rules, the honeycomb and the
stars run to the view's edges; the planet keeps its place on the centred
canvas; the id mark keeps its distance from the trailing edge; the status
line is centred. On a tall view the band stays one canvas high, centred.

build_doom3_menus.py writes the document.
"""

from __future__ import annotations

import math
import random

from doom3_menu_kit import (
    CANVAS_W, FULL, NO_POINTER, U, Document, absolute, box, colour, font, group, held, keyword, label, length, linear, number,
    path, picture, pinned, radial, rgb, solid, stroke, track, transform, vector,
)

PLACEHOLDER = "#str_04339"   # OK: the engine supplies the text
LAUNCH = "guis/assets/splash/launch"

# The stock picture's measures, in canvas u (640 x 480).
BAND_TOP, BAND_BOTTOM = 77.0, 403.0          # the letterbox opening: 16 % to 84 % of the height
PLANET_X, PLANET_Y, PLANET_R = 234.0, 240.0, 190.0
ID_BLOCK = (507.5, 336.3, 98.8, 115.0)       # the id mark's block in the picture
STATUS_Y = 410.0

# Tokens (section 10.15 and the picture).
RULE = "#3988A8"
TEAL_LINE = "#4FB6CF"
TEAL_FILL = "#2A8AA6"
TEAL_WASH = "#1B6A86"
STATUS = "#00CFF0"
EMBER_CORE, EMBER_HOT, EMBER_GLOW = "#FFD98A", "#FF8420", "#E0431A"

# The honeycomb: flat-topped cells 22.5 u across.
SIDE = 11.25
STEP_X, STEP_Y = 1.5 * SIDE, math.sqrt(3) * SIDE
FIELD_W = 1260.0             # u: wide enough for a 21:9 view, centred on the canvas
FIELD_LEFT = 320.0 - FIELD_W / 2
BAND_H = BAND_BOTTOM - BAND_TOP


def field(ident: str, paths: list, **more) -> dict:
    """A vector the width of the widest view and the height of the band,
    centred on the canvas: its paths are in canvas u less (FIELD_LEFT,
    BAND_TOP), and it draws nothing outside the band."""
    return vector(ident, {"position": keyword("absolute"), "left": length(50, "%"), "margin-left": length(-U * FIELD_W / 2),
                          "top": length(0), "width": length(U * FIELD_W), "height": length(U * BAND_H), **NO_POINTER, **more}, paths)


def at(x: float, y: float) -> tuple:
    """A canvas point in a field's own dp."""
    return (round(U * (x - FIELD_LEFT), 2), round(U * (y - BAND_TOP), 2))


def fit(ident: str, paths: list, pad: float = 2.0, **more) -> dict:
    """A vector just large enough for `paths`, whose points are canvas u: a
    piece that is animated on its own is its own small node."""
    points = [point for item in paths for command in item["commands"] for point in command.get("points", ())]
    x0, y0 = min(x for x, _ in points) - pad, min(y for _, y in points) - pad
    x1, y1 = max(x for x, _ in points) + pad, max(y for _, y in points) + pad
    for item in paths:
        for command in item["commands"]:
            if "points" in command:
                command["points"] = [[round(U * (x - x0), 2), round(U * (y - y0), 2)] for x, y in command["points"]]
    return vector(ident, {"position": keyword("absolute"), "left": length(50, "%"), "margin-left": length(round(U * (x0 - 320), 2)),
                          "top": length(round(U * (y0 - BAND_TOP), 2)), "width": length(round(U * (x1 - x0), 2)),
                          "height": length(round(U * (y1 - y0), 2)), **NO_POINTER, **more}, paths)


def cell_centre(column: int, row: int, side: float = SIDE) -> tuple:
    """The centre of a flat-topped cell: columns 1.5 sides apart, odd ones
    half a cell down. Column 0, row 0 is at the canvas centre."""
    return (320.0 + 1.5 * side * column, 240.0 + math.sqrt(3) * side * (row + (0.5 if column % 2 else 0.0)))


def hexagon(x: float, y: float, side: float) -> list:
    """A flat-topped hexagon's corners, from its leading corner clockwise."""
    half = math.sqrt(3) * side / 2
    return [(x - side, y), (x - side / 2, y - half), (x + side / 2, y - half), (x + side, y), (x + side / 2, y + half), (x - side / 2, y + half)]


def polylines(ident: str, lines: list, paint: dict) -> dict:
    """One path of many open lines: each line starts with its own move."""
    commands = []
    for line in lines:
        for index, point in enumerate(line):
            commands.append({"id": f"p{len(commands)}", "op": "line" if index else "move", "points": [list(point)]})
    return {"id": ident, "commands": commands, "stroke": paint}


def polygons(ident: str, shapes: list, fill: dict, blend: str | None = None) -> dict:
    """One path of many closed shapes."""
    commands = []
    for shape in shapes:
        for index, point in enumerate(shape):
            commands.append({"id": f"p{len(commands)}", "op": "line" if index else "move", "points": [list(point)]})
        commands.append({"id": f"p{len(commands)}", "op": "close"})
    result = {"id": ident, "commands": commands, "fill": fill}
    if blend:
        result["blend"] = blend
    return result


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


# ----------------------------------------------------------------- the layers

def stars(rng: random.Random) -> dict:
    """A field of stars: 1 u points, most of them faint."""
    by_alpha: dict = {}
    for _index in range(260):
        x, y = FIELD_LEFT + rng.uniform(0, FIELD_W), rng.uniform(BAND_TOP, BAND_BOTTOM)
        size = 0.9 if rng.random() < 0.85 else 1.5
        alpha = rng.choice((0.25, 0.25, 0.4, 0.4, 0.6, 0.9))
        by_alpha.setdefault(alpha, []).append([at(x, y), at(x + size, y), at(x + size, y + size), at(x, y + size)])
    return field("init-stars", [polygons(f"stars{index}", shapes, solid(rgb("#DDE8F0", alpha)))
                                for index, (alpha, shapes) in enumerate(sorted(by_alpha.items()))])


def planet(doc: Document) -> list:
    """Mars in three dimensions: the main menu's planet model under one
    light from the leading side, so its trailing side is night, turning a
    third of a degree a second. A faint line of air follows the lit limb."""
    doc.state["clock"] = {"type": "number", "initial": 0}
    size = 2 * PLANET_R + 20
    model = {"id": "init-planet", "type": "model",
             "properties": {**box(PLANET_X - size / 2, PLANET_Y - size / 2 - BAND_TOP, size, size), **NO_POINTER},
             "scene": {"parts": [{"model": "models/wipes/planet2.lwo"}],
                       # The model is a sphere of radius 23.7 standing on its origin: lowered by its
                       # radius it turns about its own centre, and from 72.5 away under a 40 degree
                       # view it fills the node but for 10 u all round.
                       "origin": [0, 0, -23.9], "rotation": [0, {"op": "+", "args": [40, {"op": "*", "args": [{"state": "clock"}, 0.33]}]}, 0],
                       "camera": [-72.5, 0, 0], "fov": 40,
                       "lights": [{"origin": [-70, 150, 40], "colour": [1.0, 0.94, 0.88]}]}}
    limb = []
    for step in range(0, 41):
        angle = math.radians(115 + step * 3.25)   # the leading half, top to bottom
        limb.append((U * (size / 2 + (PLANET_R + 0.5) * math.cos(angle)), U * (size / 2 - (PLANET_R + 0.5) * math.sin(angle))))
    air = vector("init-planet-air", {**box(PLANET_X - size / 2, PLANET_Y - size / 2 - BAND_TOP, size, size), **NO_POINTER}, [
        {"id": "air", "commands": [{"id": f"p{index}", "op": "line" if index else "move", "points": [[round(x, 2), round(y, 2)]]}
                                   for index, (x, y) in enumerate(limb)],
         "stroke": stroke(solid(rgb("#F2C8B4", 0.28)), U * 1.6, minimum=1)}])
    return [model, air]


def embers(doc: Document, rng: random.Random) -> list:
    """The night side's fires: specks along a ring of fissures and a
    scatter beyond it, in clusters that flicker each on its own; under them
    a dull glow. All of it is additive light."""
    def on_night_side(x: float, y: float) -> bool:
        return (x - PLANET_X) ** 2 + (y - PLANET_Y) ** 2 < (PLANET_R - 4) ** 2 and x > PLANET_X + 48 and BAND_TOP + 4 < y < BAND_BOTTOM - 4

    def speck(x: float, y: float, reach: float) -> list:
        corners = rng.randint(4, 6)
        turn = rng.uniform(0, math.tau)
        return [(x + reach * rng.uniform(0.5, 1.0) * math.cos(turn + math.tau * corner / corners) * 0.7,
                 y + reach * rng.uniform(0.5, 1.0) * math.sin(turn + math.tau * corner / corners)) for corner in range(corners)]

    # The ring: an ellipse seen from the side, broken into runs.
    centre_x, centre_y, radius_x, radius_y = 362.0, 232.0, 40.0, 84.0
    clusters: list = []
    angle = rng.uniform(0, 30)
    while angle < 350:
        run = rng.uniform(14, 34)
        cluster = []
        for _speck in range(int(run * rng.uniform(0.35, 0.6))):
            along = math.radians(angle + rng.uniform(0, run))
            wander = rng.gauss(0, 3.0)
            x = centre_x + (radius_x + wander) * math.cos(along)
            y = centre_y + (radius_y + wander * 1.6) * math.sin(along)
            if on_night_side(x, y):
                cluster.append((x, y, rng.uniform(1.3, 3.6)))
        if cluster:
            clusters.append(cluster)
        angle += run + rng.uniform(4, 22)
    # A scatter of lone fires across the rest of the night side.
    for _lone in range(9):
        x, y = PLANET_X + rng.uniform(60, 180), PLANET_Y + rng.uniform(-150, 150)
        if on_night_side(x, y):
            clusters.append([(x + rng.gauss(0, 2.5), y + rng.gauss(0, 2.5), rng.uniform(0.9, 2.2)) for _n in range(rng.randint(2, 5))
                             if on_night_side(x, y)])

    glow_stops = [(0, rgb(EMBER_GLOW, 0.20)), (0.35, rgb(EMBER_GLOW, 0.30)), (0.7, rgb(EMBER_GLOW, 0.12)), (1, rgb(EMBER_GLOW, 0))]
    glow_box = [at(centre_x - 95, centre_y - 130), at(centre_x + 70, centre_y - 130), at(centre_x + 70, centre_y + 130), at(centre_x - 95, centre_y + 130)]
    nodes = [field("init-ember-glow", [
        {"id": "glow", "commands": [{"id": f"p{index}", "op": "line" if index else "move", "points": [list(point)]}
                                    for index, point in enumerate(glow_box)] + [{"id": "close", "op": "close"}],
         "fill": radial(at(centre_x, centre_y), at(centre_x + 90, centre_y), glow_stops), "blend": "additive"}], opacity=number(1))]
    doc.timeline("init-ember-glow.breathe", 6000, [track("init-ember-glow", "opacity", [
        (0, number(1)), (1700, number(0.78)), (2900, number(0.95)), (4300, number(0.7)), (6000, number(1))])], iterations=0)
    for index, cluster in enumerate(clusters):
        ident = f"init-ember-{index}"
        halo = polygons("halo", [speck(x, y, reach * 2.6) for x, y, reach in cluster], solid(rgb(EMBER_GLOW, 0.34)), "additive")
        hot = polygons("hot", [speck(x, y, reach * 1.3) for x, y, reach in cluster], solid(rgb(EMBER_HOT, 0.85)), "additive")
        core = polygons("core", [speck(x, y, reach * 0.5) for x, y, reach in cluster], solid(rgb(EMBER_CORE, 0.8)), "additive")
        nodes.append(fit(ident, [halo, hot, core], opacity=number(1)))
        period = rng.randint(1700, 4200)
        doc.timeline(f"{ident}.flicker", period, [track(ident, "opacity", pulse(rng, 0.45, 1.0, period, 3))], iterations=0)
    return nodes


def wash() -> dict:
    """The band's tint: teal over everything in it, and lighter strips
    across it with soft edges."""
    left, right = at(FIELD_LEFT, 0)[0], at(FIELD_LEFT + FIELD_W, 0)[0]

    def strip(ident: str, top: float, bottom: float, alpha: float) -> dict:
        y0, y1 = U * (top - BAND_TOP), U * (bottom - BAND_TOP)
        edge = min(U * 5, (y1 - y0) / 2)
        tint, clear = rgb(TEAL_WASH, alpha), rgb(TEAL_WASH, 0)
        span = (y1 - y0) or 1
        return {"id": ident, "commands": [{"id": "p0", "op": "move", "points": [[left, y0]]}, {"id": "p1", "op": "line", "points": [[right, y0]]},
                                          {"id": "p2", "op": "line", "points": [[right, y1]]}, {"id": "p3", "op": "line", "points": [[left, y1]]},
                                          {"id": "close", "op": "close"}],
                "fill": linear((0, y0), (0, y1), [(0, clear), (round(edge / span, 3), tint), (round(1 - edge / span, 3), tint), (1, clear)])}

    whole = {"id": "tint", "commands": [{"id": "p0", "op": "move", "points": [[left, 0]]}, {"id": "p1", "op": "line", "points": [[right, 0]]},
                                        {"id": "p2", "op": "line", "points": [[right, U * BAND_H]]},
                                        {"id": "p3", "op": "line", "points": [[left, U * BAND_H]]}, {"id": "close", "op": "close"}],
             "fill": solid(rgb(TEAL_WASH, 0.17))}
    return field("init-wash", [whole, strip("strip0", 96, 150, 0.11), strip("strip1", 176, 196, 0.06), strip("strip2", 246, 262, 0.08),
                               strip("strip3", 300, 372, 0.10)])


def columns_and_rows(side: float) -> tuple:
    reach_x = int(FIELD_W / 2 / (1.5 * side)) + 1
    reach_y = int(BAND_H / 2 / (math.sqrt(3) * side)) + 2
    return range(-reach_x, reach_x + 1), range(-reach_y, reach_y + 1)


def honeycomb() -> list:
    """The fine grid. Each cell draws its top edge and its two leading
    edges, so every edge of the honeycomb is drawn once. It is cut into
    strips six columns wide: one vector's coverage has a budget."""
    columns, rows = columns_and_rows(SIDE)
    strips: dict = {}
    for column in columns:
        for row in rows:
            corners = hexagon(*cell_centre(column, row), SIDE)
            if corners[5][1] < BAND_TOP - STEP_Y or corners[1][1] > BAND_BOTTOM + STEP_Y:
                continue
            strips.setdefault((column - columns[0]) // 6, []).append([corners[5], corners[0], corners[1], corners[2]])
    paint = stroke(solid(rgb(TEAL_LINE, 0.30)), U * 0.75, minimum=1)
    return [fit(f"init-honeycomb-{index}", [polylines("cells", lines, paint)]) for index, lines in sorted(strips.items())]


def lit_cells(doc: Document, rng: random.Random) -> list:
    """Single cells of the fine grid that light and fade: each has a period
    and a moment of its own, and most of the time is dark."""
    columns, rows = columns_and_rows(SIDE)
    visible = [(column, row) for column in columns for row in rows
               if abs(cell_centre(column, row)[0] - 320) < 560 and BAND_TOP + 8 < cell_centre(column, row)[1] < BAND_BOTTOM - 8]
    nodes = []
    for index, (column, row) in enumerate(rng.sample(visible, 44)):
        ident = f"init-cell-{index}"
        shape = hexagon(*cell_centre(column, row), SIDE - 0.6)
        nodes.append(fit(ident, [polygons("cell", [shape], solid(rgb(TEAL_LINE, 0.5)))], opacity=number(0)))
        period = rng.randint(3800, 9500)
        start = rng.randint(100, period - 2300)
        rise, hold, fall = rng.randint(250, 600), rng.randint(60, 400), rng.randint(500, 1100)
        peak = round(rng.uniform(0.35, 0.9), 3)
        doc.timeline(f"{ident}.blink", period, [track(ident, "opacity", [
            (0, number(0)), (start, number(0)), (start + rise, number(peak)), (start + rise + hold, number(peak)),
            (max(start + rise + hold + 100, min(period - 50, start + rise + hold + fall)), number(0)), (period, number(0))])], iterations=0)
    return nodes


def large_hexagons(doc: Document, rng: random.Random) -> list:
    """The large hexagons: three cells to the side, on the fine grid's own
    lines, translucent teal under a brighter outline. They gather at the
    trailing side of the planet. Each is a node of its own and pulses on its
    own period."""
    side = 3 * SIDE
    columns, rows = columns_and_rows(side)
    nodes = []
    for column in columns:
        for row in rows:
            x, y = cell_centre(column, row, side)
            if abs(x - 320) > 590 or not (BAND_TOP - 20 < y < BAND_BOTTOM + 20):
                continue
            # Dense beyond the planet's trailing limb, sparse over its day side.
            chance = 0.62 if x > 330 else 0.30 if x > 250 else 0.12 if x > 40 else 0.34
            if rng.random() > chance:
                continue
            ident = f"init-hex-{len(nodes)}"
            shape = hexagon(x, y, side - 0.8)
            weight = rng.choice((0.10, 0.14, 0.18, 0.24))
            fill = polygons("fill", [shape], solid(rgb(TEAL_FILL, weight)))
            edge = polylines("edge", [[*shape, shape[0]]], stroke(solid(rgb(TEAL_LINE, min(0.75, weight * 3.2))), U * 1.1, minimum=1))
            nodes.append(fit(ident, [fill, edge], opacity=number(1)))
            period = rng.randint(2600, 7400)
            doc.timeline(f"{ident}.pulse", period, [track(ident, "opacity", pulse(rng, 0.30, 1.0, period, 2))], iterations=0)
    return nodes


def bokeh(rng: random.Random) -> dict:
    """A few very large, soft hexagons out of focus at the trailing side."""
    shapes = []
    for x, y, side in ((470, 150, 58), (560, 215, 74), (430, 300, 66), (620, 330, 82), (700, 170, 70), (140, 120, 52), (40, 300, 64)):
        shapes.append([at(*corner) for corner in hexagon(x + rng.uniform(-6, 6), y + rng.uniform(-6, 6), side)])
    return field("init-bokeh", [polygons(f"soft{index}", [shape], solid(rgb(TEAL_FILL, 0.07))) for index, shape in enumerate(shapes)])


def letterbox() -> list:
    """The black bars and their rules: 2.5 u of cyan with a soft edge on the
    band's side. The bars run on past the canvas on a tall view."""
    def bar(ident: str, top: float, height: float) -> dict:
        return group(ident, {**absolute(left=0, top=U * top, height=U * height), "width": length(100, "%"),
                             "background-color": colour([0, 0, 0, 1]), **NO_POINTER})

    w = {"fraction": 1}

    def rule(ident: str, y: float, glow_down: bool) -> dict:
        lit, clear = rgb(RULE, 0.45), rgb(RULE, 0)
        glow = [(0, U * 2.5), (w, U * 2.5), (w, U * 9), (0, U * 9)] if glow_down else [(0, 0), (w, 0), (w, U * 6.5), (0, U * 6.5)]
        ramp = linear((0, U * 2.5), (0, U * 9), [(0, lit), (1, clear)]) if glow_down else linear((0, U * 6.5), (0, 0), [(0, lit), (1, clear)])
        line_y = 0 if glow_down else U * 6.5
        return vector(ident, {**absolute(left=0, top=U * (y if glow_down else y - 6.5), height=U * 9), "width": length(100, "%"), **NO_POINTER}, [
            path("glow", glow, fill=ramp),
            path("rule", [(0, line_y), (w, line_y), (w, line_y + U * 2.5), (0, line_y + U * 2.5)], fill=solid(rgb(RULE)))])

    return [bar("init-bar-top", -3000, 3000 + BAND_TOP - 2.5), bar("init-bar-bottom", BAND_BOTTOM + 2.5, 3000),
            rule("init-rule-top", BAND_TOP - 2.5, True), rule("init-rule-bottom", BAND_BOTTOM, False)]


def id_mark() -> dict:
    """The id mark, the picture's one piece that stays a bitmap: its block
    cropped from the installed picture, at its distance from the trailing
    edge."""
    x, y, w, h = ID_BLOCK
    whole = picture("init-id-picture", LAUNCH, {**absolute(left=-U * x, top=-U * y, width=U * 640, height=U * 480), **NO_POINTER})
    return group("init-id", {**absolute(right=U * (640 - x - w), top=U * y, width=U * w, height=U * h), "overflow": keyword("hidden"),
                             **NO_POINTER, "opacity": number(1)}, [whole])


def initialization_document() -> dict:
    """The start-up screen: the stock picture's elements rebuilt one by one
    behind the status line, with the planet turning, the fires flickering
    and the hexagons pulsing each on its own."""
    doc = Document("opend3.initialization")
    doc.state.update({"message": {"type": "string", "initial": ""}, "step": {"type": "number", "initial": 0}})
    rng = random.Random(20261115)

    band = group("init-band", {**absolute(left=0, top=U * BAND_TOP, height=U * BAND_H), "width": length(100, "%"), "overflow": keyword("hidden"),
                               **NO_POINTER}, [])
    on_canvas = {**absolute(top=0, width=CANVAS_W, height=0), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)}
    band["children"] = [
        stars(rng),
        group("init-planet-place", on_canvas, planet(doc)),
        *embers(doc, rng),
        wash(),
        bokeh(rng),
        *honeycomb(),
        *lit_cells(doc, rng),
        *large_hexagons(doc, rng),
    ]

    # The status line: BigChars small cells (8 x 16 u), which are the face's
    # cells at half their width.
    status = label("init-status", PLACEHOLDER, {
        **absolute(left=0, top=U * STATUS_Y, height=U * 16), "width": length(100, "%"), "font-family": font("bigchars"),
        "font-size": length(U * 16), "line-height": length(U * 16), "color": colour(rgb(STATUS)), "text-align": keyword("center"),
        "white-space": keyword("nowrap"), "transform": transform(sx=0.5), **NO_POINTER})
    doc.bind("init-status.text", "init-status", "text", {"state": "message"})
    trail = group("init-trail", {**absolute(left=0, top=0, height=0), "width": length(100, "%")}, [id_mark()])
    stage = group("init-stage", {**pinned("middle"), **NO_POINTER, "opacity": number(0)}, [band, *letterbox(), trail, status])
    root = group("screen", {**FULL, "background-color": colour([0, 0, 0, 1]), "font-family": font("bigchars"), "font-size": length(18),
                            "color": colour([1, 1, 1, 1])}, [stage])

    # The picture arrives out of black in 400 ms; each step of start-up
    # lights the status line white for a moment (the menus' flash).
    doc.timeline("initEnter", 400, [track("init-stage", "opacity", held([(0, number(0)), (400, number(1))]))])
    doc.timeline("initStep", 250, [track("init-status", "color", held([(0, colour([1, 1, 1, 1])), (250, colour(rgb(STATUS)))]))])
    loops = [timeline["id"] for timeline in doc.timelines if timeline.get("iterations") == 0]
    doc.events["onInit"] = [{"op": "setState", "values": {"step": 0}}]
    doc.events["onEnter"] = [{"op": "playTimeline", "timeline": "initEnter"}, *[{"op": "playTimeline", "timeline": loop} for loop in loops]]
    doc.events["stepChanged"] = [{"op": "playTimeline", "timeline": "initStep"}]
    return doc.build(root)
