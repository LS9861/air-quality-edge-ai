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
        return "MODERATE";
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

    // ---- BLUE area (y >= 16): air quality status (double height) ----
    oled.setTextSize(2);
    oled.setCursor(0, 16);
    oled.print("AQ:");
    oled.print(display_status_text(status));

    // Line 3: PM values
    oled.setTextSize(1);
    oled.setCursor(0, 36);
    oled.print("PM2.5:");
    oled.print(pm25_atm);
    oled.print(" PM10:");
    oled.print(pm10_atm);

    // Line 4: particle count + MQ raw
    oled.setCursor(0, 48);
    oled.print("n0.3:");
    oled.print(n03);
    oled.print(" MQ:");
    oled.print(mq135_raw);

    oled.display();
}

