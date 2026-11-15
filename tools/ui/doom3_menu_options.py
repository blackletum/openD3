#!/usr/bin/env python3
"""openD3's retained CONTROLS and GAME OPTIONS pages.

Sections 6.6, 6.7 and 9.3 of docs/dev/ui-visual-design.md: settings sit on
black row plates with one chamfered corner; a label is right-aligned to a
gutter and its value is bare text that steps on a click; the one drawn input
is the slider, a ticked ruler with a 4 x 8 u thumb. Each page's plate carries
its apply bar in a notch.

The session presents either page over the home, from the home's own options
list (idSessionLocal::HandleRetainedSessionRequest, the OPEND3 options
requests). CONTROLS uses the session's binding route (PublishRetainedControls,
HandleRetainedControlsRequest, RetainedControlsKey): BINDINGS is the session's
RETAINED_CONTROLS_BINDINGS, in order. GAME OPTIONS sets its CVars through
settings.player.set, which takes only the settings the engine registers.

build_doom3_menus.py writes the documents.
"""

from __future__ import annotations

from doom3_menu_kit import (
    FACE_BANK, FACE_DEFAULT, FULL, NO_POINTER, U, Document, absolute, box, colour, control, group, item_outline, keyword,
    label, length, nav_button, number, path, rgb, solid, stroke, token, track, typeface, vector,
)
from doom3_menu_pages import PLACEHOLDER, WHOLE, name_field, page_frame, page_shell, title_and_rule

STR = {
    "controls": "#str_02164", "game": "#str_02129", "apply": "#str_04062", "controls.apply.hint": "#str_04063",
    "game.apply.hint": "#str_04073", "action": "#str_02098", "keys": "#str_02099", "waiting": "#str_07000",
    "yes": "#str_00836", "no": "#str_00837",
}

# The stock page's four categories and their rows: (label, binding).
CATEGORIES = (
    ("#str_02091", (("#str_02100", "_forward"), ("#str_02101", "_back"), ("#str_02102", "_moveLeft"), ("#str_02103", "_moveRight"),
                    ("#str_02104", "_moveUp"), ("#str_02105", "_moveDown"), ("#str_02106", "_left"), ("#str_02107", "_right"),
                    ("#str_02108", "_strafe"), ("#str_02109", "_speed"))),
    ("#str_02092", (("#str_00242", "_impulse1"), ("#str_00243", "_impulse2"), ("#str_01378", "_impulse3"), ("#str_01421", "_impulse4"),
                    ("#str_01422", "_impulse5"), ("#str_01423", "_impulse6"), ("#str_02110", "_impulse7"), ("#str_00249", "_impulse8"),
                    ("#str_02111", "_impulse9"), ("#str_01425", "_impulse10"), ("#str_02021", "_impulse0"), ("#str_02024", "_impulse11"))),
    ("#str_02094", (("#str_02112", "_attack"), ("#str_02113", "_impulse15"), ("#str_02114", "_impulse14"), ("#str_02115", "_impulse13"),
                    ("#str_02116", "_lookUp"), ("#str_02117", "_lookDown"), ("#str_02118", "_mlook"), ("#str_02119", "_impulse18"),
                    ("#str_02120", "_zoom"), ("#str_04066", "_impulse19"))),
    ("#str_04064", (("#str_04067", "savegame quick"), ("#str_04068", "loadgame quick"), ("#str_04069", "screenshot"),
                    ("#str_02068", "clientMessageMode"), ("#str_02122", "clientMessageMode 1"), ("#str_04070", "_impulse20"),
                    ("#str_02125", "_impulse22"), ("#str_02126", "_impulse17"), ("#str_02127", "_impulse28"), ("#str_02128", "_impulse29"),
                    ("#str_04071", "clientDropWeapon"))),
)
BINDINGS = tuple(binding for _heading, rows in CATEGORIES for _label, binding in rows)

# Stock open-state plates (AnimControlsUp, AnimGameUp) in canvas u: 22 u cuts
# top-leading and bottom-trailing, 32 u top-trailing and bottom-leading, and
# the notch where the apply bar nests, 15 u deep between two 45 degree steps.
CONTROLS_PLATE = [(183, 46), (596, 46), (628, 78), (628, 365), (606, 387), (490, 387), (475, 372), (292, 372), (277, 387), (193, 387),
                  (161, 355), (161, 68)]
GAME_PLATE = [(183, 66), (475, 66), (507, 98), (507, 365), (485, 387), (439, 387), (424, 372), (259, 372), (244, 387), (193, 387),
              (161, 355), (161, 88)]
BRIDGE = [(136, 389), (202, 389), (218, 405), (152, 405)]
FLAIRS = [[(152, 215), (159, 208), (159, 271), (152, 271)], [(215, 389), (227, 389), (234, 396), (208, 396)]]


def row_plate(ident: str, width: float) -> dict:
    """Section 6.6's option row plate: black at 60 % with a 5 u chamfer on its
    top-trailing corner and a darker rim (73 % at the edge). It darkens the
    scene behind a line of text and does nothing else: no hover, no selected
    state."""
    rim = [(U * 1, U * 1), (U * (width - 5.4), U * 1), (U * (width - 1), U * 5.4), (U * (width - 1), U * 15), (U * 1, U * 15)]
    return vector(f"{ident}-plate", {**FULL, **NO_POINTER}, [
        path("plate", item_outline(width, 16), fill=solid(rgb("#000000", 0.6))),
        path("rim", rim, stroke=stroke(solid(rgb("#000000", 0.33)), U * 2, minimum=1))])


def row_label(ident: str, key: str, left: float, width: float, align: str) -> dict:
    return label(f"{ident}-label", key, {**box(left, 0, width, 16), **typeface(FACE_BANK, 0.25, 16, token("text.active"), align), **NO_POINTER})


def value_states(doc: Document, ident: str, nodes: tuple) -> dict:
    """Section 7.1: a value is text.value and turns white at once under the
    pointer or the focus."""
    rest, lit = colour(token("text.value")), colour(token("text.active"))
    return doc.states(ident, [(node, "color", {"default": rest, "hover": lit, "disabled": colour(token("text.dim"))}, 50, 100) for node in nodes])


def choice_row(doc: Document, ident: str, key: str, top: float, cvar: str, on_value, off_value, is_on: dict) -> dict:
    """A two-value choice (section 6.7): bare text after the gutter, No or
    Yes, that steps to the other value on a click. No arrows and no box."""
    for name, value in (("On", on_value), ("Off", off_value)):
        doc.actions[f"{ident}{name}"] = {"operation": "settings.player.set", "arguments": {"cvar": cvar, "value": value}}
    doc.events[f"{ident}Step"] = [{"op": "if", "condition": is_on, "then": [{"op": "action", "action": f"{ident}Off"}],
                                   "else": [{"op": "action", "action": f"{ident}On"}]}]
    face = typeface(FACE_BANK, 0.25, 16, token("text.value"))
    yes = label(f"{ident}-yes", STR["yes"], {**box(200, 0, 96, 16), **face, **NO_POINTER, "display": keyword("none")})
    no = label(f"{ident}-no", STR["no"], {**box(200, 0, 96, 16), **face, **NO_POINTER, "display": keyword("block")})
    doc.bind(f"{ident}-yes.display", f"{ident}-yes", "display", {"op": "select", "args": [is_on, "block", "none"]})
    doc.bind(f"{ident}-no.display", f"{ident}-no", "display", {"op": "select", "args": [is_on, "none", "block"]})
    ids = value_states(doc, ident, (f"{ident}-yes", f"{ident}-no"))
    return group(ident, box(20, top, 300, 16), [row_plate(ident, 300), row_label(ident, key, 4, 176, "right"), yes, no],
                 control={"role": "button", "label": key, "event": f"{ident}Step", "states": ids})


def slider_row(doc: Document, ident: str, key: str, top: float, cvar: str, state: str, minimum: float, maximum: float, step: float,
               decimals: int) -> dict:
    """Section 6.7's slider: a ruler 71 x 9 u with eight major ticks every 10
    u that rise from 2 to 9 u, minor ticks at the midpoints, a baseline, and
    a 4 x 8 u thumb with a solid 1 u outline and a 40 % centre. The control
    shows magnitude by height as well as position."""
    doc.actions[f"{ident}Set"] = {"operation": "settings.player.set", "input": "number",
                                  "arguments": {"cvar": cvar, "value": {"input": "value"}}}
    ruler = token("text.value", 0.5)
    ticks = [path("base", [(0, U * 8.5), (U * 71, U * 8.5), (U * 71, U * 9), (0, U * 9)], fill=solid(token("text.value", 0.2)))]
    for index in range(8):
        x, height = 10 * index, 2 + index
        ticks.append(path(f"major{index}", [(U * x, U * (9 - height)), (U * (x + 1), U * (9 - height)), (U * (x + 1), U * 9), (U * x, U * 9)],
                          fill=solid(ruler)))
        if index < 7:
            ticks.append(path(f"minor{index}", [(U * (x + 5), U * 6.5), (U * (x + 6), U * 6.5), (U * (x + 6), U * 9), (U * (x + 5), U * 9)],
                              fill=solid(token("text.value", 0.15))))
    thumb_ink = vector(f"{ident}-thumb-ink", {**FULL, **NO_POINTER}, [
        path("centre", WHOLE, fill=solid([1, 1, 1, 0.4])),
        path("outline", [(0.75, 0.75), ({"fraction": 1, "dp": -0.75}, 0.75), ({"fraction": 1, "dp": -0.75}, {"fraction": 1, "dp": -0.75}),
                         (0.75, {"fraction": 1, "dp": -0.75})], stroke=stroke(solid([1, 1, 1, 1]), U, minimum=1))])
    track = group(f"{ident}-track", box(190, 3.5, 71, 9), [
        vector(f"{ident}-ruler", {**FULL, **NO_POINTER}, ticks),
        group(f"{ident}-fill", absolute(left=0, top=0, width=0, height=U * 9)),
        group(f"{ident}-thumb", absolute(left=0, top=U * 0.5, width=U * 4, height=U * 8), [thumb_ink])])
    value = label(f"{ident}-value", PLACEHOLDER, {**box(266, 0, 30, 16), **typeface(FACE_BANK, 0.25, 16, token("text.value"), "right"), **NO_POINTER})
    ids = value_states(doc, ident, (f"{ident}-value",))
    return group(ident, box(20, top, 300, 16), [row_plate(ident, 300), row_label(ident, key, 4, 176, "right"), track, value],
                 control={"role": "slider", "label": key, "action": f"{ident}Set", "value": {"state": state}, "states": ids,
                          "minimum": minimum, "maximum": maximum, "step": step, "decimals": decimals, "orientation": "horizontal",
                          "parts": {"track": f"{ident}-track", "fill": f"{ident}-fill", "thumb": f"{ident}-thumb", "value": f"{ident}-value"}})


def apply_bar(doc: Document, key: str, cell_left: float, hint: str, event: str = "pageClose") -> dict:
    """Section 6.9's apply bar: the nav button's parts with the leading cap
    mirrored, so both ends lean outward and the bar nests in the plate's
    notch. It saves the page's changes by closing it, as the stock bar does."""
    band = [(U * 26, U * 6), (U * 207, U * 6), (U * 226, U * 27), (U * 7, U * 27)]
    inset = [(U * 29, U * 8), (U * 204, U * 8), (U * 219, U * 25), (U * 14, U * 25)]
    return nav_button(doc, "page_apply", key, box(cell_left, 369, 233, 32), event=event, hint=hint, band=band, inset=inset)


# ------------------------------------------------------------------- CONTROLS

def bind_row(doc: Document, row: int, key: str, top: float) -> dict:
    """A binding (section 6.7): the action's label and, from the gutter, its
    keys as bare text. A click waits for a key, and says so in white."""
    ident, state = f"controls_bind_{row}", f"controls.{row}.keys"
    doc.state[state] = {"type": "string", "initial": "", "keyBinding": BINDINGS[row]}
    waiting = {"op": "==", "args": [{"state": "controls.capture"}, row]}
    keys = label(f"{ident}-keys", PLACEHOLDER, {**box(121, 0, 195, 16), **typeface(FACE_BANK, 0.25, 16, token("text.value")), "overflow": keyword("hidden"),
                                                **NO_POINTER, "display": keyword("block")})
    doc.bind(f"{ident}-keys.text", f"{ident}-keys", "text", {"state": state})
    doc.bind(f"{ident}-keys.display", f"{ident}-keys", "display", {"op": "select", "args": [waiting, "none", "block"]})
    asking = label(f"{ident}-waiting", STR["waiting"], {**box(121, 0, 195, 16), **typeface(FACE_BANK, 0.25, 16, token("text.active")), **NO_POINTER,
                                                         "display": keyword("none")})
    doc.bind(f"{ident}-waiting.display", f"{ident}-waiting", "display", {"op": "select", "args": [waiting, "block", "none"]})
    ids = value_states(doc, ident, (f"{ident}-keys",))
    return group(ident, box(130, top, 320, 16), [row_plate(ident, 320), row_label(ident, key, 6, 112, "left"), keys, asking],
                 control={"role": "button", "label": key, "action": "controlsBind", "states": ids})


def category_tab(doc: Document, index: int, key: str) -> dict:
    """Section 7.1's controls category tab: a Default 0.24 label right-aligned
    to the row gutter with no plate at rest; a plate in chrome.line at 30 %
    under the pointer; the open category's label is white."""
    ident = f"controls_tab_{index}"
    chosen = {"op": "==", "args": [{"state": "controls.tab"}, index]}
    hot = vector(f"{ident}-hot", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("plate", WHOLE, fill=solid(token("chrome.line", 0.3)))])
    idle = label(f"{ident}-label", key, {**FULL, **typeface(FACE_DEFAULT, 0.24, 14, token("text.action"), "right"), **NO_POINTER})
    open_label = label(f"{ident}-open", key, {**FULL, **typeface(FACE_DEFAULT, 0.24, 14, token("text.active"), "right"), **NO_POINTER,
                                               "display": keyword("none")})
    doc.bind(f"{ident}-open.display", f"{ident}-open", "display", {"op": "select", "args": [chosen, "block", "none"]})
    ids = doc.states(ident, [
        (f"{ident}-hot", "opacity", {"default": number(0), "hover": number(1)}, 200, 400),
        (f"{ident}-label", "color", {"default": colour(token("text.action")), "hover": colour(token("text.active"))}, 200, 200),
    ])
    doc.events[f"controlsTab{index}"] = [{"op": "setState", "values": {"controls.tab": index}}, {"op": "action", "action": "soundForward"},
                                         {"op": "playTimeline", "timeline": f"controlsFlash{index}"}]
    return group(ident, box(0, 50 + 20 * index, 122, 14), [hot, idle, open_label],
                 control={"role": "button", "label": key, "event": f"controlsTab{index}", "states": ids})


def controls_document() -> dict:
    """The CONTROLS page (section 9.3): four category tabs right-aligned to
    the row gutter, the open category's bindings on row plates at a 23 u
    pitch, and the apply bar in the plate's notch. A row's Accept waits for a
    key; Delete, Backspace or the secondary button clears the focused row."""
    doc = Document("opend3.controls")
    doc.state.update({"controls.capture": {"type": "number", "initial": -1}, "controls.touchLayout": {"type": "boolean", "initial": False},
                      "controls.tab": {"type": "number", "initial": 0}})
    for verb in ("controlsBind", "controlsClear", "controlsBack", "soundForward"):
        doc.session(verb)
    content = [*title_and_rule("controls", STR["controls"], 448),
               label("controls-caption-action", STR["action"], {**box(136, 34, 110, 12), **typeface(FACE_BANK, 0.25, 12, token("text.value")), **NO_POINTER}),
               label("controls-caption-keys", STR["keys"], {**box(251, 34, 195, 12), **typeface(FACE_BANK, 0.25, 12, token("text.value")), **NO_POINTER})]
    row = 0
    for index, (heading, rows) in enumerate(CATEGORIES):
        content.append(category_tab(doc, index, heading))
        built = []
        for position, (key, _binding) in enumerate(rows):
            built.append(bind_row(doc, row, key, 48 + 23 * position))
            row += 1
        holder = group(f"controls-rows-{index}", {**absolute(left=0, top=0, height=0), "width": length(100, "%"), "display": keyword("none")}, built)
        doc.bind(f"controls-rows-{index}.display", f"controls-rows-{index}", "display",
                 {"op": "select", "args": [{"op": "==", "args": [{"state": "controls.tab"}, index]}, "block", "none"]})
        content.append(holder)
    # Section 8.4 (ControlsFlash): a category's rows flash flash.row, white at
    # 15 %, top to bottom 20 ms apart, each gone in 250 ms.
    longest = max(len(rows) for _heading, rows in CATEGORIES)
    for position in range(longest):
        content.append(vector(f"controls-flash-{position}", {**box(130, 48 + 23 * position, 320, 16), **NO_POINTER, "opacity": number(0)},
                              [path("flash", item_outline(320, 16), fill=solid(rgb("#FFFFFF", 0.15)))]))
    for index, (_heading, rows) in enumerate(CATEGORIES):
        tracks = []
        for position in range(longest):
            at = 20 * position
            lit = [(at + 2, number(1)), (at + 250, number(0))] if position < len(rows) else []
            tracks.append(track(f"controls-flash-{position}", "opacity", [(0, number(0)), (1, number(0)), *lit, (500, number(0))]))
        doc.timeline(f"controlsFlash{index}", 500, tracks)
    doc.events["onSecondary"] = [{"op": "action", "action": "controlsClear"}]
    doc.events["onBack"] = [{"op": "call", "event": "pageClose"}]
    bar = apply_bar(doc, STR["apply"], 267, STR["controls.apply.hint"])
    return page_frame(doc, page_shell(doc, CONTROLS_PLATE, BRIDGE, FLAIRS), content, bar, [], on_canvas=True, content_box=(165, 50, 450, 350),
                      back="controlsBack")


# --------------------------------------------------------------- GAME OPTIONS

def game_options_document() -> dict:
    """The GAME OPTIONS page (section 9.3): the stock page's ten rows at a 23
    u pitch. Yes-or-no rows step on a click; Player Name is an edit; the two
    mouse rows are sliders."""
    doc = Document("opend3.gameoptions")
    doc.state["game.name"] = {"type": "string", "initial": ""}
    doc.state["ui.numberDraftsPending"] = {"type": "boolean", "initial": False}
    for verb in ("gameBack", "gameName"):
        doc.session(verb)
    doc.actions["rename"] = {"input": "string", "operation": "ui.state.set",
                             "arguments": {"key": "game.name", "value": {"input": "value"}, "event": "nameEntered"}}
    doc.events["nameEntered"] = [{"op": "action", "action": "gameName"}]

    def flag(ident: str, key: str, position: int, cvar: str) -> dict:
        doc.state[f"cvar.{cvar}"] = {"type": "boolean", "initial": False, "cvar": cvar}
        return choice_row(doc, ident, key, 38 + 23 * position, cvar, True, False, {"state": f"cvar.{cvar}"})

    doc.state["cvar.m_pitch"] = {"type": "number", "initial": 0.022, "cvar": "m_pitch"}
    doc.state["cvar.m_smooth"] = {"type": "number", "initial": 1, "cvar": "m_smooth"}
    doc.state["cvar.sensitivity"] = {"type": "number", "initial": 5, "cvar": "sensitivity"}
    name_row = group("game_name-row", box(20, 38 + 23, 300, 16), [
        row_plate("game_name-row", 300), row_label("game_name-row", "#str_02193", 4, 176, "right"),
        name_field(doc, "game_name", box(198, 0, 98, 16), "game.name", "rename", 32)])
    content = [*title_and_rule("game", STR["game"], 325),
               flag("game_decals", "#str_02132", 0, "g_decals"),
               name_row,
               flag("game_reload", "#str_02134", 2, "ui_autoReload"),
               flag("game_switch", "#str_02135", 3, "ui_autoSwitch"),
               flag("game_hud", "#str_02136", 4, "g_showHud"),
               flag("game_gun", "#str_02137", 5, "ui_showGun"),
               choice_row(doc, "game_invert", "#str_02138", 38 + 23 * 6, "m_pitch", "-0.022", "0.022",
                          {"op": "<", "args": [{"state": "cvar.m_pitch"}, 0]}),
               slider_row(doc, "game_smooth", "#str_02139", 38 + 23 * 7, "m_smooth", "cvar.m_smooth", 1, 8, 1, 0),
               slider_row(doc, "game_sensitivity", "#str_02140", 38 + 23 * 8, "sensitivity", "cvar.sensitivity", 1, 30, 0.5, 1),
               flag("game_freelook", "#str_02141", 9, "in_freeLook")]
    doc.events["onBack"] = [{"op": "call", "event": "pageClose"}]
    bar = apply_bar(doc, STR["apply"], 225, STR["game.apply.hint"])
    return page_frame(doc, page_shell(doc, GAME_PLATE, BRIDGE, FLAIRS), content, bar, [], on_canvas=True, content_box=(165, 70, 340, 330),
                      back="gameBack")
