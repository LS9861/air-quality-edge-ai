#include "i2c_scan.h"
#include "config.h"
#include <Arduino.h>
#include <Wire.h>

// Scans the I2C bus and prints every responding address.
// Returns the number of devices found.
int i2c_scan()
{
    Serial.print("# I2C scan on SDA=");
    Serial.print(PIN_OLED_SDA);
    Serial.print(" SCL=");
    Serial.println(PIN_OLED_SCL);

    int found = 0;
    for (uint8_t addr = 0x01; addr < 0x7F; addr++)
    {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0)
        {
            Serial.print("# I2C device found at 0x");
            if (addr < 0x10)
                Serial.print('0');
            Serial.print(addr, HEX);
            if (addr == 0x3C || addr == 0x3D)
                Serial.print("  (SSD1306 OLED)");
            Serial.println();
            found++;
        }
    }

    if (found == 0)
        Serial.println("# I2C: no devices found (OLED not wired yet?)");
    else
    {
        Serial.print("# I2C: ");
        Serial.print(found);
        Serial.println(" device(s) found");
    }
    return found;
}
