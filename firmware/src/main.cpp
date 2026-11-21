#include <Arduino.h>
#include "config.h"

// Declarations from other .cpp files
bool pms5003_poll();
void sensors_init();
int sensors_read_mq135();
bool sensors_read_dht(float &temp_c, float &humidity_pct);

extern uint32_t pms_bytes_rx;
extern uint32_t pms_frames_ok;
extern uint32_t pms_frames_bad;

extern uint16_t pms_pm1_cf1, pms_pm25_cf1, pms_pm10_cf1;
extern uint16_t pms_pm1_atm, pms_pm25_atm, pms_pm10_atm;
extern uint16_t pms_n03, pms_n05, pms_n10, pms_n25, pms_n50, pms_n100;

unsigned long lastRead = 0;
unsigned long lastDiag = 0;

void setup()
{
    Serial.begin(SERIAL_BAUD);
    // Do NOT block on !Serial: on ESP32-C3 native USB this makes output
    // timing erratic (device waits for a host that resets it on connect).
    delay(1500);

    // PMS5003 UART
    Serial1.begin(PMS_BAUD, SERIAL_8N1, PIN_PMS_RX, PIN_PMS_TX);

    // MQ-135 + DHT22
    sensors_init();

        // CSV header
    Serial.println(CSV_HEADER);
}

void loop()
{
        // 1. Poll PMS5003 continuously (non-blocking)
    pms5003_poll();

    // 2. Read MQ-135 and DHT22 at fixed interval
    if (millis() - lastRead >= READ_INTERVAL_MS)
    {
                lastRead = millis();

        int mq135 = sensors_read_mq135();

        float temp, hum;
        sensors_read_dht(temp, hum);

        // 3. Print full raw CSV line (must match CSV_HEADER order)
        Serial.print(millis());          // timestamp_ms
        Serial.print(','); Serial.print(pms_pm1_cf1);
        Serial.print(','); Serial.print(pms_pm25_cf1);
        Serial.print(','); Serial.print(pms_pm10_cf1);
        Serial.print(','); Serial.print(pms_pm1_atm);
        Serial.print(','); Serial.print(pms_pm25_atm);
        Serial.print(','); Serial.print(pms_pm10_atm);
        Serial.print(','); Serial.print(pms_n03);
        Serial.print(','); Serial.print(pms_n05);
        Serial.print(','); Serial.print(pms_n10);
        Serial.print(','); Serial.print(pms_n25);
        Serial.print(','); Serial.print(pms_n50);
        Serial.print(','); Serial.print(pms_n100);
        Serial.print(','); Serial.print(mq135);
        Serial.print(','); Serial.print(temp, 2);
        Serial.print(','); Serial.println(hum, 2);
    }
        // 4. Periodic PMS5003 diagnostic (every 10 s).
    // Prefixed with '#' so the logger ignores these lines.
    if (millis() - lastDiag >= 10000UL)
    {
        lastDiag = millis();
        Serial.print("# PMS diag frames_ok=");
        Serial.print(pms_frames_ok);
        Serial.print(" bad=");
        Serial.print(pms_frames_bad);
        Serial.print(" | CNT[0.3/0.5/1/2.5/5/10]=");
        Serial.print(pms_n03);  Serial.print('/');
        Serial.print(pms_n05);  Serial.print('/');
        Serial.print(pms_n10);  Serial.print('/');
        Serial.print(pms_n25);  Serial.print('/');
        Serial.print(pms_n50);  Serial.print('/');
        Serial.print(pms_n100);
        Serial.println();
}
}

