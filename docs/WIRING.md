# Air Quality Monitor — Wiring Guide

Board: **ESP32-C3 DevKitM-1** (3.3 V logic; 5 V on the VIN/5V pin when USB-powered)

> **Safety first**
> - ESP32-C3 GPIO pins are **3.3 V only**. Never feed 5 V into a GPIO.
> - MQ-135 runs on **5 V** and its analog output can exceed 3.3 V -> a **voltage
>   divider is mandatory** before GPIO0.
> - OLED and DHT22 are **3.3 V** devices.

## Pin map (matches `firmware/include/config.h`)

| Signal | ESP32-C3 pin | Sensor |
|--------|--------------|--------|
| DHT22 data | **GPIO10** | DHT22 data |
| MQ-135 analog (after divider) | **GPIO0** (ADC1_CH0) | MQ-135 AO |
| PMS5003 RX (ESP receives) | **GPIO20** | PMS5003 TX |
| PMS5003 TX (ESP sends, optional) | **GPIO21** | PMS5003 RX |
| OLED SDA | **GPIO8** | SSD1306 SDA |
| OLED SCL | **GPIO9** | SSD1306 SCL |
| LED GOOD | GPIO4 | (Phase 6) |
| LED MODERATE | GPIO5 | (Phase 6) |
| LED POOR | GPIO6 | (Phase 6) |

## Resistors you need

| Purpose | Value | Notes |
|---------|-------|-------|
| **MQ-135 voltage divider** | **R1 = 10 kOhm, R2 = 10 kOhm** | Divides AO by 2 -> 5 V becomes 2.5 V max. Safe for the 3.3 V ADC. |
| **DHT22 pull-up** on data line | **10 kOhm** (4.7k-10k OK) | Between data (GPIO10) and 3.3 V. Improves reliability. |
| **OLED I2C pull-ups** | Usually **built in** | Add 4.7 kOhm SDA/SCL->3V3 only if I2C errors / no device found. |
| **LED current-limit** | **220 Ohm** per LED | One per LED (GPIOx -> 220 -> LED anode -> GND). Phase 6 only. |

**Buy list:** 2x 10k (divider) + 1x 10k (DHT pull-up) + 3x 220 (LEDs) + optional 2x 4.7k (I2C).

---

## 1. DHT22 (temp + humidity) — START HERE, verify first

```
   DHT22                ESP32-C3
  +------+
  | VCC  |-------- 3V3  (3.3 V)
  | DATA |-------- GPIO10
  |      |            |
  |      |          [10k]   <- pull-up between DATA and 3V3
  | NC   |   (not connected)
  | GND  |-------- GND
  +------+
```
- Some DHT22 modules already have an onboard pull-up — adding external 10k in
  parallel never hurts.
- Keep the DATA wire short.

---

## 2. MQ-135 (air quality, analog) — needs voltage divider

MQ-135 module VCC = **5 V**. Analog output (AO) at full scale ~5 V -> must be
halved before GPIO0.

```
  MQ-135                divider                 ESP32-C3
  +------+
  | VCC  |---------------------------- 5V   (VIN / 5V pin from USB)
  | GND  |---------------------------- GND
  | AO   |----+------ R1 (10k) ---------+---- GPIO0 (ADC1_CH0)
  +------+    |                          |
              |                       R2 (10k)
              |                          |
             (AO)                       GND
```
- **AO -> R1(10k) -> node -> R2(10k) -> GND**, tap the **node** (between R1 and
  R2) to **GPIO0**.
- At AO = 5 V, node ~ **2.5 V** -> safe.
- MQ-135 needs **~24-48 h burn-in** and a few minutes warm-up.

---

## 3. PMS5003 (particulate matter, UART)

PMS5003 uses **5 V** power and **3.3 V logic** on its UART lines (safe for ESP).

```
  PMS5003            ESP32-C3
  +---------+
  | VCC     |------ 5V
  | GND     |------ GND
  | TX      |------ GPIO20 (ESP RX)
  | RX      |------ GPIO21 (ESP TX)   [optional]
  | SET/RST |--- 3V3 or leave
  +---------+
```
- **PMS TX -> GPIO20** is the essential one (ESP receives).
- **PMS RX <- GPIO21** optional (sleep/set commands).
- PMS5003 runs at **9600 baud**; needs a solid 5 V (inrush current).
- PMS TX is **3.3 V logic** — directly safe, do **not** add a divider.

---

## 4. OLED SSD1306 (I2C) — 3.3 V ONLY

```
  OLED SSD1306        ESP32-C3
  +-------+           (4-pin: GND VCC SCL SDA)
  | GND   |------ GND
  | VCC   |------ 3V3   (3.3 V)
  | SCL   |------ GPIO9
  | SDA   |------ GPIO8
  +-------+
```
- Internal pull-ups usually on module. If `I2C: no devices found`, add
  **4.7k SDA->3V3 and SCL->3V3**.

---

## 5. Status LEDs (Phase 6 — optional for now)

```
  GPIOx ----[220]----|>|---- GND      (x = 4, 5, 6)
                     LED
```
- One **220 Ohm** per LED, anode toward the GPIO.

---

## Power summary

| Device | Supply |
|--------|--------|
| ESP32-C3 | USB (5 V); board makes 3.3 V |
| MQ-135 | 5 V (VIN) |
| PMS5003 | 5 V (VIN) |
| OLED | 3.3 V |
| DHT22 | 3.3 V |

- **Common ground** for everything.

---

## Bring-up order & verification

Wire and test **one block at a time**:

1. **DHT22 first**
   - Wire: VCC->3V3, DATA->GPIO10 + 10k pull-up, GND->GND.
   - Flash the **dev firmware** (`main.cpp`).
   - Serial log `temp_c,hum_pct` fills in (e.g. `...,23.00,57.20`).
     **No `-999.0`** = DHT working. OLED shows `Temp:.. Hum:..`.
2. **OLED** — confirm `# I2C device found at 0x3C` and `# OLED init OK`.
3. **MQ-135** — after divider, `mq135_raw` shows a plausible steady value
   (~300-400 clean air). Burn-in 24-48 h.
4. **PMS5003** — `n03..n100` non-zero; `frames_ok` increasing, `bad=0`.
