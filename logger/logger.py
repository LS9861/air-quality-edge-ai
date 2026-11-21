import serial
import serial.tools.list_ports
import csv
import time
import os
from datetime import datetime

BAUD = 115200
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT_DIR, "data", "raw")

SCENES = {
    "good": "window open / clean air",
    "moderate": "window closed / stuffy",
    "poor": "candle smoke",
}

EXPECTED_HEADER = (
    "timestamp_ms,pm1_cf1,pm25_cf1,pm10_cf1,pm1_atm,pm25_atm,pm10_atm,"
    "n03,n05,n10,n25,n50,n100,mq135_raw,temp_c,hum_pct"
)
EXPECTED_COLS = len(EXPECTED_HEADER.split(","))


def find_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "USB" in p.description or "CH340" in p.description or "CP210" in p.description:
            return p.device
    return None


def ask_scene():
    print("Select scene label for this recording:")
    for i, (key, desc) in enumerate(SCENES.items(), 1):
        print(f"  {i}) {key:<9} - {desc}")
    while True:
        choice = input("Enter label (good/moderate/poor): ").strip().lower()
        if choice in SCENES:
            return choice
        print("  Invalid. Choose one of:", ", ".join(SCENES))


def main():
    scene = ask_scene()
    out_dir = os.path.join(OUT_DIR, scene)
    os.makedirs(out_dir, exist_ok=True)

    port = find_port() or input("Enter COM port (e.g. COM3): ").strip()
    filename = os.path.join(out_dir, "air_quality_" + scene + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv")

    print(f"Connecting {port} @ {BAUD}...")
    with serial.Serial(port, BAUD, timeout=1) as ser, open(filename, "w", newline="") as f:
        time.sleep(2)
        writer = csv.writer(f)
        writer.writerow(EXPECTED_HEADER.split(","))
        f.flush()
        print(f"Saving to {filename} (Ctrl+C to stop)")

        try:
            while True:
                try:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                except (serial.SerialException, OSError) as e:
                    print(f"\n[serial error] {e} - reconnecting in 3s...")
                    time.sleep(3)
                    try:
                        ser.close()
                    except Exception:
                        pass
                    ser = serial.Serial(port, BAUD, timeout=1)
                    time.sleep(2)
                    continue

                if not line or line.startswith("#"):
                    continue
                cols = line.split(",")
                if line == EXPECTED_HEADER or len(cols) != EXPECTED_COLS:
                    continue

                writer.writerow(cols)
                f.flush()
                print(line)
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
