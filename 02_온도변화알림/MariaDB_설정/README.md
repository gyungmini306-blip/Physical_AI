# MariaDB 설정 (Windows 직접 실행)

Docker/WSL은 필요 없습니다. 먼저 00번의 setup.cmd를 실행해 공통 Arduino/Python/MariaDB 환경을 설치합니다.

1. ../관리도구/setup-db.cmd: MariaDB 초기화, 실행, DB 및 계정/테이블 생성.
2. ../관리도구/check-db.cmd: 실제 연결 및 테이블 조회 확인.
3. ../관리도구/connect-db.cmd: SQL 콘솔 (credentials.json의 app_password 입력).
4. ../관리도구/stop-db.cmd: DB 종료, 데이터 유지.
평소에는 상위 폴더 start-server.cmd만 실행하면 DB 시작, COM 포트 감지, USB 데이터 저장, PC 웹 화면 열기가 자동으로 진행됩니다. 위 개별 CMD는 관리 및 진단용입니다.

| 항목 | 값 |
|---|---|
| 호스트 | 127.0.0.1 |
| 포트 | 3307 |
| DB | temperature_alert |
| 사용자 | temperature_app |
| 비밀번호 | %LOCALAPPDATA%/ESP32SchoolKit/temperature-mariadb/credentials.json의 app_password |

MariaDB 11.4.14 Windows ZIP 배포판 사용. 데이터 및 비밀번호는 %LOCALAPPDATA%/ESP32SchoolKit/temperature-mariadb/ 아래에 저장됩니다. 학교 PC가 초기화되면 별도로 백업해야 합니다. 비밀번호 파일은 공유/업로드하지 마세요. 서버는 로컬에서만 수신합니다. 포트가 이미 사용 중이면 중단합니다. 기존 Docker 데이터와 SQLite 데이터는 자동 이전하지 않습니다.

compose.yaml 및 setup-docker.ps1은 이전 Docker 방식의 참고용입니다. 기본 실행 경로는 네이티브입니다. Windows 직접 실행과 실제 센서 연동은 아직 검증하지 않았습니다.

공식 문서: https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/installing-mariadb/binary-packages/installing-mariadb-windows-zip-packages

## 실제 DB 검증

관리도구/setup-db.cmd 이후 관리도구/test-db.cmd를 실행하면 실제 INSERT, SELECT, ROLLBACK을 확인합니다. 테스트 행은 남기지 않습니다. start-server.cmd는 PC 브라우저를 자동으로 엽니다.
