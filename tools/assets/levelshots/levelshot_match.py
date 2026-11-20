# Copyright (C) 2026 DarkMatter Productions. GPL-3.0-or-later.
"""Retail inputs, idTech 4 camera maths and image matching for levelshot recovery."""
from __future__ import annotations

import io
import os
import math
import re
import zipfile
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# The retail Doom 3 base directory (the one holding pak000.pk4).
D3BASE = Path(os.environ.get("OPEND3_DOOM3_BASE", ""))
W, H = 640, 480          # working resolution for the 4:3 view
FX = FY = W / 2          # 90 degree horizontal fov at 4:3
CX, CY = W / 2, H / 2

MP = {"d3dm1", "d3dm2", "d3dm3", "d3dm4", "d3dm5"}


def map_path(shot: str) -> str:
    return f"game/mp/{shot}" if shot in MP else f"game/{shot}"


@lru_cache(maxsize=None)
def _paks():
    if not (D3BASE / "pak000.pk4").exists():
        raise SystemExit("set OPEND3_DOOM3_BASE to the Doom 3 install's base directory")
    return [zipfile.ZipFile(p) for p in sorted(D3BASE.glob("pak*.pk4"), reverse=True)]


def retail_read(name: str) -> bytes:
    for z in _paks():
        try:
            return z.read(name)
        except KeyError:
            continue
    raise KeyError(name)


def retail_shot(shot: str) -> np.ndarray:
    """The retail picture unstretched back to 4:3 at the working resolution (RGB)."""
    im = Image.open(io.BytesIO(retail_read(f"guis/assets/splash/{shot}.tga"))).convert("RGB")
    return np.asarray(im.resize((W, H), Image.LANCZOS))


def map_entities(shot: str) -> list[dict]:
    text = retail_read(f"maps/{map_path(shot)}.map").decode("latin1")
    ents, depth, cur = [], 0, None
    pair = re.compile(r'^\s*"([^"]*)"\s+"([^"]*)"\s*$')
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("//"):
            continue
        if s == "{":
            depth += 1
            if depth == 1:
                cur = {}
            continue
        if s == "}":
            if depth == 1 and cur is not None:
                ents.append(cur)
            depth -= 1
            continue
        if depth == 1:
            m = pair.match(line)
            if m:
                cur[m.group(1)] = m.group(2)
    return ents


# -- idAngles / camera ------------------------------------------------------------

def angles_to_axis(pitch, yaw, roll):
    sp, cp = math.sin(math.radians(pitch)), math.cos(math.radians(pitch))
    sy, cy = math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
    sr, cr = math.sin(math.radians(roll)), math.cos(math.radians(roll))
    f = np.array([cp * cy, cp * sy, -sp])
    l = np.array([sr * sp * cy + cr * -sy, sr * sp * sy + cr * cy, sr * cp])
    u = np.array([cr * sp * cy + -sr * -sy, cr * sp * sy + -sr * cy, cr * cp])
    return f, l, u


def axis_to_angles(f, l, u):
    sp = max(-1.0, min(1.0, f[2]))
    theta = -math.asin(sp)
    pitch = math.degrees(theta)
    yaw = math.degrees(math.atan2(f[1], f[0]))
    roll = math.degrees(math.atan2(l[2], u[2]))
    return pitch, yaw % 360.0, roll


def unproject(cam, uv: np.ndarray, d: np.ndarray, fx=FX, fy=FY, cx=CX, cy=CY) -> np.ndarray:
    x, y, z, p, yw, r = cam
    f, l, u = angles_to_axis(p, yw, r)
    org = np.array([x, y, z])
    lc = (cx - uv[:, 0]) * d / fx
    hc = (cy - uv[:, 1]) * d / fy
    return org + d[:, None] * f + lc[:, None] * l + hc[:, None] * u


def cam_to_cv(cam):
    x, y, z, p, yw, r = cam
    f, l, u = angles_to_axis(p, yw, r)
    R = np.stack([-l, -u, f])
    t = -R @ np.array([x, y, z])
    return R, t


def cv_to_cam(R, t):
    C = -R.T @ t
    l, u, f = -R[0], -R[1], R[2]
    p, yw, r = axis_to_angles(f, l, u)
    return (float(C[0]), float(C[1]), float(C[2]), p, yw, r)


def K(fx=FX, fy=FY):
    return np.array([[fx, 0, CX], [0, fy, CY], [0, 0, 1]], dtype=np.float64)


# -- matching ---------------------------------------------------------------------

import threading
_tls = threading.local()


def _tools():
    if not hasattr(_tls, "sift"):
        _tls.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        _tls.sift = cv2.SIFT_create(nfeatures=4000, contrastThreshold=0.01)
        _tls.matcher = cv2.BFMatcher(cv2.NORM_L2)
    return _tls


def prep(rgb: np.ndarray) -> np.ndarray:
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    return _tools().clahe.apply(g)


def rootsift(rgb: np.ndarray):
    kp, des = _tools().sift.detectAndCompute(prep(rgb), None)
    if des is None or len(kp) == 0:
        return np.zeros((0, 2), np.float32), None
    des = des / (des.sum(axis=1, keepdims=True) + 1e-7)
    des = np.sqrt(des).astype(np.float32)
    return np.float32([k.pt for k in kp]), des


def match(feat_a, feat_b, ratio=0.8):
    """Ratio-test matches; returns (pts_a, pts_b)."""
    pa, da = feat_a
    pb, db = feat_b
    if da is None or db is None or len(pa) < 8 or len(pb) < 8:
        return np.zeros((0, 2)), np.zeros((0, 2))
    knn = _tools().matcher.knnMatch(da, db, k=2)
    good = [m[0] for m in knn if len(m) == 2 and m[0].distance < ratio * m[1].distance]
    if not good:
        return np.zeros((0, 2)), np.zeros((0, 2))
    return pa[[m.queryIdx for m in good]], pb[[m.trainIdx for m in good]]


def fundamental_inliers(pa, pb, thresh=2.0):
    if len(pa) < 12:
        return 0, np.zeros(len(pa), bool)
    try:
        F, mask = cv2.findFundamentalMat(pa, pb, cv2.USAC_MAGSAC, thresh, 0.999, 5000)
    except cv2.error:
        return 0, np.zeros(len(pa), bool)
    if mask is None:
        return 0, np.zeros(len(pa), bool)
    mask = mask.ravel().astype(bool)
    return int(mask.sum()), mask


# -- coarse descriptor ------------------------------------------------------------

def coarse_desc(rgb: np.ndarray) -> np.ndarray:
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    g = cv2.resize(g, (64, 48), interpolation=cv2.INTER_AREA)
    lum = np.log1p(g)
    gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1)
    mag = np.sqrt(gx * gx + gy * gy)
    out = []
    for a in (cv2.GaussianBlur(lum, (5, 5), 1.0), cv2.GaussianBlur(mag, (5, 5), 1.0)):
        a = a - a.mean()
        a = a / (np.linalg.norm(a) + 1e-6)
        out.append(a.ravel())
    hsv = cv2.cvtColor(cv2.resize(rgb, (64, 48), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [12, 4], [0, 180, 0, 256]).ravel()
    hist = np.sqrt(hist / (hist.sum() + 1e-6))
    out.append(hist)
    return np.concatenate(out)


def coarse_score(a: np.ndarray, b: np.ndarray) -> float:
    n = 64 * 48
    return float(a[:n] @ b[:n] + a[n:2 * n] @ b[n:2 * n] + 0.5 * (a[2 * n:] @ b[2 * n:]))


def edge_desc(rgb: np.ndarray, size=(320, 240)) -> np.ndarray:
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    g = cv2.resize(g, size, interpolation=cv2.INTER_AREA)
    lum = np.log1p(g)
    gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1)
    mag = cv2.GaussianBlur(np.sqrt(gx * gx + gy * gy), (0, 0), 1.5)
    lum = cv2.GaussianBlur(lum, (0, 0), 2.0)
    out = []
    for a in (mag, lum):
        a = a - a.mean()
        out.append((a / (np.linalg.norm(a) + 1e-6)).ravel())
    return np.concatenate(out)


def edge_score(a, b):
    n = a.size // 2
    return float(a[:n] @ b[:n] + 0.5 * (a[n:] @ b[n:]))


def fov_to_f(fov_x: float) -> float:
    return (W / 2) / math.tan(math.radians(fov_x) / 2)


def f_to_fov(f: float) -> float:
    return math.degrees(2 * math.atan((W / 2) / f))


def floor_points(shot: str, min_nz=0.8):
    """Vertices of upward-facing world surfaces (the _area models of the .proc)."""
    text = retail_read(f"maps/{map_path(shot)}.proc").decode("latin1")
    pts = []
    for m in re.finditer(r'model \{ /\* name = \*/ "_area\d+"', text):
        end = text.find("\nmodel {", m.end())
        body = text[m.end(): end if end > 0 else len(text)]
        for v in re.finditer(r"\( (\S+) (\S+) (\S+) \S+ \S+ (\S+) (\S+) (\S+) \)", body):
            if float(v.group(6)) >= min_nz:
                pts.append((float(v.group(1)), float(v.group(2)), float(v.group(3))))
    return pts
