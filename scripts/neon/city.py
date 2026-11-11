"""The contribution calendar as the lit windows of a neon megablock.

Every day of the last year is one window. Contribution level sets the light,
from dark glass (0) through violet and pink to a white-hot cyan (4). The block
stands on a rain-soaked street that mirrors it, under a header of neon signs
that show the yearly total and streaks.
"""
from __future__ import annotations

from datetime import date, timedelta

from . import scene
from .font import draw_text, text_width
from .header import CAR, _beacon, _rain_layers
from .pixels import Canvas, hash01, hexc, mix
from .scene import P, W
from .svgkit import discrete, img, linear, neon, svg, wrap

H = 160
PITCH, CELL = 8, 7
GY = 34                 # top of the first window row
STREET = 104            # first row of wet asphalt

LEVEL = {
    0: ("#140c26", "#1d1336", "#0e081b"),
    1: ("#3b1d72", "#55309a", "#2c1556"),
    2: ("#8a2fd6", "#b05cf0", "#6a22a8"),
    3: ("#ff2e88", "#ff8cc2", "#c41f66"),
    4: ("#00e5ff", "#e6fdff", "#00a7c2"),
}
LEVEL = {k: tuple(hexc(c) for c in v) for k, v in LEVEL.items()}
PREVIEW: dict[str, Canvas] = {}


def arrange(days: list[dict]) -> list:
    """Pad days into Sunday-first columns (None = outside the range)."""
    first = (date.fromisoformat(days[0]["date"]).weekday() + 1) % 7
    cells = [None] * first + list(days)
    while len(cells) % 7:
        cells.append(None)
    return cells


def streaks(days: list[dict]) -> tuple[int, int]:
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    current = 0
    tail = list(days)
    if tail and tail[-1]["count"] == 0:       # today may still be young
        tail = tail[:-1]
    for d in reversed(tail):
        if d["count"] == 0:
            break
        current += 1
    return current, longest


def _window(c: Canvas, x: int, y: int, level: int, seed: int) -> None:
    base, hi, lo = LEVEL[level]
    c.rect(x, y, CELL, CELL, base)
    if level == 0:
        c.hline(x, x + CELL - 1, y, hi)
        if hash01(x, y, seed) < 0.25:                    # a passing reflection
            c.put(x + 1, y + 2, hi)
            c.put(x + 2, y + 1, hi)
        return
    c.hline(x, x + CELL - 1, y + CELL - 1, lo)
    c.vline(x + CELL - 1, y, y + CELL - 1, lo)
    c.rect(x + 2, y + 2, 3, 3, hi)
    c.put(x + 1, y + 1, hi)
    if level >= 3:
        c.rect(x + 1, y + 1, 5, 5, mix(base, hi, 0.55))
        c.rect(x + 2, y + 2, 3, 3, hi)


def build(days: list[dict], total: int) -> tuple[str, Canvas]:
    cells = arrange(days)
    weeks = len(cells) // 7
    grid_w = weeks * PITCH - 1
    gx = (W - grid_w) // 2 + 6

    c = Canvas(W, H, fill=(0, 0, 0))
    scene.sky(c, horizon=STREET, top=0.1, stars=50, seed=21)
    scene.far_city(c, STREET - 1, seed=23)
    scene.haze(c, 60, STREET, 0.3)

    # the megablock facade
    fx0, fx1, fy0, fy1 = gx - 5, gx + grid_w + 4, GY - 12, GY + 7 * PITCH + 3
    c.rect(fx0, fy0, fx1 - fx0 + 1, STREET - fy0, P["mid"])
    c.hline(fx0, fx1, fy0, P["mid_hi"])
    c.vline(fx0, fy0, STREET - 1, P["mid_rim"])
    c.vline(fx1, fy0, STREET - 1, P["mid_rim2"])
    for x in range(fx0 + 6, fx1 - 4, 12):                # roof clutter
        if hash01(x, 1, 3) < 0.35:
            c.rect(x, fy0 - 3, 4, 3, P["mid_hi"])
        elif hash01(x, 2, 3) < 0.25:
            c.vline(x, fy0 - 8, fy0 - 1, P["mid_hi"])
    c.rect(gx - 2, GY - 2, grid_w + 4, 7 * PITCH + 3, hexc("#07040e"))

    # month labels on the facade band above the windows
    last_label, last_month = -9, None
    for col in range(weeks):
        day = next((d for d in cells[col * 7:col * 7 + 7] if d), None)
        if day is None:
            continue
        m = date.fromisoformat(day["date"]).month
        if m != last_month and col - last_label >= 4 and col < weeks - 2:
            name = date(2000, m, 1).strftime("%b").upper()
            draw_text(c, gx + col * PITCH, GY - 9, name, hexc("#a89bd6"), hexc("#05030b"))
            last_label = col
        last_month = m
    for row, name in ((1, "MON"), (3, "WED"), (5, "FRI")):
        draw_text(c, fx0 - text_width(name) - 3, GY + row * PITCH + 1, name, hexc("#8a7cc0"), hexc("#05030b"))

    lit = []
    for i, d in enumerate(cells):
        col, row = divmod(i, 7)
        x, y = gx + col * PITCH, GY + row * PITCH
        if d is None:
            c.rect(x, y, CELL, CELL, hexc("#0a0616"))
            continue
        _window(c, x, y, d["level"], 5)
        if d["level"] >= 3:
            c.glow(x + 3, y + 3, 6 if d["level"] == 3 else 8, LEVEL[d["level"]][0], 0.22)
        if d["level"] > 0:
            lit.append((x, y, d["level"], i))
    # re-stamp windows so halos sit behind the glass
    for x, y, level, _ in lit:
        _window(c, x, y, level, 5)

    # legend
    ly = GY + 7 * PITCH + 7
    lx = fx1 - (5 * PITCH + text_width("LESS") + text_width("MORE") + 6)
    draw_text(c, lx, ly + 1, "LESS", hexc("#8a7cc0"))
    for k in range(5):
        _window(c, lx + text_width("LESS") + 3 + k * PITCH, ly, k, 1)
    draw_text(c, lx + text_width("LESS") + 4 + 5 * PITCH, ly + 1, "MORE", hexc("#8a7cc0"))
    draw_text(c, fx0 + 2, ly + 1, "LAST 12 MONTHS", hexc("#8a7cc0"))

    # neon header: total and streaks
    current, longest = streaks(days)
    specs = [(f"{total} CONTRIBUTIONS", P["pink"]), (f"STREAK {current}", P["cyan"]),
             (f"BEST {longest}", P["yellow"])]
    signs = []
    widths = [text_width(t) + 8 for t, _ in specs]
    gap = 10
    sx = (W - (sum(widths) + gap * (len(specs) - 1))) // 2
    for (text, colour), w in zip(specs, widths):
        sg = scene.horizontal_sign(sx, 4, text, colour)
        c.vline(sg.x + 3, sg.y + sg.h, fy0 - 1, P["near_hi"])
        c.vline(sg.x + sg.w - 4, sg.y + sg.h, fy0 - 1, P["near_hi"])
        sg.paint_panel(c)
        signs.append(sg)
        sx += w + gap

    # street
    c.rect(0, STREET - 1, W, 1, hexc("#2a1840"))
    lit_signs = [(sg, neon(sg.w + 12, sg.h + 12, {(x + 6, y + 6) for x, y in sg.tubes},
                           sg.colour, radius=5, strength=0.6, core_mix=0.6)) for sg in signs]
    src = Canvas(W, STREET)
    src.px = [row[:] for row in c.px[:STREET]]
    for sg, l in lit_signs:
        scene.composite(src, l, sg.x - 6, sg.y - 6)
    street = [scene.reflection(src, STREET, f, 2, H - STREET, ripple=0.0) for f in range(2)]
    for s in street:
        for x in range(0, W, 23):                       # lane markings
            for k in range(8):
                s.tint(x + k, 22, hexc("#4a3a6a"), 0.6)

    preview = Canvas(W, H)
    preview.px = [row[:] for row in src.px] + [row[:] for row in street[0].px]

    body = [img(c), wrap(img(street[0], 0, STREET), discrete("opacity", (1, 0), (0, .5), 1.4)),
            wrap(img(street[1], 0, STREET, ' opacity="0"'), discrete("opacity", (0, 1), (0, .5), 1.4))]
    for i, (sg, l) in enumerate(lit_signs):
        el = img(l, sg.x - 6, sg.y - 6)
        if i == 0:
            el = wrap(el, discrete("opacity", (1, .2, 1, .3, 1), (0, .7, .71, .73, .74), 8.0))
        body.append(el)

    # a few windows blink off and on, like someone flicking the lights
    for j, (x, y, level, i) in enumerate(lit):
        if hash01(i, 0, 13) < 0.07:
            dur = 4 + hash01(i, 1, 13) * 7
            body.append(wrap(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="#140c26" opacity="0"/>',
                             discrete("opacity", (0, 0.85, 0), (0, 0.8, 0.86), round(dur, 2))))
    # today's window pulses
    if cells:
        last = max(i for i, d in enumerate(cells) if d)
        col, row = divmod(last, 7)
        x, y = gx + col * PITCH, GY + row * PITCH
        body.append(wrap(f'<rect x="{x - 1}" y="{y - 1}" width="{CELL + 2}" height="{CELL + 2}" fill="none" '
                         f'stroke="#ffffff" stroke-width="1" opacity="0"/>',
                         discrete("opacity", (0, 0.9, 0), (0, 0.4, 0.8), 1.6)))
    # a scan beam sweeps across the facade
    body.append(wrap(f'<rect x="{gx}" y="{GY - 1}" width="3" height="{7 * PITCH}" fill="#7ff6ff" opacity="0.18"/>',
                     linear("x", (str(gx - 4), str(gx + grid_w + 1), str(gx + grid_w + 1)), (0, 0.55, 1), 7.0)))
    # traffic on the street
    car = Canvas(len(CAR[0]), len(CAR))
    car.blit(CAR, 0, 0)
    body.append(f'<g>{linear("transform", (f"{W + 10} {STREET + 6}", f"-30 {STREET + 6}", f"-30 {STREET + 6}"), (0, 0.45, 1), 11, "translate")}'
                f'{img(car)}<rect x="11" y="2" width="16" height="1" fill="#ff2e88" opacity="0.3"/></g>')
    body.append(f'<g>{linear("transform", (f"-30 {STREET + 22}", f"{W + 10} {STREET + 22}", f"{W + 10} {STREET + 22}"), (0, 0.4, 1), 13, "translate", extra=" begin=\"-5s\"")}'
                f'<g transform="scale(-1 1) translate(-11 0)">{img(car)}</g></g>')
    body.append(_beacon(fx0 + 6, fy0 - 9, 1.8, 0.2))
    body.append(_beacon(fx1 - 6, fy0 - 9, 2.1, 0.9))
    body.append(_rain_layers(W, H, 17))

    PREVIEW["city"] = preview
    label = (f"Neon pixel-art city whose windows are my GitHub contributions: "
             f"{total} in the last year, current streak {current}, best {longest}")
    return svg(W, H, label, body), preview
