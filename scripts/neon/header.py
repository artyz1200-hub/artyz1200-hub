"""Profile header: a neon title and the animated Seoul skyline over the Han river."""
from __future__ import annotations

from . import scene
from .font import draw_text, text_width, title_strokes
from .pixels import Canvas, hash01, hexc, mix, sprite
from .scene import NEON, P, W
from .svgkit import cycle, discrete, flicker, img, linear, neon, svg, tubes_off, wrap

PREVIEW: dict[str, Canvas] = {}      # filled for local PNG previews


def _rain_layers(w: int, h: int, seed: int, heavy: bool = True) -> str:
    out = []
    layers = ((260, 4, (150, 170, 255), 70, 0.9, "far"), (90, 7, (200, 215, 255), 110, 0.55, "near"))
    for count, length, colour, alpha, dur, tag in layers:
        if not heavy:
            count //= 2
        r = scene.rain(w, h, count, length, colour, alpha, seed + len(tag))
        rid = f"rain-{tag}-{seed}"
        out.append(f'<defs>{img(r, 0, 0, f" id=\"{rid}\"")}</defs>'
                   f'<g>{linear("transform", (f"0 {-h}", "0 0"), (0, 1), dur, "translate")}'
                   f'<use href="#{rid}" y="0"/><use href="#{rid}" y="{h}"/></g>')
    return "".join(out)


def _beacon(x: int, y: int, dur: float, begin: float, colour: str = "#ff3048") -> str:
    return wrap(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{colour}"/>',
                discrete("opacity", (1, 0.15), (0, 0.5), dur, f' begin="{begin}s"'))


# --- title -----------------------------------------------------------------------
TITLE_H = 64


def title_svg(text: str = "Hi, I'm Artur") -> str:
    c = Canvas(W, TITLE_H, fill=(0, 0, 0))
    scene.sky(c, horizon=TITLE_H + 40, top=0.15, stars=60, seed=5)
    scene.far_city(c, TITLE_H, seed=41)
    scene.haze(c, 30, TITLE_H, 0.35)

    first = " ".join(text.split(" ")[:-1]) + " "
    glyphs, adv = title_strokes(text)
    s = 3
    ox = (W - adv * s) // 2
    oy = 14
    split = len(first)
    solid_a, solid_b = set(), set()
    for i, cells in enumerate(glyphs):
        for gx, gy in cells:
            for dx in range(s):
                for dy in range(s):
                    (solid_a if i < split else solid_b).add((ox + gx * s + dx, oy + gy * s + dy))
    # underline tube under the name with a gap, like a broken neon bar
    bx0 = min(x for x, _ in solid_b) if solid_b else ox
    bx1 = max(x for x, _ in solid_b) if solid_b else ox
    bar = {(x, oy + 7 * s + 3) for x in range(bx0, bx1 + 1) if not 14 < x - bx0 < 18}

    tubes_off(c, solid_a, P["cyan"])
    tubes_off(c, solid_b | bar, P["pink"])

    # flanking vertical Hangul signs: 서울 on the left, 아르투르 (Artur) on the right
    left = scene.vertical_sign(16, 6, "서울", P["violet"])
    right = scene.vertical_sign(W - 16 - 15, 6, "아르투르", P["yellow"])
    for sg in (left, right):
        c.vline(sg.x + sg.w // 2, 0, sg.y - 1, P["near_hi"])
        sg.paint_panel(c)

    lit_a = neon(W, TITLE_H, solid_a, P["cyan"], radius=7, strength=0.7)
    lit_b = neon(W, TITLE_H, solid_b | bar, P["pink"], radius=8, strength=0.8)
    signs = [(sg, neon(sg.w + 12, sg.h + 12, {(x + 6, y + 6) for x, y in sg.tubes},
                       sg.colour, radius=5, strength=0.6, core_mix=0.6)) for sg in (left, right)]

    # power-on: stutter, settle; the name flickers again late in the loop
    dur = 10.0
    on_a = discrete("opacity", (0, 1, 0, 1, 0.3, 1), (0, .06, .1, .16, .2, .26), dur)
    on_b = discrete("opacity", (0, 1, 0, 0.4, 1, 0.2, 1), (0, .14, .18, .24, .3, .86, .875), dur)

    preview = Canvas(W, TITLE_H)
    preview.px = [row[:] for row in c.px]
    for lit in (lit_a, lit_b):
        scene.composite(preview, lit)
    for sg, lit in signs:
        scene.composite(preview, lit, sg.x - 6, sg.y - 6)
    PREVIEW["title"] = preview

    return svg(W, TITLE_H, text, [
        img(c),
        wrap(img(lit_a), on_a),
        wrap(img(lit_b), on_b),
        wrap(img(signs[0][1], left.x - 6, left.y - 6), flicker(7.3, 0.3)),
        wrap(img(signs[1][1], right.x - 6, right.y - 6), flicker(9.1, 0.7, dips=3)),
        _rain_layers(W, TITLE_H, 3, heavy=False),
    ])


# --- skyline ---------------------------------------------------------------------
SKY_H = 200
BASE = 138        # where the buildings stand
WATER = 141       # first row of river
DECK = 125        # bridge deck top


def _billboard_frames(w: int, h: int) -> list[Canvas]:
    words = (("LLM", "cyan"), ("RAG", "pink"), ("MULTI-AGENT", "yellow"),
             ("PYTORCH", "pink"), ("DATA SCIENCE", "cyan"))
    frames = []
    for i, (word, col) in enumerate(words):
        f = Canvas(w, h, fill=hexc("#05121c"))
        for y in range(0, h, 2):
            f.hline(0, w - 1, y, hexc("#081a27"))
        tone = NEON[col]
        tx = (w - text_width(word)) // 2
        draw_text(f, tx, h // 2 - 4, word, mix(tone, (255, 255, 255), 0.35), shadow=mix(tone, (0, 0, 0), 0.6))
        # tiny equaliser bars along the bottom
        for k in range(2, w - 2, 2):
            bh = 1 + int(hash01(k, i, 9) * 3)
            f.vline(k, h - 1 - bh, h - 2, mix(tone, (0, 0, 0), 0.45))
        f.hline(0, w - 1, 0, tone)
        frames.append(f)
    return frames


TRAIN = sprite("""
.hhhhhhhhhhhhhhhhhhhhh.hhhhhhhhhhhhhhhhhhhhh.hhhhhhhhhhhhhhhhhhhhh.hhhhhhhhhhhhhhhhhhhhhh.
hbbbbbbbbbbbbbbbbbbbbbhbbbbbbbbbbbbbbbbbbbbbhbbbbbbbbbbbbbbbbbbbbbhbbbbbbbbbbbbbbbbbbbbbbbh
bwwbwwbwwbwwbwwbwwbwwbbwwbwwbwwbwwbwwbwwbwwbbwwbwwbwwbwwbwwbwwbwwbbwwbwwbwwbwwbwwbwwbwwbcc
bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbc
ppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp
.kk...kk...........kk...kk...........kk...kk...........kk...kk...........kk...kk.........
""", {"h": hexc("#3b2a5e"), "b": hexc("#1d1430"), "w": hexc("#ffe7b0"), "c": hexc("#e8f8ff"),
      "p": hexc("#ff2e88"), "k": hexc("#07040f")})

CAR = sprite("""
...cccc....
..cwwwwc...
rbbbbbbbbbh
.bbbbbbbbb.
..u.....u..
""", {"c": hexc("#2c1d4a"), "w": hexc("#7ff6ff"), "b": hexc("#1a1030"), "r": hexc("#ff2e88"),
      "h": hexc("#ffffff"), "u": hexc("#00e5ff")})


def _skyline() -> tuple[Canvas, list, dict, list]:
    c = Canvas(W, SKY_H, fill=(0, 0, 0))
    scene.sky(c, horizon=BASE)
    scene.moon(c, 330, 40, 13)
    scene.ridge(c, 112, 16, 38, P["ridge"], 3)
    beacons = []
    beacons.append(scene.namsan(c, 150, 86, BASE))
    scene.far_city(c, BASE)
    beacons.append(scene.lotte(c, 418, 16, BASE))
    scene.haze(c, 96, BASE, 0.32)

    mids = [(26, 28, 68, P["mid_rim"]), (58, 18, 94, None), (80, 32, 82, P["mid_rim2"]),
            (116, 16, 100, None), (196, 24, 74, P["mid_rim2"]), (224, 34, 88, P["mid_rim"]),
            (262, 18, 102, None), (282, 50, 56, P["mid_rim2"]), (336, 18, 96, None),
            (356, 26, 70, P["mid_rim"]), (386, 14, 106, None), (434, 28, 84, P["mid_rim"]),
            (464, 20, 98, None)]
    for i, (x, w, top, rim) in enumerate(mids):
        scene.building(c, x, w, top, BASE, 100 + i, rim=rim)

    signs = [
        scene.vertical_sign(54, 72, "서울", P["pink"]),
        scene.vertical_sign(184, 80, "데이터", P["cyan"]),
        scene.vertical_sign(382, 76, "코딩", P["violet"]),
        scene.horizontal_sign(85, 71, "NLP", P["cyan"]),
        scene.horizontal_sign(229, 77, "RAG", P["yellow"]),
        scene.horizontal_sign(437, 73, "AI", P["pink"]),
        scene.horizontal_sign(286, 92, "PYTHON", P["yellow"]),
    ]
    for sg in signs:
        if sg.x < 382 or sg.y > 80:
            c.vline(sg.x + 2, sg.y - 3, sg.y - 1, P["mid_hi"])
            c.vline(sg.x + sg.w - 3, sg.y - 3, sg.y - 1, P["mid_hi"])
        sg.paint_panel(c)

    # billboard frame on the tall block
    bb = {"x": 287, "y": 62, "w": 40, "h": 18}
    c.rect(bb["x"] - 2, bb["y"] - 2, bb["w"] + 4, bb["h"] + 4, P["near_hi"])
    c.glow(bb["x"] + bb["w"] / 2, bb["y"] + bb["h"] / 2, 34, P["cyan"], 0.18, squash=0.6)

    # dark foreground towers framing the view
    scene.near_block(c, -2, 22, 34, BASE, 7)
    scene.near_block(c, 460, 22, 44, BASE, 8)
    for x, y in ((9, 31), (470, 41)):
        c.vline(x, y - 8, y, P["near_hi"])
        beacons.append((x, y - 9))

    # embankment expressway
    c.rect(0, BASE - 1, W, WATER - BASE + 1, hexc("#0a0616"))
    c.hline(0, W - 1, BASE - 1, hexc("#2a1840"))
    for x in range(0, W, 9):
        c.put(x, BASE, hexc("#ffcf7a"))

    # bridge: deck, railing lights, pylons
    c.hline(0, W - 1, DECK, P["deck"])
    for y in range(DECK + 1, DECK + 4):
        c.hline(0, W - 1, y, P["deck_face"])
    c.hline(0, W - 1, DECK + 4, P["deck_under"])
    for x in range(2, W, 6):
        c.put(x, DECK - 1, P["pink"] if (x // 6) % 2 else P["cyan"])
        c.put(x, DECK + 2, hexc("#3b2a5e"))
    for x in range(18, W, 52):
        c.rect(x, DECK + 5, 4, WATER - DECK - 5, P["pylon"])
        c.vline(x, DECK + 5, WATER - 1, hexc("#1d1236"))
    return c, signs, bb, beacons


def _fountain_frames(n: int = 3) -> list[Canvas]:
    """Banpo Bridge's moonlight rainbow fountain, falling from the deck."""
    rainbow = [hexc(h) for h in ("#ff2e88", "#ff8a3d", "#ffd23f", "#4dff9a", "#00e5ff", "#7a5cff", "#d24dff")]
    frames = []
    h = WATER - (DECK + 5) + 3
    for f in range(n):
        c = Canvas(W, h)
        for x in range(150, 330):
            if x % 2:
                continue
            col = rainbow[(x // 9) % len(rainbow)]
            for y in range(h):
                drop = (y + f * 2 + int(hash01(x, 0, 3) * 6)) % 6
                if drop < 3:
                    c.put(x + (y // 5), y, (*col, 200 if y < h - 3 else 120))
        frames.append(c)
    return frames


def skyline_svg() -> str:
    base, signs, bb, beacons = _skyline()
    lit = [(sg, neon(sg.w + 12, sg.h + 12, {(x + 6, y + 6) for x, y in sg.tubes}, sg.colour,
                     radius=5, strength=0.6, core_mix=0.6)) for sg in signs]
    boards = _billboard_frames(bb["w"], bb["h"])
    fountain = _fountain_frames()

    # reflections are taken from the lit city
    litc = Canvas(W, WATER)
    litc.px = [row[:] for row in base.px[:WATER]]
    for sg, l in lit:
        scene.composite(litc, l, sg.x - 6, sg.y - 6)
    for y in range(bb["h"]):
        for x in range(bb["w"]):
            litc.put(bb["x"] + x, bb["y"] + y, boards[0].px[y][x])
    water = [scene.reflection(litc, WATER, f, 3, SKY_H - WATER) for f in range(3)]

    preview = Canvas(W, SKY_H)
    preview.px = [row[:] for row in litc.px] + [row[:] for row in water[0].px]
    scene.composite(preview, fountain[0], 0, DECK + 5)
    PREVIEW["skyline"] = preview

    body = [img(base), cycle(water, 1.2, 0, WATER)]
    body.append(cycle(fountain, 0.45, 0, DECK + 5))
    for i, (sg, l) in enumerate(lit):
        el = img(l, sg.x - 6, sg.y - 6)
        if i in (1, 4, 6):
            body.append(wrap(el, flicker(5.5 + i * 1.7, hash01(i, 0, 4), dips=2 + i % 2)))
        else:
            body.append(el)
    # billboard cycles through what I work on
    n = len(boards)
    keys = [k / n for k in range(n)]
    body.append("".join(
        wrap(img(f, bb["x"], bb["y"], f' opacity="{1 if k == 0 else 0}"'),
             discrete("opacity", ["1" if j == k else "0" for j in range(n)], keys, 12.5))
        for k, f in enumerate(boards)))
    body.append(wrap(f'<rect x="{bb["x"]}" y="{bb["y"]}" width="{bb["w"]}" height="1" '
                     f'fill="#bffcff" opacity="0.5"/>',
                     linear("y", (str(bb["y"]), str(bb["y"] + bb["h"] - 1)), (0, 1), 2.2)))

    for i, (x, y) in enumerate(beacons):
        body.append(_beacon(x, y, 1.6 + i * 0.3, i * 0.4))

    # traffic on the expressway: tail lights drift left, headlights right
    for i in range(10):
        right = i % 2 == 0
        dur = 7 + hash01(i, 1, 2) * 6
        col = "#fff4d6" if right else "#ff3048"
        y = BASE + (1 if right else 2)
        vals = ("-6", str(W + 6)) if right else (str(W + 6), "-6")
        body.append(wrap(f'<rect x="0" y="{y}" width="2" height="1" fill="{col}"/>',
                         linear("x", vals, (0, 1), round(dur, 2), extra=f' begin="-{hash01(i, 2, 2) * dur:.2f}s"')))

    # the train crossing the bridge, and its reflection
    train = Canvas(len(TRAIN[0]), len(TRAIN))
    train.blit(TRAIN, 0, 0)
    tw = train.w
    loop = 14.0
    move = ("{} 0".format(W + 4), "{} 0".format(-tw - 4), "{} 0".format(-tw - 4))
    body.append(f'<g>{linear("transform", move, (0, 0.55, 1), loop, "translate")}'
                f'{img(train, 0, DECK - train.h)}</g>')
    refl = Canvas(train.w, train.h)
    refl.blit(TRAIN[::-1], 0, 0)
    body.append(f'<g opacity="0.28">{linear("transform", move, (0, 0.55, 1), loop, "translate")}'
                f'{img(refl, 0, 2 * WATER - DECK + 6)}</g>')

    # a hover car crossing the sky
    car = Canvas(len(CAR[0]), len(CAR))
    car.blit(CAR, 0, 0)
    body.append(f'<g>{linear("transform", (f"{W + 10} 58", "-20 50", "-20 50"), (0, 0.6, 1), 16, "translate")}'
                f'{img(car)}<rect x="-14" y="2" width="14" height="1" fill="#ff2e88" opacity="0.35"/></g>')
    body.append(f'<g>{linear("transform", ("-20 104", f"{W + 10} 98", f"{W + 10} 98"), (0, 0.5, 1), 21, "translate", extra=" begin=\"-6s\"")}'
                f'<g transform="scale(-1 1) translate(-11 0)">{img(car)}</g></g>')

    body.append(_rain_layers(W, SKY_H, 9))
    return svg(W, SKY_H, "Pixel-art neon Seoul at night: N Seoul Tower, a rainy skyline, "
               "a train crossing a bridge over the Han river", body)

