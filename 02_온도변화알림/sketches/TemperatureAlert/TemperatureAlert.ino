#include <Arduino.h>
#include <esp_system.h>
#include <DHT.h>
#include <WiFi.h>
#include <WebServer.h>
#include "TrendMonitor.h"
#include "AlarmOutput.h"

// DHT11 on GPIO25; red LED on GPIO18; falling alarm on GPIO23.
constexpr uint8_t DHT_PIN = 25;
#define DHT_TYPE DHT11
constexpr uint8_t RISE_LED = 18;
constexpr uint8_t BUZZER_PIN = 23; // Active-high signal to electrically compatible buzzer driver.
constexpr uint32_t SAMPLE_MS = 3000;
constexpr uint32_t BUZZER_MS = 1000;
const char* AP_SSID = "Temperature-ESP32";
const char* AP_PASSWORD = "tempdemo2026"; // Public classroom demo password.

DHT dht(DHT_PIN, DHT_TYPE);
WebServer server(80);
TrendMonitor monitor;
uint32_t lastSample = 0, alarmStart = 0, eventCount = 0, lastEventSec = 0;
bool buzzerOn = false, webReady = false;
Trend lastEvent = Trend::WarmingUp;
char bootId[17] = {};
uint32_t sampleSeq = 0;
String jsonNumber(float value);
void emitSample(bool event, uint32_t now);

const char* stateName(Trend state) {
  switch (state) {
    case Trend::Rising: return "RISING";
    case Trend::Falling: return "FALLING";
    case Trend::Stable: return "STABLE";
    case Trend::SensorError: return "SENSOR_ERROR";
    default: return "WARMING_UP";
  }
}

void setBuzzer(bool on) {
  buzzerOn = on;
  digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
}

void sampleTemperature(uint32_t now) {
  // A long sampling interruption invalidates the 30-second history.
  if (now - lastSample >= SAMPLE_MS * 2) monitor.reset();
  lastSample = now;
  float value = dht.readTemperature();
  bool event = monitor.update(value);
  digitalWrite(RISE_LED, riseLed(monitor.state) ? HIGH : LOW);
  if (event) {
    ++eventCount;
    lastEvent = monitor.state;
    lastEventSec = now / 1000;
  }
  if (startBuzzer(monitor.state, event)) {
    alarmStart = now;
    setBuzzer(true);
  } else if (monitor.state != Trend::Falling) {
    setBuzzer(false);
  }
  emitSample(event, now);
}

const char PAGE[] PROGMEM = R"HTML(<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>온도 변화 알림</title>
<style>
body{font-family:system-ui,sans-serif;background:#edf2f7;color:#172033;margin:0;padding:24px}
main{max-width:560px;margin:auto}section{background:white;border-radius:12px;padding:20px;margin:12px 0}
h1{font-size:24px}#temp{font-size:42px;font-weight:bold}#state{font-size:20px;font-weight:bold}
.rise{color:#b91c1c}.fall{color:#1d4ed8}.error{color:#b45309}small{color:#475569}
</style></head><body><main><h1>ESP32 온도 변화 알림</h1>
<section><small>현재 온도</small><div id="temp">--</div><div id="delta">30초 변화량: --</div></section>
<section><small>현재 상태</small><div id="state">연결 중</div><p id="connection"></p></section>
<section><div id="count">알림 횟수: 0</div><div id="last">최근 알림: 없음</div></section>
<small>3초마다 측정 · 약 30초 전 대비 ±2°C · 상승: 빨간 LED / 하강 진입: 부저 1초 · 웹 화면은 1초마다 갱신</small>
<script>
const names={WARMING_UP:'측정 준비 중',STABLE:'정상',RISING:'온도 상승 · 빨간 LED',FALLING:'온도 하강 · 부저 경보',SENSOR_ERROR:'센서 측정 실패'};
const e=id=>document.getElementById(id);
const number=v=>typeof v==='number'?v.toFixed(1)+' °C':'--';
async function poll(){
  try{
    const controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort(),2500);
    let data;
    try{
      const res=await fetch('/api/status',{cache:'no-store',signal:controller.signal});
      if(!res.ok)throw Error('HTTP');
      data=await res.json();
    }finally{clearTimeout(timeout);}
    e('temp').textContent=number(data.temperature);
    e('delta').textContent='30초 변화량: '+number(data.delta);
    e('state').textContent=names[data.state]||'알 수 없음';
    e('state').className=data.state==='RISING'?'rise':data.state==='FALLING'?'fall':data.state==='SENSOR_ERROR'?'error':'';
    e('count').textContent='알림 횟수: '+data.eventCount;
    e('last').textContent=data.eventCount?'최근 알림: '+names[data.lastEvent]+' (부팅 후 '+data.lastEventSec+'초)':'최근 알림: 없음';
    e('connection').textContent='ESP32 연결됨';
  }catch(err){
    e('connection').textContent='연결 끊김 — Wi-Fi 확인';
    e('temp').textContent='--';e('delta').textContent='30초 변화량: --';
    e('state').textContent='연결 오류';e('state').className='error';
  }finally{setTimeout(poll,1000);}
}
poll();
</script></main></body></html>)HTML";

String jsonNumber(float value) {
  return isfinite(value) ? String(value, 1) : String("null");
}

void emitSample(bool event, uint32_t now) {
  String line = "{\"kind\":\"temperature\",\"boot\":\"";
  line += bootId;
  line += "\",\"seq\":"; line += String(++sampleSeq);
  line += ",\"uptime_ms\":"; line += String(now);
  line += ",\"temperature\":"; line += jsonNumber(monitor.temperature);
  line += ",\"delta\":"; line += jsonNumber(monitor.delta);
  line += ",\"state\":\""; line += stateName(monitor.state);
  line += "\",\"alarm\":"; line += (event ? "true" : "false");
  line += "}";
  Serial.println(line);
}

void sendStatus() {
  String body = "{\"temperature\":";
  body += jsonNumber(monitor.temperature);
  body += ",\"delta\":";
  body += jsonNumber(monitor.delta);
  body += ",\"state\":\""; body += stateName(monitor.state);
  body += "\",\"eventCount\":"; body += String(eventCount);
  body += ",\"lastEvent\":\""; body += stateName(lastEvent);
  body += "\",\"lastEventSec\":"; body += String(lastEventSec);
  body += "}";
  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json", body);
}

void setup() {
  Serial.begin(115200);
  snprintf(bootId, sizeof(bootId), "%08lx%08lx", (unsigned long)esp_random(), (unsigned long)esp_random());
  pinMode(RISE_LED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(RISE_LED, LOW);
  setBuzzer(false);
  dht.begin();
  WiFi.mode(WIFI_AP);
  webReady = WiFi.softAP(AP_SSID, AP_PASSWORD);
  if (webReady) {
    server.on("/", HTTP_GET, [](){ server.send_P(200, "text/html; charset=utf-8", PAGE); });
    server.on("/api/status", HTTP_GET, sendStatus);
    server.begin();
    Serial.print("Web address: http://"); Serial.println(WiFi.softAPIP());
  } else {
    Serial.println("Wi-Fi AP failed; local temperature alarms remain available.");
  }
  lastSample = millis();
}

void loop() {
  uint32_t now = millis();
  if (buzzerOn && now - alarmStart >= BUZZER_MS) setBuzzer(false);
  if (now - lastSample >= SAMPLE_MS) sampleTemperature(now);
  if (webReady) server.handleClient();
  delay(2);
}
