# 관리도구 (필요할 때만 실행)

일상 실행: 상위 폴더의 start-server.cmd 한 개만 실행합니다.

| 파일 | 용도 |
|---|---|
| connect-db.cmd | SQL 콘솔 접속 |
| check-db.cmd | DB 연결 확인 |
| test-db.cmd | DB 저장·조회·롤백 검사 |
| setup-db.cmd | DB만 시작 / 초기화 |
| stop-db.cmd | DB 종료 (먼저 start-server.cmd 종료) |
| install-libraries.cmd | DHT 라이브러리 재설치 |
| setup-server.cmd | Python 의존성 확인 |

manage-db.py는 위 DB 관리 명령을 기존 MariaDB_설정/native_db.py로 연결합니다. 직접 실행할 필요 없습니다. 데이터와 비밀번호는 기존 위치에 유지됩니다.
