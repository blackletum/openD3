#!/usr/bin/env python3
"""openD3's retained system check.

The screen before the main menu that offers the detected performance preset
whenever the preset system's version differs from the one the configuration
last checked (upstream's docs/dev/ui/performance-presets.md, "System check";
src/framework/Session_presetcheck.cpp). It is the dialog shell of section
6.10 of docs/dev/ui-visual-design.md grown to a readout: the question, the
detected hardware, the nine presets as a ladder with the recommended one lit
and the current one outlined, the recommendation's scale and frame cap, and
where the choice can be changed later.

The stock screen guis/presetcheck.gui (repo-authored, from the retail message
box's art) draws the scene under this document: the menu's stars and Mars.
The session draws it with its dialog, the window CheckDialog, hidden
(Session_DrawPresetCheckScene). Both read the same state, already localized:

    check_body, check_primary         the question, and the first action's label
    check_gpu, check_vram, check_ram, check_cpu, check_display
    check_recommended, check_detail, check_current, check_footer
    check_tierLow, check_tierHigh     the ladder's two end names
    check_recommendedTier, check_currentTier   ladder cells, -1 for none
    check_matches                     the settings already are the recommendation
    check_busy                        the apply is restarting the renderer

and answer with the session verbs presetCheckApply (APPLY RECOMMENDED, or
CONTINUE when the settings already match), presetCheckKeep (KEEP CURRENT)
and presetCheckLater (ASK ME NEXT TIME, and Back).

The plate is 440 x 330 u at (100, 75) on the canvas. The stock screen uses
the same plate coordinates, so a change to one belongs in the other.

build_doom3_menus.py writes the document.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from doom3_menu_kit import (
    FACE_BANK, FACE_DEFAULT, FULL, NO_POINTER, U, Document, box, colour, cut_plate, dialog, edge_glow, em, font, footer_link,
    group, hairline, keyword, label, length, menu_item, number, path, rgb, solid, token, typeface, vector, walk, SLOT_12,
)

ROOT = Path(__file__).resolve().parents[2]
STRINGS_DIR = ROOT / "content" / "baseod3" / "pak0" / "strings"
FONTS_DIR = ROOT / "content" / "baseod3" / "pak0" / "fonts"
PLACEHOLDER = "#str_232016"        # Unknown: the session supplies every bound text

PLATE_W, PLATE_H, PLATE_TOP = 440.0, 330.0, 75.0   # u
LEFT, SPAN = 30.0, 380.0                           # u: the readout's column in the plate
VALUE_X = 145.0                                    # u: the value column
BODY_TOP, BODY_LINE, BODY_LINES = 30.0, 14.0, 4
ROW_PITCH = 12.0
TIERS = 9                                          # opend3::PerformancePresetCount
CELL_H, CELL_GAP = 10.0, 2.5
BUTTON_TOP, BUTTON_W = 276.0, 190.0
BUTTONS_X = (25.0, 225.0)
LINK_TOP = 302.0
FOOTER_LEFT, FOOTER_W, FOOTER_SCALE = 20.0, 400.0, 0.17

HARDWARE = (("gpu", "#str_232004"), ("vram", "#str_232005"), ("ram", "#str_232006"), ("cpu", "#str_232007"),
            ("display", "#str_232008"))
STATES = ("check_body", "check_primary", "check_gpu", "check_vram", "check_ram", "check_cpu", "check_display",
          "check_recommended", "check_detail", "check_current", "check_footer", "check_tierLow", "check_tierHigh")
HEADING = rgb("#99CCFF", 0.8)


@lru_cache(maxsize=None)
def tables() -> dict:
    """Every language's openD3 strings, by key."""
    found = {}
    for path in sorted(STRINGS_DIR.glob("*_opend3.lang")):
        entries = dict(re.findall(r'"(#str_\d+)"\s+"((?:[^"\\]|\\.)*)"', path.read_text(encoding="utf-8")))
        found[path.stem.split("_")[0]] = entries
    return found


@lru_cache(maxsize=None)
def face(name: str, size: float):
    from PIL import ImageFont
    return ImageFont.truetype(str(FONTS_DIR / f"{name}.ttf"), max(1, round(size)))


def text_width(face_name: str, scale: float, text: str) -> float:
    """A line's width in dp at a stock textscale, as typeface() sets it."""
    size, spacing = em(scale), 0.0
    if scale <= 0.30:
        grow, track_by = SLOT_12[face_name]
        size, spacing = em(scale) * grow, em(scale) * track_by
    return face(face_name, size).getlength(text) * size / max(1, round(size)) + spacing * len(text)


def wrapped(face_name: str, scale: float, text: str, width: float) -> int:
    lines, line = 1, ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and text_width(face_name, scale, trial) > width:
            lines, line = lines + 1, word
        else:
            line = trial
    return lines


def check_fit() -> None:
    """Every language's question in three lines and every action's label in
    its cell, or the build stops: the runtime would clip them. The footer
    is measured with the stock OPTIONS and SYSTEM in it."""
    for language, entries in tables().items():
        for key in ("#str_232001", "#str_232002", "#str_232003"):
            count = wrapped(FACE_BANK, 0.25, entries[key], U * SPAN)
            if count > BODY_LINES:
                raise SystemExit(f"presetcheck: the {language} question {key} takes {count} lines of {BODY_LINES}")
        for key in ("#str_232011", "#str_232012", "#str_232027"):
            if text_width(FACE_DEFAULT, 0.25, entries[key]) > U * (BUTTON_W - 12):
                raise SystemExit(f"presetcheck: the {language} action {key} does not fit its {BUTTON_W} u cell")
        if text_width(FACE_DEFAULT, 0.25, entries["#str_232013"]) > U * 200:
            raise SystemExit(f"presetcheck: the {language} link does not fit")
        footer = entries["#str_232023"].replace("%s", "OPTIONS", 1).replace("%s", "SYSTEM", 1)
        if text_width(FACE_BANK, FOOTER_SCALE, footer) > U * FOOTER_W:
            raise SystemExit(f"presetcheck: the {language} footer does not fit its line")


def heading(ident: str, key: str, top: float) -> list:
    """A readout section's name, Default 0.2, over a title rule."""
    return [label(f"{ident}-text", key, {**box(LEFT, top, SPAN, 12), **typeface(FACE_DEFAULT, 0.2, 12, HEADING), **NO_POINTER}),
            vector(f"{ident}-rule", {**box(LEFT, top + 13, SPAN, 1), **NO_POINTER},
                   [path("rule", [(0, 0), ({"fraction": 1}, 0), ({"fraction": 1}, {"fraction": 1}), (0, {"fraction": 1})],
                         fill=solid(token("rule.title")))])]


def row(doc: Document, ident: str, key: str, state: str, top: float, *, value_face: str = FACE_BANK, value_scale: float = 0.2,
        tint: list | None = None) -> list:
    """A readout row: its name in text.dim, the session's value after it."""
    name = label(f"{ident}-name", key, {**box(LEFT, top, VALUE_X - LEFT - 6, ROW_PITCH), **typeface(FACE_BANK, 0.2, ROW_PITCH, token("text.dim")),
                                        **NO_POINTER, "overflow": keyword("hidden")})
    value = label(f"{ident}-value", PLACEHOLDER, {**box(VALUE_X, top, LEFT + SPAN - VALUE_X, ROW_PITCH),
                                                  **typeface(value_face, value_scale, ROW_PITCH, tint or token("text.active")),
                                                  **NO_POINTER, "overflow": keyword("hidden")})
    doc.bind(f"{ident}-value.text", f"{ident}-value", "text", {"state": state})
    return [name, value]


def ladder(doc: Document, top: float) -> list:
    """The nine presets, Minimum leading: each a chrome plate a little
    brighter than the one before, the recommended one lit in text.action and
    the current one outlined in white with a marker under it; the two end
    names under the ends."""
    cell_w = round((SPAN - (TIERS - 1) * CELL_GAP) / TIERS, 3)
    shape = cut_plate(U * cell_w, U * CELL_H, (0, U * 3, 0, 0))
    nodes = []
    for tier in range(TIERS):
        left = round(LEFT + tier * (cell_w + CELL_GAP), 3)
        place = box(left, top, cell_w, CELL_H)
        nodes.append(vector(f"tier-{tier}", {**place, **NO_POINTER},
                            [path("plate", shape, fill=solid(rgb("#738CB2", round(0.18 + 0.03 * tier, 3))))]))
        lit = vector(f"tier-{tier}-lit", {**place, **NO_POINTER, "opacity": number(0)},
                     [path("plate", shape, fill=solid(token("text.action", 0.85)))])
        doc.bind(f"tier-{tier}-lit.opacity", f"tier-{tier}-lit", "opacity",
                 {"op": "select", "args": [{"op": "==", "args": [{"state": "check_recommendedTier"}, tier]}, 1, 0]})
        now = group(f"tier-{tier}-current", {**box(left - 2, top - 2, cell_w + 4, CELL_H + 8), **NO_POINTER, "opacity": number(0)}, [
            vector(f"tier-{tier}-outline", box(0, 0, cell_w + 4, CELL_H + 4),
                   hairline("outline", [(x + U * 2, y + U * 2) for x, y in shape], "#FFFFFF", alpha=0.9)),
            vector(f"tier-{tier}-marker", box(cell_w / 2 - 1, CELL_H + 5, 6, 3), [
                path("marker", [(0, U * 3), (U * 3, 0), (U * 6, U * 3)], fill=solid(rgb("#FFFFFF", 0.9)))])])
        doc.bind(f"tier-{tier}-current.opacity", f"tier-{tier}-current", "opacity",
                 {"op": "select", "args": [{"op": "==", "args": [{"state": "check_currentTier"}, tier]}, 1, 0]})
        nodes += [lit, now]
    ends = typeface(FACE_BANK, 0.18, 10, token("text.dim"))
    low = label("tier-low", PLACEHOLDER, {**box(LEFT, top + CELL_H + 5, SPAN / 2, 10), **ends, **NO_POINTER})
    high = label("tier-high", PLACEHOLDER, {**box(LEFT + SPAN / 2, top + CELL_H + 5, SPAN / 2, 10), **ends, **NO_POINTER,
                                            "text-align": keyword("right")})
    doc.bind("tier-low.text", "tier-low", "text", {"state": "check_tierLow"})
    doc.bind("tier-high.text", "tier-high", "text", {"state": "check_tierHigh"})
    return nodes + [low, high]


def preset_check_document() -> dict:
    """The system check: the question and the readout in the dialog shell,
    APPLY RECOMMENDED (CONTINUE when nothing would change) and KEEP CURRENT
    as its two buttons, and ASK ME NEXT TIME as the quiet link under them.
    APPLY RECOMMENDED takes the focus. While an apply restarts the renderer
    the choices give way to APPLYING SETTINGS.

    The shell appears in one frame, as engine message boxes do (section
    9.9): the session activates the check during start-up, before the first
    frame, and an entrance timeline played then never completes."""
    check_fit()
    doc = Document("opend3.presetcheck")
    for name in STATES:
        doc.state[name] = {"type": "string", "initial": ""}
    for name in ("check_recommendedTier", "check_currentTier"):
        doc.state[name] = {"type": "number", "initial": -1}
    for name in ("check_matches", "check_busy"):
        doc.state[name] = {"type": "boolean", "initial": False}
    for verb in ("presetCheckApply", "presetCheckKeep", "presetCheckLater"):
        doc.session(verb)
    busy = {"state": "check_busy"}
    doc.events["checkPickLater"] = [{"op": "if", "condition": {"op": "!", "args": [busy]},
                                     "then": [{"op": "action", "action": "presetCheckLater"}]}]
    doc.events["presetCheckApplying"] = [{"op": "setState", "values": {"check_busy": True}}]

    body = label("check-body", PLACEHOLDER, {**box(LEFT, BODY_TOP, SPAN, BODY_LINES * BODY_LINE),
                                             **typeface(FACE_BANK, 0.25, BODY_LINE, token("text.active")),
                                             "white-space": keyword("pre-wrap"), "overflow": keyword("hidden"), **NO_POINTER})
    doc.bind("check-body.text", "check-body", "text", {"state": "check_body"})
    parts = [body, *heading("check-hardware", "#str_232025", 90)]
    y = 106.0
    for ident, key in HARDWARE:
        parts += row(doc, f"check-{ident}", key, f"check_{ident}", y)
        y += ROW_PITCH
    parts += heading("check-preset", "#str_232026", 170)
    parts += ladder(doc, 188)
    parts += row(doc, "check-recommended", "#str_232010", "check_recommended", 216, value_face=FACE_DEFAULT, value_scale=0.25,
                 tint=token("text.action"))
    detail = label("check-detail", PLACEHOLDER, {**box(VALUE_X, 228, LEFT + SPAN - VALUE_X, ROW_PITCH),
                                                 **typeface(FACE_BANK, 0.2, ROW_PITCH, token("text.value")), **NO_POINTER,
                                                 "overflow": keyword("hidden")})
    doc.bind("check-detail.text", "check-detail", "text", {"state": "check_detail"})
    parts.append(detail)
    parts += row(doc, "check-current", "#str_232009", "check_current", 240, value_face=FACE_DEFAULT, value_scale=0.22)
    footer = label("check-footer", PLACEHOLDER, {**box(FOOTER_LEFT, 255, FOOTER_W, 10), **typeface(FACE_BANK, FOOTER_SCALE, 10, token("text.dim")),
                                                 **NO_POINTER, "overflow": keyword("hidden")})
    doc.bind("check-footer.text", "check-footer", "text", {"state": "check_footer"})
    parts.append(footer)

    apply_button = menu_item(doc, "check_apply", PLACEHOLDER, box(BUTTONS_X[0], BUTTON_TOP, BUTTON_W, 19), BUTTON_W, centred=True,
                             action="presetCheckApply", navigation={"right": "check_keep", "down": "check_later"})
    keep_button = menu_item(doc, "check_keep", "#str_232012", box(BUTTONS_X[1], BUTTON_TOP, BUTTON_W, 19), BUTTON_W, centred=True,
                            action="presetCheckKeep", navigation={"left": "check_apply", "down": "check_later"})
    doc.bind("check_apply-label.text", "check_apply-label", "text", {"state": "check_primary"})
    later = footer_link(doc, "check_later", "#str_232013", box((PLATE_W - 200) / 2, LINK_TOP, 200, 16), event="checkPickLater")
    later["control"]["navigation"] = {"up": "check_apply"}
    choices = group("check-choices", {**FULL, "display": keyword("block")}, [apply_button, keep_button, later])
    doc.bind("check-choices.display", "check-choices", "display", {"op": "select", "args": [busy, "none", "block"]})
    working = label("check-busy", "#str_232022", {**box(LEFT, BUTTON_TOP, SPAN, 19), **typeface(FACE_DEFAULT, 0.28, 19, token("text.data"), "center"),
                                                  **NO_POINTER, "display": keyword("none")})
    doc.bind("check-busy.display", "check-busy", "display", {"op": "select", "args": [busy, "block", "none"]})
    parts += [choices, working]

    modal = dialog(doc, "check", "#str_232000", PLACEHOLDER, [], initial="check_apply", back="checkPickLater",
                   width=PLATE_W, height=PLATE_H, top=PLATE_TOP, contents=parts, animate=False)
    nodes = {node["id"]: node for node in walk(modal)}
    assert "check_apply" in nodes and "check-title" in nodes
    doc.events["onBack"] = [{"op": "call", "event": "checkPickLater"}]
    doc.events["onActivate"] = [{"op": "call", "event": "checkShow"}, {"op": "focus", "control": "check_apply"},
                                {"op": "playTimeline", "timeline": "edgeGlow"}]
    root = group("screen", {**FULL, "font-family": font(FACE_DEFAULT), "font-size": length(18), "color": colour([1, 1, 1, 1])},
                 [modal, edge_glow(doc)])
    return doc.build(root)
