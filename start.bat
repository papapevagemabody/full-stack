@echo off
echo ========================================
echo   Запуск Full-Stack приложения
echo ========================================
echo.

REM Сохраняем корневую директорию проекта
set PROJECT_ROOT=%~dp0
cd /d %PROJECT_ROOT%

echo [1/3] Запуск Docker контейнеров (PostgreSQL + MinIO)...
cd /d %PROJECT_ROOT%backend
docker-compose up -d
if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось запустить Docker контейнеры
    echo Убедитесь, что Docker установлен и запущен
    pause
    exit /b 1
)
echo ✓ Docker контейнеры запущены
echo.

echo [2/3] Запуск Backend сервера...
cd /d %PROJECT_ROOT%backend
if not exist venv (
    echo Создание виртуального окружения...
    python -m venv venv
)
if not exist venv\Scripts\activate.bat (
    echo ОШИБКА: Виртуальное окружение не создано правильно
    pause
    exit /b 1
)
start "Backend Server" cmd /k "cd /d %PROJECT_ROOT%backend && venv\Scripts\activate && pip install -q -r requirements.txt && python app.py"
echo ✓ Backend запускается на http://localhost:8001
echo.

timeout /t 3 /nobreak >nul

echo [3/3] Запуск Frontend...
cd /d %PROJECT_ROOT%frontend
if not exist node_modules (
    echo Установка зависимостей...
    call npm install
)
start "Frontend Server" cmd /k "cd /d %PROJECT_ROOT%frontend && npm start"
echo ✓ Frontend запускается на http://localhost:3000
echo.

echo ========================================
echo   Все сервисы запускаются!
echo ========================================
echo.
echo Frontend:  http://localhost:3000
echo Backend:   http://localhost:8001
echo API Docs:  http://localhost:8001/api/docs
echo.
echo Окна с серверами открыты в отдельных окнах.
echo Закройте их для остановки серверов.
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
