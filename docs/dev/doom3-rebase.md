# openD3 on the openQ4 engine: rebase record

This is the working record of openD3's move onto the current openQ4 engine. It
states what was done, what has been verified and how, and what is still open.
Update it when any of that changes; it is the place a future upstream sync
starts from.

## Where openD3 came from

- openD3 forked from openQ4 `abb9a688` (2026-02-18) and carried six commits of
  Doom 3 adaptation on that snapshot. The fork tree was byte-identical to that
  openQ4 commit apart from 42 stripped Quake 4 asset files.
- The game library lived in a companion repository, `openD3-GameLibs`, and was
  synchronised into `src/game` by script.
- openQ4 then gained about 2,350 commits: the renderer module split with the
  modern OpenGL and native Vulkan backends, shadow mapping, the SDL3 platform
  layer, the hardened savegame framework, the content pack pipeline and
  in-tree game sources.

The pre-rebase tree, including the uncommitted work that was on `main` at the
time, is preserved on the branch `pre-oq4-rebase` and is the first parent of
the rebase merge.

## How the rebase was done

The branch history, oldest first:

1. **Merge openQ4** through `55bbe166a`, taking the upstream tree unchanged.
   openQ4's history is now part of openD3's, so later syncs are ordinary
   merges of `openq4-upstream/main`. The latest sync merged upstream through
   `d3056567a` (2026-11-21): HBAO and GTAO beside SSAO (`r_ssaoMethod`) with
   SSAO filtered so it no longer dithers, shadowed volumetric haze, parallax
   occlusion mapping for PBR height maps, one loading-frame pacer for the
   start-up and level loading screens (`LoadingFramePacer`,
   `common->LoadingCheckpoint`), a map change from the start-up screen
   handed straight to the loading screen, the level's first view drawn
   unseen before the hand-over, the start autosave written on the storage
   worker, texture reloads limited to the images a setting reaches, spread
   across frames and decoded on worker threads, and cheaper retained UI
   events. The one before it, through
   `b1f6ed617` (2026-11-21), brought one GLSL program per shader source with
   unchanged uniforms skipped, sixteen `shaderTexture`s per GLSL stage, and
   the retained runtime's frame savings (no layout pass at rest beside
   settings controls, lists, fields and scrollbars; sliding vectors
   compiled at cached phases; a vector's alike paths drawn as one
   geometry). The one before that, through
   `966d8ae6f` (2026-11-20), brought cascaded outdoor shadow maps on Quality and
   Ultra, a per-receiver normal offset for distant lights' shadows, layered
   OpenGL point-shadow cubes, BC6H (HDR) textures and more texture-pack
   formats, a pak found in two search roots mounted once, particle, decal
   and reverb savings (FPS-08), and upstream's own fix for
   surface GUI winding. The one before it, through `65305957d` (2026-11-18),
   brought PNG textures and screenshots, BC7 decoding and texture-pack bump
   rebuilds, render demos in checked blocks with keyframes, network protocol
   2.42 and its netcode fixes, the in-game updater, PCSS-lite soft shadows on
   the modern OpenGL path, self-shadowing characters under shadow maps,
   light-interaction and collision bookkeeping cuts, VR body and controller
   work, and retained interface warming. Before those, the syncs through
   `f3b2f9583` (2026-11-14) and `7c74cd712` (2026-11-11) brought the
   shadow-mapping fixes (FPS-03, REN-01).
2. **Remove the Quake 4 game library and content.** `src/game` and
   `src/mpgame` (Quake 4 SDK), the SDK licence and the Quake 4 runtime content
   leave the tree. The engine-side content moves to `content/baseod3`.
3. **Import the Doom 3 game library with its history.** `src/game` (base game)
   and `src/d3xp` (Resurrection of Evil) come from `openD3-GameLibs` `c450f9c`
   at their existing paths; that repository's history is a parent of the
   import commit. See [game-source-provenance.md](game-source-provenance.md).
4. **Transplant openPREY's engine layer.** openPREY already carried, on openQ4
   `b4d3fd700`, the engine work a Doom 3-lineage game needs: the unified
   in-tree game module build, Doom 3 particle and FX declarations,
   `idRenderModelPrt`, the Doom 3 `.proc` header, AAS 1.07, the collision
   world fallbacks, `idBitMsg` helpers, `idSoundEmitter` reference sounds, ARB
   interaction stages and the game API bridging in the session and async
   layers. That delta was applied by three-way merge, unedited, as its own
   commit.
5. **Convert that layer from Prey to Doom 3** and get the tree building,
   running and staging. The sections below describe the result.

## Engine/game contract

- **One define marks the difference from upstream.** `OPEND3` is set for every
  target. It guards the engine sites where Doom 3's game API or file formats
  differ from openQ4's Quake 4 ones: the AAS file version (1.07), the map
  geometry CRC (Doom 3 does not hash `model` key/values), the Quake 4 game
  services BSE and the async layer would otherwise call, Quake 4-only
  precaches and the Quake 4 language-archive check.
- **The game API is Doom 3's**, `GAME_API_VERSION` 8, defined in
  `src/game/Game.h`. The engine includes that header. Call sites pass Doom 3's
  arguments (`ServerClientConnect` with the guid, `ClientPrediction` with
  `lastPredictFrame`). `src/framework/Doom3GameCompat.h` answers the Quake 4
  game services upstream's retained screens and ban list ask for.
- **Gate D9.** Bots, multi-view demos and the repeater need game API calls
  Doom 3 does not have. Their entry points are compiled but inert and carry
  `OPEND3-GATED(D9)` markers. Re-enabling one is game API design work.
- **Collision handles.** Doom 3 game code uses integer collision handles (0 is
  the world). `idCollisionModelManager` provides them as inline overloads over
  the engine's pointer interface, so the vtable matches upstream.
- **Decl parsing.** The engine parses decls through the three-argument
  `Parse( text, length, noCaching )`. Game-side decl classes must implement
  it; `idDeclModelDef` forwards it to its two-argument parser.
- **Shutdown order.** The engine destroys game-owned decls after
  `idGame::Shutdown` returns. The game releases model-def animation references
  in `Shutdown`, before its animation manager goes away.
- **BSE** stays compiled and linked, as in openPREY, but nothing drives it:
  Doom 3 uses its own particle and FX declarations.

## Game modules

| Module | Source | Defines | State |
| --- | --- | --- | --- |
| `game_<arch>` | `src/game` | | Builds, loads and runs |
| `game-d3xp_<arch>` | `src/d3xp` | `_D3XP`, `CTF` | Builds, loads and initialises; not played |

`src/d3xp` was imported in id's GPL form. The 64-bit and engine-ABI port that
`src/game` already carried was applied to it by three-way merge per file
(base: id's GPL `neo/game`; incoming: the ported `src/game`; target:
`src/d3xp`). `Anim_Import.cpp`, `SaveGame.cpp` and `PlayerView.cpp` were
resolved by hand. A fix that applies to both games goes into both trees.

The engine selects `game-d3xp` when `d3xp` is `fs_game` or `fs_game_base`.
`d3xp` is an official game directory: it needs no `mod.json`, its retail
`game0x.pk4` binary packs are left out of the search path like the base
game's, and the module is loaded from `baseod3/`. The engine's own expansion
switch, `ID_ALLOW_D3XP`, is on.

## Verified

Windows x64, `debugoptimized`, MSVC 19.50, 2026-11-11, against the Steam
release of Doom 3 (1.3.1 packs):

- Configure, compile, link and stage of the client, the dedicated server, the
  OpenGL and Vulkan renderer modules and both game modules.
- `vk_shader_header_pin` passes after the Vulkan SPIR-V headers were
  regenerated from the merged shader sources.
- Startup finds the Steam install without `fs_basepath`, validates
  `pak000`–`pak004` by checksum and leaves `game00`–`game03` out of the search
  path.
- `game/mars_city1` loads in single player (1,969 entities), plays the intro
  cinematic with its in-world GUIs and remote camera views, writes its
  autosave and exits cleanly, on OpenGL. The same map loads and renders on the
  native Vulkan renderer (`r_renderApi vulkan`).
- The stock main menu path starts and plays the intro video.
- Both consoles carry Doom 3's colours, seen over the main menu: the in-game
  console draws cyan text, prompt, version and rule on opaque black, and the
  Win32 system console draws the same cyan on a dark slate taken from the
  menus' dialog plate. The completion popup, text selection and the SDL system
  console on Linux and macOS take the same palette but were not looked at.
- GUI and console text is drawn from the five reconstructed TrueType faces by
  default ([font system](ttf-font-system.md)). At startup the engine loads
  `fonts/english.ttf`, `an.ttf`, `bank.ttf`, `micro.ttf` and `bigchars.ttf`
  from `baseod3/pak0.pk4`, fits each face's 12, 24 and 48 point slots to the
  retail `.dat` metrics and rebuilds the console sheet. Captured at 2560x1440
  on OpenGL: the main menu, and the HUD on `game/alphalabs1` (loaded with
  `devmap`, 2,106 entities). `tools/tests/ttf_font_integrity.py` passes.
- Wide and tall screens ([layout](widescreen-layout.md)): with the layout
  patches in `baseod3/pak0.pk4`, captured on OpenGL at 4:3 (1280x960, unchanged
  from the stock layout), 16:9 (2560x1440), 21:9 (2400x1028) and 4:5
  (1024x1280). The main menu and its Options, New Game, Load Game,
  Multiplayer (Create Server), Credits and Exit screens (driven with
  `opend3_guiAction`) reach both screen edges at 21:9 and stay centred
  vertically at 4:5 with no parked panel in view. The HUD on
  `game/alphalabs1` sits in the screen corners at 16:9 and 21:9. The PDA,
  opened there with `give pda` and `impulse 19`, keeps its 4:3 canvas over the
  softened view, also on Vulkan at 1920x1080. The loading screens
  (`alphalabs1`, `generic`), the death screen, the multiplayer HUD, the
  scoreboard and the game-over screen were shown with `testGUI` at 21:9 and,
  for the loading screen and multiplayer HUD, at 4:5. On 20 November 2026, on
  Vulkan at 1680x720, 1280x720, 960x1280 and 720x1280: the HUD's health,
  armour and ammunition counts on `game/alphalabs1` and the multiplayer HUD's
  on `game/mp/d3dm1` sit in their frames at the two tall shapes (they slid
  out sideways before the shear pivot followed screen alignment), the
  message line ("Game Saved") starts at the left edge, and the in-game
  multiplayer menu's line about Escape, stock and retained, sits in the
  bottom-left corner. On OpenGL at the same four shapes the stock message
  box's dim covers the whole screen. The main menu's grid
  continues across the canvas edge at 16:9 with every fifth line brighter, in
  step on both sides, and above and below it at 4:5. With the profile in
  `.home` (a borderless 2560x1440 window, 150% display scaling) on OpenGL and
  Vulkan, the menu's arrow is drawn at 32 units with its tip within 2 px of the
  real pointer at the centre, the corners and the left expansion; with the
  window unfocused, only the system pointer shows. On OpenGL with the real
  pointer moved over each in turn, MULTIPLAYER, LOAD GAME (straight after
  MULTIPLAYER), NEW GAME, OPTIONS, MODS and EXIT each light up under the arrow
  with their own tooltip, and so do CONTROLS and GAME OPTIONS in the opened
  Options list.
- Shadow maps (`r_useShadowMap 1`, with `r_shadowMapPointLights 1`) on
  OpenGL and Vulkan, after the `7c74cd712` sync. Captured from the starting
  view of `mc_underground`, `alphalabs1`, `delta2a`, `hell1`, `recycling1` and
  `site3` with shadow maps and with stencil shadows. The pictures match, and no
  log reports a shadow-map error. Frozen with `g_stopTime 1` and measured, the
  mapped and stencil pictures of `alphalabs1` differ in about 5,000 of 3.7
  million pixels on both backends (the contact edges of the soft shadows),
  `hell1` in 0 (OpenGL) and 182 (Vulkan), and no mapped pixel is brighter than
  the unshadowed picture. Before the specular fix below, OpenGL differed in
  311,739 pixels there.
- Shadow maps again after the `f3b2f9583` sync, on the same six starting views
  on OpenGL and Vulkan, against the build before the sync (`6a720672f`). Each
  launch freezes one frame (`+g_stopTime 1`, view weapon hidden, mouse off)
  and captures it mapped, stencilled, unshadowed and mapped again. On
  `mc_underground`, `alphalabs1` and `recycling1` the merged build's mapped
  and stencil pictures differ in the same pixels as before the sync, by more
  than 8 levels in 28,843, 6,867 and 29,947 of 3.7 million (Vulkan; OpenGL
  within 120 of those), along the soft shadows' contact edges; on Vulkan its
  mapped `mc_underground` and `recycling1` frames are identical to the old
  build's. `hell1`'s mapped, stencil and unshadowed frames are identical on
  both backends. `delta2a` and `site3` keep animated lights while frozen, so
  their frames differ between two mapped captures as much as between mapped
  and stencil, before the sync and after. The old build marked `hell1`'s
  lights with nothing to cast for the stencil fallback 30 times (OpenGL) and
  6 times (Vulkan) in one launch; the merged build marks none, in any capture.
  With time running, `mc_underground` and `alphalabs4`, whose lights swing on
  binds, render mapped on both backends with no shadow-map error or fallback.
- No stencil shadows under shadow maps (2026-11-22). A temporary hook logged
  every stencil volume draw while `r_useShadowMap` was 1 (OpenGL
  `RB_StencilShadowPass`, Vulkan `VK_StencilShadowPass`). Each of 27
  campaign maps, `mars_city1` to `cpuboss`, ran on both backends: about
  900 frames from the start, with god mode, `give all`, the flashlight raised,
  a zombie and an imp spawned beside the player and noclip on. With point
  lights mapped and subview policy 0 the hook logged nothing on either
  backend. With `r_shadowMapPointLights 0` (Enhanced's old value) it logged
  92 draws on `alphalabs1`'s start on each. `delta2a`'s bathroom mirror with
  the flashlight drew no stencil under subview policy 0 or 1. Applying
  Enhanced to a profile holding `r_shadowMapPointLights 0` sets it to 1, and
  the preset self-test passes.
- The same hook, with two more that logged a light drawn unshadowed for a
  missing map (OpenGL `RB_ShadowMapRunPass`, Vulkan's receiver pass) and a
  remote camera view, on a tour of each of the 27 maps on both backends: 16
  places spread over the map, chosen from where players, monsters, items and
  path corners stand, four headings each, with the flashlight raised. It
  found three causes, now fixed: Vulkan's scratch cube pool was full (85 cubes;
  one view inside `alphalabs3` needed 92), two empty surfaces of `hell1`'s
  `guardianroom.lwo` sent seven lights to stencil on both backends, and
  Vulkan drew stencil for the optional ownership of a light whose other
  ownership had to be mapped (a spot in `hellhole`). After the fixes no view
  inside a map drew a stencil volume or an unshadowed light on either
  backend. Some places lie outside the playable space, where Doom 3 shows
  every area (300 to 555 lights in one view): there Vulkan's 256-light table
  overflows and lights go unshadowed for a frame, then stencil. Players
  never stand there. The `alphalabs2` security console, driven through its
  own `setkeyval` commands, showed three cameras' live views on both
  backends with no stencil or unshadowed light; the mirrors of `delta2a` and
  `delta3` likewise. On each of `d3dm1` to `d3dm5` a listen server and a
  second client (OpenGL and Vulkan in both roles across the five) ran with
  the server's player moved in front of the client, so the client drew
  another player under shadow maps: neither logged a stencil volume or an
  unshadowed light. Not covered: Resurrection of Evil
  (this machine has no `d3xp/pak000.pk4`), combat beyond spawned monsters
  standing by, the cinematics.
- After the `65305957d` sync (2026-11-18), on the staged build: configure,
  compile and stage of every target; `vk_shader_header_pin` passes.
  `game/mars_city1` loads on OpenGL (1,969 entities), runs its intro, saves
  and loads back into the cinematic. Its log carries the same set of warnings
  as the build before the sync run with the same commands, and no error.
  `game/alphalabs1` loads and draws with its HUD on Vulkan (2,106 entities).
  A listen server on `game/mp/d3dm1` (`spawnServer`, Deathmatch) spawns 887
  entities and shows the warmup HUD. The retained title (`ui_retained 1`)
  draws as before. Not run: a remote client against a server (network
  protocol 2.42), the updater, texture packs, PNG textures, the expansion, and
  upstream's native tests (`build_native_tests`).
- In-world GUIs after that sync. Upstream's mirrored-model winding
  (`1a09a52a2`) turned the front face for any space with a reflecting model
  matrix, and a surface GUI's matrix through its texture axes is one, so the
  merged build drew `mars_city1`'s Traffic Monitoring Station and console
  screens black on OpenGL. A surface GUI's space now winds by its host's
  reflection alone (`R_SpaceWindsReflected` in `tr_local.h`, used by
  `RB_SetSurfaceWinding` and the Vulkan `VK_Exec_SurfaceMirrored`). Captured
  on OpenGL and Vulkan: the station screen during the intro and the control
  room's consoles after a save and load draw as before the sync, the text
  reads the right way round, and the OpenGL log has the same warnings as the
  build before the sync.
- After the `966d8ae6f` sync (2026-11-20), on the staged build: configure,
  compile and stage of every target, and `vk_shader_header_pin` passes on the
  regenerated headers. `game/mars_city1` loads on OpenGL and Vulkan (1,969
  entities), saves and loads, and draws the Traffic Monitoring Station and
  the control room's consoles. Its OpenGL log has the same warnings as the
  pre-sync build run the same way, and no log has an error. `game/alphalabs1`
  draws with its HUD on Vulkan, and with `r_useShadowMap 1` and
  `r_shadowMapPointLights 1` on OpenGL and Vulkan with no shadow warning. A
  `game/mp/d3dm1` listen server spawns 887 entities and shows the warmup HUD,
  and the retained title draws as before. Not run: the new outdoor cascades
  (no outdoor map was captured), BC6H textures, texture packs and a remote
  client.
- After the `b1f6ed617` sync (2026-11-21), on the staged build: compile and
  stage of every target. At 1280x720 `game/alphalabs1` draws with its HUD
  on OpenGL, and a `game/mp/d3dm1` listen server draws the world and HUD on
  OpenGL and Vulkan and the death screen on OpenGL. The retained title and
  its pages draw as before (`docs/dev/ui/retained-menus.md`, second
  refinement round), and the start-up screen draws in about 120 draws a
  frame where it took about 240. Logs have no error. Not run: shadow maps,
  `mars_city1`, saves, and Resurrection of Evil.
- After the `d3056567a` sync (2026-11-21), on the staged build at 1280x720:
  compile and stage of every target, and `vk_shader_header_pin` passes on
  the regenerated headers. `game/mars_city1` loads on OpenGL (1,969
  entities), draws the Traffic Monitoring Station, saves and loads.
  `game/alphalabs1`, started with `map`, draws with its HUD on OpenGL and
  Vulkan and writes its start autosave through the storage worker; with
  `r_ssao 1`, `r_ssaoMethod` 0, 1 and 2 (SSAO, HBAO, GTAO) each change the
  picture on both renderers. With `ui_retained 1`, `+map game/alphalabs1`
  at launch goes from the start-up screen to the loading screen and into the
  level on Vulkan, and at the title `opend3_system open` is accepted
  (`result=1`) and the SYSTEM page draws. A `game/mp/d3dm1` listen server
  draws the world and HUD on Vulkan (887 entities), and the dedicated server
  spawns the same map with `si_map` and `spawnServer`. Logs have no error;
  the warnings are the known retail ones. Not run: shadow maps, volumetric
  haze and parallax occlusion (no stock Doom 3 content uses them), texture
  reloads from the settings, and Resurrection of Evil.
- The game library's loading checkpoints and indexed script immediates
  (2026-11-21), on OpenGL at the staged build's default window, `ui_retained
  1`, `+map game/alphalabs1` at launch, seven runs before the change and
  seven after (`com_loadingFrameTrace` 1 or 2). With `g_disasm 1` the
  disassembly of the compiled scripts is byte for byte the same as before.
  `doom_main.script` compiles in 345-570 ms instead of 537-701 ms with the
  start-up screen drawing (216 ms with `ui_retained 0`). Before, the stall
  sampler found start-up gaps of 46-77 ms with the script compiler or its
  includes on the stack (`idCompiler::GetImmediate`, `idProgram::GetDefList`,
  `idParser::Directive_include`); after, those gaps are 44-50 ms, the
  start-up pacer's own cadence (intervals p50 about 43 ms). `INITIALIZATION_PRESENTATION maxGapMsec`
  stays 130-290 ms in most runs either way, because it is set by the
  start-up screen's first vector tessellation and first present (127-409 ms,
  retained interface and driver), not by the game; in the runs where that
  falls before the window it was 57 ms before and 50-51 ms after. The
  start-up took 2,061 ms on average instead of 2,189 ms. The level load's
  gaps did not change (max 96-208 ms after, 83-128 ms before, the same
  spread): on `alphalabs1` no gap over 25 ms has script or animation code on
  the stack before or after, and the longest are the game's first hidden
  frames (`idPhysics_AF::Evaluate`) and the driver at the hand-off. The logs
  have the same 75 warning lines before and after and no error.
  Resurrection of Evil's module carries the same change and was built, not run.
- Stock specular follows Doom 3 on every path. `r_correctspecular` and
  `r_normalizebumpmap` default to 0 (they came from Prey at 1), and the OpenGL
  ARB path passes the specular constant unscaled, as id's `draw_arb2.cpp`
  does, because Doom 3's `interaction.vfp` doubles the specular map itself.
  This was measured against the shadow-map and Vulkan pictures above, not
  against retail Doom 3.
- The player's own shadow, in first person. With a light spawned behind the
  player, the body, head and held weapon cast their shadow on the surface in
  front: in single player on `mc_underground` (`g_showPlayerShadow` now
  defaults to 1; 0 removes the shadow) and in a `d3dm1` deathmatch listen
  server, each on OpenGL and Vulkan, with stencil shadows and with shadow
  maps. The shadow-map report confirms that the test light was shadow-mapped
  in each case, with the player's models among its casters.
- The dedicated server spawns `game/mp/d3dm1` (887 entities).
- The VS Code tasks and launches. The default build task compiles `builddir`
  and fast-stages `.install`. Run with their own arguments and an isolated
  `fs_savepath`, these launches load their map and exit cleanly on the given
  renderer: `mars_city1` load-and-quit (OpenGL), `comm1` (Vulkan) and the
  `d3dm1` deathmatch listen server (OpenGL). `tools/tests/vscode_fast_build.py`
  passes.
- The "Bake Light Grids (All MP)" task (`bakeLightGrids all-mp`) bakes Doom
  3's five `game/mp/` maps as deathmatch maps in one batch on OpenGL, writes a
  `.lightgridpack` for each and exits cleanly. A later `d3dm3` listen server
  loads its pack from the save path and draws with it. The bake still warns,
  for every map, that another copy of the pack comes first; none exists, and
  the warning is the bake's own read-back check failing (see "Open items").
- `+set fs_game d3xp` mounts the expansion directory, loads `game-d3xp_x64`
  and initialises the game. On the test machine, which has only the
  expansion's patch pack, startup then stops with a parse error in the
  expansion's `guis/mainmenu.gui`.
- With `+set ui_retained 1` the retained title, single-player pause and
  message box present in place of the stock ones, in the vector design of the
  [visual design specification](ui-visual-design.md): the title at 4:3, 16:9,
  21:9 and in a tall window; the difficulty list, from which MARINE loads
  `game/mars_city1`; the exit and quit-game dialogs; the pause over that game
  and its return; the hand-off to the stock options list and credits and
  back; the Load Game and Save Game pages, from which a game in
  `game/alphalabs1` was saved, saved over and deleted; and the options list
  with its CONTROLS, GAME OPTIONS and SYSTEM pages, on which a key was bound,
  two game settings changed and vertical sync was applied through the
  settings service, and the DEFAULTS dialog, whose YES put a changed game
  setting and an unbound key back to their defaults; the mods panel and the
  credits page; and the multiplayer
  list and Game Browser, from which a client joined a dedicated server of the
  same build on the same machine as far as the map load and the player's
  spawn; and the Create Server page, from which a LAN deathmatch server was
  started on `game/mp/d3dm3` with the name, limits and warmup set on the
  page; and the Multiplayer Settings panel, on which the data rate, Always
  Run, the player's name and skin were changed and read back from the
  written config; and the death screen, from which a killed player
  restarted the map, opened the Load Game page and returned to the title;
  and the level loading screen over the stock pictures of `alphalabs1`,
  `admin` and `d3dm1`, at 4:3, 16:9 and 21:9; and the in-game multiplayer
  menu on a local server, from which a player set ready, spectated,
  changed team, said a line of team chat, changed name and skin, bound a
  key, called a frag limit vote that passed, and disconnected, and whose
  System tab opened the SYSTEM page over the game, where vertical sync was
  applied; and the hell level's and the first level's loading screens on
  `hell1` and `mars_city1`; and, in stills taken mid-motion, the menus'
  choreography: the nav band standing aside and dimming, sub-lists and
  pages closing, the top bar's slide, the hint's wipe, the bindings' row
  flash and the grid lighting under the pointer; and the same screens in a
  720x1280 window, where the retained furniture goes to the top and bottom
  edges; and the start-up screen, shown through `testGUI` at seven shapes
  from 32:9 to 9:16 and traced through a real start-up, and the same
  screen standing in for the fallback loading screen on
  `testmaps/test_box`, with the planet's fires drawn on the turning globe.
  [Retained Doom 3 menus](ui/retained-menus.md) lists each check and
  what was not seen. From the merge of 18 November until 20 November the
  settings service refused the retained SYSTEM page (upstream's catalog
  gained `r_shadowMapCharacterSelfShadow`) and the stock page stood in;
  the generator now checks the page against the engine's schema.
- Level pictures (2026-11-20, `ui_retained 1`). `FindMapScreenshot` looked
  for Quake 4's `gfx/guis/loadscreens/<map>.tga`, found nothing in Doom 3's
  packs and fell back to the generic picture, so the stock and retained
  Create Server and the Game Browser showed the start-up planet for every
  map. Under `OPEND3` it looks for Doom 3's `guis/assets/splash/<map>.tga`,
  as Doom 3 does; Create Server on `game/mp/d3dm1` now shows Tomiko
  Reactor's own picture. The Game Browser, a saved game without its own
  shot and the stock pages were not looked at.
- openD3 levelshots (2026-11-20, OpenGL, `ui_retained 0`). Twenty-five level
  pictures are recaptured at the recovered retail camera with shadow maps and
  their wide and tall tiles, in the client-only `baseod3/pak2.pk4`
  ([levelshot capture](levelshot-capture.md)). With it staged,
  `FindMapScreenshot` returns `guis/assets/levelshots/<map>`, and the level
  loading screens of `game/alphalabs2`, `game/delta3` and `game/cpu`, held at
  press-to-continue, show the new picture at 1024x768 and the picture composed
  from the tiles at 1680x720 and 720x1280, with the bars, title and
  description in place. The other loading screens, the menus' level pictures
  and Vulkan were not looked at. Glass in off-axis views (levelshot tiles)
  refracts correctly after the heat-haze vertex-program rewrite in
  `draw_arb2.cpp`; ordinary views were not compared before and after.
- Saving and loading in the same build (2026-11-14, OpenGL, console
  `saveGame` and `loadGame`, an isolated `fs_savepath`). On `game/alphalabs1`
  (`devmap`), with `god`, `noclip` and `give all` set, the player moved with
  `setviewpos` and a `monster_zombie_fat` spawned: after moving away and
  loading, `getviewpos` reports the saved position and yaw, and captures taken
  before the save and five seconds after the load show the same view, the
  zombie still advancing and the same armour, health and ammunition on the
  HUD. The game ran ten more seconds and quit cleanly, and the load logs only
  the warnings an ordinary load of the map does. The same save loads from the
  main menu of a fresh process. A save made 500 frames into the opening
  cinematic of `game/mars_city1` loads back into the cinematic. Before these
  fixes no save loaded; see "Savegames are not stamped" under "Open items".
- Saves that cannot be loaded. A save with one byte changed, one cut to half
  its length and a missing one are each refused before the running map is
  touched, and play continues. Two saves damaged inside the game's payload and
  given a matching integrity trailer by hand, one naming an unknown class and
  one with 64 bytes overwritten halfway, each end with "could not restore
  saved state" and the LOAD FAILED message at the main menu, and a good save
  then loads in the same process.
- Performance presets and the startup system check, 2026-11-21, OpenGL,
  windowed 1280x720 and 720x1280, a profile saved against an older preset
  system (`com_performancePresetCheck` stale, `com_performancePreset low`).
  A plain start opens the check before the main menu: the stock
  `guis/presetcheck.gui` with `ui_retained 0`, `guis/menu/presetcheck.rui`
  over the stock screen's stars and Mars with `ui_retained 1`. Both show the
  detected GPU, memory, threads and display, the ladder with Low outlined and
  Enhanced lit, Enhanced's scale and frame cap, and OPTIONS > SYSTEM in the
  footer. KEEP CURRENT records the version and keeps Low; APPLY RECOMMENDED
  applies Enhanced (15 settings), restarts the renderer and sound and opens
  the main menu; Back records nothing, and the next start asks again. The
  stock System page's High Quality button applies Balanced and lights High,
  and its hardware scan applies the recommendation. The retained SYSTEM page
  steps Video Quality Low, Medium, High (Low, Performance, Balanced), and
  APPLY CHANGES with KEEP saves Balanced.
- Volume follows Doom 3 (2026-11-22). A fresh profile starts at full volume
  (`s_volume_dB 0`, `s_volume 1`, as retail's `DoomConfig.cfg`), with
  `s_quadraticFalloff 1` and the music scale at unity, since Doom 3 has no
  music volume. A profile still on the old -6 dB master and music pairs moves
  to 0 dB once (audio migration step 3). Quake 4's speaker attenuation, which
  cut every spatialized sound but the weapon and item channels by 3.7 dB, is
  gone with `s_speakerFraction` and `s_radioChatterFraction`. Shader volumes
  are no longer clamped at +10 dB (56 retail shaders ask for more), and
  `leadinVolume` is read in dB, as Doom 3 reads it. On `game/mars_city1`
  with `s_soundDistances` during the intro, all 106 live channels carry
  exactly the shader volume times the quadratic falloff. The game converts
  its dB values to the engine's linear scale in three places: an entity's
  `s_volume` (where 0 still means the shader's volume), `SetSoundVolume`
  (bouncing moveables, ragdolls and projectiles, which Doom 3 played at
  0 to +1 dB in place of the shader's volume) and the heartbeat. Those three
  were checked by reading the code, not in play. Doom 3's software mixer
  panning (`s_globalFraction`, `s_dotbias2`, `s_minVolume2`) is not
  replicated, since OpenAL pans, and neither is RoE's slow-motion distance
  scaling (`s_slowAttenuate`).
- Sixteen-player multiplayer, 2026-11-23, Vulkan, windowed. `si_maxPlayers`
  takes 1 to 16 in both games (`MP_MAX_PLAYERS`, 8 by default; Doom 3 took
  1 to 4 and Resurrection of Evil 1 to 8). A dedicated server on
  `game/mp/d3dm1` (deathmatch, 16 seats, LAN, loopback) took 15 clients run
  on the same machine: they joined, spawned and suicided on cue, and three
  timed out while the others were starting (two rejoined), which was not
  looked into further. One client's HUD rank list then showed the leader
  (1 frag), two players level on 0 and its own box framed, numbered
  1, 2, 2, 2, as the server log's frags say. Four telefrags in that match
  came from joining players sent to spawn points idle players stood on;
  `SpawnSpotChoices` (both games) now keeps the choice to free points, which
  was checked by reading the code, not rerun in play. The client that
  spectated saw "Spectating" without the scoreboard, so the scoreboard has
  not been seen with game data: openD3's `guis/scoreboard.gui`
  (`tools/ui/build_doom3_scoreboard.py`) was checked with `testGUI` and
  made-up state at 16:9 with 4, 8, 12 and 16 seats, Team DM at 16, and its
  opening, against the retail board at 4 seats, which it matches but for the
  player count in the title row; the HUD's rank list likewise, crowded
  (1, 2, 2, 9 with the last box framed) and with four players (Doom 3's,
  unnumbered). Create Server's Max Players: the retained page took 12, saved
  to the config, and refused 30; the stock page showed 12 and the log
  confirmed `mainmenu.layout`'s patch reached its field. Not shown: the
  listen-server warning (`#str_100625`, now in all twelve string tables),
  Team DM, Tourney and Last Man with many players, and anything in
  Resurrection of Evil.

That is all that has been run. In particular, nothing here is evidence for:
playing past the first cinematic, combat, AI, the PDA beyond its first page,
video playback, level transitions, fighting between players in multiplayer,
Linux, macOS, Android, ARM64 or VR. The TrueType text was not compared
screen by screen with the bitmap path, and was not checked on Vulkan, in the
PDA, on in-world screens or in a language other than English. The wide and
tall layouts were not checked in a multiplayer match, with the HUD's
objective, inventory and pickup notices showing, on the message boxes, intro
and credits as the game raises them, or in Resurrection of Evil. Saves were
loaded only in the states listed above: not from the menus, not an autosave or
quicksave, not during combat or with projectiles in flight, not on Vulkan and
not in Resurrection of Evil, whose module carries the same fixes but has not
run a map.

## Open items

Listed roughly by how much they block a player.

1. **Resurrection of Evil is unverified.** The expansion mounts and its
   module initialises, but no map has been loaded: the machine this was done
   on has no complete RoE data, and with the patch pack alone the expansion's
   main menu fails to parse. That needs repeating with a full install before
   deciding whether it is a GUI parser gap. The renderer carries
   `renderEntity_t::xrayIndex` and the sound world `SetSlowmo` only so the
   game compiles; neither has an effect. The expansion seats 16 players like
   the base game, but its own `guis/scoreboard.gui` and
   `guis/ctfscoreboard.gui`, which its packs put ahead of `baseod3`, were
   made for its 8 and may not show them all; no RoE board has been looked at.
2. **Savegames are not stamped.** The engine's hardened savegame framework
   expects the game to write a versioned, checksummed payload. Doom 3's game
   library writes its original unstamped payload, which `Session.cpp` accepts
   under `OPEND3` for the build that wrote it. Writing the stamped payload is
   game-side work; it must be written for openD3, not copied from openQ4's or
   openPREY's game trees, which are under their SDK licences.

   A save now loads in the build that wrote it (see "Verified"). Four things
   stood in the way, fixed in `src/game` and `src/d3xp` alike where they are
   the game's:
   - `idScriptObject::Restore` read the object's size, an `int`, through a
     cast into a `size_t`. On a 64-bit build half of it stayed unset, so the
     first script object, the player's, was refused. `idEvent`'s trace
     argument stored a material pointer the same way; it now stores whether
     there was one. The same pass made queued events keep their string
     arguments and a trace's entity number, which were never written, and
     made the clip system's own models keep their trace models across a
     restore, which had left a warning at every shutdown after a load.
   - The session (`Session.cpp`, `OPEND3`) reported the unstamped payload as
     version 0, so the engine read the GUI state inside it as an old payload's
     raw records while the save had written the current encoding. The payload
     is this build's own and is now read as the current version.
   - A failed restore crashed. `idRestoreGame::Error` deleted every object of
     the save and `idGameLocal::MapClear` then deleted `frameCommandThread`
     again; deleting half-restored objects could also crash earlier, because a
     restored object's destructor reaches into objects that hold nothing yet.
     `idRestoreGame::Abandon` now ends a failed restore whatever raised the
     error: objects never restored are deleted, the others are left allocated
     and unreferenced, and the game forgets every pointer it read. A failed
     restore therefore leaks the objects it had already restored.
   - The unstamped payload had no integrity check. The session already appends
     its integrity trailer to every save; under `OPEND3` the unstamped payload
     is now held to it, so a damaged or truncated file is refused before the
     map is torn down.

   Still open: the stamped payload itself, and with it saves that survive a
   new build. The game's readers trust what they read, so a file that passes
   the integrity check and is wrong inside (a deliberately built one, or a
   save and restore that disagree) can still restore into a wrong state
   without an error. Only the 64-bit mistakes that the tested states reached,
   or that a search for casts in the save code found, are fixed; other entity
   classes may hold more.
3. **Engine features with no stock Doom 3 content.** Kept deliberately,
   because custom content and mods could use them: BSE effects, MD5R models,
   light grids, the retained RmlUi interface, the Arena ladder (it loads only
   when a package ships its campaign file), and the extensions that came with
   the openPREY layer (glow stages, extra material keywords and deforms, GUI
   window types, subtitles, loading music, the libogg/libvorbis decode
   fallback). Many of their comments still describe Quake 4 or Prey content.
   Handling tied to one retail product was removed: the Awakening expansion's
   campaign, content checks and substitutions, the Quake 4 savegame names and
   the Prey data blocks formerly behind `HUMANHEAD`, and the stretching of
   Quake 4's message dimmer and Tourney warm-up bar, which layout patches
   replace. The chapter list and the campaign commands now name Doom 3's maps. Still to go through: the Quake 4
   HUD routes in the retained HUD, the Quake 4 language-pack listing,
   Quake 4 image and font fallbacks, and the Prey retail image aliases and
   known-missing list in `src/renderer/Image_load.cpp`
   (`PREY_RETAIL_IMAGE_ALIASES`), which came with the openPREY layer.
4. **Startup warnings still to clear** (Procedure 1 in `AGENTS.md`): the
   engine's chat window and menu background precache four Quake 4 menu images;
   the retained HUD looks for a Quake 4 HUD document; the engine asks for a
   `guisounds` shader and string `#str_107240`, which Doom 3 does not have;
   the stock menus reference the removed `s_driver` cvar; the engine and the
   game both declare `r_showSkel`. A `mars_city1` load currently logs about 25 distinct warnings,
   some of them the retail content's own.
5. **The retained interface has fifteen Doom 3 documents.** The start-up
   screen, the title, the
   single-player pause, the message box, the death screen's choices, the
   level loading screens' furniture, the in-game multiplayer menu, and the
   Load Game, Save Game,
   Controls, Game Options, System, Credits, Game Browser and Create Server
   pages, with the Mods and Multiplayer Settings panels in the title, are
   built to the
   [visual design specification](ui-visual-design.md) and present with
   `ui_retained 1` ([retained Doom 3 menus](ui/retained-menus.md)). Every
   other page and the HUD have none, so launches
   still
   pin `ui_retained 0` (the cvar itself defaults to 1) and the stock Doom 3 GUIs remain their interface. With
   `ui_retained 1` the pages without a document are the stock ones, reached
   from the retained home, and a map load warns that the retained HUD
   documents are missing before it uses the stock HUD.
6. **Tooling under `tools/` is inherited and unadapted.** The test corpus,
   validation profiles, packaging, installer and release scripts were written
   for openQ4. They were renamed mechanically and have not been run for
   openD3; many still test Quake 4 maps and content. The optional native test
   suite (`-Dbuild_native_tests=true`) references Quake 4 interface files that
   are no longer in the tree and will not configure. The build helpers Meson
   invokes are adapted and exercised, as are the VS Code tasks, launches and
   `tools/tests/vscode_fast_build.py`. Of the release tooling, only the
   documentation side has been run: `generate_release_docs.py` builds the
   offline documentation site and `tools/tests/docs_link_integrity.py` passes
   over it, the source documents and the two HTML readmes. The packager,
   installer and release verifiers still name Quake 4 and Prey layers and have
   not been run.
7. **No CI.** openQ4's GitHub workflows were removed rather than left to fail;
   they need rebuilding for openD3.
8. **Player guides are a first pass.** openQ4's documentation was removed
   because it describes Quake 4. `docs/user/` now holds five guides laid out
   like openQ4's (getting started, release status, client settings, campaigns
   and server setup). They state only what "Verified" covers and must follow
   it when it changes. openQ4's display, input, gameplay and rendering guides
   have no openD3 counterpart, because none of those features has been checked
   with Doom 3. The README has no screenshots yet. The rest of the
   documentation follows openQ4's layout: `BUILDING.md` and `TECHNICAL.md`
   take its sections, `docs/dev/` has the [source layout](source-layout.md)
   and [unreleased release notes](releases/unreleased.md), and
   `assets/release/README.html` (the package home page) and
   `assets/docs/README.html` (the project overview) are drawn in Doom 3's
   front-end menu style with openD3's TrueType faces, as is the generated
   documentation site.
9. **The light-grid bake warns falsely about its packs.**
   `LightGrid_BakeLoadsNextTime` reads the new pack back through the file
   system to confirm that it will load. For a pack written into a directory
   the bake created, that read fails, and the bake reports that another copy
   comes first although the pack loads on the next start.
10. **Shadow-map follow-ups.**
    - The performance presets are openQ4's but for one `OPEND3` value
      (2026-11-22): **Enhanced** (the one startup picked on the test machine)
      shadow-maps point lights too, where upstream leaves them on stencil
      shadows. Every tier that turns shadow maps on now maps every light.
      Upstream budgeted Enhanced for 144 Hz on Quake 4 content with point
      lights on stencil, and their cube maps were its largest cost; Enhanced
      has not been re-timed on Doom 3 since.
    - Subviews (mirrors, security monitors) render shadow maps like the main
      view under `OPEND3` (`r_shadowMapSubviewPolicy 0`, moved from the old
      default 1 once per profile). Upstream's policy 1 may draw stencil volumes
      in a subview on a cache miss; on `delta2a`'s bathroom mirror, with the
      flashlight on, it did not (the subview shares the main view's elided
      volumes, which forces a map), so the change is a safeguard rather than
      a fix for a seen fallback.
    - Stencil fallbacks that remain: a light whose map fails to render or
      sample (render, mask or resource failure, a full atlas, a Vulkan cube
      pool that video memory cannot grow) and receivers the map pass cannot
      shade keep stencil shadows rather than none, and
      `r_shadowMapPointLights 0`, `r_shadowMapSubviewPolicy 1`/`2` and
      `r_shadowMapMaxUpdatesPerView` above 0 still choose stencil when set by
      hand. Such a light, whose volumes were left out because a map was
      expected, draws unshadowed for the frame it fails.
    - Vulkan's scratch cube pool can now grow past `r_shadowMapPointCacheMegs`
      while the device-local heap stays under 80% of its budget, up to 512
      cubes (512 faces: about 6 MiB each). Unused cubes go back after five
      seconds. Tour views that saw most of a map, some of them from outside
      it, held 220 to 310 cubes.
      Not measured: the frame time of such views, and behaviour on a card
      with less video memory than the test machine's 8 GB.
    - Upstream's startup system check, which offers the detected preset when
      the preset table changes, runs with Doom 3 screens of openD3's own
      (see "Verified"). Not checked: Vulkan, a controller, a language
      other than English, and pointer or keyboard input on either screen
      (the answers were given through `performancePresetCheck` and the
      retained Back event).
    - Stale profiles keep old values: a config written before these defaults
      changed still holds `g_showPlayerShadow 0` and `r_correctspecular 1`,
      `r_normalizebumpmap 1`. There is no config migration.
    - On OpenGL, setting `r_correctspecular 1` or `r_normalizebumpmap 1`
      changes only the GLSL and Vulkan paths: the ARB program cannot follow
      them, so mapped and stencil pictures differ again.
    - OpenGL draws `hell1`'s first view brighter than Vulkan (about 420,000
      pixels), the same with shadow maps, stencil or no shadows. Not
      investigated.
    - Not covered: Resurrection of Evil, moving lights compared against
      stencil (they have only been seen rendering, with time running),
      cascaded shadow maps (`r_shadowMapCSM`).
11. **The master server address is Quake 4's.** `IDNET_HOST`
    (`src/framework/licensee.h`) is `q4master.idsoftware.com`, as upstream
    has it. That server answers: an internet server started from the menu
    on 2026-11-14 sent it a heartbeat and answered its info request. Which
    master openD3 should announce to and browse is undecided.

## Naming

The project name is openD3 everywhere, in what users see and in the source:
binaries, window titles, config and log names, environment variables and
macros (`OPEND3_*`), functions (`openD3_*`), generated headers, Meson
variables, content file names (`*_opend3`) and the dependency patches. The
runtime directory is `baseod3`. The only places upstream's name appears are
prose about the upstream project, its repository URLs and the
`openq4-upstream` remote.

`tools/build/rebrand_upstream.py` performs the rename. It
maps `openQ4`/`OpenQ4` to `openD3`, `OPENQ4` to `OPEND3`, `openq4` to `opend3`
and `baseoq4` to `baseod3`, in file contents and in paths, and reports
collisions with `--check`. It also rewrites prose that is about the upstream
project ("built on the openQ4 engine") outside its list of skipped files: in
`assets/`, `docs/` and `tools/assets/` it did so on the `7c74cd712` sync.
After running it, keep its changes only in the files the merge brought in and
restore the rest.

## Syncing with upstream

Because openD3 renames upstream's identifiers, a plain merge conflicts on
every line upstream touched that carries its name. Merge in upstream's naming
instead:

```
git fetch openq4-upstream
git switch -c sync/upstream
git merge openq4-upstream/main        # resolve as described below
python tools/build/rebrand_upstream.py --check
python tools/build/rebrand_upstream.py
```

Expect conflicts wherever both sides changed a renamed line; taking upstream's
text for such a line and letting the script rename it afterwards is usually
right. Delete the extracted dependency folders under `subprojects/` and
reconfigure if the dependency patches changed.

Keep openD3's side for `src/game`, `src/d3xp`, `content/baseod3`, the openD3
identity and the `OPEND3` sites. Never take `src/mpgame`, upstream's `src/game`
or `content/baseoq4`. Where new upstream engine code calls a Quake 4-only
`idGame` method, adapt it to Doom 3's API or gate it as D9. Regenerate the
Vulkan SPIR-V headers if both sides touched the shader sources, then rebuild
and repeat the checks under "Verified".

Upstream also lands Quake 4 game features in engine files: the session, the
file system, the user-command buttons, the retained adapter and the engine
string tables. On the `f3b2f9583` sync these were The Awakening as a mod base
(`7926e2a42`), the multiplayer buy card (`eb6b5d399`), the Classic ruleset and
its grappling-hook button (`2a36515de`, `3ddce1949`) and Instagib
(`26c58d1cf`). Where they merge cleanly they arrive unnoticed, so after
resolving, reverse those commits' engine hunks (rebranded) and grep the engine
for their symbols (`FS_AwakeningActive`, `q4xbase`, `RETAINED_MP_BUY`,
`BUTTON_HOOK`, `Instagib`). A three-way merge of each conflicted file against
the rebranded base and upstream side (`git merge-file` on the converted
blobs) leaves only the real conflicts.

On the `65305957d` sync the Quake 4 features were The Awakening's pause menu
and settings-page family (`6b6c48a1f`, `ac1ea4b50`) and its levelshot sets
(`5ead3e6dd`), the multiplayer modifier layer and presets (`8bd169759`,
`1308a18fe`), the map database's settings hook (`0210f852a`, which calls a
Quake 4-only `idGame::ValidateServerSettings`) and the smart weapon switch's
`ui_autoSwitch` migration (`5afbc3e88`; Doom 3's `ui_autoSwitch` is a switch).
Their engine hunks were reversed, rebranded, with `git apply -R --3way`. The
sync also dropped upstream's new tests for the Quake 4 game library (the
enhanced-physics, live-event, HUD-catalog and clip fast-path checks). The
in-game updater arrived with upstream's release-signing key, which signs
openQ4's releases: openD3 empties it (`src/updater/UpdateSigningKey.h`), so an
update check can only open the release page.

On the `966d8ae6f` sync the Quake 4 feature was switching between Quake 4
and The Awakening in place (`ca16875ce`): its engine side remounts the game
directories under the running engine and calls `FS_AwakeningActive` and the
Quake 4 game API. Every file it touched was rebuilt as openD3's side plus
upstream's other changes: a three-way merge of upstream's file against the
commit's own before and after drops the commit, and a second three-way merge
of that, rebranded, against openD3's file brings in the rest. The Russian
gameplay tables it added for Quake 4 (`d724454c6`) stay out, and openD3 keeps
its Russian engine strings, which upstream moved into those tables. Upstream's
surface-GUI winding fix (`966d8ae6f`) matches openD3's `62c9773c6`; the
merge takes upstream's wording. Both sides had touched the Vulkan shader
sources, so the SPIR-V headers were regenerated with the commands
`vk_shader_header_pin.py` prints.

On the `b1f6ed617` sync the Quake 4 features were the restructured
multiplayer menus (`3f3665233`: an in-match Audio route, more vote fields,
the multiplayer HUD's settings) and the weapon order dialog (`a1bd952bc`).
Their only engine hunks were in the session and the retained adapter's verb
and setting tables, so `src/framework/Session.cpp` and `Session_menu.cpp`
keep openD3's side and the adapter drops those verbs and CVars. Git's rename
detection carried the settings-tree and multiplayer strings from
`content/baseoq4`'s language tables into openD3's; `content/baseod3` keeps
openD3's side. No shader source changed.

On the `d3056567a` sync no Quake 4 feature reached the engine, but rename
detection carried upstream's Quake 4 game changes (the medic's combat stance,
an indexed lookup of script immediates, `common->LoadingCheckpoint` calls in
the script compiler and the model parser) into `src/game` and `src/d3xp`;
both trees keep openD3's side, and the new medic test stays out. Those are
SDK-licensed code. openD3's game library got its own GPL equivalent
afterwards, written from its own sources: `common->LoadingCheckpoint` after
each definition the script compiler finishes, after each script file is read
and before it is compiled, and after each animation `idAnimManager::GetAnim`
loads, and script immediates found through a hash of type and value instead
of a walk over all of them (`idCompiler::FindImmediate`), in both trees; the
"Verified" section has the measurements. The Ambient Occlusion choice adds `r_ssaoMethod` to the
settings service's catalog, so `tools/ui/doom3_menu_system.py` declares it
and `system.rui` was regenerated; openD3's SYSTEM page shows no ambient
occlusion row, so upstream's two new strings (`#str_232633`, `#str_232634`)
are not taken. `content/baseod3/pak0/glprogs/ssao.fs` takes upstream's new
OpenGL kernels. The stock Display page's `gui_set_sys_ao` sync in
`Session_menu.cpp` arrived with it and does nothing for Doom 3's menus.
openD3 does not keep upstream's new developer documents (loading
presentation, parallax occlusion, retained event costs) or the multiplayer
guide. The only real conflicts after the converted three-way merge were
`Image_load.cpp` (openD3's Prey alias table beside upstream's new include)
and `tr_fontTTF.cpp`, where upstream's parallel glyph rasterizer now passes
openD3's `verticalScale`. Both sides had touched the Vulkan shader sources;
the SPIR-V headers were regenerated after the rebrand, which renames the
parallax functions inside `pbr_direct.glsl`.

`rebrand_upstream.py` has no `--help`: any argument other than `--check`
runs it for real. Besides the files below, it renames openD3's own
`Session_ShowOpenD3Levelshot` in `src/framework/Session.cpp`; restore it.

The script also rewrites openD3's own prose in `docs/` and `assets/` and a
few tools that the merge did not touch, and the legacy `openq4-ui` format
names in `src/ui/retained`: restore those, and comments about upstream's own
packages.

When testing from the command line, remember that every `+set` is applied at
startup wherever it stands on the line. A setting meant to change later in the
command sequence (`g_stopTime 1` after a `waitMsec`) is written `+g_stopTime 1`.
