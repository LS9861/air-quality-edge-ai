#include "net.h"
#include "config.h"
#include <WiFi.h>
#include <time.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#if !OWM_USE_HTTP
#include <WiFiClientSecure.h>
#endif
#include "secrets.h"

// ---- State ----
static bool wifi_started = false;
static bool wifi_warned = false;
static bool sntp_configured = false;
static bool sntp_ok = false;

static NetWeather weather;
static unsigned long last_weather_fetch = 0;
static unsigned long last_weather_attempt = 0;
static const unsigned long WEATHER_RETRY_MS = 60000UL; // retry cadence on failure

static const char *WDAYS[] = {"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"};

const char *net_weekday_short(int weekday)
{
    if (weekday < 0 || weekday > 6)
        return "--";
    return WDAYS[weekday];
}

static void start_wifi()
{
    Serial.println("# NET: connecting to WiFi...");
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    wifi_started = true;
}

static void config_sntp()
{
    // configTzTime sets the timezone (with DST rules) and starts SNTP.
    configTzTime(TZ_INFO, NTP_SERVER_1, NTP_SERVER_2);
    sntp_configured = true;
    Serial.println("# NET: SNTP configured");
}

static NetTime get_time_now()
{
    NetTime t;
    struct tm ti;
    if (!getLocalTime(&ti, 0))
        return t; // valid stays false
    t.valid = true;
    t.day = ti.tm_mday;
    t.month = ti.tm_mon;
    t.weekday = ti.tm_wday;
    t.hour = ti.tm_hour;
    t.minute = ti.tm_min;
    return t;
}

// Map OWM "main" group to a short label.
static String owm_condition(JsonDocument &doc)
{
    const char *main = doc["weather"][0]["main"] | "";
    if (strlen(main) == 0)
        return String("--");
    // Trim to ~9 chars to fit the display; keep known short forms.
    if (strcmp(main, "Thunderstorm") == 0) return String("Storm");
    if (strcmp(main, "Drizzle") == 0)      return String("Drizzle");
    if (strcmp(main, "Clouds") == 0)       return String("Cloudy");
    if (strcmp(main, "Clear") == 0)        return String("Clear");
    if (strcmp(main, "Snow") == 0)         return String("Snow");
    if (strcmp(main, "Rain") == 0)         return String("Rain");
    if (strcmp(main, "Mist") == 0 || strcmp(main, "Fog") == 0 ||
        strcmp(main, "Haze") == 0)
        return String("Mist");
    return String(main);
}

static void fetch_weather()
{
    last_weather_attempt = millis();
    if (WiFi.status() != WL_CONNECTED)
        return;

    HTTPClient http;
#if OWM_USE_HTTP
    String url = String("http://api.openweathermap.org/data/2.5/weather?q=") +
                 OWM_CITY + "&appid=" + OWM_API_KEY + "&units=" + OWM_UNITS;
    if (!http.begin(url))
    {
        Serial.println("# NET: OWM begin failed");
        return;
    }
#else
    WiFiClientSecure client;
    client.setInsecure(); // skip cert validation (fine for a hobby dashboard)
    String url = String("https://api.openweathermap.org/data/2.5/weather?q=") +
                 OWM_CITY + "&appid=" + OWM_API_KEY + "&units=" + OWM_UNITS;
    if (!http.begin(client, url))
    {
        Serial.println("# NET: OWM begin failed");
        return;
    }
#endif

    int code = http.GET();
    if (code == 200)
    {
        String payload = http.getString();
        JsonDocument doc;
        DeserializationError err = deserializeJson(doc, payload);
        if (!err)
        {
            weather.temp_c = doc["main"]["temp"] | 0.0f;
            weather.condition = owm_condition(doc);
            weather.valid = true;
            Serial.printf("# NET: weather %.1fC %s\n", weather.temp_c,
                          weather.condition.c_str());
        }
        else
        {
            Serial.printf("# NET: JSON parse error: %s\n", err.c_str());
        }
    }
    else
    {
        Serial.printf("# NET: OWM HTTP %d\n", code);
    }
    http.end();
}

void net_init()
{
    start_wifi();
}

void net_update()
{
    if (!wifi_started)
        return;

    bool connected = (WiFi.status() == WL_CONNECTED);

    if (connected)
    {
        wifi_warned = false; // reconnecting successfully clears the warning

        if (!sntp_configured)
            config_sntp();

        // Mark SNTP success once local time is valid.
        if (sntp_configured && !sntp_ok)
        {
            struct tm ti;
            if (getLocalTime(&ti, 0))
            {
                sntp_ok = true;
                Serial.println("# NET: time synced");
            }
        }

        // Periodic weather fetch (first one immediately after connect).
        unsigned long now = millis();
        if (last_weather_attempt == 0)
        {
            fetch_weather();
            last_weather_fetch = now;
        }
        else if (weather.valid &&
                 (now - last_weather_fetch >= OWM_FETCH_INTERVAL_MS))
        {
            fetch_weather();
            last_weather_fetch = now;
        }
        else if (!weather.valid &&
                 (now - last_weather_attempt >= WEATHER_RETRY_MS))
        {
            fetch_weather(); // retry until first success
        }
    }
    else if (!wifi_warned && millis() > 15000)
    {
        wifi_warned = true;
        Serial.println("# NET: WiFi not connected yet (display shows --)");
    }
}

NetTime net_get_time()
{
    if (!sntp_ok)
        return NetTime();
    return get_time_now();
}

NetWeather net_get_weather()
{
    return weather;
}
