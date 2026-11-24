"""
Generate wiring artifacts for the Air Quality Monitor - THREE methods:

  1. docs/WIRING.pdf        - clean printable drawn schematic (reportlab)
  2. docs/schematics/*.png  - inline schematic images (matplotlib)
  3. docs/WIRING.md         - plain-text / ASCII wiring description

Run:  python docs/make_wiring_pdf.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
PDF_OUT = os.path.join(HERE, "WIRING.pdf")
PNG_DIR = os.path.join(HERE, "schematics")
os.makedirs(PNG_DIR, exist_ok=True)

INK = "#1f2d3d"
DEVICE_FILL = "#eef4fc"
DEVICE_EDGE = "#2b3f63"
WIRE = "#2f3a45"
PIN = "#1f6feb"
ACCENT = "#b00020"
GREEN = "#1a7f37"
RAIL5 = "#c0392b"
RAIL3 = "#1f6feb"
GNDC = "#3d3d3d"


# ===================== METHOD 2: matplotlib PNG schematics =================
def _fig(title):
    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=170)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.015, 0.965, title, fontsize=12.5, fontweight="bold", color=INK, ha="left")
    return fig, ax


def _dev(ax, x, y, w, h, title, pins):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.004,rounding_size=0.015",
                 linewidth=1.6, edgecolor=DEVICE_EDGE, facecolor=DEVICE_FILL, zorder=2))
    ax.text(x + w / 2, y + h + 0.02, title, ha="center", va="bottom",
            fontsize=10, fontweight="bold", color=INK, zorder=6)
    xy = {}
    for name, side, yf in pins:
        py = y + yf * h
        if side == "L":
            px = x
            ax.plot([px - 0.045, px], [py, py], color=WIRE, lw=1.5, zorder=3)
            ax.text(px - 0.052, py, name, ha="right", va="center", fontsize=7.2, color=INK)
        else:
            px = x + w
            ax.plot([px, px + 0.045], [py, py], color=WIRE, lw=1.5, zorder=3)
            ax.text(px + 0.052, py, name, ha="left", va="center", fontsize=7.2, color=INK)
        ax.plot(px, py, "o", color=PIN, ms=4.5, zorder=4)
        xy[name] = (px, py)
    return xy


def _w(ax, pts, color=WIRE, lbl=None):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=1.5,
            solid_capstyle="round", zorder=3)
    if lbl:
        i = max(1, len(pts) // 2)
        ax.text((pts[i - 1][0] + pts[i][0]) / 2, (pts[i - 1][1] + pts[i][1]) / 2 + 0.013,
                lbl, fontsize=6.6, color=ACCENT, ha="center")


def _res_h(ax, x0, x1, y, label):
    n = 7; step = (x1 - x0) / n
    xs = [x0]; ys = [y]
    for i in range(1, n):
        xs.append(x0 + step * i); ys.append(y + (0.017 if i % 2 else -0.017))
    xs.append(x1); ys.append(y)
    ax.plot(xs, ys, color=WIRE, lw=1.4, zorder=3)
    ax.text((x0 + x1) / 2, y + 0.036, label, fontsize=6.9, ha="center", color=INK)


def _res_v(ax, x, y0, y1, label):
    n = 7; step = (y1 - y0) / n
    ys = [y0]; xs = [x]
    for i in range(1, n):
        ys.append(y0 + step * i); xs.append(x + (0.017 if i % 2 else -0.017))
    ys.append(y1); xs.append(x)
    ax.plot(xs, ys, color=WIRE, lw=1.4, zorder=3)
    ax.text(x + 0.028, (y0 + y1) / 2, label, fontsize=6.9, va="center", color=INK)


def png_dht():
    fig, ax = _fig("1. DHT22   VCC->3V3   DATA->GPIO10 (+10k pull-up)   GND->GND")
    d = _dev(ax, 0.05, 0.42, 0.20, 0.34, "DHT22",
             [("VCC", "R", .80), ("DATA", "R", .58), ("NC", "R", .36), ("GND", "R", .14)])
    e = _dev(ax, 0.70, 0.30, 0.24, 0.58, "ESP32-C3",
             [("GPIO10", "L", .82), ("3V3", "L", .58), ("GND", "L", .34)])
    _w(ax, [d["VCC"], (0.52, d["VCC"][1]), (0.52, e["3V3"][1]), e["3V3"]], RAIL3, "3V3")
    _w(ax, [d["GND"], (0.60, d["GND"][1]), (0.60, e["GND"][1]), e["GND"]], GNDC, "GND")
    _w(ax, [d["DATA"], (0.40, d["DATA"][1]), (0.40, e["GPIO10"][1]), e["GPIO10"]], WIRE, "DATA")
    yt = d["DATA"][1] + 0.20
    _w(ax, [(0.40, d["DATA"][1]), (0.40, d["DATA"][1] + 0.03)])
    _res_v(ax, 0.40, d["DATA"][1] + 0.03, yt - 0.03, "10k")
    _w(ax, [(0.40, yt - 0.03), (0.40, yt), (0.52, yt)], RAIL3)
    ax.plot(0.40, d["DATA"][1], "o", color=WIRE, ms=5, zorder=5)
    ax.text(0.415, yt + 0.01, "to 3V3 (pull-up)", fontsize=6.6, color=RAIL3)
    ax.text(0.5, 0.07, "Verify: dev firmware -> serial temp_c,hum_pct (no -999.0); OLED Temp/Hum",
            ha="center", fontsize=8, color=GREEN)
    fig.savefig(os.path.join(PNG_DIR, "dht22.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def png_mq():
    fig, ax = _fig("2. MQ-135   voltage divider (R1/R2 = 10k), tap node -> GPIO0")
    m = _dev(ax, 0.05, 0.42, 0.20, 0.34, "MQ-135",
             [("VCC 5V", "R", .82), ("AO", "R", .50), ("GND", "R", .18)])
    e = _dev(ax, 0.72, 0.24, 0.22, 0.62, "ESP32-C3",
             [("GPIO0", "L", .80), ("5V/VIN", "L", .55), ("GND", "L", .30)])
    _w(ax, [m["VCC 5V"], (0.60, m["VCC 5V"][1]), (0.60, e["5V/VIN"][1]), e["5V/VIN"]], RAIL5, "5V (VIN)")
    _w(ax, [m["GND"], (0.54, m["GND"][1]), (0.54, e["GND"][1]), e["GND"]], GNDC, "GND")
    yao = m["AO"][1]
    _w(ax, [m["AO"], (0.34, yao)])
    _res_h(ax, 0.34, 0.46, yao, "R1 10k")
    nx = 0.50
    _w(ax, [(0.46, yao), (nx, yao)])
    ax.plot(nx, yao, "o", color=PIN, ms=6, zorder=5)
    _w(ax, [(nx, yao), (0.66, yao), (0.66, e["GPIO0"][1]), e["GPIO0"]], ACCENT, "-> GPIO0")
    yg = yao - 0.20
    _w(ax, [(nx, yao), (nx, yao - 0.03)])
    _res_v(ax, nx, yao - 0.03, yg + 0.03, "R2 10k")
    _w(ax, [(nx, yg), (nx, e["GND"][1]), e["GND"]], GNDC)
    ax.text(0.34, 0.10, "AO(5V) - R1 - NODE - R2 - GND ;  NODE -> GPIO0 (~2.5V safe)",
            fontsize=8, color=GREEN)
    ax.text(0.34, 0.05, "MQ-135 needs ~24-48h burn-in.", fontsize=8, color=ACCENT)
    fig.savefig(os.path.join(PNG_DIR, "mq135.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def png_pms():
    fig, ax = _fig("3. PMS5003   5V power, 3.3V logic (no divider)")
    p = _dev(ax, 0.05, 0.42, 0.20, 0.36, "PMS5003",
             [("VCC", "R", .84), ("GND", "R", .60), ("TX", "R", .38), ("RX", "R", .16)])
    e = _dev(ax, 0.70, 0.28, 0.24, 0.60, "ESP32-C3",
             [("5V/VIN", "L", .80), ("GND", "L", .58), ("GPIO20", "L", .36), ("GPIO21", "L", .16)])
    _w(ax, [p["VCC"], (0.52, p["VCC"][1]), (0.52, e["5V/VIN"][1]), e["5V/VIN"]], RAIL5, "5V")
    _w(ax, [p["GND"], (0.58, p["GND"][1]), (0.58, e["GND"][1]), e["GND"]], GNDC, "GND")
    _w(ax, [p["TX"], (0.64, p["TX"][1]), (0.64, e["GPIO20"][1]), e["GPIO20"]], WIRE, "TX->GPIO20")
    _w(ax, [p["RX"], (0.62, p["RX"][1]), (0.62, e["GPIO21"][1]), e["GPIO21"]], WIRE, "RX<-GPIO21 opt")
    ax.text(0.5, 0.08, "9600 baud. PMS TX is 3.3V logic -> direct. Use a solid 5V (inrush).",
            ha="center", fontsize=8, color=GREEN)
    fig.savefig(os.path.join(PNG_DIR, "pms5003.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def png_oled():
    fig, ax = _fig("4. OLED SSD1306   3.3V only, I2C addr 0x3C")
    o = _dev(ax, 0.05, 0.42, 0.20, 0.36, "OLED SSD1306",
             [("GND", "R", .84), ("VCC 3V3", "R", .60), ("SCL", "R", .38), ("SDA", "R", .16)])
    e = _dev(ax, 0.70, 0.28, 0.24, 0.60, "ESP32-C3",
             [("GND", "L", .80), ("3V3", "L", .58), ("GPIO9", "L", .36), ("GPIO8", "L", .16)])
    _w(ax, [o["GND"], (0.50, o["GND"][1]), (0.50, e["GND"][1]), e["GND"]], GNDC, "GND")
    _w(ax, [o["VCC 3V3"], (0.56, o["VCC 3V3"][1]), (0.56, e["3V3"][1]), e["3V3"]], RAIL3, "3V3")
    _w(ax, [o["SCL"], (0.62, o["SCL"][1]), (0.62, e["GPIO9"][1]), e["GPIO9"]], WIRE, "SCL->GPIO9")
    _w(ax, [o["SDA"], (0.66, o["SDA"][1]), (0.66, e["GPIO8"][1]), e["GPIO8"]], WIRE, "SDA->GPIO8")
    ax.text(0.5, 0.08, "3.3V only. Pull-ups usually built-in. If none found, add 4.7k SDA/SCL->3V3.",
            ha="center", fontsize=8, color=GREEN)
    fig.savefig(os.path.join(PNG_DIR, "oled.png"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def make_pngs():
    png_dht(); png_mq(); png_pms(); png_oled()
    print("Wrote PNGs ->", PNG_DIR)


# ===================== METHOD 1: reportlab PDF =============================
W, H = A4


def _box(c, x, y, w, h, title):
    c.setFillColor(colors.HexColor(DEVICE_FILL))
    c.setStrokeColor(colors.HexColor(DEVICE_EDGE))
    c.setLineWidth(1.3)
    c.roundRect(x, y, w, h, 3 * mm, stroke=1, fill=1)
    c.setFillColor(colors.HexColor(INK))
    c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString(x + w / 2, y + h - 11, title)


def _esp(c, x, y, w, h, pins):
    _box(c, x, y, w, h, "ESP32-C3")
    xy = {}
    for name, side, dy in pins:
        py = y + h - dy * mm
        px = x + w if side == "R" else x
        c.setStrokeColor(colors.HexColor(WIRE)); c.setLineWidth(1.2)
        if side == "R":
            c.line(px, py, px + 5 * mm, py)
        else:
            c.line(px - 5 * mm, py, px, py)
        c.setFillColor(colors.HexColor(PIN)); c.circle(px, py, 1.8, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica", 7)
        if side == "R":
            c.drawString(px + 3, py - 2.2, name)
        else:
            c.drawRightString(px - 3, py - 2.2, name)
        xy[name] = (px, py)
    return xy


def _wirec(c, pts, color=WIRE, lbl=None):
    c.setStrokeColor(colors.HexColor(color)); c.setLineWidth(1.2)
    p = c.beginPath(); p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    c.drawPath(p)
    if lbl:
        i = max(1, len(pts) // 2)
        c.setFillColor(colors.HexColor(ACCENT)); c.setFont("Helvetica", 6.6)
        c.drawCentredString((pts[i - 1][0] + pts[i][0]) / 2, (pts[i - 1][1] + pts[i][1]) / 2 + 2, lbl)


def _resh(c, x0, x1, y, label):
    n = 7; step = (x1 - x0) / n
    p = c.beginPath(); p.moveTo(x0, y)
    for i in range(1, n):
        p.lineTo(x0 + step * i, y + (3 if i % 2 else -3))
    p.lineTo(x1, y)
    c.setStrokeColor(colors.HexColor(WIRE)); c.setLineWidth(1.2); c.drawPath(p)
    c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica", 6.8)
    c.drawCentredString((x0 + x1) / 2, y + 6, label)


def _resv(c, x, y0, y1, label):
    n = 7; step = (y1 - y0) / n
    p = c.beginPath(); p.moveTo(x, y0)
    for i in range(1, n):
        p.lineTo(x + (3 if i % 2 else -3), y0 + step * i)
    p.lineTo(x, y1)
    c.setStrokeColor(colors.HexColor(WIRE)); c.setLineWidth(1.2); c.drawPath(p)
    c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica", 6.8)
    c.drawString(x + 6, (y0 + y1) / 2, label)


def _head(c, text, sub=""):
    c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica-Bold", 15)
    c.drawString(18 * mm, H - 18 * mm, text)
    if sub:
        c.setFillColor(colors.HexColor("#55606e")); c.setFont("Helvetica", 8.6)
        c.drawString(18 * mm, H - 23 * mm, sub)


def pdf_title(c):
    _head(c, "Air Quality Monitor - Wiring Guide",
          "ESP32-C3 DevKitM-1  |  3.3V logic  |  pins match firmware/include/config.h")
    y = H - 60 * mm
    c.setFillColor(colors.HexColor("#fff6e8")); c.setStrokeColor(colors.HexColor("#e0a000"))
    c.setLineWidth(1); c.roundRect(18 * mm, y, W - 36 * mm, 30 * mm, 3 * mm, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#7a5200")); c.setFont("Helvetica-Bold", 9.5)
    c.drawString(22 * mm, y + 24 * mm, "SAFETY")
    c.setFont("Helvetica", 8)
    for i, ln in enumerate([
        "- ESP32-C3 GPIO pins are 3.3V ONLY. Never feed 5V into a GPIO.",
        "- MQ-135 runs on 5V; its analog output can exceed 3.3V -> divider MANDATORY on GPIO0.",
        "- OLED and DHT22 are 3.3V devices. All devices share a common GND.",
    ]):
        c.drawString(22 * mm, y + 18 * mm - i * 4.8 * mm, ln)

    ty = y - 12 * mm
    c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica-Bold", 10.5)
    c.drawString(18 * mm, ty, "Resistors you need")
    rows = [
        ("MQ-135 voltage divider", "2 x 10 kOhm", "AO -> R1 -> node(GPIO0); node -> R2 -> GND"),
        ("DHT22 pull-up", "10 kOhm", "DATA(GPIO10) -> 10k -> 3V3"),
        ("OLED I2C pull-ups", "built-in / 4.7k x2", "only if no I2C device found"),
        ("LED limit (Phase 6)", "220 Ohm x3", "GPIOx -> 220 -> LED -> GND"),
    ]
    ry = ty - 7 * mm
    for i, (a, b, d) in enumerate(rows):
        c.setFillColor(colors.HexColor("#f2f4f7") if i % 2 == 0 else colors.white)
        c.rect(18 * mm, ry - 1.6 * mm, W - 36 * mm, 6.2 * mm, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica", 8)
        c.drawString(20 * mm, ry, a)
        c.setFont("Helvetica-Bold", 8); c.drawString(70 * mm, ry, b)
        c.setFont("Helvetica", 8); c.drawString(108 * mm, ry, d)
        ry -= 6.6 * mm

    py = ry - 6 * mm
    c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica-Bold", 10.5)
    c.drawString(18 * mm, py, "Pin map  (firmware/include/config.h)")
    pins = [
        ("DHT22 DATA", "GPIO10"), ("MQ-135 AO (after divider)", "GPIO0 (ADC1_CH0)"),
        ("PMS5003 TX -> ESP", "GPIO20"), ("PMS5003 RX <- ESP (opt)", "GPIO21"),
        ("OLED SDA", "GPIO8"), ("OLED SCL", "GPIO9"), ("LEDs GOOD/MOD/POOR", "GPIO4 / 5 / 6"),
    ]
    ry2 = py - 7 * mm
    for i, (a, b) in enumerate(pins):
        c.setFillColor(colors.HexColor("#f2f4f7") if i % 2 == 0 else colors.white)
        c.rect(18 * mm, ry2 - 1.6 * mm, W - 36 * mm, 6.2 * mm, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica", 8)
        c.drawString(20 * mm, ry2, a)
        c.setFont("Helvetica-Bold", 8); c.drawString(90 * mm, ry2, b)
        ry2 -= 6.6 * mm

    by = ry2 - 8 * mm
    c.setFillColor(colors.HexColor(GREEN)); c.setFont("Helvetica-Bold", 10.5)
    c.drawString(18 * mm, by, "Bring-up order (test one block at a time)")
    c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica", 8)
    for i, ln in enumerate([
        "1. DHT22  -> flash dev firmware; serial temp_c,hum_pct fill in (no -999.0).",
        "2. OLED   -> '# I2C device found at 0x3C' and '# OLED init OK'.",
        "3. MQ-135 -> mq135_raw ~300-400 clean air (burn-in 24-48h).",
        "4. PMS    -> n03..n100 non-zero; frames_ok increases, bad=0.",
    ]):
        c.drawString(20 * mm, by - 6 * mm - i * 5 * mm, ln)

    c.setFillColor(colors.HexColor("#8a8a8a")); c.setFont("Helvetica-Oblique", 7)
    c.drawString(18 * mm, 16 * mm, "Also see: docs/WIRING.md (text) and docs/schematics/*.png (images).")
    c.showPage()


def pdf_dht(c):
    _head(c, "1. DHT22 (temp + humidity) - START HERE",
          "VCC->3V3, DATA->GPIO10 (+10k pull-up to 3V3), GND->GND")
    dx, dy, dw, dh = 30 * mm, 120 * mm, 42 * mm, 55 * mm
    _box(c, dx, dy, dw, dh, "DHT22")
    dht = {}
    for name, yy in [("VCC", dy + dh - 14 * mm), ("DATA", dy + dh - 27 * mm),
                     ("NC", dy + dh - 40 * mm), ("GND", dy + dh - 51 * mm)]:
        c.setStrokeColor(colors.HexColor(WIRE)); c.setLineWidth(1.2)
        c.line(dx + dw, yy, dx + dw + 5 * mm, yy)
        c.setFillColor(colors.HexColor(PIN)); c.circle(dx + dw, yy, 1.8, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica", 7)
        c.drawRightString(dx + dw - 4, yy - 2.2, name)
        dht[name] = (dx + dw, yy)
    esp = _esp(c, 150 * mm, 105 * mm, 40 * mm, 75 * mm,
               [("GPIO10", "L", 22), ("3V3", "L", 40), ("GND", "L", 58)])
    _wirec(c, [dht["VCC"], (110 * mm, dht["VCC"][1]), (110 * mm, esp["3V3"][1]), esp["3V3"]], RAIL3, "3V3")
    _wirec(c, [dht["GND"], (118 * mm, dht["GND"][1]), (118 * mm, esp["GND"][1]), esp["GND"]], GNDC, "GND")
    _wirec(c, [dht["DATA"], (100 * mm, dht["DATA"][1]), (100 * mm, esp["GPIO10"][1]), esp["GPIO10"]], WIRE, "DATA")
    c.setStrokeColor(colors.HexColor(WIRE)); c.setLineWidth(1.2)
    c.line(100 * mm, dht["DATA"][1], 100 * mm, dht["DATA"][1] + 10 * mm)
    _resv(c, 100 * mm, dht["DATA"][1] + 10 * mm, dht["DATA"][1] + 30 * mm, "10k")
    c.line(100 * mm, dht["DATA"][1] + 30 * mm, 100 * mm, dht["DATA"][1] + 38 * mm)
    _wirec(c, [(100 * mm, dht["DATA"][1] + 38 * mm), (110 * mm, dht["DATA"][1] + 38 * mm),
               (110 * mm, esp["3V3"][1])], RAIL3)
    c.setFillColor(colors.HexColor(ACCENT)); c.setFont("Helvetica", 6.8)
    c.drawString(102 * mm, dht["DATA"][1] + 39 * mm, "3V3 (pull-up)")
    c.setFillColor(colors.HexColor(GREEN)); c.setFont("Helvetica", 9)
    c.drawString(18 * mm, 80 * mm, "Verify: flash dev firmware. Serial shows temp_c,hum_pct (no -999.0); OLED Temp/Hum.")
    c.showPage()


def pdf_mq(c):
    _head(c, "2. MQ-135 (analog) - REQUIRES VOLTAGE DIVIDER",
          "MQ-135 VCC=5V; AO halved by R1/R2 (10k each) before GPIO0")
    mx, my, mw, mh = 28 * mm, 115 * mm, 40 * mm, 60 * mm
    _box(c, mx, my, mw, mh, "MQ-135")
    mq = {}
    for name, yy in [("VCC 5V", my + mh - 15 * mm), ("AO", my + mh - 33 * mm), ("GND", my + mh - 51 * mm)]:
        c.setFillColor(colors.HexColor(PIN)); c.circle(mx + mw, yy, 1.8, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica", 7)
        c.drawRightString(mx + mw - 4, yy - 2.2, name)
        mq[name] = (mx + mw, yy)
    esp = _esp(c, 155 * mm, 100 * mm, 38 * mm, 80 * mm,
               [("GPIO0", "L", 24), ("5V/VIN", "L", 44), ("GND", "L", 64)])
    _wirec(c, [mq["VCC 5V"], (120 * mm, mq["VCC 5V"][1]), (120 * mm, esp["5V/VIN"][1]), esp["5V/VIN"]], RAIL5, "5V (VIN)")
    _wirec(c, [mq["GND"], (112 * mm, mq["GND"][1]), (112 * mm, esp["GND"][1]), esp["GND"]], GNDC, "GND")
    yao = mq["AO"][1]
    _wirec(c, [mq["AO"], (72 * mm, yao)])
    _resh(c, 72 * mm, 88 * mm, yao, "R1 10k")
    nx = 96 * mm
    _wirec(c, [(88 * mm, yao), (nx, yao)])
    c.setFillColor(colors.HexColor(PIN)); c.circle(nx, yao, 2.2, stroke=0, fill=1)
    _wirec(c, [(nx, yao), (135 * mm, yao), (135 * mm, esp["GPIO0"][1]), esp["GPIO0"]], ACCENT, "-> GPIO0")
    c.setStrokeColor(colors.HexColor(WIRE)); c.setLineWidth(1.2)
    c.line(nx, yao, nx, yao - 15 * mm)
    _resv(c, nx, yao - 15 * mm, yao - 35 * mm, "R2 10k")
    c.line(nx, yao - 35 * mm, nx, yao - 45 * mm)
    _wirec(c, [(nx, yao - 45 * mm), (nx, esp["GND"][1]), esp["GND"]], GNDC)
    c.setFillColor(colors.HexColor(GREEN)); c.setFont("Helvetica", 9)
    c.drawString(18 * mm, 78 * mm, "AO(5V) -> R1(10k) -> NODE -> R2(10k) -> GND ; tap NODE -> GPIO0 (~2.5V safe).")
    c.setFillColor(colors.HexColor(ACCENT))
    c.drawString(18 * mm, 72 * mm, "MQ-135 needs ~24-48h burn-in for stable readings.")
    c.showPage()


def pdf_pms_oled(c):
    _head(c, "3. PMS5003 (UART)    &    4. OLED SSD1306 (I2C)",
          "PMS: 5V power, 3.3V logic (no divider).  OLED: 3.3V only, addr 0x3C.")
    px, py, pw, ph = 28 * mm, 150 * mm, 40 * mm, 60 * mm
    _box(c, px, py, pw, ph, "PMS5003")
    pms = {}
    for name, yy in [("VCC 5V", py + ph - 12 * mm), ("GND", py + ph - 24 * mm),
                     ("TX", py + ph - 36 * mm), ("RX", py + ph - 48 * mm)]:
        c.setFillColor(colors.HexColor(PIN)); c.circle(px + pw, yy, 1.8, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica", 7)
        c.drawRightString(px + pw - 4, yy - 2.2, name)
        pms[name] = (px + pw, yy)
    esp = _esp(c, 155 * mm, 150 * mm, 38 * mm, 60 * mm,
               [("5V/VIN", "L", 12), ("GND", "L", 24), ("GPIO20", "L", 36), ("GPIO21", "L", 48)])
    _wirec(c, [pms["VCC 5V"], (120 * mm, pms["VCC 5V"][1]), (120 * mm, esp["5V/VIN"][1]), esp["5V/VIN"]], RAIL5, "5V")
    _wirec(c, [pms["GND"], (112 * mm, pms["GND"][1]), (112 * mm, esp["GND"][1]), esp["GND"]], GNDC, "GND")
    _wirec(c, [pms["TX"], (128 * mm, pms["TX"][1]), (128 * mm, esp["GPIO20"][1]), esp["GPIO20"]], WIRE, "TX->GPIO20")
    _wirec(c, [pms["RX"], (135 * mm, pms["RX"][1]), (135 * mm, esp["GPIO21"][1]), esp["GPIO21"]], WIRE, "RX<-GPIO21 opt")
    c.setFillColor(colors.HexColor(GREEN)); c.setFont("Helvetica", 8)
    c.drawString(28 * mm, 140 * mm, "9600 baud. PMS TX is 3.3V logic -> direct. Use a solid 5V (inrush).")

    ox, oy, ow, oh = 28 * mm, 55 * mm, 45 * mm, 55 * mm
    _box(c, ox, oy, ow, oh, "OLED SSD1306")
    oled = {}
    for name, yy in [("GND", oy + oh - 12 * mm), ("VCC 3V3", oy + oh - 24 * mm),
                     ("SCL", oy + oh - 36 * mm), ("SDA", oy + oh - 48 * mm)]:
        c.setFillColor(colors.HexColor(PIN)); c.circle(ox + ow, yy, 1.8, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(INK)); c.setFont("Helvetica", 7)
        c.drawRightString(ox + ow - 4, yy - 2.2, name)
        oled[name] = (ox + ow, yy)
    esp2 = _esp(c, 155 * mm, 55 * mm, 38 * mm, 60 * mm,
                [("GND", "L", 12), ("3V3", "L", 24), ("GPIO9", "L", 36), ("GPIO8", "L", 48)])
    _wirec(c, [oled["GND"], (120 * mm, oled["GND"][1]), (120 * mm, esp2["GND"][1]), esp2["GND"]], GNDC, "GND")
    _wirec(c, [oled["VCC 3V3"], (128 * mm, oled["VCC 3V3"][1]), (128 * mm, esp2["3V3"][1]), esp2["3V3"]], RAIL3, "3V3")
    _wirec(c, [oled["SCL"], (135 * mm, oled["SCL"][1]), (135 * mm, esp2["GPIO9"][1]), esp2["GPIO9"]], WIRE, "SCL->GPIO9")
    _wirec(c, [oled["SDA"], (142 * mm, oled["SDA"][1]), (142 * mm, esp2["GPIO8"][1]), esp2["GPIO8"]], WIRE, "SDA->GPIO8")
    c.setFillColor(colors.HexColor(GREEN)); c.setFont("Helvetica", 8)
    c.drawString(28 * mm, 46 * mm, "3.3V only. Pull-ups usually built-in. If none found, add 4.7k SDA/SCL->3V3.")
    c.showPage()


def make_pdf():
    c = canvas.Canvas(PDF_OUT, pagesize=A4)
    c.setTitle("Air Quality Monitor - Wiring Guide")
    pdf_title(c)
    pdf_dht(c)
    pdf_mq(c)
    pdf_pms_oled(c)
    c.save()
    print("Wrote PDF ->", PDF_OUT)


if __name__ == "__main__":
    make_pngs()
    make_pdf()
