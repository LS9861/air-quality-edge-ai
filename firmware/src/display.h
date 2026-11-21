#pragma once

#include <Arduino.h>

// Air quality status used by display / LEDs (interim heuristic until ML).
enum AirStatus
{
    AIR_GOOD = 0,
    AIR_MODERATE = 1,
    AIR_POOR = 2
};

// Connection snapshot passed to the display (dev firmware only).
// Valid=false fields render as "--" so the layout still works offline.
struct DisplayEnv
{
    bool time_valid = false;
    const char *weekday = "--";  // "Mon"
    int day = 0;
    int month = 0;               // 0 = Jan .. 11 = Dec
    int hour = 0;
    int minute = 0;
    bool weather_valid = false;
    float weather_temp = 0.0f;
    const char *condition = "--";
    const char *city = "Stuttgart";
};

// Initialize I2C + SSD1306. Safe to call even if no display is attached
// (the library reports false; we just log it).
bool display_init();

// Refresh the screen with the latest readings (sensor-only layout).
void display_update(float temp_c, float hum_pct, int mq135_raw,
                    uint16_t pm25_atm, uint16_t pm10_atm, uint16_t n03,
                    AirStatus status);

// Refresh the screen with the connected-weather-station layout (dev firmware):
//   yellow: 23.3C 58%
//   blue:   AIR: GOOD
//           Mon 14 Apr 10:42
//           18C Cloudy
void display_update_env(float temp_c, float hum_pct, AirStatus status,
                        const DisplayEnv &env);

// Compute an interim air-quality status from raw signals.
// Thresholds are placeholders, to be tuned after real data collection.
AirStatus display_compute_status(int mq135_raw, uint16_t pm25_atm, uint16_t n03);

const char *display_status_text(AirStatus status);
