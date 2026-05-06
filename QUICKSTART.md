# 🚀 Быстрый запуск

## Минимальные шаги для запуска:

### 1. Запустить инфраструктуру (Docker)
```bash
cd backend
docker-compose up -d
```

### 2. Запустить Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python app.py
```

### 3. Запустить Frontend (в новом терминале)
```bash
cd frontend
npm install
npm start
```

## ✅ Готово!

- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/api/docs

## 🔑 Демо аккаунты:
- `admin` / `admin123`
- `user` / `user123`






