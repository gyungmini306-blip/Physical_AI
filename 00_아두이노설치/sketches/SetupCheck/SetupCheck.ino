// Compile-only smoke test; no hardware peripherals required.
void setup() {
  Serial.begin(115200);
  Serial.println("ESP32 setup check");
}

void loop() {
  delay(1000);
}
