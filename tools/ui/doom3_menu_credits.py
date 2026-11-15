#!/usr/bin/env python3
"""openD3's retained Credits page and the title's Mods panel.

Sections 8.6, 9.5 and 9.7 of docs/dev/ui-visual-design.md.

Credits: two black letterbox bars close in, the logo sits in the strip
between them, and name and role pairs flash in at 30, 140 and 30, 160, hold,
and fall away, one pair every 3000 ms. The page carries no names: the session
reads each line from the stock menu's credits window of the same name
(idSessionLocal::PublishRetainedCredits fills every credits.<window> state).

Mods: the stock Mods page's plate, list and two buttons, shown in the title
document as the session's mods dialog (PublishRetainedMods, SelectRetainedMod;
MOD_ROWS is the session's RETAINED_MOD_ROWS).

build_doom3_menus.py writes the documents.
"""

from __future__ import annotations

from doom3_menu_kit import (
    CANVAS_H, CANVAS_W, FACE_AN, FACE_BANK, FACE_DEFAULT, FULL, NO_POINTER, U, Document, absolute, box, colour, edge_glow,
    font, group, keyword, label, length, nav_button, number, path, picture, radial, rgb, solid, token, track, transform,
    typeface, vector, pinned,
)
from doom3_menu_pages import EDGE, PLACEHOLDER, WHOLE, glow_button, row_parts, scroll_bar, title_and_rule

LOGO = "guis/assets/mainmenu/doom3"

# ----------------------------------------------------------------------- credits

# The stock id Software sequence (CreditsTextAnimation): each pair's window
# number, in the order they show, one every 3000 ms.
PAIRS = (1, 2, 3, 11, 25, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24)
STEP_MS = 3000
LOOP_MS = len(PAIRS) * STEP_MS + 6000   # the last pair falls for 6000 ms after it shows
FALL = [0.6, 0.0, 1.0, 1.0]             # accel(0.6, 0): a pair falls ever faster
SLIDE_IN = [0.0, 0.0, 0.5, 1.0]         # accel(0, 0.5)
NAME = rgb("#99FFFF")                   # text.credit.name
ROLE = rgb("#339999")                   # text.credit.role


def credit_keys(start: int, shown: list, hidden: list) -> list:
    """Keys that hold `hidden` until `start`, then run `shown` (ms from the
    pair's start, value, easing), then hold the last value to the loop's end."""
    keys = [(0, hidden)]
    if start > 1:
        keys.append((start - 1, hidden))
    for at, value, ease in shown:
        keys.append((max(start + at, keys[-1][0] + 1), value, ease))
    if keys[-1][0] < LOOP_MS:
        keys.append((LOOP_MS, keys[-1][1]))
    return keys


def credits_document() -> dict:
    """The Credits page (section 9.7). Section 8.6's choreography for each
    pair: a white bar 300 u wide flashes and shrinks to 100 u in 250 ms while
    the name slides in 10 u over 400 ms; the role repeats the entry 250 ms
    later; from 1000 ms both fall to the bottom over 6000 ms, accel(0.6, 0),
    fading over 5500 ms. The next pair starts at 3000 ms."""
    doc = Document("opend3.credits")
    doc.session("back", "creditsBack")
    doc.events["onBack"] = [{"op": "action", "action": "back"}]
    visible, gone = number(1), number(0)
    rest = transform()
    entered = transform(tx=U * 10)
    fallen = transform(ty=U * 340)
    tracks, pairs = [], []
    bar_one, bar_two = [], []
    for order, window in enumerate(PAIRS):
        start = order * STEP_MS
        for suffix, tint, top, delay in (("", NAME, 0, 0), ("a", ROLE, 20, 250)):
            name = f"CreditsText{window}{suffix}"
            ident = f"credit-{window}{suffix}"
            doc.state[f"credits.{name}"] = {"type": "string", "initial": ""}
            node = label(ident, PLACEHOLDER, {**box(0, top, 400, 21), **typeface(FACE_BANK, 0.35, 21, tint), **NO_POINTER,
                                              "opacity": number(0), "transform": transform()})
            doc.bind(f"{ident}.text", ident, "text", {"state": f"credits.{name}"})
            pairs.append(node)
            tracks.append(track(ident, "opacity", credit_keys(start + delay, [(0, visible, None), (1000 - delay, visible, None),
                                                                          (6500 - delay, gone, None)], gone)))
            tracks.append(track(ident, "transform", credit_keys(start + delay, [(0, entered, SLIDE_IN), (400, rest, None),
                                                                            (1000 - delay, rest, FALL), (7000 - delay, fallen, None)], entered)))
        bar_one.append(start)
        bar_two.append(start + 250)

    def bar(ident: str, top: float, starts: list) -> dict:
        """The entry's white bar: 300 x 12 u, shrinking to 100 u from its leading end."""
        full, small = transform(), transform(tx=-U * 100, sx=1 / 3)
        opacity, shape = [], []
        for start in starts:
            first = 1 if start == 0 else start
            if start > 0:
                opacity.append((start - 1, gone))
                shape.append((start - 1, full))
            opacity += [(first, visible), (start + 250, gone)]
            shape += [(first, full, [0.1, 0.0, 0.2, 1.0]), (start + 250, small)]
        opacity = ([(0, gone)] if opacity[0][0] > 0 else []) + opacity + [(LOOP_MS, gone)]
        shape = ([(0, full)] if shape[0][0] > 0 else []) + shape + [(LOOP_MS, small)]
        tracks.append(track(ident, "opacity", opacity))
        tracks.append(track(ident, "transform", shape))
        return vector(ident, {**box(0, top, 300, 12), **NO_POINTER, "opacity": number(0), "transform": transform()},
                      [path("bar", WHOLE, fill=solid([1, 1, 1, 1]))])

    bars = [bar("credit-bar-name", 10, bar_one), bar("credit-bar-role", 30, bar_two)]
    doc.timeline("creditsRoll", LOOP_MS, tracks, iterations=0)

    # Letterbox bars with slanted steel-blue edges: 200 u from the top, 139 u
    # from the bottom, closing in over 1800 ms.
    edge = token("chrome.bar", 0.6)
    w = {"fraction": 1}

    def beyond(ident: str, top: float) -> dict:
        """Black past a bar's outer edge, moving with the bar: on a tall view
        the letterbox keeps its opening on the centred canvas and the bars
        run on to the view's top and bottom edges (section 3)."""
        return group(ident, {**absolute(left=0, top=top, height=U * 3000), "width": length(100, "%"), "background-color": colour([0, 0, 0, 1]),
                             **NO_POINTER})

    upper = vector("credits-upper", {**absolute(left=0, top=0, height=U * 204), "width": length(100, "%"), **NO_POINTER, "transform": transform()}, [
        path("bar", [(0, 0), (w, 0), (w, U * 200), (0, U * 200)], fill=solid([0, 0, 0, 1])),
        path("edge", [(0, U * 200), ({"fraction": 0.62}, U * 200), ({"fraction": 0.62, "dp": U * 4}, U * 204), (w, U * 204), (w, U * 200),
                      (0, U * 200)], fill=solid(edge))],
        children=[beyond("credits-upper-beyond", top=-U * 3000)])
    lower = vector("credits-lower", {**absolute(left=0, top=U * 337, height=U * 143), "width": length(100, "%"), **NO_POINTER, "transform": transform()}, [
        path("bar", [(0, U * 4), (w, U * 4), (w, U * 143), (0, U * 143)], fill=solid([0, 0, 0, 1])),
        path("edge", [(0, U * 4), ({"fraction": 0.38}, U * 4), ({"fraction": 0.38, "dp": U * 4}, 0), (w, 0), (w, U * 4), (0, U * 4)],
             fill=solid(edge))],
        children=[beyond("credits-lower-beyond", top=U * 143)])
    logo = picture("credits-logo", LOGO, {**box(370, 207, 256, 128), **NO_POINTER, "image-color": colour([1, 1, 1, 1]), "opacity": number(0)})
    heading = label("credits-heading", "#str_02225", {**box(10, 112, 400, 21), **typeface(FACE_BANK, 0.40, 21, token("text.active")), **NO_POINTER,
                                                      "opacity": number(0)})
    roll = group("credits-roll", box(30, 140, 400, 340), [*bars, *pairs])
    doc.timeline("creditsEnter", 2000, [
        track("credits-upper", "transform", [(0, transform(ty=-U * 204), [0.0, 0.0, 0.2, 1.0]), (1800, transform()), (2000, transform())]),
        track("credits-lower", "transform", [(0, transform(ty=U * 143), [0.0, 0.0, 0.2, 1.0]), (2000, transform())]),
        track("credits-logo", "opacity", [(0, number(0)), (600, number(1)), (2000, number(1))]),
        track("credits-heading", "opacity", [(0, number(0)), (500, number(0)), (1000, number(1)), (2000, number(1))]),
    ])
    canvas = group("canvas", {**absolute(top=0, width=CANVAS_W, height=0), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)},
                   [logo, heading, roll])
    # BACK TO MENU runs off the trailing edge at the bottom-trailing corner;
    # the copyright stands at the bottom-leading corner.
    back = nav_button(doc, "credits_back", "#str_02263", absolute(left=U * (480 - 320), right=-U * 38, top=U * 453, height=U * 32),
                      action="back")
    trail_side = group("trail-side", {**absolute(top=0, height=0), "left": length(50, "%"), "width": length(50, "%")}, [back])
    notice = label("credits-copyright", "#str_04851", {**box(7, 452, 450, 28), **typeface(FACE_BANK, 0.20, 12, rgb("#FFFFFF", 0.3)),
                                                        "white-space": keyword("pre-wrap"), **NO_POINTER})
    # BACK TO MENU and the copyright keep to the view's bottom corners.
    stage = group("stage", FULL, [group("stage-middle", {**pinned("middle"), **NO_POINTER}, [upper, lower, canvas]),
                                  group("stage-low", pinned("bottom"), [trail_side, notice])])
    doc.events["onActivate"] = [{"op": "playTimeline", "timeline": "creditsEnter"}, {"op": "playTimeline", "timeline": "creditsRoll"},
                                {"op": "playTimeline", "timeline": "edgeGlow"}]
    root = group("screen", {**FULL, "font-family": font(FACE_DEFAULT), "font-size": length(18), "color": colour([1, 1, 1, 1])},
                 [stage, edge_glow(doc)])
    return doc.build(root)


# -------------------------------------------------------------------------- mods

MOD_ROWS = 32   # RETAINED_MOD_ROWS
MOD_ROW_H = 14.0
MOD_LIST_W = 290.0
MODS_PLATE = [(172, 45), (454, 45), (486, 77), (486, 182), (478, 190), (478, 356), (456, 378), (182, 378), (150, 346), (150, 67)]


def mod_row(doc: Document, index: int) -> dict:
    """A mod's row: its name and its version, AN 0.25. The first Accept
    selects it; Accept on the selected mod loads it."""
    ident = f"mod-{index}"
    for field in ("name", "version"):
        doc.state[f"mods.row{index}.{field}"] = {"type": "string", "initial": ""}
    cell = {"overflow": keyword("hidden"), **NO_POINTER}
    name = label(f"{ident}-name", PLACEHOLDER, {**box(2, 0, 214, MOD_ROW_H), **typeface(FACE_AN, 0.25, MOD_ROW_H, rgb("#FFFFFF", 0.8)), **cell})
    version = label(f"{ident}-version", PLACEHOLDER, {**box(220, 0, MOD_LIST_W - 222, MOD_ROW_H),
                                                       **typeface(FACE_AN, 0.25, MOD_ROW_H, rgb("#FFFFFF", 0.8)), **cell})
    doc.bind(f"{ident}-name.text", f"{ident}-name", "text", {"state": f"mods.row{index}.name"})
    doc.bind(f"{ident}-version.text", f"{ident}-version", "text", {"state": f"mods.row{index}.version"})
    chosen = {"op": "==", "args": [{"state": "mods.selected"}, index]}
    doc.bind(f"{ident}.display", ident, "display", {"op": "select", "args": [{"op": "<", "args": [index, {"state": "mods.count"}]}, "block", "none"]})
    doc.bind(f"{ident}-selected.display", f"{ident}-selected", "display", {"op": "select", "args": [chosen, "block", "none"]})
    doc.events[f"modRow{index}"] = [{"op": "if", "condition": chosen, "then": [{"op": "action", "action": "modsLoad"}],
                                     "else": [{"op": "setState", "values": {"mods.pick": index}}, {"op": "action", "action": "modsSelect"}]}]
    plates, ids = row_parts(doc, ident, (f"{ident}-name", f"{ident}-version"))
    return group(ident, {"position": keyword("relative"), "display": keyword("none"), "width": length(U * MOD_LIST_W), "height": length(U * MOD_ROW_H),
                         "flex-shrink": number(0)}, [*plates, name, version],
                 control={"role": "button", "label": PLACEHOLDER, "event": f"modRow{index}", "states": ids})


def mods_panel(doc: Document) -> dict:
    """The Mods page (section 9.5) as the title's mods dialog: the page plate
    at its stock place with its sheen, MODS over a rule, the list in its well
    and LOAD MOD and CANCEL. LOAD MOD stays disabled until a mod is selected.
    The logo is hidden while the plate is open (section 8.4)."""
    doc.state.update({"modsModal.visible": {"type": "boolean", "initial": False}, "mods.count": {"type": "number", "initial": 0},
                      "mods.selected": {"type": "number", "initial": -1}, "mods.pick": {"type": "number", "initial": -1}})
    for name in ("author", "date", "engine", "directory"):
        doc.state[f"mods.{name}"] = {"type": "string", "initial": ""}
    doc.session("modsSelect")
    doc.session("modsLoad")
    doc.session("soundBack")
    xs, ys = [x for x, _ in MODS_PLATE], [y for _, y in MODS_PLATE]
    left, top = min(xs), min(ys)
    local = [(U * (x - left), U * (y - top)) for x, y in MODS_PLATE]
    sheen = radial((U * 3, U * 3), (U * 173, U * 3), [(0, token("plate.sheen")), (1, token("plate.sheen", 0))])
    plate = vector("mods-plate", {**box(left, top, max(xs) - left, max(ys) - top), **NO_POINTER},
                   [path("body", local, fill=solid(token("plate.page"))), path("sheen", local, fill=sheen)])
    flash = vector("mods-flash", {**box(left, top, max(xs) - left, max(ys) - top), **NO_POINTER, "opacity": number(0)},
                   [path("flash", local, fill=solid([1, 1, 1, 1]))])
    well = vector("mods-well", {**box(5, 40, 310, 240), **NO_POINTER},
                  [path("well", WHOLE, fill=solid(token("well.list"))),
                   path("border", EDGE, stroke={"paint": solid(token("rule.hair")), "widthDp": U, "minimumPixels": 1, "join": "miter", "cap": "butt"})])
    rows = group("mods-rows", {"position": keyword("relative"), "display": keyword("flex"), "flex-direction": keyword("column"),
                               "width": length(U * MOD_LIST_W)}, [mod_row(doc, index) for index in range(MOD_ROWS)])
    viewport = group("mods-list", {**box(7, 44, MOD_LIST_W, 232), "overflow": keyword("auto")}, [rows])
    bar = scroll_bar(doc, "mods_scroll", "mods-list", box(298, 42, 16, 236), "#str_04098")
    load = glow_button(doc, "mods_load", "#str_04099", 74, 292, action="modsLoad", hint="#str_04108")
    cancel = glow_button(doc, "mods_cancel", "#str_04216", 184, 292, 69, event="modsModalHide")
    doc.bind("mods_load.enabled", "mods_load", "enabled", {"op": ">=", "args": [{"state": "mods.selected"}, 0]})
    content = group("mods-content", box(153, 48, 340, 330), [*title_and_rule("mods", "#str_04098", 310), well, viewport, bar, load, cancel])
    canvas = group("mods-canvas", {**absolute(top=0, width=CANVAS_W, height=0), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)},
                   [plate, flash, content])
    stage = group("mods-stage", {**absolute(left=0), "width": length(100, "%"), "height": length(CANVAS_H), "top": length(50, "%"),
                                 "margin-top": length(-CANVAS_H / 2)}, [canvas])
    node = group("modsModal", {**FULL, "display": keyword("none")}, [stage], modal={"initialFocus": "mods_cancel", "back": "modsModalHide"})
    doc.bind("modsModal.display", "modsModal", "display", {"op": "select", "args": [{"state": "modsModal.visible"}, "block", "none"]})
    doc.timeline("modsEnter", 400, [track("mods-flash", "opacity", [(0, number(0.4)), (50, number(0.25)), (350, number(0)), (400, number(0))]),
                                    track("logo", "opacity", [(0, number(1)), (400, number(0))])])
    doc.timeline("modsLeave", 400, [track("logo", "opacity", [(0, number(0)), (400, number(1))])])
    doc.events["modsModalShow"] = [{"op": "setState", "values": {"modsModal.visible": True}}, {"op": "playTimeline", "timeline": "modsEnter"}]
    doc.events["modsModalHide"] = [{"op": "setState", "values": {"modsModal.visible": False}}, {"op": "action", "action": "soundBack"},
                                   {"op": "playTimeline", "timeline": "modsLeave"}]
    return node
