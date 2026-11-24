# Project Checklist — Air Quality Edge AI

Single source of truth for progress and phase discipline.
**Rule: do not mix phases.** Finish data collection before touching
test / train / LED / display. Keep the board undisturbed during recordings.

Legend: `[ ]` todo · `[~]` in progress · `[x]` done

---

## Phase 0 — Hardware & firmware bring-up  ✅

- [x] MQ-135 (analog, voltage divider) — reading stable, responds to breath
- [x] DHT22 — temp/humidity, all reads OK
- [x] PMS5003 — frames parse (`frames_ok` climbing, `bad=0`); counts n03..n100 valid
      (mass fields are 0 on this clone — expected; use counts)
- [x] OLED SSD1306 @ 0x3C — init OK, live display
- [x] All-sensor combined `sensor_test` — all four work together
- [x] 16-column raw CSV schema validated end-to-end

## Phase 1 — Logger tooling  ✅

- [x] `logger/session_logger.py` — named sessions (`good1` -> `data/raw/good/good_1_<ts>.csv`)
- [x] Auto-detect COM port + session name, any order
- [x] Flexible names: `good1` / `good 1` / `moderate-2` / `Good1`
- [x] Robust line reassembly (no dropped rows on fragmentation)
- [x] **Per-batch flush + fsync every 30 s** (power-loss safe)
- [x] **Heartbeat every 5 min** (rows / bytes / rate / last T) + first 3 rows shown
- [x] Auto-reconnect on serial drop

## Phase 2 — DATA COLLECTION  ⏳ (current phase)

> Board runs `raw_data_collection.cpp` (16-col). Do NOT flash anything else.
> One clean scene per run; keep conditions constant for the whole run.

**Target:** ~4–6 h per class, across different times of day.

- [~] `moderate` — recording `moderate_1` (door closed) — in progress
- [ ] `moderate` — more sessions (`moderate_2`, ... at other times)
- [ ] `good` — e.g. `good_1` (window open / fresh air)
- [ ] `poor` — e.g. `poor_1` (candle / elevated pollutants)
- [ ] Roughly balanced total time per class

**Per-session procedure**
1. Warm up 15–30 min if the board was off (MQ-135 baseline).
2. Set the scene; keep it constant for the whole run.
3. `cd logger` then `python session_logger.py moderate1` (or `good1`, `poor1`).
4. Watch the first rows + heartbeats confirm it's alive.
5. Ctrl+C to stop; note it in `data/raw/RECORDING_LOG.md`.

**Do NOT during collection**
- ❌ Flash / upload / `pio run -t upload`
- ❌ Open/replug the USB (drops the serial session)
- ❌ Change firmware mode (file renames) — keep `raw_data_collection.cpp` active

---

## Phase 3 — Data review & ML (after ALL collection is done)

- [ ] Quick data sanity: sample counts per class, no big gaps, values in range
- [ ] `ml/run_pipeline.py --data-root data/raw` (discover -> preprocess -> train -> eval)
- [ ] Address window-leakage (`--split-by-file`) before trusting accuracy
- [ ] `class_weight='balanced'` + macro-F1 for class imbalance
- [ ] Tune / replace interim AQ thresholds using real data
- [ ] Pick final model; record accuracy / confusion matrix

## Phase 4 — Deploy / on-device test (after training)

- [ ] Export model to C array / header (`firmware/models/`)
- [ ] On-device inference replaces the rule-based heuristic
- [ ] Verify predictions on-device match host

## Phase 5 — Status LED indicator (built, not yet flashed)

- [x] `status_led.cpp/.h` — non-blocking `millis()` blinker, single pin GPIO4
      - GOOD = steady ON · MODERATE = ~1 s blink · POOR = fast ~200 ms blink
- [x] Wired into dev `main.cpp` (not into collect firmware)
- [ ] Compile-check (build only, no upload)
- [ ] Flash + visual test — **only in Phase 5, after data collection**
- [ ] Confirm blink rates for each status on real hardware

## Phase 6 — Dev firmware / display polish (optional, after data)

- [ ] Optional: AQ line one size larger on OLED (`GOOD`/`MOD`/`POOR` at size 2)
- [ ] Verify weather-station layout with WiFi/NTP/OWM
- [ ] Final end-to-end demo

---

## Firmware mode — keep in sync!

The board runs ONE main at a time. Before any upload, check which is `.cpp`:

| Mode | Active file | Use for |
|------|-------------|---------|
| **Collect** (board runs this now) | `raw_data_collection.cpp` | data collection |
| Dev | `main.cpp` (others `.disabled`) | OLED + WiFi + LEDs + status LED |
| Bring-up | `sensor_test.cpp` (others `.disabled`) | per-sensor checks |

**Invariant during collection:** `raw_data_collection.cpp` is the active `.cpp`,
`main.cpp` and `sensor_test.cpp` are `.disabled`.

Quick check:
```powershell
Get-ChildItem firmware\src -Name | Where-Object { $_ -match '\.(cpp|disabled)$' }
```

---

## Current state (update as you go)

- **Board firmware:** `raw_data_collection` (16-col) — collecting
- **Recording:** `moderate_1` in progress (`data/raw/moderate/moderate_1_*.csv`)
- **Nothing flashed or uploaded during this session's collection.**
