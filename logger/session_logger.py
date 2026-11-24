"""
Named-session data logger for the Air Quality project.

Instead of picking a scene from a menu, you type a free-form SESSION NAME
for each recording, e.g.:

    good 1
    good 2
    good 3
    moderate 1
    moderate 2
    poor 1

The first word must be the class label (good / moderate / poor) so files land
in the right training folder. The rest is a human label for the session.

Saved as:   data/raw/<class>/<name_with_underscores>_<timestamp>.csv

Example:
    name "good 1"  ->  data/raw/good/good_1_20261124_143001.csv

Usage (arguments are auto-detected, any order):
    python session_logger.py                   (prompts for name + port)
    python session_logger.py good1             (name only; port auto-detected)
    python session_logger.py "good 1"          (name with a number)
    python session_logger.py COM3 good1        (port + name)
    python session_logger.py good1 COM3        (order does not matter)

Everything that is NOT a COMx/device path is treated as the session name,
so `good 1` (unquoted) also works.

Press Ctrl+C to stop a recording. The CSV header is written immediately, so
even a very short run produces a valid file.
"""

import serial
import serial.tools.list_ports
import csv
import sys
import time
import os
import re
from datetime import datetime

BAUD = 115200
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT_DIR, "data", "raw")

# The three training classes. The first token of the session name must be
# one of these (case-insensitive).
CLASSES = ("good", "moderate", "poor")

# Must match CSV_HEADER in firmware/include/config.h
EXPECTED_HEADER = (
    "timestamp_ms,pm1_cf1,pm25_cf1,pm10_cf1,pm1_atm,pm25_atm,pm10_atm,"
    "n03,n05,n10,n25,n50,n100,mq135_raw,temp_c,hum_pct"
)
EXPECTED_COLS = len(EXPECTED_HEADER.split(","))


def find_port():
    """Return the first likely USB-serial port, or None."""
    for p in serial.tools.list_ports.comports():
        desc = p.description or ""
        if "USB" in desc or "CH340" in desc or "CP210" in desc or "JTAG" in desc:
            return p.device
    return None


def parse_session_name(raw):
    """
    Turn a free-form user string into (class_label, safe_stem).

    'good 1'      -> ('good', 'good_1')
    'Moderate-2'  -> ('moderate', 'moderate_2')
    'poor candle' -> ('poor', 'poor_candle')
    """
    raw = raw.strip()
    if not raw:
        raise ValueError("empty session name")

    # Split on whitespace and common separators, so both 'good 1' and
    # 'moderate-2' / 'good.1' / 'poor_candle' resolve the class correctly.
    # Also handle a number glued to the class word: 'good1' -> 'good' + '1'.
    m = re.match(r"^(good|moderate|poor)(.*)$", raw, re.IGNORECASE)
    if m:
        cls = m.group(1).lower()
        rest = m.group(2)
    else:
        parts = re.split(r"[\s\-_.]+", raw, maxsplit=1)
        cls = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

    if cls not in CLASSES:
        raise ValueError(
            f"session name must start with one of {CLASSES}, got '{raw.split()[0]}'"
        )

    # Normalise the descriptor: strip leading separators, collapse spaces.
    rest = re.sub(r"^[\s\-_.]+", "", rest)
    rest = re.sub(r"[\s\-_.]+", " ", rest).strip()

    # Build a filesystem-safe stem: lowercase, alnum + underscore only.
    stem = f"{cls} {rest}".strip().lower()
    stem = re.sub(r"\s+", "_", stem)
    stem = re.sub(r"[^a-z0-9_]", "", stem)
    if not stem:
        stem = cls
    return cls, stem


def ask_session_name():
    """Prompt until a valid 'class [descriptor]' name is entered."""
    print("Session name must start with a class: good / moderate / poor")
    print("Examples:  good 1   |   good 2   |   moderate 1   |   poor candle")
    while True:
        raw = input("Session name: ").strip()
        try:
            cls, stem = parse_session_name(raw)
            return cls, stem
        except ValueError as e:
            print(f"  {e}")


def looks_like_port(s):
    """Heuristic: does this string look like a serial port, not a session name?"""
    s = s.strip()
    return bool(re.match(r"^(COM\d+|/dev/(ttyUSB|ttyACM|cu\.)\S*|/dev/\S+)$", s, re.IGNORECASE))


def classify_args(args):
    """
    Auto-classify positional args as (port, session_name), in ANY order.

    Accepts either/both of:
        session_logger.py good1
        session_logger.py COM3 "good 1"
        session_logger.py "good 1" COM3
    Anything that looks like a COM port -> port; anything else -> session name.
    Extra tokens are joined into the session name (so `good 1` unquoted works).
    """
    port = None
    name_parts = []
    for a in args:
        if port is None and looks_like_port(a):
            port = a
        else:
            name_parts.append(a)
    name = " ".join(name_parts).strip() or None
    return port, name


def main():
    port_arg, name_arg = classify_args(sys.argv[1:])

    # 1. Session name
    if name_arg is not None:
        cls, stem = parse_session_name(name_arg)
    else:
        cls, stem = ask_session_name()

    # 2. Port
    port = port_arg or find_port() or input("Enter COM port (e.g. COM3): ").strip()

    # 3. Destination: data/raw/<class>/<stem>_<timestamp>.csv
    out_dir = os.path.join(OUT_DIR, cls)
    os.makedirs(out_dir, exist_ok=True)
    filename = os.path.join(out_dir, stem + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv")

    print(f"Class:   {cls}")
    print(f"Session: {stem}")
    print(f"Port:    {port} @ {BAUD}")
    print(f"Saving:  {os.path.relpath(filename, ROOT_DIR)}")
    print("(Ctrl+C to stop)\n")

    with serial.Serial(port, BAUD, timeout=1) as ser, open(filename, "w", newline="", encoding="utf-8") as f:
        time.sleep(2)  # let the board settle after opening the port
        writer = csv.writer(f)
        writer.writerow(EXPECTED_HEADER.split(","))
        f.flush()

        # Byte buffer: reassemble complete lines even if the OS delivers them
        # in fragments. Never drop a partial tail - keep it for the next read.
        buf = b""
        n_rows = 0

        # Power-loss safety: force the OS to physically write to disk
        # (fsync) at least this often, in case of a crash / USB drop.
        FS_FSYNC_INTERVAL_S = 30
        # Human heartbeat on the console every this often.
        HEARTBEAT_INTERVAL_S = 300  # 5 min

        start_time = time.time()
        last_fsync = time.time()
        last_heartbeat = time.time()

        def flush_and_fsync():
            """Flush Python buffers and fsync to disk. Never raises."""
            try:
                f.flush()
                os.fsync(f.fileno())
            except (OSError, ValueError):
                pass

        def heartbeat():
            """Print a periodic liveness + integrity line to the console."""
            elapsed = time.time() - start_time
            try:
                size = os.path.getsize(filename)
            except OSError:
                size = -1
            mins = elapsed / 60.0
            rate = (n_rows / mins) if mins > 0 else 0.0
            print(f"# [heartbeat] {n_rows} rows | {size} bytes | "
                  f"{mins:.1f} min | {rate:.1f} rows/min | last T={last_ts}")

        last_ts = "-"

        try:
            while True:
                try:
                    chunk = ser.read(ser.in_waiting or 1)
                except (serial.SerialException, OSError) as e:
                    print(f"\n[serial error] {e} - reconnecting in 3s...")
                    time.sleep(3)
                    try:
                        ser.close()
                    except Exception:
                        pass
                    ser = serial.Serial(port, BAUD, timeout=1)
                    time.sleep(2)
                    buf = b""  # discard partial line from the dead session
                    continue

                if not chunk:
                    continue

                buf += chunk
                *complete, buf = buf.split(b"\n")

                wrote_any = False
                for raw_line in complete:
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line or line.startswith("#"):
                        continue
                    if line == EXPECTED_HEADER:
                        continue

                    cols = line.split(",")
                    if len(cols) != EXPECTED_COLS:
                        # Show but don't save malformed rows.
                        print(f"[skip malformed {len(cols)}/{EXPECTED_COLS}] {line!r}")
                        continue

                    writer.writerow(cols)
                    n_rows += 1
                    wrote_any = True
                    last_ts = cols[0]
                    # Show the first few rows immediately so you can see it's
                    # alive, then stay quiet (heartbeat every 5 min thereafter).
                    if n_rows <= 3:
                        print(f"[{n_rows}] {line}")

                if wrote_any:
                    # flush() per batch; fsync throttled below.
                    f.flush()

                now = time.time()
                if now - last_fsync >= FS_FSYNC_INTERVAL_S:
                    last_fsync = now
                    flush_and_fsync()

                if now - last_heartbeat >= HEARTBEAT_INTERVAL_S:
                    last_heartbeat = now
                    flush_and_fsync()
                    heartbeat()

        except KeyboardInterrupt:
            flush_and_fsync()
            print(f"\nStopped. {n_rows} rows saved to {os.path.relpath(filename, ROOT_DIR)}")


if __name__ == "__main__":
    main()
