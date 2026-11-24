#pragma once

// ============================================================
// Air Quality Edge AI - Global Configuration
// Modify this file when changing wiring or sampling behavior
// ============================================================

// ---------- Pin Definitions (ESP32-C3) ----------
// PMS5003 (UART)
#define PIN_PMS_RX 20 // ESP32 RX <- PMS TX
#define PIN_PMS_TX 21 // ESP32 TX -> PMS RX (optional, for sleep commands)

// MQ-135 (Analog) — MUST use voltage divider (5V -> ~3.3V max)
#define PIN_MQ135_ADC 0 // ADC1_CH0 (GPIO0)

// DHT22 (Digital)
#define PIN_DHT 10
#define DHT_TYPE DHT22

// ---------- Status LED (single pin, blink-rate encodes air quality) ----------
// One LED toggles at a rate that reflects the air-quality state, so the
// status is readable at a glance even when the OLED is out of view.
//   GOOD      : steady ON (no blink)        -> calm
//   MODERATE  : ~1 s period blink           -> attention
//   POOR      : fast ~200 ms blink          -> urgent
#define PIN_STATUS_LED 4

// (Legacy) three-LED scheme pins - kept for reference; unused by the
// single-pin blink indicator above.
#define PIN_LED_GOOD 4
#define PIN_LED_MODERATE 5
#define PIN_LED_POOR 6

// ---------- OLED Display (SSD1306, I2C) ----------
// 0.96" module is typically 128x64. Change OLED_HEIGHT to 32 for 128x32 boards.
#define PIN_OLED_SDA 8
#define PIN_OLED_SCL 9
#define OLED_WIDTH 128
#define OLED_HEIGHT 64
#define OLED_ADDR 0x3C // try 0x3D if the screen stays blank

// ---------- Network / Weather (dev firmware only) ----------
// Credentials live in include/secrets.h (git-ignored; copy secrets.example.h).
// This firmware is WiFi-only via net.h/net.cpp, used exclusively by main.cpp.
#define NTP_SERVER_1 "pool.ntp.org"
#define NTP_SERVER_2 "time.nist.gov"
#define TZ_INFO "CET-1CEST,M3.5.0,M10.5.0/3" // Europe/Berlin (Stuttgart), auto DST
#define OWM_CITY "Stuttgart,DE"
#define OWM_UNITS "metric"            // metric => Celsius
#define OWM_FETCH_INTERVAL_MS 900000UL // 15 min
#define NET_UPDATE_INTERVAL_MS 1000UL  // display clock refresh (~1 s)

// OWM transport: 1 = HTTP (plain), 0 = HTTPS (TLS, default).
// NOTE: on this Arduino-ESP32 core, HTTPClient links WiFiClientSecure either
// way, so switching to HTTP does NOT reduce flash (~957 KB either way).
// Keep HTTPS (0) for an encrypted API key; use HTTP (1) only to avoid
// cert setup on very old setups. Flash headroom is handled by the partition
// table instead (see partitions.csv).
#define OWM_USE_HTTP 0

// ---------- Sampling Parameters ----------
#define SERIAL_BAUD 115200
#define PMS_BAUD 9600
#define READ_INTERVAL_MS 2000    // DHT22 minimum 2s between reads
#define MQ135_SAMPLES 10         // Average N ADC samples
#define MQ135_SAMPLE_DELAY_MS 10 // Delay between ADC samples

// ---------- Data Collection ----------
#define WINDOW_SIZE 50 // Samples per inference window (Phase 6)
#define NUM_CHANNELS 4 // PM2.5, PM10, MQ135, Temp (humidity as 5th later)
#define NUM_CLASSES 3  // GOOD / MODERATE / POOR

// ---------- CSV Output ----------
// Full RAW schema for ML. Mass fields may be 0 on PMS clones; the particle
// counts (n03..n100) carry the real signal. Keep everything raw so the ML
// stage decides what to use.
// Columns:
//   timestamp_ms,
//   pm1_cf1,pm25_cf1,pm10_cf1,       (PMS standard particle, CF=1)
//   pm1_atm,pm25_atm,pm10_atm,       (PMS atmospheric)
//   n03,n05,n10,n25,n50,n100,        (particle counts >0.3/0.5/1/2.5/5/10 um)
//   mq135_raw,temp_c,hum_pct
#define CSV_HEADER "timestamp_ms,pm1_cf1,pm25_cf1,pm10_cf1,pm1_atm,pm25_atm,pm10_atm,n03,n05,n10,n25,n50,n100,mq135_raw,temp_c,hum_pct"
#define CSV_COLUMNS 16
#define INVALID_SENTINEL -1    // Used when sensor read fails
#define DHT_ERROR_VALUE -999.0 // Used when DHT read fails