#include "config.h"
#include "display.h"
#include "i2c_scan.h"
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

static Adafruit_SSD1306 oled(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
static bool oled_ok = false;

bool display_init()
{
    Wire.begin(PIN_OLED_SDA, PIN_OLED_SCL);

    // Diagnostic: report what's actually on the I2C bus before init.
    i2c_scan();

    // SSD1306_SWITCHCAPVCC: generate 3.3V internally from 3V3 supply.
    if (!oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR))
    {
        oled_ok = false;
        Serial.println("# OLED init failed (check wiring / address 0x3C vs 0x3D)");
        return false;
    }

    oled_ok = true;
    oled.clearDisplay();
    oled.setTextColor(SSD1306_WHITE);
    oled.setTextSize(1);
    // Yellow band: title
    oled.setCursor(0, 0);
    oled.println("Air Quality Edge AI");
    // Blue area: status
    oled.setCursor(0, 20);
    oled.println("Booting...");
    oled.display();
    Serial.println("# OLED init OK");
    return true;
}

const char *display_status_text(AirStatus status)
{
    switch (status)
    {
    case AIR_GOOD:
        return "GOOD";
    case AIR_MODERATE:
        return "MOD";
    case AIR_POOR:
        return "POOR";
    default:
        return "???";
    }
}

// Interim heuristic: adjust thresholds after collecting GOOD/MODERATE/POOR data.
AirStatus display_compute_status(int mq135_raw, uint16_t pm25_atm, uint16_t n03)
{
    // POOR: strong signal on any channel
    if (mq135_raw > 450 || pm25_atm > 35 || n03 > 300)
        return AIR_POOR;
    // MODERATE: elevated
    if (mq135_raw > 380 || pm25_atm > 15 || n03 > 150)
        return AIR_MODERATE;
    return AIR_GOOD;
}

void display_update(float temp_c, float hum_pct, int mq135_raw,
                    uint16_t pm25_atm, uint16_t pm10_atm, uint16_t n03,
                    AirStatus status)
{
    if (!oled_ok)
        return;

    oled.clearDisplay();
    oled.setTextSize(1);
    oled.setTextColor(SSD1306_WHITE);

    // ---- YELLOW band (top 16 px, page 0): temperature + humidity ----
    oled.setCursor(0, 0);
    if (temp_c <= DHT_ERROR_VALUE / 2)
    {
        oled.print("Temp: --.-C  Hum: --%");
    }
    else
    {
        oled.print("Temp:");
        oled.print(temp_c, 1);
        oled.print("C Hum:");
        oled.print(hum_pct, 0);
        oled.print("%");
    }

    // ---- BLUE area (y >= 16): uniform size-1 lines, fixed spacing ----
    // Uniform size 1 guarantees no overlap regardless of status word length.
    oled.setCursor(0, 18);
    oled.print("AQ: ");
    oled.print(display_status_text(status));

    oled.setCursor(0, 30);
    oled.print("PM2.5:");
    oled.print(pm25_atm);
    oled.print(" PM10:");
    oled.print(pm10_atm);

    oled.setCursor(0, 42);
    oled.print("n0.3:");
    oled.print(n03);
    oled.print(" MQ:");
    oled.print(mq135_raw);

    // 4th line: uptime (s) as a liveness indicator.
    oled.setCursor(0, 54);
    oled.print("Up:");
    oled.print(millis() / 1000);
    oled.print("s");

    oled.display();
}

// Connected weather-station layout for the dev firmware.
// Yellow band (pages 0-1): big temp + humidity.
// Blue area: air status, local date/time, outdoor weather.
void display_update_env(float temp_c, float hum_pct, AirStatus status,
                        const DisplayEnv &env)
{
    if (!oled_ok)
        return;

    oled.clearDisplay();
    oled.setTextColor(SSD1306_WHITE);

    // ---- YELLOW band (top 16 px): one size-1 line, Temp + Hum together ----
    // Keep <= 21 chars (6px each) so it fits 128px. Compact spacing.
    oled.setTextSize(1);
    oled.setCursor(0, 0);
    if (temp_c <= DHT_ERROR_VALUE / 2)
    {
        oled.print("Temp:--.-C Hum:--%");
    }
    else
    {
        oled.print("Temp:");
        oled.print(temp_c, 1);
        oled.print("C Hum:");
        oled.print(hum_pct, 0);
        oled.print("%");
    }

    // ---- BLUE area (y >= 16): 4 lines at 12-px pitch (y=18,30,42,54) ----

    oled.setCursor(0, 18);
    oled.print("Room Air: ");
    oled.print(display_status_text(status));

    oled.setCursor(0, 30);
    if (env.time_valid)
    {
        static const char *MONTHS[] = {"Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};
        int m = (env.month >= 0 && env.month <= 11) ? env.month : 0;
        oled.print(env.weekday);
        oled.print(' ');
        oled.print(env.day);
        oled.print(' ');
        oled.print(MONTHS[m]);
        oled.print(' ');
        if (env.hour < 10) oled.print('0');
        oled.print(env.hour);
        oled.print(':');
        if (env.minute < 10) oled.print('0');
        oled.print(env.minute);
    }
    else
    {
        oled.print("-- -- --- --:--");
    }

    oled.setCursor(0, 42);
    oled.print("City: ");
    oled.print(env.city);

    oled.setCursor(0, 54);
    if (env.weather_valid)
    {
        oled.print("Out: ");
        oled.print(env.weather_temp, 0);
        oled.print("C, ");
        oled.print(env.condition);
    }
    else
    {
        oled.print("Out: --C, --");
    }

    oled.display();
}

