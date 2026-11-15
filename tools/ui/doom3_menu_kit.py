#!/usr/bin/env python3
"""Shared parts of openD3's retained Doom 3 menus.

Every measured value cites docs/dev/ui-visual-design.md: section 3
(coordinates and anchors), section 4 (tokens), section 6 (geometry), section 7
(states) and section 8 (motion). The Interface Atlas draws the same parts.

Stock measurements are source units (u) on the 640x480 canvas. The documents
declare a 720 dp view-height canvas with a 960 dp minimum width, so 1 u is
1.5 dp on any view at least as wide as 4:3.

build_doom3_menus.py builds the documents from these parts.
"""

from __future__ import annotations

import json

U = 1.5            # dp per stock source unit
CANVAS_W = 960.0   # the 4:3 canvas in dp
CANVAS_H = 720.0


def rgb(hex_colour: str, alpha: float = 1.0) -> list[float]:
    value = hex_colour.lstrip("#")
    return [round(int(value[i:i + 2], 16) / 255, 4) for i in (0, 2, 4)] + [alpha]


# ------------------------------------------------------------ tokens (section 4)

TOKENS = {
    "text.active": ("#FFFFFF", 1.0),
    "text.action": ("#99FFFF", 1.0),
    "text.value": ("#99CCCC", 1.0),
    "text.dim": ("#FFFFFF", 0.5),
    "text.link": ("#FFFFFF", 0.4),
    "text.press": ("#FFFFFF", 0.1),
    "text.hint": ("#FFFFFF", 0.2),
    "text.data": ("#FFBF66", 1.0),
    "chrome.line": ("#8CA6BF", 0.5),
    "chrome.line.hover": ("#8CA6BF", 1.0),
    "chrome.line.flash": ("#CCE6FF", 1.0),
    "chrome.fill": ("#738CB2", 0.3),
    "chrome.fill.hover": ("#8CA6BF", 0.5),
    "chrome.fill.open": ("#738CB2", 0.4),
    "chrome.fill.disabled": ("#737373", 0.3),
    "chrome.tab": ("#738CB2", 0.2),
    "chrome.strip": ("#738CB2", 0.11),
    "chrome.band": ("#99D9CC", 0.08),
    "chrome.bar": ("#7399B2", 0.2),
    "chrome.glow": ("#80B2CC", 0.5),
    "chrome.glow.hover": ("#99CCE6", 1.0),
    "chrome.glow.disabled": ("#667399", 0.5),
    "plate.page": ("#2E4052", 0.8),
    "plate.dialog": ("#2E404C", 1.0),
    "plate.bridge": ("#336BAB", 0.15),
    "plate.flair": ("#6699CC", 0.2),
    "plate.sheen": ("#FFFFFF", 0.18),
    "plate.shade": ("#00141A", 0.3),
    "plate.outline": ("#99CCFF", 1.0),
    "plate.dim": ("#000000", 0.5),
    "rule.title": ("#99CCFF", 0.2),
    "rule.group": ("#99CCFF", 0.1),
    "rule.shot": ("#669999", 1.0),
    "rule.hair": ("#000000", 1.0),
    "well.list": ("#000000", 0.6),
    "well.inset": ("#000000", 0.5),
    "well.select": ("#4C8580", 0.5),
    "scene.edge": ("#333B40", 1.0),
    "flash.build": ("#FFFFFF", 0.4),
    "flash.tab": ("#FFFFFF", 0.7),
    "flash.press": ("#FFFFFF", 0.8),
}


def token(name: str, alpha: float | None = None) -> list[float]:
    """A token's colour, at its own alpha or at `alpha`."""
    hex_colour, own = TOKENS[name]
    return rgb(hex_colour, own if alpha is None else alpha)


# Section 8.1: geometry decelerates (accel(0.2, 0.8)), groups slide with
# accel(0.4, 0.6), and the hover plate settles long (accel(0, 0.9)).
DECEL = [0.2, 0.0, 0.2, 1.0]
SLIDE = [0.4, 0.0, 0.4, 1.0]
SETTLE = [0.0, 0.0, 0.1, 1.0]

FACE_DEFAULT = "english"   # fonts/english.ttf: actions and titles
FACE_BANK = "bank"         # fonts/bank.ttf: labels, values, body
FACE_AN = "an"             # fonts/an.ttf: save and mod lists


def em(scale: float) -> float:
    """The em of a stock textscale, in dp (section 5: 72 s)."""
    return round(72 * scale, 3)


# ---------------------------------------------------------------- typed values

def length(value: float, unit: str = "dp") -> dict:
    return {"type": "length", "value": round(value, 3), "unit": unit}


def colour(value: list[float]) -> dict:
    return {"type": "color", "value": value}


def keyword(value: str) -> dict:
    return {"type": "keyword", "value": value}


def number(value: float) -> dict:
    return {"type": "number", "value": value}


def font(name: str) -> dict:
    return {"type": "font", "value": name}


def text(key: str) -> dict:
    return {"type": "text", "value": key}


def image(source: str) -> dict:
    return {"type": "image", "value": source}


def transform(tx: float = 0, ty: float = 0, sx: float = 1, sy: float = 1) -> dict:
    return {"type": "transform", "unit": "dp", "value": [round(tx, 3), round(ty, 3), sx, sy, 0]}


def absolute(left=None, top=None, width=None, height=None, right=None, bottom=None) -> dict:
    props = {"position": keyword("absolute")}
    for name, value in (("left", left), ("top", top), ("width", width), ("height", height),
                        ("right", right), ("bottom", bottom)):
        if value is None:
            continue
        props[name] = value if isinstance(value, dict) else length(value)
    return props


def box(x: float, y: float, w: float, h: float) -> dict:
    """A stock rect, in u, as an absolute box in dp."""
    return absolute(left=U * x, top=U * y, width=U * w, height=U * h)


FULL = {**absolute(left=0, top=0), "width": length(100, "%"), "height": length(100, "%")}


def pinned(where: str) -> dict:
    """The box of a band across the view, one canvas high (720 dp), that its
    children measure their stock positions in: "top" stands under the view's
    top edge, "bottom" on its bottom edge and "middle" is centred. On a view
    no taller than 4:3 the view is one canvas high and the three are the same
    box. On a taller view (section 3) what belongs to an edge goes there with
    its band, and the height between is the backdrop's."""
    place = {**absolute(left=0), "width": length(100, "%"), "height": length(CANVAS_H)}
    if where == "top":
        place["top"] = length(0)
    elif where == "bottom":
        place["bottom"] = length(0)
    else:
        place.update({"top": length(50, "%"), "margin-top": length(-CANVAS_H / 2)})
    return place
NO_POINTER = {"pointer-events": keyword("none")}


# -------------------------------------------------------------------- geometry
#
# A vector node that spans the view takes its x from an anchor (section 3):
# the leading edge, the trailing edge or the centred 4:3 canvas.

def lead(u: float) -> dict:
    return {"fraction": 0, "dp": round(U * u, 3)}


def trail(u: float) -> dict:
    return {"fraction": 1, "dp": round(U * (u - 640), 3)}


def mid(u: float) -> dict:
    return {"fraction": 0.5, "dp": round(U * (u - 320), 3)}


def far(u: float) -> dict:
    """An x measured back from a box's own trailing edge, in u."""
    return {"fraction": 1, "dp": round(-U * u, 3)}


def down(u: float) -> dict:
    """A y measured up from a box's own bottom edge, in u."""
    return {"fraction": 1, "dp": round(-U * u, 3)}


def point(x, y) -> list:
    def one(value):
        return round(value, 3) if isinstance(value, (int, float)) else value
    return [one(x), one(y)]


def path(ident: str, points: list, *, fill=None, stroke=None, closed=True, blend=None) -> dict:
    """A polygon or polyline. A point is (x, y), or ("q", control, end) for a
    quadratic curve to `end`."""
    commands = []
    for index, entry in enumerate(points):
        if entry[0] == "q":
            commands.append({"id": f"p{index}", "op": "quadratic", "points": [point(*entry[1]), point(*entry[2])]})
        else:
            commands.append({"id": f"p{index}", "op": "move" if index == 0 else "line", "points": [point(*entry)]})
    if closed:
        commands.append({"id": "close", "op": "close"})
    result = {"id": ident, "commands": commands}
    if fill is not None:
        result["fill"] = fill
    if stroke is not None:
        result["stroke"] = stroke
    if blend:
        result["blend"] = blend
    return result


def solid(value: list[float]) -> dict:
    return {"type": "solid", "color": colour(value)}


def linear(start, end, stops) -> dict:
    return {"type": "linear", "from": point(*start), "to": point(*end),
            "stops": [{"at": at, "color": colour(value)} for at, value in stops]}


def radial(centre, edge, stops) -> dict:
    return {"type": "radial", "from": point(*centre), "to": point(*edge),
            "stops": [{"at": at, "color": colour(value)} for at, value in stops]}


def stroke(paint: dict, width: float, *, minimum: float = 1, join: str = "miter", cap: str = "butt") -> dict:
    return {"paint": paint, "widthDp": round(width, 3), "minimumPixels": minimum, "join": join, "cap": cap}


def hairline(ident: str, points: list, tint: str, *, closed: bool = True, alpha: float = 1.0) -> list:
    """Section 6.2's glowing hairline: a 1 u core over a falloff of 24, 18, 12
    and 6 % at 1 to 4 u either side. Four stacked strokes of the line's colour
    at 6 % each give the measured steps; the node's opacity carries the
    token's alpha, so a state change moves the core and its glow together."""
    paths = []
    for step in (4, 3, 2, 1):
        paths.append(path(f"{ident}-glow{step}", points, closed=closed,
                          stroke=stroke(solid(rgb(tint, round(0.06 * alpha, 4))), U * (1 + 2 * step), minimum=0)))
    paths.append(path(f"{ident}-core", points, closed=closed, stroke=stroke(solid(rgb(tint, alpha)), U, minimum=1)))
    return paths


GLOW_ROOM = 6.0   # u: a hairline's falloff reaches 4.5 u past the shape it outlines


def outset(shape: list, room: float = GLOW_ROOM) -> list:
    """`shape` (dp points in its box) moved into a node `room` u larger on
    every side, so a hairline on the box's own edge keeps its falloff: a
    vector node draws nothing outside its box."""
    def moved(value):
        if isinstance(value, dict):
            return {**value, "dp": round(value.get("dp", 0) + U * room, 3)}
        return value + U * room
    def far_side(value):
        # A fraction of the larger node: one `room` back in from its far edge.
        if isinstance(value, dict) and value.get("fraction"):
            return {**value, "dp": round(value.get("dp", 0) - U * room, 3)}
        return moved(value)
    return [(far_side(x), far_side(y)) for x, y in shape]


def outset_box(room: float = GLOW_ROOM) -> dict:
    """The node `outset` shapes draw in: its parent's box grown by `room` u."""
    return {"position": keyword("absolute"), "left": length(-U * room), "top": length(-U * room),
            "right": length(-U * room), "bottom": length(-U * room)}


# ----------------------------------------------------------------------- nodes

def group(ident: str, props: dict, children=(), **extra) -> dict:
    node = {"id": ident, "type": "group", "properties": props}
    if children:
        node["children"] = list(children)
    node.update(extra)
    return node


def vector(ident: str, props: dict, paths: list, children=(), **extra) -> dict:
    node = {"id": ident, "type": "vector", "properties": props, "paths": paths}
    if children:
        node["children"] = list(children)
    node.update(extra)
    return node


def label(ident: str, key: str, props: dict) -> dict:
    return {"id": ident, "type": "text", "properties": {"text": text(key), **props}}


def picture(ident: str, source: str, props: dict, fit: str = "fill") -> dict:
    return {"id": ident, "type": "image", "properties": {"image": image(source), "image-fit": keyword(fit), **props}}


# Section 5, rule 3: up to textscale 0.30 the stock draws from its 12 point
# atlas, whose capitals stand taller and whose letters stand further apart
# than the 48 point design (docs/dev/ttf-font-system.md). The stock path fits
# each TrueType slot to those retail metrics; a retained document names a size
# and a letter spacing, so it asks for the same fit here: the face's size
# factor, and the constant each pen advance grows by, as a fraction of the em.
SLOT_12 = {FACE_DEFAULT: (1.12, 0.10), FACE_AN: (1.14, 0.08), FACE_BANK: (1.08, 0.0)}


def typeface(face: str, scale: float, line: float, tint: list[float], align: str = "left", **more) -> dict:
    """Text at a stock textscale in a line `line` u tall, centred on that
    line by its height (section 5: text sits on its cell by cap height)."""
    size, spacing = em(scale), 0.0
    if scale <= 0.30:
        grow, track_by = SLOT_12[face]
        size, spacing = round(em(scale) * grow, 3), round(em(scale) * track_by, 3)
    props = {"font-family": font(face), "font-size": length(size), "line-height": length(U * line),
             "color": colour(tint), "text-align": keyword(align), "white-space": keyword("nowrap")}
    if spacing:
        props["letter-spacing"] = length(spacing)
    props.update(more)
    return props


def track(node: str, prop: str, keys: list) -> dict:
    """keys: (ms, typed value[, easing of the interval starting here])."""
    result = []
    for key in keys:
        entry = {"atMs": key[0], "value": key[1]}
        if len(key) > 2 and key[2] is not None:
            entry["easing"] = key[2]
        result.append(entry)
    return {"node": node, "property": prop, "keys": result}


def held(keys: list) -> list:
    """Keys that start from their first value whatever the property holds: a
    timeline starts from the property's current value, so the first value is
    set again 1 ms in. The first key's easing shapes the move that follows."""
    return [(0, keys[0][1]), (1, *keys[0][1:]), *keys[1:]]


# --------------------------------------------------------------------- document

class Document:
    def __init__(self, ident: str):
        self.ident = ident
        self.timelines: list[dict] = []
        self.state: dict = {}
        self.actions: dict = {}
        self.events: dict = {}
        self.bindings: list = []
        self.detail: dict | None = None
        self.hints: list[str] = []

    def timeline(self, ident: str, duration: float, tracks: list, *, iterations: int | None = None,
                 complete: str | None = None, essential: bool | None = None) -> str:
        # The runtime refuses a whole document for one bad track, and a refused
        # document is a silent fall back to the stock screen: fail here.
        for item in tracks:
            times = [key["atMs"] for key in item["keys"]]
            if times[0] != 0 or any(later <= earlier for earlier, later in zip(times, times[1:])) or times[-1] > duration:
                raise ValueError(f"timeline {ident}: {item['node']}.{item['property']} keys at {times} in {duration} ms")
        entry = {"id": ident, "durationMs": duration, "tracks": tracks}
        if iterations is not None:
            entry["iterations"] = iterations
        if essential is not None:
            entry["essential"] = essential
        if complete is not None:
            entry["complete"] = complete
        self.timelines.append(entry)
        return ident

    def bind(self, ident: str, node: str, prop: str, value) -> None:
        self.bindings.append({"id": ident, "node": node, "property": prop, "value": value})

    def session(self, action: str, command: str | None = None) -> str:
        """A request the session answers (idSessionLocal::HandleRetainedSessionRequest)."""
        self.actions[action] = {"operation": "session.menu", "arguments": {"command": command or action}}
        return action

    def hint(self, key: str) -> int:
        """The hint-line subject of a control whose hint is `key` (section 7.3)."""
        self.hints.append(key)
        return len(self.hints) - 1

    def states(self, control: str, parts: list) -> dict:
        """A control's five feedback timelines (section 7.1). Each part is
        (node, property, {state: value}, in ms, out ms[, flash value[, easing]]).

        Arrival (hover, and focus, which is hover: section 7.5) reaches the
        hover value over `in` ms; with a flash value the property jumps to it
        first and settles from there, which is the outline's flash. Release
        (default) runs `out` ms, slower than arrival. A press runs 200 ms and
        never latches. A timeline starts from the property's current value, so
        a jump is a 1 ms step."""
        ids = {}
        for state in ("default", "hover", "focus", "pressed", "disabled"):
            tracks, longest = [], 2
            for part in parts:
                node, prop, values, into, out = part[:5]
                flash = part[5] if len(part) > 5 else None
                ease = part[6] if len(part) > 6 else None
                value = values.get(state, values["default"] if state == "disabled" else values.get("hover") if state != "default" else None)
                if state == "default":
                    keys, end = [(0, value), (out, value)], out
                elif state in ("hover", "focus"):
                    if flash is not None:
                        keys, end = [(0, flash), (1, flash, ease), (into, value)], into
                    else:
                        keys, end = [(0, value), (into, value)], into
                elif state == "pressed":
                    keys, end = [(0, value), (200, value)], 200
                else:
                    keys, end = [(0, value), (150, value)], 150
                tracks.append(track(node, prop, keys))
                longest = max(longest, end)
            ident = f"{control}.{state}"
            self.timeline(ident, longest, tracks)
            ids[state] = ident
        return ids

    def hint_line(self) -> dict:
        """Section 7.3's hint line: Bank 0.25 at 17, 470, anchored to the
        bottom-leading corner, naming the control under the pointer or the
        focus. Each new hint wipes in from the leading end in 150 ms while it
        falls from white at 50 % to its rest at 20 % in 250 ms; the runtime
        plays that for the document each time the subject changes
        (detail.shown). A hint leaves with its subject, in one frame."""
        self.state["hint"] = {"type": "number", "initial": -1}
        self.detail = {"state": "hint", "none": -1, "shown": "hintShown"}
        value = ""
        for index in range(len(self.hints) - 1, -1, -1):
            value = {"op": "select", "args": [{"op": "==", "args": [{"state": "hint"}, index]}, self.hints[index], value]}
        place = absolute(left=0, top=0, width=U * 420, height=U * 12)
        words = label("hint-text", self.hints[0] if self.hints else "#str_01998", {
            **place, **typeface(FACE_BANK, 0.25, 12, rgb("#FFFFFF")), **NO_POINTER, "opacity": number(TOKENS["text.hint"][1])})
        self.bind("hint-line.text", "hint-text", "text", value)
        wipe = group("hint-wipe", {**place, "overflow": keyword("hidden"), **NO_POINTER}, [words])
        self.timeline("hintShown", 250, [
            track("hint-wipe", "width", held([(0, length(0)), (150, length(U * 420)), (250, length(U * 420))])),
            track("hint-text", "opacity", held([(0, number(0.5)), (250, number(TOKENS["text.hint"][1]))]))])
        return group("hint-line", {**box(17, 468, 420, 12), **NO_POINTER, "opacity": number(1)}, [wipe])

    def build(self, root: dict) -> dict:
        result = {"format": "retained-ui", "version": 1, "id": self.ident,
                  "canvas": {"height": CANVAS_H, "minWidth": CANVAS_W}}
        if self.state:
            result["state"] = self.state
        if self.actions:
            result["actions"] = self.actions
        if self.events:
            result["events"] = self.events
        if self.bindings:
            result["bindings"] = self.bindings
        if self.detail:
            result["detail"] = self.detail
        result["timelines"] = self.timelines
        result["root"] = root
        return result


def control(doc: Document, key: str, ids: dict, *, action: str | None = None, event: str | None = None,
            hint: str | None = None, navigation: dict | None = None) -> dict:
    result = {"role": "button", "label": key, "states": ids}
    if action:
        result["action"] = action
    else:
        result["event"] = event
    if hint:
        result["detail"] = doc.hint(hint)
    if navigation:
        result["navigation"] = navigation
    return result


# ------------------------------------------------------------------ components

def nav_button(doc: Document, ident: str, key: str, place: dict, *, action: str | None = None,
               event: str | None = None, hint: str | None = None, band: list | None = None, inset: list | None = None) -> dict:
    """Section 6.3's primary nav button: a parallelogram in a cell 32 u tall.
    The band is 21 u, from 5 to 26 u below the cell top; its leading edge
    runs from 7 u in at the top to 26 u in at the bottom, and the trailing
    end is the same slant, so neighbours interlock. `place` gives the cell,
    which may be longer than stock (section 3: the band spans the view); the
    slants keep their run and the label stays centred.

    Section 7.1: the outline starts each arrival at chrome.line.flash and
    settles to chrome.line.hover in 250 ms; the hover plate fades to
    chrome.fill.hover in 200 ms while it shrinks to its inset rect over 300
    ms; release takes 400 ms; a press dips the label to text.press."""
    # `band` and `inset` give another shape of the same parts (the apply bar).
    band = band or [(U * 7, U * 5), (far(26), U * 5), (far(7), U * 26), (U * 26, U * 26)]
    inset = inset or [(U * 12, U * 7), (far(27), U * 7), (far(12), U * 24), (U * 27, U * 24)]
    fill = vector(f"{ident}-fill", {**FULL, **NO_POINTER}, [path("band", band, fill=solid(token("chrome.fill")))])
    # Open, the band is chrome.fill.open: this much of the same hue over the fill.
    opened = vector(f"{ident}-open", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("band", band, fill=solid(rgb("#738CB2", 0.143)))])
    opened_flash = vector(f"{ident}-openflash", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("band", band, fill=solid([1, 1, 1, 1]))])
    plate = vector(f"{ident}-plate", {**FULL, **NO_POINTER, "opacity": number(0), "transform": transform()},
                   [path("plate", inset, fill=solid(token("chrome.fill.hover")))])
    line = vector(f"{ident}-line", {**FULL, **NO_POINTER, "opacity": number(0.5)}, hairline("line", band, "#8CA6BF"))
    flash = vector(f"{ident}-flash", {**FULL, **NO_POINTER, "opacity": number(0)}, hairline("line", band, "#CCE6FF"))
    lines = group(f"{ident}-lines", {**FULL, **NO_POINTER, "opacity": number(1)}, [line, flash])
    text_node = label(f"{ident}-label", key, {**absolute(left=0, top=U * 5, height=U * 21), "width": length(100, "%"),
                                              **typeface(FACE_DEFAULT, 0.26, 21, token("text.active"), "center"), **NO_POINTER,
                                              "opacity": number(1)})
    white, press, dim = colour(token("text.active")), colour(token("text.press")), colour(token("text.dim"))
    grown, rest = transform(sx=1.06, sy=1.22), transform()
    ids = doc.states(ident, [
        (f"{ident}-line", "opacity", {"default": number(0.5), "hover": number(1), "disabled": number(0)}, 250, 400),
        (f"{ident}-flash", "opacity", {"default": number(0), "hover": number(0)}, 250, 400, number(1)),
        (f"{ident}-plate", "opacity", {"default": number(0), "hover": number(1)}, 200, 400),
        (f"{ident}-plate", "transform", {"default": rest, "hover": rest}, 300, 400, grown, SETTLE),
        (f"{ident}-label", "color", {"default": white, "hover": white, "pressed": press, "disabled": dim}, 250, 250),
    ])
    return group(ident, place, [fill, opened, opened_flash, plate, lines, text_node],
                 control=control(doc, key, ids, action=action, event=event, hint=hint))


def nav_modes(doc: Document, ident: str) -> None:
    """A nav button's three standings beside its own hover and press
    (sections 7.1 and 8.4), each a timeline from whatever it shows now.

    `<id>Lit`: at rest, outlined, its label white. `<id>Dim`: another button
    owns the screen (a sub-list or a page is open): the label falls to
    text.dim in 200 ms and the outline goes out. `<id>Open`: the button has
    grown into its own sub-list or page: its band flashes white at 70 % and
    settles to chrome.fill.open in 50 + 300 ms, and its outline goes out in
    250 ms. These drive the label's and the outline group's opacity, which
    the control's own states leave alone."""
    label_id, lines_id, open_id, flash_id = f"{ident}-label", f"{ident}-lines", f"{ident}-open", f"{ident}-openflash"

    def to(node: str, value: float, ms: int) -> dict:
        return track(node, "opacity", [(0, number(value)), (ms, number(value))])

    doc.timeline(f"{ident}Lit", 300, [to(label_id, 1, 200), to(lines_id, 1, 300), to(open_id, 0, 200), to(flash_id, 0, 200)])
    doc.timeline(f"{ident}Dim", 200, [to(label_id, 0.5, 200), to(lines_id, 0, 200), to(open_id, 0, 200), to(flash_id, 0, 200)])
    doc.timeline(f"{ident}Open", 350, [
        to(label_id, 1, 200), to(lines_id, 0, 250), track(open_id, "opacity", held([(0, number(1)), (350, number(1))])),
        track(flash_id, "opacity", held([(0, number(0.7)), (50, number(0.5)), (350, number(0))]))])


def item_outline(width: float, height: float = 19.0, cut: float = 5.0) -> list:
    """Section 6.4's low box: a rectangle with a 5 u chamfer on its
    top-trailing corner, `width` by `height` u."""
    return [(0, 0), (U * (width - cut), 0), (U * width, U * cut), (U * width, U * height), (0, U * height)]


def menu_item(doc: Document, ident: str, key: str, place: dict, width: float, *, action: str | None = None,
              event: str | None = None, hint: str | None = None, centred: bool = False, inset: float = 12.0,
              navigation: dict | None = None, locked: bool = False, face: str = FACE_DEFAULT) -> dict:
    """Section 6.4's sub-menu item, which is also the dialog button: a faint
    plate with one chamfered corner and a hairline around it, 19 u tall, with
    a Default 0.25 label in text.action.

    Section 7.1: on arrival the label turns white in 250 ms, the outline
    flashes and settles in 250 ms and the plate rises to chrome.fill.hover in
    200 ms; release takes 400 ms (the label 250); a press flashes the plate
    white at 80 % and decays. A locked item shows text.dim and keeps its
    shape (section 7.5)."""
    shape = item_outline(width)
    plate = vector(f"{ident}-plate", {**FULL, **NO_POINTER, "opacity": number(1)}, [path("plate", shape, fill=solid(token("chrome.fill")))])
    hot = vector(f"{ident}-hot", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("plate", shape, fill=solid(token("chrome.fill.hover")))])
    press = vector(f"{ident}-press", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("plate", shape, fill=solid(token("flash.press")))])
    line = vector(f"{ident}-line", {**outset_box(), **NO_POINTER, "opacity": number(0.5)}, hairline("line", outset(shape), "#8CA6BF"))
    flash = vector(f"{ident}-flash", {**outset_box(), **NO_POINTER, "opacity": number(0)}, hairline("line", outset(shape), "#CCE6FF"))
    rest_tint = token("text.dim") if locked else token("text.action")
    text_props = {**absolute(left=0 if centred else U * inset, top=0, height=U * 19),
                  **typeface(face, 0.25, 19, rest_tint, "center" if centred else "left"), **NO_POINTER}
    text_props["width"] = length(100, "%") if centred else length(U * (width - inset))
    text_node = label(f"{ident}-label", key, text_props)
    idle, white = colour(rest_tint), colour(token("text.dim") if locked else token("text.active"))
    ids = doc.states(ident, [
        (f"{ident}-plate", "opacity", {"default": number(1), "hover": number(0)}, 200, 400),
        (f"{ident}-hot", "opacity", {"default": number(0), "hover": number(1)}, 200, 400),
        (f"{ident}-press", "opacity", {"default": number(0), "hover": number(0), "pressed": number(1)}, 200, 200),
        (f"{ident}-line", "opacity", {"default": number(0.5), "hover": number(1)}, 250, 400),
        (f"{ident}-flash", "opacity", {"default": number(0), "hover": number(0)}, 250, 400, number(1)),
        (f"{ident}-label", "color", {"default": idle, "hover": white, "disabled": colour(token("text.dim"))}, 250, 250),
    ])
    return group(ident, {**place, "width": length(U * width), "height": length(U * 19)}, [plate, hot, press, line, flash, text_node],
                 control=control(doc, key, ids, action=action, event=event, hint=hint, navigation=navigation))


def footer_link(doc: Document, ident: str, key: str, place: dict, *, action: str | None = None,
                event: str | None = None, hint: str | None = None, align: str = "center") -> dict:
    """A footer link (sections 7.1 and 9.2): Default 0.25 in text.link; white
    in 100 ms on arrival, back in 200 ms, and a press dips it to text.press."""
    text_node = label(f"{ident}-label", key, {**FULL, **typeface(FACE_DEFAULT, 0.25, 22, token("text.link"), align), **NO_POINTER})
    ids = doc.states(ident, [
        (f"{ident}-label", "color", {"default": colour(token("text.link")), "hover": colour(token("text.active")),
                                     "pressed": colour(token("text.press")), "disabled": colour(rgb("#FFFFFF", 0.2))}, 100, 200),
    ])
    return group(ident, place, [text_node], control=control(doc, key, ids, action=action, event=event, hint=hint))


def cut_plate(width: float, height: float, cuts: tuple) -> list:
    """A rectangle `width` by `height` dp with its corners cut at 45 degrees
    by `cuts` dp: top-leading, top-trailing, bottom-trailing, bottom-leading."""
    tl, tr, br, bl = cuts
    return [(tl, 0), (width - tr, 0), (width, tr), (width, height - br), (width - br, height), (bl, height), (0, height - bl), (0, tl)]


def dialog(doc: Document, ident: str, title_key: str, body_key: str, buttons: list, *, initial: str,
           back: str, width: float = 364.0, height: float = 144.0, contents: list | None = None,
           animate: bool = True, dim_alpha: float | None = None, body_lines: float = 56.0, button_width: float = 96.0,
           button_face: str = FACE_DEFAULT) -> dict:
    """Section 6.10's dialog shell: the one opaque object in the menus. A
    slate plate with all four corners cut 22 u, a corner sheen and its
    mirrored shade, and a separate pale-blue hairline 5 u outside it with its
    corners cut 25 u, over a 50 % dim of the whole view. It is centred in the
    view (section 3). The title is Default 0.32 at (20, 5), the rule 2 u at
    (5, 23), the body Bank 0.25 at (30, 40), and the buttons sub-menu items
    in 96 u cells, the affirmative leading (section 7.4).

    Section 8.4: the dim arrives in 200 ms; at 200 the plate flashes white
    and settles in 50 + 200 ms; content and focus arrive at 260. Closing
    fades everything together in 200 ms. `buttons` is [(id, key, x in the
    plate, action or None, event or None, hint)]; `initial` takes the focus
    and `back` is the event Back runs. With `animate` off the shell appears
    and vanishes in one frame, as engine message boxes do (section 9.9)."""
    visible, shown = f"{ident}.visible", f"{ident}.contents"
    doc.state[visible] = {"type": "boolean", "initial": False}
    doc.state[shown] = {"type": "boolean", "initial": False}
    w, h = U * width, U * height
    plate_shape = cut_plate(w, h, (U * 22,) * 4)
    grow = U * 5
    outline_shape = [(x - grow if x < w / 2 else x + grow, y - grow if y < h / 2 else y + grow)
                     for x, y in cut_plate(w, h, (U * 23,) * 4)]
    reach = U * 170
    plate = vector(f"{ident}-plate", {**FULL, **NO_POINTER}, [
        path("plate", plate_shape, fill=solid(token("plate.dialog"))),
        path("sheen", plate_shape, fill=radial((U * 3, U * 3), (U * 3 + reach, U * 3),
                                               [(0, token("plate.sheen")), (1, token("plate.sheen", 0))])),
        path("shade", plate_shape, fill=radial((w - U * 3, h - U * 3), (w - U * 3 - reach, h - U * 3),
                                               [(0, token("plate.shade")), (1, token("plate.shade", 0))])),
    ])
    outline = vector(f"{ident}-outline", {**outset_box(12), **NO_POINTER}, hairline("outline", outset(outline_shape, 12), "#99CCFF"))
    flash = vector(f"{ident}-flash", {**FULL, **NO_POINTER, "opacity": number(0)},
                   [path("flash", plate_shape, fill=solid(token("flash.build", 1.0)))])
    title = label(f"{ident}-title", title_key, {**box(20, 5, width - 44, 20), **typeface(FACE_DEFAULT, 0.32, 20, token("text.active"))})
    rule = vector(f"{ident}-rule", {**box(5, 23, width - 39, 2), **NO_POINTER},
                  [path("rule", [(0, 0), ({"fraction": 1}, 0), ({"fraction": 1}, {"fraction": 1}), (0, {"fraction": 1})],
                        fill=solid(token("rule.title")))])
    body = contents if contents is not None else [label(f"{ident}-body", body_key, {
        **box(30, 40, width - 64, body_lines), **typeface(FACE_BANK, 0.25, 15, token("text.active")), "white-space": keyword("pre-wrap")})]
    items = [menu_item(doc, button_id, key, absolute(left=U * x, top=U * (height - 38)), button_width, action=action, event=event,
                       hint=hint, centred=True, face=button_face) for button_id, key, x, action, event, hint in buttons]
    inner = group(f"{ident}-contents", {**FULL, "display": keyword("none")}, [title, rule, *body, *items])
    shell = group(f"{ident}-shell", {**absolute(top=U * 130, width=w, height=h), "left": length(50, "%"),
                                     "margin-left": length(-w / 2), "opacity": number(0 if animate else 1)},
                  [outline, plate, flash, inner])
    dim_alpha = TOKENS["plate.dim"][1] if dim_alpha is None else dim_alpha
    dim = group(f"{ident}-dim", {**FULL, "background-color": colour(token("plate.dim", 0 if animate else dim_alpha))})
    stage = group(f"{ident}-stage", {**absolute(left=0), "width": length(100, "%"), "height": length(CANVAS_H),
                                     "top": length(50, "%"), "margin-top": length(-CANVAS_H / 2)}, [shell])
    node = group(ident, {**FULL, "display": keyword("none")}, [dim, stage], modal={"initialFocus": initial, "back": back})
    doc.bind(f"{ident}.display", ident, "display", {"op": "select", "args": [{"state": visible}, "block", "none"]})
    doc.bind(f"{ident}-contents.display", f"{ident}-contents", "display", {"op": "select", "args": [{"state": shown}, "block", "none"]})
    show, ready, hide, gone = f"{ident}Show", f"{ident}Shown", f"{ident}Hide", f"{ident}Hidden"
    if animate:
        on, off = colour(token("plate.dim", dim_alpha)), colour(token("plate.dim", 0))
        doc.timeline(f"{ident}Enter", 450, [
            track(f"{ident}-dim", "background-color", [(0, off), (200, on), (450, on)]),
            track(f"{ident}-shell", "opacity", [(0, number(0)), (199, number(0)), (200, number(1)), (450, number(1))]),
            track(f"{ident}-flash", "opacity", [(0, number(0)), (199, number(0)), (200, number(0.4)), (250, number(0.25)), (450, number(0))]),
        ])
        doc.timeline(f"{ident}Content", 260, [track(f"{ident}-contents", "opacity", [(0, number(1)), (260, number(1))])], complete=ready)
        doc.timeline(f"{ident}Leave", 200, [
            track(f"{ident}-dim", "background-color", [(0, on), (200, off)]),
            track(f"{ident}-shell", "opacity", [(0, number(1)), (200, number(0))]),
            track(f"{ident}-flash", "opacity", [(0, number(0)), (200, number(0))]),
        ], complete=gone)
        inner["properties"]["opacity"] = number(1)
        doc.events[show] = [{"op": "setState", "values": {visible: True, shown: False}},
                            {"op": "playTimeline", "timeline": f"{ident}Enter"},
                            {"op": "playTimeline", "timeline": f"{ident}Content"}]
        doc.events[ready] = [{"op": "setState", "values": {shown: True}}]
        doc.events[hide] = [{"op": "setState", "values": {shown: False}}, {"op": "playTimeline", "timeline": f"{ident}Leave"}]
        doc.events[gone] = [{"op": "setState", "values": {visible: False}}]
    else:
        doc.events[show] = [{"op": "setState", "values": {visible: True, shown: True}}]
        doc.events[hide] = [{"op": "setState", "values": {visible: False, shown: False}}]
    return node


def walk(node: dict):
    """`node` and every node under it, depth first."""
    yield node
    for child in node.get("children", ()):
        yield from walk(child)


def edge_glow(doc: Document) -> dict:
    """Section 9.1's edge glow: additive scene.edge hugging the view's real
    edges (section 9.11), about 14 u deep at the sides and 12.5 u top and
    bottom, flickering between 100 and 85 % on a 500 ms period (section 8.5).
    It draws over everything, dialogs included."""
    lit, out = token("scene.edge"), token("scene.edge", 0)
    w, h = {"fraction": 1}, {"fraction": 1}
    side, cap = U * 14, U * 12.5
    paths = [
        path("left", [(0, 0), (side, 0), (side, h), (0, h)], fill=linear((0, 0), (side, 0), [(0, lit), (1, out)]), blend="additive"),
        path("right", [({"fraction": 1, "dp": -side}, 0), (w, 0), (w, h), ({"fraction": 1, "dp": -side}, h)],
             fill=linear((w, 0), ({"fraction": 1, "dp": -side}, 0), [(0, lit), (1, out)]), blend="additive"),
        path("top", [(0, 0), (w, 0), (w, cap), (0, cap)], fill=linear((0, 0), (0, cap), [(0, lit), (1, out)]), blend="additive"),
        path("bottom", [(0, {"fraction": 1, "dp": -cap}), (w, {"fraction": 1, "dp": -cap}), (w, h), (0, h)],
             fill=linear((0, h), (0, {"fraction": 1, "dp": -cap}), [(0, lit), (1, out)]), blend="additive"),
    ]
    doc.timeline("edgeGlow", 500, [track("edge-glow", "opacity", [(0, number(1)), (250, number(0.85)), (500, number(1))])], iterations=0)
    return vector("edge-glow", {**FULL, **NO_POINTER, "opacity": number(1)}, paths)


# -------------------------------------------------------------------- encoding

HEADER = """// Copyright (C) 2026 DarkMatter Productions. GPL-3.0-or-later.
// Generated by tools/ui/build_doom3_menus.py from docs/dev/ui-visual-design.md;
// regenerate instead of editing. Presented only while ui_retained is 1.
"""


def encode(value, depth: int = 0) -> str:
    """Structured JSON with every small object or array on one line."""
    flat = json.dumps(value, ensure_ascii=False)
    if len(flat) <= 110 or not isinstance(value, (dict, list)) or not value:
        return flat
    pad, inner = " " * depth, " " * (depth + 1)
    if isinstance(value, dict):
        items = [f"{inner}{json.dumps(key, ensure_ascii=False)}: {encode(item, depth + 1)}" for key, item in value.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    items = [f"{inner}{encode(item, depth + 1)}" for item in value]
    return "[\n" + ",\n".join(items) + "\n" + pad + "]"


def render(document: dict) -> str:
    return HEADER + encode(document) + "\n"
