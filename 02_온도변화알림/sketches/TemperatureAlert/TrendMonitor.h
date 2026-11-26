#pragma once
#include <math.h>
#include <stdint.h>

// 10 intervals x 3 seconds = approximately 30 seconds.
constexpr uint8_t HISTORY_SIZE = 10;
constexpr float ALERT_DELTA = 2.0f;
constexpr float CLEAR_DELTA = 1.0f;

enum class Trend { WarmingUp, Stable, Rising, Falling, SensorError };

class TrendMonitor {
 public:
  Trend state = Trend::WarmingUp;
  float temperature = NAN;
  float delta = NAN;

  void reset(Trend next = Trend::WarmingUp) {
    count = 0;
    cursor = 0;
    state = next;
    temperature = NAN;
    delta = NAN;
  }

  // Returns true only when entering a new rising/falling state.
  bool update(float value) {
    if (!isfinite(value)) {
      reset(Trend::SensorError);
      return false;
    }
    temperature = value;
    if (count < HISTORY_SIZE) {
      history[cursor] = value;
      cursor = (cursor + 1) % HISTORY_SIZE;
      ++count;
      delta = NAN;
      state = Trend::WarmingUp;
      return false;
    }
    delta = value - history[cursor];
    history[cursor] = value;
    cursor = (cursor + 1) % HISTORY_SIZE;
    Trend previous = state;
    if (delta >= ALERT_DELTA) state = Trend::Rising;
    else if (delta <= -ALERT_DELTA) state = Trend::Falling;
    else if (previous == Trend::Rising && delta > CLEAR_DELTA) state = Trend::Rising;
    else if (previous == Trend::Falling && delta < -CLEAR_DELTA) state = Trend::Falling;
    else state = Trend::Stable;
    return state != previous && (state == Trend::Rising || state == Trend::Falling);
  }
 private:
  float history[HISTORY_SIZE] = {};
  uint8_t count = 0;
  uint8_t cursor = 0;
};
