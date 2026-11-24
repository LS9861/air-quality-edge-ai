#pragma once

#include <Arduino.h>
#include "display.h" // AirStatus enum

// ============================================================
// Status LED indicator (single pin, blink-rate encodes status)
// ============================================================
// A non-blocking millis()-based blinker. Call status_led_update()
// frequently from loop(); it never delays, so sampling is unaffected.
//
//   GOOD      : steady ON
//   MODERATE  : ~1 s period  (500 ms on / 500 ms off)
//   POOR      : fast blink   (100 ms on / 100 ms off)
//   (unknown) : off

// Configure the LED pin. Call once in setup().
void status_led_init();

// Set the pattern for the current status. Cheap; call whenever status
// changes (or every loop - it only reprograms on change).
void status_led_set(AirStatus status);

// Drive the LED according to the current pattern. Call every loop().
void status_led_update();
