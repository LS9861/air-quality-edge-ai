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

// Status LEDs (optional, for Phase 6)
#define PIN_LED_GOOD 4
#define PIN_LED_MODERATE 5
#define PIN_LED_POOR 6

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