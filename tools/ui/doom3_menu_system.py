#!/usr/bin/env python3
"""openD3's retained SYSTEM page.

Section 9.3 of docs/dev/ui-visual-design.md: the stock System page's two
group boxes, video and audio, on the options plate with its apply bar.

The page edits a draft in the engine's settings service and applies it there
(src/ui/SettingsService.cpp, SystemSettingsHost): settings.system.begin on
opening, settings.system.edit for each row, settings.system.apply for APPLY
CHANGES, and the service's Keep or Revert confirmation after a display
change. The service owns the settings.* state; a document it serves must
declare all of it (UI_RetainedSettingsDocument), which page_state does.
Volume and Reverse Channels are not in the service's catalog and set their
CVars at once through settings.player.set.

build_doom3_menus.py writes the document.
"""

from __future__ import annotations

import system_display_catalog
from doom3_menu_kit import (
    FACE_BANK, FULL, NO_POINTER, U, Document, box, colour, dialog, group, keyword, label, length, number, path, rgb, solid,
    stroke, token, typeface, vector, walk,
)
from doom3_menu_options import BRIDGE, FLAIRS, apply_bar, row_label, row_plate, slider_row, value_states
from doom3_menu_pages import PLACEHOLDER, page_frame, page_shell, title_and_rule

# The settings service's catalog (SystemSettingsHost::Schema()): each
# setting's draft and baseline state, its type and initial value.
CATALOG = {
    **{key: ("string", "") for key in ("com_performancePreset", "r_renderer", "r_rendererBenchmarkPreset", "r_renderApi", "r_renderDevice")},
    **{key: ("boolean", False) for key in (
        "r_bloom", "r_borderless", "r_crt", "r_fullscreen", "r_fullscreenDesktop", "r_hdrToneMap", "r_lightGridPreload", "r_shadows",
        "r_skipBump", "r_skipSky", "r_skipSpecular", "r_ssao", "r_useLightGrid", "ui_aspectCorrection", "image_downSize",
        "image_downSizeBump", "image_downSizeSpecular", "image_ignoreHighQuality", "image_writeGeneratedImages", "r_motionBlur",
        "r_shadowMapCSM", "r_shadowMapProjectedCSM", "r_shadowMapCascadeStabilize", "r_motionBlurObjectVectors",
        "r_shadowMapHashedAlpha", "r_shadowMapTranslucentReceivers", "r_useShadowMap", "s_useEAXReverb")},
    **{key: ("boolean", True) for key in ("r_shadowMapPointLights", "r_hdrSceneTarget")},
    **{key: ("number", 0) for key in (
        "r_brightness", "r_customHeight", "r_customWidth", "r_displayRefresh", "r_forceAmbient", "r_mode", "r_multiSamples",
        "r_multiScreen", "r_postAA", "r_screen", "r_screenFraction", "r_swapInterval", "r_windowHeight", "r_windowWidth",
        "com_machineSpec", "com_maxfps", "image_anisotropy", "image_downSizeBumpLimit", "image_downSizeLimit",
        "image_downSizeSpecularLimit", "image_usePrecompressedTextures", "r_rendererUploadFrameBuffers", "r_rendererUploadMegs",
        "r_shadowMapMaxUpdatesPerView", "r_shadowMapCascadeCount", "r_shadowMapPointFilterMode", "image_picmip", "r_shadowMapSize",
        "s_maxEmitterChannels", "s_maxSoundsPerShader", "s_numberOfSpeakers")},
    "r_shadowMapPointSize": ("number", 512), "r_shadowMapFilterTaps": ("number", 9), "r_shadowMapPointFilterTaps": ("number", 9),
    "r_shadowMapFilterMode": ("number", 2), "r_shadowMapAtlasSize": ("number", 4096), "r_ssaoSamples": ("number", 20),
    "r_bloomMipCount": ("number", 5), "r_motionBlurSamples": ("number", 8), "ui_retainedScale": ("number", 1),
    "ui_retainedTextScale": ("number", 1),
}
RENDER_SLOTS = 32   # the renderer device list (RenderingSettings)
MODE_SLOTS = system_display_catalog.MODE_SLOTS

# Doom 3's four video qualities as the engine's performance presets.
QUALITIES = (("low", "#str_02149"), ("balanced", "#str_02148"), ("quality", "#str_02147"), ("ultra", "#str_04078"))

STR = {
    "title": "#str_00183", "video": "#str_02145", "audio": "#str_02158", "quality": "#str_02146", "size": "#str_02153",
    "fullscreen": "#str_02154", "brightness": "#str_02155", "vsync": "#str_04126", "aa": "#str_04128", "shadows": "#str_04123",
    "specular": "#str_04124", "bump": "#str_04125", "volume": "#str_02163", "reverse": "#str_02161", "apply": "#str_04062",
    "apply.hint": "#str_04074", "yes": "#str_00836", "no": "#str_00837", "off": "#str_00641",
    "keep.title": "#str_229993", "keep": "#str_229994", "revert": "#str_229995", "retry": "#str_229996",
    "discard.title": "#str_42934", "discard": "#str_42935", "keep.editing": "#str_229999", "ready": "#str_230007",
}

# Stock open-state plate (AnimSystemUp) in canvas u, with the apply bar's notch.
SYSTEM_PLATE = [(183, 26), (525, 26), (557, 58), (557, 365), (535, 387), (452, 387), (437, 372), (272, 372), (257, 387), (193, 387),
                (161, 355), (161, 48)]
ROW_LEFT = 35.0   # u: a row in its group box
PITCH = 21.0


def st(key: str) -> dict:
    return {"state": key}


def op(name: str, *args) -> dict:
    return {"op": name, "args": list(args)}


def no(term) -> dict:
    return op("!", term)


def both(*terms) -> dict:
    result = terms[0]
    for term in terms[1:]:
        result = op("&&", result, term)
    return result


# The draft takes edits while it is open and nothing is under way.
EDITABLE = both(st("settings.open"), op("==", st("settings.phase"), 1), no(st("settings.busy")), no(st("settings.confirmationVisible")),
                no(st("page.discardVisible")))


def page_state() -> dict:
    """Every state the page declares: the service's whole settings.* schema
    (UI_SettingsStateSchema) and the page's own."""
    state = {}
    for key, (kind, initial) in CATALOG.items():
        state[f"settings.draft.{key}"] = {"type": kind, "initial": initial}
        state[f"settings.baseline.{key}"] = {"type": kind, "initial": initial}
    for key in ("open", "dirty", "busy", "canApply", "canConfirm", "canRevert", "canRetry", "confirmationVisible", "msaaAvailable"):
        state[f"settings.{key}"] = {"type": "boolean", "initial": False}
    state.update({
        "settings.phase": {"type": "number", "initial": 0}, "settings.remaining": {"type": "number", "initial": 0},
        "settings.request": {"type": "string", "initial": ""}, "settings.message": {"type": "string", "initial": STR["ready"]},
        "page.discardVisible": {"type": "boolean", "initial": False},
    })
    for key in ("committed", "mapLoaded", "consumed", "effective", "pending"):
        state[f"settings.lightGrid.{key}"] = {"type": "boolean", "initial": False}
    for key in ("available", "fallback"):
        state[f"settings.renderer.{key}"] = {"type": "boolean", "initial": False}
    # What the service says about the antialiasing count it can draw (upstream's FPS-05); the page shows neither.
    state["settings.msaa.clamped"] = {"type": "boolean", "initial": False}
    state["settings.msaa.status"] = {"type": "string", "initial": ""}
    state.update(system_display_catalog.keys())
    render = {"catalog": "string", "count": "number", "selected": "number", "active": "string", "pending": "boolean",
              "autoDetect": "boolean", "canRestart": "boolean", "canChoose": "boolean", "vulkan": "boolean", "gl": "boolean",
              "gles": "boolean", "notice": "string", "backend": "string"}
    for index in range(RENDER_SLOTS):
        render[f"{index}.label"], render[f"{index}.usable"] = "string", "boolean"
    for key, kind in render.items():
        initial = {"string": "", "boolean": False, "number": -1 if key == "selected" else 0}[kind]
        state[f"settings.render.{key}"] = {"type": kind, "initial": initial}
    return state


def group_box(ident: str, key: str, top: float, height: float) -> list:
    """Section 6.6's group box: a body in rule.group under a 16 u header band
    in rule.group.header, its bottom-trailing corner chamfered, with a Bank
    caption in text.dim."""
    w, h = U * 350, U * height
    body = vector(f"{ident}-box", {**box(20, top, 350, height), **NO_POINTER}, [
        path("body", [(0, 0), (w, 0), (w, h - U * 9), (w - U * 9, h), (0, h)], fill=solid(rgb("#99CCFF", 0.10))),
        path("header", [(0, 0), (w, 0), (w, U * 16), (0, U * 16)], fill=solid(rgb("#99CCFF", 0.13)))])
    caption = label(f"{ident}-caption", key, {**box(28, top + 2, 200, 12), **typeface(FACE_BANK, 0.25, 12, token("text.dim")), **NO_POINTER})
    return [body, caption]


def step_row(doc: Document, ident: str, key: str, top: float, values: list, program: list, enabled: dict) -> dict:
    """A choice (section 6.7): bare text after the gutter that steps to the
    next value on a click. `values` is [(node id suffix, text key or None,
    shown expression)]; a None key is a text the caller binds."""
    nodes = []
    for suffix, text_key, shown in values:
        node = label(f"{ident}-{suffix}", text_key or PLACEHOLDER, {**box(200, 0, 96, 16), **typeface(FACE_BANK, 0.25, 16, token("text.value")),
                                                                    **NO_POINTER, "display": keyword("none"), "overflow": keyword("hidden")})
        doc.bind(f"{ident}-{suffix}.display", f"{ident}-{suffix}", "display", op("select", shown, "block", "none"))
        nodes.append(node)
    doc.events[f"{ident}Step"] = program
    ids = value_states(doc, ident, tuple(node["id"] for node in nodes))
    doc.bind(f"{ident}.enabled", ident, "enabled", enabled)
    return group(ident, box(ROW_LEFT, top, 300, 16), [row_plate(ident, 300), row_label(ident, key, 4, 176, "right"), *nodes],
                 control={"role": "button", "label": key, "event": f"{ident}Step", "states": ids})


def edit(doc: Document, name: str, values: dict) -> dict:
    """An instruction that stages literal values in the draft."""
    doc.actions[name] = {"operation": "settings.system.edit", "arguments": values}
    return {"op": "action", "action": name}


def flag_row(doc: Document, ident: str, key: str, top: float, setting: str, inverse: bool = False) -> dict:
    """A yes-or-no setting; `inverse` shows a skip setting as its Enable row."""
    draft = st(f"settings.draft.{setting}")
    shown = no(draft) if inverse else draft
    program = [{"op": "if", "condition": draft, "then": [edit(doc, f"{ident}Clear", {setting: False})],
                "else": [edit(doc, f"{ident}Set", {setting: True})]}]
    return step_row(doc, ident, key, top, [("yes", STR["yes"], shown), ("no", STR["no"], no(shown))], program, EDITABLE)


def label_tree(prefix: str, index: dict, low: int, high: int):
    """The label the slot `index` names: a balanced tree of selects."""
    if low == high:
        return st(f"{prefix}.{low}.label")
    middle = (low + high) // 2
    return op("select", op("<=", index, middle), label_tree(prefix, index, low, middle), label_tree(prefix, index, middle + 1, high))


def system_document() -> dict:
    """The SYSTEM page: Video Settings (quality, fullscreen, screen size,
    brightness, vertical sync, antialiasing, shadows, specular, bump maps)
    and Audio Settings (volume, reverse channels) in group boxes, the
    service's status line, and APPLY CHANGES in the plate's notch.

    Every video row edits the service's draft; nothing changes until APPLY
    CHANGES. A display change then asks to be kept, and reverts by itself
    when its countdown ends. Back with unapplied changes asks before it
    discards them."""
    doc = Document("opend3.system")
    doc.state.update(page_state())
    doc.actions.update({
        "begin": {"operation": "settings.system.begin", "arguments": {}},
        "apply": {"operation": "settings.system.apply", "arguments": {}},
        "cancel": {"operation": "settings.system.cancel", "arguments": {}},
        "dismiss": {"operation": "ui.dismiss", "arguments": {}},
        "keep": {"operation": "settings.system.confirm", "arguments": {"request": st("settings.request")}},
        "revert": {"operation": "settings.system.revert", "arguments": {"request": st("settings.request")}},
        "retry": {"operation": "settings.system.retry", "arguments": {"request": st("settings.request")}},
        "modeNext": {"operation": "settings.system.displayMode", "arguments": {
            "index": op("%", op("+", st("settings.display.mode.selected"), 1), op("max", st("settings.display.mode.optionCount"), 1)),
            "catalog": st("settings.display.catalog")}},
    })
    for name in ("soundForward", "soundBack"):
        doc.session(name)

    content = [*title_and_rule("system", STR["title"], 375), *group_box("system-video", STR["video"], 36, 212),
               *group_box("system-audio", STR["audio"], 254, 62)]
    top = 56.0

    # Video Quality: Doom 3's four qualities, each one of the engine's presets.
    preset = st("settings.draft.com_performancePreset")
    for name, _key in QUALITIES:
        doc.actions[f"preset.{name}"] = {"operation": "settings.system.preset", "arguments": {"name": name}}
    chain = [{"op": "action", "action": "preset.low"}]
    for index in range(len(QUALITIES) - 2, -1, -1):
        chain = [{"op": "if", "condition": op("==", preset, QUALITIES[index][0]),
                  "then": [{"op": "action", "action": f"preset.{QUALITIES[index + 1][0]}"}], "else": chain}]
    known = None
    for name, _key in QUALITIES:
        known = op("==", preset, name) if known is None else op("||", known, op("==", preset, name))
    quality_values = [(name, key, op("==", preset, name)) for name, key in QUALITIES] + [("custom", None, no(known))]
    quality = step_row(doc, "system_quality", STR["quality"], top, quality_values, chain, EDITABLE)
    doc.bind("system_quality-custom.text", "system_quality-custom", "text", preset)
    content.append(quality)

    content.append(flag_row(doc, "system_fullscreen", STR["fullscreen"], top + PITCH, "r_fullscreen"))

    # Screen Size: the display's modes in exclusive full screen, stepped in
    # the service's list; otherwise the window's size, which the row shows.
    listed = both(st("settings.display.available"), st("settings.draft.r_fullscreen"), no(st("settings.draft.r_fullscreenDesktop")),
                  op(">", st("settings.display.mode.optionCount"), 0))
    size = step_row(doc, "system_size", STR["size"], top + 2 * PITCH, [("mode", None, listed), ("width", None, no(listed))],
                    [{"op": "action", "action": "modeNext"}], both(EDITABLE, listed))
    doc.bind("system_size-mode.text", "system_size-mode", "text",
             label_tree("settings.display.mode", st("settings.display.mode.selected"), 0, MODE_SLOTS - 1))
    doc.bind("system_size-width.text", "system_size-width", "text",
             {"op": "numberText", "args": [st("settings.draft.r_windowWidth")], "decimals": 0})
    height_node = label("system_size-height", PLACEHOLDER, {**box(248, 0, 48, 16), **typeface(FACE_BANK, 0.25, 16, token("text.value")),
                                                            **NO_POINTER, "display": keyword("none")})
    # The window's size reads width, a small cross, height.
    cross = vector("system_size-cross", {**box(240, 6, 4, 4), **NO_POINTER, "display": keyword("none")}, [
        path("a", [(0, 0), ({"fraction": 1}, {"fraction": 1})], closed=False, stroke=stroke(solid(token("text.value")), 1.2)),
        path("b", [({"fraction": 1}, 0), (0, {"fraction": 1})], closed=False, stroke=stroke(solid(token("text.value")), 1.2))])
    doc.bind("system_size-cross.display", "system_size-cross", "display", op("select", listed, "none", "block"))
    size["children"] += [height_node, cross]
    doc.bind("system_size-height.display", "system_size-height", "display", op("select", listed, "none", "block"))
    doc.bind("system_size-height.text", "system_size-height", "text",
             {"op": "numberText", "args": [st("settings.draft.r_windowHeight")], "decimals": 0})
    content.append(size)

    brightness = slider_row(doc, "system_brightness", STR["brightness"], top + 3 * PITCH, "r_brightness", "settings.draft.r_brightness",
                            0.5, 2.0, 0.1, 1)
    doc.actions["system_brightnessSet"] = {"input": "number", "operation": "settings.system.edit", "arguments": {"r_brightness": {"input": "value"}}}
    doc.bind("system_brightness.enabled", "system_brightness", "enabled", EDITABLE)
    content.append(brightness)

    sync = st("settings.draft.r_swapInterval")
    content.append(step_row(doc, "system_vsync", STR["vsync"], top + 4 * PITCH,
                            [("yes", STR["yes"], op("!=", sync, 0)), ("no", STR["no"], op("==", sync, 0))],
                            [{"op": "if", "condition": op("==", sync, 0), "then": [edit(doc, "vsyncOn", {"r_swapInterval": 1})],
                              "else": [edit(doc, "vsyncOff", {"r_swapInterval": 0})]}], EDITABLE))

    # Antialiasing: off, 2x, 4x, 8x, where the renderer offers it.
    samples = st("settings.draft.r_multiSamples")
    aa_chain = [edit(doc, "aa0", {"r_multiSamples": 0})]
    for value, following in ((4, 8), (2, 4), (0, 2)):
        aa_chain = [{"op": "if", "condition": op("==", samples, value), "then": [edit(doc, f"aa{following}", {"r_multiSamples": following})],
                     "else": aa_chain}]
    aa = step_row(doc, "system_aa", STR["aa"], top + 5 * PITCH,
                  [("off", STR["off"], op("==", samples, 0)), ("count", None, op("!=", samples, 0))], aa_chain,
                  both(EDITABLE, st("settings.msaaAvailable")))
    doc.bind("system_aa-count.text", "system_aa-count", "text", {"op": "numberText", "args": [samples], "decimals": 0})
    content.append(aa)

    content.append(flag_row(doc, "system_shadows", STR["shadows"], top + 6 * PITCH, "r_shadows"))
    content.append(flag_row(doc, "system_specular", STR["specular"], top + 7 * PITCH, "r_skipSpecular", inverse=True))
    content.append(flag_row(doc, "system_bump", STR["bump"], top + 8 * PITCH, "r_skipBump", inverse=True))

    # Audio: applied at once, outside the service's draft.
    doc.state["cvar.s_volume_dB"] = {"type": "number", "initial": -6, "cvar": "s_volume_dB"}
    doc.state["cvar.s_reverse"] = {"type": "boolean", "initial": False, "cvar": "s_reverse"}
    content.append(slider_row(doc, "system_volume", STR["volume"], 274, "s_volume_dB", "cvar.s_volume_dB", -40, 0, 1, 0))
    for name, value in (("On", True), ("Off", False)):
        doc.actions[f"system_reverse{name}"] = {"operation": "settings.player.set", "arguments": {"cvar": "s_reverse", "value": value}}
    reverse = st("cvar.s_reverse")
    content.append(step_row(doc, "system_reverse", STR["reverse"], 274 + PITCH,
                            [("yes", STR["yes"], reverse), ("no", STR["no"], no(reverse))],
                            [{"op": "if", "condition": reverse, "then": [{"op": "action", "action": "system_reverseOff"}],
                              "else": [{"op": "action", "action": "system_reverseOn"}]}], True))
    for node in content:
        if node["id"] in ("system_brightness", "system_volume"):
            node["properties"]["left"] = length(U * ROW_LEFT)

    # The service's status, in the player's language.
    status = label("system-status", STR["ready"], {**box(20, 318, 350, 26), **typeface(FACE_BANK, 0.25, 12, token("text.dim"), "center"),
                                                   **NO_POINTER, "overflow": keyword("hidden"), "white-space": keyword("normal")})
    doc.bind("system-status.text", "system-status", "text", st("settings.message"))
    content.append(status)

    # APPLY CHANGES acts while the draft can be applied.
    doc.events["apply"] = [{"op": "if", "condition": st("settings.canApply"), "then": [{"op": "action", "action": "apply"}]}]
    bar = apply_bar(doc, STR["apply"], 238, STR["apply.hint"], None)
    bar["control"].pop("action", None)
    bar["control"]["event"] = "apply"
    doc.bind("page_apply.enabled", "page_apply", "enabled", both(st("settings.canApply"), no(st("settings.confirmationVisible"))))

    # A display change asks to be kept (the service's confirmation). Its
    # buttons carry the request they answer; Back reverts.
    remaining = label("confirmModal-remaining", PLACEHOLDER, {**box(30, 60, 300, 20), **typeface(FACE_BANK, 0.25, 20, token("text.value"), "center")})
    doc.bind("confirmModal-remaining.text", "confirmModal-remaining", "text", {"op": "numberText", "args": [st("settings.remaining")], "decimals": 0})
    doc.events["confirmationBack"] = [{"op": "if", "condition": st("settings.canRevert"), "then": [{"op": "action", "action": "revert"}]}]
    confirm = dialog(doc, "confirmModal", STR["keep.title"], STR["keep.title"], [
        ("settings_keep", STR["keep"], 20, "keep", None, None), ("settings_retry", STR["retry"], 134, "retry", None, None),
        ("settings_revert", STR["revert"], 248, "revert", None, None)], initial="settings_revert", back="confirmationBack",
        animate=False, contents=[remaining], button_face=FACE_BANK)
    doc.bind("settings_keep.enabled", "settings_keep", "enabled", st("settings.canConfirm"))
    doc.bind("settings_revert.enabled", "settings_revert", "enabled", st("settings.canRevert"))
    nodes = {node["id"]: node for node in walk(confirm)}
    nodes["settings_retry"]["properties"]["display"] = keyword("none")
    doc.bind("settings_retry.display", "settings_retry", "display", op("select", st("settings.canRetry"), "block", "none"))

    # Back with unapplied changes asks first (section 7.4: focus opens on the
    # choice that changes nothing).
    question = label("discardModal-body", STR["discard.title"], {**box(30, 44, 300, 30), **typeface(FACE_BANK, 0.25, 15, token("text.active")),
                                                                 "white-space": keyword("normal")})
    discard = dialog(doc, "discardModal", STR["title"], STR["discard.title"], [
        ("discard_yes", STR["discard"], 44, None, "discard", None), ("discard_no", STR["keep.editing"], 196, None, "continueEditing", None)],
        initial="discard_no", back="continueEditing", animate=False, contents=[question], button_width=124.0, button_face=FACE_BANK)
    # Both dialogs follow the service's state rather than their own.
    for ident, shown in (("confirmModal", st("settings.confirmationVisible")),
                         ("discardModal", both(st("page.discardVisible"), no(st("settings.confirmationVisible"))))):
        doc.bindings = [binding for binding in doc.bindings if binding["id"] not in (f"{ident}.display", f"{ident}-contents.display")]
        doc.bind(f"{ident}.display", ident, "display", op("select", shown, "block", "none"))
        nodes = {node["id"]: node for node in walk(confirm if ident == "confirmModal" else discard)}
        nodes[f"{ident}-contents"]["properties"]["display"] = keyword("block")
        for event in (f"{ident}Show", f"{ident}Hide"):
            doc.events.pop(event, None)
        for key in (f"{ident}.visible", f"{ident}.contents"):
            doc.state.pop(key, None)
    hide = {"op": "setState", "values": {"page.discardVisible": False}}
    doc.events["continueEditing"] = [hide, {"op": "action", "action": "soundBack"}]
    doc.events["discard"] = [{"op": "if", "condition": both(st("page.discardVisible"), no(st("settings.busy"))),
                              "then": [{"op": "action", "action": "cancel"}, hide, {"op": "action", "action": "dismiss"}]}]
    idle = both(no(st("settings.busy")), op("||", op("==", st("settings.phase"), 0), op("==", st("settings.phase"), 1)))
    doc.events["onBack"] = [{"op": "if", "condition": st("page.discardVisible"), "then": [{"op": "call", "event": "continueEditing"}], "else": [
        {"op": "if", "condition": idle, "then": [
            {"op": "if", "condition": st("settings.dirty"), "then": [{"op": "setState", "values": {"page.discardVisible": True}},
                                                                      {"op": "action", "action": "soundForward"}],
             "else": [{"op": "action", "action": "cancel"}, {"op": "action", "action": "dismiss"}]}]}]}]

    document = page_frame(doc, page_shell(doc, SYSTEM_PLATE, BRIDGE, FLAIRS), content, bar, [confirm, discard], on_canvas=True,
                          content_box=(165, 30, 390, 370))
    document["events"]["onActivate"] = [{"op": "action", "action": "begin"}, {"op": "setState", "values": {"page.discardVisible": False}},
                                        *document["events"]["onActivate"]]
    # Opened from the in-game multiplayer menu's System tab (the session sets
    # page.ingame) the page stands over the game under that menu's strip:
    # there is no list to bridge to, and the scene's edge glow and the main
    # menu's hint line are not that menu's.
    doc.state["page.ingame"] = {"type": "boolean", "initial": False}
    for node in walk(document["root"]):
        if node["id"] in ("plate-bridge", "plate-bridge-flash", "plate-flair", "plate-flair-flash", "edge-glow", "hint-line"):
            node["properties"]["display"] = keyword("block")
            doc.bind(f"{node['id']}.display", node["id"], "display", op("select", st("page.ingame"), "none", "block"))
    # The plate is made to stand over the menu's dark scene. Over a lit game,
    # whose own messages cross it, it takes a black backing of its own shape.
    # It runs under the apply bar in the plate's notch as well.
    shape = [(445, 397) if point == (437, 372) else (264, 397) if point == (272, 372) else point for point in SYSTEM_PLATE]
    xs, ys = [x for x, _ in shape], [y for _, y in shape]
    backing = vector("plate-ingame", {**box(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)), **NO_POINTER, "display": keyword("none")},
                     [path("backing", [(U * (x - min(xs)), U * (y - min(ys))) for x, y in shape], fill=solid(rgb("#000000", 0.6)))])
    doc.bind("plate-ingame.display", "plate-ingame", "display", op("select", both(st("page.ingame"), st("page.shown")), "block", "none"))
    canvas = next(node for node in walk(document["root"]) if node["id"] == "canvas")
    canvas["children"].insert(next(index for index, node in enumerate(canvas["children"]) if node["id"] == "plate-body"), backing)
    return document
