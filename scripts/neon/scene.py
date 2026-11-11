"""Neon Seoul at night: sky, Namsan with N Seoul Tower, the skyline, the Han river.

Everything here paints into opaque ``Canvas`` objects. ``header.py`` turns the
result into animated SVG layers.
"""
from __future__ import annotations

import math

from .font import HANGUL_H, hangul_bits, text_bits, text_width
from .pixels import Canvas, add, bayer, fbm1, hash01, hexc, mix, ramp

W = 480

P = {k: hexc(v) for k, v in {
    "sky0": "#04020a", "sky1": "#080414", "sky2": "#0f0722", "sky3": "#1a0b33",
    "sky4": "#2a0f45", "sky5": "#43145a", "sky6": "#651c66", "sky7": "#8a2a6c",
    "star": "#b9a8e8", "star_hi": "#f3eaff",
    "moon": "#ffe3f1", "moon_dim": "#f2b6d6", "moon_glow": "#ff4fa3",
    "ridge": "#1b0d31", "ridge_hi": "#2b1347",
    "hill": "#0f0820", "hill_rim": "#3a1752",
    "far": "#170c2b", "far_hi": "#22123b", "far_win": "#3d2b6e", "far_win2": "#6a3f8f",
    "mid": "#0d0719", "mid_hi": "#1d1035", "mid_rim": "#5b1f63", "mid_rim2": "#1f4a6b",
    "near": "#05030b", "near_hi": "#0d0818",
    "win_warm": "#ffbf6e", "win_warm2": "#e08a4a", "win_cyan": "#6ff3ff",
    "win_pink": "#ff6fb7", "win_white": "#e8e6ff", "win_dim": "#3a2a55",
    "haze": "#7a2a6e",
    "pink": "#ff2e88", "cyan": "#00e5ff", "violet": "#b44dff", "yellow": "#ffd23f",
    "red": "#ff3048", "panel": "#0a0614",
    "deck": "#2a1d45", "deck_face": "#140c26", "deck_under": "#07040f", "pylon": "#0e081c",
    "water": "#05030f", "water2": "#0a0620",
}.items()}

SKY = [P[f"sky{i}"] for i in range(8)]
NEON = {"pink": P["pink"], "cyan": P["cyan"], "violet": P["violet"], "yellow": P["yellow"]}


# --- sky ---------------------------------------------------------------------------
def sky(c: Canvas, horizon: int, top: float = 0.0, stars: int = 120, seed: int = 1) -> None:
    for y in range(c.h):
        t = top + (1 - top) * (y / max(1, horizon)) ** 1.6
        for x in range(c.w):
            c.put(x, y, ramp(SKY, t, x, y))
    # thin bands of smog lit from below
    for y in range(c.h):
        band = math.exp(-((y - horizon * 0.62) / (horizon * 0.09)) ** 2)
        if band < 0.05:
            continue
        for x in range(c.w):
            n = fbm1(x / 46 + y * 0.13, seed + 7)
            t = band * max(0, n - 0.42) * 1.6
            if t > bayer(x, y) * 0.9:
                c.tint(x, y, P["sky6"], min(0.55, t))
    for i in range(stars):
        x = int(hash01(i, 1, seed) * c.w)
        y = int(hash01(i, 2, seed) ** 1.7 * horizon * 0.55)
        c.put(x, y, P["star_hi"] if hash01(i, 3, seed) > 0.85 else P["star"])


def moon(c: Canvas, cx: int, cy: int, r: int) -> None:
    c.glow(cx, cy, r * 3.2, P["moon_glow"], 0.35)
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d = math.hypot(x - cx, y - cy)
            if d <= r:
                shade = (x - cx + y - cy) / (2 * r)
                col = P["moon"] if shade < 0.15 + bayer(x, y) * 0.3 else P["moon_dim"]
                # synth-wave cuts through the lower half
                if y > cy + 2 and (y - cy) % 4 in (0,) and (y - cy) > 1:
                    col = mix(col, P["sky4"], 0.85)
                c.put(x, y, col)


# --- landscape -----------------------------------------------------------------------
def ridge(c: Canvas, base: int, amp: int, scale: float, colour, seed: int) -> None:
    for x in range(c.w):
        top = base - int(fbm1(x / scale, seed) * amp)
        for y in range(top, c.h):
            c.put(x, y, colour)


def namsan(c: Canvas, cx: int = 150, peak: int = 86, bottom: int = 138) -> tuple[int, int]:
    """Namsan hill and N Seoul Tower. Returns the beacon position."""
    for x in range(c.w):
        d = (x - cx) / 105
        if abs(d) >= 1:
            continue
        top = int(peak + (bottom - peak) * (d * d) * (1.4 - 0.4 * abs(d)) + fbm1(x / 9, 31) * 3)
        for y in range(top, bottom + 1):
            c.put(x, y, P["hill"])
        c.put(x, top, P["hill_rim"])
    # tower: tapered base, shaft, observation pod, antenna
    for y in range(peak - 8, peak + 1):
        half = 1 + (y - (peak - 8)) // 4
        c.hline(cx - half, cx + half, y, P["mid_hi"])
    for y in range(peak - 36, peak - 8):
        c.put(cx, y, P["mid_hi"])
        c.put(cx + 1, y, P["mid"])
    pod = peak - 36
    for y, half in ((pod - 2, 2), (pod - 1, 4), (pod, 5), (pod + 1, 5), (pod + 2, 4), (pod + 3, 3)):
        c.hline(cx - half, cx + half + 1, y, P["mid_hi"])
    for x in range(cx - 4, cx + 6):
        c.put(x, pod, P["win_white"] if x % 2 == 0 else P["win_cyan"])
        c.put(x, pod + 1, P["win_pink"] if x % 3 == 0 else P["mid_hi"])
    c.glow(cx + 0.5, pod + 0.5, 12, P["pink"], 0.28, squash=0.6)
    for y in range(pod - 18, pod - 2):
        c.put(cx, y, P["win_white"] if y % 4 == 0 else P["mid_rim"])
    return cx, pod - 19


def far_city(c: Canvas, base: int, seed: int = 11) -> None:
    x = -3
    i = 0
    while x < c.w:
        w = 6 + int(hash01(i, 0, seed) * 14)
        h = 10 + int(hash01(i, 1, seed) ** 1.4 * 34)
        top = base - h
        c.rect(x, top, w, h + 1, P["far"])
        c.hline(x, x + w - 1, top, P["far_hi"])
        if hash01(i, 2, seed) > 0.6:                       # rooftop mast
            c.vline(x + w // 2, top - 4, top - 1, P["far_hi"])
        for wy in range(top + 2, base - 1, 2):
            for wx in range(x + 1, x + w - 1, 2):
                r = hash01(wx, wy, seed + 3)
                if r < 0.14:
                    c.put(wx, wy, P["far_win2"] if r < 0.03 else P["far_win"])
        x += w + (1 if hash01(i, 4, seed) > 0.7 else 0)
        i += 1


def haze(c: Canvas, y0: int, y1: int, strength: float) -> None:
    for y in range(y0, y1):
        t = ((y - y0) / max(1, y1 - y0)) ** 1.5 * strength
        for x in range(c.w):
            if t > bayer(x, y) * 0.5:
                c.tint(x, y, P["haze"], t)


def lotte(c: Canvas, cx: int, top: int, base: int) -> tuple[int, int]:
    """A slim tapering supertall with a lit crown. Returns the beacon position."""
    for y in range(top, base + 1):
        k = (y - top) / (base - top)
        half = 1 + int(10 * k ** 0.85)
        for x in range(cx - half, cx + half + 1):
            col = P["mid_hi"] if x < cx else P["far"]
            if x == cx - half:
                col = P["mid_rim"]
            c.put(x, y, col)
        if y % 3 == 0:
            for x in range(cx - half + 1, cx + half):
                if hash01(x, y, 77) < 0.22:
                    c.put(x, y, P["win_cyan"] if x < cx else P["far_win2"])
        c.put(cx, y, P["mid_rim2"])
    for y in range(top + 3, top + 13):                    # glowing crown slit
        c.put(cx, y, P["win_white"])
    c.glow(cx, top + 8, 8, P["cyan"], 0.3, squash=1.6)
    return cx, top - 2


def windows(c: Canvas, x: int, y: int, w: int, h: int, seed: int, density: float, pal) -> None:
    for wy in range(y + 3, y + h - 1, 3):
        if hash01(wy, 0, seed) < 0.18:
            continue                                       # a dark floor
        for wx in range(x + 2, x + w - 3, 3):
            r = hash01(wx, wy, seed)
            if r < density:
                col = pal[int(hash01(wx, wy, seed + 1) * len(pal))]
                c.put(wx, wy, col)
                c.put(wx + 1, wy, mix(col, P["mid"], 0.35))
            elif r < density + 0.1:
                c.put(wx, wy, P["win_dim"])


def building(c: Canvas, x: int, w: int, top: int, base: int, seed: int,
             rim=None, density: float = 0.32, pal=None) -> None:
    rim = rim or P["mid_rim"]
    c.rect(x, top, w, base - top + 1, P["mid"])
    c.hline(x, x + w - 1, top, P["mid_hi"])
    c.vline(x, top, base, rim)
    c.vline(x + w - 1, top + 1, base, P["near_hi"])
    pal = pal or (P["win_warm"], P["win_warm"], P["win_warm2"], P["win_cyan"], P["win_white"], P["win_pink"])
    windows(c, x, top, w, base - top, seed, density, pal)
    # rooftop clutter
    r = hash01(seed, 9)
    if r < 0.4:
        c.rect(x + 2, top - 3, 4, 3, P["mid_hi"])
    elif r < 0.75:
        c.vline(x + w - 4, top - 7, top - 1, P["mid_hi"])
        c.hline(x + w - 6, x + w - 2, top - 5, P["mid_hi"])


def near_block(c: Canvas, x: int, w: int, top: int, base: int, seed: int) -> None:
    c.rect(x, top, w, base - top + 1, P["near"])
    c.hline(x, x + w - 1, top, P["near_hi"])
    for fy in range(top + 6, base - 4, 7):                 # fire escapes
        c.hline(x + 2, x + w - 3, fy, P["near_hi"])
        for k in range(x + 2, x + w - 2, 3):
            c.put(k, fy - 1, P["near_hi"])
    for fy in range(top + 3, base - 2, 7):
        for wx in range(x + 3, x + w - 3, 4):
            if hash01(wx, fy, seed) < 0.22:
                col = P["win_pink"] if hash01(wx, fy, seed + 1) < 0.4 else P["win_warm2"]
                c.put(wx, fy, col)
                c.put(wx + 1, fy, col)


# --- neon signs ---------------------------------------------------------------------
class Sign:
    """A sign is a dark panel and a set of tube pixels (relative to x, y)."""

    def __init__(self, x: int, y: int, w: int, h: int, tubes: set, colour, name: str):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.tubes, self.colour, self.name = tubes, colour, name

    def paint_panel(self, c: Canvas) -> None:
        c.rect(self.x, self.y, self.w, self.h, P["panel"])
        c.glow(self.x + self.w / 2, self.y + self.h / 2, max(self.w, self.h) * 0.9,
               self.colour, 0.16, squash=self.h / max(self.w, 1))
        dark = mix(self.colour, P["panel"], 0.72)
        for (tx, ty) in self.tubes:
            c.put(self.x + tx, self.y + ty, dark)


def _border(w: int, h: int) -> set:
    s = set()
    for x in range(1, w - 1):
        s |= {(x, 1), (x, h - 2)}
    for y in range(1, h - 1):
        s |= {(1, y), (w - 2, y)}
    return s


def vertical_sign(x: int, y: int, text: str, colour, pad: int = 2) -> Sign:
    w = 7 + 2 * (pad + 2)
    h = len(text) * (HANGUL_H + 2) + 2 * pad + 2
    tubes = _border(w, h)
    for i, ch in enumerate(text):
        for gx, gy in hangul_bits(ch):
            tubes.add((pad + 2 + gx, pad + 2 + i * (HANGUL_H + 2) + gy))
    return Sign(x, y, w, h, tubes, colour, text)


def horizontal_sign(x: int, y: int, text: str, colour, scale: int = 1) -> Sign:
    tw = text_width(text) * scale
    w, h = tw + 8, 5 * scale + 8
    tubes = _border(w, h)
    for gx, gy in text_bits(text):
        for sx in range(scale):
            for sy in range(scale):
                tubes.add((4 + gx * scale + sx, 4 + gy * scale + sy))
    return Sign(x, y, w, h, tubes, colour, text)


def composite(dst: Canvas, src: Canvas, x: int = 0, y: int = 0) -> None:
    """Alpha-composite a (partly transparent) canvas onto an opaque one."""
    for sy in range(src.h):
        for sx in range(src.w):
            p = src.px[sy][sx]
            if p is None or p[3] == 0:
                continue
            if p[3] == 255:
                dst.put(x + sx, y + sy, p)
            else:
                cur = dst.get(x + sx, y + sy)
                if cur is not None:
                    dst.px[y + sy][x + sx] = (*add(cur, p, p[3] / 255 * 0.85), 255)


# --- water -----------------------------------------------------------------------------
def reflection(src: Canvas, water: int, frame: int, frames: int, height: int,
               ripple: float = 1.0) -> Canvas:
    """The skyline mirrored in rippling, dark river water."""
    out = Canvas(src.w, height, fill=P["water"])
    phase = frame / frames * 2 * math.pi
    for d in range(height):
        sy = water - 1 - int(d * 0.9)
        if sy < 0:
            break
        amp = (0.6 + d / 14) * ripple
        fade = 0.3 + d / height * 0.45
        row_dark = hash01(d, frame, 5) < 0.12 + d / height * 0.2
        for x in range(src.w):
            dx = round(math.sin(d * 0.85 + phase + x * 0.035) * amp + (hash01(x // 7, d, frame) - 0.5) * ripple)
            p = src.get(min(src.w - 1, max(0, x + dx)), sy)
            if p is None:
                continue
            lum = (p[0] + p[1] + p[2]) / 765
            col = mix(p, P["water"], fade * (0.55 if lum > 0.45 else 1.0))
            col = mix(col, P["water2"], 0.25)
            if row_dark and lum < 0.5:
                col = mix(col, P["water"], 0.6)
            out.put(x, d, col)
    return out


def rain(w: int, h: int, count: int, length: int, colour, alpha: int, seed: int,
         slant: float = 0.0) -> Canvas:
    """Transparent, vertically tileable rain streaks."""
    c = Canvas(w, h)
    for i in range(count):
        x0 = hash01(i, 0, seed) * w
        y0 = int(hash01(i, 1, seed) * h)
        ln = length + int(hash01(i, 2, seed) * length * 0.6)
        for k in range(ln):
            a = int(alpha * (0.35 + 0.65 * k / ln))
            c.put(int(x0 + k * slant) % w, (y0 + k) % h, (*colour, a))
    return c
