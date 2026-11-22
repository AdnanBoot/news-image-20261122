"""Deterministic 1024x1024 broadsheet front page generator."""

from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1024
HEIGHT = 1024
BG_PAPER = "#f7f2e7"
INK_DARK = "#1a1d24"
INK_MUTED = "#4e545f"
NAVY_BAND = "#132238"
RED_ACCENT = "#b8292f"
RULE_COLOR = "#252932"
SCENE_BORDER = "#cfc7b4"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

STATS_BAR = (
    "Nearly 200 delegations at COP31 in Antalya • "
    "23,000 German workers strike on Monday • "
    "A$368 billion committed to AUKUS • "
    "629-6: India's highest Test total in New Zealand"
)

FOOTER_LEFT = (
    "SPACE: Voyager 1 is now one light-day from Earth — 16.1 billion miles away; "
    "its signals take 24 hours to reach home."
)
FOOTER_RIGHT = (
    "PARIS: Turnout fell at Saturday's cost-of-living marches — 82,500 nationwide, "
    "21,500 in Paris, officials say."
)


def load_font(filename, size):
    """Load a TrueType font from FONT_DIR, falling back to DejaVuSans or default."""
    for candidate in (FONT_DIR / filename, FONT_DIR / "DejaVuSans.ttf"):
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size)
            except OSError:
                continue
    return ImageFont.load_default()


def measure_text(draw, text, font):
    """Return (width, height) of rendered text via textbbox."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_text(draw, text, font, max_width):
    """Greedy word-wrap fitting lines within max_width."""
    words = text.split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        w, _ = measure_text(draw, candidate, font)
        if w <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def fit_text_block(
    draw,
    text,
    font_file,
    max_width,
    max_height,
    max_lines,
    start_size,
    min_size=7,
    line_spacing_ratio=1.22,
):
    """Find largest font size whose wrapped lines fit within max_width and max_height."""
    for size in range(start_size, min_size - 1, -1):
        font = load_font(font_file, size)
        lines = wrap_text(draw, text, font, max_width)
        line_h = max(1, round(size * line_spacing_ratio))
        if len(lines) <= max_lines and len(lines) * line_h <= max_height:
            return font, lines, line_h
    font = load_font(font_file, min_size)
    lines = wrap_text(draw, text, font, max_width)[:max_lines]
    line_h = max(1, round(min_size * line_spacing_ratio))
    return font, lines, line_h


def draw_text_lines(draw, x, y, lines, font, line_h, fill):
    """Draw wrapped text lines starting at (x, y) with vertical step line_h."""
    for idx, line in enumerate(lines):
        draw.text((x, y + idx * line_h), line, font=font, fill=fill)


def draw_star(draw, cx, cy, outer_r, inner_r, fill, points=5):
    """Draw a filled star polygon centered at (cx, cy)."""
    coords = []
    step = math.pi / points
    for i in range(points * 2):
        angle = -math.pi / 2 + i * step
        r = outer_r if i % 2 == 0 else inner_r
        coords.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(coords, fill=fill)


def _draw_scene_box(draw, box, bg):
    """Fill scene background and draw 1px SCENE_BORDER outline."""
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], fill=bg, outline=SCENE_BORDER, width=1)


def _draw_sun(draw, cx, cy, r, ray_color="#d9822b", disc_color="#e89c31"):
    """Draw a sun disc with 8 radiating rays."""
    for i in range(8):
        angle = i * (math.pi / 4)
        x_start = cx + (r + 3) * math.cos(angle)
        y_start = cy + (r + 3) * math.sin(angle)
        x_end = cx + (r + 9) * math.cos(angle)
        y_end = cy + (r + 9) * math.sin(angle)
        draw.line([(x_start, y_start), (x_end, y_end)], fill=ray_color, width=2)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=disc_color)


def _draw_factory(draw, x_left, x_right, base_y, height=34):
    """Draw a sawtooth-roof factory silhouette with two smokestacks."""
    stack_w = 10
    stack1_x = x_left + 14
    stack2_x = x_left + 34
    draw.rectangle(
        [stack1_x, base_y - height - 18, stack1_x + stack_w, base_y - height + 4],
        fill="#2d333b",
    )
    draw.rectangle(
        [stack2_x, base_y - height - 14, stack2_x + stack_w, base_y - height + 4],
        fill="#2d333b",
    )
    mid_x = (x_left + x_right) // 2
    roof_top = base_y - height
    roof_valley = base_y - int(height * 0.65)
    body = [
        (x_left, base_y),
        (x_left, roof_valley),
        (x_left + (mid_x - x_left) // 2, roof_top),
        (mid_x, roof_valley),
        (mid_x + (x_right - mid_x) // 2, roof_top),
        (x_right, roof_valley),
        (x_right, base_y),
    ]
    draw.polygon(body, fill="#2d333b")
    return stack1_x + stack_w // 2, base_y - height - 18


def scene_cop31_globe(draw, box):
    """COP31 climate summit: sun, globe with continents, and factory with smoke."""
    x0, y0, x1, y1 = box
    _draw_scene_box(draw, box, "#e6ece6")
    _draw_sun(draw, x1 - 46, y0 + 25, 14)

    gx, gy, gr = x0 + 116, y0 + 48, 35
    draw.ellipse(
        [gx - gr, gy - gr, gx + gr, gy + gr],
        fill="#4b89a8",
        outline="#2b556b",
        width=2,
    )
    # Continent blobs
    draw.polygon(
        [
            (gx - 24, gy - 18),
            (gx - 8, gy - 26),
            (gx + 2, gy - 14),
            (gx - 6, gy - 2),
            (gx - 20, gy - 4),
        ],
        fill="#72a163",
    )
    draw.polygon(
        [
            (gx + 8, gy - 10),
            (gx + 24, gy - 14),
            (gx + 28, gy + 4),
            (gx + 14, gy + 16),
            (gx + 4, gy + 6),
        ],
        fill="#72a163",
    )
    # Latitude arc
    draw.arc(
        [gx - gr + 3, gy - 12, gx + gr - 3, gy + 12],
        start=10,
        end=170,
        fill="#2b556b",
        width=1,
    )

    sx, sy = _draw_factory(draw, x1 - 156, x1 - 36, y1 - 2, height=32)
    for dx, dy, rx, ry in [(2, -10, 10, 6), (14, -18, 13, 7), (28, -24, 15, 8)]:
        draw.ellipse(
            [sx + dx - rx, sy + dy - ry, sx + dx + rx, sy + dy + ry],
            fill="#9aa3ad",
        )


def scene_sinaloa(draw, box):
    """Sinaloa operation: desert road, flaming barricades, cactus, sun, map pin."""
    x0, y0, x1, y1 = box
    _draw_scene_box(draw, box, "#efe6d4")
    _draw_sun(draw, x1 - 38, y0 + 22, 10)

    # Cactus on left
    cx = x0 + 52
    draw.rounded_rectangle(
        [cx - 6, y0 + 18, cx + 6, y1 - 36], radius=5, fill="#4a7c59"
    )
    draw.rounded_rectangle(
        [cx - 18, y0 + 30, cx - 4, y0 + 38], radius=3, fill="#4a7c59"
    )
    draw.rounded_rectangle(
        [cx - 18, y0 + 22, cx - 10, y0 + 38], radius=3, fill="#4a7c59"
    )
    draw.rounded_rectangle(
        [cx + 4, y0 + 36, cx + 18, y0 + 44], radius=3, fill="#4a7c59"
    )
    draw.rounded_rectangle(
        [cx + 10, y0 + 26, cx + 18, y0 + 44], radius=3, fill="#4a7c59"
    )

    # Road band
    draw.rectangle([x0 + 1, y1 - 34, x1 - 1, y1 - 1], fill="#6b6f76")
    dash_y = y1 - 18
    for dx in range(x0 + 10, x1 - 16, 30):
        draw.line([(dx, dash_y), (min(dx + 18, x1 - 4), dash_y)], fill="#ffffff", width=2)

    # Three flaming barricades
    bar_xs = [x0 + 130, x0 + 232, x0 + 334]
    for bx in bar_xs:
        by = y1 - 32
        draw.rectangle([bx, by, bx + 34, by + 12], fill="#2d333b")
        for fx in (bx + 9, bx + 25):
            draw.polygon(
                [(fx - 5, by), (fx, by - 14), (fx + 5, by)], fill="#e07b2a"
            )
            draw.polygon(
                [(fx - 2, by), (fx, by - 8), (fx + 2, by)], fill="#f2c94c"
            )

    # Red map pin above middle barricade
    px, py = bar_xs[1] + 17, y0 + 28
    draw.polygon([(px - 5, py + 3), (px + 5, py + 3), (px, py + 13)], fill=RED_ACCENT)
    draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=RED_ACCENT)
    draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill="#ffffff")


def scene_beijing_telecom(draw, box):
    """FCC telecom ban: smartphone, signal arcs, prohibition mark, ruling docs."""
    x0, y0, x1, y1 = box
    _draw_scene_box(draw, box, "#e8ebee")

    # Smartphone centered-left at (x0+150, y0+48), 54w x 84h
    pcx, pcy = x0 + 150, y0 + 48
    pw, ph = 54, 84
    px0, py0 = pcx - pw // 2, pcy - ph // 2
    px1, py1 = pcx + pw // 2, pcy + ph // 2
    draw.rounded_rectangle([px0, py0, px1, py1], radius=8, fill="#2d333b")
    draw.rectangle([px0 + 5, py0 + 10, px1 - 5, py1 - 10], fill="#9fb6c4")
    draw.line([(pcx - 8, py0 + 5), (pcx + 8, py0 + 5)], fill="#6b7280", width=2)

    # Signal arcs near phone's top-right corner
    acx, acy = px1 + 4, py0 + 18
    for r in (16, 26, 36):
        draw.arc(
            [acx - r, acy - r, acx + r, acy + r],
            start=-55,
            end=45,
            fill="#4b89a8",
            width=3,
        )

    # Prohibition mark
    mcx, mcy, mr = x0 + 232, y0 + 34, 26
    draw.ellipse(
        [mcx - mr, mcy - mr, mcx + mr, mcy + mr], outline=RED_ACCENT, width=5
    )
    offset = int(mr * 0.68)
    draw.line(
        [(mcx - offset, mcy - offset), (mcx + offset, mcy + offset)],
        fill=RED_ACCENT,
        width=5,
    )

    # Three horizontal document bars on right
    dx0, dx1 = x0 + 300, x1 - 24
    for i in range(3):
        dy0 = y0 + 20 + i * 22
        dy1 = dy0 + 14
        draw.rounded_rectangle([dx0, dy0, dx1, dy1], radius=3, fill="#c8cfd6")
        draw.rectangle([dx0, dy0, dx0 + 6, dy1], fill="#7c8794")


def scene_berlin_strike(draw, box):
    """German strike: factory on left and three picket placards on right."""
    x0, y0, x1, y1 = box
    _draw_scene_box(draw, box, "#ebe4d6")
    _draw_factory(draw, x0 + 20, x0 + 220, y1 - 2, height=38)

    for px in (x0 + 268, x0 + 322, x0 + 376):
        draw.line([(px, y1 - 4), (px, y0 + 30)], fill="#7a5230", width=3)
        sx0, sy0 = px - 22, y0 + 14
        sx1, sy1 = px + 22, y0 + 40
        draw.rectangle(
            [sx0, sy0, sx1, sy1], fill="#ffffff", outline=SCENE_BORDER, width=1
        )
        draw.line([(sx0 + 6, sy0 + 9), (sx1 - 6, sy0 + 9)], fill=RED_ACCENT, width=3)
        draw.line([(sx0 + 6, sy0 + 17), (sx1 - 10, sy0 + 17)], fill=INK_DARK, width=2)


def scene_aukus_sub(draw, box):
    """AUKUS submarines: sky, sea with wave arcs, submarine with periscope & prop."""
    x0, y0, x1, y1 = box
    _draw_scene_box(draw, box, "#dfe9ee")

    sea_y = y0 + 30
    draw.rectangle([x0 + 1, sea_y, x1 - 1, y1 - 1], fill="#3b6e8c")
    for wx in range(x0 + 8, x1 - 20, 34):
        draw.arc(
            [wx, sea_y - 5, wx + 28, sea_y + 5],
            start=0,
            end=180,
            fill="#ffffff",
            width=2,
        )

    # Submarine centered
    cx = (x0 + x1) // 2
    hy0 = y0 + 52
    hx0, hx1, hy1 = cx - 120, cx + 120, hy0 + 34
    draw.rounded_rectangle([hx0, hy0, hx1, hy1], radius=17, fill="#2d333b")

    # Conning tower & periscope
    draw.rectangle([cx - 24, hy0 - 14, cx + 14, hy0 + 2], fill="#2d333b")
    periscope_top = sea_y - 11
    draw.line([(cx - 4, hy0 - 14), (cx - 4, periscope_top)], fill="#2d333b", width=2)
    draw.line([(cx - 4, periscope_top), (cx + 2, periscope_top)], fill="#2d333b", width=2)

    # Small muted-grey surface ship floating on the surface line at right
    ship_x0, ship_x1 = x1 - 92, x1 - 22
    draw.polygon(
        [
            (ship_x0, sea_y - 8),
            (ship_x1, sea_y - 8),
            (ship_x1 - 8, sea_y + 1),
            (ship_x0 + 6, sea_y + 1),
        ],
        fill="#6f7782",
    )
    draw.rectangle([ship_x0 + 18, sea_y - 16, ship_x0 + 44, sea_y - 8], fill="#6f7782")
    draw.rectangle([ship_x0 + 26, sea_y - 21, ship_x0 + 34, sea_y - 16], fill="#6f7782")

    # Propeller X at right end
    px, py = hx1 + 6, hy0 + 17
    draw.line([(px - 6, py - 9), (px + 6, py + 9)], fill="#2d333b", width=3)
    draw.line([(px - 6, py + 9), (px + 6, py - 9)], fill="#2d333b", width=3)

    # Three porthole dots
    for dx in (-52, 0, 52):
        draw.ellipse(
            [cx + dx - 3, hy0 + 14, cx + dx + 3, hy0 + 20], fill="#f2c94c"
        )


def scene_cricket(draw, box):
    """Wellington Test: sun, cricket pitch, stumps & bails, leaning bat, red ball."""
    x0, y0, x1, y1 = box
    _draw_scene_box(draw, box, "#e9efe4")
    _draw_sun(draw, x0 + 34, y0 + 24, 10)

    cx = (x0 + x1) // 2
    draw.rectangle([cx - 34, y0 + 6, cx + 34, y1 - 6], fill="#d9c9a3")

    # Stumps and bails
    stump_bottom = y1 - 12
    stump_top = stump_bottom - 30
    for sx in (cx - 10, cx, cx + 10):
        draw.rectangle([sx - 1, stump_top, sx + 2, stump_bottom], fill="#c9a227")
    draw.rectangle([cx - 10, stump_top - 3, cx - 1, stump_top], fill="#a68117")
    draw.rectangle([cx + 1, stump_top - 3, cx + 10, stump_top], fill="#a68117")

    # Leaning cricket bat right of stumps
    draw.line([(cx + 42, y0 + 38), (cx + 50, y0 + 54)], fill="#4b3621", width=4)
    draw.rounded_rectangle(
        [cx + 44, y0 + 52, cx + 58, y1 - 10],
        radius=3,
        fill="#b98a4a",
        outline="#8a6230",
        width=1,
    )

    # Red cricket ball mid-flight with seam and motion dashes
    bx, by, br = cx + 96, y0 + 34, 9
    draw.ellipse([bx - br, by - br, bx + br, by + br], fill="#b8292f")
    draw.arc(
        [bx - 5, by - 7, bx + 5, by + 7],
        start=-40,
        end=140,
        fill="#ffffff",
        width=1,
    )
    for idx, length in enumerate((14, 18, 12)):
        dy = by - 4 + idx * 4
        draw.line([(bx - 14 - length, dy), (bx - 14, dy)], fill="#7c8794", width=2)


PANELS = [
    (
        "01",
        "CLIMATE • ANTALYA",
        "COP31 Nears Final Deal as Approval Session Opens Sunday",
        "Presidents Australia and Türkiye table a package they say all nearly 200 delegations can accept; objections closed at 03:00 GMT ahead of Sunday's vote.",
        scene_cop31_globe,
    ),
    (
        "02",
        "AMERICAS • SINALOA",
        "Mexico Captures FBI Top-Ten Drug Lord 'El Chapo Isidro'",
        "Fausto Isidro Meza Flores and two other leaders were seized in a Friday-night operation in Sinaloa; the arrest sparked clashes and flaming roadblocks. A $5 million US reward had been offered.",
        scene_sinaloa,
    ),
    (
        "03",
        "ASIA • BEIJING",
        "China Condemns US Ban on Its Telecom Firms' Phone Access",
        "Beijing 'firmly opposes' Thursday's FCC vote barring China Mobile, China Telecom and China Unicom from direct access to US numbers, and warns of countermeasures.",
        scene_beijing_telecom,
    ),
    (
        "04",
        "EUROPE • BERLIN",
        "23,000 German Workers to Strike Again on Monday",
        "IG Metall extends its walkout across 19 northern firms — Mercedes-Benz, Meyer Werft and Siemens Gamesa — in a pay dispute; the union demands 5%.",
        scene_berlin_strike,
    ),
    (
        "05",
        "DEFENCE • CANBERRA",
        "Australia Tells US Budget Office It Is Wrong on AUKUS",
        "'They are wrong,' says Defence Minister Marles of a CBO report that selling Virginia-class submarines could shrink the US attack fleet through 2060.",
        scene_aukus_sub,
    ),
    (
        "06",
        "SPORT • WELLINGTON",
        "Pant's 128 Powers India to Record 629-6 in Wellington",
        "India post their highest Test total in New Zealand, passing the 520 of 2009, to lead by 261 at lunch on day four; New Zealand made 368.",
        scene_cricket,
    ),
]


def render_front_page(out_path):
    """Render the deterministic 1024x1024 broadsheet front page PNG to out_path."""
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (WIDTH, HEIGHT), BG_PAPER)
    draw = ImageDraw.Draw(img)

    # Top double rule
    draw.line([(32, 24), (992, 24)], fill=RULE_COLOR, width=2)
    draw.line([(32, 28), (992, 28)], fill=RULE_COLOR, width=1)

    # Kicker & Masthead
    kicker_font = load_font("DejaVuSans-Bold.ttf", 11)
    kicker_text = "GLOBAL FRONT PAGE • SIX KEY STORIES • 24-HOUR SUMMARY"
    draw.text((512, 35), kicker_text, font=kicker_font, fill=INK_MUTED, anchor="mt")

    masthead_font = load_font("DejaVuSerif-Bold.ttf", 62)
    draw.text((512, 50), "WORLD NEWS", font=masthead_font, fill=INK_DARK, anchor="mt")

    # Navy band with red end caps
    draw.rectangle([32, 122, 992, 152], fill=NAVY_BAND)
    draw.rectangle([32, 122, 46, 152], fill=RED_ACCENT)
    draw.rectangle([978, 122, 992, 152], fill=RED_ACCENT)
    date_font = load_font("DejaVuSans-Bold.ttf", 14)
    draw.text(
        (512, 137),
        "SUNDAY 22 NOVEMBER 2026",
        font=date_font,
        fill="#ffffff",
        anchor="mm",
    )

    # Stats bar
    draw.line([(32, 159), (992, 159)], fill=RULE_COLOR, width=1)
    draw.line([(32, 181), (992, 181)], fill=RULE_COLOR, width=1)
    stats_font = load_font("DejaVuSans-Bold.ttf", 7)
    for size in range(10, 6, -1):
        candidate = load_font("DejaVuSans-Bold.ttf", size)
        if measure_text(draw, STATS_BAR, candidate)[0] <= 960:
            stats_font = candidate
            break
    draw.text((512, 170), STATS_BAR, font=stats_font, fill=INK_DARK, anchor="mm")

    # Panel grid: 2 columns x 3 rows
    margin = 32
    col_w = 468
    col_gap = 24
    row_h = 248
    row_gap = 14
    grid_top = 186

    tag_font = load_font("DejaVuSans-Bold.ttf", 11)
    lead_font = load_font("DejaVuSans-Bold.ttf", 8)

    for idx, (num, tag, headline, sub, scene_fn) in enumerate(PANELS):
        col = idx % 2
        row = idx // 2
        px = margin + col * (col_w + col_gap)
        py = grid_top + row * (row_h + row_gap)
        row_bottom = py + row_h

        if idx == 0:
            draw.line([(px, py), (px + col_w, py)], fill=RED_ACCENT, width=4)
        else:
            draw.line([(px, py), (px + col_w, py)], fill=RULE_COLOR, width=2)

        draw.text((px, py + 6), tag, font=tag_font, fill=RED_ACCENT)
        num_w, _ = measure_text(draw, num, tag_font)
        draw.text((px + col_w - num_w, py + 6), num, font=tag_font, fill=INK_MUTED)

        if idx == 0:
            tag_w, _ = measure_text(draw, tag, tag_font)
            pill_x = px + tag_w + 10
            pill_y = py + 5
            draw.rectangle(
                [pill_x, pill_y, pill_x + 44, pill_y + 13], fill=RED_ACCENT
            )
            draw.text(
                (pill_x + 22, pill_y + 6.5),
                "LEAD",
                font=lead_font,
                fill="#ffffff",
                anchor="mm",
            )

        scene_fn(draw, (px, py + 26, px + col_w, py + 122))

        headline_y = py + 130
        h_font, h_lines, h_line_h = fit_text_block(
            draw,
            headline,
            "DejaVuSerif-Bold.ttf",
            max_width=col_w,
            max_height=50,
            max_lines=2,
            start_size=19,
            min_size=12,
        )
        draw_text_lines(draw, px, headline_y, h_lines, h_font, h_line_h, INK_DARK)

        sub_y = headline_y + len(h_lines) * h_line_h + 5
        s_font, s_lines, s_line_h = fit_text_block(
            draw,
            sub,
            "DejaVuSans.ttf",
            max_width=col_w,
            max_height=max(1, row_bottom - sub_y),
            max_lines=3,
            start_size=13,
            min_size=9,
            line_spacing_ratio=1.24,
        )
        draw_text_lines(draw, px, sub_y, s_lines, s_font, s_line_h, INK_MUTED)

    # Footer
    draw.line([(32, 958), (992, 958)], fill=RULE_COLOR, width=1)
    draw.rectangle([32, 977, 44, 989], fill=RED_ACCENT)
    draw.rectangle([524, 977, 536, 989], fill=NAVY_BAND)

    footer_font = load_font("DejaVuSans-Bold.ttf", 7)
    for size in range(11, 6, -1):
        candidate = load_font("DejaVuSans-Bold.ttf", size)
        w_left, _ = measure_text(draw, FOOTER_LEFT, candidate)
        w_right, _ = measure_text(draw, FOOTER_RIGHT, candidate)
        if w_left <= 450 and w_right <= 450:
            footer_font = candidate
            break

    # Draw footer text; wrap to 2 lines if single line exceeds 450px
    for fx, ftext in ((50, FOOTER_LEFT), (542, FOOTER_RIGHT)):
        fw, _ = measure_text(draw, ftext, footer_font)
        if fw <= 450:
            draw.text((fx, 983), ftext, font=footer_font, fill=INK_DARK, anchor="lm")
        else:
            f_lines = wrap_text(draw, ftext, footer_font, 450)[:2]
            draw_text_lines(draw, fx, 971, f_lines, footer_font, 12, INK_DARK)

    img.save(out_file, format="PNG", optimize=True)


def main():
    """Render entry.png beside this script."""
    render_front_page(Path(__file__).resolve().parent / "entry.png")


if __name__ == "__main__":
    main()
