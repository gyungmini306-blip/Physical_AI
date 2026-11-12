# 학교 PC용 ESP32 자동 설치기

Windows 10/11 x64에서 Arduino 개발환경을 다시 구축하는 실습용 스크립트입니다. 학교 PC가 매번 초기화되는 경우 반복 실행할 수 있습니다.

## 실행 방법

1. 저장소에서 **Code → Download ZIP**을 눌러 다운로드하고 압축을 풉니다.
2. `esp32-school-setup/setup.cmd`를 더블클릭합니다.
3. 설치가 끝나면 Arduino IDE에서 **ESP32 Dev Module**과 실제 CP210x USB 포트(COM 번호)를 선택합니다.
4. ESP32 업로드 후 시리얼 모니터 속도를 **115200 baud**로 지정합니다.

## 설치 대상

| 항목 | 버전 |
|---|---|
| Arduino IDE (ZIP 압축 해제 방식) | 2.3.10 |
| Arduino CLI | 1.5.1 |
| ESP32 보드 패키지 | Espressif 3.3.12 |
| CP210x USB to UART 드라이버 | Silicon Labs 공식 버전 |
| 보드 | ESP32 Dev Module |

개발 도구는 주로 `%LOCALAPPDATA%\ESP32SchoolKit`에 저장됩니다. ESP32 Core는 사용자 Arduino15 경로에 설치됩니다. 인터넷 접근과 저장 공간이 필요합니다.

**학교 관리자 권한이 제한되어 있다면 CP210x 드라이버 설치가 실패할 수 있습니다.** 이 경우 학교 전산 담당자에게 설치를 요청해야 합니다. 본 스크립트는 관리자 정책을 우회하지 않습니다.

## 파일

- `setup.cmd` — 더블클릭 설치 실행
- `setup.ps1` — 공식 프로그램 다운로드, 압축 해제, ESP32 Core 설치, CP210x 드라이버 설치 시도, 컴파일 검사
- `launch-ide.cmd` — Arduino IDE 실행
- `check-build.cmd` — 소스코드 컴파일 확인
- `sketches/SmartHomeCare/SmartHomeCare.ino` — PIR/IR/LED 센서 실습 코드

## GPIO 연결

| 장치 | ESP32 GPIO | 기능 |
|---|---|---|
| HC-SR501 PIR OUT | 25 | HIGH일 때 움직임 감지로 처리 |
| IR 장애물 센서 OUT | 26 | LOW일 때 장애물 감지로 처리 |
| 녹색 LED | 18 | PIR 상태 |
| 노란색 LED | 19 | IR 상태 |

ESP32 GPIO에 5V를 직접 입력하면 손상 위험이 있습니다. 전원/신호 전압, 공통 GND, LED 전류 제한 저항을 확인하세요. 이 코드는 센서 상태 확인용이며 실제 낙상/울음 위험 탐지 기능은 구현하지 않았습니다.

## 제한 사항

- **Docker는 설치하지 않습니다.** 학교 PC에서 Arduino IDE/CLI를 직접 사용합니다.
- 컴퓨터 초기화 시 도구를 다시 내려받아야 할 수 있습니다.
- 학교 네트워크, PC 정책 또는 드라이버 권한에 따라 설치가 실패할 수 있습니다.
- 실제 학교 PC에서 스크립트 전체가 성공하는지는 아직 검증되지 않았습니다.

공식 자료: [Arduino IDE](https://github.com/arduino/arduino-ide/releases), [Arduino CLI](https://github.com/arduino/arduino-cli/releases), [ESP32 Core](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html), [CP210x](https://www.silabs.com/software-and-tools/usb-to-uart-bridge-vcp-drivers).

## 추가 기능 — SmartHomeCarePlus

기존 코드에 더해 ESP32의 자체 Wi-Fi로 **스마트폰 웹 대시보드, PIR/IR 감지 횟수, 최근 12개 이벤트 기록, 동시 감지 주의 알림**을 확인하는 별도 예제를 추가했습니다. 원본 코드는 삭제하거나 변경하지 않았습니다.

- 코드: [`sketches/SmartHomeCarePlus/SmartHomeCarePlus.ino`](sketches/SmartHomeCarePlus/SmartHomeCarePlus.ino)
- 사용법: [`sketches/SmartHomeCarePlus/README.md`](sketches/SmartHomeCarePlus/README.md)
- `setup.cmd`는 기존 원본 예제를 검사합니다. PLUS를 올리려면 Arduino IDE에서 PLUS 스케치를 직접 열어 업로드해야 합니다.
- `check-build.cmd`는 원본과 PLUS 두 예제를 컴파일합니다.
- PLUS 스마트폰 연결: `HomeCare-ESP32` / `homecare2026` → `http://192.168.4.1` (교실 시연용 공개 기본 비밀번호)
- 동시 센서 감지는 실제 사고나 위험을 판정하지 않으며, 학습용 상태 표시입니다.

