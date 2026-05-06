#!/bin/bash

echo "========================================"
echo "  Запуск Full-Stack приложения"
echo "========================================"
echo ""

echo "[1/3] Запуск Docker контейнеров (PostgreSQL + MinIO)..."
cd backend
docker-compose up -d
if [ $? -ne 0 ]; then
    echo "ОШИБКА: Не удалось запустить Docker контейнеры"
    echo "Убедитесь, что Docker установлен и запущен"
    exit 1
fi
echo "✓ Docker контейнеры запущены"
echo ""

echo "[2/3] Запуск Backend сервера..."
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
python app.py &
BACKEND_PID=$!
echo "✓ Backend запущен на http://localhost:8001 (PID: $BACKEND_PID)"
echo ""

sleep 3

echo "[3/3] Запуск Frontend..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "Установка зависимостей..."
    npm install
fi
npm start &
FRONTEND_PID=$!
echo "✓ Frontend запущен на http://localhost:3000 (PID: $FRONTEND_PID)"
echo ""

echo "========================================"
echo "  Все сервисы запущены!"
echo "========================================"
echo ""
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:8001"
echo "API Docs:  http://localhost:8001/api/docs"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

# Ожидание прерывания
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait






