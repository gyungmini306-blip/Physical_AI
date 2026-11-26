-- MariaDB temperature measurements. Times are UTC.
USE temperature_alert;

CREATE TABLE IF NOT EXISTS measurements (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    received_at DATETIME(3) NOT NULL DEFAULT UTC_TIMESTAMP(3),
    boot CHAR(16) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    seq INT UNSIGNED NOT NULL,
    uptime_ms INT UNSIGNED NOT NULL,
    temperature DOUBLE NULL,
    delta DOUBLE NULL,
    state ENUM('WARMING_UP','STABLE','RISING','FALLING','SENSOR_ERROR') NOT NULL,
    alarm TINYINT UNSIGNED NOT NULL DEFAULT 0,
    CONSTRAINT chk_alarm CHECK (alarm IN (0, 1)),
    CONSTRAINT chk_seq CHECK (seq > 0),
    UNIQUE KEY uq_boot_seq (boot, seq),
    KEY idx_received (received_at),
    KEY idx_alarm (alarm, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
