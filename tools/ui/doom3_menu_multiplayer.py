#!/usr/bin/env python3
"""openD3's retained multiplayer pages: the Game Browser, Create Server and
the title's Multiplayer Settings panel.

Sections 6.6, 7.1 and 9.6 of docs/dev/ui-visual-design.md: the multiplayer
page takes the whole screen over the stars with its own frame, the title
screen's bands mirrored to the top; a page title, two nav parallelograms as
tabs (GAME BROWSER, CREATE SERVER) and a MAIN MENU link; and the browser
panel: column headers over black column wells, the server list across them,
the source toggles and the small glow buttons.

The session lists the servers through its Join Game route
(idSessionLocal::PublishRetainedJoinGame fills join.row<n>.* for JOIN_ROWS rows
around the chosen server; HandleRetainedJoinGameRequest takes the verbs). A
row is `server-<n>`; its first Accept chooses the server and Accept on the
chosen one joins it.

Create Server sits on the page's one plate, bridged to its tab: the server's
name, the map list under the chosen map's picture, the option rows, ADVANCED
SERVER OPTIONS in a dialog and the create bar. The session publishes it
through its Create Server route (PublishRetainedCreateServer and
PublishRetainedCreateMaps fill create.*; HandleRetainedCreateServerRequest
takes the verbs). A yes-or-no row is a toggle and a limit a whole-number
field, each handing the session its value; Gametype and the server rate step
to their next value, as the stock choices do.

build_doom3_menus.py writes the documents.
"""

from __future__ import annotations

from doom3_menu_kit import (
    CANVAS_H, CANVAS_W, FACE_BANK, FACE_DEFAULT, FULL, NO_POINTER, U, Document, absolute, box, colour, control, dialog,
    edge_glow, far, font, footer_link, group, keyword, label, lead, length, nav_button, number, path, picture, rgb, solid,
    stroke, token, trail, typeface, vector,
)
from doom3_menu_options import row_plate
from doom3_menu_pages import EDGE, PLACEHOLDER, WHOLE, glow_button, name_field, page_shell, row_parts, scroll_bar

JOIN_ROWS = 64      # RETAINED_JOIN_ROWS
ROW_H = 14.0
LIST_W = 593.0      # u: the list beside its 16 u scroll gutter
WELL_H = 261.0      # u: the column wells; the stock's are 141 u over a filter box this page does not have
CAPTION = rgb("#CCFFFF")   # text.caption

# The stock columns, in the browser panel's own u: (state field, heading,
# sort verb, well left, well width).
COLUMNS = (
    ("name", "#str_02268", "joinSortName", 7, 243),
    ("players", "#str_01990", "joinSortPlayers", 252, 67),
    ("ping", "#str_02048", "joinSortPing", 321, 38),
    ("type", "#str_02272", "joinSortGameType", 361, 95),
    ("map", "#str_02274", "joinSortMap", 458, 157),
)


def top_frame() -> dict:
    """The page's frame (section 9.6): the title screen's bottom strips
    mirrored to the top, 12 u at the leading side and 29 u at the trailing
    side with a 45 degree step, and the second band under them."""
    paths = [
        path("strip", [(lead(0), 0), (trail(640), 0), (trail(640), U * 29), (trail(388), U * 29), (trail(371), U * 12), (lead(0), U * 12)],
             fill=solid(token("chrome.strip"))),
        path("band", [(lead(187), U * 16), (trail(379), U * 16), (trail(396), U * 33), (trail(640), U * 33), (trail(640), U * 40),
                      (lead(209), U * 40)], fill=solid(token("chrome.band"))),
    ]
    return vector("frame", {**FULL, **NO_POINTER}, paths)


def page_furniture(doc: Document, open_tab: str, browser: dict, create: dict, back: str) -> tuple:
    """The multiplayer page's own furniture (section 9.6): the page title,
    the two tabs with the open one's band lit, and MAIN MENU at the trailing
    side. `browser` and `create` say what each tab runs, as nav_button's
    `action` or `event`; `back` is the action MAIN MENU runs. Returns the
    parts that sit on the canvas and the trailing-side holder."""
    title = label("mp-title", "#str_02264", {**box(18, 14, 200, 22), **typeface(FACE_DEFAULT, 0.35, 22, CAPTION), **NO_POINTER})
    # The page's frame is the title screen's mirrored to the top, and so are
    # its tabs: the nav parallelogram leaning the other way.
    lean = {"band": [(U * 26, U * 5), (far(7), U * 5), (far(26), U * 26), (U * 7, U * 26)],
            "inset": [(U * 27, U * 7), (far(12), U * 7), (far(27), U * 24), (U * 12, U * 24)]}
    tabs = {"tab_browser": nav_button(doc, "tab_browser", "#str_02265", box(-7, 37, 214, 32), hint="#str_02266", **lean, **browser),
            "tab_create": nav_button(doc, "tab_create", "#str_02200", box(183, 37, 214, 32), hint="#str_02267", **lean, **create)}
    tabs[open_tab]["children"][0]["paths"][0]["fill"] = solid(token("chrome.fill.hover"))
    main_menu = footer_link(doc, "link_mainmenu", "#str_02305", absolute(right=U * (640 - 390 - 120), top=U * 4, width=U * 120, height=U * 22),
                            action=back, hint="#str_01974")
    trail_side = group("trail-side", {**absolute(top=0, height=0), "left": length(50, "%"), "width": length(50, "%")}, [main_menu])
    return [title, *tabs.values()], trail_side


def header(doc: Document, field: str, key: str, verb: str, left: float, width: float) -> dict:
    """A browser column header (section 7.1): text.value, white in 100 ms
    under the pointer; a press sorts the list by its column."""
    ident = f"join_head_{field}"
    text_node = label(f"{ident}-label", key, {**FULL, **typeface(FACE_BANK, 0.25, 16, token("text.value")), **NO_POINTER})
    ids = doc.states(ident, [(f"{ident}-label", "color", {"default": colour(token("text.value")), "hover": colour(token("text.active"))}, 100, 100)])
    return group(ident, box(left + 2, 16, width - 2, 16), [text_node], control=control(doc, key, ids, action=doc.session(verb)))


def radio(doc: Document, ident: str, key: str, left: float, top: float, width: float, chosen: dict, action: str) -> dict:
    """Section 7.1's radio toggle: an 8 x 8 u box with a 1 u border, filled
    when set, and a label that brightens under the pointer."""
    edge = [(0.75, 0.75), (U * 8 - 0.75, 0.75), (U * 8 - 0.75, U * 8 - 0.75), (0.75, U * 8 - 0.75)]
    off = vector(f"{ident}-off", {**box(1, 3, 8, 8), **NO_POINTER}, [path("box", edge, stroke=stroke(solid(rgb("#80B2B2", 0.8)), U, minimum=1))])
    on = vector(f"{ident}-on", {**box(1, 3, 8, 8), **NO_POINTER, "display": keyword("none")}, [
        path("fill", [(0, 0), (U * 8, 0), (U * 8, U * 8), (0, U * 8)], fill=solid(rgb("#99FFFF", 0.4))),
        path("box", edge, stroke=stroke(solid(rgb("#99FFFF", 0.8)), U, minimum=1))])
    doc.bind(f"{ident}-on.display", f"{ident}-on", "display", {"op": "select", "args": [chosen, "block", "none"]})
    text_node = label(f"{ident}-label", key, {**box(10, 0, width - 10, 15), **typeface(FACE_BANK, 0.25, 15, rgb("#FFFFFF", 0.5)), **NO_POINTER})
    ids = doc.states(ident, [(f"{ident}-label", "color", {"default": colour(rgb("#FFFFFF", 0.5)), "hover": colour(rgb("#FFFFFF", 0.8))}, 100, 100)])
    return group(ident, box(left, top, width, 15), [off, on, text_node], control=control(doc, key, ids, action=action))


def server_row(doc: Document, index: int) -> dict:
    """A server's row across the column wells: Bank 0.25. Its first Accept
    chooses the server; Accept on the chosen one joins it."""
    ident, key = f"server-{index}", f"join.row{index}"
    for field in ("name", "ping", "players", "type", "map"):
        doc.state[f"{key}.{field}"] = {"type": "string", "initial": ""}
    cells = []
    for field, _heading, _verb, left, width in COLUMNS:
        node = label(f"{ident}-{field}", PLACEHOLDER, {**box(left - 5, 0, width - 4, ROW_H), **typeface(FACE_BANK, 0.25, ROW_H, rgb("#FFFFFF", 0.8)),
                                                       "overflow": keyword("hidden"), **NO_POINTER})
        doc.bind(f"{ident}-{field}.text", f"{ident}-{field}", "text", {"state": f"{key}.{field}"})
        cells.append(node)
    server = {"op": "+", "args": [{"state": "join.first"}, index]}
    chosen = {"op": "==", "args": [{"state": "join.selected"}, server]}
    doc.bind(f"{ident}.display", ident, "display", {"op": "select", "args": [{"op": "<", "args": [server, {"state": "join.count"}]}, "block", "none"]})
    doc.bind(f"{ident}-selected.display", f"{ident}-selected", "display", {"op": "select", "args": [chosen, "block", "none"]})
    doc.events[f"joinRow{index}"] = [{"op": "if", "condition": chosen, "then": [{"op": "action", "action": "joinServer"}],
                                      "else": [{"op": "setState", "values": {"join.pick": index}}, {"op": "action", "action": "joinPick"}]}]
    plates, ids = row_parts(doc, ident, tuple(node["id"] for node in cells))
    return group(ident, {"position": keyword("relative"), "display": keyword("none"), "width": length(U * LIST_W), "height": length(U * ROW_H),
                         "flex-shrink": number(0)}, [*plates, *cells],
                 control={"role": "button", "label": PLACEHOLDER, "event": f"joinRow{index}", "states": ids})


def join_game_document() -> dict:
    """The Game Browser (section 9.6): the page frame and title, the two
    tabs, MAIN MENU, and the browser panel at 5, 85 on the canvas: five
    column headers over their wells, the list, INTERNET and LAN, REFRESH, GET
    NEW LIST and JOIN GAME, which stays disabled until a server is chosen,
    The session's status and notice lines are not shown: their strings are
    not in Doom 3's language files."""
    doc = Document("opend3.joingame")
    doc.state.update({
        "join.count": {"type": "number", "initial": 0}, "join.first": {"type": "number", "initial": 0},
        "join.selected": {"type": "number", "initial": -1}, "join.pick": {"type": "number", "initial": -1},
        "join.lan": {"type": "boolean", "initial": False}, "join.scanning": {"type": "boolean", "initial": False},
    })
    for verb in ("joinBack", "joinPick", "joinServer", "joinRefresh", "joinNewList", "joinSourceInternet", "joinSourceLan", "joinCreate"):
        doc.session(verb)
    doc.events["onBack"] = [{"op": "action", "action": "joinBack"}]
    doc.events["onSecondary"] = [{"op": "action", "action": "joinRefresh"}]

    wells = [vector(f"join-well-{field}", {**box(left, 34, width, WELL_H), **NO_POINTER},
                    [path("well", WHOLE, fill=solid(token("well.list"))), path("border", EDGE, stroke=stroke(solid(token("rule.hair")), U, minimum=1))])
             for field, _heading, _verb, left, width in COLUMNS]
    heads = [header(doc, *column) for column in COLUMNS]
    rows = group("join-rows", {"position": keyword("relative"), "display": keyword("flex"), "flex-direction": keyword("column"),
                               "width": length(U * LIST_W)}, [server_row(doc, index) for index in range(JOIN_ROWS)])
    viewport = group("join-list", {**box(7, 36, LIST_W, WELL_H - 4), "overflow": keyword("auto")}, [rows])
    bar = scroll_bar(doc, "join_scroll", "join-list", box(600, 35, 15, WELL_H - 2), "#str_02265")
    internet = radio(doc, "join_internet", "#str_02280", 458, 0, 90, {"op": "!", "args": [{"state": "join.lan"}]}, "joinSourceInternet")
    lan = radio(doc, "join_lan", "#str_02282", 550, 0, 60, {"state": "join.lan"}, "joinSourceLan")
    buttons = 34 + WELL_H + 13
    refresh = glow_button(doc, "join_refresh", "#str_02276", 7, buttons, 119, action="joinRefresh")
    new_list = glow_button(doc, "join_newlist", "#str_02278", 134, buttons, 122, action="joinNewList")
    join = glow_button(doc, "join_go", "#str_02288", 503, buttons, 112, action="joinServer")
    doc.bind("join_go.enabled", "join_go", "enabled", {"op": ">=", "args": [{"state": "join.selected"}, 0]})
    panel = group("join-panel", box(5, 85, 630, 360), [*wells, *heads, viewport, bar, internet, lan, refresh, new_list, join])

    canvas_parts, trail_side = page_furniture(doc, "tab_browser", {"action": "joinRefresh"}, {"action": "joinCreate"}, "joinBack")
    canvas = group("canvas", {**absolute(top=0, width=CANVAS_W, height=0), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)},
                   [*canvas_parts, panel])
    stage = group("stage", {**absolute(left=0), "width": length(100, "%"), "height": length(CANVAS_H), "top": length(50, "%"),
                            "margin-top": length(-CANVAS_H / 2)}, [top_frame(), canvas, trail_side, doc.hint_line()])
    doc.events["onActivate"] = [{"op": "playTimeline", "timeline": "edgeGlow"}]
    root = group("screen", {**FULL, "font-family": font(FACE_DEFAULT), "font-size": length(18), "color": colour([1, 1, 1, 1])},
                 [stage, edge_glow(doc)])
    return doc.build(root)


# -------------------------------------------------------------- CREATE SERVER

MAP_ROWS = 64        # RETAINED_CREATE_MAP_ROWS
MAP_ROW_H = 14.0     # u: the stock list's pitch
MAP_W = 130.0
MAPS_SHOWN = 7       # whole rows in the list's 108 u

# The stock plate's open state (MPLANBgMain1 to 9 once Create Server opens) in
# canvas u: 22 u cuts but for the 32 u top-trailing one, and an 8 u step in
# the trailing edge. The bridge runs from the plate up to the CREATE SERVER tab.
CREATE_PLATE = [(106, 84), (528, 84), (560, 116), (560, 266), (552, 274), (552, 426), (530, 448), (106, 448), (84, 426), (84, 106)]
CREATE_BRIDGE = [(125, 66), (365, 66), (349, 82), (109, 82)]

YES, NO = "#str_00836", "#str_00837"
NAME_ROW = (32, 20, 400, 6, 100, "left", 110)   # stock MPLANCS0


def page_row(index: int) -> tuple:
    """An option row of the page (stock MPLANCS1 to 10): left, top, width,
    then the label's left, width and alignment, then the value's left."""
    return (180, 51 + 24 * index, 252, 1, 145, "right", 155)


def advanced_row(index: int) -> tuple:
    """A row of ADVANCED SERVER OPTIONS (stock ADVNet1 to 8)."""
    return (20, 38 + 26 * index, 400, 1, 240, "right", 260)


def setting_states(doc: Document, ident: str, label_node: str, values: tuple) -> dict:
    """Section 7.1: a value is text.value and turns white under the pointer or
    the focus; a row that does not apply dims its label and its value."""
    rest, lit, dim = colour(token("text.value")), colour(token("text.active")), colour(token("text.dim"))
    return doc.states(ident, [(label_node, "color", {"default": lit, "hover": lit, "disabled": dim}, 50, 100),
                              *[(node, "color", {"default": rest, "hover": lit, "disabled": dim}, 50, 100) for node in values]])


def setting_label(ident: str, key: str, place: tuple) -> dict:
    _left, _top, _width, label_left, label_w, align, _value_x = place
    return label(f"{ident}-label", key, {**box(label_left, 0, label_w, 16), **typeface(FACE_BANK, 0.25, 16, token("text.active"), align), **NO_POINTER})


def value_request(doc: Document, verb: str, kind: str) -> str:
    """A verb that carries the control's own value to the session."""
    doc.actions[verb] = {"operation": "session.menuValue", "input": kind, "arguments": {"command": verb, "value": {"input": "value"}}}
    return verb


def flag_row(doc: Document, ident: str, key: str, place: tuple, state: str, verb: str | None, named: str | None = None, *,
             cvar: str | None = None, align: str = "left") -> dict:
    """A two-value setting (section 6.7): bare text after the gutter, No or
    Yes, that steps to the other value on a click. With `named`, the page
    state holding the value's name, the row shows that text for either value
    (Server Type: Internet or LAN). With `cvar` the row reads and sets that
    CVar itself (settings.player.set) and asks the session nothing. `align`
    places the value in its column."""
    left, top, width, _label_left, _label_w, _align, value_x = place
    doc.state[state] = {"type": "boolean", "initial": False, **({"cvar": cvar} if cvar else {})}
    face, value_w = typeface(FACE_BANK, 0.25, 16, token("text.value"), align), width - value_x - 4
    on = label(f"{ident}-on", PLACEHOLDER if named else YES, {**FULL, **face, **NO_POINTER})
    checked = group(f"{ident}-checked", {**box(value_x, 0, value_w, 16), "display": keyword("none"), **NO_POINTER}, [on])
    off = label(f"{ident}-off", PLACEHOLDER if named else NO, {**box(value_x, 0, value_w, 16), **face, **NO_POINTER, "display": keyword("block")})
    doc.bind(f"{ident}-off.display", f"{ident}-off", "display", {"op": "select", "args": [{"state": state}, "none", "block"]})
    if named:
        doc.state[named] = {"type": "string", "initial": ""}
        for node in (f"{ident}-on", f"{ident}-off"):
            doc.bind(f"{node}.text", node, "text", {"state": named})
    ids = setting_states(doc, ident, f"{ident}-label", (f"{ident}-on", f"{ident}-off"))
    if cvar:
        action = f"{ident}Set"
        doc.actions[action] = {"operation": "settings.player.set", "input": "boolean", "arguments": {"cvar": cvar, "value": {"input": "value"}}}
    else:
        action = value_request(doc, verb, "boolean")
    return group(ident, box(left, top, width, 16), [row_plate(ident, width), setting_label(ident, key, place), checked, off],
                 control={"role": "toggle", "label": key, "action": action, "value": {"state": state},
                          "states": ids, "parts": {"checked": f"{ident}-checked"}})


def step_row(doc: Document, ident: str, key: str, place: tuple, state: str, verb: str, *, align: str = "left") -> dict:
    """A choice of several values (section 6.7): its value's name as bare
    text, which a click steps to the next. The session names the value;
    `align` places it in its column."""
    left, top, width, _label_left, _label_w, _align, value_x = place
    doc.state[state] = {"type": "string", "initial": ""}
    value = label(f"{ident}-value", PLACEHOLDER, {**box(value_x, 0, width - value_x - 4, 16), **typeface(FACE_BANK, 0.25, 16, token("text.value"), align),
                                                  "overflow": keyword("hidden"), **NO_POINTER})
    doc.bind(f"{ident}-value.text", f"{ident}-value", "text", {"state": state})
    ids = setting_states(doc, ident, f"{ident}-label", (f"{ident}-value",))
    return group(ident, box(left, top, width, 16), [row_plate(ident, width), setting_label(ident, key, place), value],
                 control={"role": "button", "label": key, "action": doc.session(verb), "states": ids})


def edit_row(doc: Document, ident: str, key: str, place: tuple, state: str, verb: str, limit: int, *, integer: tuple | None = None,
             tint: list | None = None) -> dict:
    """A typed setting on its row plate (the stock edits): text, which Enter
    writes into the page's `state` before `verb` asks the session to take
    it, or with `integer` a whole number in that range, which goes with the
    verb."""
    left, top, width, _label_left, _label_w, _align, value_x = place
    if integer is not None:
        doc.state[state] = {"type": "number", "initial": integer[0]}
        action = value_request(doc, verb, "number")
    else:
        doc.state[state] = {"type": "string", "initial": ""}
        doc.session(verb)
        action = f"{ident}Enter"
        doc.actions[action] = {"input": "string", "operation": "ui.state.set",
                               "arguments": {"key": state, "value": {"input": "value"}, "event": f"{ident}Entered"}}
        doc.events[f"{ident}Entered"] = [{"op": "action", "action": verb}]
    field = name_field(doc, ident, box(value_x - 3, 0, width - value_x - 1, 16), state, action, limit, boxed=False,
                       tint=tint or token("text.value"), key=key, integer=integer)
    row = f"{ident}-row"
    return group(row, box(left, top, width, 16), [row_plate(row, width), setting_label(row, key, place), field])


def map_row(doc: Document, index: int) -> dict:
    """A map in the list: Bank 0.25. Accept chooses it, and its picture
    follows."""
    ident, state = f"map-{index}", f"create.map{index}"
    doc.state[state] = {"type": "string", "initial": ""}
    name = label(f"{ident}-name", PLACEHOLDER, {**box(1, 0, MAP_W - 2, MAP_ROW_H), **typeface(FACE_BANK, 0.25, MAP_ROW_H, rgb("#FFFFFF", 0.8)),
                                                "overflow": keyword("hidden"), **NO_POINTER})
    doc.bind(f"{ident}-name.text", f"{ident}-name", "text", {"state": state})
    entry = {"op": "+", "args": [{"state": "create.map_first"}, index]}
    doc.bind(f"{ident}.display", ident, "display", {"op": "select", "args": [{"op": "<", "args": [entry, {"state": "create.map_count"}]}, "block", "none"]})
    doc.bind(f"{ident}-selected.display", f"{ident}-selected", "display",
             {"op": "select", "args": [{"op": "==", "args": [{"state": "create.map_selected"}, entry]}, "block", "none"]})
    doc.events[f"createMap{index}"] = [{"op": "setState", "values": {"create.pick": index}}, {"op": "action", "action": "createMap"}]
    plates, ids = row_parts(doc, ident, (f"{ident}-name",))
    return group(ident, {"position": keyword("relative"), "display": keyword("none"), "width": length(U * MAP_W), "height": length(U * MAP_ROW_H),
                         "flex-shrink": number(0)}, [*plates, name],
                 control={"role": "button", "label": PLACEHOLDER, "event": f"createMap{index}", "states": ids})


def map_pager(doc: Document, ident: str, key: str, action: str, shown: dict) -> dict:
    """A row that pages the list, when there are more maps than it holds."""
    text_node = label(f"{ident}-label", key, {**box(1, 0, MAP_W - 2, MAP_ROW_H), **typeface(FACE_BANK, 0.25, MAP_ROW_H, token("text.action")), **NO_POINTER})
    hot = vector(f"{ident}-hot", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("bar", WHOLE, fill=solid(token("well.select", 0.25)))])
    ids = doc.states(ident, [
        (f"{ident}-hot", "opacity", {"default": number(0), "hover": number(1)}, 50, 200),
        (f"{ident}-label", "color", {"default": colour(token("text.action")), "hover": colour(token("text.active"))}, 50, 200),
    ])
    doc.bind(f"{ident}.display", ident, "display", {"op": "select", "args": [shown, "block", "none"]})
    return group(ident, {"position": keyword("relative"), "display": keyword("none"), "width": length(U * MAP_W), "height": length(U * MAP_ROW_H),
                         "flex-shrink": number(0)}, [hot, text_node], control={"role": "button", "label": key, "action": action, "states": ids})


def create_server_document() -> dict:
    """Create Server (section 9.6), on the stock panel's own coordinates at
    85, 85 on the canvas: the server's name; the chosen map's picture over
    the map list in a black frame; nine option rows on a 24 u pitch; ADVANCED
    SERVER OPTIONS, which opens a dialog of eight more; and the create bar.
    Team Damage applies to the team game types only. The stock PunkBuster
    row, for a discontinued service, is not built."""
    doc = Document("opend3.createserver")
    doc.state.update({
        "create.gametype": {"type": "number", "initial": 0}, "create.rate": {"type": "number", "initial": 0},
        "create.map_count": {"type": "number", "initial": 0}, "create.map_first": {"type": "number", "initial": 0},
        "create.map_selected": {"type": "number", "initial": -1}, "create.pick": {"type": "number", "initial": -1},
        "create.shot": {"type": "string", "initial": ""},
        # The adapter keeps this: a field holds text not yet entered.
        "ui.numberDraftsPending": {"type": "boolean", "initial": False},
    })
    for verb in ("createBack", "createBrowser", "createMap", "createStart", "createMapsNewer", "createMapsOlder", "soundForward", "soundBack"):
        doc.session(verb)
    doc.events["onBack"] = [{"op": "action", "action": "createBack"}]
    doc.events["createTab"] = [{"op": "focus", "control": "create_name"}]
    # CREATE takes the page as it stands; text typed but not entered gets the focus back first.
    doc.actions["editDraft"] = {"operation": "ui.numberDrafts.focus", "arguments": {}}
    doc.events["createRequested"] = [{"op": "if", "condition": {"state": "ui.numberDraftsPending"},
                                      "then": [{"op": "action", "action": "editDraft"}], "else": [{"op": "action", "action": "createStart"}]}]

    name = edit_row(doc, "create_name", "#str_02297", NAME_ROW, "create.name", "createName", 24, tint=token("text.data"))

    # The map: its picture in a rule.shot frame, the caption, and the list.
    cut = [(0.75, 0.75), (U * 130, 0.75), (U * 138 - 0.75, U * 8), (U * 138 - 0.75, U * 236 - 0.75), (0.75, U * 236 - 0.75)]
    frame = vector("create-map-frame", {**box(32, 51, 138, 236), **NO_POINTER},
                   [path("well", cut, fill=solid(token("well.list")), stroke=stroke(solid(token("rule.hair")), U, minimum=1))])
    shot = picture("create-shot", "", {**box(37, 56, 128, 96), **NO_POINTER}, fit="cover")
    doc.bind("create-shot.image", "create-shot", "image", {"state": "create.shot"})
    shot_frame = vector("create-shot-frame", {**box(37, 56, 128, 96), **NO_POINTER}, [path("frame", EDGE, stroke=stroke(solid(token("rule.shot")), U, minimum=1))])
    caption = label("create-map-caption", "#str_02296", {**box(35, 153, 100, 14), **typeface(FACE_BANK, 0.25, 14, token("text.active")), **NO_POINTER})
    first, count = {"state": "create.map_first"}, {"state": "create.map_count"}
    rows = [map_pager(doc, "map-newer", "#str_231127", "createMapsNewer", {"op": ">", "args": [first, 0]}),
            *[map_row(doc, index) for index in range(MAP_ROWS)],
            map_pager(doc, "map-older", "#str_231128", "createMapsOlder", {"op": "<", "args": [{"op": "+", "args": [first, MAP_ROWS]}, count]})]
    column = group("create-map-rows", {"position": keyword("relative"), "display": keyword("flex"), "flex-direction": keyword("column"),
                                       "width": length(U * MAP_W)}, rows)
    # The stock list's box is 35, 167, 130, 115; its first row starts 7 u down.
    viewport = group("create-maps", {**box(35, 174, MAP_W, 108), "overflow": keyword("auto")}, [column])
    bar = scroll_bar(doc, "create_scroll", "create-maps", box(153, 174, 16, 108), "#str_02296")
    bar["properties"]["display"] = keyword("none")
    doc.bind("create_scroll.display", "create_scroll", "display", {"op": "select", "args": [{"op": ">", "args": [count, MAPS_SHOWN]}, "block", "none"]})

    team_damage = flag_row(doc, "create_teamdamage", "#str_01980", page_row(2), "create.teamdamage", "createTeamDamage")
    game_type = {"state": "create.gametype"}
    doc.bind("create_teamdamage.enabled", "create_teamdamage", "enabled",
             {"op": "||", "args": [{"op": "==", "args": [game_type, 2]}, {"op": "==", "args": [game_type, 4]}]})
    options = [
        flag_row(doc, "create_lan", "#str_02298", page_row(0), "create.lan", "createLan", named="create.lan_name"),
        step_row(doc, "create_gametype", "#str_01978", page_row(1), "create.gametype_name", "createGameTypeNext"),
        team_damage,
        edit_row(doc, "create_fraglimit", "#str_01982", page_row(3), "create.fraglimit", "createFragLimit", 3, integer=(1, 100)),
        edit_row(doc, "create_timelimit", "#str_01983", page_row(4), "create.timelimit", "createTimeLimit", 2, integer=(0, 60)),
        edit_row(doc, "create_maxplayers", "#str_02299", page_row(5), "create.maxplayers", "createMaxPlayers", 1, integer=(1, 8)),
        flag_row(doc, "create_warmup", "#str_01984", page_row(6), "create.warmup", "createWarmup"),
        flag_row(doc, "create_spectators", "#str_02300", page_row(7), "create.spectators", "createSpectators"),
        flag_row(doc, "create_dedicated", "#str_02301", page_row(8), "create.dedicated", "createDedicated"),
    ]
    advanced_button = glow_button(doc, "create_advanced", "#str_04109", 180, 293, 252, event="advancedOpen", hint="#str_04110")
    create_button = glow_button(doc, "create_go", "#str_04111", 34, 327, 398, event="createRequested", hint="#str_02304")
    content = group("page-content", {**box(85, 85, 474, 362), "display": keyword("none"), "opacity": number(1)},
                    [name, frame, shot, shot_frame, caption, viewport, bar, *options, advanced_button, create_button])
    doc.bind("page-content.display", "page-content", "display", {"op": "select", "args": [{"state": "page.shown"}, "block", "none"]})

    # ADVANCED SERVER OPTIONS (stock AdvancedNetWin): eight rows and the way out.
    advanced = dialog(doc, "advancedModal", "#str_04112", PLACEHOLDER, [
        ("advanced_close", "#str_04119", 102, None, "advancedClose", "#str_04120")], initial="advanced_close", back="advancedClose",
        width=444, height=290, button_width=240, contents=[
            flag_row(doc, "advanced_usepass", "#str_02302", advanced_row(0), "create.usepass", "createUsePass"),
            edit_row(doc, "advanced_password", "#str_02291", advanced_row(1), "create.password", "createPassword", 16),
            edit_row(doc, "advanced_rcon", "#str_04113", advanced_row(2), "create.rconpassword", "createRconPassword", 16),
            flag_row(doc, "advanced_reload", "#str_04114", advanced_row(3), "create.reloadengine", "createReloadEngine"),
            flag_row(doc, "advanced_mods", "#str_04115", advanced_row(4), "create.servermods", "createServerMods"),
            edit_row(doc, "advanced_mapcycle", "#str_04116", advanced_row(5), "create.mapcycle", "createMapCycle", 200),
            flag_row(doc, "advanced_pure", "#str_04117", advanced_row(6), "create.pure", "createPure"),
            step_row(doc, "advanced_rate", "#str_04118", advanced_row(7), "create.rate_name", "createRateNext"),
        ])
    doc.events["advancedOpen"] = [{"op": "action", "action": "soundForward"}, {"op": "call", "event": "advancedModalShow"}]
    doc.events["advancedClose"] = [{"op": "action", "action": "soundBack"}, {"op": "call", "event": "advancedModalHide"}]

    shell = page_shell(doc, CREATE_PLATE, CREATE_BRIDGE, [])
    canvas_parts, trail_side = page_furniture(doc, "tab_create", {"action": "createBrowser"}, {"event": "createTab"}, "createBack")
    canvas = group("canvas", {**absolute(top=0, width=CANVAS_W, height=0), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)},
                   [*shell, content, *canvas_parts])
    stage = group("stage", {**absolute(left=0), "width": length(100, "%"), "height": length(CANVAS_H), "top": length(50, "%"),
                            "margin-top": length(-CANVAS_H / 2)}, [top_frame(), canvas, trail_side, doc.hint_line()])
    doc.events["onActivate"] = [{"op": "setState", "values": {"page.shown": False}}, {"op": "playTimeline", "timeline": "pageEnter"},
                                {"op": "playTimeline", "timeline": "pageContent"}, {"op": "playTimeline", "timeline": "edgeGlow"}]
    root = group("screen", {**FULL, "font-family": font(FACE_DEFAULT), "font-size": length(18), "color": colour([1, 1, 1, 1])},
                 [stage, edge_glow(doc), advanced])
    return doc.build(root)


# ------------------------------------------------------- MULTIPLAYER SETTINGS

# The stock plate's open state (MPPSBgMain1 to 13) in canvas u: 22 u cuts at
# the leading corners, 32 u at the trailing ones, and an 8 u step out in the
# trailing edge. The bridge wraps the plate's bottom-trailing corner and runs
# to the multiplayer list.
MPSET_PLATE = [(72, 120), (358, 120), (390, 152), (390, 295), (398, 303), (398, 358), (366, 390), (72, 390), (50, 368), (50, 142)]
MPSET_BRIDGE = [(390, 275), (467, 275), (521, 329), (521, 338), (412, 338), (412, 405), (294, 405), (279, 390), (366, 390), (398, 358),
                (398, 303), (390, 295)]
# The stock swatches, in their order: the picture and the skin ui_skin takes.
SKINS = (
    ("default", "skins/characters/player/marine_mp"),
    ("green", "skins/characters/player/marine_mp_green"),
    ("blue", "skins/characters/player/marine_mp_blue"),
    ("red", "skins/characters/player/marine_mp_red"),
    ("yellow", "skins/characters/player/marine_mp_yellow"),
)


def settings_row(index: int) -> tuple:
    """A row of the panel (stock PS4, PS3, PS1). The stock rows stand at 58,
    81 and 104 u under a CD key row at 35; without that row the three sit
    half a pitch higher, between the rule and the skin box."""
    return (20, 46 + 23 * index, 300, 1, 100, "right", 110)


def skin_swatch(doc: Document, index: int, name: str, skin: str) -> dict:
    """A player skin (section 9.6): the stock 32 x 64 u picture in a 1 u black
    border, white on the skin in use and under the pointer. Accept wears it."""
    ident = f"mpset_skin_{name}"
    doc.actions[f"{ident}Wear"] = {"operation": "settings.player.set", "arguments": {"cvar": "ui_skin", "value": skin}}
    image = picture(f"{ident}-picture", f"guis/assets/mainmenu/skin_{name}", {**FULL, **NO_POINTER})
    border = vector(f"{ident}-border", {**FULL, **NO_POINTER}, [path("border", EDGE, stroke=stroke(solid(token("rule.hair")), U, minimum=1))])
    hot = vector(f"{ident}-hot", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("border", EDGE, stroke=stroke(solid([1, 1, 1, 0.6]), U, minimum=1))])
    worn = vector(f"{ident}-worn", {**FULL, **NO_POINTER, "display": keyword("none")}, [path("border", EDGE, stroke=stroke(solid([1, 1, 1, 1]), U, minimum=1))])
    doc.bind(f"{ident}-worn.display", f"{ident}-worn", "display",
             {"op": "select", "args": [{"op": "==", "args": [{"state": "cvar.ui_skin"}, skin]}, "block", "none"]})
    ids = doc.states(ident, [(f"{ident}-hot", "opacity", {"default": number(0), "hover": number(1)}, 100, 200)])
    return group(ident, box(35 + 60 * index, 148, 32, 64), [image, border, hot, worn],
                 control={"role": "button", "label": "#str_02195", "action": f"{ident}Wear", "states": ids})


def mp_settings_panel(doc: Document) -> dict:
    """Multiplayer Settings (section 9.6) as a panel of the title, where the
    stock page is: the plate with its bridge to the multiplayer list, the
    title over its rule, Data rate, Always Run and Player Name, the five skin
    swatches in an inset box, and SAVE SETTINGS, which closes it. Every
    setting takes effect as it is changed, as on the stock page. The stock CD
    key row is not built: openD3 has no keys. The logo is hidden while the
    plate is open (section 8.4)."""
    doc.state.update({"mpSettingsModal.visible": {"type": "boolean", "initial": False},
                      "cvar.ui_skin": {"type": "string", "initial": "", "cvar": "ui_skin"},
                      # The adapter keeps this: the name field holds text not yet entered.
                      "ui.numberDraftsPending": {"type": "boolean", "initial": False}})
    doc.session("soundBack")
    xs, ys = [x for x, _ in MPSET_PLATE], [y for _, y in MPSET_PLATE]
    left, top = min(xs), min(ys)
    local = [(U * (x - left), U * (y - top)) for x, y in MPSET_PLATE]
    place = box(left, top, max(xs) - left, max(ys) - top)
    sheen = {"type": "radial", "from": [U * 3, U * 3], "to": [U * 173, U * 3],
             "stops": [{"at": 0, "color": colour(token("plate.sheen"))}, {"at": 1, "color": colour(token("plate.sheen", 0))}]}
    whole = {**absolute(left=0, top=0, width=CANVAS_W, height=CANVAS_H), **NO_POINTER}
    bridge = vector("mpset-bridge", whole, [path("bridge", [(U * x, U * y) for x, y in MPSET_BRIDGE], fill=solid(token("plate.bridge")))])
    plate = vector("mpset-plate", {**place, **NO_POINTER}, [path("body", local, fill=solid(token("plate.page"))), path("sheen", local, fill=sheen)])
    flash = vector("mpset-flash", {**place, **NO_POINTER, "opacity": number(0)}, [path("flash", local, fill=solid([1, 1, 1, 1]))])

    title = label("mpset-title", "#str_04100", {**box(20, 5, 320, 20), **typeface(FACE_DEFAULT, 0.32, 20, token("text.active")), **NO_POINTER})
    rule = vector("mpset-rule", {**box(7, 23, 320, 2), **NO_POINTER}, [path("rule", WHOLE, fill=solid(token("rule.title")))])
    rate = step_row(doc, "mpset_rate", "#str_04101", settings_row(0), "mpsettings.rate_name", "mpRateNext", align="center")
    run = flag_row(doc, "mpset_run", "#str_04102", settings_row(1), "cvar.in_alwaysRun", None, cvar="in_alwaysRun", align="center")
    name = edit_row(doc, "mpset_name", "#str_02193", settings_row(2), "mpsettings.name", "mpName", 40)
    cut = [(0.75, 0.75), (U * 292, 0.75), (U * 300 - 0.75, U * 8), (U * 300 - 0.75, U * 96 - 0.75), (0.75, U * 96 - 0.75)]
    skins = vector("mpset-skins", {**box(20, 128, 300, 96), **NO_POINTER},
                   [path("well", cut, fill=solid(token("well.inset")), stroke=stroke(solid(token("rule.hair")), U, minimum=1))])
    skins_title = label("mpset-skins-title", "#str_02195", {**box(25, 130, 100, 14), **typeface(FACE_BANK, 0.25, 14, token("text.active")), **NO_POINTER})
    swatches = [skin_swatch(doc, index, name_, skin) for index, (name_, skin) in enumerate(SKINS)]
    save = glow_button(doc, "mpset_save", "#str_04103", 184, 237, 130, event="mpSettingsModalHide", hint="#str_02202")
    content = group("mpset-content", box(50, 122, 340, 270), [title, rule, rate, run, name, skins, skins_title, *swatches, save])
    canvas = group("mpset-canvas", {**absolute(top=0, width=CANVAS_W, height=0), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)},
                   [bridge, plate, flash, content])
    stage = group("mpset-stage", {**absolute(left=0), "width": length(100, "%"), "height": length(CANVAS_H), "top": length(50, "%"),
                                  "margin-top": length(-CANVAS_H / 2)}, [canvas])
    node = group("mpSettingsModal", {**FULL, "display": keyword("none")}, [stage], modal={"initialFocus": "mpset_save", "back": "mpSettingsModalHide"})
    doc.bind("mpSettingsModal.display", "mpSettingsModal", "display", {"op": "select", "args": [{"state": "mpSettingsModal.visible"}, "block", "none"]})
    doc.timeline("mpSettingsEnter", 400, [
        {"node": "mpset-flash", "property": "opacity", "keys": [{"atMs": 0, "value": number(0.4)}, {"atMs": 50, "value": number(0.25)},
                                                               {"atMs": 350, "value": number(0)}, {"atMs": 400, "value": number(0)}]},
        {"node": "logo", "property": "opacity", "keys": [{"atMs": 0, "value": number(1)}, {"atMs": 400, "value": number(0)}]}])
    doc.timeline("mpSettingsLeave", 400, [
        {"node": "logo", "property": "opacity", "keys": [{"atMs": 0, "value": number(0)}, {"atMs": 400, "value": number(1)}]}])
    doc.events["mpSettingsModalShow"] = [{"op": "setState", "values": {"mpSettingsModal.visible": True}},
                                         {"op": "playTimeline", "timeline": "mpSettingsEnter"}]
    doc.events["mpSettingsModalHide"] = [{"op": "setState", "values": {"mpSettingsModal.visible": False}}, {"op": "action", "action": "soundBack"},
                                         {"op": "playTimeline", "timeline": "mpSettingsLeave"}]
    return node
