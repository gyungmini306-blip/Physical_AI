# 02_온도변화알림

## 동작 요구사항

DHT11을 3초마다 측정하고 약 30초 전과 비교합니다. 기존 판정 기준(±2°C, 해제 ±1°C)을 유지합니다. 최초 판정은 약 33초 후입니다.

| 상태 | 빨간 LED(GPIO18) | 부저 신호(GPIO23) |
|---|---|---|
| 상승(+2°C 이상) | 켜짐 | 꺼짐 |
| 하강(-2°C 이하) | 꺼짐 | 기본 비활성화 / 검증 후 PWM 1초 |
| 정상/준비/오류 | 꺼짐 | 꺼짐 |

하강 경보가 지속되어도 반복 울리지 않습니다. GPIO19와 파란 LED는 사용하지 않습니다. 상승/하강 진입 모두 DB 경보 기록에 저장됩니다.

## 회로

| 부품 | 연결 |
|---|---|
| DHT11 VCC | 3V3 (센서 모듈 정격 확인) |
| DHT11 DATA | GPIO25 |
| DHT11 GND | GND |
| 빨간 LED 양극 | GPIO18 → 220Ω 직렬 저항 |
| 빨간 LED 음극 | GND |
| 부저 구동 신호 | GPIO23, 기본 입력(고임피던스), 선택적 2kHz PWM |
| 부저 연결 | 정격·방식·회로 및 부품 손상 여부 확인 전 분리 |

**안전 기본값:** 탄 냄새가 발생한 이력이 있으므로 전원을 분리하고 실제 부품 및 배선을 점검하기 전에는 다시 연결하지 마세요. 기존 TMB12A05 및 정체가 확인되지 않은 패시브 부저는 직접 GPIO 구동을 금지합니다. 패시브라는 명칭만으로 압전식 여부나 3.3V 구동 호환성을 알 수 없습니다. 저항만으로 안전을 보장할 수 없습니다.

패시브 압전 부저용 LEDC PWM(2kHz, 하강 진입 시 1초) 코드를 포함했습니다. `sketches/TemperatureAlert/BuzzerConfig.h`의 `PASSIVE_BUZZER_ENABLED` 기본값은 false이며 GPIO23은 입력 상태로 둡니다. 실제 부품과 구동회로가 전기적으로 적합하고 손상되지 않았음을 확인한 뒤에만 활성화할 수 있습니다. 하강 판단과 DB 경보 기록은 부저 비활성화 상태에서도 유지됩니다. DHT11의 VCC 정격과 실제 핀 명칭 역시 확인해야 합니다.

## Windows 실행 (Docker/WSL 불필요)

**start-server.cmd** 하나가 Arduino IDE/CLI, ESP32 Core, CP210x, DHT 라이브러리, Python, Flask, pyserial, PyMySQL, Windows MariaDB를 검사하고 누락된 항목을 설치합니다. 00번 폴더는 필요 없습니다. 기존 설치와 DB는 그대로 재사용합니다.

보드에 최신 스케치가 없는 경우 먼저 Arduino IDE에서 TemperatureAlert.ino를 수동 업로드하세요. 명령 프롬프트에서 `start-server.cmd --ide`를 실행하면 설치 후 스케치가 열립니다. 자동 업로드로 다른 과제 펌웨어를 덮어쓰지 않습니다.

### 평소에는 한 번만 클릭

1. ESP32를 USB로 연결하고 Arduino IDE 시리얼 모니터를 닫습니다.
2. **start-server.cmd**를 더블클릭합니다.

CP210x COM 포트 자동 감지, MariaDB 시작/초기화/연결 확인, Python USB 수신 서버 실행, 브라우저 자동 열기가 순차 실행됩니다. COM1/COM2 같은 내장 통신 포트는 자동 선택하지 않습니다. CP210x 장치가 여러 개일 때만 번호를 묻습니다. 장치가 감지되지 않으면 오류를 표시합니다. 다른 USB-UART 장치는 명령 프롬프트에서 start-server.cmd COMx (실제 포트)를 사용합니다. 기록만 보려면 start-server.cmd --history를 실행합니다.

웹 주소: http://127.0.0.1:5000. 사용 중 CMD 창을 유지하고 종료는 Ctrl+C. MariaDB는 종료하지 않으며 데이터도 보존합니다. 다시 업로드할 때에는 먼저 서버를 종료합니다.

관리용 CMD는 삭제했습니다. 필요한 경우 같은 CMD를 명령 프롬프트에서 `start-server.cmd --menu` (관리 메뉴), `start-server.cmd --db console` (SQL), `start-server.cmd --db selftest` (DB 검증), `start-server.cmd --db stop` (DB 종료, 먼저 웹 서버 종료)로 실행합니다. 기존 SENSOR_ERROR는 센서 측정 문제로 별도로 해결해야 합니다.

DB는 127.0.0.1:3307 / temperature_alert / measurements. 실제 데이터와 비밀번호는 %LOCALAPPDATA%/ESP32SchoolKit/temperature-mariadb 아래 보존. 상세: [MariaDB_설정](MariaDB_설정/). 기존 SQLite 데이터는 자동 이전하지 않습니다. 기존 SQLite 기록 조회는 자동 설치된 Python 환경으로 server/app.py --backend sqlite 실행.

## PC 웹 화면

USB 115200 baud JSON → Python(pyserial) → MariaDB → Flask 웹. 현재 온도/변화량/상태, 최고/최저/평균, 그래프, 경보 이력, 날짜 필터, CSV 내보내기. USB 연결이 끊기면 실시간 표시를 해제하며 끊긴 동안의 데이터는 복구되지 않습니다. 웹 기본 주소는 로컬 PC 전용입니다.

스마트폰 직접 연결(선택): Temperature-ESP32 / tempdemo2026 / http://192.168.4.1. 이 페이지는 ESP32 자체 RAM을 조회하며 DB 기록 화면과 별개입니다.

## 검증

- tests/test_trend.cpp: C++ 온도 변화 및 출력 규칙 단위 테스트. g++ -std=c++11 -Wall -Wextra -pedantic tests/test_trend.cpp -o test_trend 로 컴파일 후 실행.
- server/test_database.py: SQLite 및 JSON 검증 단위 테스트.
- start-server.cmd --db selftest: 설치 PC에서 실제 MariaDB 쓰기/읽기/롤백 확인.
- 실제 Windows 설치, ESP32 업로드 및 부저 전기적 동작은 별도 검증 필요. 손의 체온이나 실온 공기로 완만하게 온도를 바꾸고 물/결로/불꽃/고온 열풍은 피하세요.

교육용 예제이며 안전 인증 경보 장치가 아닙니다.
