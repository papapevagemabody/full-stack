# Лабораторная работа №6: Контейнеризация и автоматизация развертывания

## 1) Архитектура контейнеризации

### Сервисы
- `frontend` — React-приложение (Node.js, порт `3000` внутри сети Docker)
- `backend` — FastAPI (порт `8001`)
- `postgres` — PostgreSQL 15 (порт `5432`)
- `minio` — S3-совместимое хранилище (порт `9000`, console `9001`)
- `reverse-proxy` — Nginx (публичный вход, порт `80`)

### Сетевое взаимодействие
- Внешний трафик идет в `reverse-proxy:80`
- `reverse-proxy` маршрутизирует:
  - `/` -> `frontend:3000`
  - `/api/*` -> `backend:8001/*`
  - `/files/*`, `/static/*` -> `backend:8001`
- `backend` работает с `postgres` и `minio` по внутренней сети `app-net`

---

## 2) Контейнеризация компонентов

### Backend
- `backend/Dockerfile`:
  - Python 3.11 slim
  - системные зависимости для OpenCV
  - установка `requirements.txt`
  - `HEALTHCHECK` по `/health`
  - запуск через `uvicorn`

### Frontend
- `frontend/Dockerfile`:
  - Node 20 Alpine
  - `npm ci`
  - запуск `npm start` на `0.0.0.0:3000`

### Reverse proxy
- `deploy/nginx/default.conf`:
  - реверс-прокси для frontend/backend
  - endpoint `/healthz` для healthcheck прокси

### Docker ignore
- `backend/.dockerignore`
- `frontend/.dockerignore`

---

## 3) Оркестрация через Docker Compose

Файл: `docker-compose.yml` (в корне проекта)

- Запуск всех сервисов одной командой
- Настроены:
  - порты
  - сети
  - тома
  - переменные окружения
  - healthcheck
  - `depends_on` с `condition: service_healthy`

Запуск:

```bash
docker compose up -d --build
```

Проверка:

```bash
docker compose ps
docker compose logs -f reverse-proxy backend frontend postgres minio
```

---

## 4) Безопасная и управляемая конфигурация

- Конфигурация вынесена в переменные окружения:
  - `backend/.env`
  - `frontend/.env`
- Добавлены шаблоны:
  - `backend/.env.example`
  - `frontend/.env.example`
- `.gitignore` обновлен:
  - исключены `backend/.env`, `frontend/.env` и общий `.env`
  - разрешены `*.env.example`

---

## 5) CI/CD

Файл: `.github/workflows/ci-cd.yml`

Этапы:
- `backend-quality`:
  - установка зависимостей
  - `ruff check backend`
  - `pytest backend/tests/unit`
- `frontend-quality`:
  - `npm ci`
  - `eslint`
  - `npm test`
  - `npm run build`
- `docker-build`:
  - сборка образов `backend` и `frontend`
  - валидация `docker compose config`
- `deploy`:
  - авторазвертывание после успешных проверок в `main`
  - через SSH (секреты GitHub: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_PATH`)

---

## 6) Проверка итоговой конфигурации

### 6.1 Воспроизводимость
- На чистой машине достаточно:
  - Docker + Docker Compose
  - `docker compose up -d --build`

### 6.2 Работоспособность сервисов
- `http://localhost` — frontend через proxy
- `http://localhost/api/health` — backend health
- `http://localhost:9001` — MinIO console

### 6.3 Сохранение MVP и доработок
- Проверить:
  - регистрацию/логин
  - RBAC (admin/user)
  - загрузку и просмотр файлов

### 6.4 Устойчивость к типовым сбоям

1. Падение backend:
```bash
docker compose stop backend
docker compose start backend
```
Ожидание: сервис поднимается, proxy восстанавливает маршрутизацию.

2. Ошибка внешней зависимости (MinIO):
```bash
docker compose stop minio
```
Ожидание: backend доступен, file-операции возвращают корректные ошибки/503.

3. Ошибка БД:
```bash
docker compose stop postgres
```
Ожидание: health backend деградирует, запросы к БД падают контролируемо.
