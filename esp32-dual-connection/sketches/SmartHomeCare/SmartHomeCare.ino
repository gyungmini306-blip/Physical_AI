#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ESP32 Dev Module (ESP32-D0WD-V3), Espressif core 3.3.12.
// Verify sensor OUT voltage: GPIO inputs must not receive 5V.
constexpr uint8_t PIR_PIN = 25;
constexpr uint8_t IR_PIN = 26;
constexpr uint8_t GREEN_LED = 18;
constexpr uint8_t YELLOW_LED = 19;
constexpr uint8_t PIR_ACTIVE = HIGH;
constexpr uint8_t IR_ACTIVE = LOW;

constexpr uint32_t SAMPLE_MS = 100;
constexpr uint32_t REPORT_MS = 1000;
constexpr uint32_t DEBOUNCE_MS = 300;
constexpr uint32_t ALERT_DWELL_MS = 1500;

const char *BLE_NAME = "SmartHomeCare-ESP32";
const char *SERVICE_UUID = "7a8c0001-a83b-4c47-9b37-cda143808888";
const char *TX_UUID = "7a8c0002-a83b-4c47-9b37-cda143808888";
const char *RX_UUID = "7a8c0003-a83b-4c47-9b37-cda143808888";

BLEServer *bleServer = nullptr;
BLECharacteristic *bleTx = nullptr;
volatile bool bleConnected = false;
volatile bool ackRequested = false;
uint32_t sequenceNo = 0;
uint32_t pirCount = 0, irCount = 0, alertCount = 0;
bool pir = false, ir = false, alert = false, ack = false;
uint32_t bothSince = 0;
uint32_t lastSample = 0, lastReport = 0;
String eventName = "BOOT";
uint32_t eventId = 0;

struct StableInput {
  bool raw = false;
  bool stable = false;
  uint32_t changedAt = 0;
  bool update(bool next, uint32_t now) {
    if (next != raw) { raw = next; changedAt = now; }
    if (stable != raw && now - changedAt >= DEBOUNCE_MS) {
      stable = raw;
      return true;
    }
    return false;
  }
};
StableInput pirInput, irInput;

void recordEvent(const char *name) {
  eventName = name;
  ++eventId;
}

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *) override { bleConnected = true; }
  void onDisconnect(BLEServer *server) override {
    bleConnected = false;
    server->startAdvertising();
  }
};

class ReceiveCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *characteristic) override {
    String command = characteristic->getValue();
    command.trim();
    if (command.equalsIgnoreCase("ACK")) ackRequested = true;
  }
};

void handleAck() {
  if (ackRequested) {
    ackRequested = false;
    if (alert) {
      ack = true;
      recordEvent("ACK");
    }
  }
}

void handleSerialCommands() {
  static String line;
  while (Serial.available()) {
    char c = static_cast<char>(Serial.read());
    if (c == '\n' || c == '\r') {
      line.trim();
      if (line.equalsIgnoreCase("ACK")) ackRequested = true;
      line = "";
    } else if (line.length() < 32) {
      line += c;
    }
  }
}

void sense(uint32_t now) {
  bool nextPir = digitalRead(PIR_PIN) == PIR_ACTIVE;
  bool nextIr = digitalRead(IR_PIN) == IR_ACTIVE;
  if (pirInput.update(nextPir, now)) {
    pir = pirInput.stable;
    if (pir) ++pirCount;
    recordEvent(pir ? "PIR MOTION" : "PIR CLEAR");
  }
  if (irInput.update(nextIr, now)) {
    ir = irInput.stable;
    if (ir) ++irCount;
    recordEvent(ir ? "IR DETECTED" : "IR CLEAR");
  }
  digitalWrite(GREEN_LED, pir ? HIGH : LOW);
  digitalWrite(YELLOW_LED, ir ? HIGH : LOW);

  // Demo-only rule; NOT a medically validated danger detector.
  if (pir && ir) {
    if (bothSince == 0) bothSince = now == 0 ? 1 : now;
    if (!alert && now - bothSince >= ALERT_DWELL_MS) {
      alert = true;
      ack = false;
      ++alertCount;
      recordEvent("ALERT ON");
    }
  } else {
    bothSince = 0;
    if (alert || ack) {
      alert = false;
      ack = false;
      recordEvent("ALERT CLEAR");
    }
  }
}

void sendFrame(const String &frame) {
  Serial.println(frame);
  if (!bleConnected || bleTx == nullptr) return;
  // 20-byte chunks work with default BLE ATT MTU.
  String terminated = frame + "\n";
  for (size_t offset = 0; offset < terminated.length() && bleConnected; offset += 20) {
    String chunk = terminated.substring(offset, offset + 20);
    bleTx->setValue((uint8_t *)chunk.c_str(), chunk.length());
    bleTx->notify();
    delay(18);
  }
}

void report(uint32_t now) {
  String payload;
  payload.reserve(250);
  payload += "{\"seq\":" + String(++sequenceNo);
  payload += ",\"sec\":" + String(now / 1000);
  payload += ",\"pir\":" + String(pir ? "true" : "false");
  payload += ",\"ir\":" + String(ir ? "true" : "false");
  payload += ",\"alert\":" + String(alert ? "true" : "false");
  payload += ",\"ack\":" + String(ack ? "true" : "false");
  payload += ",\"pirCount\":" + String(pirCount);
  payload += ",\"irCount\":" + String(irCount);
  payload += ",\"alertCount\":" + String(alertCount);
  payload += ",\"eventId\":" + String(eventId);
  payload += ",\"event\":\"" + eventName + "\"}";
  sendFrame(payload);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT);
  pinMode(IR_PIN, INPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);

  uint32_t now = millis();
  pirInput.raw = pirInput.stable = digitalRead(PIR_PIN) == PIR_ACTIVE;
  irInput.raw = irInput.stable = digitalRead(IR_PIN) == IR_ACTIVE;
  pir = pirInput.stable;
  ir = irInput.stable;
  pirInput.changedAt = irInput.changedAt = now;

  BLEDevice::init(BLE_NAME);
  bleServer = BLEDevice::createServer();
  bleServer->setCallbacks(new ServerCallbacks());
  BLEService *service = bleServer->createService(SERVICE_UUID);
  bleTx = service->createCharacteristic(TX_UUID, BLECharacteristic::PROPERTY_NOTIFY);
  bleTx->addDescriptor(new BLE2902());
  BLECharacteristic *bleRx = service->createCharacteristic(RX_UUID, BLECharacteristic::PROPERTY_WRITE);
  bleRx->setCallbacks(new ReceiveCallbacks());
  service->start();
  BLEAdvertising *advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(SERVICE_UUID);
  advertising->start();
}

void loop() {
  uint32_t now = millis();
  handleSerialCommands();
  handleAck();
  if (now - lastSample >= SAMPLE_MS) {
    lastSample = now;
    sense(now);
  }
  if (now - lastReport >= REPORT_MS) {
    lastReport = now;
    report(now);
  }
  delay(2);
}
