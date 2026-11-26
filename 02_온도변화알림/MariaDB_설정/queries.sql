-- Read-only queries; no simulated readings are inserted.
USE temperature_alert;
SELECT VERSION();
SHOW TABLES;
DESCRIBE measurements;
SELECT * FROM measurements ORDER BY id DESC LIMIT 20;
SELECT COUNT(*) AS samples, MIN(temperature) AS minimum,
       MAX(temperature) AS maximum, AVG(temperature) AS average,
       COALESCE(SUM(alarm),0) AS alarms
FROM measurements;
SELECT * FROM measurements WHERE alarm=1 ORDER BY id DESC LIMIT 20;
