"""
Badge/Certificate generation for course completions.
Generates a premium shareable PNG badge using Pillow.
"""

import io
import math
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Badge dimensions (OG image size - perfect for sharing)
W, H = 1200, 630

def _hex(color):
    """Convert #rrggbb or #rrggbbaa to (r,g,b,a) tuple."""
    c = color.lstrip('#')
    if len(c) == 6:
        r, g, b = int(c[0:2],16), int(c[2:4],16), int(c[4:6],16)
        return (r, g, b, 255)
    r, g, b, a = int(c[0:2],16), int(c[2:4],16), int(c[4:6],16), int(c[6:8],16)
    return (r, g, b, a)

def _try_font(size, bold=False):
    """Try to load a good font, fall back to default."""
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial Bold.ttf" if bold else "C:/Windows/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

def generate_badge(course_title: str, username: str, completed_date: datetime = None) -> bytes:
    """
    Generate a premium course completion badge PNG.
    Returns raw PNG bytes.
    """
    if completed_date is None:
        completed_date = datetime.utcnow()

    # ── Base canvas ────────────────────────────────────────
    img = Image.new("RGBA", (W, H), (9, 9, 15, 255))  # #09090f
    draw = ImageDraw.Draw(img)

    # ── Background grid pattern ────────────────────────────
    for x in range(0, W, 48):
        draw.line([(x, 0), (x, H)], fill=(255, 255, 255, 8), width=1)
    for y in range(0, H, 48):
        draw.line([(0, y), (W, y)], fill=(255, 255, 255, 8), width=1)

    # ── Golden glow radial at center ───────────────────────
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(300, 0, -1):
        alpha = int(40 * (1 - r/300) * (1 - r/300))
        gd.ellipse([(W//2 - r, H//2 - r), (W//2 + r, H//2 + r)],
                   fill=(251, 191, 36, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=30))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # ── Outer border frame ─────────────────────────────────
    border_margin = 24
    # Gradient-like border: draw multiple rects with decreasing alpha
    for i, alpha in enumerate([60, 40, 25, 15]):
        m = border_margin - i
        draw.rectangle([m, m, W - m - 1, H - m - 1],
                       outline=(251, 191, 36, alpha), width=1)

    # ── Corner accent dots ─────────────────────────────────
    dot_r = 5
    corners = [(40, 40), (W-40, 40), (40, H-40), (W-40, H-40)]
    for cx, cy in corners:
        draw.ellipse([(cx-dot_r, cy-dot_r), (cx+dot_r, cy+dot_r)],
                     fill=(251, 191, 36, 200))

    # ── Top badge strip ────────────────────────────────────
    draw.rectangle([border_margin+8, border_margin+8, W-border_margin-8, border_margin+50],
                   fill=(251, 191, 36, 18))
    top_font = _try_font(13, bold=True)
    strip_text = "ROHITH BUILDS  ·  COURSE COMPLETION CERTIFICATE"
    bbox = draw.textbbox((0,0), strip_text, font=top_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, border_margin + 22), strip_text,
              font=top_font, fill=(251, 191, 36, 200))

    # ── Trophy / medal emoji area ──────────────────────────
    trophy_font = _try_font(80)
    try:
        draw.text((W//2, 140), "🏆", font=trophy_font, anchor="mm",
                  fill=(255, 215, 0, 255))
    except Exception:
        # Fallback: draw a golden circle
        draw.ellipse([(W//2 - 45, 110), (W//2 + 45, 200)],
                     fill=(251, 191, 36, 220))

    # ── Stars decoration ───────────────────────────────────
    star_positions = [(W//2 - 120, 155), (W//2 + 120, 155),
                      (W//2 - 90, 130), (W//2 + 90, 130)]
    star_font = _try_font(22)
    for sx, sy in star_positions:
        try:
            draw.text((sx, sy), "✦", font=star_font, anchor="mm",
                      fill=(251, 191, 36, 150))
        except Exception:
            draw.ellipse([(sx-3, sy-3), (sx+3, sy+3)], fill=(251, 191, 36, 150))

    # ── "COURSE COMPLETED" heading ─────────────────────────
    heading_font = _try_font(48, bold=True)
    heading = "COURSE COMPLETED"
    bbox = draw.textbbox((0, 0), heading, font=heading_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 230), heading,
              font=heading_font, fill=(251, 191, 36, 255))

    # ── Divider line ───────────────────────────────────────
    draw.line([(W//2 - 200, 292), (W//2 + 200, 292)],
              fill=(251, 191, 36, 80), width=1)

    # ── Course title ───────────────────────────────────────
    course_font = _try_font(34, bold=True)
    # Wrap if too long
    max_chars = 44
    if len(course_title) > max_chars:
        # Split at word boundary
        words = course_title.split()
        line1, line2 = [], []
        for w in words:
            if len(" ".join(line1 + [w])) <= max_chars:
                line1.append(w)
            else:
                line2.append(w)
        lines = [" ".join(line1), " ".join(line2)]
    else:
        lines = [course_title]

    y_course = 308
    for line in lines:
        if line:
            bbox = draw.textbbox((0, 0), line, font=course_font)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, y_course), line,
                      font=course_font, fill=(241, 245, 249, 240))
            y_course += 44

    # ── "This certifies that" label ───────────────────────
    label_font = _try_font(16)
    label = "This certifies that"
    bbox = draw.textbbox((0, 0), label, font=label_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y_course + 10), label,
              font=label_font, fill=(100, 116, 139, 255))

    # ── Username ───────────────────────────────────────────
    name_font = _try_font(30, bold=True)
    display_name = username
    bbox = draw.textbbox((0, 0), display_name, font=name_font)
    tw = bbox[2] - bbox[0]
    # Underline effect
    y_name = y_course + 36
    draw.text(((W - tw) // 2, y_name), display_name,
              font=name_font, fill=(251, 191, 36, 255))
    draw.line([((W - tw) // 2, y_name + 38),
               ((W + tw) // 2, y_name + 38)],
              fill=(251, 191, 36, 100), width=1)

    # ── Date ──────────────────────────────────────────────
    date_font = _try_font(14)
    date_str = f"Completed on {completed_date.strftime('%B %d, %Y')}"
    bbox = draw.textbbox((0, 0), date_str, font=date_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y_name + 52), date_str,
              font=date_font, fill=(100, 116, 139, 200))

    # ── Bottom branding ────────────────────────────────────
    brand_font = _try_font(15, bold=True)
    brand = "rohithbuilds.com"
    bbox = draw.textbbox((0, 0), brand, font=brand_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, H - 48), brand,
              font=brand_font, fill=(251, 191, 36, 120))

    # ── Convert to RGB PNG bytes ───────────────────────────
    rgb = Image.new("RGB", img.size, (9, 9, 15))
    rgb.paste(img, mask=img.split()[3])

    buf = io.BytesIO()
    rgb.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()
