#!/usr/bin/env python3
"""openD3's retained Load Game and Save Game pages.

Sections 6.5 to 6.9 and 9.5 of docs/dev/ui-visual-design.md: a page sits on a
slate plate with a bridge to the nav button that opened it and one or two
flair strokes; its content is a title over a rule, a list in a black well
with a plain scroll bar, a level shot, and small glow buttons.

The session presents a page over the home that handed off to it and fills it
through page state (idSessionLocal::PublishRetainedLoadPage,
PublishRetainedSavePage); the page answers with the session's own verbs
(HandleRetainedLoadRequest, HandleRetainedSaveRequest). ROWS is the session's
RETAINED_LOAD_ROWS.

build_doom3_menus.py writes the documents.
"""

from __future__ import annotations

from doom3_menu_kit import (
    CANVAS_H, CANVAS_W, DECEL, FACE_AN, FACE_BANK, FACE_DEFAULT, FULL, NO_POINTER, U, Document, absolute, box, colour,
    control, dialog, down, edge_glow, far, font, group, hairline, item_outline, keyword, label, length, linear,
    nav_button, number, outset, outset_box, path, picture, radial, rgb, solid, stroke, token, track, transform,
    typeface, vector,
)

ROWS = 64           # RETAINED_LOAD_ROWS: the saves the list holds at a time
ROW_H = 14.5         # u: the stock list shows 16 rows in 232 u
LIST_W = 390.0       # u: the list beside its 16 u scroll gutter
PLACEHOLDER = "#str_04339"   # OK: the session supplies the text

STR = {
    "load": "#str_02187", "load.button": "#str_02188", "load.hint": "#str_02189", "load.close": "#str_02212",
    "delete": "#str_02190", "delete.hint": "#str_02191", "delete.title": "#str_02313", "delete.body": "#str_02314",
    "delete.yes": "#str_02315", "delete.yes.hint": "#str_02316",
    "save": "#str_02179", "save.button": "#str_02185", "save.hint": "#str_02186", "save.close": "#str_02210",
    "overwrite.title": "#str_02306", "overwrite.body": "#str_02307", "overwrite.hint": "#str_02309",
    "name": "#str_02181", "level": "#str_41583", "yes": "#str_02308", "no": "#str_04144", "ok": "#str_04339",
    "empty": "#str_231100", "empty.text": "#str_231101", "newer": "#str_231106", "older": "#str_231107",
    "name.field": "#str_231109", "notice.title": "#str_02179",
}

WHOLE = [(0, 0), ({"fraction": 1}, 0), ({"fraction": 1}, {"fraction": 1}), (0, {"fraction": 1})]
EDGE = [(0.75, 0.75), ({"fraction": 1, "dp": -0.75}, 0.75), ({"fraction": 1, "dp": -0.75}, {"fraction": 1, "dp": -0.75}),
        (0.75, {"fraction": 1, "dp": -0.75})]


def u_points(points: list) -> list:
    """Canvas points in u as dp."""
    return [(U * x, U * y) for x, y in points]


# ------------------------------------------------------------------- the plate

def page_shell(doc: Document, plate: list, bridge: list, flairs: list) -> list:
    """Section 6.9's page plate on the 4:3 canvas: the body in plate.page with
    no outline, its corner sheen, the bridge toward the nav button that opened
    the page and the flair strokes, each its own polygon in its own colour.

    Section 8.2: every piece is born white (flash.build) and settles in 50 ms
    and then 300 ms: the bridge at 0, the plate at 50 while it unfolds for 400
    ms, accel(0.2, 0.8), the flair at 150. Content switches on at 400 ms."""
    xs, ys = [x for x, _ in plate], [y for _, y in plate]
    left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)
    place = box(left, top, right - left, bottom - top)
    local = [(U * (x - left), U * (y - top)) for x, y in plate]
    sheen = radial((U * 3, U * 3), (U * 173, U * 3), [(0, token("plate.sheen")), (1, token("plate.sheen", 0))])
    body = vector("plate-body", {**place, **NO_POINTER, "transform": transform(), "opacity": number(1)},
                  [path("body", local, fill=solid(token("plate.page"))), path("sheen", local, fill=sheen)])
    body_flash = vector("plate-flash", {**place, **NO_POINTER, "transform": transform(), "opacity": number(0)},
                        [path("flash", local, fill=solid([1, 1, 1, 1]))])
    whole = {**absolute(left=0, top=0, width=CANVAS_W, height=CANVAS_H), **NO_POINTER}
    bridge_node = vector("plate-bridge", {**whole, "opacity": number(1)}, [path("bridge", u_points(bridge), fill=solid(token("plate.bridge")))])
    bridge_flash = vector("plate-bridge-flash", {**whole, "opacity": number(0)}, [path("bridge", u_points(bridge), fill=solid([1, 1, 1, 1]))])
    flair_node = vector("plate-flair", {**whole, "opacity": number(1)},
                        [path(f"flair{index}", u_points(points), fill=solid(token("plate.flair"))) for index, points in enumerate(flairs)])
    flair_flash = vector("plate-flair-flash", {**whole, "opacity": number(0)},
                         [path(f"flair{index}", u_points(points), fill=solid([1, 1, 1, 1])) for index, points in enumerate(flairs)])
    small = transform(sx=0.62, sy=0.46)

    def born(node: str, at: int) -> list:
        """A piece's white flash: 40 % at `at`, most of the way down by 50 ms, gone by 350."""
        keys = [(0, number(0))] + ([(at - 1, number(0))] if at > 1 else []) + [(max(at, 1), number(0.4)), (at + 50, number(0.25)),
                                                                              (at + 350, number(0)), (600, number(0))]
        return [track(node, "opacity", keys)]

    def shown(node: str, at: int) -> list:
        keys = [(0, number(0))] + ([(at - 1, number(0))] if at > 1 else []) + [(max(at, 1), number(1)), (600, number(1))]
        return [track(node, "opacity", keys)]

    doc.state["page.shown"] = {"type": "boolean", "initial": False}
    # A plate with no flair (Create Server) has no flair pieces.
    doc.timeline("pageEnter", 600, [
        *shown("plate-bridge", 0), *born("plate-bridge-flash", 0),
        *shown("plate-body", 50), *born("plate-flash", 50),
        track("plate-body", "transform", [(0, small), (50, small, DECEL), (450, transform()), (600, transform())]),
        track("plate-flash", "transform", [(0, small), (50, small, DECEL), (450, transform()), (600, transform())]),
        *([*shown("plate-flair", 150), *born("plate-flair-flash", 150)] if flairs else []),
    ])
    doc.timeline("pageContent", 400, [track("page-content", "opacity", [(0, number(1)), (400, number(1))])], complete="pageShown")
    doc.events["pageShown"] = [{"op": "setState", "values": {"page.shown": True}}]
    return [bridge_node, bridge_flash, body, body_flash, *([flair_node, flair_flash] if flairs else [])]


# ------------------------------------------------------------------ components

def glow_button(doc: Document, ident: str, key: str, x: float, y: float, width: float = 99.0, *, action: str | None = None,
                event: str | None = None, hint: str | None = None) -> dict:
    """Section 6.5's small glow button: hairlines 16 u apart with a square
    leading end and a 5 u chamfer on the top-trailing corner, filled with the
    frame's colour at 53 % beside the lines and 40 % across the middle. No
    separate plate. Section 7.1: the label turns white and the frame flashes
    and settles to chrome.glow.hover in 250 ms; release takes 400 ms; a press
    flashes the frame white; disabled is dim, not absent."""
    shape = item_outline(width, 16)
    glow = token("chrome.glow")
    fill = vector(f"{ident}-fill", {**FULL, **NO_POINTER, "opacity": number(1)}, [path("fill", shape, fill=linear(
        (0, 0), (0, U * 16), [(0, glow[:3] + [0.265]), (0.5, glow[:3] + [0.2]), (1, glow[:3] + [0.265])]))])
    line = vector(f"{ident}-line", {**outset_box(), **NO_POINTER, "opacity": number(0.5)}, hairline("line", outset(shape), "#80B2CC"))
    hot = vector(f"{ident}-hot", {**outset_box(), **NO_POINTER, "opacity": number(0)}, hairline("line", outset(shape), "#99CCE6"))
    flash = vector(f"{ident}-flash", {**outset_box(), **NO_POINTER, "opacity": number(0)}, hairline("line", outset(shape), "#FFFFFF"))
    text_node = label(f"{ident}-label", key, {**FULL, **typeface(FACE_DEFAULT, 0.25, 16, token("text.action"), "center"), **NO_POINTER})
    ids = doc.states(ident, [
        (f"{ident}-fill", "opacity", {"default": number(1), "hover": number(1), "disabled": number(0.5)}, 250, 400),
        (f"{ident}-line", "opacity", {"default": number(0.5), "hover": number(0), "disabled": number(0.25)}, 250, 400),
        (f"{ident}-hot", "opacity", {"default": number(0), "hover": number(1), "disabled": number(0)}, 250, 400),
        (f"{ident}-flash", "opacity", {"default": number(0), "hover": number(0), "pressed": number(1)}, 250, 400, number(0.8)),
        (f"{ident}-label", "color", {"default": colour(token("text.action")), "hover": colour(token("text.active")),
                                     "disabled": colour(token("text.dim"))}, 250, 250),
    ])
    return group(ident, box(x, y, width, 16), [fill, line, hot, flash, text_node],
                 control=control(doc, key, ids, action=action, event=event, hint=hint))


def scroll_bar(doc: Document, ident: str, viewport: str, place: dict, key: str) -> dict:
    """Section 6.7's scroll bar, the plainest object on the screen: a flat 16
    u gutter in white at 17 % and a square grey-teal thumb inset 2 u, with no
    chamfer and no glow. The thumb lightens under the pointer or the focus."""
    trough = vector(f"{ident}-trough", {**FULL, **NO_POINTER}, [path("gutter", WHOLE, fill=solid([1, 1, 1, 0.17]))])
    inset = [(U * 2, U * 2), (far(2), U * 2), (far(2), down(2)), (U * 2, down(2))]
    base = vector(f"{ident}-thumb-base", {**FULL, **NO_POINTER, "opacity": number(1)}, [path("thumb", inset, fill=solid(rgb("#6E9499")))])
    active = vector(f"{ident}-thumb-active", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("thumb", inset, fill=solid(rgb("#B2D8D8")))])
    thumb = group(f"{ident}-thumb", absolute(left=0, top=0, width=U * 16, height=U * 16), [base, active])
    track_node = group(f"{ident}-track", {"position": keyword("relative"), "display": keyword("block"), "width": length(U * 16),
                                          "height": length(100, "%")}, [trough, thumb])
    ids = doc.states(ident, [
        (f"{ident}-thumb-base", "opacity", {"default": number(1), "hover": number(0), "disabled": number(0.4)}, 100, 200),
        (f"{ident}-thumb-active", "opacity", {"default": number(0), "hover": number(1), "disabled": number(0)}, 100, 200),
    ])
    return group(ident, place, [track_node],
                 control={"role": "scrollbar", "label": key, "viewport": viewport, "orientation": "vertical",
                          "lineStep": round(U * ROW_H, 3), "minimumThumb": U * 16,
                          "parts": {"track": f"{ident}-track", "thumb": f"{ident}-thumb"}, "states": ids})


def row_parts(doc: Document, ident: str, texts: tuple) -> tuple:
    """A list row's plates and feedback (sections 6.7 and 7.4): no plate at
    rest; the row's text turns white under the pointer or the focus over a
    faint bar; the selected row lies on a filled bar in well.select."""
    selected = vector(f"{ident}-selected", {**FULL, **NO_POINTER, "display": keyword("none")},
                      [path("bar", WHOLE, fill=solid(token("well.select")))])
    hot = vector(f"{ident}-hot", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("bar", WHOLE, fill=solid(token("well.select", 0.25)))])
    rest, lit = colour(rgb("#FFFFFF", 0.8)), colour(token("text.active"))
    ids = doc.states(ident, [
        (f"{ident}-hot", "opacity", {"default": number(0), "hover": number(1)}, 50, 200),
        *[(node, "color", {"default": rest, "hover": lit, "disabled": colour(token("text.dim"))}, 50, 200) for node in texts],
    ])
    return [selected, hot], ids


def save_row(doc: Document, index: int, prefix: str, chosen: list) -> dict:
    """One of the list's rows: the save's name at the stock list's first tab
    stop (2 u) and its level at the second (230 u), AN 0.25. Its first Accept
    selects the save; Accept on the selected save runs `chosen`."""
    ident, key = f"row-{index}", f"{prefix}.row{index}"
    for field in ("context", "name", "location"):
        doc.state[f"{key}.{field}"] = {"type": "string", "initial": ""}
    cell = {"overflow": keyword("hidden"), **NO_POINTER}
    name = label(f"{ident}-name", PLACEHOLDER, {**box(2, 0, 224, ROW_H), **typeface(FACE_AN, 0.25, ROW_H, rgb("#FFFFFF", 0.8)), **cell})
    location = label(f"{ident}-location", PLACEHOLDER, {**box(230, 0, LIST_W - 232, ROW_H),
                                                         **typeface(FACE_AN, 0.25, ROW_H, rgb("#FFFFFF", 0.8)), **cell})
    doc.bind(f"{ident}-name.text", f"{ident}-name", "text", {"state": f"{key}.name"})
    doc.bind(f"{ident}-location.text", f"{ident}-location", "text", {"state": f"{key}.location"})
    save = {"op": "+", "args": [{"state": f"{prefix}.first"}, index]}
    is_selected = {"op": "==", "args": [{"state": f"{prefix}.selected"}, save]}
    doc.bind(f"{ident}.display", ident, "display", {"op": "select", "args": [{"op": "<", "args": [save, {"state": f"{prefix}.count"}]}, "block", "none"]})
    doc.bind(f"{ident}-selected.display", f"{ident}-selected", "display", {"op": "select", "args": [is_selected, "block", "none"]})
    event = f"{prefix}Row{index}"
    doc.events[event] = [{"op": "if", "condition": is_selected, "then": chosen,
                          "else": [{"op": "setState", "values": {f"{prefix}.pick": index}}, {"op": "action", "action": "select"}]}]
    plates, ids = row_parts(doc, ident, (f"{ident}-name", f"{ident}-location"))
    return group(ident, {"position": keyword("relative"), "display": keyword("none"), "width": length(U * LIST_W), "height": length(U * ROW_H),
                         "flex-shrink": number(0)}, [*plates, name, location],
                 control={"role": "button", "label": PLACEHOLDER, "event": event, "states": ids, "context": {"state": f"{key}.context"}})


def pager_row(doc: Document, ident: str, key: str, action: str, shown: dict) -> dict:
    """A row that pages the list to the newer or the older saves, when there
    are more than the list holds."""
    text_node = label(f"{ident}-label", key, {**box(2, 0, LIST_W - 4, ROW_H), **typeface(FACE_BANK, 0.25, ROW_H, token("text.action")),
                                              **NO_POINTER})
    hot = vector(f"{ident}-hot", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("bar", WHOLE, fill=solid(token("well.select", 0.25)))])
    ids = doc.states(ident, [
        (f"{ident}-hot", "opacity", {"default": number(0), "hover": number(1)}, 50, 200),
        (f"{ident}-label", "color", {"default": colour(token("text.action")), "hover": colour(token("text.active"))}, 50, 200),
    ])
    doc.bind(f"{ident}.display", ident, "display", {"op": "select", "args": [shown, "block", "none"]})
    return group(ident, {"position": keyword("relative"), "display": keyword("none"), "width": length(U * LIST_W), "height": length(U * ROW_H),
                         "flex-shrink": number(0)}, [hot, text_node], control={"role": "button", "label": key, "action": action, "states": ids})


def row_value(prefix: str, field: str, index: dict, low: int = 0, high: int = ROWS - 1):
    """The `field` of the row `index` names: a balanced tree of selects, six
    deep, where one chain of 64 would pass the expression depth limit."""
    if low == high:
        return {"state": f"{prefix}.row{low}.{field}"}
    middle = (low + high) // 2
    return {"op": "select", "args": [{"op": "<=", "args": [index, middle]}, row_value(prefix, field, index, low, middle),
                                     row_value(prefix, field, index, middle + 1, high)]}


def save_list(doc: Document, prefix: str, chosen: list, title_key: str) -> list:
    """The list in its well (sections 6.6 and 9.5): column captions in
    text.value over a black well at 60 % with a 1 u black border, the saves
    newest first in a scrolling viewport, the scroll bar in the well's last
    16 u, and a line for an empty list. Content coordinates."""
    doc.state.update({
        f"{prefix}.pick": {"type": "number", "initial": -1}, f"{prefix}.first": {"type": "number", "initial": 0},
        f"{prefix}.count": {"type": "number", "initial": 0}, f"{prefix}.selected": {"type": "number", "initial": -1},
        "browser.generation": {"type": "number", "initial": 0}, "browser.sort": {"type": "number", "initial": 0},
        "browser.filter": {"type": "number", "initial": 0},
    })
    captions = [label(f"{prefix}-caption-name", STR["name"], {**box(7, 36, 195, 12), **typeface(FACE_BANK, 0.25, 12, token("text.value")), **NO_POINTER}),
                label(f"{prefix}-caption-level", STR["level"], {**box(237, 36, 170, 12), **typeface(FACE_BANK, 0.25, 12, token("text.value")), **NO_POINTER})]
    well = vector(f"{prefix}-well", {**box(5, 50, 410, 240), **NO_POINTER},
                  [path("well", WHOLE, fill=solid(token("well.list"))), path("border", EDGE, stroke=stroke(solid(token("rule.hair")), U, minimum=1))])
    first, count = {"state": f"{prefix}.first"}, {"state": f"{prefix}.count"}
    rows = [pager_row(doc, "row-newer", STR["newer"], "newer", {"op": ">", "args": [first, 0]}),
            *[save_row(doc, index, prefix, chosen) for index in range(ROWS)],
            pager_row(doc, "row-older", STR["older"], "older", {"op": "<", "args": [{"op": "+", "args": [first, ROWS]}, count]})]
    column = group(f"{prefix}-rows", {"position": keyword("relative"), "display": keyword("flex"), "flex-direction": keyword("column"),
                                      "width": length(U * LIST_W)}, rows)
    viewport = group(f"{prefix}-list", {**box(7, 54, LIST_W, 232), "overflow": keyword("auto")}, [column])
    bar = scroll_bar(doc, f"{prefix}_scroll", f"{prefix}-list", box(398, 52, 16, 236), title_key)
    empty = group(f"{prefix}-empty", {**box(7, 120, LIST_W, 80), "display": keyword("none"), **NO_POINTER}, [
        label(f"{prefix}-empty-heading", STR["empty"], {**box(0, 0, LIST_W, 16), **typeface(FACE_DEFAULT, 0.25, 16, token("text.dim"), "center")}),
        label(f"{prefix}-empty-text", STR["empty.text"], {**box(40, 22, LIST_W - 80, 48), **typeface(FACE_BANK, 0.25, 15, token("text.dim"), "center"),
                                                           "white-space": keyword("normal")})])
    doc.bind(f"{prefix}-empty.display", f"{prefix}-empty", "display", {"op": "select", "args": [{"op": "==", "args": [count, 0]}, "block", "none"]})
    # The session's cues after it pages or refreshes the list.
    doc.events["pagedOlder"] = [{"op": "focus", "control": "row-0"}]
    doc.events["pagedNewer"] = [{"op": "focus", "control": f"row-{ROWS - 1}"}]
    for row in range(ROWS):
        doc.events[f"browserFocus{row}"] = [{"op": "focus", "control": f"row-{row}"}]
    return [*captions, well, viewport, bar, empty]


def name_field(doc: Document, ident: str, place: dict, state: str, action: str, limit: int, *, boxed: bool = True,
               tint: list | None = None, key: str | None = None, integer: tuple | None = None) -> dict:
    """Section 6.7's edit: bare text on a well.list box with a 1 u black
    border (the stock save-name field), Bank 0.25. Focus lights a hairline
    around the box. Enter commits the text through `action`.

    Without `boxed` the field draws no box of its own: it sits on an option
    row's plate, as the stock Create Server edits do. `tint` is the text's
    colour and `key` the field's name for assistive output. With `integer`,
    (minimum, maximum), the field takes a whole number in that range and
    hands `action` the number; a value outside it is not entered."""
    parts = {part: f"{ident}-{part}" for part in ("viewport", "text", "selection", "caret", "composition", "validation")}
    height = 16.0
    tint = tint or token("text.active")
    field = vector(f"{ident}-field", {**FULL, **NO_POINTER, "opacity": number(1 if boxed else 0)},
                   [path("well", WHOLE, fill=solid(token("well.list"))), path("border", EDGE, stroke=stroke(solid(token("rule.hair")), U, minimum=1))])
    focus = vector(f"{ident}-focus", {**outset_box(), **NO_POINTER, "opacity": number(0)},
                   hairline("line", outset([(0, 0), ({"fraction": 1}, 0), ({"fraction": 1}, {"fraction": 1}), (0, {"fraction": 1})]), "#8CA6BF"))

    def ink(name: str, paint: list, width: float, tall: float) -> dict:
        return vector(name, {**absolute(left=0, top=0, width=width, height=tall), "display": keyword("block"), "opacity": number(1), **NO_POINTER},
                      [path("ink", WHOLE, fill=solid(paint))])

    text_node = label(parts["text"], PLACEHOLDER, {**absolute(left=0, top=0, width=4096, height=U * height),
                                                    **typeface(FACE_BANK, 0.25, height, tint), "white-space": keyword("pre")})
    viewport = group(parts["viewport"], {**absolute(left=U * 3, top=0, height=U * height), "right": length(U * 3), "display": keyword("block"),
                                         "overflow": keyword("hidden")},
                     [ink(parts["selection"], token("well.select"), 0, U * height), text_node,
                      ink(parts["caret"], [1, 1, 1, 1], 1.5, U * height), ink(parts["composition"], token("text.action"), 0, 1.5)])
    validation = label(parts["validation"], PLACEHOLDER, {**absolute(left=0, top=U * (height + 1), height=U * 12), "width": length(100, "%"),
                                                           **typeface(FACE_BANK, 0.25, 12, token("text.dim")), "display": keyword("none")})
    ids = doc.states(ident, [(f"{ident}-focus", "opacity", {"default": number(0), "hover": number(1)}, 250, 400)])
    spec = {"label": key or STR["name.field"], "action": action, "value": {"state": state}, "maxBytes": limit, "parts": parts, "states": ids}
    if integer is not None:
        # The field has no room under it for a message: a refused value just stays a draft.
        validation["properties"].update({"width": length(0), "height": length(0), "overflow": keyword("hidden")})
        spec.update({"role": "number", "minimum": integer[0], "maximum": integer[1], "integer": True, "exponent": False})
    else:
        spec.update({"role": "text", "allowEmpty": True})
    return group(ident, place, [field, focus, viewport, validation], control=spec)


# ------------------------------------------------------------------- documents

SECOND_PLACE = box(213, 410, 224, 32)                                                    # LOAD GAME, on the canvas
FIRST_PLACE = absolute(left=U * 27, right=U * (320 - 241), top=U * 410, height=U * 32)   # SAVE GAME, to the leading edge

# Stock open-state plates (AnimMainToLG, AnimMainToSG), in canvas u. Corner
# cuts follow section 6.9: 22 u top-leading and bottom-trailing, 32 u
# top-trailing and bottom-leading. The load plate steps in 8 u beside its
# vertical flair.
LOAD_PLATE = [(72, 45), (554, 45), (586, 77), (586, 182), (578, 190), (578, 356), (556, 378), (82, 378), (50, 346), (50, 67)]
LOAD_BRIDGE = [(185, 380), (546, 380), (530, 396), (426, 396), (410, 412), (217, 412)]
LOAD_FLAIRS = [[(580, 191), (587, 184), (587, 265), (580, 272)], [(121, 380), (181, 380), (181, 387), (128, 387)]]
SAVE_PLATE = [(59, 45), (456, 45), (488, 77), (488, 356), (466, 378), (69, 378), (37, 346), (37, 67)]
SAVE_BRIDGE = [(53, 380), (300, 380), (284, 396), (215, 396), (199, 412), (85, 412)]
SAVE_FLAIRS = [[(490, 259), (497, 252), (497, 333), (490, 340)], [(328, 380), (450, 380), (457, 387), (335, 387)]]


def page_frame(doc: Document, shell: list, content: list, owner: dict, modals: list, on_canvas: bool,
               content_box: tuple = (53, 48, 540, 330)) -> dict:
    """A page over the home that handed off to it: the plate and the content
    on the centred 4:3 canvas (section 3), the owning nav button drawn again
    in its home place as the way back, the hint line, the edge glow and the
    page's dialogs. The home hides its own copy of that button and its hint."""
    inner = group("page-content", {**box(*content_box), "display": keyword("none"), "opacity": number(1)}, content)
    doc.bind("page-content.display", "page-content", "display", {"op": "select", "args": [{"state": "page.shown"}, "block", "none"]})
    canvas = group("canvas", {**absolute(top=0, width=CANVAS_W, height=0), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)},
                   [*shell, inner, *([owner] if on_canvas else [])])
    sides = [] if on_canvas else [group("lead-side", {**absolute(left=0, top=0, height=0), "width": length(50, "%")}, [owner])]
    stage = group("stage", {**absolute(left=0), "width": length(100, "%"), "height": length(CANVAS_H), "top": length(50, "%"),
                            "margin-top": length(-CANVAS_H / 2)}, [canvas, *sides, doc.hint_line()])
    doc.events["onActivate"] = [{"op": "setState", "values": {"page.shown": False}}, {"op": "playTimeline", "timeline": "pageEnter"},
                                {"op": "playTimeline", "timeline": "pageContent"}, {"op": "playTimeline", "timeline": "edgeGlow"}]
    root = group("screen", {**FULL, "font-family": font(FACE_DEFAULT), "font-size": length(18), "color": colour([1, 1, 1, 1])},
                 [stage, edge_glow(doc), *modals])
    return doc.build(root)


def title_and_rule(prefix: str, key: str, rule_w: float) -> list:
    return [label(f"{prefix}-title", key, {**box(20, 5, 320, 20), **typeface(FACE_DEFAULT, 0.32, 20, token("text.active")), **NO_POINTER}),
            vector(f"{prefix}-rule", {**box(5, 23, rule_w, 2), **NO_POINTER}, [path("rule", WHOLE, fill=solid(token("rule.title")))])]


def load_game_document() -> dict:
    """The Load Game page (section 9.5): the list, the selected save's level
    shot in its frame with its date and time in a group box below, and LOAD
    GAME and DELETE, which stay disabled until a save is selected. DELETE
    asks first. A save that cannot load says why over its picture."""
    doc = Document("opend3.loadgame")
    for name in ("context", "shot", "date", "time", "skill", "played", "error"):
        doc.state[f"load.{name}"] = {"type": "string", "initial": ""}
    doc.state["load.ingame"] = {"type": "boolean", "initial": False}
    for action, command in (("back", "loadBack"), ("newer", "loadNewer"), ("older", "loadOlder")):
        doc.session(action, command)
    generation = {"state": "browser.generation"}
    picked = {"op": "+", "args": [{"state": "load.first"}, {"state": "load.pick"}]}
    for action, command, index in (("select", "loadSelect", picked), ("load", "loadSave", {"state": "load.selected"}),
                                   ("delete", "loadDelete", {"state": "load.selected"})):
        doc.actions[action] = {"operation": "session.menu", "arguments": {"command": command, "index": index, "generation": generation}}
    doc.session("soundForward")
    doc.session("soundBack")
    chosen = {"op": ">=", "args": [{"state": "load.selected"}, 0]}
    content = [*title_and_rule("load", STR["load"], 510), *save_list(doc, "load", [{"op": "action", "action": "load"}], STR["load"])]

    # The selected save: its picture in a rule.shot frame, then a group box
    # (rule.group, its trailing corners chamfered) with the date in white,
    # the time, the difficulty and the play time.
    shot = picture("load-shot", "", {**box(422, 50, 105, 79), **NO_POINTER}, fit="cover")
    doc.bind("load-shot.image", "load-shot", "image", {"state": "load.shot"})
    frame = vector("load-shot-frame", {**box(422, 50, 105, 79), **NO_POINTER}, [path("frame", EDGE, stroke=stroke(solid(token("rule.shot")), U, minimum=1))])
    error = group("load-error", {**box(423, 96, 103, 32), "display": keyword("none"), "background-color": colour([0, 0, 0, 0.8]), **NO_POINTER}, [
        label("load-error-text", PLACEHOLDER, {**box(3, 1, 97, 30), **typeface(FACE_BANK, 0.20, 10, token("text.data")), "white-space": keyword("normal"),
                                               "overflow": keyword("hidden")})])
    doc.bind("load-error.display", "load-error", "display", {"op": "select", "args": [{"op": "!=", "args": [{"state": "load.error"}, ""]}, "block", "none"]})
    doc.bind("load-error-text.text", "load-error-text", "text", {"state": "load.error"})
    details_box = vector("load-details-box", {**box(422, 129, 105, 115), **NO_POINTER}, [
        path("box", [(0, 0), (U * 96, 0), (U * 105, U * 9), (U * 105, U * 106), (U * 96, U * 115), (0, U * 115)], fill=solid(token("rule.group")))])
    details = []
    for index, (name, tint, scale) in enumerate((("date", token("text.active"), 0.25), ("time", token("text.value"), 0.25),
                                                 ("skill", token("text.value"), 0.24), ("played", token("text.value"), 0.24))):
        node = label(f"load-{name}", PLACEHOLDER, {**box(425, 138 + 15 * index, 100, 12), **typeface(FACE_BANK, scale, 12, tint), "overflow": keyword("hidden"),
                                                   **NO_POINTER})
        doc.bind(f"load-{name}.text", f"load-{name}", "text", {"state": f"load.{name}"})
        details.append(node)
    load_button = glow_button(doc, "load_go", STR["load.button"], 422, 252, action="load", hint=STR["load.hint"])
    delete_button = glow_button(doc, "load_delete", STR["delete"], 422, 274, event="deleteAsk", hint=STR["delete.hint"])
    doc.bind("load_go.enabled", "load_go", "enabled", chosen)
    doc.bind("load_delete.enabled", "load_delete", "enabled", chosen)
    content += [shot, frame, error, details_box, *details, load_button, delete_button]

    # DELETE asks first (section 7.4), naming the save in text.data.
    selected_row = {"op": "clamp", "args": [{"op": "-", "args": [{"state": "load.selected"}, {"state": "load.first"}]}, 0, ROWS - 1]}
    target = label("delete-target", PLACEHOLDER, {**box(30, 72, 300, 15), **typeface(FACE_AN, 0.25, 15, token("text.data")), "overflow": keyword("hidden")})
    doc.bind("delete-target.text", "delete-target", "text", row_value("load", "name", selected_row))
    question = label("deleteModal-body", STR["delete.body"], {**box(30, 40, 300, 30), **typeface(FACE_BANK, 0.25, 15, token("text.active")),
                                                              "white-space": keyword("normal")})
    delete_modal = dialog(doc, "deleteModal", STR["delete.title"], STR["delete.body"], [
        ("delete_yes", STR["delete.yes"], 61, None, "deleteConfirm", STR["delete.yes.hint"]),
        ("delete_no", STR["no"], 210, None, "deleteCancel", None)], initial="delete_no", back="deleteCancel", contents=[question, target])
    doc.events["deleteAsk"] = [{"op": "action", "action": "soundForward"}, {"op": "call", "event": "deleteModalShow"}]
    doc.events["deleteCancel"] = [{"op": "action", "action": "soundBack"}, {"op": "call", "event": "deleteModalHide"}]
    doc.events["deleteConfirm"] = [{"op": "action", "action": "delete"}, {"op": "call", "event": "deleteModalHide"}]
    doc.events["onBack"] = [{"op": "action", "action": "back"}]

    owner = nav_button(doc, "page_close", STR["load"], SECOND_PLACE, action="back", hint=STR["load.close"])
    return page_frame(doc, page_shell(doc, LOAD_PLATE, LOAD_BRIDGE, LOAD_FLAIRS), content, owner, [delete_modal], on_canvas=True)


def save_game_document() -> dict:
    """The Save Game page (section 9.5): the list, the name field in a
    well.list box and SAVE GAME beside it. A row's first Accept puts its name
    in the field; SAVE GAME, or Enter in the field, saves under the name
    there. The session asks before saving over a save and says why when it
    cannot save."""
    doc = Document("opend3.savegame")
    doc.state.update({"save.name": {"type": "string", "initial": ""}, "save.target": {"type": "string", "initial": ""},
                      "save.notice": {"type": "string", "initial": ""},
                      # The adapter keeps this: the name field holds text not yet entered.
                      "ui.numberDraftsPending": {"type": "boolean", "initial": False}})
    for action, command in (("back", "saveBack"), ("save", "saveSave"), ("overwrite", "saveOverwrite"), ("newer", "saveNewer"),
                            ("older", "saveOlder")):
        doc.session(action, command)
    doc.actions["select"] = {"operation": "session.menu", "arguments": {
        "command": "saveSelect", "index": {"op": "+", "args": [{"state": "save.first"}, {"state": "save.pick"}]},
        "generation": {"state": "browser.generation"}}}
    doc.session("soundBack")
    # Entering the name writes it into save.name, then saves under it. A name
    # typed but not entered takes the focus back, where Enter saves under it.
    doc.actions["rename"] = {"input": "string", "operation": "ui.state.set",
                             "arguments": {"key": "save.name", "value": {"input": "value"}, "event": "nameEntered"}}
    doc.actions["editName"] = {"operation": "ui.numberDrafts.focus", "arguments": {}}
    doc.events["nameEntered"] = [{"op": "action", "action": "save"}]
    doc.events["saveRequested"] = [{"op": "if", "condition": {"state": "ui.numberDraftsPending"},
                                    "then": [{"op": "action", "action": "editName"}], "else": [{"op": "action", "action": "save"}]}]
    doc.events["onBack"] = [{"op": "action", "action": "back"}]

    content = [*title_and_rule("save", STR["save"], 410), *save_list(doc, "save", [{"op": "call", "event": "saveRequested"}], STR["save"])]
    field = name_field(doc, "save_name", box(8, 297, 295, 16), "save.name", "rename", 32)
    save_button = glow_button(doc, "save_go", STR["save.button"], 311, 297, event="saveRequested", hint=STR["save.hint"])
    content += [field, save_button]

    # Saving over a save asks first, naming it; a refusal says why.
    target = label("overwrite-target", PLACEHOLDER, {**box(30, 72, 300, 15), **typeface(FACE_AN, 0.25, 15, token("text.data")), "overflow": keyword("hidden")})
    doc.bind("overwrite-target.text", "overwrite-target", "text", {"state": "save.target"})
    question = label("overwriteModal-body", STR["overwrite.body"], {**box(30, 40, 300, 30), **typeface(FACE_BANK, 0.25, 15, token("text.active")),
                                                                    "white-space": keyword("normal")})
    overwrite_modal = dialog(doc, "overwriteModal", STR["overwrite.title"], STR["overwrite.body"], [
        ("overwrite_yes", STR["yes"], 61, None, "overwriteConfirm", STR["overwrite.hint"]),
        ("overwrite_no", STR["no"], 210, None, "overwriteCancel", None)], initial="overwrite_no", back="overwriteCancel",
        contents=[question, target])
    doc.events["overwriteConfirm"] = [{"op": "action", "action": "overwrite"}, {"op": "call", "event": "overwriteModalHide"}]
    doc.events["overwriteCancel"] = [{"op": "action", "action": "soundBack"}, {"op": "call", "event": "overwriteModalHide"}]
    notice = label("noticeModal-body", PLACEHOLDER, {**box(30, 40, 300, 56), **typeface(FACE_BANK, 0.25, 15, token("text.active")),
                                                     "white-space": keyword("normal")})
    doc.bind("noticeModal-body.text", "noticeModal-body", "text", {"state": "save.notice"})
    notice_modal = dialog(doc, "noticeModal", STR["notice.title"], PLACEHOLDER, [
        ("notice_ok", STR["ok"], 135, None, "noticeClose", None)], initial="notice_ok", back="noticeClose", contents=[notice])
    doc.events["noticeClose"] = [{"op": "action", "action": "soundBack"}, {"op": "call", "event": "noticeModalHide"}]

    owner = nav_button(doc, "page_close", STR["save"], FIRST_PLACE, action="back", hint=STR["save.close"])
    return page_frame(doc, page_shell(doc, SAVE_PLATE, SAVE_BRIDGE, SAVE_FLAIRS), content, owner, [overwrite_modal, notice_modal],
                      on_canvas=False)
