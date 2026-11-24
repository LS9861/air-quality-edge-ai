"""
Generate a clean, printable wiring PDF for the Air Quality Monitor.

Draws simple schematics (device boxes, wires, resistor symbols, labels) with
reportlab. Output: docs/WIRING.pdf

Run:  python docs/make_wiring_pdf.py
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "WIRING.pdf")

W, H = A4


def box(c, x, y, w, h, title, fill=colors.HexColor("#eef3fb")):
    c.setFillColor(fill)
    c.setStrokeColor(colors.HexColor("#2b3a55"))
    c.setLineWidth(1.2)
    c.roundRect(x, y, w, h, 3 * mm, stroke=1, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + w / 2, y + h - 6, title)


def wire(c, x1, y1, x2, y2, color=colors.HexColor("#333333"), label=None,
         lw=1.1):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x1, y1, x2, y2)
    if label:
        c.setFillColor(colors.HexColor("#b00020"))
        c.setFont("Helvetica", 6.5)
        c.drawString((x1 + x2) / 2 + 2, (y1 + y2) / 2 + 1.5, label)


def resistor(c, x, y, w, h, label):
    """Zig-zag resistor symbol, drawn horizontally within box (x,y,w,h)."""
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.1)
    n = 6
    step = w / n
    pts = [(x, y + h / 2)]
    for i in range(1, n):
        px = x + i * step
        py = y + (h if i % 2 == 0 else 0)
        pts.append((px, py))
    pts.append((x + w, y + h / 2))
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    c.drawPath(p)
    c.setFont("Helvetica", 6.5)
    c.setFillColor(colors.black)
    c.drawCentredString(x + w / 2, y - 8, label)


def pindot(c, x, y, label, side="r"):
    c.setFillColor(colors.HexColor("#1f6feb"))
    c.circle(x, y, 1.6, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 6.5)
    if side == "r":
        c.drawString(x + 4, y - 2, label)
    else:
        c.drawRightString(x - 4, y - 2, label)


def header(c, text, sub=""):
    c.setFillColor(colors.HexColor("#1f2d3d"))
    c.setFont("Helvetica-Bold", 15)
    c.drawString(18 * mm, H - 18 * mm, text)
    if sub:
        c.setFont("Helvetica", 8.5)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawString(18 * mm, H - 23 * mm, sub)


# ----------------------------------------------------------------------------
def page_title(c):
    header(c, "Air Quality Monitor - Wiring Guide",
           "ESP32-C3 DevKitM-1  |  3.3V logic  |  pins match config.h")

    # Safety box
    y = H - 62 * mm
    c.setFillColor(colors.HexColor("#fff4e5"))
    c.setStrokeColor(colors.HexColor("#e0a000"))
    c.setLineWidth(1)
    c.roundRect(18 * mm, y, W - 36 * mm, 32 * mm, 3 * mm, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#7a5200"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(22 * mm, y + 26 * mm, "SAFETY")
    c.setFont("Helvetica", 8)
    lines = [
        "- ESP32-C3 GPIO pins are 3.3V ONLY. Never feed 5V into a GPIO.",
        "- MQ-135 runs on 5V; its analog output can exceed 3.3V -> voltage divider MANDATORY on GPIO0.",
        "- OLED and DHT22 are 3.3V devices.",
        "- Common ground (GND) for all devices.",
    ]
    for i, ln in enumerate(lines):
        c.drawString(22 * mm, y + 20 * mm - i * 4.6 * mm, ln)

    # Resistor table
    ty = y - 10 * mm
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(18 * mm, ty, "Resistors you need")
    rows = [
        ("MQ-135 voltage divider", "2 x 10 kOhm", "AO -> R1 -> node (GPIO0); node -> R2 -> GND"),
        ("DHT22 pull-up", "10 kOhm", "DATA (GPIO10) -> 10k -> 3V3"),
        ("OLED I2C pull-ups", "built-in / 2 x 4.7k", "only if no I2C device found"),
        ("LED current-limit (Phase 6)", "3 x 220 Ohm", "GPIOx -> 220 -> LED -> GND"),
    ]
    ry = ty - 6 * mm
    c.setFont("Helvetica", 8)
    for i, (a, b, d) in enumerate(rows):
        c.setFillColor(colors.HexColor("#f0f0f0") if i % 2 == 0 else colors.white)
        c.rect(18 * mm, ry - 1.5 * mm, W - 36 * mm, 6 * mm, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.drawString(20 * mm, ry, a)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(72 * mm, ry, b)
        c.setFont("Helvetica", 8)
        c.drawString(110 * mm, ry, d)
        ry -= 6.5 * mm

    # Pin map table
    py = ry - 6 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(18 * mm, py, "Pin map (config.h)")
    pin_rows = [
        ("DHT22 DATA", "GPIO10"),
        ("MQ-135 AO (after divider)", "GPIO0  (ADC1_CH0)"),
        ("PMS5003 TX -> ESP", "GPIO20"),
        ("PMS5003 RX <- ESP (opt)", "GPIO21"),
        ("OLED SDA", "GPIO8"),
        ("OLED SCL", "GPIO9"),
        ("LEDs GOOD/MOD/POOR", "GPIO4 / 5 / 6"),
    ]
    ry2 = py - 6 * mm
    for i, (a, b) in enumerate(pin_rows):
        c.setFillColor(colors.HexColor("#f0f0f0") if i % 2 == 0 else colors.white)
        c.rect(18 * mm, ry2 - 1.5 * mm, W - 36 * mm, 6 * mm, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        c.drawString(20 * mm, ry2, a)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(90 * mm, ry2, b)
        ry2 -= 6.5 * mm

    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(colors.HexColor("#777777"))
    c.drawString(18 * mm, 18 * mm, "Generated by docs/make_wiring_pdf.py")
    c.showPage()


def page_dht(c):
    header(c, "1. DHT22 (temp + humidity) - START HERE",
           "Wire VCC->3V3, DATA->GPIO10 with 10k pull-up, GND->GND")
    # ESP box
    ex, ey, ew, eh = 150 * mm, 110 * mm, 40 * mm, 60 * mm
    box(c, ex, ey, ew, eh, "ESP32-C3")
    pindot(c, ex, ey + eh - 20 * mm, "GPIO10", "l")
    pindot(c, ex, ey + eh - 35 * mm, "3V3", "l")
    pindot(c, ex, ey + eh - 50 * mm, "GND", "l")

    # DHT box
    dx, dy, dw, dh = 40 * mm, 110 * mm, 40 * mm, 60 * mm
    box(c, dx, dy, dw, dh, "DHT22")
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.black)
    c.drawRightString(dx + dw - 3, dy + dh - 20 * mm, "VCC")
    c.drawRightString(dx + dw - 3, dy + dh - 30 * mm, "DATA")
    c.drawRightString(dx + dw - 3, dy + dh - 40 * mm, "NC")
    c.drawRightString(dx + dw - 3, dy + dh - 50 * mm, "GND")

    # wires
    wire(c, dx + dw, dy + dh - 20 * mm, ex, ey + eh - 35 * mm, label="3V3")
    wire(c, dx + dw, dy + dh - 50 * mm, ex, ey + eh - 50 * mm, label="GND")
    # data wire with pull-up
    midx = (dx + dw + ex) / 2
    wire(c, dx + dw, dy + dh - 30 * mm, ex, ey + eh - 20 * mm, label="DATA")
    # pull-up tap
    tapx = midx
    tapy = dy + dh - 30 * mm
    c.setStrokeColor(colors.HexColor("#333333"))
    c.line(tapx, tapy, tapx, tapy + 25 * mm)  # up to 3V3 rail
    resistor(c, tapx - 8 * mm, tapy + 8 * mm, 16 * mm, 5 * mm, "10k")
    # 3V3 rail short
    c.setStrokeColor(colors.HexColor("#333333"))
    c.line(tapx, tapy + 25 * mm, tapx + 20 * mm, tapy + 25 * mm)
    wire(c, tapx + 20 * mm, tapy + 25 * mm, ex, ey + eh - 35 * mm)
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#b00020"))
    c.drawString(tapx + 2, tapy + 26 * mm, "3V3 (pull-up)")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.drawString(18 * mm, 80 * mm, "Verify: flash dev firmware. Serial shows temp_c,hum_pct")
    c.drawString(18 * mm, 74 * mm, "and NO -999.0.  OLED shows Temp:.. Hum:..")
    c.showPage()


def page_mq(c):
    header(c, "2. MQ-135 (air quality, analog) - VOLTAGE DIVIDER",
           "MQ-135 VCC=5V. AO must be halved via R1/R2 before GPIO0.")
    ex, ey, ew, eh = 155 * mm, 100 * mm, 38 * mm, 65 * mm
    box(c, ex, ey, ew, eh, "ESP32-C3")
    pindot(c, ex, ey + eh - 20 * mm, "GPIO0 (ADC)", "l")

    mx, my, mw, mh = 30 * mm, 100 * mm, 40 * mm, 65 * mm
    box(c, mx, my, mw, mh, "MQ-135")
    c.setFont("Helvetica", 7)
    c.drawRightString(mx + mw - 3, my + mh - 20 * mm, "VCC (5V)")
    c.drawRightString(mx + mw - 3, my + mh - 35 * mm, "AO")
    c.drawRightString(mx + mw - 3, my + mh - 50 * mm, "GND")

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.HexColor("#b00020"))
    c.drawString(mx, my + mh + 4, "5V supply (VIN)")

    # VCC/GND straight wires to rails (just draw and label)
    wire(c, mx + mw, my + mh - 20 * mm, 120 * mm, my + mh - 20 * mm, label="5V (VIN)")
    wire(c, mx + mw, my + mh - 50 * mm, 120 * mm, my + mh - 50 * mm, label="GND")

    # AO path: AO -> R1 -> node -> GPIO0 ; node -> R2 -> GND
    aoy = my + mh - 35 * mm
    wire(c, mx + mw, aoy, 90 * mm, aoy)          # AO to R1 left
    resistor(c, 90 * mm, aoy - 2.5 * mm, 16 * mm, 5 * mm, "R1 10k")
    nodex = 108 * mm
    wire(c, 106 * mm, aoy, nodex, aoy)
    c.setFillColor(colors.HexColor("#1f6feb"))
    c.circle(nodex, aoy, 1.8, stroke=0, fill=1)
    wire(c, nodex, aoy, ex, ey + eh - 20 * mm, label="-> GPIO0")
    # R2 down to GND
    c.setStrokeColor(colors.HexColor("#333333"))
    c.line(nodex, aoy, nodex, aoy - 18 * mm)
    resistor(c, nodex - 8 * mm, aoy - 25 * mm, 16 * mm, 5 * mm, "R2 10k")
    c.line(nodex, aoy - 25 * mm, nodex, aoy - 30 * mm)
    wire(c, nodex, aoy - 30 * mm, ex, ey + eh - 50 * mm, label="GND")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.drawString(18 * mm, 70 * mm, "AO(5V) -> R1(10k) -> NODE -> R2(10k) -> GND")
    c.drawString(18 * mm, 64 * mm, "Tap NODE (between R1,R2) -> GPIO0.  Node ~ 2.5V max = safe.")
    c.drawString(18 * mm, 58 * mm, "MQ-135 needs ~24-48h burn-in for stable readings.")
    c.showPage()


def page_pms_oled(c):
    header(c, "3. PMS5003 (UART)   &   4. OLED SSD1306 (I2C)",
           "PMS: 5V power, 3.3V logic (no divider). OLED: 3.3V only.")

    # PMS
    box(c, 30 * mm, 155 * mm, 42 * mm, 62 * mm, "PMS5003")
    c.setFont("Helvetica", 7)
    for i, n in enumerate(["VCC (5V)", "GND", "TX", "RX", "SET/RST"]):
        c.drawRightString(30 * mm + 39 * mm, 155 * mm + 50 * mm - i * 9 * mm, n)
    box(c, 150 * mm, 155 * mm, 40 * mm, 62 * mm, "ESP32-C3")
    c.setFont("Helvetica", 7)
    c.drawString(152 * mm, 155 * mm + 50 * mm, "5V (VIN)")
    c.drawString(152 * mm, 155 * mm + 41 * mm, "GND")
    c.drawString(152 * mm, 155 * mm + 32 * mm, "GPIO20 (RX)")
    c.drawString(152 * mm, 155 * mm + 23 * mm, "GPIO21 (TX)")
    # wires
    wire(c, 72 * mm, 155 * mm + 50 * mm, 150 * mm, 155 * mm + 50 * mm, label="5V")
    wire(c, 72 * mm, 155 * mm + 41 * mm, 150 * mm, 155 * mm + 41 * mm, label="GND")
    wire(c, 72 * mm, 155 * mm + 32 * mm, 150 * mm, 155 * mm + 32 * mm, label="TX->GPIO20")
    wire(c, 72 * mm, 155 * mm + 23 * mm, 150 * mm, 155 * mm + 23 * mm, label="RX<-GPIO21 (opt)")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 7.5)
    c.drawString(30 * mm, 150 * mm, "9600 baud. PMS TX is 3.3V logic -> direct, NO divider.")
    c.drawString(30 * mm, 144 * mm, "PMS5003 has inrush current: use a solid 5V supply.")

    # OLED
    box(c, 45 * mm, 55 * mm, 42 * mm, 60 * mm, "OLED SSD1306")
    c.setFont("Helvetica", 7)
    for i, n in enumerate(["GND", "VCC (3V3)", "SCL", "SDA"]):
        c.drawRightString(45 * mm + 39 * mm, 55 * mm + 45 * mm - i * 10 * mm, n)
    box(c, 150 * mm, 55 * mm, 40 * mm, 60 * mm, "ESP32-C3")
    c.setFont("Helvetica", 7)
    c.drawString(152 * mm, 55 * mm + 45 * mm, "GND")
    c.drawString(152 * mm, 55 * mm + 35 * mm, "3V3")
    c.drawString(152 * mm, 55 * mm + 25 * mm, "GPIO9 (SCL)")
    c.drawString(152 * mm, 55 * mm + 15 * mm, "GPIO8 (SDA)")
    wire(c, 87 * mm, 55 * mm + 45 * mm, 150 * mm, 55 * mm + 45 * mm, label="GND")
    wire(c, 87 * mm, 55 * mm + 35 * mm, 150 * mm, 55 * mm + 35 * mm, label="3V3")
    wire(c, 87 * mm, 55 * mm + 25 * mm, 150 * mm, 55 * mm + 25 * mm, label="SCL")
    wire(c, 87 * mm, 55 * mm + 15 * mm, 150 * mm, 55 * mm + 15 * mm, label="SDA")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 7.5)
    c.drawString(45 * mm, 50 * mm, "Addr 0x3C. 3.3V ONLY. Pull-ups usually built-in.")
    c.drawString(45 * mm, 44 * mm, "If 'I2C: no devices found', add 4.7k SDA/SCL -> 3V3.")
    c.showPage()


def main():
    c = canvas.Canvas(OUT, pagesize=A4)
    c.setTitle("Air Quality Monitor - Wiring Guide")
    page_title(c)
    page_dht(c)
    page_mq(c)
    page_pms_oled(c)
    c.save()
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
