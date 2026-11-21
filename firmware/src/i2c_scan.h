#pragma once

// Scans the I2C bus (SDA/SCL from config.h). Prints results to Serial.
// Returns number of devices found.
int i2c_scan();
