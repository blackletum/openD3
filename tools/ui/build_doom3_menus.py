#!/usr/bin/env python3
"""Build openD3's retained Doom 3 menus.

The documents are the vector replacement of Doom 3's front end that
docs/dev/ui-visual-design.md specifies, in the Remastered layout of its
section 3. docs/dev/ui/retained-menus.md records what each one covers and how
the session presents it. They draw furniture only: the stock menu keeps
drawing the scene behind them (space, the stars, the planet and its halo, the
scan lines and the grid), from the player's own installation.

The generated files are canonical sources. Re-run this script after editing
it or doom3_menu_kit.py; do not hand-edit its outputs.

    python tools/ui/build_doom3_menus.py [--check]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from doom3_menu_kit import (
    CANVAS_H, CANVAS_W, DECEL, FACE_BANK, FACE_DEFAULT, FULL, NO_POINTER, U, Document, absolute, box, colour,
    dialog, edge_glow, font, footer_link, group, keyword, label, lead, length, menu_item, mid, nav_button, number,
    path, picture, render, solid, stroke, token, track, trail, transform, typeface, vector, walk,
)

from doom3_menu_credits import credits_document, mods_panel
from doom3_menu_death import death_document
from doom3_menu_loading import loading_document
from doom3_menu_mpmenu import multiplayer_menu_document
from doom3_menu_multiplayer import create_server_document, join_game_document, mp_settings_panel
from doom3_menu_options import controls_document, game_options_document
from doom3_menu_pages import FIRST_PLACE, SECOND_PLACE, load_game_document, save_game_document
from doom3_menu_system import system_document

ROOT = Path(__file__).resolve().parents[2]
PAK0 = ROOT / "content" / "baseod3" / "pak0"
OUTPUTS = {
    "title": PAK0 / "guis" / "menu" / "title.rui",
    "pause": PAK0 / "guis" / "menu" / "pause.rui",
    "msgbox": PAK0 / "guis" / "menu" / "msgbox.rui",
    "loadgame": PAK0 / "guis" / "menu" / "loadgame.rui",
    "savegame": PAK0 / "guis" / "menu" / "savegame.rui",
    "controls": PAK0 / "guis" / "menu" / "settings" / "controls.rui",
    "game": PAK0 / "guis" / "menu" / "settings" / "game.rui",
    "system": PAK0 / "guis" / "menu" / "settings" / "system.rui",
    "credits": PAK0 / "guis" / "menu" / "credits.rui",
    "joingame": PAK0 / "guis" / "menu" / "joingame.rui",
    "createserver": PAK0 / "guis" / "menu" / "createserver.rui",
    "restartmenu": PAK0 / "guis" / "menu" / "restartmenu.rui",
    "loading": PAK0 / "guis" / "loading" / "loading.rui",
    "mp_escape": PAK0 / "guis" / "menu" / "mp_escape.rui",
}

# Stock strings (strings/english.lang in the installation).
STR = {
    "newgame": "#str_02207", "newgame.hint": "#str_02209", "newgame.close": "#str_02208",
    "savegame": "#str_02179", "savegame.hint": "#str_02211",
    "loadgame": "#str_02187", "loadgame.hint": "#str_02213",
    "multiplayer": "#str_00253", "multiplayer.hint": "#str_02215",
    "quitgame": "#str_02216", "quitgame.hint": "#str_02217", "quitgame.body": "#str_04145", "quitgame.no.hint": "#str_04146",
    "options": "#str_00186", "options.hint": "#str_02206", "options.close": "#str_02205",
    "opt.controls": "#str_02164", "opt.controls.hint": "#str_02166", "opt.game": "#str_02129", "opt.game.hint": "#str_02168",
    "mp.browser": "#str_02198", "mp.browser.hint": "#str_02199", "mp.create": "#str_02200", "mp.create.hint": "#str_02201",
    "mp.settings": "#str_04100", "mp.close": "#str_02214",
    "opt.system": "#str_00167", "opt.system.hint": "#str_02170", "opt.defaults": "#str_04086", "opt.defaults.hint": "#str_04087",
    "mods": "#str_04098", "mods.hint": "#str_04108",
    "updates": "#str_04837", "updates.hint": "#str_04838",
    "credits": "#str_02218", "credits.hint": "#str_02219",
    "exit": "#str_01248", "exit.hint": "#str_01976", "exit.title": "#str_01975", "exit.body": "#str_02337", "exit.yes.hint": "#str_01994",
    "resume": "#str_04106", "resume.hint": "#str_04107",
    "yes": "#str_02308", "no": "#str_04144",
    "difficulty": "#str_04088",
    "skill0": "#str_04089", "skill0.hint": "#str_04090",
    "skill1": "#str_04091", "skill1.hint": "#str_04092",
    "skill2": "#str_04093", "skill2.hint": "#str_04094",
    "skill3": "#str_04095", "skill3.hint": "#str_04097", "skill3.locked": "#str_04096",
}

LOGO = "guis/assets/mainmenu/doom3"   # the stock logo bitmap (a bitmap exception, section 6)


# ----------------------------------------------------------------- the frame

def frame() -> dict:
    """Section 6.8's frame pieces in the Remastered layout (section 9.11):
    the top bar from the leading edge to the flare at the top-trailing
    corner; the bottom strips to both edges with their step at its stock
    distance from the trailing edge; the second band likewise. Each band is
    one polygon in its own colour, and only the flare's boundary is stroked."""
    bar, strip, band = "chrome.bar", "chrome.strip", "chrome.band"
    paths = [
        # Top bar: a 12 u band at 60 % of the colour over a 4 u line at 100 %.
        path("bar-band", [(lead(0), U * -1), (trail(542), U * -1), (trail(542), U * 11), (lead(0), U * 11)],
             fill=solid(token(bar, 0.12))),
        path("bar-line", [(lead(0), U * 11), (trail(542), U * 11), (trail(542), U * 15), (lead(0), U * 15)],
             fill=solid(token(bar))),
        # The flare: the bar continued, widening toward the trailing edge
        # along a concave arc and a 45 degree run, about 37 u deep at the edge.
        path("flare", [(trail(542), U * -1), (trail(640), U * -1), (trail(640), U * 37), (trail(629), U * 27),
                       ("q", (trail(614), U * 16), (trail(594), U * 15)), (trail(542), U * 15)],
             fill=solid(token(bar, 0.12))),
        path("flare-line", [(trail(542), U * 13), (trail(594), U * 13), ("q", (trail(614), U * 14), (trail(629), U * 25.5)),
                            (trail(640), U * 35.5)], closed=False, stroke=stroke(solid(token(bar)), U * 3, minimum=1)),
        # Bottom strips: 12 u at the leading side, 29 u at the trailing side.
        path("strip", [(lead(0), U * 468), (trail(371), U * 468), (trail(388), U * 451), (trail(640), U * 451),
                       (trail(640), U * 480), (lead(0), U * 480)], fill=solid(token(strip))),
        path("strip-chamfer", [(lead(0), U * 447), (lead(20), U * 468), (lead(0), U * 468)], fill=solid(token(strip))),
        # Second band: 24 u tall under the nav buttons, 7 u toward the trailing edge.
        path("band", [(lead(187), U * 464), (lead(209), U * 440), (trail(640), U * 440), (trail(640), U * 447),
                      (trail(396), U * 447), (trail(379), U * 464)], fill=solid(token(band))),
    ]
    return vector("frame", {**FULL, **NO_POINTER}, paths)


def options_list(doc: Document) -> dict:
    """Section 9.3: OPTIONS' sub-list, grown from the stub above the tab into
    a plate in chrome.fill.open at 3, 351, 132 x 89 u, with four sub-menu
    items at a 20 u pitch: CONTROLS, GAME OPTIONS, SYSTEM and DEFAULTS. It
    stays at the leading edge with the tab (section 3).

    Section 8.4 (AnimMainToOptions): the first nav button narrows aside over
    200 ms, accel(0.4, 0.6), the plate grows upward over 200 ms as a flash
    that settles, and the items arrive from 280 ms, 50 ms apart. Closing has
    no stagger."""
    doc.state["opt.open"] = {"type": "boolean", "initial": False}
    height = U * 89
    shape = [(U * 7, 0), (U * 130, 0), (U * 132, U * 2), (U * 132, height), (0, height), (0, U * 7)]
    tab = vector("opt-tab", {**FULL, **NO_POINTER, "transform": transform()}, [path("tab", shape, fill=solid(token("chrome.fill.open")))])
    tab_flash = vector("opt-tab-flash", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("tab", shape, fill=solid([1, 1, 1, 1]))])
    enter = [track("opt-tab", "transform", [(0, transform(ty=height / 2, sy=0.02), DECEL), (200, transform()), (700, transform())]),
             track("opt-tab-flash", "opacity", [(0, number(0.7)), (50, number(0.5)), (300, number(0)), (700, number(0))]),
             track("nav_first", "left", [(0, length(U * 27)), (200, length(U * 137)), (700, length(U * 137))])]
    rows = []
    for row, (ident, name) in enumerate((("opt_controls", "controls"), ("opt_game", "game"), ("opt_system", "system"), ("opt_defaults", "defaults"))):
        request = {"controls": "optionsControls", "game": "optionsGame", "system": "optionsSystem", "defaults": "optionsDefaults"}[name]
        item = menu_item(doc, ident, STR[f"opt.{name}"], absolute(left=0, top=0), 124, action=doc.session(request), hint=STR[f"opt.{name}.hint"],
                         inset=4)
        flash = vector(f"{ident}-arrive", {**FULL, **NO_POINTER, "opacity": number(0)},
                       [path("flash", [(0, 0), (U * 119, 0), (U * 124, U * 5), (U * 124, U * 19), (0, U * 19)], fill=solid([1, 1, 1, 1]))])
        rows.append(group(f"{ident}-row", {**box(2, 2 + 20 * row, 124, 19), "opacity": number(1)}, [item, flash]))
        at = 280 + 50 * row
        enter.append(track(f"{ident}-row", "opacity", [(0, number(0)), (at - 1, number(0)), (at, number(1)), (700, number(1))]))
        enter.append(track(f"{ident}-arrive", "opacity", [(0, number(0)), (at - 1, number(0)), (at, number(0.7)), (at + 50, number(0.4)),
                                                         (at + 250, number(0))]))
    doc.timeline("optEnter", 700, enter)
    doc.timeline("optLeave", 200, [track("nav_first", "left", [(0, length(U * 137)), (200, length(U * 27))])])
    node = group("opt-list", {**box(3, 351, 132, 89), "display": keyword("none")}, [tab, tab_flash, *rows])
    doc.bind("opt-list.display", "opt-list", "display", {"op": "select", "args": [{"state": "opt.open"}, "block", "none"]})
    doc.session("soundForward")
    doc.session("soundBack")
    doc.events["optionsOpen"] = [{"op": "setState", "values": {"opt.open": True}}, {"op": "action", "action": "soundForward"},
                                 {"op": "playTimeline", "timeline": "optEnter"}, {"op": "focus", "control": "opt_controls"}]
    doc.events["optionsClose"] = [{"op": "if", "condition": {"state": "opt.open"},
                                   "then": [{"op": "setState", "values": {"opt.open": False}}, {"op": "action", "action": "soundBack"},
                                            {"op": "playTimeline", "timeline": "optLeave"}, {"op": "focus", "control": "nav_options"}]}]
    doc.events["optionsToggle"] = [{"op": "if", "condition": {"state": "opt.open"},
                                    "then": [{"op": "call", "event": "optionsClose"}], "else": [{"op": "call", "event": "optionsOpen"}]}]
    return node


def multiplayer_list(doc: Document) -> dict:
    """Section 9.6: MULTIPLAYER's sub-list, three sub-menu items rising above
    the button at the trailing edge (section 3): FIND MULTIPLAYER GAME, CREATE
    SERVER and MULTIPLAYER SETTINGS, on a plate in chrome.fill.open. It opens
    as the other lists do: the plate grows upward as a flash that settles and
    the items arrive 50 ms apart."""
    doc.state["mp.open"] = {"type": "boolean", "initial": False}
    height = U * 65
    shape = [(U * 7, 0), (U * 214, 0), (U * 216, U * 2), (U * 216, height), (0, height), (0, U * 7)]
    tab = vector("mp-tab", {**FULL, **NO_POINTER, "transform": transform()}, [path("tab", shape, fill=solid(token("chrome.fill.open")))])
    tab_flash = vector("mp-tab-flash", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("tab", shape, fill=solid([1, 1, 1, 1]))])
    enter = [track("mp-tab", "transform", [(0, transform(ty=height / 2, sy=0.02), DECEL), (200, transform()), (700, transform())]),
             track("mp-tab-flash", "opacity", [(0, number(0.7)), (50, number(0.5)), (300, number(0)), (700, number(0))])]
    rows = []
    for row, (ident, name, request, hint) in enumerate((("mp_browser", "browser", "mpBrowser", STR["mp.browser.hint"]),
                                                        ("mp_create", "create", "mpCreate", STR["mp.create.hint"]),
                                                        ("mp_settings", "settings", "mpSettings", None))):
        item = menu_item(doc, ident, STR[f"mp.{name}"], absolute(left=0, top=0), 208, action=doc.session(request), hint=hint, inset=6)
        flash = vector(f"{ident}-arrive", {**FULL, **NO_POINTER, "opacity": number(0)},
                       [path("flash", [(0, 0), (U * 203, 0), (U * 208, U * 5), (U * 208, U * 19), (0, U * 19)], fill=solid([1, 1, 1, 1]))])
        rows.append(group(f"{ident}-row", {**box(4, 3 + 20 * row, 208, 19), "opacity": number(1)}, [item, flash]))
        at = 280 + 50 * row
        enter.append(track(f"{ident}-row", "opacity", [(0, number(0)), (at - 1, number(0)), (at, number(1)), (700, number(1))]))
        enter.append(track(f"{ident}-arrive", "opacity", [(0, number(0)), (at - 1, number(0)), (at, number(0.7)), (at + 50, number(0.4)),
                                                         (at + 250, number(0))]))
    doc.timeline("mpEnter", 700, enter)
    node = group("mp-list", {**absolute(right=U * 6, top=U * 350, width=U * 216, height=U * 65), "display": keyword("none")}, [tab, tab_flash, *rows])
    doc.bind("mp-list.display", "mp-list", "display", {"op": "select", "args": [{"state": "mp.open"}, "block", "none"]})
    doc.events["mpOpen"] = [{"op": "if", "condition": {"state": "opt.open"}, "then": [{"op": "playTimeline", "timeline": "optLeave"}]},
                            {"op": "setState", "values": {"mp.open": True, "opt.open": False, "ng.open": False}},
                            {"op": "action", "action": "soundForward"}, {"op": "playTimeline", "timeline": "mpEnter"},
                            {"op": "focus", "control": "mp_browser"}]
    doc.events["mpClose"] = [{"op": "if", "condition": {"state": "mp.open"},
                              "then": [{"op": "setState", "values": {"mp.open": False}}, {"op": "action", "action": "soundBack"},
                                       {"op": "focus", "control": "nav_third"}]}]
    doc.events["mpToggle"] = [{"op": "if", "condition": {"state": "mp.open"},
                               "then": [{"op": "call", "event": "mpClose"}], "else": [{"op": "call", "event": "mpOpen"}]}]
    return node


def options_tab(doc: Document, action: str) -> dict:
    """Section 6.8's OPTIONS tab and the stub above it, at the bottom-leading
    corner: a trapezoid 24 u tall with 45 degree ends in chrome.tab. Section
    7.1: the label goes to white in 100 ms and the body to 35 % in 300 ms;
    release takes 200 and 300 ms; a press dips the label."""
    ident = "nav_options"
    rise = 36.0   # u: the stub stands this far above the tab, in the body's own node
    shape = [
        path("tab", [(U * 2, U * rise), (U * 192, U * rise), (U * 169, U * (rise + 24)), (U * 22, U * (rise + 24)), (U * 2, U * (rise + 4))],
             fill=solid(token("chrome.tab", 1.0))),
        path("stub", [(U * 2, U * rise), (U * 2, U * (rise - 30)), (U * 4, U * (rise - 32)), (U * 25, U * (rise - 32)),
                      (U * 29, U * (rise - 28)), (U * 29, U * (rise - 16)), (U * 45, U * rise)], fill=solid(token("chrome.tab", 1.0))),
    ]
    body = vector(f"{ident}-body", {**absolute(left=0, top=-U * rise, height=U * (rise + 24)), "width": length(100, "%"), **NO_POINTER,
                                    "opacity": number(0.2)}, shape)
    text_node = label(f"{ident}-label", STR["options"], {**absolute(left=0, top=U * 1.5, height=U * 21), "width": length(100, "%"),
                                                          **typeface(FACE_DEFAULT, 0.26, 21, token("text.link"), "center"), **NO_POINTER})
    ids = doc.states(ident, [
        (f"{ident}-body", "opacity", {"default": number(0.2), "hover": number(0.35)}, 300, 300),
        (f"{ident}-label", "color", {"default": colour(token("text.link")), "hover": colour(token("text.active")),
                                     "pressed": colour(token("text.press"))}, 100, 200),
    ])
    from doom3_menu_kit import control
    return group(ident, box(1, 440, 196, 24), [body, text_node],
                 control=control(doc, STR["options"], ids, event=action, hint=STR["options.hint"]))


# --------------------------------------------------------------- the new game list

LIST_ROWS = 4


def new_game_list(doc: Document) -> dict:
    """Section 9.4: the difficulty list rises out of NEW GAME. A tab in
    chrome.fill.open with a 7 u chamfer on its top-leading corner and a 2 u
    one on its top-trailing corner (section 6.1) holds a caption (Bank 0.25)
    and four sub-menu items at a 20 u pitch. There is no page plate: the
    scene stays visible. Nightmare stays locked, in text.dim, until the game
    unlocks it (g_nightmare). The list keeps its stock offsets from the
    leading edge, with the button that owns it (section 3).

    Section 8.4 (AnimMainToNG): the tab unfolds upward from the band in 300
    ms, accel(0.2, 0.8), born as a white flash that settles in 50 + 200 ms;
    the items arrive from 280 ms, 50 ms apart, each as a flash. Closing has no
    stagger."""
    doc.state["ng.open"] = {"type": "boolean", "initial": False}
    doc.state["nightmare"] = {"type": "boolean", "initial": False, "cvar": "g_nightmare"}
    height = U * 97   # 318 to 415 u
    tab_shape = [(U * 7, 0), (U * 177, 0), (U * 179, U * 2), (U * 179, height), (0, height), (0, U * 7)]
    tab = vector("ng-tab", {**FULL, **NO_POINTER, "transform": transform()}, [path("tab", tab_shape, fill=solid(token("chrome.fill.open")))])
    tab_flash = vector("ng-tab-flash", {**FULL, **NO_POINTER, "opacity": number(0)}, [path("tab", tab_shape, fill=solid([1, 1, 1, 1]))])
    caption = label("ng-caption", STR["difficulty"], {**box(2, 1, 170, 13), **typeface(FACE_BANK, 0.25, 13, token("text.dim")),
                                                      **NO_POINTER, "opacity": number(1)})
    rows = []
    specs = [("ng_skill0", STR["skill0"], "newGame0", STR["skill0.hint"], False),
             ("ng_skill1", STR["skill1"], "newGame1", STR["skill1.hint"], False),
             ("ng_skill2", STR["skill2"], "newGame2", STR["skill2.hint"], False),
             ("ng_skill3", STR["skill3"], "newGame3", STR["skill3.hint"], False),
             ("ng_skill3_locked", STR["skill3"], "newGame3", STR["skill3.locked"], True)]
    enter = [track("ng-tab", "transform", [(0, transform(ty=height / 2, sy=0.02), DECEL), (300, transform())]),
             track("ng-tab-flash", "opacity", [(0, number(0.7)), (50, number(0.5)), (300, number(0)), (700, number(0))]),
             track("ng-caption", "opacity", [(0, number(0)), (279, number(0)), (280, number(1)), (700, number(1))])]
    for index, (ident, key, action, hint, locked) in enumerate(specs):
        row = min(index, LIST_ROWS - 1)
        item = menu_item(doc, ident, key, absolute(left=0, top=0), 171, action=doc.session(action), hint=hint, locked=locked)
        flash = vector(f"{ident}-arrive", {**FULL, **NO_POINTER, "opacity": number(0)},
                       [path("flash", [(0, 0), (U * 166, 0), (U * 171, U * 5), (U * 171, U * 19), (0, U * 19)], fill=solid([1, 1, 1, 1]))])
        holder = group(f"{ident}-row", {**box(0, 17 + 20 * row, 171, 19), "opacity": number(1), "display": keyword("block")}, [item, flash])
        at = 280 + 50 * row
        enter.append(track(f"{ident}-row", "opacity", [(0, number(0)), (at - 1, number(0)), (at, number(1)), (700, number(1))]))
        enter.append(track(f"{ident}-arrive", "opacity", [(0, number(0)), (at - 1, number(0)), (at, number(0.7)), (at + 50, number(0.4)),
                                                         (at + 250, number(0))]))
        rows.append(holder)
    doc.bind("ng_skill3-row.display", "ng_skill3-row", "display", {"op": "select", "args": [{"state": "nightmare"}, "block", "none"]})
    doc.bind("ng_skill3_locked-row.display", "ng_skill3_locked-row", "display", {"op": "select", "args": [{"state": "nightmare"}, "none", "block"]})
    doc.timeline("ngEnter", 700, enter)
    node = group("ng-list", {**box(34, 318, 179, 97), "display": keyword("none")}, [tab, tab_flash, caption, *rows])
    doc.bind("ng-list.display", "ng-list", "display", {"op": "select", "args": [{"state": "ng.open"}, "block", "none"]})
    doc.session("soundForward")
    doc.session("soundBack")
    doc.events["newGameOpen"] = [{"op": "setState", "values": {"ng.open": True}}, {"op": "action", "action": "soundForward"},
                                 {"op": "playTimeline", "timeline": "ngEnter"}, {"op": "focus", "control": "ng_skill1"}]
    doc.events["newGameClose"] = [{"op": "if", "condition": {"state": "ng.open"},
                                   "then": [{"op": "setState", "values": {"ng.open": False}}, {"op": "action", "action": "soundBack"},
                                            {"op": "focus", "control": "nav_first"}]}]
    doc.events["newGameToggle"] = [{"op": "if", "condition": {"state": "ng.open"},
                                    "then": [{"op": "call", "event": "newGameClose"}], "else": [{"op": "call", "event": "newGameOpen"}]}]
    return node


# ------------------------------------------------------------------ the home

def home_document(pause: bool) -> dict:
    """The title screen (section 9.2), or the single-player pause variant of
    it (section 9.10): the frame, the logo, the nav band of three interlocking
    parallelograms, the OPTIONS tab, the footer links and the hint line, with
    the exit dialog (and, paused, the quit-game dialog) over them.

    The session's requests: newGame0 to newGame3, loadGame, saveGame,
    multiplayer, settings, mods, updates, credits, resume, quitToMenu, quit.
    Its events: open, returnHome, depart, release."""
    doc = Document("opend3.pause" if pause else "opend3.title")
    for request in ("loadGame", "settings", "quit"):
        doc.session(request)

    # Nav band (section 6.3). NEW GAME lengthens to the leading edge and
    # MULTIPLAYER to the trailing edge; LOAD GAME keeps its canvas place.
    # A page draws its owning button again as the way back, so each button
    # carries an opacity the hand-off can take away.
    first_place = {**FIRST_PLACE, "opacity": number(1)}
    third_place = absolute(left=U * (409 - 320), right=U * 1, top=U * 410, height=U * 32)
    if pause:
        first = nav_button(doc, "nav_first", STR["savegame"], first_place, action=doc.session("saveGame"), hint=STR["savegame.hint"])
        third = nav_button(doc, "nav_third", STR["quitgame"], third_place, event="quitGameAsk", hint=STR["quitgame.hint"])
    else:
        first = nav_button(doc, "nav_first", STR["newgame"], first_place, event="newGameToggle", hint=STR["newgame.hint"])
        third = nav_button(doc, "nav_third", STR["multiplayer"], third_place, event="mpToggle", hint=STR["multiplayer.hint"])
    second = nav_button(doc, "nav_second", STR["loadgame"], {**SECOND_PLACE, "opacity": number(1)}, action="loadGame", hint=STR["loadgame.hint"])

    # Footer links (section 9.2), anchored to the bottom-trailing corner.
    def link(ident, key, x, w, **how):
        return footer_link(doc, ident, key, absolute(right=U * (640 - x - w), top=U * 454, width=U * w, height=U * 22), **how)
    if pause:
        links = [link("link_resume", STR["resume"], 420, 140, action=doc.session("resume"), hint=STR["resume.hint"])]
    else:
        links = [link("link_mods", STR["mods"], 384, 50, action=doc.session("mods"), hint=STR["mods.hint"]),
                 link("link_updates", STR["updates"], 441, 73, action=doc.session("updates"), hint=STR["updates.hint"]),
                 link("link_credits", STR["credits"], 522, 65, action=doc.session("credits"), hint=STR["credits.hint"])]
    links.append(link("link_exit", STR["exit"], 594, 40, event="exitAsk", hint=STR["exit.hint"]))

    leading = [first, options_tab(doc, "optionsToggle"), options_list(doc)]
    if not pause:
        leading.append(new_game_list(doc))
        # The two lists share the corner: one opens as the other closes.
        doc.events["newGameOpen"][0:0] = [{"op": "if", "condition": {"state": "opt.open"},
                                           "then": [{"op": "setState", "values": {"opt.open": False}},
                                                    {"op": "playTimeline", "timeline": "optLeave"}]}]
        doc.events["optionsOpen"][0:0] = [{"op": "setState", "values": {"ng.open": False}}]
        trailing_list = multiplayer_list(doc)
        # One list at a time: opening another closes MULTIPLAYER's.
        doc.events["newGameOpen"][0:0] = [{"op": "setState", "values": {"mp.open": False}}]
        doc.events["optionsOpen"][0:0] = [{"op": "setState", "values": {"mp.open": False}}]
    # Zero-height holders carry the anchors: their own boxes take no pointer.
    lead_side = group("lead-side", {**absolute(left=0, top=0, height=0), "width": length(50, "%")}, leading)
    canvas = group("canvas", {**absolute(top=0, width=CANVAS_W, height=0), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)}, [
        picture("logo", LOGO, {**box(212, 155, 256, 128), **NO_POINTER, "image-color": colour([1, 1, 1, 1]), "opacity": number(1)}),
        second,
    ])
    trail_side = group("trail-side", {**absolute(top=0, height=0), "left": length(50, "%"), "width": length(50, "%")},
                       [third, *links, *([] if pause else [trailing_list])])

    # Dialogs (section 6.10): focus opens on the choice that changes nothing.
    doc.session("soundForward")
    doc.session("soundBack")
    exit_modal = dialog(doc, "exitModal", STR["exit.title"], STR["exit.body"], [
        ("exit_yes", STR["yes"], 61, "quit", None, STR["exit.yes.hint"]),
        ("exit_no", STR["no"], 210, None, "exitCancel", None)], initial="exit_no", back="exitCancel")
    doc.events["exitAsk"] = [{"op": "action", "action": "soundForward"}, {"op": "call", "event": "exitModalShow"}]
    doc.events["exitCancel"] = [{"op": "action", "action": "soundBack"}, {"op": "call", "event": "exitModalHide"}]
    modals = [exit_modal]
    if not pause:
        # MODS opens the session's mods dialog, drawn as the stock Mods page.
        modals.append(mods_panel(doc))
        # MULTIPLAYER SETTINGS is a panel of the title, as the stock page is.
        modals.append(mp_settings_panel(doc))
    if pause:
        doc.session("quitToMenu")
        modals.append(dialog(doc, "quitGameModal", STR["quitgame"], STR["quitgame.body"], [
            ("quitgame_yes", STR["yes"], 61, "quitToMenu", None, STR["quitgame.hint"]),
            ("quitgame_no", STR["no"], 210, None, "quitGameCancel", STR["quitgame.no.hint"])], initial="quitgame_no", back="quitGameCancel"))
        doc.events["quitGameAsk"] = [{"op": "action", "action": "soundForward"}, {"op": "call", "event": "quitGameModalShow"}]
        doc.events["quitGameCancel"] = [{"op": "action", "action": "soundBack"}, {"op": "call", "event": "quitGameModalHide"}]
        # Back on the pause closes the options list, or returns to the game
        # (section 9.10).
        doc.events["onBack"] = [{"op": "if", "condition": {"state": "opt.open"}, "then": [{"op": "call", "event": "optionsClose"}],
                                 "else": [{"op": "action", "action": "resume"}]}]
    else:
        # Back on the title closes an open list, or asks to exit.
        doc.events["onBack"] = [{"op": "if", "condition": {"state": "ng.open"}, "then": [{"op": "call", "event": "newGameClose"}],
                                 "else": [{"op": "if", "condition": {"state": "opt.open"}, "then": [{"op": "call", "event": "optionsClose"}],
                                           "else": [{"op": "if", "condition": {"state": "mp.open"}, "then": [{"op": "call", "event": "mpClose"}],
                                                     "else": [{"op": "call", "event": "exitAsk"}]}]}]}]

    hint = doc.hint_line()
    stage = group("stage", {**absolute(left=0), "width": length(100, "%"), "height": length(CANVAS_H), "top": length(50, "%"),
                            "margin-top": length(-CANVAS_H / 2)}, [frame(), canvas, lead_side, trail_side, hint])
    furniture = group("furniture", {**FULL, "opacity": number(0)}, [stage])
    glow = edge_glow(doc)
    root = group("screen", {**FULL, "font-family": font(FACE_DEFAULT), "font-size": length(18), "color": colour([1, 1, 1, 1])},
                 [furniture, glow, *modals])

    # Section 8.5: the logo shimmers between 90 and 100 % on a 4 s period.
    doc.timeline("logoShimmer", 4000, [track("logo", "image-color", [(0, colour([1, 1, 1, 1])), (2000, colour([0.9, 0.9, 0.9, 1])),
                                                                     (4000, colour([1, 1, 1, 1]))])], iterations=0)
    # Section 8.3: the frame and the nav band are revealed already built as
    # the stock menu's black fades out, from 500 ms over 1000 ms. Paused in a
    # game the menu is there at once.
    if pause:
        doc.timeline("open", 50, [track("furniture", "opacity", [(0, number(1)), (50, number(1))]),
                                  track("logo", "opacity", [(0, number(1)), (50, number(1))])])
    else:
        doc.timeline("open", 1500, [track("furniture", "opacity", [(0, number(0)), (500, number(0)), (1500, number(1))]),
                                    track("logo", "opacity", [(0, number(1)), (1500, number(1))])])
    # Back from a page: the furniture is in place, the nav buttons and the
    # hint line are the home's again, and the logo returns in 600 ms.
    doc.timeline("returnHome", 600, [track("furniture", "opacity", [(0, number(1)), (50, number(1)), (600, number(1))]),
                                     track("logo", "opacity", [(0, number(0)), (600, number(1))]),
                                     track("nav_first", "opacity", [(0, number(1)), (50, number(1))]),
                                     track("nav_second", "opacity", [(0, number(1)), (50, number(1))]),
                                     track("hint-line", "opacity", [(0, number(1)), (50, number(1))])])
    # A page opens: the logo is hidden while any page plate is open (section
    # 8.4), and the page shows its own hints.
    doc.timeline("depart", 600, [track("logo", "opacity", [(0, number(1)), (600, number(0))]),
                                 track("hint-line", "opacity", [(0, number(0)), (50, number(0)), (600, number(0))])])
    # The page presents 50 ms after the choice and draws the button that
    # opened it itself, as the way back.
    # Credits take the whole screen: the menu's furniture leaves for them.
    doc.timeline("carry_credits", 250, [track("furniture", "opacity", [(0, number(1)), (250, number(0))])])
    doc.events["carry_credits"] = [{"op": "playTimeline", "timeline": "carry_credits"}]
    for request, button in (("loadGame", "nav_second"), ("saveGame", "nav_first")):
        doc.timeline(f"carry_{request}", 50, [track(button, "opacity", [(0, number(1)), (49, number(1)), (50, number(0))])])
        doc.events[f"carry_{request}"] = [{"op": "playTimeline", "timeline": f"carry_{request}"}]
    # Returning to the game closes the menu at once.
    doc.timeline("release", 50, [track("furniture", "opacity", [(0, number(0)), (50, number(0))]),
                                 track("edge-glow", "opacity", [(0, number(0)), (50, number(0))])])
    ambient = [{"op": "playTimeline", "timeline": "logoShimmer"}, {"op": "playTimeline", "timeline": "edgeGlow"}]
    doc.events["open"] = [{"op": "playTimeline", "timeline": "open"}, *ambient]
    doc.events["returnHome"] = [{"op": "playTimeline", "timeline": "returnHome"}, *ambient]
    doc.events["depart"] = [{"op": "playTimeline", "timeline": "depart"}]
    doc.events["release"] = [{"op": "playTimeline", "timeline": "release"}]
    if not pause:
        doc.events["open"].insert(0, {"op": "setState", "values": {"ng.open": False}})
    return doc.build(root)


# ------------------------------------------------------------ the message box

def message_box_document() -> dict:
    """The engine's message box (section 9.9, the stock guis/msg.gui): the
    dialog shell of section 6.10 at the same place, over a 70 % dim, with no
    open animation. The session fills it through the stock box's own state
    and reads the button back as a command (idSessionLocal::MessageBox,
    HandleMsgCommands):

        title, message                              the texts, already localized
        visible_msgbox, visible_waitbox             a box with buttons, or a wait
        visible_left, visible_right, left, right    two buttons and their labels
        visible_mid, mid                            the lone button and its label

    It answers with the session verbs msgLeft, msgRight and msgMid. The
    buttons stand at plate x 60, 135 and 210. A wait box has a title and no
    buttons. Back answers as the trailing button, or the lone one. The entry
    prompt, the CD key box and the download box keep the stock screen."""
    doc = Document("opend3.msgbox")
    for name in ("title", "message", "left", "right", "mid", "str_entry"):
        doc.state[name] = {"type": "string", "initial": ""}
    for name in ("visible_msgbox", "visible_waitbox", "visible_left", "visible_right", "visible_mid", "visible_entry"):
        doc.state[name] = {"type": "boolean", "initial": False}
    for verb in ("msgLeft", "msgRight", "msgMid"):
        doc.session(verb)
    placeholder = "#str_04339"   # OK: the session supplies every text here
    modal = dialog(doc, "msg", placeholder, placeholder, [
        ("msg_left", placeholder, 61, None, "msgPickLeft", None),
        ("msg_mid", placeholder, 135, None, "msgPickMid", None),
        ("msg_right", placeholder, 210, None, "msgPickRight", None)], initial="msg_right", back="msgPickRight",
        animate=False, dim_alpha=0.7, body_lines=64.0)
    nodes = {node["id"]: node for node in walk(modal)}
    doc.bind("msg-title.text", "msg-title", "text", {"state": "title"})
    doc.bind("msg-body.text", "msg-body", "text", {"state": "message"})
    for button, shown, text_state in (("msg_left", "visible_left", "left"), ("msg_right", "visible_right", "right"),
                                      ("msg_mid", "visible_mid", "mid")):
        nodes[button]["properties"]["display"] = keyword("none")
        doc.bind(f"{button}.display", button, "display", {"op": "select", "args": [{"state": shown}, "block", "none"]})
        doc.bind(f"{button}-label.text", f"{button}-label", "text", {"state": text_state})
    doc.events["msgPickLeft"] = [{"op": "action", "action": "msgLeft"}]
    doc.events["msgPickMid"] = [{"op": "action", "action": "msgMid"}]
    doc.events["msgPickRight"] = [{"op": "if", "condition": {"state": "visible_right"}, "then": [{"op": "action", "action": "msgRight"}],
                                   "else": [{"op": "if", "condition": {"state": "visible_mid"},
                                             "then": [{"op": "action", "action": "msgMid"}]}]}]
    # The session shows the box by activating it; the trailing button of two,
    # or the lone one, takes the focus (section 7.4).
    doc.events["onActivate"] = [{"op": "call", "event": "msgShow"},
                                {"op": "if", "condition": {"state": "visible_mid"}, "then": [{"op": "focus", "control": "msg_mid"}],
                                 "else": [{"op": "if", "condition": {"state": "visible_right"},
                                           "then": [{"op": "focus", "control": "msg_right"}]}]}]
    doc.events["onBack"] = [{"op": "call", "event": "msgPickRight"}]
    root = group("screen", {**FULL, "font-family": font(FACE_DEFAULT), "font-size": length(18), "color": colour([1, 1, 1, 1])},
                 [modal, edge_glow(doc)])
    doc.events["onActivate"].append({"op": "playTimeline", "timeline": "edgeGlow"})
    return doc.build(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail when a generated document differs from its source")
    args = parser.parse_args()
    documents = {"title": home_document(False), "pause": home_document(True), "msgbox": message_box_document(),
                 "loadgame": load_game_document(), "savegame": save_game_document(),
                 "controls": controls_document(), "game": game_options_document(), "system": system_document(),
                 "credits": credits_document(), "joingame": join_game_document(),
                 "createserver": create_server_document(), "restartmenu": death_document(),
                 "loading": loading_document(), "mp_escape": multiplayer_menu_document()}
    stale = []
    for name, document in documents.items():
        output = OUTPUTS[name]
        rendered = render(document)
        if args.check:
            current = output.read_bytes().decode("utf-8").replace("\r\n", "\n") if output.exists() else None
            if current != rendered:
                stale.append(str(output.relative_to(ROOT)))
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(rendered.encode("utf-8"))
        print(f"wrote {output.relative_to(ROOT)} ({len(rendered)} bytes)")
    if stale:
        print("stale generated documents: " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
