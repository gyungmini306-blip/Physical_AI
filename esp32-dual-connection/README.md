# ESP32 Smart Home Care — USB + Bluetooth BLE

Prototype for ESP32-D0WD-V3 / ESP32 Dev Module. **Not a certified safety device.**

## Wiring (verify the actual modules before applying power)

| Component | ESP32 pin | Notes |
|---|---|---|
| HC-SR501 PIR OUT | GPIO25 | Typical 3.3V digital signal; module VCC goes to suitable VIN/5V |
| IR obstacle sensor OUT | GPIO26 | **Measure output voltage:** ESP32 GPIO must not receive 5V |
| Green LED | GPIO18 | Series resistor required |
| Yellow LED | GPIO19 | Series resistor required |
| Sensor GNDs | GND | Common ground |

PIR active HIGH / IR active LOW are assumptions; validate with raw readings. Debounce is 300ms. Alert demo rule: PIR and IR both active continuously for 1.5s; ACK acknowledges while alert remains active, and state clears when either sensor clears. It **does not** prove a fall or safety incident.

## 1. Arduino IDE upload

Open `sketches/SmartHomeCare/SmartHomeCare.ino`, install **esp32 by Espressif Systems 3.3.12**, select `ESP32 Dev Module` and the actual USB bridge port (previous setup: COM3), then Upload. Close Serial Monitor before launching Python dashboard because both cannot own COM3 concurrently.

## 2. PC dashboard

Windows with Python 3.10+:

```powershell
cd pc
py -m pip install -r requirements.txt
py dashboard.py --port COM3
```

Program tries **both** USB and BLE simultaneously. BLE receiver requires Windows Bluetooth LE hardware/radio and Windows Bluetooth enabled. To use USB without Bluetooth: `py dashboard.py --port COM3 --no-ble`. To use BLE only: `py dashboard.py --port ""`.

The ESP32 broadcasts `SmartHomeCare-ESP32` with a custom GATT service. Notifications are divided into 20-byte fragments and reassembled by a newline-terminated JSON protocol. The dashboard deduplicates identical `seq` frames from USB and BLE. The most recent `event` is repeated in subsequent snapshots until another event; only one latest event is preserved per 1-second report, so fast intermediate transitions may not all be logged. `ACK` commands can be sent over both interfaces; an ACK is accepted only during an active alert.

If the Windows PC has no Bluetooth adapter, USB still works; installing Python BLE packages does not create Bluetooth capability. Bluetooth is local wireless communication; internet is not needed.

## 3. Docker compile (optional)

```powershell
docker build -t esp32-dev:1.0 .
docker run --rm -v "${PWD}:/workspace" esp32-dev:1.0 arduino-cli compile --fqbn esp32:esp32:esp32 /workspace/sketches/SmartHomeCare
```

The recommended physical USB upload route is Arduino IDE on Windows. Docker USB passthrough via WSL2/USBIP is not configured by this project.

## 4. Tests

```powershell
py -m unittest discover -s tests -v
```

## JSON example

```json
{"seq":8,"sec":25,"pir":false,"ir":true,"alert":false,"ack":false,"pirCount":2,"irCount":1,"alertCount":0,"eventId":3,"event":"IR DETECTED"}
```

`sec` is seconds since ESP32 boot. Counts reset on reboot; they are not persisted. USB and BLE may both send the same `seq` and are deduplicated. For robust production use add disconnect alarms, persistent history, timestamping, transport integrity, security/pairing, watchdog/reconnect, and independent warning hardware.

## References

- Espressif Arduino ESP32 BLE examples: https://github.com/espressif/arduino-esp32/tree/master/libraries/BLE/examples
- Bleak documentation: https://bleak.readthedocs.io/en/latest/usage.html
