# Copyright (C) 2026 DarkMatter Productions. GPL-3.0-or-later.
"""Recover the retail camera of Doom 3's loading-screen pictures.

python recover_levelshot_cameras.py [shot ...] [--workers N] [--fresh] [--floor] [--cube] [--dense] [--force]
Writes <work>/results/<shot>.json and <shot>_cmp.png (retail | render). A shot with a
found result is re-solved from it unless --fresh. See docs/dev/levelshot-capture.md.
"""
from __future__ import annotations

import argparse
import json
import math
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

import levelshot_match as geom
from levelshot_match import W, H
from levelshot_client import WORK, Session, probe_line, read_tga, read_depth

RESULTS = WORK / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

SHOTS = ["admin", "alphalabs1", "alphalabs2", "alphalabs3", "alphalabs4", "caverns1", "caverns2",
         "comm1", "commoutside", "cpu", "cpuboss", "d3dm1", "d3dm2", "d3dm3", "d3dm4", "d3dm5",
         "delta1", "delta2a", "delta2b", "delta3", "delta4", "delta5", "enpro", "hellhole",
         "mars_city2", "mc_underground", "monorail", "recycling1", "recycling2", "site3"]

launch_lock = threading.Lock()
POOL = ThreadPoolExecutor(14)
FRESH = False
CELL = 144
PITCHES = (-15, 15)
YAWSTEP = 45
FLOOR = False
FORCE = False
LEVEL = False
REGION = None
CUBE = False
WIDE_POLISH = False
# cube faces as (pitch, yaw); pitch -90 looks up
FACES = ((0, 0), (0, 90), (0, 180), (0, 270), (-90, 0), (90, 0))
FACE = 256
import queue
homes: queue.Queue = queue.Queue()
CW, CH = 160, 120


def log(shot, *a):
    print(f"[{time.strftime('%H:%M:%S')}] {shot}:", *a, flush=True)


def candidates(shot):
    if REGION:
        x0, x1, y0, y1, z0, z1, step = REGION
        import numpy as _np
        return [(x, y, z) for x in _np.arange(x0, x1 + 1e-3, step) for y in _np.arange(y0, y1 + 1e-3, step)
                for z in _np.arange(z0, z1 + 1e-3, step)]
    pts = []
    for e in geom.map_entities(shot):
        o = e.get("origin")
        if not o:
            continue
        try:
            x, y, z = (float(v) for v in o.split()[:3])
        except ValueError:
            continue
        cls = e.get("classname", "")
        if cls.startswith("light"):
            pts.append((x, y, z - 24))
        elif cls.startswith(("info_player", "path_", "monster_", "item_", "ammo_", "weapon_", "moveable_", "func_door", "trigger")):
            pts.append((x, y, z + 64))
        else:
            pts.append((x, y, z + 8))
    # thin to one position per cell
    seen, out = set(), []
    for p in pts:
        k = tuple(int(math.floor(c / CELL)) for c in p)
        if k not in seen:
            seen.add(k)
            out.append(p)
    if FLOOR:
        # eye height above the level's floors, so candidates stand in open space,
        # on a coarser grid than the entity positions
        floor_seen = set()
        for (x, y, z) in geom.floor_points(shot):
            p = (x, y, z + 64)
            k = tuple(int(math.floor(c / (CELL * 1.5))) for c in p)
            if k not in floor_seen and tuple(int(math.floor(c / CELL)) for c in p) not in seen:
                floor_seen.add(k)
                out.append(p)
    return out


class Recover:
    def __init__(self, shot, session: Session):
        self.shot = shot
        self.s = session
        self.retail = geom.retail_shot(shot)
        self.retail_feat = geom.rootsift(self.retail)
        self.retail_desc = geom.coarse_desc(self.retail)
        self.n = 0

    def render(self, cams, w, h, depth=False, fov=90.0, chunk=48, timeout=180, fovs=None):
        """Render probes; returns list of (rgb, depth|None)."""
        out = []
        fovs = fovs or [fov] * len(cams)
        for i in range(0, len(cams), chunk):
            names, lines = [], []
            for cam, fv in zip(cams[i:i + chunk], fovs[i:i + chunk]):
                self.n += 1
                name = f"lsq/p/{self.n}"
                names.append(name)
                lines.append(probe_line(name, w, h, cam, fov=fv, depth=depth))
            if not self.s.request(lines, timeout=timeout):
                raise RuntimeError("probe request timed out")
            for name in names:
                tga = self.s.out(name + ".tga")
                rgb = read_tga(tga) if tga.exists() else np.zeros((h, w, 3), np.uint8)
                d = None
                dp = self.s.out(name + ".depth")
                if depth and dp.exists():
                    d = read_depth(dp, w, h)
                out.append((rgb, d))
                for ext in (".tga", ".depth", ".pose"):
                    p = self.s.out(name + ext)
                    if p.exists():
                        p.unlink()
        return out

    def coarse(self, top=40):
        pos = candidates(self.shot)
        cams = [(x, y, z, p, yw, 0.0) for (x, y, z) in pos for p in PITCHES for yw in range(0, 360, YAWSTEP)]
        log(self.shot, f"coarse sweep: {len(pos)} positions, {len(cams)} probes")
        small = cv2.resize(self.retail, (CW, CH), interpolation=cv2.INTER_AREA)
        rfeat = geom.rootsift(small)

        def score(rgb):
            if rgb.mean() < 1.0:
                return 0
            pa, pb = geom.match(rfeat, geom.rootsift(rgb))
            n, _ = geom.fundamental_inliers(pa, pb, 1.5)
            return n

        scored = []
        for i in range(0, len(cams), 960):
            batch = cams[i:i + 960]
            imgs = [rgb for rgb, _ in self.render(batch, CW, CH)]
            for cam, n in zip(batch, POOL.map(score, imgs)):
                scored.append((n, cam))
        scored.sort(key=lambda t: -t[0])
        log(self.shot, "coarse best:", [(n, tuple(round(v) for v in c)) for n, c in scored[:5]])
        return [c for _, c in scored[:top]]

    def coarse_cube(self, top=40):
        """Every direction from every candidate position: six square 90 degree faces each,
        rendered with depth. Each face is scored by the retail camera pose it supports: matches
        to the retail picture become world points through the face's depth, and PnP finds how
        many agree on one camera. A repeated texture rarely does."""
        pos = candidates(self.shot)
        cams = [(x, y, z, p, yw, 0.0) for (x, y, z) in pos for (p, yw) in FACES]
        log(self.shot, f"cube sweep: {len(pos)} positions, {len(cams)} faces")

        def score(args):
            face, rgb, d = args
            if d is None or rgb.mean() < 1.0:
                return 0, None
            return self.pose_from_matches(face, rgb, d, FACE)

        scored = []
        for i in range(0, len(cams), 240):
            batch = cams[i:i + 240]
            shots = self.render(batch, FACE, FACE, depth=True)
            for (k, cam) in POOL.map(score, [(f, rgb, d) for f, (rgb, d) in zip(batch, shots)]):
                if cam is not None:
                    scored.append((k, cam))
        scored.sort(key=lambda t: -t[0])
        log(self.shot, "cube poses:", [(k, tuple(round(v) for v in c)) for k, c in scored[:6]])
        return scored[:top]

    def pose_from_matches(self, face, rgb, d, size):
        """The retail camera from one square face's matches and depth (PnP), wherever the face stands."""
        pa, pb = geom.match(self.retail_feat, geom.rootsift(rgb))
        n, mask = geom.fundamental_inliers(pa, pb)
        if n < 10:
            return 0, None
        pr, pp = pa[mask].astype(np.float64), pb[mask].astype(np.float64)
        ui = np.clip(np.round(pp).astype(int), 1, size - 2)
        dz = d[ui[:, 1], ui[:, 0]]
        win = np.stack([d[ui[:, 1] + dy, ui[:, 0] + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
        ok = (dz > 40) & (win.min(0) > 0) & (win.max(0) / np.maximum(win.min(0), 1e-3) < 1.04)
        if ok.sum() < 8:
            return 0, None
        f = size / 2
        world = geom.unproject(face, pp[ok], dz[ok].astype(np.float64), fx=f, fy=f, cx=size / 2, cy=size / 2)
        try:
            okp, rvec, tvec, inl = cv2.solvePnPRansac(world, pr[ok], geom.K(), None, iterationsCount=2000,
                                                       reprojectionError=4.0, confidence=0.999,
                                                       flags=cv2.SOLVEPNP_SQPNP)
        except cv2.error:
            return 0, None
        if not okp or inl is None or len(inl) < 8:
            return 0, None
        inl = inl.ravel()
        rvec, tvec = cv2.solvePnPRefineLM(world[inl], pr[ok][inl], geom.K(), None, rvec, tvec)
        R, _ = cv2.Rodrigues(rvec)
        cam = geom.cv_to_cam(R, tvec.ravel())
        if not np.all(np.isfinite(cam)) or abs(cam[5]) > 60:
            return 0, None
        return len(inl), cam

    def evaluate(self, cam, fov=90.0):
        (rgb, d), = self.render([cam], W, H, depth=True, fov=fov)
        feat = geom.rootsift(rgb)
        pa, pb = geom.match(self.retail_feat, feat)
        n, mask = geom.fundamental_inliers(pa, pb)
        return n, pa[mask] if n else pa[:0], pb[mask] if n else pb[:0], rgb, d

    def solve(self, cam, fov=90.0, iters=10, free_focal=False):
        """Render, match, solve PnP for the retail camera (and its focal length), repeat."""
        best = None
        last_move = 1e9
        for it in range(iters):
            n, pr, pp, rgb, d = self.evaluate(cam, fov)
            if n < 12 or d is None:
                log(self.shot, f"  it{it}: stop, {n} matches, depth {d is not None}")
                break
            ui = np.clip(np.round(pp).astype(int), 1, [W - 2, H - 2])
            dz = d[ui[:, 1], ui[:, 0]]
            win = np.stack([d[ui[:, 1] + dy, ui[:, 0] + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
            ok = (dz > 0) & (win.min(0) > 0) & (win.max(0) / np.maximum(win.min(0), 1e-3) < 1.04)
            if ok.sum() < 10:
                log(self.shot, f"  it{it}: stop, {int(ok.sum())} matches on smooth depth")
                break
            fr = geom.fov_to_f(fov)
            world = geom.unproject(cam, pp[ok].astype(np.float64), dz[ok].astype(np.float64), fx=fr, fy=fr)
            img = pr[ok].astype(np.float64)
            Kr = geom.K(geom.fov_to_f(fov), geom.fov_to_f(fov))
            okp, rvec, tvec, inl = cv2.solvePnPRansac(world, img, Kr, None, iterationsCount=5000,
                                                       reprojectionError=3.0, confidence=0.999,
                                                       flags=cv2.SOLVEPNP_SQPNP)
            if not okp or inl is None or len(inl) < 8:
                log(self.shot, f"  it{it}: stop, PnP failed ({0 if inl is None else len(inl)} of {len(world)})")
                break
            inl = inl.ravel()
            newfov = fov
            # the focal length is only estimated once the pose has settled
            if free_focal and len(inl) >= 40 and it >= 2 and last_move < 25:
                flags = (cv2.CALIB_USE_INTRINSIC_GUESS | cv2.CALIB_FIX_PRINCIPAL_POINT | cv2.CALIB_FIX_ASPECT_RATIO |
                         cv2.CALIB_ZERO_TANGENT_DIST | cv2.CALIB_FIX_K1 | cv2.CALIB_FIX_K2 | cv2.CALIB_FIX_K3)
                try:
                    _, Kc, _, rv, tv = cv2.calibrateCamera([world[inl].astype(np.float32)], [img[inl].astype(np.float32)],
                                                          (W, H), Kr.copy(), np.zeros(5), [rvec], [tvec], flags=flags)
                    newfov = geom.f_to_fov(Kc[0, 0])
                    if abs(newfov - 90) < 12:
                        rvec, tvec, Kr = rv[0], tv[0], Kc
                    else:
                        newfov = fov
                except cv2.error:
                    newfov = fov
            rvec, tvec = cv2.solvePnPRefineLM(world[inl], img[inl], Kr, None, rvec, tvec)
            proj, _ = cv2.projectPoints(world[inl], rvec, tvec, Kr, None)
            err = float(np.median(np.linalg.norm(proj.reshape(-1, 2) - img[inl], axis=1)))
            R, _ = cv2.Rodrigues(rvec)
            new = geom.cv_to_cam(R, tvec.ravel())
            # a render at the starting guess is only a fallback: prefer poses the solve produced
            if it > 0 and (best is None or best.get("start") or n > best["inliers"]):
                best = dict(cam=cam, fov=fov, inliers=n, pnp=int(len(inl)), err=err, rgb=rgb)
            elif best is None:
                best = dict(cam=cam, fov=fov, inliers=n, pnp=int(len(inl)), err=err, rgb=rgb, start=True)
            move = np.linalg.norm(np.subtract(new[:3], cam[:3]))
            if not np.all(np.isfinite(new)) or move > 300 or abs(new[5]) > 45:
                log(self.shot, f"  it{it}: stop, solve jumped {move:.0f} units")
                break
            turn = max(abs((new[i] - cam[i] + 180) % 360 - 180) for i in (3, 4, 5))
            log(self.shot, f"  it{it}: inliers {n} pnp {len(inl)} err {err:.2f}px move {move:.1f} turn {turn:.2f} fov {newfov:.2f}")
            df = abs(newfov - fov)
            last_move = move
            cam, fov = new, newfov
            if move < 0.25 and turn < 0.03 and df < 0.05:
                break
        n, *_rest, rgb, d = self.evaluate(cam, fov)
        if best is None or best.get("start") or n >= best["inliers"]:
            best = dict(cam=cam, fov=fov, inliers=n, pnp=best["pnp"] if best else 0,
                        err=best["err"] if best else -1, rgb=rgb)
        return best

    def refine(self, cam, fov=90.0, rounds=40):
        """Bounded pattern search on edge alignment around the geometric solution."""
        target = geom.edge_desc(self.retail)
        p = list(cam) + [fov]
        origin = list(p)
        limit = [4.0, 4.0, 4.0, 0.4, 0.4, 0.0 if LEVEL else 0.4, 0.0]  # fov stays at Doom 3's 90
        steps = [1.5, 1.5, 1.5, 0.15, 0.15, 0.15, 0.3]
        if WIDE_POLISH:
            # a wider search where the solve cannot settle (pre-release geometry near the camera)
            limit = [100.0, 100.0, 100.0, 10.0, 10.0, 0.0 if LEVEL else 5.0, 0.0]
            steps = [24.0, 24.0, 24.0, 2.0, 2.0, 1.0, 0.3]
            rounds = 80
        floor = [0.2, 0.2, 0.2, 0.02, 0.02, 0.02, 0.05]

        def evalp(ps):
            imgs = self.render([tuple(q[:6]) for q in ps], 320, 240, fov=None, fovs=[q[6] for q in ps])
            return [geom.edge_score(target, geom.edge_desc(rgb)) for rgb, _ in imgs]

        cur = evalp([p])[0]
        start = cur
        for r in range(rounds):
            cands = []
            for i in range(7):
                for s in (-1, 1):
                    q = list(p)
                    q[i] += s * steps[i]
                    if abs(q[i] - origin[i]) <= limit[i]:
                        cands.append(q)
            scores = evalp(cands)
            j = int(np.argmax(scores))
            if scores[j] > cur + 1e-5:
                p, cur = cands[j], scores[j]
            else:
                steps = [max(f, s * 0.5) for s, f in zip(steps, floor)]
                if all(s <= f for s, f in zip(steps, floor)):
                    break
        log(self.shot, f"  refine: score {start:.4f} -> {cur:.4f}, fov {p[6]:.2f}")
        return tuple(p[:6]), p[6], cur

    def run(self):
        seed = RESULTS / f"{self.shot}.json"
        prior = json.loads(seed.read_text()) if seed.exists() else {}
        if prior.get("found") and not FRESH:
            log(self.shot, "seeded from", prior["cam"])
            top = [tuple(prior["cam"])]
            self.seed_fov = prior.get("fov", 90.0)
        elif CUBE:
            top = [c for _, c in self.coarse_cube()]
        else:
            top = self.coarse()
        scored = []
        for cam in top:
            n, pr, pp, rgb, d = self.evaluate(cam)
            if d is not None and n and len(pp):
                ui = np.clip(np.round(pp).astype(int), 0, [W - 1, H - 1])
                dz = d[ui[:, 1], ui[:, 0]]
                if np.median(dz[dz > 0]) < 40 if (dz > 0).any() else True:
                    n = 0  # a wall close-up matching a repeated texture
            scored.append((n, cam))
        scored.sort(key=lambda t: -t[0])
        log(self.shot, "fine candidates:", [(n, tuple(round(v) for v in c)) for n, c in scored[:8]])
        results = []
        for n, cam in scored[:10]:
            if n < 15:
                continue
            r = self.solve(cam)
            if r and r["err"] >= 0:
                results.append(r)
                if r["inliers"] > 120 and r["err"] < 1.5:
                    break
        if not results:
            return None
        best = max(results, key=lambda r: r["inliers"])
        start = list(best["cam"])
        if LEVEL:
            start[5] = 0.0  # the retail shot is level
        cam, fov, score = self.refine(tuple(start), 90.0)
        (rgb, _), = self.render([cam], W, H, fov=fov)
        best.update(cam=cam, fov=fov, edge=score, rgb=rgb)
        return best


def process(shot, retry=True):
    try:
        mapname = geom.map_path(shot)
        # the search needs geometry only: stencil shadows are cheaper; the shots use shadow maps
        extra = {"r_useShadowMap": "0"}
        if shot in geom.MP:
            extra.update({"si_gameType": "deathmatch", "net_allowCheats": "1", "net_LANServer": "1"})
        name = homes.get()
        with launch_lock:
            # hold the lock until the world draws so GL clients never initialise together
            for attempt in range(4):
                s = Session(name, mapname, extra=extra, wait_ms=10000)
                try:
                    if s.request([probe_line("lsq/warm", 64, 48, (0, 0, 0, 0, 0, 0))], timeout=150):
                        break
                except RuntimeError:
                    pass
                s.close()
                log(shot, f"client start {attempt + 1} failed")
                time.sleep(20)
            else:
                raise RuntimeError("client never served the first probe")
        try:
            run_one(shot, s)
        finally:
            s.close()
            homes.put(name)
    except Exception:
        log(shot, "FAILED\n" + traceback.format_exc())
        if retry:
            log(shot, "retrying once")
            process(shot, retry=False)


def run_one(shot, s):
    if True:
            rec = Recover(shot, s)
            t0 = time.time()
            best = rec.run()
            if best is None:
                log(shot, "NO MATCH")
                res = RESULTS / f"{shot}.json"
                if not (res.exists() and json.loads(res.read_text()).get("found")):
                    res.write_text(json.dumps({"shot": shot, "found": False}))
                return
            cam = best["cam"]
            res = RESULTS / f"{shot}.json"
            prior = json.loads(res.read_text()) if res.exists() else {}
            if prior.get("found") and not FORCE and not (best["err"] >= 0 and best["err"] <= max(1.0, prior.get("err", 9) * 1.25)
                                           and best["inliers"] >= 0.7 * prior.get("inliers", 0)
                                           and np.linalg.norm(np.subtract(cam[:3], prior["cam"][:3])) < 120):
                log(shot, f"KEPT prior (new inliers {best['inliers']} err {best['err']:.2f} not better)")
                return
            log(shot, f"BEST inliers {best['inliers']} err {best['err']:.2f} cam {tuple(round(v, 2) for v in cam)} ({time.time() - t0:.0f}s)")
            cmp = np.concatenate([rec.retail, best["rgb"]], axis=1)
            cv2.imwrite(str(RESULTS / f"{shot}_cmp.png"), cv2.cvtColor(cmp, cv2.COLOR_RGB2BGR))
            (RESULTS / f"{shot}.json").write_text(json.dumps(
                {"shot": shot, "found": True, "cam": cam, "fov": best.get("fov", 90.0), "edge": best.get("edge"),
                 "inliers": best["inliers"], "pnp": best["pnp"], "err": best["err"]}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--cell", type=float, default=144)
    ap.add_argument("--homes", default="w")
    ap.add_argument("--dense", action="store_true")
    ap.add_argument("--floor", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--wide", action="store_true")
    ap.add_argument("--wide-polish", action="store_true", help="polish over +-100 units and +-10 degrees")
    ap.add_argument("--cube", action="store_true", help="sweep six cube faces per position and solve from each face")
    ap.add_argument("--level", action="store_true", help="hold roll at 0 in the final polish")
    ap.add_argument("--region", help="x0,x1,y0,y1,z0,z1,step: a grid of positions instead of the level's")
    ap.add_argument("--pitches", help="comma-separated sweep pitches")
    ap.add_argument("--yawstep", type=int)
    a = ap.parse_args()
    global FRESH, CELL, PITCHES, YAWSTEP, CW, CH, FLOOR
    FRESH = a.fresh
    FLOOR = a.floor
    global FORCE, LEVEL
    FORCE = a.force
    LEVEL = a.level
    global REGION, CUBE, WIDE_POLISH
    CUBE = a.cube
    WIDE_POLISH = a.wide_polish
    if a.region:
        REGION = tuple(float(v) for v in a.region.split(","))
    if a.pitches:
        PITCHES = tuple(float(v) for v in a.pitches.split(","))
    if a.yawstep:
        YAWSTEP = a.yawstep
    CELL = a.cell
    if a.wide:
        CELL, FLOOR, PITCHES, YAWSTEP, CW, CH = 192, True, (-35, -10, 15), 45, 200, 150
    if a.dense:
        CELL, PITCHES, YAWSTEP, CW, CH = min(CELL, 96), (-30, -10, 10, 30), 30, 200, 150
    shots = a.shots or SHOTS
    for i in range(a.workers):
        homes.put(f"{a.homes}{i}")
    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(process, shots))


if __name__ == "__main__":
    main()
