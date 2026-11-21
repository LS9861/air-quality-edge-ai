#include <Arduino.h>
#include "config.h"
#include "display.h"
#include "net.h"

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
unsigned long lastDisplay = 0;

// Cached latest readings so the display can refresh (clock) faster than the
// 2 s sensor cadence without re-reading sensors.
static int s_mq135 = 0;
static float s_temp = DHT_ERROR_VALUE;
static float s_hum = 0.0f;

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

    // Status LEDs
    pinMode(PIN_LED_GOOD, OUTPUT);
    pinMode(PIN_LED_MODERATE, OUTPUT);
    pinMode(PIN_LED_POOR, OUTPUT);

        // OLED display
    display_init();

    // Network: WiFi + SNTP + weather (non-blocking, dev firmware only)
    net_init();

        // CSV header
    Serial.println(CSV_HEADER);
}

void loop()
{
        // 1. Poll PMS5003 continuously (non-blocking)
    pms5003_poll();

    // 2. Service the network (WiFi / SNTP / weather) - non-blocking
    net_update();

    // 3. Read MQ-135 and DHT22 at fixed interval
    if (millis() - lastRead >= READ_INTERVAL_MS)
    {
                lastRead = millis();

        s_mq135 = sensors_read_mq135();

        sensors_read_dht(s_temp, s_hum);

        // Print full raw CSV line (must match CSV_HEADER order)
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
        Serial.print(','); Serial.print(s_mq135);
        Serial.print(','); Serial.print(s_temp, 2);
        Serial.print(','); Serial.println(s_hum, 2);
    }

    // 4. Refresh OLED + status LEDs (~1 s, so the clock stays live)
    if (millis() - lastDisplay >= NET_UPDATE_INTERVAL_MS)
    {
        lastDisplay = millis();

        AirStatus status = display_compute_status(s_mq135, pms_pm25_atm, pms_n03);

        DisplayEnv env;
        NetTime nt = net_get_time();
        if (nt.valid)
        {
            env.time_valid = true;
            env.weekday = net_weekday_short(nt.weekday);
            env.day = nt.day;
            env.month = nt.month;
            env.hour = nt.hour;
            env.minute = nt.minute;
        }
        NetWeather wx = net_get_weather();
        if (wx.valid)
        {
            env.weather_valid = true;
            env.weather_temp = wx.temp_c;
            env.condition = wx.condition.c_str();
        }
        display_update_env(s_temp, s_hum, status, env);

        digitalWrite(PIN_LED_GOOD, status == AIR_GOOD ? HIGH : LOW);
        digitalWrite(PIN_LED_MODERATE, status == AIR_MODERATE ? HIGH : LOW);
        digitalWrite(PIN_LED_POOR, status == AIR_POOR ? HIGH : LOW);
    }

        // 5. Periodic PMS5003 diagnostic (every 10 s).
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


