#!/usr/bin/env python3
"""openD3's retained death screen.

Section 9.8 of docs/dev/ui-visual-design.md: `guis/restart.gui` is the menu's
furniture in hell's colours. Its scene is real imagery the specification
keeps (the fire video, the faces, the blood, the pentagrams, the logo and the
washes, scan lines and dirt over them), so the stock screen goes on drawing
it and this document draws only what a player acts on: the three choices,
each typed in letter by letter as the stock types it, and the line under a
choice that says what it does.

The session presents the document when the player has died and the level is
unloaded (idSessionLocal::OpenRestartMenu), draws the stock scene under it
with the stock choices hidden (DrawRetainedPageHome, RETAINED_DEATH_FURNITURE)
and takes its three requests: deathRestart, deathLoad and deathMenu.

build_doom3_menus.py writes the document.
"""

from __future__ import annotations

from doom3_menu_kit import (
    CANVAS_H, CANVAS_W, FACE_BANK, FACE_DEFAULT, FULL, NO_POINTER, U, Document, absolute, box, colour, font, group,
    label, length, number, track, typeface,
)

# The stock choices: the control's id, its top on the canvas, when it starts
# typing after the screen opens (the stock Open window's resets), its typed
# stages as (ms after it starts, text), the last of which stays, the line
# under it and the request it sends.
CHOICES = (
    ("death_restart", 260, 1700, ((50, "#str_02550"), (100, "#str_02551"), (150, "#str_02552"), (200, "#str_02553"),
                                  (250, "#str_02554"), (300, "#str_02555"), (350, "#str_02546")), "#str_02556", "deathRestart"),
    ("death_load", 300, 1900, ((50, "#str_02557"), (100, "#str_02558"), (150, "#str_02559"), (200, "#str_02560")),
     "#str_02561", "deathLoad"),
    ("death_menu", 340, 2200, ((50, "#str_04208"), (100, "#str_04209"), (150, "#str_04210"), (200, "#str_04211"),
                               (250, "#str_04212"), (300, "#str_04213"), (400, "#str_04214")), "#str_02566", "deathMenu"),
)
OPEN_MS = 2700   # the last choice has finished typing
# Measured against the stock screen at 1280x720: its text sits 2 dp lower in
# the cell than a centred line and stands 0.6 dp wider a letter.
TEXT_DROP = 2.0
TRACKING = {"letter-spacing": length(0.6)}


def choice(doc: Document, ident: str, top: float, start: int, stages: tuple, subtitle: str, request: str, tracks: list) -> dict:
    """A choice (section 9.8): Bank at the stock's default scale, centred in
    a 120 x 20 u cell, white at 50 %; under the pointer or the focus it rises
    to white in 400 ms and its line appears at 50 %, and both fall back in
    400 ms. Its stages are stacked labels, shown one at a time as it types."""
    labels = []
    for index, (at, key) in enumerate(stages):
        node = f"{ident}-stage{index}"
        labels.append(label(node, key, {**absolute(left=0, top=TEXT_DROP), "width": length(100, "%"), "height": length(100, "%"),
                                        **typeface(FACE_BANK, 0.35, 20, [1, 1, 1, 1], "center", **TRACKING), **NO_POINTER, "opacity": number(0)}))
        shown = start + at
        # The first two keys clear a stage a previous death left showing: a
        # timeline starts from the property's current value.
        keys = [(0, number(0)), (1, number(0)), (shown - 1, number(0)), (shown, number(1))]
        if index + 1 < len(stages):
            gone = start + stages[index + 1][0]
            keys += [(gone - 1, number(1)), (gone, number(0)), (OPEN_MS, number(0))]
        else:
            keys += [(OPEN_MS, number(1))]
        tracks.append(track(node, "opacity", keys))
    text = group(f"{ident}-text", {**FULL, **NO_POINTER, "opacity": number(0.5)}, labels)
    line = label(f"{ident}-line", subtitle, {**absolute(left=U * -50, top=U * 18, width=U * 220, height=U * 20),
                                             **typeface(FACE_BANK, 0.26, 20, [1, 1, 1, 1], "center"), **NO_POINTER, "opacity": number(0)})
    ids = doc.states(ident, [(f"{ident}-text", "opacity", {"default": number(0.5), "hover": number(1)}, 400, 400),
                             (f"{ident}-line", "opacity", {"default": number(0), "hover": number(0.5)}, 400, 400)])
    doc.bind(f"{ident}.enabled", ident, "enabled", {"state": "death.ready"})
    return group(ident, box(252, top, 120, 20), [text, line],
                 control={"role": "button", "label": stages[-1][1], "action": doc.session(request), "states": ids})


def death_document() -> dict:
    """The death screen's choices over the stock scene: Restart, Load and
    Main Menu, typed in at 1.7, 1.9 and 2.2 s after the screen opens, as the
    stock types them, and taking input once the last has finished, with
    Restart focused."""
    doc = Document("opend3.restartmenu")
    doc.state["death.ready"] = {"type": "boolean", "initial": False}
    tracks: list = []
    choices = [choice(doc, *entry, tracks) for entry in CHOICES]
    doc.timeline("deathOpen", OPEN_MS, tracks, complete="deathOpened")
    # Restart takes the focus once the choices take input, so a keyboard or
    # a controller can accept it at once. A focused button shows no focus
    # while the pointer is in use, so nothing lights for the mouse.
    doc.events["deathOpened"] = [{"op": "setState", "values": {"death.ready": True}},
                                 {"op": "focus", "control": CHOICES[0][0]}]
    doc.events["onActivate"] = [{"op": "setState", "values": {"death.ready": False}}, {"op": "playTimeline", "timeline": "deathOpen"}]
    canvas = group("canvas", {**absolute(top=0, width=CANVAS_W, height=0), "left": length(50, "%"), "margin-left": length(-CANVAS_W / 2)}, choices)
    stage = group("stage", {**absolute(left=0), "width": length(100, "%"), "height": length(CANVAS_H), "top": length(50, "%"),
                            "margin-top": length(-CANVAS_H / 2)}, [canvas])
    root = group("screen", {**FULL, "font-family": font(FACE_DEFAULT), "font-size": length(18), "color": colour([1, 1, 1, 1])}, [stage])
    return doc.build(root)
