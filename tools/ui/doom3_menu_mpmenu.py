#!/usr/bin/env python3
"""openD3's retained in-game multiplayer menu.

Section 10.13 of docs/dev/ui-visual-design.md: a strip of tabs along the top
edge with one panel hanging from the current tab, the game visible behind it
and nothing dimming the scene; one teal hairline family; the current tab
darkened; panels tied to their tabs by a cut trapezoid.

The game keeps its menu (guis/mpmain.gui): its state and its commands stay
there and it only stops drawing while this card covers it
(idSessionLocal::UpdateRetainedMultiplayer). The session copies what the
card shows from the game's menu (mp.warmup, mp.ready_text, mp.spec_text,
mp.teams, mp.team, mp.vote, mp.say) and turns the card's requests into the
stock menu's own commands (HandleRetainedMultiplayerRequest).

This card draws the strip and six panels. The seventh tab, System, opens
the retained SYSTEM page (guis/menu/settings/system.rui) over the game,
because the engine's settings service serves that one document: the session
keeps this card's strip drawn behind the page with System current, and the
page returns to the card. Where the page cannot present, the session hands
the screen to the stock menu's System page (RETAINED_MP_STOCK_PAGES), so the
card stands where the stock menu stands, on the centred 4:3 canvas, and that
hand-off does not move the strip.

build_doom3_menus.py writes the document.
"""

from __future__ import annotations

from doom3_menu_kit import (
    CANVAS_H, CANVAS_W, FACE_BANK, FACE_DEFAULT, FULL, NO_POINTER, U, Document, absolute, box, colour, font, group, hairline,
    keyword, label, length, number, path, rgb, solid, stroke, track, typeface, vector, pinned,
)
from doom3_menu_multiplayer import SKINS, edit_row, flag_row, skin_swatch, step_row
from doom3_menu_options import CATEGORIES, STR as OPTION_STR, bind_row, choice_row, slider_row
from doom3_menu_pages import EDGE, PLACEHOLDER, WHOLE, name_field

# Section 10.13's tokens.
STRIP = rgb("#336666", 0.6)
STRIP_GLOW = "#8CBFBF"
TAB_TEXT = rgb("#B2FFFF")
TAB_HOVER = rgb("#73B2B2", 0.5)
TAB_CURRENT = rgb("#000D00", 0.4)
PANEL_FILL = rgb("#1A3333", 0.5)
PANEL_BORDER = rgb("#1A4040")
PANEL_LINK = rgb("#337366", 0.3)
FRAME_LINE = rgb("#8CBFBF", 0.40)   # mp.line at the top of its flicker (33 to 40 %)
SHADOW = [0, 0, 0, 1]
BUTTON_FILL = rgb("#99FFFF", 0.3)
BUTTON_BORDER = rgb("#66B2B2")
BUTTON_TEXT = rgb("#99FFFF")
TEXT = [1, 1, 1, 1]
TEXT_OFF = [1, 1, 1, 0.4]
SELECT_FILL = rgb("#99FFFF", 0.4)
SELECT_BORDER = rgb("#99FFFF", 0.8)
TOGGLE_OFF = rgb("#666666")

# The stock tabs: (id, label, x, width). A tab with a panel here shows it
# (mp.tab is the tab's place in this list). System has no panel: the engine's
# settings service serves one document, the SYSTEM page, which the session
# opens under the strip (mpSystem) while the card shows the tab as current.
TABS = (("main", "#str_02381", 0, 48), ("vote", "#str_02484", 50, 87), ("player", "#str_04157", 139, 105),
        ("controls", "#str_04158", 246, 82), ("options", "#str_04159", 330, 72), ("system", "#str_04160", 404, 66),
        ("exit", "#str_04161", 472, 43))
PANEL_TABS = {"main": 0, "vote": 1, "player": 2, "controls": 3, "options": 4, "exit": 6}
SYSTEM_TAB = 5
# What opening a tab resets beside mp.tab: New Vote starts with no type chosen.
TAB_RESET = {"vote": {"vote.type": -1, "vote.item_count": 0}}


def tab(doc: Document, ident: str, key: str, left: float, width: float) -> dict:
    """A tab (section 10.13): a Bank 0.25 label centred in its cell; a wash
    in mp.menu.tab.hover under the pointer in 100 ms; the current tab is
    darkened and never moves."""
    name = f"mp_tab_{ident}"
    hot = vector(f"{name}-hot", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("wash", WHOLE, fill=solid(TAB_HOVER))])
    place = PANEL_TABS.get(ident, SYSTEM_TAB)
    current = vector(f"{name}-current", {**FULL, **NO_POINTER, "display": keyword("none")}, [path("dark", WHOLE, fill=solid(TAB_CURRENT))])
    doc.bind(f"{name}-current.display", f"{name}-current", "display",
             {"op": "select", "args": [{"op": "==", "args": [{"state": "mp.tab"}, place]}, "block", "none"]})
    children = [hot, current]
    doc.events[f"{name}Open"] = [{"op": "setState", "values": {"mp.tab": place, **TAB_RESET.get(ident, {})}},
                                 {"op": "action", "action": "mpClick" if ident in PANEL_TABS else "mpSystem"}]
    children.append(label(f"{name}-label", key, {**FULL, **typeface(FACE_BANK, 0.25, 15, TAB_TEXT, "center"), **NO_POINTER}))
    ids = doc.states(name, [(f"{name}-hot", "opacity", {"default": number(0), "hover": number(1)}, 100, 100)])
    return group(name, box(left, 0, width, 15), children, control={"role": "button", "label": key, "event": f"{name}Open", "states": ids})


def strip() -> list:
    """The tab strip (section 10.13): the body in mp.menu.strip from the top
    edge to 16 u, its ends cut on a slant, and the bright line with its halo
    along its lower edge."""
    shape = [(U * -12, 0), (U * 528, 0), (U * 519, U * 16), (U * -3, U * 16)]
    body = vector("mp-strip", {**absolute(left=0, top=0, width=CANVAS_W, height=U * 24), **NO_POINTER}, [path("body", shape, fill=solid(STRIP))])
    line = vector("mp-strip-line", {**absolute(left=U * -20, top=0, width=U * 560, height=U * 24), **NO_POINTER},
                  hairline("line", [(U * 8, 0), (U * 17, U * 15.5), (U * 539, U * 15.5), (U * 548, 0)], STRIP_GLOW, closed=False, alpha=0.8))
    return [body, line]


def panel(ident: str, tab_left: float, tab_width: float, rect: tuple, content: list, leading_frame: bool) -> dict:
    """The panel recipe (section 10.13): a translucent backing with its own
    dark border, the frame line 6 u outside it, and a trapezoid from the tab
    spreading 16 u to each side at its base, where it meets the frame."""
    left, top, width, height = rect
    link = vector(f"{ident}-link", {**absolute(left=0, top=0, width=CANVAS_W, height=U * 40), **NO_POINTER}, [
        path("link", [(U * tab_left, U * 17), (U * (tab_left + tab_width), U * 17), (U * (tab_left + tab_width + 16), U * 33),
                      (U * (tab_left - 16), U * 33)], fill=solid(PANEL_LINK))])
    frame_points = [(U * (left - 6), U * (top - 6)), (U * (left + width + 6), U * (top - 6)), (U * (left + width + 6), U * (top + height + 6)),
                    (U * (left - 6), U * (top + height + 6))]
    frame = vector(f"{ident}-frame", {**absolute(left=U * -20, top=0, width=CANVAS_W + U * 40, height=CANVAS_H), **NO_POINTER, "opacity": number(1)},
                   [path("frame", [(x + U * 20, y) for x, y in frame_points], closed=leading_frame, stroke=stroke(solid(FRAME_LINE), U, minimum=1))])
    backing = vector(f"{ident}-backing", {**box(left, top, width, height), **NO_POINTER},
                     [path("fill", WHOLE, fill=solid(PANEL_FILL)), path("border", EDGE, stroke=stroke(solid(PANEL_BORDER), U, minimum=1))])
    body = group(f"{ident}-body", box(left, top, width, height), content)
    return group(ident, {**absolute(left=0, top=0, width=CANVAS_W, height=0), "display": keyword("none")}, [link, frame, backing, body])


def shadowed(node: dict) -> dict:
    """`node`, a text, over the stock's shadow 1: its black copy 1 u down and
    to the trailing side, at the text's own alpha. The stock gives it to the
    labels and links that stand over the game with nothing behind them."""
    props = dict(node["properties"])
    place = {name: props.pop(name) for name in ("position", "left", "top", "right", "bottom", "width", "height", "display") if name in props}
    tint = props["color"]["value"]
    under = {"id": f"{node['id']}-shadow", "type": "text",
             "properties": {**props, **FULL, "color": colour([*SHADOW[:3], tint[3]]), "left": length(U), "top": length(U)}}
    node["properties"] = {**props, **FULL}
    return group(f"{node['id']}-set", {**place, **NO_POINTER}, [under, node])


def row_label(ident: str, key: str, centre: float, tint: list = TEXT) -> dict:
    """A row's label (section 10.13): Bank 0.25, right-aligned to the gutter
    at x 120, with the stock's shadow."""
    return shadowed(label(ident, key, {**box(4, centre - 8, 116, 16), **typeface(FACE_BANK, 0.25, 16, tint, "right"), **NO_POINTER}))


def filled_button(doc: Document, ident: str, top: float, action: str, text_state: str) -> dict:
    """A filled button (section 10.13): 128 x 16 u in mp.button.fill with a 1
    u border and a Bank 0.25 label, which the session names. Replacement rule
    4: its text turns white under the pointer in 50 ms and a press flashes
    the fill."""
    fill = vector(f"{ident}-fill", {**FULL, **NO_POINTER}, [path("fill", WHOLE, fill=solid(BUTTON_FILL)),
                                                            path("border", EDGE, stroke=stroke(solid(BUTTON_BORDER), U, minimum=1))])
    flash = vector(f"{ident}-flash", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("flash", WHOLE, fill=solid(rgb("#99FFFF", 0.5)))])
    text_node = label(f"{ident}-label", PLACEHOLDER, {**FULL, **typeface(FACE_BANK, 0.25, 16, BUTTON_TEXT, "center"), **NO_POINTER})
    doc.bind(f"{ident}-label.text", f"{ident}-label", "text", {"state": text_state})
    ids = doc.states(ident, [
        (f"{ident}-label", "color", {"default": colour(BUTTON_TEXT), "hover": colour(TEXT)}, 50, 50),
        (f"{ident}-flash", "opacity", {"default": number(0), "hover": number(0), "pressed": number(1)}, 50, 200),
    ])
    return group(ident, box(129, top, 128, 16), [fill, flash, text_node], control={"role": "button", "label": PLACEHOLDER, "action": action, "states": ids})


def toggle(doc: Document, ident: str, key: str, left: float, centre: float, action: str, chosen: dict | None, enabled: dict) -> dict:
    """A toggle (section 10.13): an 8 x 8 u box with a 1 u border, filled
    with mp.select when chosen, and its caption 10 u to its trailing side.
    Unavailable, its border is #666666 and its caption 40 %."""
    edge = [(0.75, 0.75), (U * 8 - 0.75, 0.75), (U * 8 - 0.75, U * 8 - 0.75), (0.75, U * 8 - 0.75)]
    square = [(0, 0), (U * 8, 0), (U * 8, U * 8), (0, U * 8)]
    place = {**absolute(left=0, top=U * 4, width=U * 8, height=U * 8), **NO_POINTER}
    off = vector(f"{ident}-off", {**place, "display": keyword("block")}, [path("box", edge, stroke=stroke(solid(TOGGLE_OFF), U, minimum=1))])
    live = vector(f"{ident}-box", {**place, "display": keyword("none")}, [path("box", edge, stroke=stroke(solid(BUTTON_BORDER), U, minimum=1))])
    doc.bind(f"{ident}-off.display", f"{ident}-off", "display", {"op": "select", "args": [enabled, "none", "block"]})
    doc.bind(f"{ident}-box.display", f"{ident}-box", "display", {"op": "select", "args": [enabled, "block", "none"]})
    children = [off, live]
    if chosen is not None:
        on = vector(f"{ident}-on", {**place, "display": keyword("none")}, [path("fill", square, fill=solid(SELECT_FILL)),
                                                                            path("box", edge, stroke=stroke(solid(SELECT_BORDER), U, minimum=1))])
        doc.bind(f"{ident}-on.display", f"{ident}-on", "display", {"op": "select", "args": [{"op": "&&", "args": [enabled, chosen]}, "block", "none"]})
        children.append(on)
    children.append(label(f"{ident}-label", key, {**absolute(left=U * 10, top=0, width=U * 42, height=U * 16),
                                                  **typeface(FACE_BANK, 0.25, 16, TEXT), **NO_POINTER}))
    ids = doc.states(ident, [(f"{ident}-label", "color", {"default": colour(TEXT), "hover": colour(TEXT), "disabled": colour(TEXT_OFF)}, 50, 50)])
    doc.bind(f"{ident}.enabled", ident, "enabled", enabled)
    return group(ident, box(left, centre - 8, 54, 16), children, control={"role": "button", "label": key, "action": action, "states": ids})


def text_link(doc: Document, ident: str, key: str, top: float, action: str) -> dict:
    """A text link (section 10.13): 127 x 17 u, right-aligned, mp.menu.tab,
    white under the pointer in 50 ms."""
    text_node = shadowed(label(f"{ident}-label", key, {**FULL, **typeface(FACE_BANK, 0.25, 17, TAB_TEXT, "right"), **NO_POINTER}))
    ids = doc.states(ident, [(f"{ident}-label", "color", {"default": colour(TAB_TEXT), "hover": colour(TEXT)}, 50, 50)])
    return group(ident, box(2, top, 127, 17), [text_node], control={"role": "button", "label": key, "action": action, "states": ids})


def main_panel(doc: Document) -> dict:
    """The Main panel (stock MainWindow, 0, 39, 339 x 178 u, flush to the
    leading edge): Set Status with the ready button in warm-up and Game in
    Progress otherwise; Join with the spectate button; Team with Red and
    Blue in a team game; Vote with Yes and No while a vote is open; and the
    chat field with its Say Global or Say Team switch."""
    warmup, teams, voting = {"state": "mp.warmup"}, {"state": "mp.teams"}, {"state": "mp.vote"}
    ready = filled_button(doc, "mp_ready", 18, "mpReady", "mp.ready_text")
    ready["properties"]["display"] = keyword("none")
    doc.bind("mp_ready.display", "mp_ready", "display", {"op": "select", "args": [warmup, "block", "none"]})
    in_progress = label("mp-in-progress", "#str_02496", {**box(131, 18, 160, 16), **typeface(FACE_BANK, 0.25, 16, TEXT_OFF), **NO_POINTER,
                                                         "display": keyword("block")})
    doc.bind("mp-in-progress.display", "mp-in-progress", "display", {"op": "select", "args": [warmup, "none", "block"]})
    spectate = filled_button(doc, "mp_spectate", 49, "mpSpectate", "mp.spec_text")
    # A row that does not apply shows its label at 40 %, as the stock's dimmed copy does.
    row_labels = []
    for name, key, centre, on in (("team", "#str_02498", 86, teams), ("vote", "#str_02501", 119, voting)):
        for suffix, tint, shown in (("label", TEXT, "block"), ("label-off", TEXT_OFF, "none")):
            node = row_label(f"mp-{name}-{suffix}", key, centre, tint)
            node["properties"]["display"] = keyword("block")
            doc.bind(f"{node['id']}.display", node["id"], "display", {"op": "select", "args": [on, shown, "none" if shown == "block" else "block"]})
            row_labels.append(node)
    red = toggle(doc, "mp_team_red", "#str_02499", 134, 86, "mpTeamToggle", {"op": "==", "args": [{"state": "mp.team"}, 0]}, teams)
    blue = toggle(doc, "mp_team_blue", "#str_02500", 191, 86, "mpTeamToggle", {"op": "==", "args": [{"state": "mp.team"}, 1]}, teams)
    yes = toggle(doc, "mp_vote_yes", "#str_00836", 134, 119, "mpVoteYes", None, voting)
    no = toggle(doc, "mp_vote_no", "#str_00837", 191, 119, "mpVoteNo", None, voting)

    # Chat: the switch names its mode (the session supplies the text), with
    # the stock line under it; Enter in the field says the text.
    say = label("mp_say-label", PLACEHOLDER, {**FULL, **typeface(FACE_BANK, 0.25, 16, TEXT, "right"), **NO_POINTER})
    doc.bind("mp_say-label.text", "mp_say-label", "text", {"state": "mp.say"})
    say_hint = label("mp_say-hint", "#str_02497", {**absolute(left=0, top=U * 11, height=U * 12), "width": length(100, "%"),
                                                   **typeface(FACE_BANK, 0.20, 12, TEXT, "right"), **NO_POINTER})
    ids = doc.states("mp_say", [(node, "color", {"default": colour(TEXT), "hover": colour(BUTTON_TEXT)}, 50, 50) for node in ("mp_say-label", "mp_say-hint")])
    say_switch = group("mp_say", box(14, 140, 106, 24), [say, say_hint], control={"role": "button", "label": "#str_02497", "action": "mpChatMode", "states": ids})
    doc.actions["chatEntered"] = {"input": "string", "operation": "ui.state.set", "arguments": {"key": "mp.chat", "value": {"input": "value"}, "event": "chatSay"}}
    doc.events["chatSay"] = [{"op": "action", "action": "mpChat"}]
    chat = name_field(doc, "mp_chat", box(130, 145, 200, 18), "mp.chat", "chatEntered", 80, key="#str_02497")
    content = [row_label("mp-ready-label", "#str_02495", 26), ready, in_progress, row_label("mp-join-label", "#str_04155", 57), spectate,
               *row_labels, red, blue, yes, no, say_switch, chat]
    return panel("mp-main", 0, 48, (0, 39, 339, 178), content, leading_frame=False)


# The stock vote types in the list's order: (the game's vote index, the row's
# label, the line over its value).
VOTE_TYPES = ((0, "#str_02487", "#str_02487"), (7, "#str_04149", "#str_04149"), (1, "#str_01983", "#str_02489"),
              (2, "#str_01982", "#str_02490"), (3, "#str_02376", "#str_02492"), (5, "#str_02504", "#str_02494"),
              (6, "#str_01987", "#str_01987"), (4, "#str_02505", "#str_02493"))
VOTE_ITEMS = 16      # RETAINED_MP_VOTE_ITEMS
LIST_ROW_H = 18.0
TEXT_IDLE = [1, 1, 1, 0.6]
LIST_SELECT = rgb("#99FFFF", 0.1)
WELL_FILL = rgb("#000000", 0.6)
WELL_BORDER = rgb("#264040")


def well(ident: str, place: dict) -> dict:
    """mp.well.fill: black at 60 % with a 1 u border."""
    return vector(ident, {**place, **NO_POINTER}, [path("fill", WHOLE, fill=solid(WELL_FILL)),
                                                   path("border", EDGE, stroke=stroke(solid(WELL_BORDER), U, minimum=1))])


def list_row(doc: Document, ident: str, width: float, text: dict | str, chosen: dict, event: str, relative: bool) -> dict:
    """A list row (section 10.13): Bank 0.25 in mp.text.idle, white under the
    pointer in 50 ms, the current choice on an mp.select fill; unavailable,
    it is 40 % and ignores the pointer. `text` is a string key or a state
    expression."""
    selected = vector(f"{ident}-selected", {**FULL, **NO_POINTER, "display": keyword("none")}, [path("fill", WHOLE, fill=solid(LIST_SELECT))])
    doc.bind(f"{ident}-selected.display", f"{ident}-selected", "display", {"op": "select", "args": [chosen, "block", "none"]})
    node = label(f"{ident}-label", text if isinstance(text, str) else PLACEHOLDER,
                 {**box(3, 0, width - 6, LIST_ROW_H), **typeface(FACE_BANK, 0.25, LIST_ROW_H, TEXT_IDLE), "overflow": keyword("hidden"), **NO_POINTER})
    if not isinstance(text, str):
        doc.bind(f"{ident}-label.text", f"{ident}-label", "text", text)
    ids = doc.states(ident, [(f"{ident}-label", "color", {"default": colour(TEXT_IDLE), "hover": colour(TEXT), "disabled": colour(rgb("#CCCCCC", 0.4))}, 50, 50)])
    place = ({"position": keyword("relative"), "display": keyword("block"), "width": length(U * width), "height": length(U * LIST_ROW_H),
              "flex-shrink": number(0)} if relative else {})
    return group(ident, place, [selected, node], control={"role": "button", "label": text if isinstance(text, str) else PLACEHOLDER,
                                                           "event": event, "states": ids})


def plain_button(doc: Document, ident: str, key: str, place: dict, event: str) -> dict:
    """A filled button with a fixed label (see filled_button)."""
    fill = vector(f"{ident}-fill", {**FULL, **NO_POINTER}, [path("fill", WHOLE, fill=solid(BUTTON_FILL)),
                                                            path("border", EDGE, stroke=stroke(solid(BUTTON_BORDER), U, minimum=1))])
    flash = vector(f"{ident}-flash", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("flash", WHOLE, fill=solid(rgb("#99FFFF", 0.5)))])
    text_node = label(f"{ident}-label", key, {**FULL, **typeface(FACE_BANK, 0.25, 18, BUTTON_TEXT, "center"), **NO_POINTER})
    ids = doc.states(ident, [
        (f"{ident}-label", "color", {"default": colour(BUTTON_TEXT), "hover": colour(TEXT), "disabled": colour(TEXT_OFF)}, 50, 50),
        (f"{ident}-flash", "opacity", {"default": number(0), "hover": number(0), "pressed": number(1)}, 50, 200),
    ])
    return group(ident, place, [fill, flash, text_node], control={"role": "button", "label": key, "event": event, "states": ids})


def vote_panel(doc: Document) -> dict:
    """The New Vote panel (38, 39, 434 x 178 u): the vote types in a list
    well, each live only where the server allows it; beside it the chosen
    type's line and its value, a whole number for the two limits or a list
    for a game type, a player or a map (with the map's picture); and Call New
    Vote and Cancel Vote. The session supplies the list (vote.item<n>) when
    a type is chosen and takes the vote to the game."""
    doc.state.update({"vote.type": {"type": "number", "initial": -1}, "vote.pick_type": {"type": "number", "initial": -1},
                      "vote.allowed": {"type": "number", "initial": 0}, "vote.number": {"type": "number", "initial": 10},
                      "vote.item_count": {"type": "number", "initial": 0}, "vote.item_selected": {"type": "number", "initial": -1},
                      "vote.pick_item": {"type": "number", "initial": -1}, "vote.shot": {"type": "string", "initial": ""}})
    kind = {"state": "vote.type"}

    def is_type(*types: int) -> dict:
        """True while the chosen vote type is one of `types`."""
        test = {"op": "==", "args": [kind, types[0]]}
        for index in types[1:]:
            test = {"op": "||", "args": [test, {"op": "==", "args": [kind, index]}]}
        return test

    def shown(node: dict, test: dict) -> dict:
        """`node`, taking its place only while `test` holds."""
        node["properties"]["display"] = keyword("none")
        doc.bind(f"{node['id']}.display", node["id"], "display", {"op": "select", "args": [test, "block", "none"]})
        return node

    title = label("vote-title", "#str_02502", {**box(6, 2, 100, 14), **typeface(FACE_BANK, 0.25, 14, TEXT), **NO_POINTER})
    types = []
    for position, (index, key, _line) in enumerate(VOTE_TYPES):
        doc.state[f"vote.on{index}"] = {"type": "boolean", "initial": False}
        ident = f"vote_type_{index}"
        doc.events[f"{ident}Pick"] = [{"op": "setState", "values": {"vote.pick_type": index}}, {"op": "action", "action": "mpVoteType"}]
        row = list_row(doc, ident, 154, key, {"op": "==", "args": [kind, index]}, f"{ident}Pick", relative=False)
        row["properties"] = box(9, 19 + 19 * position, 154, LIST_ROW_H)
        doc.bind(f"{ident}.enabled", ident, "enabled", {"state": f"vote.on{index}"})
        types.append(row)

    # The line over the value names the chosen type; with voting off or a
    # vote under way it says so instead.
    line_text = ""
    for index, _key, line in reversed(VOTE_TYPES):
        line_text = {"op": "select", "args": [{"op": "==", "args": [kind, index]}, line, line_text]}
    allowed = {"op": "==", "args": [{"state": "vote.allowed"}, 1]}
    status_text = {"op": "select", "args": [{"op": "==", "args": [{"state": "vote.allowed"}, 2]}, "#str_02486",
                                             {"op": "select", "args": [allowed, line_text, "#str_02485"]}]}
    line = label("vote-line", "#str_02485", {**box(171, 18, 250, 14), **typeface(FACE_BANK, 0.25, 14, TEXT), **NO_POINTER})
    doc.bind("vote-line.text", "vote-line", "text", status_text)

    doc.actions["voteNumber"] = {"input": "number", "operation": "ui.state.set", "arguments": {"key": "vote.number", "value": {"input": "value"}}}
    field = shown(name_field(doc, "vote_number", box(171, 34, 50, 18), "vote.number", "voteNumber", 3, key="#str_02489", integer=(0, 100)),
                  is_type(1, 2))

    rows = []
    for index in range(VOTE_ITEMS):
        doc.state[f"vote.item{index}"] = {"type": "string", "initial": ""}
        ident = f"vote_item_{index}"
        doc.events[f"{ident}Pick"] = [{"op": "setState", "values": {"vote.pick_item": index}}, {"op": "action", "action": "mpVoteItem"}]
        row = list_row(doc, ident, 124, {"state": f"vote.item{index}"}, {"op": "==", "args": [{"state": "vote.item_selected"}, index]},
                       f"{ident}Pick", relative=True)
        doc.bind(f"{ident}.display", ident, "display", {"op": "select", "args": [{"op": "<", "args": [index, {"state": "vote.item_count"}]}, "block", "none"]})
        rows.append(row)
    column = group("vote-item-rows", {"position": keyword("relative"), "display": keyword("flex"), "flex-direction": keyword("column"),
                                      "width": length(U * 124)}, rows)
    items = shown(group("vote-items", box(168, 34, 128, 115), [well("vote-items-well", FULL),
                                                               group("vote-item-list", {**box(2, 2, 124, 111), "overflow": keyword("auto")}, [column])]),
                  is_type(3, 4, 5))
    picture_node = {"id": "vote-shot", "type": "image", "properties": {"image": {"type": "image", "value": ""}, "image-fit": keyword("cover"), **FULL, **NO_POINTER}}
    doc.bind("vote-shot.image", "vote-shot", "image", {"state": "vote.shot"})
    shot = shown(group("vote-shot-frame", box(300, 38, 128, 96), [
        picture_node, vector("vote-shot-edge", {**FULL, **NO_POINTER}, [path("edge", EDGE, stroke=stroke(solid(rgb("#669999")), U, minimum=1))])]),
        is_type(5))

    doc.events["voteCall"] = [{"op": "action", "action": "mpCallVote"}]
    call = plain_button(doc, "vote_call", "#str_04150", box(171, 153, 125, 18), "voteCall")
    doc.bind("vote_call.enabled", "vote_call", "enabled", {"op": "&&", "args": [allowed, {"op": ">=", "args": [kind, 0]}]})
    doc.events["voteCancel"] = [{"op": "setState", "values": {"mp.tab": 0}}, {"op": "action", "action": "mpClick"}]
    cancel = plain_button(doc, "vote_cancel", "#str_04151", box(300, 153, 128, 18), "voteCancel")
    content = [title, well("vote-types-well", box(6, 17, 160, 155)), *types, line, field, items, shot, call, cancel]
    return panel("mp-vote", 50, 87, (38, 39, 434, 178), content, leading_frame=True)


def player_panel(doc: Document) -> dict:
    """The Multiplayer panel (123, 39, 318 x 178 u): Data rate, Always Run
    and Player Name on option rows, and the five skin pictures in an inset
    box, as on the title's Multiplayer Settings panel. Each takes effect as
    it is changed."""
    doc.state["cvar.ui_skin"] = {"type": "string", "initial": "", "cvar": "ui_skin"}
    row = lambda index: (9, 8 + 23 * index, 300, 1, 100, "right", 110)
    rate = step_row(doc, "mpp_rate", "#str_04101", row(0), "mpsettings.rate_name", "mpRateNext", align="center")
    run = flag_row(doc, "mpp_run", "#str_04102", row(1), "cvar.in_alwaysRun", None, cvar="in_alwaysRun", align="center")
    name = edit_row(doc, "mpp_name", "#str_02193", row(2), "mpsettings.name", "mpName", 40)
    cut = [(0.75, 0.75), (U * 292, 0.75), (U * 300 - 0.75, U * 8), (U * 300 - 0.75, U * 96 - 0.75), (0.75, U * 96 - 0.75)]
    skins = vector("mpp-skins", {**box(9, 78, 300, 96), **NO_POINTER},
                   [path("well", cut, fill=solid(rgb("#000000", 0.5)), stroke=stroke(solid(rgb("#000000")), U, minimum=1))])
    skins_title = label("mpp-skins-title", "#str_02195", {**box(14, 80, 100, 14), **typeface(FACE_BANK, 0.25, 14, TEXT), **NO_POINTER})
    swatches = [skin_swatch(doc, index, name_, skin, left=24, top=98) for index, (name_, skin) in enumerate(SKINS)]
    return panel("mp-player", 139, 105, (123, 39, 318, 178), [rate, run, name, skins, skins_title, *swatches], leading_frame=True)


def sub_tab(doc: Document, index: int, key: str) -> dict:
    """A Controls sub-tab (section 10.13): a Default 0.24 label right-aligned
    to the row gutter; white with a faint plate under the pointer; the open
    category's label is white."""
    ident = f"mpc_tab_{index}"
    chosen = {"op": "==", "args": [{"state": "controls.tab"}, index]}
    hot = vector(f"{ident}-hot", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("plate", WHOLE, fill=solid(rgb("#8CA6BF", 0.3)))])
    idle = label(f"{ident}-label", key, {**FULL, **typeface(FACE_DEFAULT, 0.24, 14, BUTTON_TEXT, "right"), **NO_POINTER})
    open_label = label(f"{ident}-open", key, {**FULL, **typeface(FACE_DEFAULT, 0.24, 14, TEXT, "right"), **NO_POINTER, "display": keyword("none")})
    doc.bind(f"{ident}-open.display", f"{ident}-open", "display", {"op": "select", "args": [chosen, "block", "none"]})
    ids = doc.states(ident, [
        (f"{ident}-hot", "opacity", {"default": number(0), "hover": number(1)}, 200, 400),
        (f"{ident}-label", "color", {"default": colour(BUTTON_TEXT), "hover": colour(TEXT)}, 200, 200),
    ])
    doc.events[f"{ident}Open"] = [{"op": "setState", "values": {"controls.tab": index}}, {"op": "action", "action": "mpClick"}]
    return group(ident, box(0, 14 + 20 * index, 122, 14), [hot, idle, open_label],
                 control={"role": "button", "label": key, "event": f"{ident}Open", "states": ids})


def controls_panel(doc: Document) -> dict:
    """The Controls panel (60, 39, 451 x 295 u): four sub-tabs and the open
    category's bindings, up to twelve rows at a 23 u pitch, the main menu's
    categories and rows (rule 8). A row's Accept waits for a key; Delete or
    Backspace clears the focused row."""
    doc.state.update({"controls.capture": {"type": "number", "initial": -1}, "controls.touchLayout": {"type": "boolean", "initial": False},
                      "controls.tab": {"type": "number", "initial": 0}})
    captions = [label("mpc-caption-action", OPTION_STR["action"], {**box(136, 1, 110, 12), **typeface(FACE_BANK, 0.25, 12, rgb("#99CCCC")), **NO_POINTER}),
                label("mpc-caption-keys", OPTION_STR["keys"], {**box(251, 1, 195, 12), **typeface(FACE_BANK, 0.25, 12, rgb("#99CCCC")), **NO_POINTER})]
    content, row = list(captions), 0
    for index, (heading, rows) in enumerate(CATEGORIES):
        content.append(sub_tab(doc, index, heading))
        built = []
        for position, (key, _binding) in enumerate(rows):
            built.append(bind_row(doc, row, key, 14 + 23 * position))
            row += 1
        holder = group(f"mpc-rows-{index}", {**absolute(left=0, top=0, height=0), "width": length(100, "%"), "display": keyword("none")}, built)
        doc.bind(f"mpc-rows-{index}.display", f"mpc-rows-{index}", "display",
                 {"op": "select", "args": [{"op": "==", "args": [{"state": "controls.tab"}, index]}, "block", "none"]})
        content.append(holder)
    doc.events["onSecondary"] = [{"op": "action", "action": "controlsClear"}]
    return panel("mp-controls", 246, 82, (60, 39, 451, 295), content, leading_frame=True)


def options_panel(doc: Document) -> dict:
    """The Options panel (195, 39, 315 x 230 u): the stock nine rows, seven
    two-state choices and two sliders, in the main menu's furniture (rule
    8). Each sets its CVar as it is changed."""
    def flag(ident: str, key: str, position: int, cvar: str) -> dict:
        doc.state[f"cvar.{cvar}"] = {"type": "boolean", "initial": False, "cvar": cvar}
        return choice_row(doc, ident, key, 8 + 24 * position, cvar, True, False, {"state": f"cvar.{cvar}"})

    doc.state["cvar.m_pitch"] = {"type": "number", "initial": 0.022, "cvar": "m_pitch"}
    doc.state["cvar.m_smooth"] = {"type": "number", "initial": 1, "cvar": "m_smooth"}
    doc.state["cvar.sensitivity"] = {"type": "number", "initial": 5, "cvar": "sensitivity"}
    rows = [flag("mpo_freelook", "#str_02141", 0, "in_freeLook"), flag("mpo_decals", "#str_02132", 1, "g_decals"),
            flag("mpo_reload", "#str_02134", 2, "ui_autoReload"), flag("mpo_switch", "#str_02135", 3, "ui_autoSwitch"),
            flag("mpo_hud", "#str_02136", 4, "g_showHud"), flag("mpo_gun", "#str_02137", 5, "ui_showGun"),
            choice_row(doc, "mpo_invert", "#str_02138", 8 + 24 * 6, "m_pitch", "-0.022", "0.022", {"op": "<", "args": [{"state": "cvar.m_pitch"}, 0]}),
            slider_row(doc, "mpo_smooth", "#str_02139", 8 + 24 * 7, "m_smooth", "cvar.m_smooth", 1, 8, 1, 0),
            slider_row(doc, "mpo_sensitivity", "#str_02140", 8 + 24 * 8, "sensitivity", "cvar.sensitivity", 1, 30, 0.5, 1)]
    # The shared rows stand 20 u in; the panel's stand 7 u in.
    holder = group("mpo-rows", {**absolute(left=U * -13, top=0, height=0), "width": length(100, "%")}, rows)
    return panel("mp-options", 330, 72, (195, 39, 315, 230), [holder], leading_frame=True)


def exit_panel(doc: Document) -> dict:
    """The Exit panel (378, 39, 132 x 58 u): three text links."""
    content = [text_link(doc, "mp_return", "#str_04152", 2, "mpClose"), text_link(doc, "mp_disconnect", "#str_04153", 20, "mpDisconnect"),
               text_link(doc, "mp_quit", "#str_04154", 38, "quit")]
    return panel("mp-exit", 472, 43, (378, 39, 132, 58), content, leading_frame=True)


def multiplayer_menu_document() -> dict:
    """The in-game multiplayer menu's card: the tab strip, its six panels and
    the hint line breathing at the bottom. System opens the SYSTEM page
    under the strip (mpSystem)."""
    doc = Document("opend3.mpescape")
    doc.state.update({
        "mp.shown": {"type": "boolean", "initial": False}, "mp.tab": {"type": "number", "initial": 0},
        "mp.warmup": {"type": "boolean", "initial": False}, "mp.ready_text": {"type": "string", "initial": ""},
        "mp.spec_text": {"type": "string", "initial": ""}, "mp.teams": {"type": "boolean", "initial": False},
        "mp.team": {"type": "number", "initial": 0}, "mp.vote": {"type": "boolean", "initial": False},
        "mp.say": {"type": "string", "initial": ""}, "mp.chat": {"type": "string", "initial": ""},
        # The adapter keeps this: the chat field holds text not yet entered.
        "ui.numberDraftsPending": {"type": "boolean", "initial": False},
    })
    for verb in ("mpClose", "mpDisconnect", "quit", "mpSystem", "mpReady", "mpSpectate", "mpTeamToggle", "mpVoteYes", "mpVoteNo", "mpChat",
                 "mpChatMode", "mpClick", "controlsBind", "controlsClear", "mpVoteType", "mpVoteItem", "mpCallVote"):
        doc.session(verb)
    tabs = [tab(doc, *entry) for entry in TABS]
    panels = []
    for node, index in ((main_panel(doc), PANEL_TABS["main"]), (vote_panel(doc), PANEL_TABS["vote"]), (player_panel(doc), PANEL_TABS["player"]),
                        (controls_panel(doc), PANEL_TABS["controls"]), (options_panel(doc), PANEL_TABS["options"]),
                        (exit_panel(doc), PANEL_TABS["exit"])):
        doc.bind(f"{node['id']}.display", node["id"], "display", {"op": "select", "args": [{"op": "==", "args": [{"state": "mp.tab"}, index]}, "block", "none"]})
        panels.append(node)
    hint = label("mp-hint", "#str_04156", {**box(12, 425, 256, 30), **typeface(FACE_BANK, 0.25, 30, TEXT), **NO_POINTER, "opacity": number(1)})
    doc.timeline("mpHint", 2000, [track("mp-hint", "opacity", [(0, number(1)), (1000, number(0.4)), (2000, number(1))])], iterations=0)
    # The frame line flickers between 40 and 33 % on the stock's 400 ms table.
    doc.timeline("mpFlicker", 400, [track(f"{node['id']}-frame", "opacity", [(0, number(1)), (200, number(0.825)), (400, number(1))])
                                    for node in panels], iterations=0)
    canvas = group("canvas", {**absolute(top=0, width=CANVAS_W, height=0), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)},
                   [*strip(), *tabs, *panels])
    # Rule 7: the strip and its panels hang from the top edge; the hint line
    # keeps its 55 u above the bottom edge on a tall view and its 12 u from the
    # left edge on a wide one, where the stock line docks too (mphud.layout).
    low = group("stage-low", {**pinned("bottom"), **NO_POINTER}, [
        group("canvas-low", {**absolute(top=0, left=0, width=CANVAS_W, height=0)}, [hint])])
    stage = group("stage", {**FULL, "display": keyword("none")}, [low, canvas])
    doc.bind("stage.display", "stage", "display", {"op": "select", "args": [{"state": "mp.shown"}, "block", "none"]})
    # The session raises `open` as the card covers the game's menu and
    # `release` as the menu closes.
    doc.events["open"] = [{"op": "setState", "values": {"mp.shown": True, "mp.tab": 0, "vote.type": -1, "vote.item_count": 0}},
                          {"op": "playTimeline", "timeline": "mpHint"}, {"op": "playTimeline", "timeline": "mpFlicker"}]
    doc.events["release"] = [{"op": "setState", "values": {"mp.shown": False}}]
    doc.events["onBack"] = [{"op": "action", "action": "mpClose"}]
    root = group("screen", {**FULL, "font-family": font(FACE_DEFAULT), "font-size": length(18), "color": colour([1, 1, 1, 1])}, [stage])
    return doc.build(root)
