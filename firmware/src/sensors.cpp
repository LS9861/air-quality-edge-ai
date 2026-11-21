#include "config.h"
#include <Arduino.h>
#include <DHT.h>

static DHT dht(PIN_DHT, DHT_TYPE);

void sensors_init()
{
    dht.begin();
        // MQ-135 ADC: use 12-bit resolution (0-4095)
    analogReadResolution(12);
    // Set attenuation for ~3.3V range (full-scale ~3.3V input)
    analogSetAttenuation(ADC_11db);
}

// Returns averaged raw ADC value (0-4095)
int sensors_read_mq135()
{
    long sum = 0;
    for (int i = 0; i < MQ135_SAMPLES; i++)
    {
        sum += analogRead(PIN_MQ135_ADC);
        delay(MQ135_SAMPLE_DELAY_MS);
    }
    return (int)(sum / MQ135_SAMPLES);
}

// Reads temperature & humidity; returns false if DHT read fails
bool sensors_read_dht(float &temp_c, float &humidity_pct)
{
    float hum = dht.readHumidity();
    float temp = dht.readTemperature();

    if (isnan(hum) || isnan(temp))
    {
        temp_c = DHT_ERROR_VALUE;
        humidity_pct = DHT_ERROR_VALUE;
        return false;
    }

    temp_c = temp;
    humidity_pct = hum;
    return true;
}