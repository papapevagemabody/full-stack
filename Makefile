.PHONY: help build up down logs restart clean init-db migrate

help:
	@echo "Доступные команды:"
	@echo "  make build     - Собрать Docker образы"
	@echo "  make up        - Запустить все контейнеры"
	@echo "  make down      - Остановить все контейнеры"
	@echo "  make logs      - Показать логи контейнеров"
	@echo "  make restart   - Перезапустить контейнеры"
	@echo "  make clean     - Остановить и удалить контейнеры и volumes"
	@echo "  make init-db   - Инициализировать базу данных"
	@echo "  make migrate   - Мигрировать данные из MinIO в PostgreSQL"

build:
	docker-compose build --no-cache

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

clean:
	docker-compose down -v
	docker system prune -f

init-db:
	docker-compose exec app python docker_init.py

migrate:
	docker-compose exec app python migrate_to_postgresql.py

ps:
	docker-compose ps

shell:
	docker-compose exec app bash

db-shell:
	docker-compose exec postgres psql -U postgres -d image_redaction_db

minio-console:
	@echo "MinIO Console: http://localhost:9001"
	@echo "Login: admin"
	@echo "Password: password123"

pgadmin:
	@echo "pgAdmin: http://localhost:5050"
	@echo "Login: admin@admin.com"
	@echo "Password: admin123"
	@echo ""
	@echo "Для подключения к PostgreSQL:"
	@echo "Host: postgres"
	@echo "Port: 5432"
	@echo "Database: image_redaction_db"
	@echo "Username: postgres"
	@echo "Password: password123"