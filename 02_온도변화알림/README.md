# 02_온도변화알림 — 온도 상승·하강 감지

ESP32와 온도 센서를 사용하여 주변 온도를 측정하고, 최근 약 30초 동안의 변화량이 기준을 넘으면 LED, 부저, 스마트폰 웹 화면으로 알립니다.

## 구현 상태

소스 구현 완료. 센서 및 부저 모델은 아직 사용자 확인 전이며, DHT11과 액티브 HIGH 부저 구동회로를 가정합니다. DHT22는 코드 상단의 DHT_TYPE을 DHT22로 변경합니다. 실제 ESP32 업로드·배선·하드웨어 검증은 별도 필요합니다.

## 준비물 및 배선

| 부품 | ESP32 | 비고 |
|---|---|---|
| DHT11 DATA | GPIO25 | 3.3V 로직; 풀업은 모듈 구성 확인 |
| DHT11 VCC | 3.3V | 실제 센서/모듈 정격 확인 |
| DHT11 GND | GND | 공통 접지 |
| 빨간 LED | GPIO18 | 직렬 220~330Ω 저항, 상승 |
| 파란 LED | GPIO19 | 직렬 220~330Ω 저항, 하강 |
| 부저 구동 신호 | GPIO23 | 액티브 HIGH, 별도 트랜지스터 등 적합한 구동회로 |
| 부저 GND | GND | 외부 전원 사용 시에도 공통 접지 |

DHT11 핀 배치는 모듈에 따라 다릅니다. 베어 센서는 DATA와 3.3V 사이에 4.7~10kΩ 풀업 저항을 사용하며, 모듈에 이미 내장되었는지 확인합니다. ESP32 GPIO에 5V를 직접 입력하지 마세요. 부저는 정격 전압/전류/극성 및 구동회로 확인 후 연결합니다. 모르면 부저를 연결하지 않고 LED와 웹만 먼저 시험하세요.

## 실행

1. [00_아두이노설치](../00_아두이노설치/)의 setup.cmd로 공통 환경 설치.
2. 이 폴더의 install-libraries.cmd 실행 (과제 전용 DHT 라이브러리만 설치). 또는 Arduino IDE 라이브러리 매니저에서 DHT sensor library, Adafruit Unified Sensor 설치.
3. [TemperatureAlert.ino](sketches/TemperatureAlert/TemperatureAlert.ino)를 Arduino IDE에서 열기.
4. ESP32 Dev Module, 실제 COM 포트 선택 및 업로드. 시리얼 모니터 115200.
5. 스마트폰 Wi-Fi에서 Temperature-ESP32 연결 (시연용 비밀번호 tempdemo2026).
6. 브라우저에서 http://192.168.4.1 접속 (실제 주소는 시리얼 출력 확인). 인터넷 없음 표시는 정상일 수 있습니다.

기존 과제 및 공통 설치기는 변경하지 않습니다. 공개 비밀번호는 교실 시연용으로만 사용하세요.

## 동작 기준 (임시 설정)

3초마다 측정하고 10개 간격 전의 측정값과 비교합니다. 최초 11번째 유효 측정부터 판정합니다. 연속 측정 간격이 6초 이상 벌어지거나 센서 값이 유효하지 않으면 이력을 초기화합니다.

| 상태 | 조건 | 출력 |
|---|---|---|
| 상승 | 변화량 +2°C 이상 | 빨간 LED, 진입 시 1초 부저 |
| 하강 | 변화량 -2°C 이하 | 파란 LED, 진입 시 1초 부저 |
| 정상 | 경보 조건 미충족 | LED 꺼짐 |
| 준비/오류 | 이력 부족 또는 센서 읽기 실패 | LED와 부저 꺼짐 |

히스테리시스: 상승 경보는 변화량이 +1°C 이하로 돌아오면 해제, 하강은 -1°C 이상으로 돌아오면 해제합니다. 반대 방향의 경보 기준에 바로 도달하면 상태가 전환됩니다. 같은 상태가 이어지면 부저와 알림 횟수를 반복 증가시키지 않습니다. 최근 경보와 누적 횟수는 RAM에만 보관하며 재부팅 시 초기화됩니다.

웹 페이지는 연결 중에 상태를 주기적으로 조회합니다. 앱 백그라운드 푸시, 문자, 외부 인터넷 통지 기능은 포함하지 않습니다.

## 파일

- sketches/TemperatureAlert/TemperatureAlert.ino: 센서, LED, 부저, Wi-Fi, 웹 서버
- sketches/TemperatureAlert/TrendMonitor.h: 온도 변화 판단
- install-libraries.cmd: 과제 의존 라이브러리 설치
- tests/test_trend.cpp: 온도 판정 단위 테스트 (PC C++ 컴파일러용)

## 검증 방법

PC C++ 컴파일러가 있으면 이 폴더에서:

```sh
g++ -std=c++11 -Wall -Wextra -pedantic tests/test_trend.cpp -o test_trend
./test_trend
```

실물 시험: 안정 상태에서 약 33초 대기 → 센서를 손의 체온이나 온도 차이가 있는 공기로 완만히 따뜻하게/차갑게 하여 경보 확인 → 원상 복귀 확인 → DATA 연결 해제 후 오류 표시 확인(배선 변경 시 전원 차단). 물, 불꽃, 고온 열풍, 결로는 피하세요. ESP32 안전경보 인증 제품이 아닌 교육용 예제입니다.

공식 자료: [Adafruit DHT 라이브러리](https://github.com/adafruit/DHT-sensor-library), [ESP32 Wi-Fi API](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/wifi.html).
