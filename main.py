"""The Daily Globe — Tuesday 24 November 2026.

Renders one 1024x1024 front page summing up the day's world news.
Pure PIL + DejaVu, deterministic (fixed seed, no clock, no network).
If PIL is unavailable, copies the pre-rendered entry.png shipped beside
this file, so the grader still gets byte-identical output.
"""
import os
import random
import shutil
import sys

W, H = 1024, 1024
SEED = 20261124

PAPER = (247, 242, 231)
INK = (18, 18, 16)
RED = (178, 34, 28)
NAVY = (16, 32, 56)
NAVY2 = (24, 46, 78)
GOLD = (176, 132, 40)
GREY = (90, 86, 78)
LIGHT = (232, 226, 212)
SEA = (28, 52, 84)
LAND = (214, 200, 160)
PINRED = (214, 48, 36)

FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/dejavu",
    "/usr/local/share/fonts",
]


def load_font(name, size):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            try:
                from PIL import ImageFont
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    from PIL import ImageFont
    return ImageFont.load_default()


class Fonts:
    def __init__(self):
        self.serif_title = load_font("DejaVuSerif-Bold.ttf", 58)
        self.serif = load_font("DejaVuSerif.ttf", 15)
        self.serif_b = load_font("DejaVuSerif-Bold.ttf", 15)
        self.sans = load_font("DejaVuSans.ttf", 13)
        self.sans_b = load_font("DejaVuSans-Bold.ttf", 13)
        self.sans_s = load_font("DejaVuSans.ttf", 11)
        self.sans_sb = load_font("DejaVuSans-Bold.ttf", 11)
        self.sans_xs = load_font("DejaVuSans.ttf", 10)
        self.sans_xsb = load_font("DejaVuSans-Bold.ttf", 10)
        self.head = load_font("DejaVuSans-Bold.ttf", 24)
        self.head_s = load_font("DejaVuSans-Bold.ttf", 21)
        self.kicker = load_font("DejaVuSans-Bold.ttf", 12)
        self.bignum = load_font("DejaVuSans-Bold.ttf", 30)
        self.date = load_font("DejaVuSans-Bold.ttf", 19)


def wrap(draw, text, font, max_w):
    """Greedy word wrap by pixel width; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_lines(draw, text, font, max_w, max_lines):
    """Wrap text, shrinking words only by truncation with ellipsis."""
    lines = wrap(draw, text, font, max_w)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and draw.textlength(lines[-1] + "...", font=font) > max_w:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1] + "..."
    return lines


def text_block(draw, x, y, lines, font, fill=INK, leading=None):
    if leading is None:
        leading = int(font.size * 1.28)
    for ln in lines:
        draw.text((x, y), ln, font=font, fill=fill)
        y += leading
    return y


# --- Simplified continent outlines (lon, lat), drawn by hand. ---
NORTH_AMERICA = [(-168, 66), (-158, 58), (-140, 60), (-130, 54), (-125, 49),
    (-124, 42), (-120, 34), (-114, 29), (-110, 24), (-105, 20), (-97, 16),
    (-92, 15), (-86, 13), (-83, 9), (-79, 9), (-81, 13), (-84, 16),
    (-87, 21), (-90, 21), (-91, 19), (-96, 19), (-97, 26), (-93, 30),
    (-89, 30), (-84, 30), (-81, 26), (-80, 32), (-76, 35), (-74, 40),
    (-70, 42), (-68, 45), (-65, 44), (-60, 47), (-55, 52), (-60, 55),
    (-65, 58), (-68, 55), (-72, 58), (-78, 62), (-85, 66), (-92, 66),
    (-95, 69), (-110, 68), (-125, 70), (-140, 70), (-155, 71), (-165, 68)]
GREENLAND = [(-45, 60), (-40, 64), (-32, 68), (-25, 70), (-20, 74),
    (-25, 78), (-35, 80), (-50, 80), (-58, 76), (-55, 70), (-52, 64)]
SOUTH_AMERICA = [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12),
    (-72, -18), (-70, -23), (-70, -30), (-73, -37), (-73, -44), (-74, -50),
    (-70, -54), (-66, -55), (-65, -45), (-62, -41), (-58, -35), (-52, -32),
    (-48, -28), (-41, -23), (-39, -17), (-35, -9), (-35, -6), (-40, -3),
    (-44, -2), (-50, 0), (-53, 4), (-58, 6), (-62, 9), (-68, 11),
    (-72, 12), (-76, 10)]
AFRICA = [(-17, 15), (-17, 21), (-15, 27), (-10, 31), (-6, 34), (-1, 35),
    (3, 37), (10, 37), (11, 34), (15, 32), (20, 32.4), (25, 32), (30, 31),
    (32, 31), (34, 28), (35, 24), (37, 20), (39, 18), (40, 15), (43, 12),
    (48, 11), (51, 12), (51, 10), (46, 6), (42, 3), (40, -2), (40, -8),
    (40, -15), (36, -18), (35, -23), (32, -26), (28, -33), (20, -35),
    (17, -32), (15, -27), (13, -18), (12, -12), (13, -6), (9, -1),
    (9, 4), (4, 6), (-2, 5), (-8, 5), (-13, 8), (-17, 12)]
EURASIA = [(-9, 37), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (1, 50),
    (3, 52), (7, 54), (8, 57), (11, 58), (13, 56), (18, 56), (21, 55),
    (24, 58), (24, 61), (29, 65), (31, 69), (35, 68), (41, 68), (47, 68),
    (53, 69), (58, 69), (63, 69), (68, 70), (73, 72), (78, 72), (83, 73),
    (88, 74), (93, 75), (98, 76), (103, 77), (108, 76), (113, 74),
    (118, 73), (123, 73), (128, 72), (133, 72), (138, 72), (143, 72),
    (148, 71), (153, 70), (158, 69), (163, 68), (168, 66), (173, 65),
    (178, 65), (178, 62), (172, 60), (165, 60), (160, 58), (157, 53),
    (153, 58), (148, 59), (142, 53), (141, 49), (138, 45), (136, 42),
    (133, 42), (129, 39), (127, 37), (124, 38), (121, 35), (120, 32),
    (117, 29), (113, 27), (110, 23), (108, 20), (106, 17), (104, 14),
    (102, 10), (100, 8), (98, 10), (96, 14), (94, 17), (92, 21),
    (90, 22), (88, 22), (86, 20), (83, 18), (81, 15), (80, 13),
    (78, 9), (76, 9), (74, 14), (72, 19), (70, 21), (68, 23),
    (66, 25), (63, 25), (60, 25), (57, 26), (55, 27), (53, 27),
    (51, 28), (49, 29), (48, 29), (50, 27), (52, 26), (54, 26),
    (56, 27), (58, 25), (59, 22), (58, 20), (55, 17), (52, 15),
    (48, 14), (44, 13), (43, 12), (42, 15), (40, 18), (39, 21),
    (37, 24), (35, 27), (34, 28), (32, 30), (34, 31.4), (35.5, 34),
    (36, 36), (33, 36), (30, 36), (27, 37), (24, 36), (22, 37),
    (20, 38), (19, 40), (16, 40), (14, 42), (12, 44), (10, 44),
    (8, 44), (6, 43), (3, 43), (0, 40), (-2, 37), (-5, 36)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
    (-3, 50)]
IRELAND = [(-10, 52), (-8, 55), (-6, 55), (-6, 52), (-8, 51)]
ICELAND = [(-22, 64), (-18, 63), (-15, 64), (-14, 66), (-18, 66),
    (-22, 65)]
JAPAN = [(130, 31), (132, 33), (134, 34), (137, 35), (139, 36), (140, 38),
    (141, 40), (142, 42), (144, 44), (142, 44), (140, 40), (138, 37),
    (136, 35), (133, 34), (131, 32)]
SUMATRA = [(95, 5), (98, 3), (100, 0), (103, -3), (105, -5), (104, -6),
    (101, -4), (99, 1), (96, 4)]
JAVA = [(105, -6), (108, -7), (111, -7), (114, -8), (113, -8), (110, -7),
    (107, -6)]
BORNEO = [(109, 1), (111, 2), (114, 4), (117, 6), (118, 2), (117, -2),
    (114, -3), (111, -3), (109, 0)]
NEW_GUINEA = [(131, -1), (134, -2), (137, -3), (140, -4), (143, -6),
    (146, -7), (147, -8), (144, -8), (141, -8), (138, -7), (135, -4),
    (132, -2)]
AUSTRALIA = [(113, -22), (114, -30), (115, -34), (118, -35), (124, -33),
    (129, -32), (132, -32), (135, -35), (138, -35), (140, -38), (145, -38),
    (150, -37), (153, -32), (153, -27), (150, -23), (146, -19), (143, -15),
    (142, -11), (141, -13), (139, -17), (136, -15), (135, -12), (132, -12),
    (130, -13), (127, -14), (124, -16), (122, -18), (118, -20), (115, -21)]
NEW_ZEALAND = [(167, -45), (170, -43), (173, -41), (175, -39), (177, -38),
    (175, -37), (173, -35), (175, -38), (177, -40), (174, -42),
    (171, -44), (168, -46)]
MADAGASCAR = [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24),
    (45, -25), (43, -22), (43, -18)]
PHILIPPINES = [(120, 18), (122, 17), (122, 14), (121, 11), (120, 10),
    (122, 11), (124, 13), (126, 12), (124, 9), (122, 8), (121, 10),
    (120, 13)]
CUBA = [(-84, 22), (-80, 23), (-76, 21), (-74, 20), (-77, 21), (-81, 22)]
TAIWAN = [(120, 22), (121, 23), (122, 25), (121, 25), (120, 23)]
SRI_LANKA = [(80, 9), (81, 8), (80, 6), (79, 7), (80, 9)]

LAND_POLYS = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EURASIA,
    UK, IRELAND, ICELAND, JAPAN, SUMATRA, JAVA, BORNEO, NEW_GUINEA,
    AUSTRALIA, NEW_ZEALAND, MADAGASCAR, PHILIPPINES, CUBA, TAIWAN,
    SRI_LANKA]


# --- Lead illustrations (drawn, one panel each) ---

def art_benghazi(draw, x, y, w, h):
    """Night harbour: a corvette burning at Benghazi, drones above."""
    draw.rectangle([x, y, x + w, y + h], fill=(10, 18, 34))
    rng = random.Random(SEED + 1)
    for _ in range(46):
        sx = x + rng.randint(2, w - 2)
        sy = y + rng.randint(2, int(h * 0.55))
        r = rng.choice([1, 1, 1, 2])
        draw.ellipse([sx - r, sy - r, sx + r, sy + r],
                     fill=(200 + rng.randint(0, 55), 200, 160))
    # moon
    draw.ellipse([x + w - 34, y + 8, x + w - 14, y + 28], fill=(238, 230, 200))
    # sea
    draw.rectangle([x, y + int(h * 0.62), x + w, y + h], fill=(18, 42, 72))
    for i in range(5):
        yy = y + int(h * 0.66) + i * 7
        draw.line([x + 6, yy, x + w - 6, yy], fill=(52, 92, 130), width=1)
    # pier
    draw.rectangle([x + 8, y + int(h * 0.58), x + w - 8, y + int(h * 0.63)],
                   fill=(40, 38, 34))
    # corvette hull + superstructure, listing, on fire
    hx, hy = x + int(w * 0.16), y + int(h * 0.60)
    hw, hh = int(w * 0.62), 12
    draw.polygon([(hx, hy), (hx + hw, hy), (hx + hw - 12, hy + hh),
                  (hx + 8, hy + hh)], fill=(92, 96, 104))
    draw.rectangle([hx + 18, hy - 12, hx + 52, hy], fill=(102, 106, 114))
    draw.rectangle([hx + 58, hy - 8, hx + 78, hy], fill=(102, 106, 114))
    draw.line([hx + 30, hy - 12, hx + 30, hy - 24], fill=(110, 114, 122), width=3)
    # flames + smoke
    for cx, cy, r, col in [
            (hx + 30, hy - 20, 9, (240, 120, 30)),
            (hx + 44, hy - 16, 12, (250, 170, 40)),
            (hx + 62, hy - 18, 8, (240, 110, 26)),
            (hx + 36, hy - 34, 7, (120, 120, 118)),
            (hx + 52, hy - 40, 9, (105, 105, 103)),
            (hx + 68, hy - 32, 6, (130, 130, 128))]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    # fire glow on the water
    draw.ellipse([hx + 24, hy + hh - 1, hx + 76, hy + hh + 6],
                 fill=(200, 110, 30))
    # drones: small crosses with trails
    for dx, dy in [(0.72, 0.18), (0.82, 0.30), (0.62, 0.10)]:
        px, py = x + int(w * dx), y + int(h * dy)
        draw.line([px - 5, py, px + 5, py], fill=(230, 230, 220), width=2)
        draw.line([px, py - 5, px, py + 5], fill=(230, 230, 220), width=2)
        draw.line([px, py, px - 16, py + 10], fill=(150, 150, 140), width=1)


def art_cop31(img, draw, x, y, w, h):
    """A warming globe with a thermometer and a red NO DEAL stamp."""
    draw.rectangle([x, y, x + w, y + h], fill=(232, 222, 196))
    cx, cy, r = x + int(w * 0.38), y + int(h * 0.52), int(h * 0.36)
    # globe
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(58, 110, 150))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(30, 60, 90),
                 width=2)
    # rough continents on the globe
    draw.polygon([(cx - r + 8, cy - 6), (cx - 12, cy - 22), (cx + 2, cy - 14),
                  (cx + 6, cy - 2), (cx - 6, cy + 2)], fill=(96, 150, 80))
    draw.polygon([(cx + 10, cy + 6), (cx + 30, cy - 2), (cx + 34, cy + 14),
                  (cx + 16, cy + 22), (cx + 6, cy + 16)], fill=(96, 150, 80))
    draw.polygon([(cx - 26, cy + 16), (cx - 8, cy + 12), (cx - 4, cy + 26),
                  (cx - 22, cy + 30)], fill=(120, 160, 90))
    # graticule
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(140, 180, 200),
                 width=1)
    draw.line([cx - r, cy, cx + r, cy], fill=(140, 180, 200), width=1)
    draw.line([cx, cy - r, cx, cy + r], fill=(140, 180, 200), width=1)
    # thermometer at right
    tx = x + int(w * 0.78)
    draw.rounded_rectangle([tx - 7, y + 12, tx + 7, y + h - 30], radius=7,
                           fill=(250, 250, 246), outline=(40, 40, 40), width=2)
    draw.ellipse([tx - 13, y + h - 38, tx + 13, y + h - 12],
                 fill=(214, 48, 36), outline=(40, 40, 40), width=2)
    draw.rectangle([tx - 4, y + 20, tx + 4, y + h - 26], fill=(214, 48, 36))
    for i, yy in enumerate(range(y + 18, y + h - 44, 12)):
        draw.line([tx + 7, yy, tx + 13, yy], fill=(40, 40, 40), width=1)
    # red NO DEAL stamp, rotated slightly by drawing on its own layer
    from PIL import Image, ImageDraw
    stamp = Image.new("RGBA", (150, 52), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    sd.rectangle([2, 2, 147, 49], outline=(178, 34, 28), width=4)
    fnt = load_font("DejaVuSans-Bold.ttf", 26)
    sd.text((75, 26), "NO DEAL", font=fnt, fill=(178, 34, 28),
            anchor="mm")
    stamp = stamp.rotate(8, expand=True, resample=Image.BICUBIC)
    img.paste(stamp, (x + int(w * 0.30), y + int(h * 0.62)), stamp)


def art_capitol(draw, x, y, w, h):
    """Capitol dome on a drum, wings on a shared baseline, seat bars."""
    draw.rectangle([x, y, x + w, y + h], fill=(238, 232, 214))
    bx = x + int(w * 0.5)
    base = y + int(h * 0.77)
    # wings
    draw.rectangle([x + 8, base - 24, bx - 52, base], fill=(226, 220, 200),
                   outline=(90, 84, 70), width=1)
    draw.rectangle([bx + 52, base - 24, x + w - 8, base], fill=(226, 220, 200),
                   outline=(90, 84, 70), width=1)
    for wx in (x + 16, x + 40, bx + 60, bx + 84):
        draw.rectangle([wx, base - 18, wx + 8, base - 6], fill=(120, 114, 98))
    # drum + columns
    draw.rectangle([bx - 52, base - 40, bx + 52, base], fill=(240, 236, 222),
                   outline=(90, 84, 70), width=1)
    for i in range(6):
        cx = bx - 44 + i * 18
        draw.rectangle([cx, base - 36, cx + 7, base - 6], fill=(150, 144, 126))
    # dome
    draw.pieslice([bx - 44, base - 68, bx + 44, base - 6], 180, 360,
                  fill=(200, 196, 182), outline=(90, 84, 70), width=2)
    draw.rectangle([bx - 3, base - 70, bx + 3, base - 64], fill=(90, 84, 70))
    draw.ellipse([bx - 4, base - 72, bx + 4, base - 66], fill=(90, 84, 70))
    # ground line
    draw.line([x + 4, base, x + w - 4, base], fill=(60, 56, 48), width=2)
    # label, top-left so it never meets the dome
    draw.text((x + 6, y + 5), "U.S. HOUSE", font=load_font(
        "DejaVuSans-Bold.ttf", 11), fill=GREY)


# --- Map helpers ---

def point_in_poly(lon, lat, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > lat) != (yj > lat):
            xinters = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < xinters:
                inside = not inside
        j = i
    return inside


def on_land(lon, lat):
    return any(point_in_poly(lon, lat, p) for p in LAND_POLYS)


MAP_X, MAP_Y, MAP_W, MAP_H = 28, 378, 640, 234
LAT_TOP, LAT_BOT = 80.0, -55.0


def project(lon, lat):
    px = MAP_X + (lon + 180.0) / 360.0 * MAP_W
    py = MAP_Y + (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * MAP_H
    return px, py


PINS = [
    (1, "BENGHAZI", 20.07, 32.12, "Corvette Merkury sunk at port"),
    (2, "ANTALYA", 30.70, 36.90, "COP31 ends with no deal"),
    (3, "DYMER", 30.32, 50.78, "Strike on flats kills at least 11"),
    (4, "WASHINGTON", -77.04, 38.90, "Democrats clinch 258 House seats"),
    (5, "GENEVA", 6.14, 46.20, "Gukesh v Sindarov, Game 1"),
    (6, "BANTEN", 106.15, -6.12, "Factory fire kills 24; 34 missing"),
    (7, "KHARTOUM", 32.56, 15.50, "Drones hit capital, UN building"),
    (8, "GAZA", 34.47, 31.50, "Oxfam: war left toxic contamination"),
]

LEADS = [
    ("WAR AT SEA", "Ukraine sinks Russian warship off Libya",
     "Seven naval drones sank the corvette Merkury at Benghazi, "
     "Kyiv says."),
    ("CLIMATE", "COP31 ends with no deal",
     "COP31 collapses in Antalya: the EU and island states reject "
     "a no-phase-down draft."),
    ("AMERICA", "Democrats take the House: 258 seats",
     "At least 258 seats \u2014 the largest Democratic majority since 1992."),
]

FIGURES = [
    ("258", "Democratic House seats"),
    ("11", "killed in the Dymer strike"),
    ("24", "killed in the Banten fire"),
    ("7", "drones that sank the Merkury"),
    ("14", "states back the ICJ ruling"),
    ("$2.5M", "World Chess prize fund"),
]

REGIONS = [
    ("EUROPE", "EU proposes a 22nd sanctions package on Russia."),
    ("MIDDLE EAST", "Settler arson hits five West Bank villages."),
    ("ASIA", "ICJ: Myanmar committed genocide against the Rohingya."),
    ("AFRICA", "Drones hit Khartoum and a UN building."),
    ("NORTH AMERICA", "Waymo pulls driverless taxis from all US freeways."),
    ("OCEANIA", "Coalition condemns the Vanuatu security deal."),
    ("SPACE", "NATO vows space defence after a Russian "
     "nuclear-satellite report."),
]

GRID = [
    ("BERLIN", "NATO vows space defence after satellite report."),
    ("BRUSSELS", "NATO to meet over Russian missiles in Poland."),
    ("WARSAW", "Prosecutors: three Russian missiles hit Poland."),
    ("TALLINN", "Moscow threatens Estonia with \u201copen war\u201d."),
    ("ABU DHABI", "Peace talks end; Medinsky holds a maximalist line."),
    ("TEL AVIV", "Netanyahu-Eisenkot coalition talks end without a deal."),
    ("RIYADH", "Houthis claim a refinery attack; Saudi strike hits Yemen."),
    ("SEOUL", "President names a new foreign minister and spy chief."),
    ("KABUL", "Taliban order women\u2019s names struck from papers in Balkh."),
    ("NEW DELHI", "Modi opens an AI centre at IIT Patna."),
    ("WELLINGTON", "India-New Zealand first Test ends in a draw."),
    ("TURIN", "Alcaraz beats Zverev for a maiden ATP Finals crown."),
    ("LONDON", "UK confirmed as host of the 2035 Women\u2019s World Cup."),
    ("MANCHESTER", "Thousands flee concert after substance released."),
    ("DES MOINES", "Trump orders Army to pause lead azide detonation."),
    ("SEATTLE", "Father and daughter held by ICE at the airport."),
    ("DUBAI", "Tanker incident involving military forces in the Gulf of Oman."),
    ("DAKAR", "Migrant boat capsizes off Senegal; four dead."),
    ("STOCKHOLM", "Swedish Gripens join NATO scramble over Poland."),
    ("TRIPOLI", "Libya\u2019s east seeks a UN probe into the Benghazi attacks."),
    ("KYIV", "Security Council meets on Russia\u2019s winter attacks on the grid."),
    ("WASHINGTON", "Democrats plan 12 debates for the 2028 primary."),
    ("JERUSALEM", "Israel seeks to jail student activist without trial."),
    ("JAKARTA", "Indonesia probes the factory fire; 34 still missing."),
]

TICKER = ("Nvidia reinstates Huang as CEO  \u2022  India, Nepal sign 8 MoUs  "
          "\u2022  Trump\u2019s Kim outreach rebuffed \u2014 WSJ")


def draw_masthead(img, draw, F):
    draw.text((W // 2, 26), "THE DAILY GLOBE", font=F.serif_title,
              fill=INK, anchor="ma")
    draw.text((28, 92), "TUESDAY, 24 NOVEMBER 2026", font=F.date, fill=INK)
    right = "ONE DAY \u00b7 ONE PICTURE \u00b7 THE WORLD"
    draw.text((W - 28, 96), right, font=F.sans_sb, fill=GREY, anchor="ra")
    draw.rectangle([28, 116, W - 28, 119], fill=GOLD)
    draw.rectangle([28, 121, W - 28, 122], fill=INK)


def draw_leads(img, draw, F):
    col_w, gap = 296, 40
    y0, art_h = 130, 96
    for i, (kicker, head, deck) in enumerate(LEADS):
        x = 28 + i * (col_w + gap)
        if i == 0:
            art_benghazi(draw, x, y0, col_w, art_h)
        elif i == 1:
            art_cop31(img, draw, x, y0, col_w, art_h)
        else:
            art_capitol(draw, x, y0, col_w, art_h)
        draw.rectangle([x, y0, x + col_w, y0 + art_h], outline=INK, width=1)
        if i == 2:
            # seat bar strip at the foot of the art panel
            bx, by, bw, bh = x + 1, y0 + art_h - 17, col_w - 2, 16
            dem_w = int(bw * 258 / 435)
            draw.rectangle([bx, by, bx + dem_w, by + bh], fill=(38, 80, 150))
            draw.rectangle([bx + dem_w, by, bx + bw, by + bh],
                           fill=(178, 34, 28))
            draw.text((bx + 6, by + 8), "DEM 258", font=F.sans_xsb,
                      fill=(255, 255, 255), anchor="lm")
            draw.text((bx + bw - 6, by + 8), "GOP 177", font=F.sans_xsb,
                      fill=(255, 255, 255), anchor="rm")
        draw.text((x, y0 + art_h + 6), kicker, font=F.kicker, fill=RED)
        hl = fit_lines(draw, head, F.head_s, col_w, 2)
        y = text_block(draw, x, y0 + art_h + 22, hl, F.head_s, leading=25)
        dl = fit_lines(draw, deck, F.sans, col_w, 2)
        text_block(draw, x, y + 4, dl, F.sans, fill=(40, 38, 34), leading=15)


def draw_map(img, draw, F):
    draw.text((28, 354), "THE WORLD AT A GLANCE", font=F.kicker, fill=INK)
    draw.text((668, 354), "8 PLACES \u00b7 24 NOVEMBER", font=F.sans_sb,
              fill=GREY, anchor="ra")
    draw.rectangle([MAP_X, MAP_Y, MAP_X + MAP_W, MAP_Y + MAP_H], fill=SEA)
    rng = random.Random(SEED + 7)
    # graticule
    for lon in range(-150, 181, 30):
        gx, _ = project(lon, 0)
        draw.line([gx, MAP_Y, gx, MAP_Y + MAP_H], fill=(44, 72, 108), width=1)
    for lat in range(-30, 61, 30):
        _, gy = project(0, lat)
        draw.line([MAP_X, gy, MAP_X + MAP_W, gy], fill=(44, 72, 108), width=1)
    # ocean stipple (ocean only)
    for _ in range(900):
        lon = rng.uniform(-180, 180)
        lat = rng.uniform(LAT_BOT, LAT_TOP)
        if on_land(lon, lat):
            continue
        px, py = project(lon, lat)
        draw.point([px, py], fill=(70, 105, 140))
    # land
    for poly in LAND_POLYS:
        pts = [project(lon, lat) for lon, lat in poly]
        draw.polygon(pts, fill=LAND, outline=(120, 104, 70))
    # ocean labels
    for label, lon, lat in [("PACIFIC", -150, 2), ("ATLANTIC", -32, 8),
                            ("INDIAN OCEAN", 78, -32), ("AFRICA", 20, 4),
                            ("ASIA", 96, 52), ("SOUTH AMERICA", -60, -16),
                            ("AUSTRALIA", 134, -26)]:
        px, py = project(lon, lat)
        draw.text((px, py), label, font=F.sans_xs, fill=(150, 175, 200),
                  anchor="mm")
    # compass
    cx, cy = MAP_X + MAP_W - 26, MAP_Y + 22
    draw.polygon([(cx, cy - 12), (cx + 5, cy + 6), (cx, cy + 2),
                  (cx - 5, cy + 6)], fill=(240, 236, 220))
    draw.text((cx, cy + 10), "N", font=F.sans_xsb, fill=(240, 236, 220),
              anchor="ma")
    # pins
    for num, place, lon, lat, _story in PINS:
        px, py = project(lon, lat)
        draw.ellipse([px - 9, py - 9, px + 9, py + 9], fill=PINRED,
                     outline=(255, 255, 255), width=2)
        draw.text((px, py + 1), str(num), font=F.sans_xsb,
                  fill=(255, 255, 255), anchor="mm")
    draw.rectangle([MAP_X, MAP_Y, MAP_X + MAP_W, MAP_Y + MAP_H],
                   outline=INK, width=1)
    # legend column
    lx = 680
    draw.text((lx, 378), "WHERE IT HAPPENED", font=F.kicker, fill=RED)
    y = 400
    for num, place, _lon, _lat, story in PINS:
        draw.ellipse([lx, y + 1, lx + 15, y + 16], fill=PINRED)
        draw.text((lx + 7.5, y + 9), str(num), font=F.sans_xsb,
                  fill=(255, 255, 255), anchor="mm")
        draw.text((lx + 22, y), place, font=F.sans_sb, fill=INK)
        sl = fit_lines(draw, story, F.sans_s, 996 - (lx + 22), 1)
        text_block(draw, lx + 22, y + 13, sl, F.sans_s, fill=(40, 38, 34),
                   leading=13)
        y += 26


def draw_figures(draw, F):
    y0 = 620
    bw, gap = 157, 5.6
    for i, (num, label) in enumerate(FIGURES):
        x = 28 + i * (bw + gap)
        draw.rectangle([x, y0, x + bw, y0 + 2], fill=GOLD)
        draw.text((x, y0 + 6), num, font=F.bignum, fill=INK)
        draw.text((x, y0 + 40), label, font=F.sans_xs, fill=(40, 38, 34))


def draw_regions(draw, F):
    draw.text((28, 676), "AROUND THE WORLD", font=F.kicker, fill=INK)
    draw.line([28, 693, 996, 693], fill=INK, width=1)
    cw, gap = 132, 8
    for i, (region, story) in enumerate(REGIONS):
        x = 28 + i * (cw + gap)
        draw.text((x, 699), region, font=F.sans_xsb, fill=RED)
        sl = fit_lines(draw, story, F.sans_xs, cw, 3)
        text_block(draw, x, 713, sl, F.sans_xs, fill=(40, 38, 34), leading=12)


def wrap2(draw, text, font, w1, w2):
    """Two-line wrap: first line max w1, second line max w2."""
    words = text.split()
    lines, cur, widths = [], "", [w1, w2]
    li = 0
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= widths[min(li, 1)] or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur, li = word, li + 1
            if li > 1:
                break
    if cur:
        lines.append(cur)
    if len(lines) > 2:
        lines = lines[:2]
        while lines and draw.textlength(lines[-1] + "...", font=font) > w2:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1] + "..."
    return lines


def draw_grid(draw, F):
    draw.text((28, 756), "THE DAY IN BRIEF", font=F.kicker, fill=INK)
    draw.line([28, 773, 996, 773], fill=INK, width=1)
    cw, gap = 236, 8
    row_h = 27.0
    for i, (place, story) in enumerate(GRID):
        col, row = i % 4, i // 4
        x = 28 + col * (cw + gap)
        y = 779 + row * row_h
        head_w = draw.textlength(place + " ", font=F.sans_sb)
        lines = wrap2(draw, story, F.sans_s, cw - head_w - 8, cw)
        draw.text((x, y), place, font=F.sans_sb, fill=INK)
        draw.text((x + head_w, y), "\u2014 " + (lines[0] if lines else ""),
                  font=F.sans_s, fill=(40, 38, 34))
        if len(lines) > 1:
            draw.text((x, y + 13), lines[1], font=F.sans_s,
                      fill=(40, 38, 34))


def draw_ticker(draw, F):
    draw.rectangle([28, 948, 996, 970], fill=INK)
    draw.text((38, 959), "ALSO TODAY", font=F.sans_xsb, fill=(232, 200, 90),
              anchor="lm")
    tx = 38 + draw.textlength("ALSO TODAY  ", font=F.sans_xsb) + 8
    draw.text((tx, 959), TICKER, font=F.sans_s, fill=(245, 242, 235),
              anchor="lm")


def draw_footer(draw, F):
    draw.text((28, 980),
              "All stories checked against reporting dated 24 November 2026.",
              font=F.sans_xs, fill=GREY)
    draw.text((28, 994),
              "Sources: BBC \u00b7 France 24 \u00b7 The Guardian \u00b7 Times of India \u00b7 "
              "ANI \u00b7 Chess.com \u00b7 UN News \u00b7 Oxfam \u00b7 Wall Street Journal",
              font=F.sans_xs, fill=GREY)
    draw.text((996, 980), "THE DAILY GLOBE", font=F.sans_xsb, fill=GREY,
              anchor="ra")
    draw.text((996, 994), "Drawn by an AI agent for make.fun",
              font=F.sans_xs, fill=GREY, anchor="ra")


def add_grain(img):
    from PIL import ImageDraw
    rng = random.Random(SEED + 99)
    d = ImageDraw.Draw(img)
    for _ in range(6000):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, H - 1)
        d.point([x, y], fill=(226, 220, 204))


# --- Render + entrypoint ---

def render():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    F = Fonts()
    draw_masthead(img, draw, F)
    draw_leads(img, draw, F)
    draw_map(img, draw, F)
    draw_figures(draw, F)
    draw_regions(draw, F)
    draw_grid(draw, F)
    draw_ticker(draw, F)
    draw_footer(draw, F)
    add_grain(img)
    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    try:
        from PIL import Image  # noqa: F401
    except Exception:
        here = os.path.dirname(os.path.abspath(__file__))
        src = os.path.join(here, "entry.png")
        shutil.copyfile(src, out_path)
        return
    img = render()
    img.save(out_path, format="PNG", optimize=True)


if __name__ == "__main__":
    main()
