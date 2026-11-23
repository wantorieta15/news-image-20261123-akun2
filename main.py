"""News-image 23 Nov 2026: one-page newspaper, 1024x1024, pure stdlib.

Renders "Monday 23 November 2026: 35 stories, 9 regions" and writes
entry.png into $MAKEFUN_OUTPUT_DIR. PNG encoder written by hand
(zlib + struct), 5x7 bitmap font drawn from scratch. No image library,
network, no clock, no randomness: fully deterministic.
"""

import binascii
import math
import os
import struct
import zlib

W = 1024
H = 1024

CREAM = (250, 244, 230)
PAPER = (255, 252, 244)
INK = (22, 22, 22)
RED = (178, 34, 34)
DARKRED = (140, 20, 20)
NAVY = (18, 52, 86)
BLUE = (30, 90, 160)
SKY = (135, 180, 220)
SEA = (24, 68, 110)
DARKSEA = (14, 42, 74)
WHITE = (255, 255, 255)
GREY = (120, 120, 120)
LGREY = (200, 200, 200)
ORANGE = (230, 120, 30)
YELLOW = (240, 200, 40)
GREEN = (30, 130, 70)
OCHRE = (190, 140, 30)
PURPLE = (110, 60, 160)
TEAL = (20, 140, 140)
BROWN = (140, 90, 50)
NIGHT = (16, 28, 52)
SMOKE = (90, 90, 100)

buf = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = c[0]
        buf[i + 1] = c[1]
        buf[i + 2] = c[2]


def fill(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            buf[i] = c[0]
            buf[i + 1] = c[1]
            buf[i + 2] = c[2]


def line(x0, y0, x1, y1, c, t=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        for a in range(t):
            for b in range(t):
                px(x0 + a, y0 + b, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def rect(x, y, w, h, c, t=1):
    for k in range(t):
        fill(x, y + k, w, 1, c)
        fill(x, y + h - 1 - k, w, 1, c)
        fill(x + k, y, 1, h, c)
        fill(x + w - 1 - k, y, 1, h, c)


def circle(cx, cy, r, c, filled=True):
    if filled:
        for yy in range(-r, r + 1):
            half = int(math.sqrt(max(0, r * r - yy * yy)))
            for xx in range(-half, half + 1):
                px(cx + xx, cy + yy, c)
    else:
        steps = max(24, int(2 * math.pi * r))
        for k in range(steps):
            a = 2 * math.pi * k / steps
            px(cx + int(r * math.cos(a)), cy + int(r * math.sin(a)), c)


def poly(points, c):
    """Fill a polygon given as [(x, y), ...] via scanlines."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0, y1 = min(ys), max(ys)
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, ya = points[i]
            x1, yb = points[(i + 1) % n]
            if ya == yb:
                continue
            if (ya <= y < yb) or (yb <= y < ya):
                t = (y - ya) / (yb - ya)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa = int(math.ceil(xs[k]))
            xb = int(math.floor(xs[k + 1]))
            for x in range(xa, xb + 1):
                px(x, y, c)


# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs, drawn from scratch. Uppercase, lowercase, digits,
# and common punctuation. Unknown characters render as a space.
U = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
}
L = {
    "a": ("00000", "01110", "10001", "01111", "10001", "01111", "00000"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "01110", "10000", "10000", "10000", "01110", "00000"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "01110", "10001", "11111", "10000", "01110", "00000"),
    "f": ("00110", "01000", "01110", "01000", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10110", "11000", "10110", "10001", "10001"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    "q": ("00000", "00000", "01111", "10001", "01111", "00001", "00001"),
    "r": ("00000", "00000", "10110", "11000", "10000", "10000", "10000"),
    "s": ("00000", "01111", "10000", "01110", "00001", "11110", "00000"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01000", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
}
P = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
}
FONT = {}
FONT.update(U)
FONT.update(L)
FONT.update(P)
# Bullet and em dash drawn from the same grid.
FONT["\u2022"] = ("00000", "00000", "01100", "01100", "01100", "00000", "00000")
FONT["\u2014"] = ("00000", "00000", "00000", "11111", "00000", "00000", "00000")
FONT["\u2019"] = FONT["'"]
FONT["\u201c"] = FONT['"']
FONT["\u201d"] = FONT['"']


def text_w(s, scale):
    return len(s) * 6 * scale


def text(x, y, s, scale, c, align="l"):
    if align == "c":
        x = x - text_w(s, scale) // 2
    elif align == "r":
        x = x - text_w(s, scale)
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is None:
            cx += 6 * scale
            continue
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row[col] == "1":
                    fill(cx + col * scale, y + r * scale, scale, scale, c)
        cx += 6 * scale
    return cx


def wrap(t, n):
    lines = []
    for raw in t.split("\n"):
        words = raw.split(" ")
        cur = ""
        for wd in words:
            if cur == "":
                cur = wd
            elif len(cur) + 1 + len(wd) <= n:
                cur = cur + " " + wd
            else:
                lines.append(cur)
                cur = wd
        if cur != "":
            lines.append(cur)
    return lines


def para(x, y, s, scale, c, maxw, leading=None):
    if leading is None:
        leading = 7 * scale + 3
    n = max(1, maxw // (6 * scale))
    yy = y
    for ln in wrap(s, n):
        text(x, yy, ln, scale, c)
        yy += leading
    return yy


# ---------------------------------------------------------------- PNG
def png_bytes():
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += buf[y * W * 3:(y + 1) * W * 3]

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


# ---------------------------------------------------------------- data
STATS = [
    ("35", "STORIES"),
    ("9", "REGIONS"),
    ("2", "LEADS"),
    ("6", "BRIEFINGS"),
    ("27", "IN THE INDEX"),
    ("1", "DAY"),
]

BRIEFINGS = [
    ("3", "MEXICO", "Cartel boss 'El Chapo Isidro' captured; 11 dead in raid", "badge"),
    ("4", "FINLAND", "Russian cargo ship ablaze off the Finnish coast", "flame"),
    ("5", "KYIV", "14 missing after Russian drone hits Kyiv tower block", "building"),
    ("6", "SPACE", "BepiColombo enters Mercury orbit after 8 years", "rocket"),
    ("7", "WASHINGTON", "Pentagon releases 43 secret UAP files", "file"),
    ("8", "SEOUL", "Foreign minister quits over AI-cheating scandal", "chip"),
]

INDEX_ITEMS = [
    "Lethal-AI talks to 2028",
    "Netanyahu coalition fails",
    "Israeli strikes kill 9 in Gaza",
    "Indonesia factory fire kills 7",
    "Lisbon cost-of-living march",
    "India 720/9d, Wellington",
    "Nepal PM Shah meets Modi",
    "Bolsonaro stable in ICU",
    "Kim: security, not supremacy",
    "24 killed in South Sudan",
    "Drone hits UN site, Khartoum",
    "35 killed in Nigeria reprisals",
    "Nigeria boat sinking kills 24",
    "WHO: peace plea in Congo",
    "Bitcoin off 2-year low",
    "Trump seeks Iran deal",
    "US-China talks on Hormuz",
    "France protests, 6th Sat",
    "Ganga deal expires 12 Dec",
    "Scarborough standoff grows",
    "UK to build Ukraine drones",
    "Australia PM on COP failure",
    "Saudis down Houthi missiles",
    "Lebanon: 264kg explosives",
    "Nvidia chip-smuggling ring",
    "Houthis hit Riyadh, day 3",
    "COP draft drops fossil fuels",
]

# (number, label, lon, lat, color)
PINS = [
    (1, "MIDDLE EAST", 45, 30, RED),
    (2, "EUROPE", 15, 52, BLUE),
    (3, "AFRICA", 20, 2, GREEN),
    (4, "SOUTH ASIA", 78, 22, OCHRE),
    (5, "EAST ASIA", 115, 35, PURPLE),
    (6, "SE ASIA & OCEANIA", 128, -8, TEAL),
    (7, "LATIN AMERICA", -60, -15, BROWN),
    (8, "NORTH AMERICA", -100, 45, NAVY),
    (9, "GLOBAL & SPACE", -150, -20, GREY),
]

CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70),
     (-75, 62), (-60, 55), (-55, 47), (-70, 42), (-75, 35), (-80, 26),
     (-90, 21), (-97, 16), (-92, 14), (-83, 9), (-79, 9), (-90, 14),
     (-105, 20), (-112, 29), (-120, 34), (-125, 42), (-125, 49),
     (-135, 58), (-155, 58), (-165, 60)],
    # South America
    [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-70, -18), (-70, -30),
     (-72, -40), (-74, -52), (-68, -55), (-65, -45), (-58, -35),
     (-48, -28), (-40, -22), (-35, -8), (-45, -3), (-50, 0), (-53, 5),
     (-60, 8), (-68, 11), (-75, 11)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (0, 50),
     (3, 53), (8, 57), (10, 59), (18, 56), (21, 55), (24, 58),
     (28, 60), (30, 62), (30, 70), (25, 71), (18, 69), (12, 66),
     (5, 60), (5, 58), (-2, 57), (-5, 50), (-8, 43), (-9, 37)],
    # Africa
    [(-6, 35), (10, 37), (20, 32), (30, 31), (32, 31), (35, 28),
     (43, 12), (51, 11), (48, 2), (41, -4), (40, -15), (36, -26),
     (32, -29), (26, -34), (19, -35), (16, -28), (12, -18), (9, -1),
     (9, 4), (-8, 5), (-13, 8), (-17, 15), (-17, 21), (-15, 27),
     (-10, 31)],
    # Asia
    [(30, 62), (40, 68), (60, 69), (70, 72), (90, 75), (110, 76),
     (130, 72), (150, 70), (170, 66), (178, 65), (170, 60), (162, 56),
     (158, 52), (142, 50), (140, 40), (130, 42), (127, 35), (122, 30),
     (120, 25), (110, 20), (108, 12), (105, 9), (100, 8), (98, 12),
     (92, 16), (88, 22), (80, 15), (77, 8), (73, 20), (66, 25),
     (60, 25), (57, 26), (52, 28), (48, 30), (43, 30), (40, 36),
     (36, 36), (30, 36), (28, 41)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (129, -32),
     (137, -35), (140, -38), (146, -39), (150, -37), (153, -32),
     (153, -27), (146, -19), (142, -15), (142, -11), (136, -12),
     (132, -12), (126, -14), (122, -17), (118, -20)],
]

LAND = (214, 196, 150)


def project(mx, my, mw, mh, lon, lat):
    x = mx + int((lon + 180.0) / 360.0 * mw)
    y = my + int((75.0 - lat) / 135.0 * mh)
    return (x, y)


# ---------------------------------------------------------------- icons
def icon(x, y, kind, c):
    if kind == "badge":
        circle(x + 14, y + 14, 13, c)
        circle(x + 14, y + 14, 8, WHITE)
        text(x + 11, y + 9, "*", 1, c)
    elif kind == "flame":
        poly([(x + 14, y + 2), (x + 24, y + 16), (x + 20, y + 26),
              (x + 8, y + 26), (x + 4, y + 16)], c)
        circle(x + 14, y + 20, 4, YELLOW)
    elif kind == "building":
        fill(x + 6, y + 6, 16, 22, c)
        fill(x + 9, y + 10, 3, 3, WHITE)
        fill(x + 16, y + 10, 3, 3, WHITE)
        fill(x + 9, y + 17, 3, 3, WHITE)
        fill(x + 16, y + 17, 3, 3, WHITE)
        fill(x + 9, y + 24, 3, 3, WHITE)
    elif kind == "rocket":
        poly([(x + 14, y + 2), (x + 20, y + 14), (x + 20, y + 22),
              (x + 8, y + 22), (x + 8, y + 14)], c)
        poly([(x + 8, y + 18), (x + 2, y + 26), (x + 8, y + 24)], c)
        poly([(x + 20, y + 18), (x + 26, y + 26), (x + 20, y + 24)], c)
        circle(x + 14, y + 12, 3, WHITE)
    elif kind == "file":
        fill(x + 7, y + 3, 14, 24, c)
        fill(x + 7, y + 3, 14, 5, WHITE)
        line(x + 10, y + 12, x + 18, y + 12, WHITE, 2)
        line(x + 10, y + 17, x + 18, y + 17, WHITE, 2)
        line(x + 10, y + 22, x + 16, y + 22, WHITE, 2)
    elif kind == "chip":
        fill(x + 6, y + 7, 16, 16, c)
        fill(x + 11, y + 12, 6, 6, WHITE)
        for k in range(3):
            line(x + 9 + k * 5, y + 3, x + 9 + k * 5, y + 7, c, 2)
            line(x + 9 + k * 5, y + 23, x + 9 + k * 5, y + 27, c, 2)
        for k in range(3):
            line(x + 3, y + 10 + k * 5, x + 6, y + 10 + k * 5, c, 2)
            line(x + 22, y + 10 + k * 5, x + 25, y + 10 + k * 5, c, 2)


# ---------------------------------------------------------------- scenes
def lead1_scene(x, y, w, h):
    fill(x, y, w, h, NIGHT)
    for sx, sy in [(30, 18), (90, 34), (170, 14), (260, 30), (330, 16),
                   (410, 28), (60, 55), (220, 48), (380, 52)]:
        circle(x + sx, y + sy, 2, WHITE)
    circle(x + w - 90, y + 52, 34, ORANGE)
    circle(x + w - 90, y + 52, 24, YELLOW)
    # Summit buildings
    fill(x + 30, y + h - 62, 70, 62, (60, 70, 95))
    fill(x + 110, y + h - 84, 90, 84, (70, 80, 110))
    fill(x + 210, y + h - 56, 80, 56, (60, 70, 95))
    fill(x + 300, y + h - 72, 100, 72, (70, 80, 110))
    for bx in [40, 60, 80, 125, 145, 165, 225, 245, 265, 315, 335, 355, 375]:
        fill(x + bx, y + h - 50, 8, 8, YELLOW)
    # Smoke
    for sx, sy, r in [(150, 40, 12), (165, 28, 16), (150, 14, 10),
                      (340, 46, 12), (355, 32, 15)]:
        circle(x + sx, y + sy, r, SMOKE)
    # Ground
    fill(x, y + h - 12, w, 12, (30, 30, 40))
    # Red banner
    fill(x + 16, y + h - 40, 300, 26, RED)
    text(x + 26, y + h - 35, "TALKS COLLAPSE", 2, WHITE)
    text(x + 26, y + h - 21, "NO DEAL", 2, WHITE)


def lead2_scene(x, y, w, h):
    fill(x, y, w, h, (150, 150, 155))
    fill(x, y + h // 2, w, h - h // 2, DARKSEA)
    # Clouds
    for cx, cy, cw in [(40, 22, 90), (200, 14, 110), (360, 26, 80)]:
        fill(x + cx, y + cy, cw, 14, (120, 120, 125))
        fill(x + cx + 14, y + cy - 8, cw - 28, 12, (120, 120, 125))
    # Missile trails
    line(x + 60, y + 20, x + 150, y + 90, WHITE, 2)
    line(x + 300, y + 12, x + 240, y + 96, WHITE, 2)
    line(x + 420, y + 30, x + 360, y + 100, WHITE, 2)
    circle(x + 60, y + 20, 5, YELLOW)
    circle(x + 300, y + 12, 5, YELLOW)
    circle(x + 420, y + 30, 5, YELLOW)
    # Tanker
    fill(x + 90, y + h - 78, 300, 26, (20, 20, 26))
    fill(x + 110, y + h - 104, 60, 26, (90, 40, 40))
    fill(x + 180, y + h - 104, 60, 26, (40, 80, 50))
    fill(x + 250, y + h - 104, 60, 26, (40, 60, 110))
    fill(x + 330, y + h - 104, 50, 26, (90, 40, 40))
    # Fire on the tanker
    poly([(x + 140, y + h - 104), (x + 128, y + h - 78),
          (x + 152, y + h - 78)], ORANGE)
    poly([(x + 200, y + h - 104), (x + 190, y + h - 84),
          (x + 212, y + h - 84)], YELLOW)
    poly([(x + 300, y + h - 104), (x + 288, y + h - 78),
          (x + 312, y + h - 78)], ORANGE)
    # Waves
    for wy in [h - 40, h - 28, h - 16]:
        for wx in range(10, w - 10, 46):
            line(x + wx, y + wy, x + wx + 24, y + wy, (80, 130, 180), 2)
    # Red banner
    fill(x + 16, y + 8, 330, 26, RED)
    text(x + 26, y + 13, "25 TANKERS HIT IN 7 DAYS", 2, WHITE)


# ---------------------------------------------------------------- page
def draw_page():
    fill(0, 0, W, H, CREAM)
    fill(12, 12, W - 24, H - 24, PAPER)
    rect(12, 12, W - 24, H - 24, INK, 2)

    # 1. Masthead
    text(512, 26, "THE WORLD IN ONE DAY - EST. EVERY MORNING", 1, GREY,
         align="c")
    text(512, 44, "THE WORLD IN ONE DAY", 6, INK, align="c")
    fill(60, 96, W - 120, 5, RED)
    text(512, 110, "MONDAY 23 NOVEMBER 2026", 3, RED, align="c")
    text(512, 138, "35 stories | 9 regions - the whole world on one page",
         2, INK, align="c")

    # 2. Stat strip
    sx = 24
    for num, label in STATS:
        fill(sx, 162, 160, 40, NAVY)
        text(sx + 80, 168, num, 3, WHITE, align="c")
        text(sx + 80, 192, label, 1, WHITE, align="c")
        sx += 163
    # 24 + 5*163 + 160 = 999

    # 3. Leads
    leads = [
        (24, "LEAD 1 - CLIMATE - ANTALYA",
         "COP31 COLLAPSES: 'WORST EVER'",
         "Guterres 'deeply disappointed' as oil states hijack the talks; "
         "the final draft drops any mention of fossil fuels.",
         lead1_scene),
        (524, "LEAD 2 - MIDDLE EAST - THE GULF",
         "IRAN HITS US BASE; OIL ROUTE IN FLAMES",
         "Tehran strikes the US base in Bahrain; 25 tankers hit in the "
         "Strait of Hormuz in 7 days. Houthis hit Riyadh, day 3.",
         lead2_scene),
    ]
    for lx, kicker, head, deck, scene in leads:
        fill(lx, 212, 476, 252, WHITE)
        rect(lx, 212, 476, 252, INK, 2)
        scene(lx + 8, 220, 460, 118)
        text(lx + 12, 348, kicker, 1, RED)
        para(lx + 12, 364, head, 3, INK, 452, leading=24)
        para(lx + 12, 416, deck, 2, INK, 452, leading=17)

    # 4. Briefings
    text(24, 476, "BRIEFINGS", 2, RED)
    line(150, 484, 1000, 484, INK, 2)
    bw, bh = 317, 76
    for i, (num, region, head, kind) in enumerate(BRIEFINGS):
        bx = 24 + (i % 3) * 322
        by = 494 + (i // 3) * 82
        fill(bx, by, bw, bh, WHITE)
        rect(bx, by, bw, bh, INK, 1)
        text(bx + 10, by + 8, num, 5, RED)
        icon(bx + bw - 40, by + 8, kind, NAVY)
        text(bx + 52, by + 10, region, 2, NAVY)
        para(bx + 52, by + 30, head, 2, INK, bw - 64, leading=17)

    # 5 + 6. Map (left) and Index (right)
    text(24, 668, "WORLD MAP - 9 REGIONS", 2, RED)
    text(640, 668, "THE INDEX - STORIES 9-35", 2, RED)
    line(24, 690, 624, 690, INK, 2)
    line(640, 690, 1000, 690, INK, 2)

    mx, my, mw, mh = 24, 696, 600, 240
    fill(mx, my, mw, mh, SEA)
    # Graticule
    for lon in range(-150, 181, 30):
        gx, _ = project(mx, my, mw, mh, lon, 75)
        line(gx, my, gx, my + mh, (60, 110, 160), 1)
    for lat in range(-60, 76, 30):
        _, gy = project(mx, my, mw, mh, -180, lat)
        line(mx, gy, mx + mw, gy, (60, 110, 160), 1)
    for cont in CONTINENTS:
        pts = [project(mx, my, mw, mh, lon, lat) for lon, lat in cont]
        poly(pts, LAND)
    # Pins
    for num, label, lon, lat, col in PINS:
        px_, py_ = project(mx, my, mw, mh, lon, lat)
        circle(px_, py_, 11, col)
        circle(px_, py_, 11, WHITE, filled=False)
        text(px_ - 3, py_ - 4, str(num), 1, WHITE)
    # Legend strip under the map
    ly = 944
    lx = 24
    for num, label, lon, lat, col in PINS:
        fill(lx, ly, 12, 12, col)
        text(lx + 15, ly + 2, str(num), 1, INK)
        tw = text_w(label, 1)
        text(lx + 27, ly + 2, label, 1, INK)
        lx += 42 + tw + 8
        if lx > 560:
            lx = 24
            ly += 16

    # Index: two columns, items 9-35
    col_x = [640, 824]
    col_w = 172
    for idx, item in enumerate(INDEX_ITEMS):
        num = 9 + idx
        cx = col_x[idx // 14]
        cy = 700 + (idx % 14) * 19
        text(cx, cy, str(num), 1, RED)
        para(cx + 16, cy, item, 1, INK, col_w - 16, leading=10)

    # 7. Footer
    line(24, 976, 1000, 976, INK, 2)
    text(512, 986,
         "All stories dated Monday 23 November 2026 - Wires to 08:55 WITA "
         "- Drawn in code", 1, GREY, align="c")


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        raise SystemExit("MAKEFUN_OUTPUT_DIR is not set")
    draw_page()
    data = png_bytes()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
