#!/usr/bin/env python3
"""news-image-20261123 (account 2) — "The World in One Day" broadsheet.

A single front page for Monday 23 November 2026: 35 stories across 9
regions, drawn entirely in code with PIL (stdlib + Pillow only, no
network, fully deterministic). Output -> $MAKEFUN_OUTPUT_DIR/entry.png,
exactly 1024x1024.

Formula (after the news-21 winner): cream front page, big dated
masthead, stat strip, two illustrated lead stories, six briefing
cards, a dotted world map with numbered region pins, and a numbered
index of the remaining stories.
"""
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
TITLE = "Monday 23 November 2026: 35 stories, 9 regions"

CREAM = (245, 237, 220)
PAPER = (250, 244, 230)
INK = (22, 22, 22)
RED = (176, 30, 36)
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
GRAY = (110, 104, 92)
LIGHT = (232, 222, 200)
WHITE = (255, 255, 255)
DARK = (16, 24, 48)
ORANGE = (232, 120, 30)
GOLD = (240, 180, 40)
TEAL = (24, 90, 96)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    """Load a DejaVu font; fall back to PIL's built-in bitmap font."""
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    except (OSError, IOError):
        return ImageFont.load_default()


SERIF_B = lambda s: font("DejaVuSerif-Bold.ttf", s)
SERIF = lambda s: font("DejaVuSerif.ttf", s)
SERIF_I = lambda s: font("DejaVuSerif-Italic.ttf", s)
SANS_B = lambda s: font("DejaVuSans-Bold.ttf", s)
SANS = lambda s: font("DejaVuSans.ttf", s)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(draw, x, y, text, fnt, color, max_w, leading=None):
    """Draw wrapped text; returns the y just below the last line."""
    leading = leading or int(fnt.size * 1.22)
    for line in wrap(draw, text, fnt, max_w):
        draw.text((x, y), line, font=fnt, fill=color)
        y += leading
    return y


def trunc(draw, text, fnt, max_w):
    """Shorten text with an ellipsis so it fits max_w."""
    if draw.textlength(text, font=fnt) <= max_w:
        return text
    while text and draw.textlength(text + "...", font=fnt) > max_w:
        text = text[:-1]
    return text + "..."


# ---------------------------------------------------------------- stories
# (lead, card, index) — every story is dated Monday 23 November 2026.
LEADS = [
    {
        "kicker": "LEAD 1  •  CLIMATE  •  ANTALYA",
        "headline": "COP31 COLLAPSES: 'WORST EVER'",
        "deck": ("Guterres 'deeply disappointed' as oil states hijack the "
                 "talks; the final draft drops any mention of fossil fuels."),
        "art": "cop",
    },
    {
        "kicker": "LEAD 2  •  MIDDLE EAST  •  THE GULF",
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
    (9, "Global & Space", GRAY, (-150, -20)),
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


def draw_flame(draw, x, y, s):
    """Stylised flame, base at (x, y), height s."""
    draw.polygon([(x - s * 0.45, y), (x - s * 0.15, y - s * 0.55),
                  (x, y - s), (x + s * 0.2, y - s * 0.5),
                  (x + s * 0.45, y)], fill=ORANGE)
    draw.polygon([(x - s * 0.22, y), (x - s * 0.05, y - s * 0.35),
                  (x + s * 0.08, y - s * 0.55), (x + s * 0.22, y)],
                 fill=GOLD)


def draw_icon(draw, kind, cx, cy, color):
    """Small glyph for a briefing card, centred on (cx, cy)."""
    if kind == "badge":
        draw.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=color)
        draw.ellipse([cx - 11, cy - 11, cx + 11, cy + 11],
                     outline=WHITE, width=2)
        draw.text((cx - 5, cy - 8), "*", font=SANS_B(20), fill=WHITE)
    elif kind == "flame":
        draw_flame(draw, cx, cy + 14, 30)
    elif kind == "building":
        draw.rectangle([cx - 14, cy - 14, cx + 14, cy + 16], fill=color)
        for bx in (-8, 2):
            for by in (-8, 0, 8):
                draw.rectangle([cx + bx, cy + by, cx + bx + 5, cy + by + 5],
                               fill=WHITE)
        draw_flame(draw, cx + 6, cy - 12, 16)
    elif kind == "rocket":
        draw.polygon([(cx, cy - 18), (cx + 8, cy + 2), (cx + 4, cy + 12),
                      (cx, cy + 6), (cx - 4, cy + 12), (cx - 8, cy + 2)],
                     fill=color)
        draw.ellipse([cx - 4, cy - 8, cx + 4, cy], fill=WHITE)
        draw_flame(draw, cx, cy + 18, 12)
    elif kind == "file":
        draw.rectangle([cx - 11, cy - 15, cx + 11, cy + 15], fill=WHITE,
                       outline=color, width=2)
        for i, ly in enumerate((-8, -1, 6)):
            draw.line([cx - 7, cy + ly, cx + 7, cy + ly], fill=color, width=2)
    elif kind == "chip":
        draw.rectangle([cx - 13, cy - 13, cx + 13, cy + 13], fill=color)
        draw.rectangle([cx - 6, cy - 6, cx + 6, cy + 6], fill=WHITE)
        for dx in (-13, 0, 13):
            draw.line([cx + dx, cy - 18, cx + dx, cy - 13], fill=color,
                      width=3)
            draw.line([cx + dx, cy + 13, cx + dx, cy + 18], fill=color,
                      width=3)


def draw_cop_art(draw, x, y, w, h):
    """COP31 art: night sky, orange sun, summit hall, smoke, red banner."""
    draw.rectangle([x, y, x + w, y + h], fill=DARK)
    draw.ellipse([x + w - 110, y + 14, x + w - 30, y + 94], fill=ORANGE)
    for sx in (x + 60, x + 150, x + 260, x + 360):
        draw.ellipse([sx, y + 22, sx + 26, y + 48], fill=(120, 130, 150))
    # Summit hall: columns and roof.
    draw.rectangle([x + 40, y + 96, x + w - 40, y + h - 26], fill=(52, 68, 96))
    draw.polygon([(x + 20, y + 98), (x + w // 2, y + 58),
                  (x + w - 20, y + 98)], fill=(70, 88, 118))
    for i in range(6):
        cx = x + 62 + i * 62
        draw.rectangle([cx, y + 104, cx + 16, y + h - 26], fill=(200, 205, 215))
    # Chimneys with smoke on the right.
    draw.rectangle([x + w - 96, y + 78, x + w - 78, y + h - 26],
                   fill=(90, 96, 110))
    draw.rectangle([x + w - 66, y + 88, x + w - 50, y + h - 26],
                   fill=(90, 96, 110))
    for i, (dx, dy, r) in enumerate([(0, 0, 9), (10, -14, 11), (24, -26, 13)]):
        draw.ellipse([x + w - 88 + dx - r, y + 66 + dy - r,
                      x + w - 88 + dx + r, y + 66 + dy + r],
                     fill=(150, 150, 150))
    # Red FAILED banner.
    draw.rectangle([x, y + h - 26, x + w, y + h], fill=RED)
    draw.text((x + 12, y + h - 24), "TALKS COLLAPSE  •  NO DEAL",
              font=SANS_B(15), fill=WHITE)


def draw_gulf_art(draw, x, y, w, h):
    """Gulf art: grey sky, tanker on a dark sea, missile trails, fire."""
    draw.rectangle([x, y, x + w, y + h], fill=(150, 168, 186))
    draw.rectangle([x, y + h - 64, x + w, y + h], fill=(24, 52, 84))
    # Missile trails arcing down from the sky.
    for tx, bx in ((90, 150), (210, 260), (330, 380)):
        draw.line([x + tx, y + 6, x + bx, y + h - 70], fill=WHITE, width=3)
        draw.ellipse([x + bx - 5, y + h - 76, x + bx + 5, y + h - 66],
                     fill=GOLD)
    # Tanker silhouette.
    draw.rectangle([x + 40, y + h - 58, x + w - 60, y + h - 30],
                   fill=(20, 20, 24))
    for i in range(5):
        draw.rectangle([x + 56 + i * 68, y + h - 84, x + 112 + i * 68,
                        y + h - 58], fill=(200, 60, 50) if i % 2 else
                       (60, 120, 90))
    draw.rectangle([x + w - 150, y + h - 96, x + w - 110, y + h - 58],
                   fill=(220, 220, 220))
    # Fire on the waterline.
    draw_flame(draw, x + 120, y + h - 58, 26)
    draw_flame(draw, x + 300, y + h - 58, 20)
    draw.rectangle([x, y + h - 26, x + w, y + h], fill=RED)
    draw.text((x + 12, y + h - 24), "25 TANKERS HIT IN 7 DAYS",
              font=SANS_B(15), fill=WHITE)


def draw_map(draw, x, y, w, h):
    """Equirectangular world map with numbered region pins + legend."""
    draw.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=2)

    def proj(lon, lat):
        px = x + (lon + 180.0) / 360.0 * w
        py = y + (90.0 - lat) / 180.0 * h
        return (px, py)

    # Graticule every 30 degrees.
    for lon in range(-150, 181, 30):
        px, _ = proj(lon, 0)
        draw.line([px, y, px, y + h], fill=(190, 208, 220), width=1)
    for lat in range(-60, 91, 30):
        _, py = proj(0, lat)
        draw.line([x, py, x + w, py], fill=(190, 208, 220), width=1)
    # Continents.
    for poly in CONTINENTS:
        draw.polygon([proj(lon, lat) for lon, lat in poly], fill=LAND,
                     outline=LAND_EDGE)
    # Region pins: coloured disc, white number.
    for num, name, color, (lon, lat) in REGIONS:
        px, py = proj(lon, lat)
        draw.ellipse([px - 11, py - 11, px + 11, py + 11], fill=color,
                     outline=WHITE, width=2)
        tw = draw.textlength(str(num), font=SANS_B(13))
        draw.text((px - tw / 2, py - 9), str(num), font=SANS_B(13),
                  fill=WHITE)
    # Legend strip at the bottom of the map.
    ly = y + h - 52
    draw.rectangle([x, ly, x + w, y + h], fill=PAPER)
    draw.line([x, ly, x + w, ly], fill=INK, width=1)
    cols = 3
    for i, (num, name, color, _loc) in enumerate(REGIONS):
        cx = x + 10 + (i % cols) * (w // cols)
        cy = ly + 6 + (i // cols) * 16
        draw.ellipse([cx, cy, cx + 12, cy + 12], fill=color)
        tw = draw.textlength(str(num), font=SANS_B(9))
        draw.text((cx + 6 - tw / 2, cy - 1), str(num), font=SANS_B(9),
                  fill=WHITE)
        draw.text((cx + 17, cy), name, font=SANS(10), fill=INK)


def main():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    # Double outer rule.
    d.rectangle([10, 10, W - 11, H - 11], outline=INK, width=2)
    d.rectangle([16, 16, W - 17, H - 17], outline=INK, width=1)

    # ---------------------------------------------------------- masthead
    d.text((W // 2 - d.textlength("THE WORLD IN ONE DAY  •  EST. EVERY MORNING",
                                  font=SANS_B(13)) / 2, 26),
           "THE WORLD IN ONE DAY  •  EST. EVERY MORNING",
           font=SANS_B(13), fill=GRAY)
    title = "THE WORLD IN ONE DAY"
    d.text((W // 2 - d.textlength(title, font=SERIF_B(52)) / 2, 44),
           title, font=SERIF_B(52), fill=INK)
    d.line([24, 106, W - 24, 106], fill=RED, width=4)
    date = "MONDAY 23 NOVEMBER 2026"
    d.text((W // 2 - d.textlength(date, font=SERIF_B(34)) / 2, 114),
           date, font=SERIF_B(34), fill=RED)
    sub = "35 stories  |  9 regions  -  the whole world on one page"
    d.text((W // 2 - d.textlength(sub, font=SERIF_I(16)) / 2, 152),
           sub, font=SERIF_I(16), fill=INK)

    # -------------------------------------------------------- stat strip
    stats = [("35", "STORIES"), ("9", "REGIONS"), ("2", "LEADS"),
             ("6", "BRIEFINGS"), ("27", "IN THE INDEX"), ("1", "DAY")]
    sx, sy, sw, sh = 24, 176, 160, 40
    for i, (num, label) in enumerate(stats):
        bx = sx + i * (sw + 3)
        d.rectangle([bx, sy, bx + sw, sy + sh], fill=NAVY)
        d.text((bx + sw // 2 - d.textlength(num, font=SERIF_B(20)) / 2,
                sy + 2), num, font=SERIF_B(20), fill=WHITE)
        d.text((bx + sw // 2 - d.textlength(label, font=SANS_B(9)) / 2,
                sy + 25), label, font=SANS_B(9), fill=GOLD)

    # ------------------------------------------------------------- leads
    ly = 228
    lw, lh = 476, 252
    for i, lead in enumerate(LEADS):
        lx = 24 + i * (lw + 24)
        d.rectangle([lx, ly, lx + lw, ly + lh], fill=PAPER, outline=INK,
                    width=1)
        if lead["art"] == "cop":
            draw_cop_art(d, lx + 1, ly + 1, lw - 2, 132)
        else:
            draw_gulf_art(d, lx + 1, ly + 1, lw - 2, 132)
        ty = ly + 140
        d.text((lx + 12, ty), lead["kicker"], font=SANS_B(11), fill=RED)
        ty = para(d, lx + 12, ty + 18, lead["headline"], SERIF_B(24),
                  INK, lw - 24, leading=27)
        para(d, lx + 12, ty + 2, lead["deck"], SANS(12), INK, lw - 24,
             leading=16)

    # ------------------------------------------------------------ cards
    cy = 492
    d.text((24, cy), "BRIEFINGS", font=SANS_B(13), fill=RED)
    d.line([130, cy + 8, W - 24, cy + 8], fill=INK, width=1)
    cw, chh, gap = 320, 62, 8
    for i, (num, region, head, kind) in enumerate(CARDS):
        cx = 24 + (i % 3) * (cw + gap)
        cyy = cy + 20 + (i // 3) * (chh + gap)
        d.rectangle([cx, cyy, cx + cw, cyy + chh], fill=WHITE,
                    outline=INK, width=1)
        d.rectangle([cx, cyy, cx + 34, cyy + chh], fill=LIGHT)
        tw = d.textlength(num, font=SERIF_B(20))
        d.text((cx + 17 - tw / 2, cyy + 6), num, font=SERIF_B(20),
               fill=RED)
        d.text((cx + 17 - d.textlength(region, font=SANS_B(7)) / 2,
                cyy + 34), region, font=SANS_B(7), fill=INK)
        draw_icon(d, kind, cx + 56, cyy + chh // 2,
                  [RED, ORANGE, NAVY, PURPLE, BLUE, TEAL][i])
        para(d, cx + 82, cyy + 8, head, SANS_B(12), INK, cw - 92,
             leading=15)

    # ------------------------------------------------- map + index
    by = 656
    d.text((24, by), "WORLD MAP  •  WHERE IT HAPPENED", font=SANS_B(13),
           fill=RED)
    d.line([300, by + 8, 624, by + 8], fill=INK, width=1)
    d.text((640, by), "THE INDEX  •  STORIES 9–35", font=SANS_B(13),
           fill=RED)
    d.line([872, by + 8, W - 24, by + 8], fill=INK, width=1)
    draw_map(d, 24, by + 22, 600, 310)
    ix, iy, iw, ih = 640, by + 22, 360, 310
    d.rectangle([ix, iy, ix + iw, iy + ih], fill=PAPER, outline=INK,
                width=1)
    col_w = iw // 2
    fnt = SANS(10)
    for j, item in enumerate(INDEX):
        col = j // 14
        row = j % 14
        tx = ix + 10 + col * col_w
        tyy = iy + 10 + row * 21
        label = "%d. %s" % (j + 9, item)
        d.text((tx, tyy), trunc(d, label, fnt, col_w - 14), font=fnt,
               fill=INK)
    d.text((24, H - 30),
           "All stories dated Monday 23 November 2026  •  Wires to 08:55 WITA  •  Drawn in code",
           font=SANS(11), fill=GRAY)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if not out_dir:
        raise SystemExit("MAKEFUN_OUTPUT_DIR is not set")
    os.makedirs(out_dir, exist_ok=True)
    img.save(os.path.join(out_dir, "entry.png"), format="PNG",
             optimize=True)


if __name__ == "__main__":
    main()
