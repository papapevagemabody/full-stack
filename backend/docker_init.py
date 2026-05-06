# docker_init.py
import time
import sys
from database import create_tables, check_connection
from auth import initialize_demo_users

def wait_for_postgres(max_retries=30, delay=2):
    """Ждем пока PostgreSQL станет доступен"""
    print("🔄 Ожидание PostgreSQL...")
    for i in range(max_retries):
        if check_connection():
            print("✅ PostgreSQL доступен")
            return True
        print(f"⏳ Попытка {i+1}/{max_retries}...")
        time.sleep(delay)
    print("❌ PostgreSQL не стал доступен")
    return False

def init_database():
    print("=" * 50)
    print("🚀 Инициализация базы данных")
    print("=" * 50)
    
    # Ждем доступности PostgreSQL
    if not wait_for_postgres():
        sys.exit(1)
    
    # Создаем таблицы
    print("🔄 Создание таблиц...")
    create_tables()
    print("✅ Таблицы созданы")
    
    # Создаем демо пользователей
    print("🔄 Создание демо пользователей...")
    initialize_demo_users()
    print("✅ Демо пользователи созданы")
    
    print("=" * 50)
    print("🎉 Инициализация завершена!")
    print("=" * 50)

if __name__ == "__main__":
    init_database()