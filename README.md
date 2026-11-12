# Physical_AI — ESP32 Smart Home Care

학교 PC가 부팅 시 초기화되는 환경을 위한 ESP32 개발환경 자동 설치 프로젝트입니다.

## 학교에서 사용하기

1. 이 저장소에서 **Code → Download ZIP**을 눌러 내려받고 압축을 풉니다.
2. `esp32-school-setup/setup.cmd`를 더블클릭합니다.
3. 인터넷 연결 상태에서 Arduino IDE 2.3.10, Arduino CLI 1.5.1, Espressif ESP32 Core 3.3.12를 사용자 계정 영역에 구성합니다.
4. CP210x 드라이버 설치는 **관리자 권한 및 학교 PC 정책 허용이 필요**합니다. 설치가 막히면 학교 전산실에 문의해야 합니다.
5. Arduino IDE에서 **ESP32 Dev Module**과 **실제 CP210x COM 포트**를 선택합니다. `COM1`은 실제 보드 포트인지 확인하기 전에는 선택하지 마세요.

실행: `esp32-school-setup/setup.cmd`  
코드: `esp32-school-setup/sketches/SmartHomeCare/SmartHomeCare.ino`  
확인용 컴파일: `esp32-school-setup/check-build.cmd`

## 목적과 한계

- Windows 10/11 x64 및 PowerShell 5.1 이상 환경을 대상으로 합니다.
- 매번 초기화되는 학교 PC에서는 매회 재설치 및 다운로드가 필요할 수 있습니다. 학교 인터넷/권한 제한에 따라 실패할 수 있습니다.
- **Docker 설치는 필요하지 않습니다.** Arduino IDE/CLI는 PC에서 실행하고, ESP32에 직접 업로드합니다.
- 프로그램은 PIR(GPIO25), IR(GPIO26), 녹색 LED(GPIO18), 노란색 LED(GPIO19)의 센서 신호를 표시하는 실습 예제이며, 실제 안전 경보 장치로 사용하지 마세요.
- GPIO에 5V 신호를 직접 인가하지 마세요. CP210x USB 드라이버는 Windows용이며 USB 2.0 드라이버와 별개입니다.

자세한 절차는 [`esp32-school-setup/README.md`](esp32-school-setup/README.md)에 있습니다.
