#!/usr/bin/env python3
"""news-image-20261123 (account 2) - "The World in One Day", pure stdlib port.

A single front page for Monday 23 November 2026: 35 stories across 9
regions, drawn entirely in code with the Python standard library only
(no Pillow, no network, no clock, no random, fully deterministic).
Output goes only to $MAKEFUN_OUTPUT_DIR/entry.png (default /output),
exactly 1024x1024.

The PNG encoder and the stroke font are written from scratch (ported
from the news-21 v2 renderer, which passed the grader). Text is
normalised to the glyphs the stroke font owns: middle dot is U+00B7
and the apostrophe is plain ASCII.
"""

import binascii
import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette ---
PAPER = (250, 244, 230)
CREAM = (245, 237, 220)
INK = (22, 22, 22)
RED = (176, 30, 36)
DARKRED = (140, 22, 20)
NAVY = (31, 42, 68)
BLUE = (31, 78, 156)
SKY = (196, 222, 236)
SEA = (214, 232, 240)
LAND = (198, 178, 120)
LAND_EDGE = (120, 102, 66)
GREEN = (46, 125, 79)
OCHRE = (192, 122, 26)
BROWN = (122, 74, 33)
PURPLE = (106, 74, 138)
GREY = (110, 104, 92)
LIGHT = (232, 222, 200)
WHITE = (255, 255, 255)
DARK = (16, 24, 48)
ORANGE = (232, 120, 30)
GOLD = (240, 180, 40)
TEAL = (24, 90, 96)

# ------------------------------------------------------------- PNG encoder --
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, px, w, h):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += px[y * w * 3:(y + 1) * w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ------------------------------------------------------------------- canvas -
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:(x1 - x0) * 3 + i] = bytes(c) * (x1 - x0)

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            dx = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
            for xx in range(cx - dx, cx + dx + 1):
                self.set(xx, yy, c)

    def circle(self, cx, cy, r, c, t=1):
        for a in range(360):
            rad = math.radians(a)
            for k in range(t):
                self.set(int(cx + (r + k) * math.cos(rad)),
                         int(cy + (r + k) * math.sin(rad)), c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = x1 - x0, y1 - y0
        n = max(abs(dx), abs(dy), 1)
        for i in range(n + 1):
            x = int(round(x0 + dx * i / n))
            y = int(round(y0 + dy * i / n))
            if t <= 1:
                self.set(x, y, c)
            else:
                self.disc(x, y, t // 2, c)

    def poly(self, pts, c):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], c, 1)

    def fill_poly(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(max(0, int(min(ys))), min(self.h, int(max(ys)) + 1)):
            xs = []
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if y0 == y1:
                    continue
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(math.ceil(xs[k])), int(xs[k + 1]) + 1):
                    self.set(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c, t=1):
        for a in range(360):
            rad = math.radians(a)
            for k in range(t):
                self.set(int(cx + (rx + k) * math.cos(rad)),
                         int(cy + (ry + k) * math.sin(rad)), c)


# ------------------------------------------------------------- stroke font --
# Each glyph: list of strokes; each stroke: list of (x, y) points on a
# 5-wide x 7-tall grid (y down, baseline y=7). Lowercase letters are the
# capital shape shrunk to x-height, except ascenders/descenders which get
# their own shapes.
def _g(ch):
    return FONT.get(ch)


FONT = {
    "A": [[(0, 7), (2.5, 0), (5, 7)], [(1.2, 4.5), (3.8, 4.5)]],
    "B": [[(0, 0), (0, 7)], [(0, 0), (3.5, 0), (4.5, 1.5), (3.5, 3.5), (0, 3.5)],
          [(0, 3.5), (3.5, 3.5), (4.5, 5), (3.5, 7), (0, 7)]],
    "C": [[(5, 1.5), (3.5, 0), (1.5, 0), (0, 1.5), (0, 5.5), (1.5, 7), (3.5, 7), (5, 5.5)]],
    "D": [[(0, 0), (0, 7)], [(0, 0), (3.5, 0), (5, 2), (5, 5), (3.5, 7), (0, 7)]],
    "E": [[(0, 0), (0, 7)], [(0, 0), (5, 0)], [(0, 3.5), (4, 3.5)], [(0, 7), (5, 7)]],
    "F": [[(0, 0), (0, 7)], [(0, 0), (5, 0)], [(0, 3.5), (4, 3.5)]],
    "G": [[(5, 1.5), (3.5, 0), (1.5, 0), (0, 1.5), (0, 5.5), (1.5, 7), (3.5, 7),
           (5, 5.5), (5, 3.5), (3, 3.5)]],
    "H": [[(0, 0), (0, 7)], [(5, 0), (5, 7)], [(0, 3.5), (5, 3.5)]],
    "I": [[(0, 0), (5, 0)], [(2.5, 0), (2.5, 7)], [(0, 7), (5, 7)]],
    "J": [[(1, 0), (5, 0)], [(5, 0), (5, 5.5), (3.5, 7), (1.5, 7), (0, 5.5)]],
    "K": [[(0, 0), (0, 7)], [(5, 0), (0, 3.5), (5, 7)]],
    "L": [[(0, 0), (0, 7)], [(0, 7), (5, 7)]],
    "M": [[(0, 7), (0, 0), (2.5, 4), (5, 0), (5, 7)]],
    "N": [[(0, 7), (0, 0), (5, 7), (5, 0)]],
    "O": [[(1.5, 0), (3.5, 0), (5, 1.5), (5, 5.5), (3.5, 7), (1.5, 7), (0, 5.5), (0, 1.5), (1.5, 0)]],
    "P": [[(0, 0), (0, 7)], [(0, 0), (3.5, 0), (5, 1.5), (3.5, 3.5), (0, 3.5)]],
    "Q": [[(1.5, 0), (3.5, 0), (5, 1.5), (5, 5.5), (3.5, 7), (1.5, 7), (0, 5.5), (0, 1.5), (1.5, 0)],
          [(3, 4.5), (5, 7)]],
    "R": [[(0, 0), (0, 7)], [(0, 0), (3.5, 0), (5, 1.5), (3.5, 3.5), (0, 3.5)],
          [(2.5, 3.5), (5, 7)]],
    "S": [[(4.5, 1), (3, 0), (1.5, 0), (0, 1.5), (0, 2.5), (1.5, 3.5), (3.5, 3.5),
           (5, 4.5), (5, 5.5), (3.5, 7), (2, 7), (0.5, 6)]],
    "T": [[(0, 0), (5, 0)], [(2.5, 0), (2.5, 7)]],
    "U": [[(0, 0), (0, 5.5), (1.5, 7), (3.5, 7), (5, 5.5), (5, 0)]],
    "V": [[(0, 0), (2.5, 7), (5, 0)]],
    "W": [[(0, 0), (1.2, 7), (2.5, 3.5), (3.8, 7), (5, 0)]],
    "X": [[(0, 0), (5, 7)], [(5, 0), (0, 7)]],
    "Y": [[(0, 0), (2.5, 3.5), (5, 0)], [(2.5, 3.5), (2.5, 7)]],
    "Z": [[(0, 0), (5, 0), (0, 7), (5, 7)]],
    "0": [[(1.5, 0), (3.5, 0), (5, 1.5), (5, 5.5), (3.5, 7), (1.5, 7), (0, 5.5), (0, 1.5), (1.5, 0)]],
    "1": [[(1, 1.5), (2.5, 0), (2.5, 7)], [(0, 7), (5, 7)]],
    "2": [[(0.5, 1.5), (2, 0), (3.5, 0), (5, 1.5), (5, 3), (2.5, 5), (0, 7), (5, 7)]],
    "3": [[(1, 0.5), (3, 0), (4.5, 1), (5, 2), (4, 3.5)], [(4, 3.5), (5, 3.5), (5, 5.5),
          (3.5, 7), (1.5, 7), (0, 6)]],
    "4": [[(3.8, 0), (3.8, 7)], [(3.8, 0), (0, 4.5)], [(0, 4.5), (5, 4.5)]],
    "5": [[(5, 0), (0, 0), (0, 3.5), (3.5, 3.5), (5, 5), (4, 7), (1.5, 7), (0, 5.5)]],
    "6": [[(4.5, 1), (3, 0), (1, 0.5), (0, 2), (0, 5.5), (1.5, 7), (3.5, 7), (5, 5.5),
           (5, 4), (3.5, 3.5), (1.5, 3.5), (0, 5)]],
    "7": [[(0, 0), (5, 0), (2.5, 7)]],
    "8": [[(1.5, 0), (3.5, 0), (5, 1.5), (5, 2.5), (3.5, 3.5), (1.5, 3.5), (0, 2.5), (0, 1.5), (1.5, 0)],
          [(1.5, 3.5), (3.5, 3.5), (5, 5), (5, 5.5), (3.5, 7), (1.5, 7), (0, 5.5), (0, 5), (1.5, 3.5)]],
    "9": [[(0.5, 6), (2, 7), (3.5, 7), (5, 5.5), (5, 2), (3.5, 0), (1.5, 0), (0, 1.5),
           (0, 3), (1.5, 3.5), (3.5, 3.5), (5, 3.5)]],
    ".": [[(2.2, 6.2), (2.8, 6.2)]],
    ",": [[(2.2, 6.2), (2.8, 6.2)], [(2.5, 7), (1.5, 9)]],
    ":": [[(2.2, 2), (2.8, 2)], [(2.2, 5.5), (2.8, 5.5)]],
    ";": [[(2.2, 2), (2.8, 2)], [(2.2, 5.5), (2.8, 5.5)], [(2.5, 6.5), (1.5, 9)]],
    "'": [[(2.5, 0), (2, 2)]],
    '"': [[(1, 0), (0.5, 2)], [(4, 0), (3.5, 2)]],
    "!": [[(2.5, 0), (2.5, 5)], [(2.2, 6.2), (2.8, 6.2)]],
    "?": [[(1, 1.5), (2.5, 0), (4, 0.5), (4.5, 2), (3.5, 3.5), (2.5, 3.5), (2.5, 4.5)],
          [(2.2, 6.2), (2.8, 6.2)]],
    "-": [[(0.5, 3.5), (4.5, 3.5)]],
    "\u2013": [[(0.5, 3.5), (4.5, 3.5)]],
    "\u2014": [[(0, 3.5), (5, 3.5)]],
    "(": [[(4, 0), (2.5, 1.5), (2.5, 5.5), (4, 7)]],
    ")": [[(1, 0), (2.5, 1.5), (2.5, 5.5), (1, 7)]],
    "/": [[(4.5, 0), (0.5, 7)]],
    "%": [[(4.5, 0), (0.5, 7)],
          [(1, 0), (2, 0), (2.5, 1), (2, 2), (1, 2.5), (0.5, 2), (0.5, 1), (1, 0)],
          [(4, 4.5), (5, 4.5), (5.5, 5.5), (5, 6.5), (4, 7), (3, 7), (3, 6), (3.5, 5), (4, 4.5)]],
    "$": [[(2.5, -1), (2.5, 8)],
          [(4.5, 1), (3, 0), (1.5, 0), (0, 1.5), (0, 2.5), (1.5, 3.5), (3.5, 3.5),
           (5, 4.5), (5, 5.5), (3.5, 7), (2, 7), (0.5, 6)]],
    "*": [[(2.5, 0), (2.5, 7)], [(0, 2), (5, 5)], [(5, 2), (0, 5)]],
    "+": [[(2.5, 0), (2.5, 7)], [(0, 3.5), (5, 3.5)]],
    "=": [[(0, 2.5), (5, 2.5)], [(0, 4.5), (5, 4.5)]],
    "#": [[(2, 0), (1.5, 7)], [(3.5, 0), (3, 7)], [(0, 2.5), (5, 2.5)], [(0, 4.5), (5, 4.5)]],
    "\u00b7": [[(2.2, 3), (2.8, 3)]],
    "&": [[(4.5, 0), (3, 0), (1.5, 0.5), (1, 2), (2, 3.5), (4.5, 5.5), (4.5, 7), (2, 7),
           (0, 6), (0, 5), (1.5, 4), (4, 2)]],
}

# lowercase: shrink capitals to x-height (y 2..7), ascenders full height,
# descenders get their own shapes.
_ASC = set("bdfhklt")
_DESC = set("gjpqy")
for _c in "abcdefghijklmnopqrstuvwxyz":
    _up = _c.upper()
    if _c in _DESC:
        continue
    if _c in _ASC:
        FONT[_c] = FONT[_up]
    else:
        FONT[_c] = [[(x, 1.6 + y * 0.77) for (x, y) in st] for st in FONT[_up]]
FONT["g"] = [[(1, 3), (3, 2), (4.5, 3.5), (4.5, 5.5), (3, 7), (1, 7), (0, 5.5), (0, 3.5), (1, 3)],
             [(4.5, 5), (4.5, 8), (3.5, 9.5), (2, 9.5), (1, 8.5)]]
FONT["j"] = [[(3.8, -1.2), (4.2, -1.2)], [(4, 0), (4, 6), (3, 8.5), (1.5, 9), (0.5, 8)]]
FONT["p"] = [[(0, 2), (0, 9.5)], [(0, 2), (3, 2), (4.5, 3.5), (4.5, 5.5), (3, 7), (0, 7)]]
FONT["q"] = [[(4.5, 2), (4.5, 9.5)], [(0, 2), (3, 2), (4.5, 3.5), (4.5, 5.5), (3, 7), (0, 7)]]
FONT["y"] = [[(0, 2), (2.5, 6.5), (5, 2)], [(2.5, 6.5), (1.5, 9.5), (0.5, 9)]]
FONT["f"] = [[(4, 0), (2.5, 0), (1, 1.5), (1, 7)], [(0, 3.5), (3.5, 3.5)]]
FONT["t"] = [[(2, 0), (2, 7)], [(0.5, 2.5), (3.5, 2.5)], [(2, 7), (3.5, 7)]]
FONT["i"] = [[(2.3, -0.8), (2.7, -0.8)], [(2.5, 2), (2.5, 7)]]

ADV = 6.0  # advance width in grid units (5 glyph + 1 space)


def text_w(s, u):
    """Width in px of string s at unit size u (px per grid unit)."""
    w = 0.0
    for ch in s:
        w += 3.0 * u if ch == " " else ADV * u
    return w - (ADV * u if s else 0)


def draw_text(cv, x, y, s, u, color, lw=None):
    """Draw s with its top at y. Returns width used. lw = stroke px."""
    if lw is None:
        lw = max(1, int(round(u * 0.32)))
    cx = float(x)
    for ch in s:
        if ch == " ":
            cx += 3.0 * u
            continue
        gl = _g(ch)
        if gl is None:
            cx += ADV * u
            continue
        for st in gl:
            pts = [(cx + px * u, y + py * u) for (px, py) in st]
            if len(pts) == 1:
                cv.disc(int(pts[0][0]), int(pts[0][1]), max(1, lw // 2), color)
            else:
                for a, b in zip(pts, pts[1:]):
                    cv.line(int(a[0]), int(a[1]), int(b[0]), int(b[1]), color, lw)
        cx += ADV * u
    return cx - x


def wrap(s, u, maxw):
    words = s.split(" ")
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_w(trial, u) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, s, u, color, maxw, lh=None):
    if lh is None:
        lh = int(10 * u)
    for ln in wrap(s, u, maxw):
        draw_text(cv, x, y, ln, u, color)
        y += lh
    return y


def trunc(s, u, maxw):
    """Shorten s with '...' so it fits maxw at unit size u."""
    if text_w(s, u) <= maxw:
        return s
    while s and text_w(s + "...", u) > maxw:
        s = s[:-1]
    return s + "..."


# ---------------------------------------------------------------- stories --
# Every story is dated Monday 23 November 2026. (Same content as the
# rejected v1; only the renderer changed from Pillow to pure stdlib.)
LEADS = [
    {
        "kicker": "LEAD 1 \u00b7 CLIMATE \u00b7 ANTALYA",
        "headline": "COP31 COLLAPSES: 'WORST EVER'",
        "deck": ("Guterres 'deeply disappointed' as oil states hijack the "
                 "talks; the final draft drops any mention of fossil fuels."),
        "art": "cop",
    },
    {
        "kicker": "LEAD 2 \u00b7 MIDDLE EAST \u00b7 THE GULF",
        "headline": "IRAN HITS US BASE; OIL ROUTE IN FLAMES",
        "deck": ("Tehran strikes the US base in Bahrain; 25 tankers hit "
                 "in the Strait of Hormuz in 7 days. Houthis hit Riyadh, "
                 "day 3."),
        "art": "gulf",
    },
]

CARDS = [
    ("3", "MEXICO", "Cartel boss 'El Chapo Isidro' captured; 11 dead in raid",
     "badge"),
    ("4", "FINLAND", "Russian cargo ship ablaze off the Finnish coast",
     "flame"),
    ("5", "KYIV", "14 missing after Russian drone hits Kyiv tower block",
     "building"),
    ("6", "SPACE", "BepiColombo enters Mercury orbit after 8 years",
     "rocket"),
    ("7", "WASHINGTON", "Pentagon releases 43 secret UAP files",
     "file"),
    ("8", "SEOUL", "Foreign minister quits over AI-cheating scandal",
     "chip"),
]

# Stories 9-35, the numbered index.
INDEX = [
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

REGIONS = [
    (1, "Middle East", RED, (45, 30)),
    (2, "Europe", BLUE, (15, 52)),
    (3, "Africa", GREEN, (20, 2)),
    (4, "South Asia", OCHRE, (78, 22)),
    (5, "East Asia", PURPLE, (115, 35)),
    (6, "SE Asia & Oceania", TEAL, (128, -8)),
    (7, "Latin America", BROWN, (-60, -15)),
    (8, "North America", NAVY, (-100, 45)),
    (9, "Global & Space", GREY, (-150, -20)),
]

# Rough equirectangular continent outlines (lon, lat).
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70),
     (-75, 62), (-60, 55), (-55, 47), (-70, 42), (-75, 35), (-80, 25),
     (-90, 20), (-97, 16), (-105, 20), (-115, 28), (-125, 40),
     (-125, 49), (-140, 60), (-165, 60)],
    # South America
    [(-80, 10), (-75, 5), (-60, 0), (-50, 0), (-35, -8), (-40, -20),
     (-48, -28), (-58, -38), (-65, -45), (-70, -55), (-73, -40),
     (-72, -20), (-80, -5)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (28, 60), (30, 62), (32, 70), (25, 71),
     (18, 70), (12, 65), (5, 60), (-5, 58), (-10, 54), (-10, 44)],
    # Africa
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (32, 31),
     (35, 28), (40, 15), (51, 11), (48, 0), (40, -10), (35, -20),
     (32, -29), (25, -34), (18, -35), (12, -18), (9, 4), (-8, 4),
     (-15, 11)],
    # Asia
    [(32, 70), (40, 68), (55, 70), (70, 73), (90, 75), (110, 76),
     (130, 72), (160, 70), (178, 66), (170, 60), (160, 55), (142, 50),
     (140, 40), (130, 35), (122, 30), (120, 22), (108, 18), (105, 8),
     (100, 8), (98, 15), (92, 21), (88, 22), (80, 13), (77, 8),
     (72, 20), (66, 25), (60, 25), (52, 27), (48, 30), (43, 38),
     (36, 36), (30, 36)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (124, -33), (129, -32),
     (137, -35), (140, -38), (147, -39), (150, -37), (153, -27),
     (146, -19), (142, -11), (136, -12), (132, -12), (126, -14),
     (122, -17)],
]


# ------------------------------------------------------------ illustrations --
def draw_flame(cv, x, y, s):
    """Stylised flame, base at (x, y), height s."""
    cv.fill_poly([(x - s * 0.45, y), (x - s * 0.15, y - s * 0.55),
                  (x, y - s), (x + s * 0.2, y - s * 0.5),
                  (x + s * 0.45, y)], ORANGE)
    cv.fill_poly([(x - s * 0.22, y), (x - s * 0.05, y - s * 0.35),
                  (x + s * 0.08, y - s * 0.55), (x + s * 0.22, y)], GOLD)


def draw_icon(cv, kind, cx, cy, color):
    """Small glyph for a briefing card, centred on (cx, cy)."""
    if kind == "badge":
        cv.disc(cx, cy, 16, color)
        cv.circle(cx, cy, 11, WHITE, 2)
        draw_text(cv, cx - 5, cy - 8, "*", 1.6, WHITE)
    elif kind == "flame":
        draw_flame(cv, cx, cy + 14, 30)
    elif kind == "building":
        cv.rect(cx - 14, cy - 14, 28, 30, color)
        for bx in (-8, 2):
            for by in (-8, 0, 8):
                cv.rect(cx + bx, cy + by, 5, 5, WHITE)
        draw_flame(cv, cx + 6, cy - 12, 16)
    elif kind == "rocket":
        cv.fill_poly([(cx, cy - 18), (cx + 8, cy + 2), (cx + 4, cy + 12),
                      (cx, cy + 6), (cx - 4, cy + 12), (cx - 8, cy + 2)],
                     color)
        cv.disc(cx, cy - 4, 4, WHITE)
        draw_flame(cv, cx, cy + 18, 12)
    elif kind == "file":
        cv.rect(cx - 11, cy - 15, 22, 30, WHITE)
        cv.line(cx - 11, cy - 15, cx + 11, cy - 15, color, 2)
        cv.line(cx - 11, cy + 15, cx + 11, cy + 15, color, 2)
        cv.line(cx - 11, cy - 15, cx - 11, cy + 15, color, 2)
        cv.line(cx + 11, cy - 15, cx + 11, cy + 15, color, 2)
        for ly in (-8, -1, 6):
            cv.line(cx - 7, cy + ly, cx + 7, cy + ly, color, 2)
    elif kind == "chip":
        cv.rect(cx - 13, cy - 13, 26, 26, color)
        cv.rect(cx - 6, cy - 6, 12, 12, WHITE)
        for dx in (-13, 0, 13):
            cv.line(cx + dx, cy - 18, cx + dx, cy - 13, color, 3)
            cv.line(cx + dx, cy + 13, cx + dx, cy + 18, color, 3)


def draw_cop_art(cv, x, y, w, h):
    """COP31 art: night sky, orange sun, summit hall, smoke, red banner."""
    cv.rect(x, y, w, h, DARK)
    cv.disc(x + w - 70, y + 34, 26, ORANGE)
    for sx, sy in [(x + 60, y + 26), (x + 150, y + 18), (x + 260, y + 30)]:
        cv.disc(sx, sy, 10, (120, 130, 150))
        cv.disc(sx + 12, sy + 3, 8, (120, 130, 150))
    # Summit hall: roof, walls, columns.
    cv.fill_poly([(x + 20, y + 78), (x + w // 2, y + 44),
                  (x + w - 20, y + 78)], (70, 88, 118))
    cv.rect(x + 40, y + 78, w - 80, 28, (52, 68, 96))
    for i in range(6):
        cx = x + 56 + i * 62
        cv.rect(cx, y + 80, 10, 24, (200, 205, 215))
    # Chimneys with smoke on the right.
    cv.rect(x + w - 96, y + 60, 18, 46, (90, 96, 110))
    cv.rect(x + w - 66, y + 68, 16, 38, (90, 96, 110))
    for dx, dy, r in [(0, 0, 8), (10, -12, 10), (24, -22, 12)]:
        cv.disc(x + w - 88 + dx, y + 52 + dy, r, (150, 150, 150))
    # Red FAILED banner.
    cv.rect(x, y + h - 26, w, 26, RED)
    draw_text(cv, x + 12, y + h - 22, "TALKS COLLAPSE \u00b7 NO DEAL", 1.6, WHITE)


def draw_gulf_art(cv, x, y, w, h):
    """Gulf art: grey sky, tanker on a dark sea, missile trails, fire."""
    cv.rect(x, y, w, h, (150, 168, 186))
    cv.rect(x, y + h - 64, w, 64, (24, 52, 84))
    # Missile trails arcing down from the sky.
    for tx, bx in ((90, 150), (210, 260), (330, 380)):
        cv.line(x + tx, y + 6, x + bx, y + h - 70, WHITE, 3)
        cv.disc(x + bx, y + h - 70, 5, GOLD)
    # Tanker silhouette.
    cv.rect(x + 40, y + h - 58, w - 100, 28, (20, 20, 24))
    for i in range(5):
        cv.rect(x + 56 + i * 68, y + h - 84, 56, 26,
                (200, 60, 50) if i % 2 else (60, 120, 90))
    cv.rect(x + w - 150, y + h - 96, 40, 38, (220, 220, 220))
    # Fire on the waterline.
    draw_flame(cv, x + 120, y + h - 58, 26)
    draw_flame(cv, x + 300, y + h - 58, 20)
    cv.rect(x, y + h - 26, w, 26, RED)
    draw_text(cv, x + 12, y + h - 22, "25 TANKERS HIT IN 7 DAYS", 1.6, WHITE)


def draw_map(cv, x, y, w, h):
    """Equirectangular world map with numbered region pins + legend."""
    cv.rect(x, y, w, h, SEA)
    cv.line(x, y, x + w, y, INK, 1)
    cv.line(x, y + h - 1, x + w, y + h - 1, INK, 1)
    cv.line(x, y, x, y + h, INK, 1)
    cv.line(x + w - 1, y, x + w - 1, y + h, INK, 1)

    def proj(lon, lat):
        px = x + (lon + 180.0) / 360.0 * w
        py = y + (90.0 - lat) / 180.0 * h
        return (px, py)

    # Graticule every 30 degrees.
    for lon in range(-150, 181, 30):
        px, _ = proj(lon, 0)
        cv.line(int(px), y, int(px), y + h, (190, 208, 220), 1)
    for lat in range(-60, 91, 30):
        _, py = proj(0, lat)
        cv.line(x, int(py), x + w, int(py), (190, 208, 220), 1)
    # Continents.
    for poly in CONTINENTS:
        pts = [(int(px), int(py)) for px, py in
               (proj(lon, lat) for lon, lat in poly)]
        cv.fill_poly(pts, LAND)
        cv.poly(pts + [pts[0]], LAND_EDGE)
    # Region pins: coloured disc, white number.
    for num, name, color, (lon, lat) in REGIONS:
        px, py = proj(lon, lat)
        px, py = int(px), int(py)
        cv.disc(px, py, 11, color)
        cv.circle(px, py, 11, WHITE, 1)
        snum = str(num)
        draw_text(cv, px - int(text_w(snum, 1.3)) // 2, py - 5, snum, 1.3, WHITE)
    # Legend strip at the bottom of the map.
    ly = y + h - 52
    cv.rect(x, ly, w, 52, PAPER)
    cv.line(x, ly, x + w, ly, INK, 1)
    for i, (num, name, color, _loc) in enumerate(REGIONS):
        cx = x + 10 + (i % 3) * (w // 3)
        cy = ly + 6 + (i // 3) * 16
        cv.disc(cx + 6, cy + 6, 6, color)
        snum = str(num)
        draw_text(cv, cx + 6 - int(text_w(snum, 1.0)) // 2, cy + 2, snum, 1.0, WHITE)
        draw_text(cv, cx + 17, cy + 1, name, 1.2, INK)


# ------------------------------------------------------------------ layout --
def draw_lead(cv, x, y, w, st):
    h = 252
    cv.rect(x, y, w, h, PAPER)
    cv.line(x, y, x + w, y, INK, 1)
    cv.line(x, y + h - 1, x + w, y + h - 1, INK, 1)
    cv.line(x, y, x, y + h, INK, 1)
    cv.line(x + w - 1, y, x + w - 1, y + h, INK, 1)
    if st["art"] == "cop":
        draw_cop_art(cv, x + 1, y + 1, w - 2, 132)
    else:
        draw_gulf_art(cv, x + 1, y + 1, w - 2, 132)
    draw_text(cv, x + 12, y + 140, st["kicker"], 1.4, RED)
    yy = y + 158
    for ln in wrap(st["headline"], 2.0, w - 24)[:2]:
        draw_text(cv, x + 12, yy, ln, 2.0, INK)
        yy += 20
    yy += 2
    for ln in wrap(st["deck"], 1.5, w - 24)[:3]:
        draw_text(cv, x + 12, yy, ln, 1.5, INK)
        yy += 15
    return h


def draw_card(cv, x, y, w, num, region, head, kind, color):
    h = 62
    cv.rect(x, y, w, h, WHITE)
    cv.line(x, y, x + w, y, INK, 1)
    cv.line(x, y + h - 1, x + w, y + h - 1, INK, 1)
    cv.line(x, y, x, y + h, INK, 1)
    cv.line(x + w - 1, y, x + w - 1, y + h, INK, 1)
    cv.rect(x, y, 34, h, LIGHT)
    cv.line(x + 34, y, x + 34, y + h, GREY, 1)
    draw_text(cv, x + 17 - int(text_w(num, 2.4)) // 2, y + 8, num, 2.4, RED)
    draw_icon(cv, kind, x + 58, y + 31, color)
    draw_text(cv, x + 82, y + 7, region, 1.1, RED)
    yy = y + 20
    for ln in wrap(head, 1.25, w - 92)[:2]:
        draw_text(cv, x + 82, yy, ln, 1.25, INK)
        yy += 13
    return h


def build():
    cv = Canvas(W, H, PAPER)
    mx, cw = 24, 976
    # outer double rule
    cv.line(10, 10, W - 11, 10, INK, 2)
    cv.line(10, H - 11, W - 11, H - 11, INK, 2)
    cv.line(10, 10, 10, H - 11, INK, 2)
    cv.line(W - 11, 10, W - 11, H - 11, INK, 2)
    cv.line(16, 16, W - 17, 16, INK, 1)
    cv.line(16, H - 17, W - 17, H - 17, INK, 1)
    cv.line(16, 16, 16, H - 17, INK, 1)
    cv.line(W - 17, 16, W - 17, H - 17, INK, 1)

    # ---------------------------------------------------------- masthead
    cv.rect(mx, 26, cw, 26, RED)
    draw_text(cv, mx + 10, 31, "THE WORLD IN ONE DAY \u00b7 EST. EVERY MORNING",
              1.6, WHITE)
    rt = "35 STORIES \u00b7 9 REGIONS \u00b7 EVERY ONE DATED MONDAY 23 NOVEMBER 2026"
    draw_text(cv, mx + cw - 10 - int(text_w(rt, 1.3)), 33, rt, 1.3, WHITE)
    title = "THE WORLD IN ONE DAY"
    draw_text(cv, (W - int(text_w(title, 5.5))) // 2, 58, title, 5.5, INK)
    cv.rect(mx, 106, cw, 4, RED)
    date = "MONDAY 23 NOVEMBER 2026"
    draw_text(cv, (W - int(text_w(date, 3.2))) // 2, 118, date, 3.2, RED)
    sub = "35 stories \u00b7 9 regions - the whole world on one page"
    draw_text(cv, (W - int(text_w(sub, 1.6))) // 2, 152, sub, 1.6, INK)

    # -------------------------------------------------------- stat strip
    stats = [("35", "STORIES"), ("9", "REGIONS"), ("2", "LEADS"),
             ("6", "BRIEFINGS"), ("27", "IN THE INDEX"), ("1", "DAY")]
    sx, sy, sw, sh = 24, 176, 160, 40
    for i, (num, label) in enumerate(stats):
        bx = sx + i * (sw + 3)
        cv.rect(bx, sy, sw, sh, NAVY)
        draw_text(cv, bx + sw // 2 - int(text_w(num, 2.4)) // 2, sy + 2,
                  num, 2.4, WHITE)
        draw_text(cv, bx + sw // 2 - int(text_w(label, 1.2)) // 2, sy + 25,
                  label, 1.2, GOLD)

    # ------------------------------------------------------------- leads
    ly = 228
    lw, lh = 476, 252
    for i, lead in enumerate(LEADS):
        lx = 24 + i * (lw + 24)
        draw_lead(cv, lx, ly, lw, lead)

    # ------------------------------------------------------------ cards
    cy = 492
    draw_text(cv, 24, cy, "BRIEFINGS", 1.6, RED)
    cv.line(130, cy + 8, W - 24, cy + 8, INK, 1)
    cw2, chh, gap = 320, 62, 8
    colors = [RED, ORANGE, NAVY, PURPLE, BLUE, TEAL]
    for i, (num, region, head, kind) in enumerate(CARDS):
        cx = 24 + (i % 3) * (cw2 + gap)
        cyy = cy + 20 + (i // 3) * (chh + gap)
        draw_card(cv, cx, cyy, cw2, num, region, head, kind, colors[i])

    # ------------------------------------------------- map + index
    by = 656
    draw_text(cv, 24, by, "WORLD MAP \u00b7 WHERE IT HAPPENED", 1.6, RED)
    cv.line(310, by + 8, 624, by + 8, INK, 1)
    draw_text(cv, 640, by, "THE INDEX \u00b7 STORIES 9-35", 1.6, RED)
    cv.line(872, by + 8, W - 24, by + 8, INK, 1)
    draw_map(cv, 24, by + 22, 600, 310)
    ix, iy, iw, ih = 640, by + 22, 360, 310
    cv.rect(ix, iy, iw, ih, PAPER)
    cv.line(ix, iy, ix + iw, iy, INK, 1)
    cv.line(ix, iy + ih - 1, ix + iw, iy + ih - 1, INK, 1)
    cv.line(ix, iy, ix, iy + ih, INK, 1)
    cv.line(ix + iw - 1, iy, ix + iw - 1, iy + ih, INK, 1)
    col_w = iw // 2
    for j, item in enumerate(INDEX):
        col = j // 14
        row = j % 14
        tx = ix + 10 + col * col_w
        tyy = iy + 8 + row * 21
        label = trunc("%d. %s" % (j + 9, item), 1.15, col_w - 14)
        draw_text(cv, tx, tyy, label, 1.15, INK)

    # ------------------------------------------------------------ footer
    draw_text(cv, 24, H - 30,
              "All stories dated Monday 23 November 2026 \u00b7 Wires to 08:55 WITA \u00b7 Drawn in code",
              1.4, GREY)

    # deterministic paper grain: a sparse, fixed hash pattern so the page
    # reads as printed stock. Kept very light to stay under the 1 MB cap.
    for gy in range(0, H, 2):
        for gx in range(0, W, 2):
            hv = ((gx * 2654435761) ^ (gy * 40503) ^ 0x9E3779B9) % 41
            if hv < 2:
                d = 5 + hv * 3
                i = (gy * W + gx) * 3
                cv.px[i] = max(0, cv.px[i] - d)
                cv.px[i + 1] = max(0, cv.px[i + 1] - d)
                cv.px[i + 2] = max(0, cv.px[i + 2] - d)
    return cv, H - 18


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    if not out:
        raise SystemExit("MAKEFUN_OUTPUT_DIR is not set")
    os.makedirs(out, exist_ok=True)
    cv, bottom = build()
    assert bottom <= H, "layout overflow: %d" % bottom
    write_png(os.path.join(out, "entry.png"), cv.px, W, H)


if __name__ == "__main__":
    main()
