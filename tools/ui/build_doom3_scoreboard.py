#!/usr/bin/env python3
# Copyright (C) 2026 DarkMatter Productions. GPL-3.0-or-later.
"""Writes openD3's multiplayer scoreboard, guis/scoreboard.gui.

Doom 3's scoreboard has four rows, one per seat of its four player servers.
openD3 seats up to 16 (MP_MAX_PLAYERS in src/game/MultiplayerGame.h), so its
scoreboard is a stock GUI with a row for each of 16 seats that lays out only
as many as the server has. It is built by name from the retail board's art:
the flickering frame (guis/assets/hud/mp/score_*), the scan lines and static,
the black column wells, the colour bars and the frame round your own row.

The game publishes, besides Doom 3's own per-row state (player<n>,
player<n>_score, player<n>_tdm_score, player<n>_tdm_tscore, player<n>_wins,
player<n>_ping, rank<n>, rank<n>_color1-3, rank_self, scoretext, gameinfo,
livesinfo, timeinfo):

    slots        how many rows to lay out: the server's seats, or more rows
                 if more are in use (idMultiplayerGame::UpdateScoreboardSeats)
    lines        how many rows hold a player
    playercount  "Players: 9 / 16", already localized

The rows lay out in three steps, so a board never looks crowded before it
has to:

    seats   rows  pitch  bar
    1-4       4     40    16   Doom 3's board
    5-8       8     18    14   the same height as Doom 3's
    9-16  seats     16    14   grows downwards, 16 rows end at y 389

Usage: build_doom3_scoreboard.py [--check]
"""

from __future__ import annotations

import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "content" / "baseod3" / "pak0" / "guis" / "scoreboard.gui"
ROWS = 16                     # MP_MAX_PLAYERS

SLOTS = '"gui::slots"'
# The layout every other window reads, in the forecolor of three windows
# drawn first. A window's expressions read another window's values as that
# window last evaluated them, and the GUI evaluates its windows in order, so
# each holds only what follows from the ones before it in the same frame.
# Calc: the row pitch, the bar height, the rows laid out and the step past
# Doom 3's board (0 or 1), all from the seats.
PITCH = '"Calc::forecolor"[0]'
BAR = '"Calc::forecolor"[1]'
LAID = '"Calc::forecolor"[2]'
DENSE = '"Calc::forecolor"[3]'
# Calc2: the column wells' height.
WELL = '"Calc2::forecolor"[0]'
# Calc3: the footer's top and the frame's bottom edge.
FOOT = '"Calc3::forecolor"[0]'
BOTTOM = '"Calc3::forecolor"[1]'
# Open's forecolor x runs from 1 to 0 as the board opens: the frame closes in
# from 10 units out, as Doom 3's does.
OPEN = '"Open::forecolor"[0]'

# Doom 3's GUI expressions group operators of one priority to the right, so
# "a - b - c" is a - (b - c): no expression here has an operator after a
# subtraction at the same level; brackets hold the rest.
FLICKER = "0.2, 0.45, 0.4, pdflick2 [ time * .0025 ] / 2.5"
WELL_TOP = 73                 # the column wells' top
BAR_TOP = WELL_TOP + 11       # the first row's bar
# Columns: (window suffix, well left, well width, header text, header align).
COLUMNS = (
    ("Name", 82, 186, "#str_02181", 0),
    ("Score", 269, 91, "gui::scoretext", 1),
    ("Wins", 361, 91, "#str_02619", 1),
    ("Ping", 453, 91, "#str_02048", 1),
)


def window(kind: str, name: str, props: list[str], children: list[str] = (), indent: int = 1) -> str:
    pad = "\t" * indent
    lines = [f"{pad}{kind} {name} {{"]
    lines += [f"{pad}\t{p}" for p in props]
    for child in children:
        lines.append(child)
    lines.append(f"{pad}}}")
    return "\n".join(lines)


def text_props(rect: str, text: str, scale: float, align: int, colour: str, *extra: str) -> list[str]:
    return [f"rect\t\t{rect}", f'text\t\t"{text}"', 'font\t\t"fonts/bank"', "shadow\t\t1", f"textscale\t{scale}",
            f"textalign\t{align}", f"forecolor\t{colour}", "noevents\t1", *extra]


def bar_top(row: int) -> str:
    return f"{BAR_TOP} + {row - 1} * {PITCH}"


def text_top(row: int, drop: int = 0) -> str:
    # Doom 3 sets a row's text 5 units above its bar; a 14 unit bar centres
    # one unit higher.
    return f"{BAR_TOP - 5 + drop} + {row - 1} * {PITCH} - {DENSE}"


def frame() -> list[str]:
    o = OPEN
    side = f"{BOTTOM} + 20 * {o} - 26"
    pieces = (
        ("BorderTL", f"67 - 10 * {o}, 18 - 10 * {o}, -8, 8", "corner"),
        ("BorderTM", f"75 - 10 * {o}, 18 - 10 * {o}, 478 + 20 * {o}, 8", "horiz"),
        ("BorderTR", f"553 + 10 * {o}, 18 - 10 * {o}, 8, 8", "corner"),
        ("BorderL", f"67 - 10 * {o}, 26 - 10 * {o}, -8, {side}", "vert"),
        ("BorderR", f"553 + 10 * {o}, 26 - 10 * {o}, 8, {side}", "vert"),
        ("BorderBL", f"67 - 10 * {o}, {BOTTOM} + 10 * {o}, -8, -8", "corner"),
        ("BorderBM", f"75 - 10 * {o}, {BOTTOM} + 10 * {o}, 478 + 20 * {o}, -8", "horiz"),
        ("BorderBR", f"553 + 10 * {o}, {BOTTOM} + 10 * {o}, 8, -8", "corner"),
    )
    return [window("windowDef", name, [f"rect\t\t{rect}", f"matcolor\t{FLICKER}",
                                       f'background\t"guis/assets/hud/mp/score_{art}"', "noevents\t1"])
            for name, rect, art in pieces]


def backdrop() -> list[str]:
    height = f"{BOTTOM} - 26"
    # The box takes the retail board's two-step flash as it opens; its scan
    # lines and static are drawn at the retail board's density and clipped to
    # the box, however tall it grows.
    box = window("windowDef", "BoxBg", [f"rect\t\t75, 26, 477, {height}", "backcolor\t0.1, 0.2, 0.2, 0.5",
                                         "bordercolor\t0.1, 0.25, 0.25, 1", "bordersize\t1", "noevents\t1"])
    scan = window("windowDef", "ScanClip", [f"rect\t\t77, 28, 473, {BOTTOM} - 30", "noevents\t1"], [
        window("windowDef", "Scanlines", ["rect\t\t0, 0, 473, 400", "matcolor\t0.25, 0.25, 0.25, 1",
                                          'background\t"gui/test/gui_scanlines5"', "matscaley\t5.63", "noevents\t1"], indent=2)])
    noise = window("windowDef", "StaticClip", [f"rect\t\t77, 28, 473, {BOTTOM} - 30", "noevents\t1"], [
        window("windowDef", "Static", ["rect\t\t0, 0, 473, 400", 'background\t"gui/staticalt"',
                                       "matcolor\t1, 1, 1, pdhalffade [ time * 0.001 ] / 7", "matscalex\t4",
                                       "matscaley\t4.86", "noevents\t1"], indent=2)])
    return [scan, box, noise]


def wells() -> list[str]:
    out = []
    for index, (_name, left, width, _text, _align) in enumerate(COLUMNS, 1):
        for suffix, top, height in (("", 53, "19"), ("a", WELL_TOP, WELL)):
            out.append(window("windowDef", f"Well{index}{suffix}", [
                f"rect\t\t{left}, {top}, {width}, {height}", "backcolor\t0, 0, 0, 0.35", "bordercolor\t0, 0, 0, 1",
                "bordersize\t1", "noevents\t1"]))
    return out


def rows() -> list[str]:
    out = []
    for row in range(1, ROWS + 1):
        laid = f"( {row} <= {LAID} )"
        out.append(window("windowDef", f"Bar{row}", [
            f"rect\t\t90, {bar_top(row)}, 445, {BAR}",
            f'backcolor\t"gui::rank{row}_color1", "gui::rank{row}_color2", "gui::rank{row}_color3", 0.25',
            f'visible\t\t( ( "gui::rank{row}" != 0 ) && {laid} )', "noevents\t1"]))
    out.append(window("windowDef", "BarSelf", [
        f'rect\t\t88, {BAR_TOP - 2} + ( "gui::rank_self" - 1 ) * {PITCH}, 449, {BAR} + 4',
        "bordercolor\t0.5, 0.6, 0.6, 1", "bordersize\t1", 'visible\t\t( "gui::rank_self" != 0 )', "noevents\t1"]))
    white = "1, 1, 1, 0.8"
    for row in range(1, ROWS + 1):
        top = text_top(row)
        laid = f"visible\t\t( {row} <= {LAID} )"
        cells = (
            (f"player{row}name", f"100, {top}, 166, 19", f"gui::player{row}", 0.25, 0, ("nowrap\t\t1",)),
            (f"player{row}score", f"267, {top}, 91, 19", f"gui::player{row}_score", 0.25, 1, ()),
            (f"player{row}tdmscore", f"270, {text_top(row, 3)}, 35, 19", f"gui::player{row}_tdm_score", 0.2, 2, ()),
            (f"player{row}tdmtscore", f"308, {top}, 35, 19", f"gui::player{row}_tdm_tscore", 0.25, 0, ()),
            (f"player{row}wins", f"361, {top}, 91, 19", f"gui::player{row}_wins", 0.25, 1, ()),
            (f"player{row}ping", f"453, {top}, 91, 19", f"gui::player{row}_ping", 0.25, 1, ()),
        )
        for name, rect, text, scale, align, extra in cells:
            out.append(window("windowDef", name, text_props(rect, text, scale, align, white, laid, *extra)))
    return out


def headings() -> list[str]:
    teal = "0.6, 0.8, 0.8, 1"
    out = [window("windowDef", "Scoreboard", text_props("120, 23, 385, 35", "#str_02618", 0.4, 1, "0.4, 0.7, 0.7, 1")),
           window("windowDef", "PlayerCount", text_props("404, 32, 140, 19", "gui::playercount", 0.2, 2, teal, "nowrap\t\t1"))]
    for index, (name, left, width, text, align) in enumerate(COLUMNS, 1):
        inset = 18 if align == 0 else 0
        out.append(window("windowDef", f"Heading{name}", text_props(f"{left + inset}, 50, {width}, 19", text, 0.25, align, teal)))
    return out


def footer() -> list[str]:
    teal = "0.6, 0.8, 0.8, 1"
    return [window("windowDef", "FooterBox", [f"rect\t\t82, {FOOT}, 462, 28", "backcolor\t0.4, 0.6, 0.6, 0.1",
                                               "bordercolor\t0.3, 0.4, 0.4, 1", "bordersize\t1", "noevents\t1"]),
            window("windowDef", "GameType", text_props(f"85, {FOOT} + 1, 455, 35", "gui::gameinfo", 0.23, 0, teal)),
            # Doom 3 centres the limit 30 units right of the box's centre,
            # clear of a long game type.
            window("windowDef", "LivesInfo", text_props(f"115, {FOOT} + 1, 455, 35", "gui::livesinfo", 0.23, 1, teal)),
            window("windowDef", "TimeInfo", text_props(f"85, {FOOT} + 1, 455, 35", "gui::timeinfo", 0.23, 2, teal))]


def opening() -> str:
    """The retail board's opening, timed from activation: the frame closes in
    over 400 ms, the box flashes, then each column well's edge in turn."""
    events = [
        "onTime 0 {\n\t\t\ttransition \"Open::forecolor\" \"1 0 0 0\" \"0 0 0 0\" \"400\" \"0\" \"0.8\" ;\n"
        "\t\t\ttransition \"BoxBg::backcolor\" \"1 1 1 0.2\" \"0.25 0.35 0.35 0.4\" \"70\" ;\n\t\t}",
        "onTime 70 {\n\t\t\ttransition \"BoxBg::backcolor\" \"1 1 1 0.2\" \"0.1 0.2 0.2 0.5\" \"300\" ;\n\t\t}",
    ]
    for step in range(len(COLUMNS) + 1):
        moves = []
        if step < len(COLUMNS):
            moves.append(f"transition \"Well{step + 1}::bordercolor\" \"1 1 1 0.2\" \"0 0 0 1\" \"300\" ;")
        if step > 0:
            moves.append(f"transition \"Well{step}a::bordercolor\" \"1 1 1 0.2\" \"0 0 0 1\" \"300\" ;")
        events.append(f"onTime {100 + 50 * step} {{\n" + "".join(f"\t\t\t{m}\n" for m in moves) + "\t\t}")
    return window("windowDef", "Sequence", ["rect\t\t0, 0, 0, 0", "notime\t\t1", "noevents\t1", *events])


def document() -> str:
    dense = f"( {SLOTS} > 4 )"
    crowded = f"( {SLOTS} > 8 )"
    calc = window("windowDef", "Calc", [
        "rect\t\t0, 0, 0, 0", "noevents\t1",
        f"forecolor\t40 - ( 22 * {dense} + 2 * {crowded} ), 16 - 2 * {dense}, 4 + 4 * {dense} + ( {SLOTS} - 8 ) * {crowded}, {dense}"])
    # Doom 3's wells reach 11 units above the first bar and 10 below the last.
    calc2 = window("windowDef", "Calc2", [
        "rect\t\t0, 0, 0, 0", "noevents\t1", f"forecolor\t21 + ( {LAID} - 1 ) * {PITCH} + {BAR}, 0, 0, 0"])
    # The footer stands 6 units under the wells and is 28 tall; the frame
    # closes 7 under that.
    calc3 = window("windowDef", "Calc3", [
        "rect\t\t0, 0, 0, 0", "noevents\t1", f"forecolor\t{WELL_TOP + 6} + {WELL}, {WELL_TOP + 6 + 35} + {WELL}, 0, 0"])
    opener = window("windowDef", "Open", ["rect\t\t0, 0, 0, 0", "noevents\t1", "forecolor\t1, 0, 0, 0"])
    parts = [calc, calc2, calc3, opener, opening(), *frame(), *backdrop(), *wells(), *rows(), *headings(), *footer()]
    header = """// Copyright (C) 2026 DarkMatter Productions. GPL-3.0-or-later.
// Generated by tools/ui/build_doom3_scoreboard.py; edit the generator, not this file.
//
// openD3's multiplayer scoreboard: Doom 3's board, built by name from its art,
// with a row for each of 16 seats. It lays out the rows the server seats
// (gui::slots): four at Doom 3's spacing on a server of up to four, eight in
// the same height up to eight, and one per seat beyond, the board growing down.
"""
    desktop = window("windowDef", "Desktop", [
        "rect\t\t0, 0, 640, 480", "menugui\t\t0", "nocursor\t1",
        'onActivate {\n\t\tresetTime "Sequence" "0" ;\n\t}',
        'onDeactivate {\n\t\tset "Open::forecolor" "1 0 0 0" ;\n\t}'], parts, indent=0)
    return header + desktop + "\n"


def main() -> int:
    text = document()
    if "--check" in sys.argv[1:]:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT} is out of date; run {Path(__file__).name}")
            return 1
        print(f"{OUT.name} is current")
        return 0
    OUT.write_bytes(text.encode("utf-8"))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
