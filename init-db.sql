-- init-db.sql
-- Создаем расширение для UUID если нужно
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Можно добавить дополнительные настройки
ALTER DATABASE image_redaction_db SET timezone TO 'UTC';