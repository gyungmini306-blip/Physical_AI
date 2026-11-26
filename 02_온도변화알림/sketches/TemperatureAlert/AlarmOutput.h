#pragma once
#include "TrendMonitor.h"

// Red LED follows the rising state; buzzer pulses only on entry to falling.
inline bool riseLed(Trend state) { return state == Trend::Rising; }
inline bool startBuzzer(Trend state, bool event) {
  return state == Trend::Falling && event;
}
