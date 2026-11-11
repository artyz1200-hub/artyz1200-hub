"""SVG helpers: crisp pixel images, SMIL animation snippets and neon tubes."""
from __future__ import annotations

import math
from html import escape

from .pixels import Canvas, bayer, mix

SCALE = 2.5
PIXEL_STYLE = ('<style>.px{image-rendering:optimizeSpeed;image-rendering:-moz-crisp-edges;'
               'image-rendering:-webkit-optimize-contrast;image-rendering:crisp-edges;'
               'image-rendering:pixelated}</style>')


def svg(w: int, h: int, label: str, body: list[str]) -> str:
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{int(w * SCALE)}" height="{int(h * SCALE)}" shape-rendering="crispEdges" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>',
        PIXEL_STYLE, *body, "</svg>"])


def img(canvas: Canvas, x: float = 0, y: float = 0, extra: str = "") -> str:
    return (f'<image class="px" x="{x}" y="{y}" width="{canvas.w}" height="{canvas.h}" '
            f'href="{canvas.data_uri()}"{extra}/>')


def wrap(element: str, *animations: str) -> str:
    """Put SMIL animation elements inside a self-closing element."""
    tag = element[1:element.index(" ")]
    return element[:-2] + ">" + "".join(animations) + f"</{tag}>"


def _keys(keys) -> str:
    return ";".join(f"{k:.4f}" for k in keys)


def discrete(attr: str, values, keys, dur: float, extra: str = "") -> str:
    return (f'<animate attributeName="{attr}" values="{";".join(str(v) for v in values)}" '
            f'keyTimes="{_keys(keys)}" calcMode="discrete" dur="{dur}s" '
            f'repeatCount="indefinite"{extra}/>')


def linear(attr: str, values, keys, dur: float, kind: str = "", extra: str = "") -> str:
    tag = "animateTransform" if kind else "animate"
    type_ = f' type="{kind}"' if kind else ""
    return (f'<{tag} attributeName="{attr}"{type_} values="{";".join(values)}" '
            f'keyTimes="{_keys(keys)}" dur="{dur}s" repeatCount="indefinite"{extra}/>')


def flicker(dur: float, seed: float, dips: int = 2) -> str:
    """Mostly on, with a short stutter of off-frames at a seeded moment."""
    start = 0.15 + (seed % 1) * 0.6
    vals, keys = [1], [0.0]
    t = start
    for _ in range(dips):
        vals += [0.15, 1]
        keys += [t, t + 0.012]
        t += 0.03
    return discrete("opacity", vals, keys, dur)


def cycle(frames: list[Canvas], dur: float, dx: int = 0, dy: int = 0) -> str:
    """Flip-book of frames; the first one shows when SMIL is off."""
    n = len(frames)
    keys = [i / n for i in range(n)]
    return "".join(
        wrap(img(f, dx, dy, f' opacity="{1 if i == 0 else 0}"'),
             discrete("opacity", ["1" if j == i else "0" for j in range(n)], keys, dur))
        for i, f in enumerate(frames))


# --- neon tubes ------------------------------------------------------------------
WHITE = (255, 255, 255)


def neon(w: int, h: int, solid: set, colour, radius: float = 6, strength: float = 0.75,
         core_mix: float = 0.75) -> Canvas:
    """Lit neon: transparent canvas with a dithered halo and bright tubes."""
    c = Canvas(w, h)
    best: dict = {}
    r = int(radius)
    for (sx, sy) in solid:
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                d = math.hypot(dx, dy)
                if d < radius:
                    k = (sx + dx, sy + dy)
                    if d < best.get(k, 99):
                        best[k] = d
    for (x, y), d in best.items():
        if (x, y) in solid or not c.inside(x, y):
            continue
        a = (1 - d / radius) ** 2 * strength
        a = math.floor(a * 7 + bayer(x, y)) / 7
        if a > 0:
            c.put(x, y, (*colour, int(a * 255)))
    core = mix(colour, WHITE, core_mix)
    for (x, y) in solid:
        inner = all((x + dx, y + dy) in solid for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        c.put(x, y, core if inner else mix(colour, WHITE, 0.25))
    return c


def tubes_off(c: Canvas, solid: set, colour) -> None:
    """Unlit glass tubes painted into an opaque canvas."""
    dark = mix(colour, (8, 4, 16), 0.72)
    for (x, y) in solid:
        c.put(x, y, dark)
