#!/usr/bin/env python3
"""Sum up 24 November 2026 world news in one image.
Stdlib only. Deterministic. Writes /output/entry.png
(or $MAKEFUN_OUTPUT_DIR/entry.png when set).
Layout: 1024x1024, navy header, 6 blocks 2x3.
No third-party imports.
"""
import os
import struct
import zlib

W = 1024
H = 1024

# 5x7 bitmap font. '#' = on, '.' = off.
FONT = {
    'A': ["01110","10001","10001","11111","10001","10001","10001"],
    'B': ["11110","10001","10001","11110","10001","10001","11110"],
    'C': ["01110","10001","10000","10000","10000","10001","01110"],
    'D': ["11110","10001","10001","10001","10001","10001","11110"],
    'E': ["11111","10000","10000","11110","10000","10000","11111"],
    'F': ["11111","10000","10000","11110","10000","10000","10000"],
    'G': ["01110","10001","10000","10111","10001","10001","01111"],
    'H': ["10001","10001","10001","11111","10001","10001","10001"],
    'I': ["01110","00100","00100","00100","00100","00100","01110"],
    'J': ["00111","00010","00010","00010","00010","10010","01100"],
    'K': ["10001","10010","10100","11000","10100","10010","10001"],
    'L': ["10000","10000","10000","10000","10000","10000","11111"],
    'M': ["10001","11011","10101","10101","10001","10001","10001"],
    'N': ["10001","11001","10101","10011","10001","10001","10001"],
    'O': ["01110","10001","10001","10001","10001","10001","01110"],
    'P': ["11110","10001","10001","11110","10000","10000","10000"],
    'Q': ["01110","10001","10001","10001","10101","10010","01101"],
    'R': ["11110","10001","10001","11110","10100","10010","10001"],
    'S': ["01111","10000","10000","01110","00001","00001","11110"],
    'T': ["11111","00100","00100","00100","00100","00100","00100"],
    'U': ["10001","10001","10001","10001","10001","10001","01110"],
    'V': ["10001","10001","10001","10001","10001","01010","00100"],
    'W': ["10001","10001","10001","10101","10101","11011","10001"],
    'X': ["10001","10001","01010","00100","01010","10001","10001"],
    'Y': ["10001","10001","01010","00100","00100","00100","00100"],
    'Z': ["11111","00001","00010","00100","01000","10000","11111"],
    '0': ["01110","10001","10011","10101","11001","10001","01110"],
    '1': ["00100","01100","00100","00100","00100","00100","01110"],
    '2': ["01110","10001","00001","00110","01000","10000","11111"],
    '3': ["11110","00001","00001","01110","00001","00001","11110"],
    '4': ["00010","00110","01010","10010","11111","00010","00010"],
    '5': ["11111","10000","11110","00001","00001","10001","01110"],
    '6': ["01110","10000","11110","10001","10001","10001","01110"],
    '7': ["11111","00001","00010","00100","01000","01000","01000"],
    '8': ["01110","10001","10001","01110","10001","10001","01110"],
    '9': ["01110","10001","10001","01111","00001","00001","01110"],
    ' ': ["00000","00000","00000","00000","00000","00000","00000"],
    ',': ["00000","00000","00000","00000","00100","00100","01000"],
    '.': ["00000","00000","00000","00000","00000","01100","01100"],
    '-': ["00000","00000","00000","01110","00000","00000","00000"],
    '%': ["11001","11010","00010","00100","01000","01011","10011"],
    '$': ["00100","01111","10100","01110","00101","11110","00100"],
    '+': ["00000","00100","00100","11111","00100","00100","00000"],
    ':': ["00000","01100","01100","00000","01100","01100","00000"],
    '/': ["00001","00010","00010","00100","01000","01000","10000"],
}

def text_width(s, scale, spacing=None):
    if spacing is None:
        spacing = scale
    # each glyph 5*scale wide + spacing, last glyph no trailing spacing
    if not s:
        return 0
    return len(s) * (5 * scale + spacing) - spacing

def draw_text(canvas, x, y, s, scale, color, bold=False):
    s = s.upper()
    spacing = scale
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[' '])
        for gy in range(7):
            row = glyph[gy]
            for gx in range(5):
                if row[gx] == '1':
                    # fill scale x scale block
                    for dy in range(scale):
                        for dx in range(scale):
                            px = cx + gx * scale + dx
                            py = y + gy * scale + dy
                            if 0 <= px < W and 0 <= py < H:
                                idx = (py * W + px) * 3
                                canvas[idx] = color[0]
                                canvas[idx+1] = color[1]
                                canvas[idx+2] = color[2]
                    if bold:
                        # 1px bold to the right
                        for dy in range(scale):
                            px = cx + gx * scale + scale
                            py = y + gy * scale + dy
                            if 0 <= px < W and 0 <= py < H:
                                idx = (py * W + px) * 3
                                canvas[idx] = color[0]
                                canvas[idx+1] = color[1]
                                canvas[idx+2] = color[2]
        cx += 5 * scale + spacing
    return cx

def wrap_text(s, scale, max_width):
    words = s.upper().split()
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip() if cur else w
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            # if single word too long, hard-split by chars
            if text_width(w, scale) > max_width:
                # split word into chunks that fit
                chunk = ""
                for ch in w:
                    t2 = chunk + ch
                    if text_width(t2, scale) <= max_width:
                        chunk = t2
                    else:
                        if chunk:
                            lines.append(chunk)
                        chunk = ch
                cur = chunk
            else:
                cur = w
    if cur:
        lines.append(cur)
    return lines

def fill_rect(canvas, x0, y0, x1, y1, color):
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(W, x1); y1 = min(H, y1)
    for y in range(y0, y1):
        base = y * W * 3
        for x in range(x0, x1):
            idx = base + x * 3
            canvas[idx] = color[0]
            canvas[idx+1] = color[1]
            canvas[idx+2] = color[2]

def set_px(canvas, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        idx = (y * W + x) * 3
        canvas[idx] = color[0]
        canvas[idx+1] = color[1]
        canvas[idx+2] = color[2]

def draw_circle(canvas, cx, cy, r, color):
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            if dx*dx + dy*dy <= r*r:
                set_px(canvas, cx+dx, cy+dy, color)

def draw_square(canvas, x0, y0, size, color):
    fill_rect(canvas, x0, y0, x0+size, y0+size, color)

def draw_triangle(canvas, cx, cy, r, color):
    # upward triangle, apex top
    for y in range(cy-r, cy+r+1):
        t = (y - (cy - r)) / float(2*r)  # 0 top -> 1 bottom
        half = int(t * r)
        for x in range(cx-half, cx+half+1):
            set_px(canvas, x, y, color)

def chunk(b):
    return struct.pack(">I", len(b)) + b + struct.pack(">I", zlib.crc32(b) & 0xffffffff)

def write_png(path, canvas):
    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    ihdr = b"IHDR" + ihdr_data
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + ihdr + struct.pack(">I", zlib.crc32(ihdr) & 0xffffffff)
    # IDAT: each scanline prefixed with filter 0
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        start = y * W * 3
        raw.extend(canvas[start:start+W*3])
    comp = zlib.compress(bytes(raw), 9)
    idat = b"IDAT" + comp
    idat_chunk = struct.pack(">I", len(comp)) + idat + struct.pack(">I", zlib.crc32(idat) & 0xffffffff)
    iend_data = b""
    iend = b"IEND" + iend_data
    iend_chunk = struct.pack(">I", 0) + iend + struct.pack(">I", zlib.crc32(iend) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n" + ihdr_chunk + idat_chunk + iend_chunk
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

STORIES = [
    {
        "num": "1",
        "headline": "NVIDIA SLIPS",
        "summary": "NVIDIA FELL 5.2% TO $156.40 AFTER +31.5% MON AS HUANG RETURNED AS CEO.",
        "shape": "circle",
        "color": (26, 127, 55),
    },
    {
        "num": "2",
        "headline": "ZAPORIZHZHIA STRUCK",
        "summary": "RUSSIAN DAWN STRIKE KILLED 2, WOUNDED 40+ INCL. INFANT AFTER UKRAINE SANK SHIP SUN.",
        "shape": "square",
        "color": (193, 39, 45),
    },
    {
        "num": "3",
        "headline": "HORMUZ TANKERS HIT",
        "summary": "THREE TANKERS HIT MINES IN HORMUZ AND CAUGHT FIRE DESPITE US ESCORT. IRAN RULED OUT TALKS.",
        "shape": "triangle",
        "color": (11, 95, 165),
    },
    {
        "num": "4",
        "headline": "GAZA CHIEF KILLED",
        "summary": "ISRAELI STRIKES MON NIGHT KILLED 9, INCL. HAMAS SECURITY CHIEF NAIM ABU NAHL IN GAZA CITY.",
        "shape": "circle",
        "color": (122, 31, 31),
    },
    {
        "num": "5",
        "headline": "INDONESIA FIRE",
        "summary": "DEATH TOLL FROM CANDY FACTORY FIRE IN SERANG, BANTEN ROSE TO 26 ON TUE.",
        "shape": "square",
        "color": (217, 93, 0),
    },
    {
        "num": "6",
        "headline": "COLOMBIA CAR BOMB",
        "summary": "CAR BOMB AT META GOVERNOR OFFICE INJURED 22, DAMAGED 80+ BUILDINGS ON EVE OF FARC ANNIVERSARY.",
        "shape": "triangle",
        "color": (106, 61, 155),
    },
]

def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")

    bg = (247, 245, 239)
    navy = (15, 42, 68)
    gold = (201, 162, 39)
    white = (255, 255, 255)
    dark = (20, 28, 38)
    grey = (90, 98, 110)
    border = (210, 208, 200)

    canvas = bytearray(W * H * 3)
    # background
    fill_rect(canvas, 0, 0, W, H, bg)

    # header bar
    fill_rect(canvas, 0, 0, W, 150, navy)
    # header line 1
    h1 = "TUESDAY, 24 NOVEMBER 2026"
    w1 = text_width(h1, 5)
    draw_text(canvas, (W - w1)//2, 28, h1, 5, white, bold=True)
    h2 = "WORLD NEWS IN ONE IMAGE"
    w2 = text_width(h2, 4)
    draw_text(canvas, (W - w2)//2, 88, h2, 4, (220, 225, 235), bold=False)
    # gold rule
    fill_rect(canvas, 0, 150, W, 156, gold)

    # blocks 2 cols x 3 rows
    # footer reserve 992-1024
    top = 168
    bottom = 992
    row_h = (bottom - top) // 3  # 274
    col_w = 494
    col_x = [12, 518]

    for idx, st in enumerate(STORIES):
        row = idx // 2
        col = idx % 2
        bx = col_x[col]
        by = top + row * row_h
        bw = col_w
        bh = row_h - 10
        # block bg white + border
        fill_rect(canvas, bx, by, bx+bw, by+bh, white)
        # border: top/bottom/left/right 2px
        fill_rect(canvas, bx, by, bx+bw, by+2, border)
        fill_rect(canvas, bx, by+bh-2, bx+bw, by+bh, border)
        fill_rect(canvas, bx, by, bx+2, by+bh, border)
        fill_rect(canvas, bx+bw-2, by, bx+bw, by+bh, border)
        # accent top bar in story colour
        fill_rect(canvas, bx, by, bx+bw, by+6, st["color"])

        inner_x = bx + 18
        inner_w = bw - 36
        # number
        draw_text(canvas, inner_x, by+20, st["num"], 4, navy, bold=True)
        # icon shape top-right, no text inside
        cx = bx + bw - 42
        cy = by + 38
        if st["shape"] == "circle":
            draw_circle(canvas, cx, cy, 18, st["color"])
        elif st["shape"] == "square":
            draw_square(canvas, cx-18, cy-18, 36, st["color"])
        else:
            draw_triangle(canvas, cx, cy, 20, st["color"])
        # headline
        hy = by + 62
        # choose scale 4 if fits, else 3
        if text_width(st["headline"], 4) <= inner_w:
            hs = 4
        else:
            hs = 3
        draw_text(canvas, inner_x, hy, st["headline"], hs, dark, bold=True)
        # summary, scale 3, wrapped
        lines = wrap_text(st["summary"], 3, inner_w)
        ly = hy + (hs * 7) + 16
        for line in lines:
            draw_text(canvas, inner_x, ly, line, 3, (45, 55, 68), bold=False)
            ly += 3 * 7 + 8

    # footer
    foot = "SOURCES: REUTERS, AP, AL JAZEERA, CNA - 24 NOV 2026"
    fw = text_width(foot, 3)
    draw_text(canvas, (W - fw)//2, 999, foot, 3, grey, bold=False)

    size = write_png(out_path, canvas)
    print(f"WROTE {out_path} {size} bytes {W}x{H}")

if __name__ == "__main__":
    main()
