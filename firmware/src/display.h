#pragma once

#include <Arduino.h>

// Air quality status used by display / LEDs (interim heuristic until ML).
enum AirStatus
{
    AIR_GOOD = 0,
    AIR_MODERATE = 1,
    AIR_POOR = 2
};

// Initialize I2C + SSD1306. Safe to call even if no display is attached
// (the library reports false; we just log it).
bool display_init();

// Refresh the screen with the latest readings.
// status: heuristic status computed by caller (or display_compute_status()).
void display_update(float temp_c, float hum_pct, int mq135_raw,
                    uint16_t pm25_atm, uint16_t pm10_atm, uint16_t n03,
                    AirStatus status);

// Compute an interim air-quality status from raw signals.
// Thresholds are placeholders, to be tuned after real data collection.
AirStatus display_compute_status(int mq135_raw, uint16_t pm25_atm, uint16_t n03);

const char *display_status_text(AirStatus status);
