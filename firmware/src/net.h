#pragma once

#include <Arduino.h>

// ============================================================
// Network layer for the DEV firmware only.
//   - Non-blocking WiFi connection
//   - SNTP time sync (local time for Stuttgart, auto DST)
//   - Periodic OpenWeatherMap current-weather fetch
// Everything is fail-safe: if WiFi/API fails, display_* shows "--"
// and CSV logging is completely unaffected.
// ============================================================

struct NetTime
{
    bool valid = false;  // SNTP synced
    int day = 0;         // day of month
    int month = 0;       // 0 = Jan .. 11 = Dec (tm_mon)
    int weekday = 0;     // 0 = Sunday .. 6 = Saturday (tm_wday)
    int hour = 0;
    int minute = 0;
};

struct NetWeather
{
    bool valid = false;   // last fetch succeeded
    float temp_c = 0.0f;
    String condition;     // short text, e.g. "Cloudy", "Clear"
};

// Start WiFi (non-blocking) + SNTP config. Call once from setup().
void net_init();

// Drive the state machine. Call every loop(). Never blocks long.
void net_update();

// Latest time / weather snapshot (read-only).
NetTime net_get_time();
NetWeather net_get_weather();

// Short weekday string ("Mon") and condition, ready for the display.
const char *net_weekday_short(int weekday);
