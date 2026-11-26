# 02_온도변화알림

## 동작 요구사항

DHT11을 3초마다 측정하고 약 30초 전과 비교합니다. 기존 판정 기준(±2°C, 해제 ±1°C)을 유지합니다. 최초 판정은 약 33초 후입니다.

| 상태 | 빨간 LED(GPIO18) | 부저 신호(GPIO23) |
|---|---|---|
| 상승(+2°C 이상) | 켜짐 | 꺼짐 |
| 하강(-2°C 이하) | 꺼짐 | 하강 진입 시 1초 HIGH |
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
| 부저 구동 신호 | GPIO23, active HIGH |
| 부저 전원/접지 | 부저 및 구동회로 정격에 맞게 구성, 공통 GND |

현재 사용자 배선은 GPIO23→저항→TMB12A05→GND이나, TMB12A05는 5V 정격 전자기식 부저로 직접 GPIO 구동을 검증하지 않았습니다. 저항만으로 보호 및 정상 음량을 보장할 수 없습니다. 전원을 끄고 부저를 분리한 뒤 정격에 맞는 구동 회로 또는 호환 부저를 확보하여 연결하세요. GPIO에 5V를 직접 연결하면 안 됩니다. 센서 및 LED는 그대로 사용 가능합니다. 베어 DHT11은 DATA 풀업 저항 필요 여부 확인.

## Windows 실행 (Docker/WSL 불필요)

1. 최신 저장소를 받아 00_아두이노설치/setup.cmd 실행(Arduino, ESP32, DHT, Python, MariaDB).
2. MariaDB_설정/setup-db.cmd 실행. 네이티브 DB, 계정, 테이블 자동 초기화.
3. MariaDB_설정/test-db.cmd 실행. 실제 INSERT/SELECT/ROLLBACK 검증. 시험 행은 저장하지 않습니다.
4. sketches/TemperatureAlert/TemperatureAlert.ino 열고 ESP32 Dev Module, 실제 COM 포트 선택 후 USB 업로드.
5. Arduino IDE 시리얼 모니터 종료(동일 COM 포트 동시 사용 불가).
6. start-server.cmd 실행, 표시된 ESP32 COM 포트 입력. DB 자동 시작 및 Flask 실행.
7. 브라우저 자동 열림; 수동 접속 http://127.0.0.1:5000. CMD 창은 유지. 종료 Ctrl+C.

DB는 127.0.0.1:3307 / temperature_alert / measurements. 실제 데이터와 비밀번호는 %LOCALAPPDATA%/ESP32SchoolKit/temperature-mariadb 아래 보존. 상세: [MariaDB_설정](MariaDB_설정/). 기존 SQLite 데이터는 자동 이전하지 않습니다. 기존 SQLite 기록 조회는 공통 Python으로 server/app.py --backend sqlite 실행.

## PC 웹 화면

USB 115200 baud JSON → Python(pyserial) → MariaDB → Flask 웹. 현재 온도/변화량/상태, 최고/최저/평균, 그래프, 경보 이력, 날짜 필터, CSV 내보내기. USB 연결이 끊기면 실시간 표시를 해제하며 끊긴 동안의 데이터는 복구되지 않습니다. 웹 기본 주소는 로컬 PC 전용입니다.

스마트폰 직접 연결(선택): Temperature-ESP32 / tempdemo2026 / http://192.168.4.1. 이 페이지는 ESP32 자체 RAM을 조회하며 DB 기록 화면과 별개입니다.

## 검증

- tests/test_trend.cpp: C++ 온도 변화 및 출력 규칙 단위 테스트. g++ -std=c++11 -Wall -Wextra -pedantic tests/test_trend.cpp -o test_trend 로 컴파일 후 실행.
- server/test_database.py: SQLite 및 JSON 검증 단위 테스트.
- MariaDB_설정/test-db.cmd: 설치 PC에서 실제 MariaDB 쓰기/읽기/롤백 확인.
- 실제 Windows 설치, ESP32 업로드 및 부저 전기적 동작은 별도 검증 필요. 손의 체온이나 실온 공기로 완만하게 온도를 바꾸고 물/결로/불꽃/고온 열풍은 피하세요.

교육용 예제이며 안전 인증 경보 장치가 아닙니다.
