// ESP32 Dev Module, HC-SR501 PIR, IR obstacle sensor, and two external LEDs.
// Verify wiring. Never input 5V to ESP32 GPIO.
const int PIR_PIN = 25;
const int IR_PIN = 26;
const int GREEN_LED = 18;
const int YELLOW_LED = 19;
const int PIR_ACTIVE = HIGH;
const int IR_ACTIVE = LOW; // Many IR obstacle modules use active-low output.

void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT);
  pinMode(IR_PIN, INPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  Serial.println("Smart Home Care System Started");
}

void loop() {
  int pirValue = digitalRead(PIR_PIN);
  int irValue = digitalRead(IR_PIN);
  bool motionDetected = (pirValue == PIR_ACTIVE);
  bool obstacleDetected = (irValue == IR_ACTIVE);
  digitalWrite(GREEN_LED, motionDetected ? HIGH : LOW);
  digitalWrite(YELLOW_LED, obstacleDetected ? HIGH : LOW);
  Serial.print("PIR: ");
  Serial.print(motionDetected ? "MOTION" : "NORMAL");
  Serial.print(" | IR: ");
  Serial.println(obstacleDetected ? "DETECTED" : "CLEAR");
  delay(500);
}
