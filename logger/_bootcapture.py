"""Boot-capture helper: reset the ESP32-C3 via RTS and print boot/serial text.

Useful for seeing messages printed before a normal capture can attach
(e.g. I2C scan, OLED init, the CSV header, first PMS frame hex dump).

Usage:
    python logger/_bootcapture.py [PORT] [SECONDS]
    python logger/_bootcapture.py COM6 6
"""
import sys
import time
try:
    import serial
except ImportError:
    sys.exit("pyserial not installed. Run: pip install pyserial")

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM6"
SECONDS = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0

try:
    s = serial.Serial(PORT, 115200, timeout=0.3)
except serial.SerialException as e:
    sys.exit(f"Could not open {PORT}: {e}\n(is the serial monitor / another program using it?)")

# ESP32-C3 reset via RTS (EN). Pulse EN low then release to reboot.
s.dtr = False
s.rts = False
time.sleep(0.1)
s.rts = True   # hold EN low -> reset
time.sleep(0.15)
s.rts = False  # release -> boot
time.sleep(0.05)

end = time.time() + SECONDS
buf = []
while time.time() < end:
    try:
        line = s.readline()
        if line:
            buf.append(line.decode("utf-8", errors="replace").rstrip("\r\n"))
    except Exception:
        pass
s.close()
print(f"===== BOOT CAPTURE on {PORT} ({SECONDS:.0f}s) =====")
print("\n".join(buf))

