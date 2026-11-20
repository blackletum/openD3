# Copyright (C) 2026 DarkMatter Productions. GPL-3.0-or-later.
"""Drive an openD3 client that serves levelshotProbe requests on one map.

Shared by recover_levelshot_cameras.py and capture_levelshots.py; see
docs/dev/levelshot-capture.md."""
from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path

import ctypes
from ctypes import wintypes

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
EXE = REPO / ".install" / "openD3-client_x64.exe"
WORK = Path(os.environ.get("OPEND3_LEVELSHOT_WORK", REPO / ".tmp" / "levelshots"))
RUNS = WORK / "runs"
SHOW = 4  # SW_SHOWNOACTIVATE; 7 = SW_SHOWMINNOACTIVE

# Shadow maps at the Ultra preset's settings (src/framework/PerformancePreset.cpp);
# otherwise the retail presentation: no post effects.
PINS = {
    "r_shadows": "1", "r_useShadowMap": "1", "r_shadowMapSize": "4096", "r_shadowMapMaxUpdatesPerView": "0",
    "r_shadowMapPointSize": "512", "r_shadowMapFilterTaps": "13", "r_shadowMapPointFilterTaps": "9",
    "r_shadowMapFilterMode": "2", "r_shadowMapPointFilterMode": "0", "r_shadowMapAtlasSize": "8192",
    "r_shadowMapCSM": "1", "r_shadowMapPointLights": "1", "r_shadowMapProjectedCSM": "0",
    "r_bloom": "0", "r_ssao": "0", "r_hdrToneMap": "0",
    "r_motionBlur": "0", "r_crt": "0", "r_useLightGrid": "0", "r_postAA": "0",
    "r_multiSamples": "0", "r_screenFraction": "100", "image_anisotropy": "8",
    "image_downSize": "0", "image_picmip": "0", "image_ignoreHighQuality": "0",
    "g_fov": "90", "ui_showGun": "0", "g_showHud": "0", "in_mouse": "0",
    "s_noSound": "0", "s_muteUnfocused": "0",
}


class Session:
    def __init__(self, name: str, mapname: str, width=1024, height=768, renderer="gl",
                 extra: dict | None = None, wait_ms=12000, after_load: list[str] | None = None):
        self.name = name
        self.home = RUNS / name
        self.game = self.home / "baseod3"
        self.lsq = self.game / "lsq"
        self.lsq.mkdir(parents=True, exist_ok=True)
        for p in (self.home / "config.spec", self.game / "config.spec"):
            p.write_text("")
        (self.game / "logs").mkdir(exist_ok=True)
        self.log = self.game / "logs" / "lsq.log"
        if self.log.exists():
            self.log.unlink()
        # poll loop: serve requests, wait a frame, again
        (self.lsq / "poll.cfg").write_text("levelshotProbe lsq/req.txt\nwait 2\nexec lsq/poll.cfg\n")
        stage = "\n".join(after_load or []) + "\n"
        (self.lsq / "stage.cfg").write_text(stage + "exec lsq/poll.cfg\n")
        sets = {
            "fs_savepath": str(self.home), "fs_devpath": str(REPO / ".install"), "fs_game": "baseod3",
            "win_allowMultipleInstances": "1", "r_borderlessDefaultMigrated": "1", "r_fullscreen": "0",
            "r_windowWidth": str(width), "r_windowHeight": str(height), "r_renderApi": renderer,
            "com_skipLogoVideos": "1", "com_skipLoadingContinue": "1", "ui_retained": "0",
            "logFile": "2", "logFileName": "logs/lsq.log", "developer": "0", "si_gameType": "singleplayer",
            "com_maxfps": "60",
        }
        sets.update(PINS)
        sets.update(extra or {})
        args = [str(EXE)]
        for k, v in sets.items():
            args += ["+set", k, v]
        args += ["+devmap", mapname, "+waitMsec", str(wait_ms), "+exec", "lsq/stage.cfg"]
        env = dict(os.environ, ALSOFT_DRIVERS="null")
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = SHOW
        self.proc = subprocess.Popen(args, cwd=str(REPO / ".install"), env=env, startupinfo=si,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Minimized clients render black; park the window beyond the desktop instead.
        threading.Thread(target=self._park, daemon=True).start()

    def _park(self):
        end = time.time() + 120
        while time.time() < end and self.proc.poll() is None:
            park(self.proc.pid)
            time.sleep(0.25)

    def request(self, lines: list[str], timeout=180.0) -> bool:
        req = self.lsq / "req.txt"
        tmp = self.lsq / "req.tmp"
        tmp.write_text("\n".join(lines) + "\n")
        os.replace(tmp, req)
        t0 = time.time()
        while req.exists():
            if self.proc.poll() is not None:
                raise RuntimeError(f"client exited ({self.proc.returncode}); see {self.log}")
            if time.time() - t0 > timeout:
                return False
            time.sleep(0.1)
        return True

    def close(self):
        if self.proc.poll() is None:
            self.proc.kill()
            try:
                self.proc.wait(60)
            except subprocess.TimeoutExpired:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # outputs ---------------------------------------------------------------
    def out(self, rel: str) -> Path:
        return self.game / rel


def read_tga(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"))


def read_pose(path: Path) -> list[float]:
    return [float(x) for x in path.read_text().split()]


def read_depth(path: Path, w: int, h: int) -> np.ndarray:
    return np.fromfile(path, dtype="<f4").reshape(h, w)


def probe_line(out: str, w: int, h: int, cam, fov=90.0, depth=False) -> str:
    x, y, z, pitch, yaw, roll = cam
    return f"{out} {w} {h} {x:.3f} {y:.3f} {z:.3f} {pitch:.4f} {yaw:.4f} {roll:.4f} {fov:.4f}" + (" depth" if depth else "")


# Minimized clients draw nothing, so windows are moved beyond the desktop instead.

user32 = ctypes.windll.user32
EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
SWP_NOSIZE, SWP_NOZORDER, SWP_NOACTIVATE = 0x1, 0x4, 0x10
SM_XVIRTUALSCREEN, SM_CXVIRTUALSCREEN = 76, 78


def park(pid: int) -> int:
    x = user32.GetSystemMetrics(SM_XVIRTUALSCREEN) + user32.GetSystemMetrics(SM_CXVIRTUALSCREEN) + 200
    moved = []

    def cb(hwnd, _):
        p = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            user32.SetWindowPos(hwnd, 0, x, 0, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
            moved.append(hwnd)
        return True

    user32.EnumWindows(EnumProc(cb), 0)
    return len(moved)


def grab(pid: int):
    """PrintWindow the process's main window client area (renders even off-screen)."""
    from PIL import Image
    gdi32 = ctypes.windll.gdi32
    found = []

    def cb(hwnd, _):
        p = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    user32.EnumWindows(EnumProc(cb), 0)
    if not found:
        return None
    hwnd = found[0]
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w, h = rect.right, rect.bottom
    hdc = user32.GetDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    user32.PrintWindow(hwnd, mdc, 0x1 | 0x2)  # PW_CLIENTONLY | PW_RENDERFULLCONTENT
    buf = ctypes.create_string_buffer(w * h * 4)
    class BMI(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG), ("biYPelsPerMeter", wintypes.LONG),
                    ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]
    bmi = BMI(ctypes.sizeof(BMI), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mdc); user32.ReleaseDC(hwnd, hdc)
    return Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
