# Unreleased openD3 development changes

These changes belong to the development tree. openD3 has **no release yet**;
the first will be 0.0.1. This file collects material for that release's notes,
with no date promised, in the layout of openQ4's release notes. Each claim here
is limited to what the [rebase record](../doom3-rebase.md#verified) covers. See
[release status](../../user/release-status.md) for the player view.

## Highlights

- **Doom 3 on the current openQ4 engine.** openD3 moved off its older engine
  onto openQ4, keeping Doom 3's GPL game library in this repository. The
  [rebase record](../doom3-rebase.md) describes how.
- **Finds and checks your game files.** Startup finds a Steam install of Doom 3
  without `fs_basepath`, validates `pak000`–`pak004` by checksum and leaves the
  retail game-binary packs out of the search path.
- **The first campaign map runs.** `game/mars_city1` loads, plays its opening
  cinematic with working in-world screens and remote camera views, writes its
  autosave and exits cleanly.
- **OpenGL and Vulkan.** The same map renders on the default OpenGL renderer
  and on the native Vulkan renderer (`+set r_renderApi vulkan`).
- **Doom 3's own menus and consoles.** The stock main menu starts and plays the
  intro video, and both consoles carry Doom 3's colours.
- **Wide and tall screens.** The stock menus, HUDs and loading screens reach
  the screen edges at any aspect: frames and bars stretch, docked pieces move
  to the edges, panels stay centred. The PDA keeps its 4:3 screen over a
  softened view of the world. No retail GUI script is shipped: small layout
  patches name the windows ([layout](../widescreen-layout.md)).
- **Level loading pictures for any screen shape.** Seventeen of Doom 3's level
  pictures are recaptured from the retail camera on the shipped maps, at
  1024 with shadow maps, with side, top and bottom tiles, so a wide or tall
  loading screen shows more of the level instead of a crop. They ship in the
  client-only `pak2.pk4` ([levelshot capture](../levelshot-capture.md)).
- **Dedicated server.** `openD3-ded_x64` spawns `game/mp/d3dm1`.
- **Your own shadow, and shadow maps that match.** In first person your body,
  head and weapon cast a shadow, in single player (`g_showPlayerShadow`, now on
  by default) and in multiplayer. Shadow maps (`r_useShadowMap 1`) draw the
  same lighting as stencil shadows on OpenGL and Vulkan.
- **Resurrection of Evil module.** `src/d3xp` builds `game-d3xp_<arch>`, which
  `+set fs_game d3xp` loads and initialises. No expansion map has been run.

## Upgrade Notes

- There is no earlier openD3 release to upgrade from. Builds from the
  pre-rebase tree do not share saves or configs with this one.
- Saves load only in the build that wrote them. A damaged save is refused
  with a message instead of being loaded.
- Launch with `ui_retained 0`. openQ4's retained interface has no Doom 3 pages.
- Only Windows x64 has been built and run.
- A settings file written by an earlier build keeps `g_showPlayerShadow 0`,
  `r_correctspecular 1` and `r_normalizebumpmap 1`. Set the new defaults
  (1, 0, 0) by hand to get the player shadow and Doom 3's specular.

## Change Log

- Remove the Quake 4 game library and content, and preserve the pre-rebase
  openD3 tree in history.
- Transplant openPREY's Doom 3-lineage engine layer and convert it to Doom 3:
  map, AAS and collision formats, particle and FX declarations, the game API
  bridge.
- Build the Doom 3 game module from `src/game` and run Doom 3 on the rebased
  engine.
- Build Resurrection of Evil as a second game module from `src/d3xp`.
- Rename openQ4 identifiers to openD3 throughout and remove handling that
  existed only for Quake 4 or Prey content.
- Give the in-game and system consoles Doom 3's colours.
- Document openD3: README, building and technical references, player guides,
  the rebase record and game source provenance, laid out like openQ4's.
- Add the openD3 banner and the packaged HTML readmes.
- Add GUI layout patches (`guis/layouts/*.layout`), the `screenstretchx`/`y`,
  `canvasclip` and `softfocus` window properties, and wide and tall layouts for
  the main menu, HUDs, PDA, loading screens and full-screen GUIs. Remove the
  hard-coded Quake 4 message dimmer and Tourney bar stretching.
- Continue the main menu's grid across wide and tall screens
  (`screenrepeatx`/`y`), its brighter fifth lines in step, let the menu cursor
  reach the whole screen whatever GUI drew last, draw it at Doom 3's 32 units,
  and leave it out while the window lacks focus, when the system pointer
  shows instead. Buttons inside a stretched menu container now take the
  pointer where they are drawn; they had answered a whole expansion to the
  left.
- The VS Code compile task reconfigures `builddir` when source files are
  added or removed.
- Add the first retained Doom 3 menus, behind `ui_retained 1`: the title screen
  with its difficulty list and exit dialog, the single-player pause, the
  engine message box, the death screen's choices, the level loading screens'
  furniture, the in-game multiplayer menu but for its System page, the options
  list and the Load Game, Save Game,
  Controls, Game Options, System, Mods, Credits, Game Browser, Create Server
  and Multiplayer Settings pages, drawn
  as vector
  furniture over the stock menu's scene and generated by
  `tools/ui/build_doom3_menus.py`. Pages without a document
  are still the stock ones, reached from the retained home.
- Start a server from the Create Server page as the page's Server Type and
  Dedicated rows say. The session read two Quake 4 CVars that openD3 does not
  have, so a menu-created server was always an internet listen server; it now
  reads the menu's own `server_type` and `dedicated` state, as Doom 3 did.
- Show Doom 3's blank level shot for a save without a picture on the stock
  Load Game page, which named a Quake 4 image.
- Merge openQ4 through `7c74cd712`, with its shadow-mapping fixes.
- Merge openQ4 through `f3b2f9583`, with its later shadow-mapping fixes: a
  light with nothing to cast no longer cycles through the stencil fallback,
  moving lights skip stencil volumes they do not draw, Vulkan keeps one
  resident map for both ownerships of a light, and the shared interaction
  domain draws every shadow-map form. Quake 4's multiplayer buy card, Classic
  ruleset, Instagib and The Awakening campaign support stay out of the engine.
- Merge openQ4 through `65305957d`: PNG textures and screenshots, BC7
  texture-pack inputs, block-format render demos with keyframes, network
  protocol 2.42, the in-game updater (with no release key, so it can only
  point at the release page), PCSS-lite soft shadows on the modern OpenGL
  path, characters shadowing themselves under shadow maps, and faster
  light-interaction and collision bookkeeping. The Awakening's menus and
  levelshots, the multiplayer modifiers and presets, the map database hook
  and the smart weapon switch stay out of the engine.
- Draw in-world GUIs again after that sync. Upstream's handling of mirrored
  models turned the front face for every surface placed by a reflection, and
  the matrix that lays a GUI on its surface through the texture axes is one,
  so OpenGL culled every in-world screen (the Vulkan passes use the same
  test). A surface GUI now turns
  only when the surface carrying it is itself mirrored.
- Add `baseod3/pak2.pk4`, the loadscreen pack: recaptures of seventeen level
  pictures with their wide and tall tiles, found first by
  `FindMapScreenshot` and shown by each level's own loading screen, and the
  tools that recover the retail cameras and capture them
  (`tools/assets/levelshots/`).
- Refract correctly through glass in off-axis views: Doom 3's heat-haze
  vertex programs assumed a symmetric projection and smeared levelshot tiles
  (and VR eyes); the OpenGL backend corrects the line as it loads them.
- Merge openQ4 through `966d8ae6f`: cascaded outdoor shadow maps on Quality
  and Ultra, steadier shadows from distant lights, layered OpenGL point-shadow
  cubes, BC6H textures and more texture-pack formats, each pak mounted once
  when two search roots hold it, and cheaper particles, decals and reverb. Quake 4's in-place switch to The Awakening and its
  Russian gameplay tables stay out.
- Skip upstream's startup system check, which offers the detected performance
  preset, until openD3 ships a screen for it.
- Default `g_showPlayerShadow` to 1 in both game modules.
- Shade stock specular as Doom 3 does: `r_correctspecular` and
  `r_normalizebumpmap` default to 0, and the OpenGL ARB path no longer doubles
  the specular constant that Doom 3's `interaction.vfp` doubles itself.
- Make saved games load: fix the 64-bit read of a script object's size and
  of a queued event's trace, read the GUI state inside a save in the encoding
  it was written in, check every save against its integrity trailer before
  loading it, and return to the menu instead of crashing when a restore
  fails.
