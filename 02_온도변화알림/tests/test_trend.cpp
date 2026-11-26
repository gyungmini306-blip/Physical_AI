#include "../sketches/TemperatureAlert/TrendMonitor.h"
#include "../sketches/TemperatureAlert/AlarmOutput.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>

static void prime(TrendMonitor& m, float temp) {
  for (int i=0; i<HISTORY_SIZE; ++i) {
    assert(!m.update(temp));
    assert(m.state == Trend::WarmingUp);
    assert(isnan(m.delta));
  }
}

int main() {
  TrendMonitor m;
  prime(m, 25);
  assert(!m.update(25));
  assert(m.state == Trend::Stable && m.delta == 0);
  assert(m.update(27));
  assert(m.state == Trend::Rising && m.delta == 2);
  assert(!m.update(27)); // Same alarm must not repeat.
  assert(!m.update(26.5f)); // Hysteresis.
  assert(m.state == Trend::Rising);
  assert(!m.update(26));
  assert(m.state == Trend::Stable);
  assert(m.update(23));
  assert(m.state == Trend::Falling && m.delta == -2);
  assert(!m.update(23.5f));
  assert(m.state == Trend::Falling);
  assert(m.update(27)); // Direct change of direction.
  assert(m.state == Trend::Rising);
  assert(!m.update(NAN));
  assert(m.state == Trend::SensorError && isnan(m.temperature));
  prime(m, 20);
  assert(m.update(18));
  assert(m.state == Trend::Falling);
  assert(!m.update(19));
  assert(m.state == Trend::Stable);
  m.reset();
  prime(m, 24);
  assert(!m.update(24));
  for(int i=0;i<40;++i) assert(!m.update(24));
  assert(m.state == Trend::Stable);
  for (Trend s : {Trend::WarmingUp, Trend::Stable, Trend::Rising, Trend::Falling, Trend::SensorError}) {
    assert(riseLed(s) == (s == Trend::Rising));
    assert(startBuzzer(s, true) == (s == Trend::Falling));
    assert(!startBuzzer(s, false));
  }
  puts("All trend and alarm-output tests passed.");
}
