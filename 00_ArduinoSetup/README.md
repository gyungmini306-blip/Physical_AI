# 공통 Arduino 개발환경 설치

Windows 10/11 x64, PowerShell 5.1 이상용. 특정 과제와 독립적으로 사용합니다.

| 도구 | 기존 설정 버전 |
|---|---|
| Arduino IDE | 2.3.10 |
| Arduino CLI | 1.5.1 |
| Espressif ESP32 Core | 3.3.12 |
| CP210x 드라이버 | Silicon Labs 제공 패키지 |

- `setup.cmd`: 설치 실행
- `setup.ps1`: 다운로드·설치 및 SetupCheck 컴파일
- `launch-ide.cmd`: IDE 실행
- `check-build.cmd`: 인수 없이 실행하면 독립적인 SetupCheck 컴파일; 스케치 폴더를 인수로 전달하면 과제 컴파일

저장소 루트의 명령 프롬프트에서 예:

```bat
00_ArduinoSetup\check-build.cmd
00_ArduinoSetup\check-build.cmd 01_SmartHomeCare\sketches\SmartHomeCare
```

도구 저장 위치: `%LOCALAPPDATA%\ESP32SchoolKit`. ESP32 Core는 Arduino15에 설치합니다. 드라이버는 관리자 승인 및 학교 정책 허용이 필요할 수 있습니다. 보드에서 GPIO에 5V 신호를 직접 입력하지 마세요.

이번 분리 작업은 소스 수준 변경이며 실제 Windows 설치·컴파일은 재검증 필요합니다. 버전과 다운로드 URL은 기존 설치기에서 유지했습니다.
