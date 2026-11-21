#include "config.h"
#include <Arduino.h>

// Internal state machine
static uint8_t frame[32];
static uint8_t idx = 0;

// Outputs (valid only when return value is true)
uint16_t pms_pm25 = 0;
uint16_t pms_pm10 = 0;

// ---- Full data fields (for diagnostics) ----
uint16_t pms_pm1_cf1 = 0, pms_pm25_cf1 = 0, pms_pm10_cf1 = 0;   // bytes 4-9
uint16_t pms_pm1_atm = 0, pms_pm25_atm = 0, pms_pm10_atm = 0;   // bytes 10-15
uint16_t pms_n03 = 0, pms_n05 = 0, pms_n10 = 0, pms_n25 = 0, pms_n50 = 0, pms_n100 = 0; // bytes 16-27

// ---- Diagnostics (readable from main.cpp) ----
// Number of raw bytes ever received on Serial1 (GPIO20).
uint32_t pms_bytes_rx = 0;
// Number of frames that passed header sync + checksum.
uint32_t pms_frames_ok = 0;
// Number of frames that had a bad checksum.
uint32_t pms_frames_bad = 0;

// Call this frequently in loop(); non-blocking
bool pms5003_poll()
{
    while (Serial1.available())
    {
        uint8_t b = Serial1.read();
        pms_bytes_rx++;

        // Synchronize: wait for 0x42 0x4D header
        if (idx == 0 && b != 0x42)
            continue;
        if (idx == 1 && b != 0x4D)
        {
            idx = 0;
            continue;
        }

        frame[idx++] = b;

        if (idx == 32)
        {
            idx = 0;

            // Verify checksum: sum of first 30 bytes == last 2 bytes (big-endian)
            uint16_t sum = 0;
            for (int i = 0; i < 30; i++)
                sum += frame[i];
                        uint16_t checksum = (frame[30] << 8) | frame[31];

                        if (sum != checksum)
                        {
                            pms_frames_bad++;
                            return false; // Corrupted frame, discard
                        }

                        // Parse every measurement field (big-endian pairs).
                        pms_pm1_cf1  = (frame[4]  << 8) | frame[5];   // PM1.0 CF=1
                        pms_pm25_cf1 = (frame[6]  << 8) | frame[7];   // PM2.5 CF=1
                        pms_pm10_cf1 = (frame[8]  << 8) | frame[9];   // PM10  CF=1
                        pms_pm1_atm  = (frame[10] << 8) | frame[11];  // PM1.0 atmos
                        pms_pm25_atm = (frame[12] << 8) | frame[13];  // PM2.5 atmos
                        pms_pm10_atm = (frame[14] << 8) | frame[15];  // PM10  atmos
                        pms_n03  = (frame[16] << 8) | frame[17];      // >0.3um
                        pms_n05  = (frame[18] << 8) | frame[19];      // >0.5um
                        pms_n10  = (frame[20] << 8) | frame[21];      // >1.0um
                        pms_n25  = (frame[22] << 8) | frame[23];      // >2.5um
                        pms_n50  = (frame[24] << 8) | frame[25];      // >5.0um
                        pms_n100 = (frame[26] << 8) | frame[27];      // >10um

                        // Main outputs use atmospheric values (per datasheet "environment" mode)
                        pms_pm25 = pms_pm25_atm;
                        pms_pm10 = pms_pm10_atm;
                        pms_frames_ok++;

            // Dump the first valid frame in hex so we can inspect all fields.
            static bool dumped = false;
            if (!dumped)
            {
                dumped = true;
                Serial.print("# PMS frame hex:");
                for (int i = 0; i < 32; i++)
                {
                    Serial.print(' ');
                    if (frame[i] < 0x10) Serial.print('0');
                    Serial.print(frame[i], HEX);
                }
                Serial.println();
            }

            return true;
        }
    }
    return false;
}