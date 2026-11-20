# Copyright (C) 2026 DarkMatter Productions. GPL-3.0-or-later.
"""Capture five-tile levelshot sets at recovered cameras, timed to the retail light state.

python capture_levelshots.py [shot ...] [--out <dir>] [--size 1024] [--sweep 30] [--results]
Cameras come from doom3_levelshots.json beside this script ({"<shot>": {"cam": [x, y, z,
pitch, yaw, roll], "fov": f, "time": ms, "stage": [cmds]}}), or with --results from
recover_levelshot_cameras.py's output. A camera with a "time" is captured at that time
without a sweep. Output defaults to content/baseod3/pak2/guis/assets/levelshots.

Run 1 renders the camera every few frames for --sweep seconds and scores each frame
against the retail picture; run 2 is a fresh client gated with "after <best time>",
which renders a check probe and the levelshot in the same frame.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

import levelshot_match as geom
from levelshot_client import REPO, WORK, Session, probe_line, read_tga, read_pose

HERE = Path(__file__).resolve().parent
RESULTS = WORK / "results"
CAMERAS = HERE / "doom3_levelshots.json"
OUT = REPO / "content" / "baseod3" / "pak2" / "guis" / "assets" / "levelshots"
USE_RESULTS = False
TILES = ("", "_left", "_right", "_top", "_bottom")


def log(shot, *a):
    print(f"[{time.strftime('%H:%M:%S')}] {shot}:", *a, flush=True)


def spec_for(shot):
    if USE_RESULTS:
        r = RESULTS / f"{shot}.json"
        return json.loads(r.read_text()) if r.exists() else {}
    spec = dict(json.loads(CAMERAS.read_text())["sets"].get(shot, {}))
    if "time" in spec:
        spec["after"] = spec["time"]
    return spec


def photo_score(target, rgb):
    a = geom.edge_desc(rgb)
    n = a.size // 2
    return float(target[:n] @ a[:n] + target[n:] @ a[n:])


def session(shot, spec, home, extra=None):
    ex = {"r_levelshotSupersample": "2"}
    if shot in geom.MP:
        ex.update({"si_gameType": "deathmatch", "net_allowCheats": "1", "net_LANServer": "1"})
    ex.update(extra or {})
    for attempt in range(4):
        s = Session(home, geom.map_path(shot), extra=ex, wait_ms=10000, after_load=spec.get("stage", []))
        try:
            if s.request([probe_line("lsq/warm", 64, 48, (0, 0, 0, 0, 0, 0))], timeout=150):
                return s
        except RuntimeError:
            pass
        s.close()
        log(shot, f"client start {attempt + 1} failed; retrying")
        time.sleep(20)
    raise RuntimeError("client never served")


def sweep(shot, spec, seconds, home):
    target = geom.edge_desc(geom.retail_shot(shot))
    cam, fov = tuple(spec["cam"]), spec.get("fov", 90.0)
    s = session(shot, spec, home)
    rows = []
    try:
        t_end = None
        while True:
            s.request([probe_line("lsq/t", 320, 240, cam, fov=fov)])
            pose = read_pose(s.out("lsq/t.pose"))
            t = int(pose[10])
            rows.append((t, photo_score(target, read_tga(s.out("lsq/t.tga")))))
            if t_end is None:
                t_end = t + seconds * 1000
            if t >= t_end:
                break
    finally:
        s.close()
    return rows


def capture(shot, spec, out: Path, size: int, after: int | None, home):
    s = session(shot, spec, home)
    try:
        gen = s.out("gfx/guis/loadscreens")
        if gen.exists():
            shutil.rmtree(gen)
        x, y, z, p, yw, r = spec["cam"]
        fov = spec.get("fov", 90.0)
        lines = [f"after {after}"] if after else []
        lines.append(probe_line("lsq/check", 640, 480, spec["cam"], fov=fov))
        lines.append(f"levelshot {size} {x:.4f} {y:.4f} {z:.4f} {p:.5f} {yw:.5f} {r:.5f} {fov:.4f}")
        if not s.request(lines, timeout=900):
            raise RuntimeError("levelshot timed out")
        check = read_tga(s.out("lsq/check.tga"))
        t = int(read_pose(s.out("lsq/check.pose"))[10])
        name = geom.map_path(shot).split("/")[-1]
        tiles = {tile: Image.open(gen / f"{name}{tile}.tga").convert("RGB") for tile in TILES}
        return t, check, tiles
    finally:
        s.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--results", action="store_true", help="read cameras from the recovery results")
    ap.add_argument("--review", default=str(WORK / "review"), help="where check images and records go")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--sweep", type=float, default=30)
    ap.add_argument("--home", default="cap")
    a = ap.parse_args()
    global USE_RESULTS
    USE_RESULTS = a.results
    out = Path(a.out)
    review = Path(a.review)
    review.mkdir(parents=True, exist_ok=True)
    shots = a.shots or (sorted(p.stem for p in RESULTS.glob("*.json")) if a.results
                        else sorted(json.loads(CAMERAS.read_text())["sets"]))
    for shot in shots:
        spec = spec_for(shot)
        if not spec.get("found", "cam" in spec):
            log(shot, "no camera; skipped")
            continue
        t0 = time.time()
        target = geom.edge_desc(geom.retail_shot(shot))
        times = [spec["after"]] if spec.get("after") is not None else []
        best = None
        sw = spec.get("sweep", a.sweep)
        if not times and sw > 0:
            rows = sweep(shot, spec, sw, a.home)
            first = rows[0][0]
            usable = sorted([r for r in rows if r[0] >= first + 4000] or rows, key=lambda r: -r[1])
            for tm, sc in usable:  # three distinct moments, best first
                if all(abs(tm - x) > 400 for x in times):
                    times.append(tm)
                if len(times) == 3:
                    break
            best = usable[0][1]
            log(shot, f"sweep {len(rows)} frames {first}..{rows[-1][0]} ms: best {best:.4f} at {times[0]}, worst {usable[-1][1]:.4f}")
        kept = None
        for tm in times or [None]:
            t, check, tiles = capture(shot, spec, out, a.size, tm, a.home)
            score = photo_score(target, check)
            log(shot, f"  capture at {t} ms (asked {tm}): score {score:.4f}")
            if kept is None or score > kept[0]:
                kept = (score, t, check, tiles)
            if best is None or score >= best * 0.97:
                break
        score, t, check, tiles = kept
        out.mkdir(parents=True, exist_ok=True)
        for tile, im in tiles.items():
            im.save(out / f"{shot}{tile}.jpg", quality=95, subsampling=0, optimize=True)
        cmp = np.concatenate([geom.retail_shot(shot), check], axis=1)
        cv2.imwrite(str(review / f"{shot}_check.png"), cv2.cvtColor(cmp, cv2.COLOR_RGB2BGR))
        rec = {"shot": shot, "cam": spec["cam"], "fov": spec.get("fov", 90.0), "time": t, "score": score,
               "sweep_best": best, "stage": spec.get("stage", [])}
        (review / f"{shot}_capture.json").write_text(json.dumps(rec, indent=1))
        log(shot, f"captured at {t} ms, score {score:.4f} ({time.time() - t0:.0f}s)")

if __name__ == "__main__":
    main()
