# Copyright (C) 2026 DarkMatter Productions. GPL-3.0-or-later.
"""Compose sets the way the engine does (Session_PrepareExpandedLoadingBackground) for review.

python review_levelshots.py <tiles dir> <out dir> [shot ...]
Writes <shot>_review.png: retail | new centre (4:3), the 21:9 composition, and the 9:16 one.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import levelshot_match as geom


def compose(tiles: Path, shot: str, aspect: float, height=1024):
    c = Image.open(tiles / f"{shot}.jpg").convert("RGB")
    cw = round(c.height * 4 / 3)
    center = c.resize((cw, c.height), Image.LANCZOS)
    if aspect >= 4 / 3:
        ow = round(aspect * c.height)
        out = Image.new("RGB", (ow, c.height))
        cx = (ow - cw) // 2
        out.paste(center, (cx, 0))
        side = cx
        right = ow - cx - cw
        L = Image.open(tiles / f"{shot}_left.jpg").convert("RGB")
        R = Image.open(tiles / f"{shot}_right.jpg").convert("RGB")
        crop = round(L.width * side / cw)
        out.paste(L.crop((L.width - crop, 0, L.width, L.height)).resize((side, c.height), Image.LANCZOS), (0, 0))
        crop = round(R.width * right / cw)
        out.paste(R.crop((0, 0, crop, R.height)).resize((right, c.height), Image.LANCZOS), (cx + cw, 0))
    else:
        oh = round(cw / aspect)
        out = Image.new("RGB", (cw, oh))
        cy = (oh - c.height) // 2
        out.paste(center, (0, cy))
        bottom = oh - cy - c.height
        T = Image.open(tiles / f"{shot}_top.jpg").convert("RGB")
        B = Image.open(tiles / f"{shot}_bottom.jpg").convert("RGB")
        crop = round(T.height * cy / c.height)
        out.paste(T.crop((0, T.height - crop, T.width, T.height)).resize((cw, cy), Image.LANCZOS), (0, 0))
        crop = round(B.height * bottom / c.height)
        out.paste(B.crop((0, 0, B.width, crop)).resize((cw, bottom), Image.LANCZOS), (0, cy + c.height))
    return out


def review(tiles: Path, out: Path, shot: str):
    retail = Image.fromarray(geom.retail_shot(shot)).resize((480, 360))
    new = Image.open(tiles / f"{shot}.jpg").convert("RGB").resize((480, 360), Image.LANCZOS)
    wide = compose(tiles, shot, 21 / 9).resize((840, 360), Image.LANCZOS)
    tall = compose(tiles, shot, 9 / 16)
    tall = tall.resize((round(tall.width * 720 / tall.height), 720), Image.LANCZOS)
    W = max(480 * 2 + 10, 840) + tall.width + 10
    sheet = Image.new("RGB", (W, 730), (40, 40, 40))
    sheet.paste(retail, (0, 0))
    sheet.paste(new, (490, 0))
    sheet.paste(wide, (0, 370))
    sheet.paste(tall, (W - tall.width, 0))
    d = ImageDraw.Draw(sheet)
    for xy, t in (((4, 4), "retail"), ((494, 4), "openD3 centre"), ((4, 374), "21:9"), ((W - tall.width + 4, 4), "9:16")):
        d.text(xy, f"{shot}  {t}", fill=(255, 255, 0))
    out.mkdir(parents=True, exist_ok=True)
    sheet.save(out / f"{shot}_review.png")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    tiles, out = Path(sys.argv[1]), Path(sys.argv[2])
    shots = sys.argv[3:] or sorted({p.stem.split("_")[0] for p in tiles.glob("*.jpg")})
    for s in shots:
        review(tiles, out, s)
        print(s)
