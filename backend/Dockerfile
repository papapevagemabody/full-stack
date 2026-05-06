FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для OpenCV и других библиотек
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    libgl1 \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем необходимые директории
RUN mkdir -p uploads static

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]