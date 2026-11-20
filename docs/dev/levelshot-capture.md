# Levelshot capture

openD3 ships its own pictures for Doom 3's level loading screens. Each one is the
retail picture (`guis/assets/splash/<map>`) recaptured from the same camera on the
shipped maps, with neighbour tiles that let the loading screen fill a wide or tall
window instead of cropping. This page covers what the sets are, how the engine uses
them, how the retail cameras were recovered and how to capture a set again.

## The sets

A set is five 1024x1024 JPEG files in `content/baseod3/pak2/guis/assets/levelshots/`,
packed into the client-only loadscreen pack `baseod3/pak2.pk4`:

- `<map>.jpg`, the 4:3 view at the retail camera, stretched to a square as Doom 3's
  pictures are;
- `<map>_left`, `_right`, `_top` and `_bottom`, the 4:3 views beside it on the same
  image plane (off-axis frusta, so the five join without a seam).

Only the levels whose retail picture is a view of the level are candidates. The hell
level's skull, the start-up and generic pictures (`launch`, `pdtempa`) and the first
level, whose loading screen has no picture, keep their stock screens.
`tools/assets/levelshots/doom3_levelshots.json` records every set's camera, field of
view, capture time and match quality.

Twenty-five of the thirty level pictures have a set: `admin`, `alphalabs1` to
`alphalabs3`, `comm1`, `commoutside`, `cpu`, `cpuboss`, `d3dm1` to `d3dm5`, `delta1`,
`delta2a`, `delta2b`, `delta3`, `delta4`, `delta5`, `enpro`, `hellhole`, `mars_city2`,
`recycling1`, `recycling2` and `site3`. Their cameras were solved to a median
reprojection error of 0.3 to 1.8 pixels at 640x480 and checked by eye against the
retail picture. The other five keep the retail picture, cropped to the window as
before; `unshipped` in the cameras file holds the best pose found for each:

- `alphalabs4`: the right room, but the solve does not settle on the shot;
- `mc_underground`: the retail walkway lighting is not in the shipped level, and the
  solve settles elsewhere;
- `monorail`: the walkway and beam nearest the camera differ from the shipped level;
- `caverns1`: the right area, but the cave haze leaves too few features to settle;
- `caverns2`: not found; the search lands on another wall with the same inscription
  texture.

## How the engine uses them

`FindMapScreenshot` returns `guis/assets/levelshots/<map>` when the set is installed
(under `OPEND3`, `src/framework/FileSystem.cpp`), so the menus' level pictures, the
pause and save screens and the loading screen all use it. On a level load the session
composes the picture to the window's shape from the centre and its side tiles (wide)
or top and bottom tiles (tall), in memory (`Session_PrepareExpandedLoadingBackground`).
Doom 3's own level screen, `guis/map/<map>.gui`, draws its picture in the window
`BackgroundImage` through the material `gui/loading/<map>`. While that window still
shows the retail material, `Session_ShowOpenD3Levelshot` (`src/framework/Session.cpp`)
points it at the openD3 picture: the centre at 4:3, the composed picture otherwise.
The layout patch (`guis/layouts/loading.layout`) already fills the screen with that
window, so nothing is cropped. A level screen a mod changed to draw another picture
keeps it, and without `pak2.pk4` every screen is stock.

## Capture settings

The sets are drawn as openD3 draws by default, apart from post effects:

- shadow maps at the Ultra preset's settings (`r_useShadowMap 1`, 4096 projected
  maps in an 8192 atlas, 512 point cubes, 13/9-tap filters, cascades for distant
  lights), not stencil shadows;
- no bloom, SSAO, HDR tone mapping, motion blur, CRT, light grid, MSAA or post AA;
- `g_fov 90`, Doom 3's default; every recovered camera uses it;
- `r_levelshotSupersample 2`: each 1024 tile is area-averaged from a 2731x2048
  render.

Leave `s_constantAmplitude` at its default. Doom 3 feeds the same amplitude to view
shake and to `idEarthQuake`, which pushes loose objects about, so a constant amplitude
shakes the view without end and can move props in the shot.

## Recovering a retail camera

`tools/assets/levelshots/recover_levelshot_cameras.py` drives one openD3 client per
level through `levelshotProbe` (see openQ4's `docs/dev/levelshot-capture.md` for the
command) and needs `OPEND3_DOOM3_BASE` set to the Doom 3 `base` directory:

1. **Sweep.** Candidate positions are entity origins from the level's `.map` and, with
   `--floor`, points at eye height over the upward-facing surfaces of its `.proc`
   areas. Each position is rendered at several headings and pitches into small probes.
   Every probe is matched against the retail picture with RootSIFT after CLAHE, scored
   by fundamental-matrix inliers.
   With `--cube` (which found the last eight sets, including the shots looking steeply
   up or down and the tilted `comm1`), each position is rendered as the six square
   faces of a cube, with depth, so every direction is covered. Each face is scored by
   the pose it supports: its matches become world points through its depth, and PnP
   counts how many agree on one retail camera. A repeated floor or ceiling texture
   matches many points but rarely a single pose, which made raw match counts useless
   here. `--region` sweeps a grid around an estimate instead of the level's positions.
2. **Solve.** The best candidates are rendered at 640x480 with depth. Matched points
   become world points through the probe depth; PnP (SQPnP in RANSAC) gives a new
   camera, which is rendered and matched again until it settles. Matches whose depth is
   under 40 units are rejected as close-ups of a repeated texture.
3. **Polish.** A bounded pattern search over position and angles maximises the
   alignment of luminance and edge images with the retail picture. The field of view
   stays at 90 degrees: estimating it from the matches was unstable where the matched
   depths span little.

Results go to `.tmp/levelshots/results/<map>.json`, with `<map>_cmp.png` showing the
retail picture beside the solved render. Check every one by eye.

## Capturing a set

`tools/assets/levelshots/capture_levelshots.py` reads the cameras file and captures each
level in two runs. The first renders the camera every few frames for 30 seconds and
scores each frame against the retail picture, which finds the moment flickering and
cycling lights match it. The second, a fresh client, waits for that game time with
`after <ms>` and takes a check probe and the five tiles in one frame. If the check
scores more than 3% below the sweep's best, the next-best moments are tried. A camera
with a recorded `time` is captured at that time without a sweep.
`review_levelshots.py` composes 21:9 and 9:16 pictures the way the engine does, for
review.

## Running clients from a script

- Clients started minimized draw nothing (every probe is black). The tools open the
  window normally without activating it and move it beyond the desktop.
- One frame that renders a few hundred probes can kill the client without a log;
  requests are sent 48 probes at a time.
- Two OpenGL clients that initialise at the same moment can hang; launches are
  serialised and retried.
- A multiplayer map starts a listen server, which sends heartbeats to the master server
  unless `net_LANServer 1`.
- On the first frames after a load with shadow maps on, probes come back black; the
  capture tools never use the first four seconds.

## Glass in off-axis views

Doom 3's heat-haze vertex programs (`heatHaze.vfp` and its two masked variants, used by
the `glass` materials) scale the refraction by the projection's first row dotted with
`( 1, 0, z, 1 )`. That is the x scale only while the projection is symmetric. A
levelshot side tile, or a centre tile larger than the window (rendered as off-axis
regions), has a z term there, and the glass smeared the scene behind it. The OpenGL
backend now rewrites that line to the x scale alone when it loads those programs
(`RB_ARBRewriteHeatHazeProjectionScale`, `src/renderer/draw_arb2.cpp`), which leaves
ordinary views as they were. VR eyes use off-axis projections too and get the same
fix; the Vulkan renderer's heat haze was not checked.

## Remaining differences

The retail pictures were taken in pre-release builds. Where the shipped level differs,
the shipped level wins: `cpuboss`'s floor is lighter, `delta1` lacks a dark column on
the right, `delta2a`'s ceiling lights are dimmer, `hellhole`'s overhead lamp is off at
every time the sweep tried, `delta4` has no console in the foreground, `commoutside`
has no large pipe across the floor, `comm1`'s wall lamps are white rather than red,
and `recycling2` shows a red alarm glow at every time tried. `recycling1` and `enpro`
settle a little from the retail camera (a door frame nearer the camera, the beam's
angle), where the geometry around them differs. Retail pictures have a black band
along the bottom, which the loading screen's bottom bar covers; the sets show the
level there.

`d3dm1`'s picture is taken while the reactor fires. Its script (`laser_loop` in
`maps/game/mp/d3dm1.script`) starts 5 seconds after load and repeats about every 30.5
seconds; `tored()` fades the room to red over 1.5 seconds about 16 seconds in. The set
is captured at 17.6 seconds, early in that fade, where the picture's average colour
matches the retail one; the fully red room is far more saturated than the retail
picture.
