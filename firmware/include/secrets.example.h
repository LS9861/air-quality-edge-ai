#pragma once

// ============================================================
// Copy this file to "secrets.h" and fill in your values.
// secrets.h is git-ignored and must NOT be committed.
//   Windows:  copy firmware\include\secrets.example.h firmware\include\secrets.h
// ============================================================

// 2.4 GHz WiFi only (ESP32-C3 has no 5 GHz radio).
#define WIFI_SSID "your-network-name"
#define WIFI_PASSWORD "your-network-password"

// OpenWeatherMap API key (https://openweathermap.org/api).
// The free "Current Weather" endpoint is sufficient.
#define OWM_API_KEY "your-openweathermap-api-key"
