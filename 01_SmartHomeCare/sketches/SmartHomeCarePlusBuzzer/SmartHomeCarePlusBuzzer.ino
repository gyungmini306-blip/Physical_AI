// ESP32 Smart Home Care PLUS (two-pin buzzer edition).
// GPIO23 controls a transistor driver; do not connect an unknown buzzer to GPIO directly.
// Educational sensor visualization ONLY. Not a fall/cry/emergency detector.
// ESP32 Arduino Core 3.3.12 / ESP32 Dev Module.
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>

constexpr uint8_t PIR_PIN = 25;
constexpr uint8_t IR_PIN = 26;
constexpr uint8_t GREEN_LED = 18;
constexpr uint8_t YELLOW_LED = 19;
constexpr uint8_t BUZZER_PIN = 23;  // GPIO -> 1k base resistor -> NPN transistor
// true = ACTIVE buzzer (has oscillator), false = PASSIVE buzzer (needs PWM tone).
constexpr bool BUZZER_ACTIVE = true;
constexpr uint32_t BUZZER_TONE_HZ = 2000;
constexpr uint8_t PIR_ACTIVE = HIGH;
constexpr uint8_t IR_ACTIVE = LOW;  // Adjust if the actual IR module is active-HIGH.

// Demo-only local hotspot credentials: publicly visible in this repository.
// Change password before using outside a controlled classroom demonstration.
const char *AP_SSID = "HomeCare-ESP32";
const char *AP_PASSWORD = "homecare2026";

constexpr unsigned long SAMPLE_MS = 80;
constexpr unsigned long BOTH_ALERT_MS = 0; // Immediate alarm when PIR+IR both active.
constexpr unsigned long BLINK_MS = 250;
constexpr size_t EVENT_CAPACITY = 12;

WebServer server(80);
struct Event { unsigned long timeMs; const char *label; };
Event events[EVENT_CAPACITY];
size_t nextEvent = 0;
size_t eventCount = 0;
unsigned long lastSampleMs = 0;
unsigned long bothSinceMs = 0;
bool pirDetected = false;
bool irDetected = false;
bool combinedAlert = false; // Tracks ongoing simultaneous sensor activation.
bool alarmLatched = false;  // Keeps buzzer on until the web acknowledgement.
bool acknowledged = false;
bool buzzerOutputOn = false;
bool passivePwmReady = false;
uint32_t pirCount = 0;
uint32_t irCount = 0;
uint32_t alertCount = 0;

const char PAGE[] PROGMEM = R"HTML(
<!doctype html><html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HomeCare | ESP32</title>
<style>
:root{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:#18243a;background:#f2f6fb}
*{box-sizing:border-box}body{margin:0;padding:24px 16px}main{max-width:760px;margin:auto}
h1{font-size:1.7rem;margin:0 0 4px}p{line-height:1.5}header{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:22px}
small,.sub{color:#69788d}.pill{border-radius:99px;padding:8px 12px;background:#dcece6;color:#145438;font-weight:700}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.card{background:white;border:1px solid #e1e9f2;border-radius:18px;padding:18px;box-shadow:0 5px 14px #1e365a0a}
.card h2{font-size:.95rem;font-weight:600;margin:0 0 10px;color:#617188}.value{font-size:1.7rem;font-weight:750}.on{color:#bf6116}.off{color:#258060}
#banner{margin:14px 0;padding:18px;border-radius:16px;background:#e7f5ef;color:#176047;font-weight:700}
#banner.alert{background:#ffede4;color:#a53714}.wide{margin-top:12px}
.counts{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;text-align:center}.counts strong{display:block;font-size:1.55rem}
button{padding:11px 15px;border:0;border-radius:10px;background:#274c85;color:white;font-weight:700;cursor:pointer;margin:6px 7px 0 0}
button.secondary{background:#e6edf5;color:#294260}button:disabled{opacity:.35;cursor:not-allowed}
li{padding:8px 0;border-bottom:1px solid #edf0f4;font-size:.9rem}ul{padding:0;list-style:none;margin:8px 0 0}
footer{font-size:.78rem;color:#66758b;margin-top:20px;line-height:1.5}
@media(max-width:440px){.grid{grid-template-columns:1fr}.counts strong{font-size:1.3rem}header{align-items:start}}
</style></head><body><main>
<header><div><h1>🏠 Smart Home Care</h1><span class="sub">ESP32 · 교실 시연용 로컬 모니터링</span></div><div id="link" class="pill">연결 중</div></header>
<div class="grid">
<section class="card"><h2>PIR 움직임 센서 · GPIO 25</h2><div id="pir" class="value">—</div><small>센서의 HIGH 출력 기준</small></section>
<section class="card"><h2>IR 근접 센서 · GPIO 26</h2><div id="ir" class="value">—</div><small>센서의 LOW 출력 기준</small></section>
</div>
<div id="banner">센서 상태 확인 중…</div>
<section class="card wide"><h2>감지 발생 횟수 (전원 켠 이후)</h2><div class="counts">
<div><strong id="pc">0</strong><small>PIR 시작</small></div><div><strong id="ic">0</strong><small>IR 시작</small></div><div><strong id="ac">0</strong><small>동시감지 주의</small></div>
</div><div style="margin-top:12px"><button id="ack" onclick="postAction('/api/ack')">주의 알림 확인</button><button class="secondary" onclick="postAction('/api/reset')">횟수·기록 초기화</button></div></section>
<section class="card wide"><h2>최근 이벤트 (최대 12건)</h2><ul id="events"><li>아직 기록 없음</li></ul></section>
<footer>작동 방식: 두 센서가 동시에 활성화되면 부저 경보를 유지하고, 웹의 '주의 알림 확인' 버튼으로만 경보를 종료합니다. 이는 교육용 임의 규칙이며 실제 낙상·울음·위험 상황을 판별하지 않습니다. 인터넷이나 클라우드를 사용하지 않습니다. 기록은 ESP32 재시작 시 사라집니다. 가정용 안전 경보 장치로 사용하지 마세요.</footer>
</main><script>
const el=id=>document.getElementById(id);
async function postAction(path){try{await fetch(path,{method:'POST'});await refresh()}catch(e){el('link').textContent='연결 끊김'}}
async function refresh(){try{
const r=await fetch('/api/status',{cache:'no-store'});if(!r.ok)throw Error('offline');const d=await r.json();
el('link').textContent='연결됨';el('pir').textContent=d.pir?'움직임 감지':'움직임 없음';el('pir').className='value '+(d.pir?'on':'off');
el('ir').textContent=d.ir?'근접 물체 감지':'감지 없음';el('ir').className='value '+(d.ir?'on':'off');
el('pc').textContent=d.pirCount;el('ic').textContent=d.irCount;el('ac').textContent=d.alertCount;
const banner=el('banner');banner.className=d.alert?'alert':'';
banner.textContent=d.alert?'⚠ 부저 경보 유지 중 — 주의 알림 확인을 눌러 정지':(d.ack?'주의 알림 확인 완료':(d.pir||d.ir?'센서 감지 중 — 일반 모니터링':'정상 — 감지 신호 없음'));
el('ack').disabled=!d.alert;
const list=el('events');list.replaceChildren();if(!d.events.length){const li=document.createElement('li');li.textContent='아직 기록 없음';list.append(li)}
for(const e of d.events){const li=document.createElement('li');li.textContent='전원 후 '+e.sec+'초 · '+e.name;list.append(li)}
}catch(e){el('link').textContent='연결 끊김'}}
refresh();setInterval(refresh,1000);
</script></body></html>
)HTML";

void addEvent(const char *label) {
  events[nextEvent] = {millis(), label};
  nextEvent = (nextEvent + 1) % EVENT_CAPACITY;
  if (eventCount < EVENT_CAPACITY) ++eventCount;
  Serial.print("[EVENT] ");
  Serial.println(label);
}

// PWM is provided by ESP32 LEDC for passive buzzers. A transistor driver is assumed.
void driveBuzzer(bool on) {
  if (on == buzzerOutputOn) return;
  if (BUZZER_ACTIVE) {
    digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
    buzzerOutputOn = on;
  } else if (passivePwmReady) {
    ledcWriteTone(BUZZER_PIN, on ? BUZZER_TONE_HZ : 0);
    buzzerOutputOn = on;
  }
}

void sampleSensors(unsigned long now) {
  if (now - lastSampleMs < SAMPLE_MS) return;
  lastSampleMs = now;
  bool newPir = (digitalRead(PIR_PIN) == PIR_ACTIVE);
  bool newIr = (digitalRead(IR_PIN) == IR_ACTIVE);
  if (newPir != pirDetected) {
    pirDetected = newPir;
    if (newPir) { ++pirCount; addEvent("PIR MOTION"); }
    else addEvent("PIR CLEAR");
  }
  if (newIr != irDetected) {
    irDetected = newIr;
    if (newIr) { ++irCount; addEvent("IR DETECTED"); }
    else addEvent("IR CLEAR");
  }
  if (pirDetected && irDetected) {
    if (bothSinceMs == 0) bothSinceMs = now;
    if (!combinedAlert && now - bothSinceMs >= BOTH_ALERT_MS) {
      combinedAlert = true;
      alarmLatched = true;
      acknowledged = false;
      ++alertCount;
      addEvent("BOTH SENSORS - ATTENTION");
    }
  } else {
    bothSinceMs = 0;
    if (combinedAlert) addEvent("SIMULTANEOUS DETECTION ENDED");
    combinedAlert = false;
    // Keep alarmLatched unchanged. The user must acknowledge the alarm.
  }
  digitalWrite(GREEN_LED, pirDetected ? HIGH : LOW);
  // Yellow: IR indicator; blink for unacknowledged simultaneous detection.
  bool yellowOn = irDetected;
  if (alarmLatched) yellowOn = (now / BLINK_MS) % 2 == 0;
  digitalWrite(YELLOW_LED, yellowOn ? HIGH : LOW);
  driveBuzzer(alarmLatched);
}

void sendStatus() {
  String json;
  json.reserve(1150);
  json += "{\"pir\":"; json += (pirDetected ? "true" : "false");
  json += ",\"ir\":"; json += (irDetected ? "true" : "false");
  json += ",\"alert\":"; json += (alarmLatched ? "true" : "false");
  json += ",\"ack\":"; json += (acknowledged ? "true" : "false");
  json += ",\"pirCount\":"; json += String(pirCount);
  json += ",\"irCount\":"; json += String(irCount);
  json += ",\"alertCount\":"; json += String(alertCount);
  json += ",\"events\":[";
  for (size_t i = 0; i < eventCount; ++i) {
    size_t pos = (nextEvent + EVENT_CAPACITY - 1 - i) % EVENT_CAPACITY;
    if (i) json += ',';
    json += "{\"sec\":";
    json += String(events[pos].timeMs / 1000UL);
    json += ",\"name\":\"";
    json += events[pos].label; // Labels are fixed constants; no user input.
    json += "\"}";
  }
  json += "]}";
  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json; charset=utf-8", json);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT);
  pinMode(IR_PIN, INPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  if (!BUZZER_ACTIVE) {
    passivePwmReady = ledcAttach(BUZZER_PIN, BUZZER_TONE_HZ, 8);
    if (!passivePwmReady) Serial.println("ERROR: buzzer PWM setup failed");
  }
  WiFi.mode(WIFI_AP);
  if (WiFi.softAP(AP_SSID, AP_PASSWORD)) {
    Serial.print("Connect your phone Wi-Fi to "); Serial.println(AP_SSID);
    Serial.print("Open http://"); Serial.println(WiFi.softAPIP());
  } else {
    Serial.println("ERROR: Wi-Fi access point failed to start");
  }
  server.on("/", HTTP_GET, []() { server.send_P(200, "text/html; charset=utf-8", PAGE); });
  server.on("/api/status", HTTP_GET, sendStatus);
  server.on("/api/ack", HTTP_POST, []() {
    if (alarmLatched) {
      alarmLatched = false;
      acknowledged = true;
      driveBuzzer(false);
      addEvent("ATTENTION ACKNOWLEDGED - BUZZER OFF");
    }
    server.send(200, "text/plain", "OK");
  });
  server.on("/api/reset", HTTP_POST, []() {
    pirCount = irCount = alertCount = 0;
    nextEvent = eventCount = 0;
    server.send(200, "text/plain", "OK");
  });
  server.onNotFound([]() { server.send(404, "text/plain", "Not found"); });
  server.begin();
  addEvent("DEVICE STARTED");
}

void loop() {
  const unsigned long now = millis();
  sampleSensors(now);
  // Blink while waiting for the next sensor sample, too.
  if (alarmLatched) {
    digitalWrite(YELLOW_LED, ((now / BLINK_MS) % 2 == 0) ? HIGH : LOW);
  }
  server.handleClient();
  delay(2);
}
