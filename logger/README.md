# Logger (data collection)

Records the ESP32's 16-column CSV stream into `data/raw/<scene>/`.

## Before you record (checklist)

1. **Collect firmware active** — in `firmware/src/`:
   - `main.cpp` renamed to `main.cpp.disabled`
   - `raw_data_collection.cpp.disabled` renamed to `raw_data_collection.cpp`
   - Flash it. Boot log must show **no** `# NET:` / `# OLED` lines (lean build).
2. **PC won't sleep** (multi-hour runs):
   ```powershell
   powercfg /change standby-timeout-ac 0
   powercfg /change monitor-timeout-ac 15
   ```
   Also disable "USB selective suspend" for the COM port in Device Manager.
3. **Sensor burned in** — MQ-135 needs ~24–48 h before readings are stable.
4. **Know your COM port** (e.g. `COM6`).
5. **Read the scene protocol** in `../data/raw/RECORDING_LOG.md` and keep that
   log updated per session.

## Run

```powershell
pip install pyserial
python logger/logger.py
# Choose label: good | moderate | poor
# Runs until Ctrl+C; writes data/raw/<scene>/air_quality_<scene>_<ts>.csv
```

## How it reads the port

Complete lines are reassembled from a raw byte buffer (not `readline()`), so a
row split across serial reads is **not** dropped. `#` diagnostic lines and the
CSV header are skipped; any malformed complete line is printed as
`[skip malformed] ...` so problems are visible. On a serial error it
reconnects and discards the partial line.

## After recording

- Update `data/raw/RECORDING_LOG.md` (conditions, duration, weather, notes).
- Train: `python ml/run_pipeline.py --data-root data/raw`
