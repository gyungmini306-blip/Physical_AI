# MariaDB 설정 (Windows 직접 실행)

과제 상위 start-server.cmd 하나로 환경 설치, DB 시작, USB 수신, 웹 화면 실행을 처리합니다. Docker/WSL 불필요.

CMD 명령 프롬프트에서 같은 실행 파일에 옵션을 추가할 수 있습니다.

| 명령 | 용도 |
|---|---|
| start-server.cmd | 실시간 모니터링 |
| start-server.cmd --history | 기존 기록만 조회 |
| start-server.cmd --db start | DB 시작 |
| start-server.cmd --db check | DB 연결 확인 |
| start-server.cmd --db console | SQL 콘솔 (app_password 입력) |
| start-server.cmd --db selftest | 실제 INSERT/SELECT/ROLLBACK 테스트 |
| start-server.cmd --db stop | DB 종료 (웹 서버부터 종료) |
| start-server.cmd --menu | 관리 메뉴 |

호스트 127.0.0.1, 포트 3307, DB temperature_alert, 사용자 temperature_app. MariaDB 11.4.14 ZIP 배포판. 데이터와 비밀번호는 %LOCALAPPDATA%/ESP32SchoolKit/temperature-mariadb/ 아래 기존 위치 그대로 유지합니다. credentials.json은 공유하지 마세요. 기존 SQLite 및 Docker DB의 자동 마이그레이션은 없습니다. SQL 예제는 queries.sql 참고. 실제 센서 동작과 변경된 원클릭 Windows 실행은 별도 확인 필요.
