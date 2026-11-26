# MariaDB 설정

02번 온도변화알림 과제의 MariaDB 개발환경입니다. 현재 단계는 **DB 서버 및 테이블 준비**입니다. 기존 Flask 서버는 아직 SQLite를 사용하며, MariaDB에 ESP32 데이터가 자동 저장되지는 않습니다.

## Docker 방식 (권장)

1. Windows에서 Docker Desktop을 실행합니다. Linux 컨테이너와 Compose v2가 필요합니다.
2. 이 폴더의 setup-db.cmd를 실행합니다. 최초 실행 시 로컬 .env에 임의 비밀번호를 생성하고 MariaDB 11.4 컨테이너와 테이블을 준비합니다. 인터넷 연결 필요.
3. connect-db.cmd를 실행한 뒤 .env의 MARIADB_PASSWORD 값을 입력합니다. 화면에 비밀번호가 보이지 않는 것은 정상입니다.
4. SQL에서 SHOW TABLES; 와 DESCRIBE measurements; 를 실행합니다.

| 설정 | 값 |
|---|---|
| 호스트 | 127.0.0.1 |
| 포트 | 3307 (컨테이너 내부 3306) |
| 데이터베이스 | temperature_alert |
| 일반 계정 | temperature_app |
| 비밀번호 | .env의 MARIADB_PASSWORD |

포트 3307은 기존 MySQL/MariaDB 기본 포트 3306과 충돌을 줄이기 위한 선택입니다. 3307도 이미 사용 중이면 compose.yaml의 호스트 포트를 변경합니다. 외부 접속을 위해 포트를 공개하지 않습니다.

## 관리 파일

- setup-db.cmd: 최초 설정 또는 재시작
- connect-db.cmd: MariaDB SQL 콘솔 (일반 계정)
- check-db.cmd: 상태 확인
- stop-db.cmd: DB 정지 (데이터 유지)
- compose.yaml: 컨테이너 설정
- init/01-schema.sql: 테이블 초기화 (빈 볼륨 최초 구동 때 실행)
- queries.sql: 조회 SQL 예제

데이터는 Docker named volume에 저장됩니다. 컨테이너 정지/재시작 시 유지되지만 볼륨 삭제, Docker 초기화, 학교 PC 초기화 시 소실될 수 있습니다. .env 파일은 Git에 올리지 않습니다. 기존 볼륨이 있다면 .env의 비밀번호를 임의로 재생성해도 DB 계정 암호는 변경되지 않습니다.

## Docker가 없는 Windows PC

공식 Windows MSI 설치 프로그램: https://mariadb.com/downloads/

MariaDB 11.4 계열을 선택하고, 설치 시 root 비밀번호를 직접 지정합니다. 관리자 권한 및 학교 PC 정책 확인이 필요합니다. MariaDB Client에서 root로 로그인하고 다음 SQL을 실행합니다. 아래 비밀번호 문자열은 직접 생성한 강한 비밀번호로 바꿉니다.

```sql
CREATE DATABASE IF NOT EXISTS temperature_alert CHARACTER SET utf8mb4;
CREATE USER 'temperature_app'@'localhost' IDENTIFIED BY 'REPLACE_WITH_STRONG_PASSWORD';
GRANT SELECT, INSERT ON temperature_alert.* TO 'temperature_app'@'localhost';
```

MariaDB Client에서 init/01-schema.sql의 내용을 실행합니다. Windows 직접 설치의 기본 포트는 3306이며 Docker 방식과 다를 수 있습니다. 외부 네트워크에서 접근할 필요는 없습니다.

## 검증 및 다음 단계

DB 설치 후 실제 SQL 접속 및 테이블 존재 여부를 확인합니다. 이 저장소 변경에서 Windows/Docker 실물 실행은 수행하지 않았습니다. 다음 단계에서 Flask의 SQLite 저장 모듈을 MariaDB 연결 방식으로 교체하거나 선택 가능하게 확장합니다. 기존 SQLite 파일은 변경하지 않습니다.

공식 문서: https://mariadb.com/docs/server/server-management/automated-mariadb-deployment-and-administration/docker-and-mariadb/
