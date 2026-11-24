#include "status_led.h"
#include "config.h"
#include <Arduino.h>

// Current blink pattern (milliseconds). on_ms == 0 means "steady ON".
struct LedPattern
{
    uint32_t on_ms;
    uint32_t off_ms;
};

static LedPattern s_pattern = {0, 0}; // default: steady ON
static bool s_pattern_set = false;
static bool s_led_state = false;
static uint32_t s_last_toggle = 0;
static uint32_t s_current_phase = 0; // duration of the phase we're in

static LedPattern pattern_for(AirStatus status)
{
    switch (status)
    {
    case AIR_GOOD:
        return {0, 0}; // steady ON
    case AIR_MODERATE:
        return {500, 500}; // ~1 s period
    case AIR_POOR:
        return {100, 100}; // fast blink (~5 Hz)
    default:
        return {0, 0};
    }
}

void status_led_init()
{
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW); // start off
    s_led_state = false;
    s_last_toggle = millis();
    s_current_phase = 0;
}

void status_led_set(AirStatus status)
{
    LedPattern p = pattern_for(status);

    // Reprogram only when the pattern actually changes.
    if (s_pattern_set && p.on_ms == s_pattern.on_ms && p.off_ms == s_pattern.off_ms)
        return;

    s_pattern = p;
    s_pattern_set = true;

    // Restart the blink cycle cleanly on change.
    if (p.on_ms == 0)
    {
        // Steady on: force ON immediately.
        s_led_state = true;
        digitalWrite(PIN_STATUS_LED, HIGH);
        s_current_phase = 0;
    }
    else
    {
        // Start with an ON phase.
        s_led_state = true;
        digitalWrite(PIN_STATUS_LED, HIGH);
        s_current_phase = p.on_ms;
    }
    s_last_toggle = millis();
}

void status_led_update()
{
    if (!s_pattern_set)
        return;

    // Steady ON: nothing to time.
    if (s_pattern.on_ms == 0)
    {
        if (!s_led_state)
        {
            s_led_state = true;
            digitalWrite(PIN_STATUS_LED, HIGH);
        }
        return;
    }

    // Blinking: toggle when the current phase elapsed.
    if (millis() - s_last_toggle >= s_current_phase)
    {
        s_last_toggle = millis();
        s_led_state = !s_led_state;
        digitalWrite(PIN_STATUS_LED, s_led_state ? HIGH : LOW);
        s_current_phase = s_led_state ? s_pattern.on_ms : s_pattern.off_ms;
    }
}
