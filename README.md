# Air Quality Edge AI

An ESP32-C3-based environmental monitoring system that streams raw sensor data
and (eventually) runs an on-device ML classifier to detect air quality states:

| State    | Meaning                                   |
|----------|-------------------------------------------|
| `GOOD`     | Clean air (e.g. window open)              |
| `MODERATE` | Stale / indoor air (e.g. window closed)   |
| `POOR`     | Smoke / elevated pollutants (e.g. candle) |

## Hardware

| Component | Interface | ESP32-C3 pin | Notes                                   |
|-----------|-----------|--------------|-----------------------------------------|
| PMS5003   | UART      | RX `GPIO20`, TX `GPIO21` | 9600 baud, 32-byte frames |
| MQ-135    | Analog ADC| `GPIO0` (ADC1_CH0)       | Use a voltage divider (5V -> <=3.3V) |
| DHT22     | Digital   | `GPIO10`                 | Temp / humidity |
| Status LEDs | GPIO    | `GPIO4/5/6`              | GOOD / MODERATE / POOR (Phase 6) |

Board: **ESP32-C3-DevKitM-1** (RISC-V, native USB-CDC).

## Repository layout

```
firmware/            PlatformIO project (C++)
  include/config.h   Pins, sampling params, CSV schema
  src/main.cpp       Sampling loop + CSV serial output
  src/sensors.cpp    MQ-135 + DHT22 drivers
  src/pms5003.cpp    PMS5003 UART parser (non-blocking state machine)
  models/            Exported model headers (.gitkeep placeholder)

logger/              Host-side serial -> CSV recorder
  logger.py          Prompts for scene label, writes data/raw/<scene>/

data/
  raw/{good,moderate,poor}/   Recorded CSVs per scene (contents git-ignored)
  processed/                  Preprocessed feature windows (git-ignored)

ml/                  Training / preprocessing / export pipeline
  notebooks/         Exploration

docs/                Design notes
.github/workflows/   CI (placeholder)
```

## Data schema (16 raw columns)

```
timestamp_ms,
pm1_cf1,pm25_cf1,pm10_cf1,
pm1_atm,pm25_atm,pm10_atm,
n03,n05,n10,n25,n50,n100,
mq135_raw,temp_c,hum_pct
```

> **Note:** The PMS5003 used is a clone whose *mass* fields stay zero; the
> *particle count* fields (`n03`..`n100`) carry the real signal. All values are
> recorded raw - the ML stage decides which features to use. DHT read failures
> are written as `-999.0`.

## Quick start

### Firmware

```powershell
# Build & flash (PlatformIO)
cd firmware
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run -t upload
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" device monitor
```

### Data logging

```powershell
pip install pyserial
python logger/logger.py
# Choose scene: good | moderate | poor
# Records until Ctrl+C into data/raw/<scene>/<timestamp>.csv
```

## Roadmap

- [x] Sensor bring-up (MQ-135, DHT22, PMS5003) & 16-column raw CSV stream
- [x] Multi-hour logger with per-scene folder labelling
- [ ] Record GOOD / MODERATE / POOR datasets
- [ ] Preprocessing + feature engineering (`ml/`)
- [ ] Train 3-class classifier
- [ ] Export model to ESP32 (TFLite / C array) and drive status LEDs

## License

See [LICENSE](LICENSE).