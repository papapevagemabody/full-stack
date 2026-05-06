# database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from config import settings
from models import Base  # Импортируем Base из models

# Параметры engine в зависимости от типа БД
_connect_args = {}
_engine_kw = {"echo": bool(settings.DEBUG and getattr(settings, "APP_ENV", "") != "test")}
if "sqlite" in settings.DATABASE_URL:
    _connect_args["check_same_thread"] = False
    _engine_kw["connect_args"] = _connect_args
    if ":memory:" in settings.DATABASE_URL:
        from sqlalchemy.pool import StaticPool

        _engine_kw["poolclass"] = StaticPool
else:
    _engine_kw["pool_pre_ping"] = True

# Создаем engine
engine = create_engine(settings.DATABASE_URL, **_engine_kw)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency для FastAPI
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Context manager для использования вне FastAPI
@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для создания таблиц
def create_tables():
    """Создает все таблицы в базе данных"""
    db_type = "SQLite" if "sqlite" in settings.DATABASE_URL else "PostgreSQL"
    print(f"🔄 Создание таблиц в {db_type}...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы")

# Функция для проверки подключения
def check_connection() -> bool:
    """Проверяет подключение к БД"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False