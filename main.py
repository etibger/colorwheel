import colorsys
import math

from PIL import Image, ImageDraw, ImageFont

# ==========================
# CONFIGURATION
# ==========================
WHEEL_SIZE = 600
LEGEND_WIDTH = 260
IMAGE_SIZE = (WHEEL_SIZE + LEGEND_WIDTH, WHEEL_SIZE)

RADIUS = WHEEL_SIZE // 2
CENTER = (RADIUS, RADIUS)
MARKER_RADIUS = 6

HEX_COLORS = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]

OUTPUT_FILE = "color_wheel_with_legend.png"

# ==========================
# HELPERS
# ==========================


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hsv(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    return colorsys.rgb_to_hsv(r, g, b)


def hsv_to_xy(h, s):
    angle = 2 * math.pi * h
    r = s * RADIUS
    x = CENTER[0] + r * math.cos(angle)
    y = CENTER[1] + r * math.sin(angle)
    return int(x), int(y)


# ==========================
# IMAGE SETUP
# ==========================
img = Image.new("RGB", IMAGE_SIZE, "white")
draw = ImageDraw.Draw(img)

# Try to load a nicer font, fallback if unavailable
try:
    font = ImageFont.truetype("DejaVuSans.ttf", 16)
    font_bold = ImageFont.truetype("DejaVuSans.ttf", 18)
except IOError:
    font = font_bold = ImageFont.load_default()

pixels = img.load()

# ==========================
# DRAW COLOR WHEEL
# ==========================
for y in range(WHEEL_SIZE):
    for x in range(WHEEL_SIZE):
        dx = x - CENTER[0]
        dy = y - CENTER[1]
        distance = math.sqrt(dx * dx + dy * dy)

        if distance <= RADIUS:
            saturation = distance / RADIUS
            hue = (math.atan2(dy, dx) / (2 * math.pi)) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, 1.0)
            pixels[x, y] = (int(r * 255), int(g * 255), int(b * 255))

# ==========================
# DRAW MARKERS + NUMBERS
# ==========================
marker_positions = []

for idx, hex_color in enumerate(HEX_COLORS, start=1):
    rgb = hex_to_rgb(hex_color)
    h, s, _ = rgb_to_hsv(rgb)
    x, y = hsv_to_xy(h, s)

    marker_positions.append((idx, hex_color, rgb, x, y))

    # Marker circle
    draw.ellipse(
        (x - MARKER_RADIUS, y - MARKER_RADIUS, x + MARKER_RADIUS, y + MARKER_RADIUS),
        outline="black",
        width=2,
    )

    # Number label near marker
    draw.text(
        (x + MARKER_RADIUS + 4, y - MARKER_RADIUS - 4),
        str(idx),
        fill="black",
        font=font_bold,
    )

# ==========================
# DRAW LEGEND
# ==========================
legend_x = WHEEL_SIZE + 20
legend_y = 30
line_height = 30

draw.text((legend_x, legend_y - 25), "Legend", fill="black", font=font_bold)

for i, hex_color, rgb, _, _ in marker_positions:
    y_pos = legend_y + (i - 1) * line_height

    # Color swatch
    draw.rectangle(
        (legend_x, y_pos, legend_x + 20, y_pos + 20), fill=rgb, outline="black"
    )

    # Legend text
    draw.text(
        (legend_x + 30, y_pos), f"{i}: {hex_color}  RGB{rgb}", fill="black", font=font
    )

# ==========================
# SAVE
# ==========================
img.save(OUTPUT_FILE)
print(f"Saved image to {OUTPUT_FILE}")
