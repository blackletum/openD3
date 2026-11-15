#!/usr/bin/env python3
"""openD3's retained level loading screen.

Section 10.14 of docs/dev/ui-visual-design.md: a loading screen is a dark
picture of the level under two black bands cut with a 45 degree step, the
word LOADING typed out above an amber bar, and the level's name and briefing
below. The picture and its scan lines are real imagery the specification
keeps, so the map's own stock screen (guis/map/<map>.gui) goes on drawing
them and this document draws the rest.

One document serves every level. The session reads the level's words and the
places of the bottom band from the stock screen and publishes them
(idSessionLocal::SelectRetainedLoadingGui): load.title, load.subtitle,
load.briefing, load.text (the screen has a subtitle and a briefing), and in
u load.band_y, load.step_x and load.title_y. The engine counts map_loading
from 0 to 1 as it loads. The session raises `present` when a load begins.

Section 10.14's variants are kinds of this document (load.kind): the hell
screen has the progress group alone over its picture, the word settling to
load.word.hell in a frame tinted red; the first level's screen is black
(the stock screen draws nothing but its backdrop) with the word and the bar
in the middle. The fallback screen is a picture with no furniture and stays
the stock GUI.

The layout is the Remastered one (rule 7): the bands run to the screen's
edges with their steps where the 4:3 canvas has them, the progress group
keeps its place from the top-leading corner, and the text block keeps its
inset from the leading edge and its distances from the bottom edge.

build_doom3_menus.py writes the document.
"""

from __future__ import annotations

from doom3_menu_kit import (
    DECEL, FACE_AN, FACE_DEFAULT, FULL, NO_POINTER, U, Document, absolute, colour, em, font, group, held, keyword, label, length,
    linear, mid, number, path, radial, rgb, solid, track, transform, typeface, vector,
)

FACE_MICRO = "micro"
PLACEHOLDER = "#str_04339"   # OK: the session supplies the text
OPEN_MS = 900                # section 10.14's timeline is at rest

# Section 10.14's tokens.
BAND = rgb("#000000", 0.6)
BAND_EDGE = "#40586F"
WORD = rgb("#3399B2")
WORD_HELL = rgb("#FF331A")
BAR_ROWS = ("#FFC266", "#FFC266", "#FFD37C", "#FFA319", "#E68A00", "#B86F00", "#995C00")
FRAME = ("#98C1C1", "#002A2A", "#79AFAF", "#003333", "#589797")   # top light and dark, bottom light and dark, ends
# The hell screen tints the frame's art #FF0000, which leaves its red alone.
FRAME_HELL = ("#980000", "#000000", "#790000", "#000000", "#580000")
# The kinds of screen (load.kind, idSessionLocal::SelectRetainedLoadingGui).
STANDARD, HELL, FIRST = 0, 1, 2

# The word's typed stages, as the stock types them: (ms, text). The stock's
# first frame is a lone L, which has no string of its own.
WORD_STAGES = ((50, "#str_03469"), (100, "#str_03470"), (150, "#str_03343"), (200, "#str_03471"), (250, "#str_03472"),
               (300, "#str_00408"))
# The flare rides the newest letter: (ms, left in u).
FLARE_STOPS = ((0, 0), (50, 17), (100, 37), (150, 57), (200, 67), (250, 81), (300, 100))
# The first level's word is centred on x 320 and grows both ways as it is
# typed; its flare's stops are the stock's, from the canvas's centre.
FIRST_FLARE_STOPS = ((0, 290 - 320), (50, 304 - 320), (100, 313 - 320), (150, 322 - 320), (200, 329 - 320), (250, 334 - 320),
                     (300, 344 - 320))

# Measured against the stock screen at 1280x720. At textscale 0.40 the stock
# draws its larger atlas, which stands about 7 % taller than the outline and
# further apart; its text also sits 1.3 u lower in its rect than a centred
# line and 2 u in from the rect's leading edge, and the briefing's lines are
# 17.7 u apart and its letters a little wider set.
FIT_40 = {FACE_MICRO: (1.07, 0.65), FACE_DEFAULT: (1.07, 0.7)}
TEXT_DROP = 1.3
TEXT_INSET = 2.0        # u: the stock draws text this far inside its rect's leading edge
BRIEFING_PITCH = 17.7
BRIEFING_TRACKING = 1.66   # dp: AN 0.25's fitted spacing and 0.22 more


def face_40(face: str, tint: list, align: str = "left") -> dict:
    """Text at the stock's textscale 0.40, fitted to the stock's metrics."""
    grow, tracking = FIT_40[face]
    return {**typeface(face, 0.40, 27, tint, align), "font-size": length(round(em(0.40) * grow, 3)), "letter-spacing": length(tracking)}


SPREAD = 80.0   # u: how far a band's node runs past each screen edge, for its slide and its step's place
LEAD, TRAIL = {"fraction": 0, "dp": 0}, {"fraction": 1, "dp": 0}


def edge_strip(ident: str, points: list, start: tuple, end: tuple, toward_edge: bool) -> dict:
    """A piece of a band's soft inner line: load.band.edge from 2 % to 67 %
    over 9 u, brightest on the band's edge."""
    stops = [(0, rgb(BAND_EDGE, 0.02)), (1, rgb(BAND_EDGE, 0.67))] if toward_edge else [(0, rgb(BAND_EDGE, 0.67)), (1, rgb(BAND_EDGE, 0.02))]
    return path(ident, points, fill=linear(start, end, stops))


def band_node(ident: str, height: float, paths: list) -> dict:
    return vector(ident, {"position": keyword("absolute"), "left": length(-U * SPREAD), "right": length(-U * SPREAD), "top": length(0),
                          "height": length(U * height), **NO_POINTER}, paths)


def top_band() -> dict:
    """The top band (section 10.14): solid to 34 u leading of the step and to
    21 u trailing of it, the step a 45 degree ramp from x 178 to 190."""
    return band_node("load-top-band-ink", 48, [
        path("band", [(LEAD, 0), (TRAIL, 0), (TRAIL, U * 21), (mid(190), U * 21), (mid(178), U * 34), (LEAD, U * 34)], fill=solid(BAND)),
        edge_strip("edge-lead", [(LEAD, U * 25), (mid(178), U * 25), (mid(178), U * 34), (LEAD, U * 34)], (0, U * 25), (0, U * 34), True),
        edge_strip("edge-step", [(mid(178), U * 25), (mid(190), U * 12), (mid(190), U * 21), (mid(178), U * 34)],
                   (mid(184), U * 18.5), (mid(188.5), U * 22.6), True),
        edge_strip("edge-trail", [(mid(190), U * 12), (TRAIL, U * 12), (TRAIL, U * 21), (mid(190), U * 21)], (0, U * 12), (0, U * 21), True),
    ])


def bottom_band() -> dict:
    """The bottom band, in its own rect's coordinates (stock bgBlackBottom,
    whose step window stands at x 347): its edge 9 u down leading of the
    step and 22 u trailing of it, the step from x 355 to 367, and a fade to
    solid black from 30 u down to 98."""
    return band_node("load-bottom-band-ink", 220, [
        path("band", [(LEAD, U * 9), (mid(355), U * 9), (mid(367), U * 22), (TRAIL, U * 22), (TRAIL, U * 220), (LEAD, U * 220)], fill=solid(BAND)),
        path("fade", [(LEAD, U * 30), (TRAIL, U * 30), (TRAIL, U * 220), (LEAD, U * 220)],
             fill=linear((0, U * 30), (0, U * 98), [(0, rgb("#000000", 0)), (1, rgb("#000000", 1))])),
        edge_strip("edge-lead", [(LEAD, U * 9), (mid(355), U * 9), (mid(355), U * 18), (LEAD, U * 18)], (0, U * 9), (0, U * 18), False),
        edge_strip("edge-step", [(mid(355), U * 9), (mid(367), U * 22), (mid(367), U * 31), (mid(355), U * 18)],
                   (mid(361), U * 15.5), (mid(356.5), U * 19.6), False),
        edge_strip("edge-trail", [(mid(367), U * 22), (TRAIL, U * 22), (TRAIL, U * 31), (mid(367), U * 31)], (0, U * 22), (0, U * 31), False),
    ])


def bar_frame(ident: str, left: float, top: float, tints: tuple) -> dict:
    """The bar's hollow frame, 170 x 9 u: a light line over a dark one at the
    top and the bottom and two-column ends, all at 80 %. `tints` is (top
    light, top dark, bottom light, bottom dark, ends)."""
    def line(name: str, at: float, tint: str) -> dict:
        return path(name, [(0, U * at), (U * 170, U * at), (U * 170, U * (at + 1)), (0, U * (at + 1))], fill=solid(rgb(tint, 0.8)))

    def end(name: str, at: float) -> dict:
        return path(name, [(U * at, U * 2), (U * (at + 2), U * 2), (U * (at + 2), U * 7), (U * at, U * 7)], fill=solid(rgb(tints[4], 0.8)))

    return vector(ident, {**absolute(left=U * left, top=U * top, width=U * 170, height=U * 9), **NO_POINTER, "opacity": number(0)},
                  [line("top-light", 0, tints[0]), line("top-dark", 1, tints[1]), line("bottom-light", 7, tints[2]),
                   line("bottom-dark", 8, tints[3]), end("lead-end", 0), end("trail-end", 168)])


def progress_fill(doc: Document, ident: str, left: float, top: float) -> dict:
    """The bar's fill (section 10.14): seven amber rows 168 x 7 u, revealed
    from the leading end by the clamped progress."""
    rows = [path(f"row{index}", [(0, U * index), (U * 168, U * index), (U * 168, U * (index + 1)), (0, U * (index + 1))], fill=solid(rgb(tint, 0.8)))
            for index, tint in enumerate(BAR_ROWS)]
    fill = vector(f"{ident}-ink", {**absolute(left=0, top=0, width=U * 168, height=U * 7), **NO_POINTER}, rows)
    doc.bind(f"{ident}.width", ident, "width", {"op": "*", "args": [{"op": "clamp", "args": [{"state": "map_loading"}, 0, 1]}, U * 168]})
    return group(ident, {**absolute(left=U * left, top=U * top, width=0, height=U * 7), "overflow": keyword("hidden"), **NO_POINTER}, [fill])


def word(tracks: list, prefix: str, place: dict, align: str, flare_stops: tuple, flare_top: float, finals: tuple) -> list:
    """The word LOADING (section 10.14): Micro 0.40, typed a letter every 50
    ms in white with the flare on the newest letter, then settling to its
    colour in 200 ms as the flare fades. `finals` is the complete word once
    for each colour it may settle to, (id suffix, tint); the caller shows
    one. `flare_stops` is the flare's left edge in u as each letter lands."""
    nodes = []
    for index, (at, key) in enumerate(WORD_STAGES):
        last = index + 1 == len(WORD_STAGES)
        for suffix, tint in (finals if last else (("", None),)):
            ident = f"{prefix}-word-{index}{suffix}"
            nodes.append(label(ident, key, {**place, **face_40(FACE_MICRO, [1, 1, 1, 1], align), "opacity": number(0)}))
            keys = [(0, number(0)), (at - 1, number(0)), (at, number(1))]
            if last:
                keys += [(OPEN_MS, number(1))]
                tracks.append(track(ident, "color", held([(0, colour([1, 1, 1, 1])), (at, colour([1, 1, 1, 1])), (at + 200, colour(tint)),
                                                          (OPEN_MS, colour(tint))])))
            else:
                gone = WORD_STAGES[index + 1][0]
                keys += [(gone - 1, number(1)), (gone, number(0)), (OPEN_MS, number(0))]
            tracks.append(track(ident, "opacity", held(keys)))
    glow = [(0, rgb("#669999", 0.5)), (1, rgb("#669999", 0))]
    flare = vector(f"{prefix}-flare", {**absolute(left=U * flare_stops[0][1], top=U * flare_top, width=U * 54, height=U * 21), **NO_POINTER,
                                       "opacity": number(0)},
                   [path("flare", [(0, 0), (U * 54, 0), (U * 54, U * 21), (0, U * 21)], fill=radial((U * 27, U * 10.5), (U * 54, U * 10.5), glow),
                         blend="additive")])
    moves = [(0, length(U * flare_stops[0][1]))]
    for at, left in flare_stops[1:]:
        moves += [(at - 1, moves[-1][1]), (at, length(U * left))]
    tracks.append(track(f"{prefix}-flare", "left", held([*moves, (OPEN_MS, length(U * flare_stops[-1][1]))])))
    tracks.append(track(f"{prefix}-flare", "opacity", held([(0, number(0)), (200, number(1)), (300, number(1)), (500, number(0)), (OPEN_MS, number(0))])))
    return [*nodes, flare]


def loading_document() -> dict:
    """The loading screen's furniture over the stock picture: the two bands
    sliding to rest, the word and the bar top-leading, and bottom-leading the
    level's title and, where the screen has them, its subtitle on the title
    bar and its briefing."""
    doc = Document("opend3.loading")
    doc.state.update({
        "map_loading": {"type": "number", "initial": 0},
        "load.title": {"type": "string", "initial": ""}, "load.subtitle": {"type": "string", "initial": ""},
        "load.briefing": {"type": "string", "initial": ""}, "load.text": {"type": "boolean", "initial": True},
        "load.band_y": {"type": "number", "initial": 322}, "load.step_x": {"type": "number", "initial": 347},
        "load.title_y": {"type": "number", "initial": 336}, "load.kind": {"type": "number", "initial": STANDARD},
    })
    tracks: list = []
    kind_is = lambda kind: {"op": "==", "args": [{"state": "load.kind"}, kind]}

    def shown(node: dict, test: dict, otherwise: bool = False) -> dict:
        """`node`, taking its place only while `test` holds (or only while it
        does not)."""
        node["properties"]["display"] = keyword("block")   # a bound property needs a base value
        doc.bind(f"{node['id']}.display", node["id"], "display", {"op": "select", "args": [test, *(("none", "block") if otherwise else ("block", "none"))]})
        return node

    def frame_in(ident: str) -> None:
        tracks.append(track(ident, "opacity", held([(0, number(0)), (300, number(0)), (OPEN_MS, number(1))])))

    # Top-leading: the band, then the progress group over it. The hell
    # screen has the group alone, its word settling to red in a red frame.
    top_slide = shown(group("load-top-band", {**absolute(left=0, top=0, height=0), "width": length(100, "%"), "transform": transform()},
                            [top_band()]), kind_is(STANDARD))
    tracks.append(track("load-top-band", "transform", held([(0, transform(tx=-U * 20), DECEL), (400, transform()), (OPEN_MS, transform())])))
    lead_word = word(tracks, "load", {**absolute(left=U * (16 + TEXT_INSET), top=U * (TEXT_DROP - 6), width=U * 200, height=U * 27), **NO_POINTER},
                     "left", FLARE_STOPS, 0, (("", WORD), ("-hell", WORD_HELL)))
    lead_frames = [bar_frame("load-frame", 5, 22, FRAME), bar_frame("load-frame-hell", 5, 22, FRAME_HELL)]
    for node in (*lead_word, *lead_frames):
        if node["id"].endswith("-hell"):
            shown(node, kind_is(HELL))
        elif node["id"] in ("load-frame", f"load-word-{len(WORD_STAGES) - 1}"):
            shown(node, kind_is(HELL), otherwise=True)
    frame_in("load-frame")
    frame_in("load-frame-hell")
    lead = shown(group("load-lead", {**absolute(left=0, top=0, height=0), "width": length(100, "%")},
                       [progress_fill(doc, "load-fill", 6, 23), *lead_frames, *lead_word]), kind_is(FIRST), otherwise=True)
    top = group("load-top", {**absolute(left=0, top=0, height=0), "width": length(100, "%")}, [top_slide, lead])

    # The first level's screen: the word centred at y 211 of the canvas and
    # the bar beneath it (frame 235, 242), from the view's centre.
    first_word = word(tracks, "load-first", {**absolute(left=U * (170 - 320), top=U * (211 + TEXT_DROP - 240), width=U * 300, height=U * 27),
                                             **NO_POINTER}, "center", FIRST_FLARE_STOPS, 217 - 240, (("", WORD),))
    frame_in("load-first-frame")
    first = shown(group("load-first", {"position": keyword("absolute"), "left": length(50, "%"), "top": length(50, "%"), "width": length(0),
                                       "height": length(0)},
                        [progress_fill(doc, "load-first-fill", 236 - 320, 243 - 240), bar_frame("load-first-frame", 235 - 320, 242 - 240, FRAME),
                         *first_word]), kind_is(FIRST))

    # Bottom-leading: the band where the stock screen has it, then the text.
    from_bottom = lambda state: {"op": "*", "args": [{"op": "-", "args": [{"state": state}, 480]}, U]}
    step = group("load-bottom-step", {**absolute(left=0, top=0, height=0), "width": length(100, "%"), "transform": transform()}, [bottom_band()])
    doc.bind("load-bottom-step.transform", "load-bottom-step", "transform",
             [{"op": "*", "args": [{"op": "-", "args": [{"state": "load.step_x"}, 347]}, U]}, 0, 1, 1, 0])
    slide = group("load-bottom-band", {**absolute(left=0, top=0, height=0), "width": length(100, "%"), "transform": transform()}, [step])
    tracks.append(track("load-bottom-band", "transform", held([(0, transform(tx=U * 30), DECEL), (400, transform()), (OPEN_MS, transform())])))
    band = group("load-bottom-place", {**absolute(left=0, top=U * (322 - 480), height=0), "width": length(100, "%")}, [slide])
    doc.bind("load-bottom-place.top", "load-bottom-place", "top", from_bottom("load.band_y"))

    # The bar runs from the leading edge to the canvas's x 512; the stock art
    # is solid to 72 % of that length and faded out by 92 %.
    along = lambda part: ({"fraction": round(0.5 * part, 4), "dp": round(U * (512 - 320) * part, 3)}, 0)
    bar = vector("load-titlebar", {**absolute(left=0, top=U * 35, height=U * 19), "width": length(100, "%"), **NO_POINTER, "transform": transform()},
                 [path("bar", [(0, 0), (mid(512), 0), (mid(512), U * 19), (0, U * 19)],
                       fill=linear(along(0.72), along(0.92), [(0, [1, 1, 1, 0.14]), (1, [1, 1, 1, 0])]))])
    tracks.append(track("load-titlebar", "transform", held([(0, transform(tx=-U * 300)), (200, transform(tx=-U * 300), DECEL), (600, transform()),
                                                            (OPEN_MS, transform())])))
    title = label("load-title", PLACEHOLDER, {**absolute(left=U * (16 + TEXT_INSET), top=U * TEXT_DROP, width=U * 610, height=U * 27),
                                              **face_40(FACE_MICRO, [1, 1, 1, 0.9]), **NO_POINTER, "opacity": number(0)})
    subtitle = label("load-subtitle", PLACEHOLDER, {**absolute(left=U * (16 + TEXT_INSET), top=U * (31 + TEXT_DROP / 2), width=U * 610, height=U * 27),
                                                    **face_40(FACE_DEFAULT, [1, 1, 1, 0.4]), **NO_POINTER, "opacity": number(0)})
    briefing = label("load-briefing", PLACEHOLDER, {**absolute(left=U * (17 + TEXT_INSET), top=U * (58 + 2 * TEXT_DROP), width=U * 521, height=U * 81),
                                                    **typeface(FACE_AN, 0.25, BRIEFING_PITCH, [1, 1, 1, 1]), "letter-spacing": length(BRIEFING_TRACKING),
                                                    "white-space": keyword("normal"),
                                                    "overflow": keyword("hidden"), **NO_POINTER, "opacity": number(0)})
    for node, state in (("load-title", "load.title"), ("load-subtitle", "load.subtitle"), ("load-briefing", "load.briefing")):
        doc.bind(f"{node}.text", node, "text", {"state": state})
    for node in (bar, subtitle, briefing):
        node["properties"]["display"] = keyword("block")   # a bound property needs a base value
    for node in ("load-titlebar", "load-subtitle", "load-briefing"):
        doc.bind(f"{node}.display", node, "display", {"op": "select", "args": [{"state": "load.text"}, "block", "none"]})
    for node in ("load-title", "load-subtitle"):
        tracks.append(track(node, "opacity", held([(0, number(0)), (200, number(0), DECEL), (600, number(1)), (OPEN_MS, number(1))])))
    tracks.append(track("load-briefing", "opacity", held([(0, number(0)), (300, number(0), DECEL), (700, number(1)), (OPEN_MS, number(1))])))
    tracks.append(track("load-briefing", "left", held([(0, length(U * (10 + TEXT_INSET))), (300, length(U * (10 + TEXT_INSET)), DECEL),
                                                       (700, length(U * (17 + TEXT_INSET))), (OPEN_MS, length(U * (17 + TEXT_INSET)))])))
    block = group("load-block", {**absolute(left=0, top=U * (336 - 480), height=0), "width": length(100, "%")}, [bar, title, subtitle, briefing])
    doc.bind("load-block.top", "load-block", "top", from_bottom("load.title_y"))
    bottom = shown(group("load-bottom", {**absolute(left=0, bottom=0, height=0), "width": length(100, "%")}, [band, block]), kind_is(STANDARD))

    # The furniture arrives as the stock cover fades from black.
    tracks.append(track("load-stage", "opacity", held([(0, number(0)), (400, number(1)), (OPEN_MS, number(1))])))
    doc.timeline("loadOpen", OPEN_MS, tracks)
    doc.events["present"] = [{"op": "playTimeline", "timeline": "loadOpen"}]
    stage = group("load-stage", {**FULL, "overflow": keyword("hidden"), "opacity": number(0)}, [bottom, top, first])
    root = group("screen", {**FULL, "font-family": font(FACE_DEFAULT), "font-size": length(18), "color": colour([1, 1, 1, 1])}, [stage])
    return doc.build(root)
