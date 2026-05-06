# Full-Stack Image Redaction Application

Приложение для обнаружения и цензурирования лиц на изображениях с использованием нейронной модели.

## 🚀 Быстрый старт

### Вариант 1: Запуск через Docker (Рекомендуется)

Самый простой способ запустить весь проект:

#### 1. Запуск инфраструктуры (PostgreSQL + MinIO)

```bash
cd backend
docker-compose up -d
```

Это запустит:
- **PostgreSQL** на порту `5432`
- **MinIO** на портах `9000` (API) и `9001` (Console)
- **pgAdmin** на порту `5050` (опционально)

#### 2. Установка зависимостей Backend

```bash
cd backend

# Создайте виртуальное окружение (если еще не создано)
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

#### 3. Настройка переменных окружения для локального запуска

Если запускаете backend локально (не в Docker), создайте файл `.env` в папке `backend`:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=image_redaction_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password123

MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password123
MINIO_SECURE=false
MINIO_BUCKET=user-files
```

#### 4. Запуск Backend

```bash
cd backend
python app.py
```

Backend будет доступен на `http://localhost:8001`

API документация: `http://localhost:8001/api/docs`

#### 5. Установка зависимостей Frontend

```bash
cd frontend
npm install
```

#### 6. Запуск Frontend

```bash
cd frontend
npm start
```

Frontend будет доступен на `http://localhost:3000`

---

### Вариант 2: Полный запуск через Docker

Если хотите запустить все через Docker (включая backend):

```bash
cd backend
make up
# или
docker-compose up -d
```

Backend будет запущен в контейнере.

---

## 📋 Полезные команды

### Docker команды (из папки backend)

```bash
# Показать статус контейнеров
make ps
# или
docker-compose ps

# Показать логи
make logs
# или
docker-compose logs -f

# Остановить контейнеры
make down
# или
docker-compose down

# Перезапустить
make restart
# или
docker-compose restart

# Остановить и удалить все (включая volumes)
make clean
```

### Работа с базой данных

```bash
# Подключиться к PostgreSQL через psql
make db-shell
# или
docker-compose exec postgres psql -U postgres -d image_redaction_db

# Инициализировать базу данных
make init-db
```

---

## 🔗 Доступ к сервисам

После запуска доступны:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Документация**: http://localhost:8001/api/docs
- **MinIO Console**: http://localhost:9001
  - Логин: `admin`
  - Пароль: `password123`
- **pgAdmin**: http://localhost:5050
  - Email: `admin@admin.com`
  - Пароль: `admin123`

### Подключение к PostgreSQL через pgAdmin:

1. Откройте http://localhost:5050
2. Войдите с учетными данными выше
3. Добавьте новый сервер:
   - **Host**: `postgres` (в Docker) или `localhost` (локально)
   - **Port**: `5432`
   - **Database**: `image_redaction_db`
   - **Username**: `postgres`
   - **Password**: `password123`

---

## 🎯 Использование приложения

1. **Регистрация/Вход**:
   - Перейдите на http://localhost:3000
   - Зарегистрируйте нового пользователя или войдите

2. **Загрузка изображений**:
   - На странице `/redaction` загрузите изображения
   - Нейронная модель автоматически обнаружит лица

3. **Цензурирование**:
   - Выберите метод цензурирования (пикселизация, размытие, черные полосы)
   - Настройте параметры
   - Примените цензуру к изображению

4. **Просмотр результатов**:
   - Просматривайте обработанные изображения
   - Скачивайте результаты

---

## 🛠️ Технологии

### Backend:
- **FastAPI** - веб-фреймворк
- **PostgreSQL** - база данных
- **MinIO** - объектное хранилище
- **OpenCV** - обработка изображений
- **Haar Cascades** - обнаружение лиц (нейронная модель)

### Frontend:
- **React** + **TypeScript**
- **React Router** - маршрутизация
- **Tailwind CSS** - стилизация

---

## 📝 Структура проекта

```
full-stack-ts/
├── backend/
│   ├── app.py              # Главный файл FastAPI приложения
│   ├── face_detection.py   # Модуль обнаружения лиц
│   ├── censorship_service.py # Сервис цензурирования
│   ├── docker-compose.yml   # Docker конфигурация
│   ├── requirements.txt     # Python зависимости
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── pages/          # Страницы приложения
│   │   ├── services/       # API сервисы
│   │   └── ...
│   ├── package.json        # Node.js зависимости
│   └── ...
└── README.md
```

---

## ⚠️ Устранение неполадок

### Backend не запускается

1. Проверьте, что PostgreSQL и MinIO запущены:
   ```bash
   docker-compose ps
   ```

2. Проверьте логи:
   ```bash
   docker-compose logs app
   ```

3. Убедитесь, что порты свободны:
   - `5432` - PostgreSQL
   - `9000`, `9001` - MinIO
   - `8001` - Backend

### Frontend не подключается к Backend

1. Убедитесь, что backend запущен на `http://localhost:8001`
2. Проверьте CORS настройки в `backend/config.py`
3. Проверьте, что в `frontend/src/services/api.ts` правильный `baseUrl`

### Проблемы с обнаружением лиц

1. Убедитесь, что OpenCV установлен: `pip install opencv-python`
2. Проверьте, что каскады загружены (они скачиваются автоматически)
3. Проверьте логи backend для ошибок

---

## 🔐 Демо пользователи

При первом запуске создаются демо пользователи:
- `admin` / `admin123`
- `user` / `user123`

---

## 📚 Дополнительная информация

- API документация доступна по адресу: http://localhost:8001/api/docs
- ReDoc документация: http://localhost:8001/api/redoc

---

## 🎉 Готово!

Теперь вы можете использовать приложение для обнаружения и цензурирования лиц на изображениях!
