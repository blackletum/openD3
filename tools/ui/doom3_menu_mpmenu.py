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

This card draws the strip and two panels, Main and Exit. The other five
tabs hand the screen to the stock menu's page of that name (card.stock_page
and mpStockPage; RETAINED_MP_STOCK_PAGES in the session), so the card stands
where the stock menu stands, on the centred 4:3 canvas, and a hand-off does
not move the strip. Rule 7's top-leading anchor waits for the other panels.

build_doom3_menus.py writes the document.
"""

from __future__ import annotations

from doom3_menu_kit import (
    CANVAS_H, CANVAS_W, FACE_BANK, FACE_DEFAULT, FULL, NO_POINTER, U, Document, absolute, box, colour, font, group, hairline,
    keyword, label, length, number, path, rgb, solid, stroke, track, typeface, vector,
)
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
FRAME_LINE = rgb("#8CBFBF", 0.36)
BUTTON_FILL = rgb("#99FFFF", 0.3)
BUTTON_BORDER = rgb("#66B2B2")
BUTTON_TEXT = rgb("#99FFFF")
TEXT = [1, 1, 1, 1]
TEXT_OFF = [1, 1, 1, 0.4]
SELECT_FILL = rgb("#99FFFF", 0.4)
SELECT_BORDER = rgb("#99FFFF", 0.8)
TOGGLE_OFF = rgb("#666666")

# The stock tabs: (id, label, x, width). Main and Exit are this card's
# panels; the rest are the stock menu's pages, in RETAINED_MP_STOCK_PAGES'
# order.
TABS = (("main", "#str_02381", 0, 48), ("vote", "#str_02484", 50, 87), ("player", "#str_04157", 139, 105),
        ("controls", "#str_04158", 246, 82), ("options", "#str_04159", 330, 72), ("system", "#str_04160", 404, 66),
        ("exit", "#str_04161", 472, 43))
PANEL_TABS = {"main": 0, "exit": 6}
STOCK_TABS = ("vote", "player", "controls", "options", "system")


def tab(doc: Document, ident: str, key: str, left: float, width: float) -> dict:
    """A tab (section 10.13): a Bank 0.25 label centred in its cell; a wash
    in mp.menu.tab.hover under the pointer in 100 ms; the current tab is
    darkened and never moves."""
    name = f"mp_tab_{ident}"
    hot = vector(f"{name}-hot", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("wash", WHOLE, fill=solid(TAB_HOVER))])
    children = [hot]
    if ident in PANEL_TABS:
        current = vector(f"{name}-current", {**FULL, **NO_POINTER, "display": keyword("none")}, [path("dark", WHOLE, fill=solid(TAB_CURRENT))])
        doc.bind(f"{name}-current.display", f"{name}-current", "display",
                 {"op": "select", "args": [{"op": "==", "args": [{"state": "mp.tab"}, PANEL_TABS[ident]]}, "block", "none"]})
        children.append(current)
        doc.events[f"{name}Open"] = [{"op": "setState", "values": {"mp.tab": PANEL_TABS[ident]}}, {"op": "action", "action": "mpClick"}]
    else:
        doc.events[f"{name}Open"] = [{"op": "setState", "values": {"card.stock_page": STOCK_TABS.index(ident)}},
                                     {"op": "action", "action": "mpStockPage"}]
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
    frame = vector(f"{ident}-frame", {**absolute(left=U * -20, top=0, width=CANVAS_W + U * 40, height=CANVAS_H), **NO_POINTER},
                   [path("frame", [(x + U * 20, y) for x, y in frame_points], closed=leading_frame, stroke=stroke(solid(FRAME_LINE), U, minimum=1))])
    backing = vector(f"{ident}-backing", {**box(left, top, width, height), **NO_POINTER},
                     [path("fill", WHOLE, fill=solid(PANEL_FILL)), path("border", EDGE, stroke=stroke(solid(PANEL_BORDER), U, minimum=1))])
    body = group(f"{ident}-body", box(left, top, width, height), content)
    return group(ident, {**absolute(left=0, top=0, width=CANVAS_W, height=0), "display": keyword("none")}, [link, frame, backing, body])


def row_label(ident: str, key: str, centre: float, tint: list = TEXT) -> dict:
    """A row's label (section 10.13): Bank 0.25, right-aligned to the gutter
    at x 120."""
    return label(ident, key, {**box(4, centre - 8, 116, 16), **typeface(FACE_BANK, 0.25, 16, tint, "right"), **NO_POINTER})


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
    text_node = label(f"{ident}-label", key, {**FULL, **typeface(FACE_BANK, 0.25, 17, TAB_TEXT, "right"), **NO_POINTER})
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


def exit_panel(doc: Document) -> dict:
    """The Exit panel (378, 39, 132 x 58 u): three text links."""
    content = [text_link(doc, "mp_return", "#str_04152", 2, "mpClose"), text_link(doc, "mp_disconnect", "#str_04153", 20, "mpDisconnect"),
               text_link(doc, "mp_quit", "#str_04154", 38, "quit")]
    return panel("mp-exit", 472, 43, (378, 39, 132, 58), content, leading_frame=True)


def multiplayer_menu_document() -> dict:
    """The in-game multiplayer menu's card: the tab strip, the Main and Exit
    panels, and the hint line breathing at the bottom. The other tabs hand
    off to the stock menu's pages."""
    doc = Document("opend3.mpescape")
    doc.state.update({
        "mp.shown": {"type": "boolean", "initial": False}, "mp.tab": {"type": "number", "initial": 0},
        "card.stock_page": {"type": "number", "initial": -1},
        "mp.warmup": {"type": "boolean", "initial": False}, "mp.ready_text": {"type": "string", "initial": ""},
        "mp.spec_text": {"type": "string", "initial": ""}, "mp.teams": {"type": "boolean", "initial": False},
        "mp.team": {"type": "number", "initial": 0}, "mp.vote": {"type": "boolean", "initial": False},
        "mp.say": {"type": "string", "initial": ""}, "mp.chat": {"type": "string", "initial": ""},
        # The adapter keeps this: the chat field holds text not yet entered.
        "ui.numberDraftsPending": {"type": "boolean", "initial": False},
    })
    for verb in ("mpClose", "mpDisconnect", "quit", "mpStockPage", "mpReady", "mpSpectate", "mpTeamToggle", "mpVoteYes", "mpVoteNo", "mpChat",
                 "mpChatMode", "mpClick"):
        doc.session(verb)
    tabs = [tab(doc, *entry) for entry in TABS]
    panels = []
    for node, index in ((main_panel(doc), 0), (exit_panel(doc), 6)):
        doc.bind(f"{node['id']}.display", node["id"], "display", {"op": "select", "args": [{"op": "==", "args": [{"state": "mp.tab"}, index]}, "block", "none"]})
        panels.append(node)
    hint = label("mp-hint", "#str_04156", {**box(12, 425, 256, 30), **typeface(FACE_BANK, 0.25, 30, TEXT), **NO_POINTER, "opacity": number(1)})
    doc.timeline("mpHint", 2000, [track("mp-hint", "opacity", [(0, number(1)), (1000, number(0.4)), (2000, number(1))])], iterations=0)
    canvas = group("canvas", {**absolute(top=0, width=CANVAS_W, height=0), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)},
                   [*strip(), *tabs, *panels, hint])
    stage = group("stage", {**FULL, "display": keyword("none")}, [canvas])
    doc.bind("stage.display", "stage", "display", {"op": "select", "args": [{"state": "mp.shown"}, "block", "none"]})
    # The session raises `open` as the card covers the game's menu and
    # `release` as the menu closes.
    doc.events["open"] = [{"op": "setState", "values": {"mp.shown": True, "mp.tab": 0}}, {"op": "playTimeline", "timeline": "mpHint"}]
    doc.events["release"] = [{"op": "setState", "values": {"mp.shown": False}}]
    doc.events["onBack"] = [{"op": "action", "action": "mpClose"}]
    root = group("screen", {**FULL, "font-family": font(FACE_DEFAULT), "font-size": length(18), "color": colour([1, 1, 1, 1])}, [stage])
    return doc.build(root)
