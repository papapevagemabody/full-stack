-- init.sql
-- Инициализация базы данных

-- Создаем расширение для UUID если нужно
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Настраиваем параметры
ALTER DATABASE image_redaction_db SET timezone TO 'UTC';

-- Можно добавить комментарий
COMMENT ON DATABASE image_redaction_db IS 'Image Redaction Application Database';

-- Создаем схему если нужно (опционально)
-- CREATE SCHEMA IF NOT EXISTS app_schema;
-- SET search_path TO app_schema;