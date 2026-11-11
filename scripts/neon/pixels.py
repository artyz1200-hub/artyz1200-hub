"""RGBA pixel canvas, deterministic noise, dithering, glow and a PNG encoder.

Standard library only, so the generator runs unchanged on GitHub Actions.
Colours are (r, g, b) tuples; canvases store (r, g, b, a) or None (clear).
"""
from __future__ import annotations

import base64
import math
import struct
import zlib

BAYER4 = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def hexc(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def mix(a, b, t: float):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def add(a, b, t: float):
    """Additive light: brighten ``a`` by ``b`` scaled by ``t``."""
    return tuple(min(255, round(a[i] + b[i] * t)) for i in range(3))


def bayer(x: int, y: int) -> float:
    return (BAYER4[y & 3][x & 3] + 0.5) / 16


def hash01(x: int, y: int = 0, seed: int = 0) -> float:
    h = (x * 374761393 + y * 668265263 + seed * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 0x1000000


def _smooth(t: float) -> float:
    return t * t * (3 - 2 * t)


def noise1(x: float, seed: int = 0) -> float:
    i = math.floor(x)
    f = _smooth(x - i)
    return hash01(i, 0, seed) * (1 - f) + hash01(i + 1, 0, seed) * f


def fbm1(x: float, seed: int = 0, octaves: int = 3) -> float:
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += noise1(x * (2 ** o), seed + o * 17) * amp
        norm += amp
        amp *= 0.5
    return total / norm


def ramp(colours, t: float, x: int, y: int):
    """Pick from a colour ramp at position t in [0, 1] with ordered dithering."""
    t = max(0.0, min(0.9999, t)) * (len(colours) - 1)
    i = int(t)
    frac = t - i
    return colours[min(i + 1, len(colours) - 1)] if frac > bayer(x, y) else colours[i]


class Canvas:
    def __init__(self, w: int, h: int, fill=None):
        self.w, self.h = w, h
        px = None if fill is None else (*fill[:3], 255)
        self.px = [[px] * w for _ in range(h)]

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def get(self, x: int, y: int):
        return self.px[y][x] if self.inside(x, y) else None

    def put(self, x: int, y: int, colour, alpha: int = 255) -> None:
        if colour is None or not self.inside(x, y):
            return
        self.px[y][x] = (colour[0], colour[1], colour[2],
                         colour[3] if len(colour) == 4 else alpha)

    def tint(self, x: int, y: int, colour, t: float) -> None:
        cur = self.get(x, y)
        if cur is not None:
            self.px[y][x] = (*mix(cur, colour, t), cur[3])

    def light(self, x: int, y: int, colour, t: float) -> None:
        cur = self.get(x, y)
        if cur is not None and t > 0:
            self.px[y][x] = (*add(cur, colour, t), cur[3])

    def rect(self, x: int, y: int, w: int, h: int, colour) -> None:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, colour)

    def hline(self, x0: int, x1: int, y: int, colour) -> None:
        for x in range(x0, x1 + 1):
            self.put(x, y, colour)

    def vline(self, x: int, y0: int, y1: int, colour) -> None:
        for y in range(y0, y1 + 1):
            self.put(x, y, colour)

    def blit(self, art, x: int, y: int, flip: bool = False) -> None:
        for sy, row in enumerate(art):
            n = len(row)
            for sx, colour in enumerate(row):
                if colour is not None:
                    self.put(x + (n - 1 - sx if flip else sx), y + sy, colour)

    def glow(self, cx: float, cy: float, radius: float, colour, strength: float,
             squash: float = 1.0) -> None:
        """Soft additive halo, quantised with ordered dithering so it stays pixel-art."""
        r = int(radius) + 1
        for y in range(int(cy) - r, int(cy) + r + 1):
            for x in range(int(cx) - r, int(cx) + r + 1):
                d = math.hypot(x - cx, (y - cy) / squash) / radius
                if d >= 1:
                    continue
                t = (1 - d) ** 2 * strength
                t = math.floor(t * 6 + bayer(x, y)) / 6     # banded, dithered falloff
                self.light(x, y, colour, t)

    # -- encoding ----------------------------------------------------------
    def to_png(self) -> bytes:
        opaque = all(p is not None and p[3] == 255 for row in self.px for p in row)
        raw = bytearray()
        for row in self.px:
            raw.append(0)
            for p in row:
                if p is None:
                    p = (0, 0, 0, 0)
                raw.extend(p[:3] if opaque else p)

        def chunk(tag: bytes, data: bytes) -> bytes:
            body = tag + data
            return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

        header = struct.pack(">IIBBBBB", self.w, self.h, 8, 2 if opaque else 6, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))

    def data_uri(self) -> str:
        return "data:image/png;base64," + base64.b64encode(self.to_png()).decode()

    def scaled_png(self, k: int) -> bytes:
        """Nearest-neighbour upscale, used only for local previews."""
        big = Canvas(self.w * k, self.h * k)
        for y in range(big.h):
            src = self.px[y // k]
            big.px[y] = [src[x // k] for x in range(big.w)]
        return big.to_png()


def sprite(art: str, palette: dict) -> list[list]:
    rows = art.strip("\n").splitlines()
    width = max(len(r) for r in rows)
    return [[palette.get(ch) if ch not in ". " else None for ch in r.ljust(width)] for r in rows]
