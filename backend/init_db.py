# init_db.py
from database import create_tables, check_connection
from auth import initialize_demo_users

def init_database():
    print("🔄 Инициализация базы данных PostgreSQL...")
    
    # Создаем таблицы
    create_tables()
    print("✅ Таблицы созданы")
    
    # Проверяем подключение
    if check_connection():
        print("✅ Подключение к PostgreSQL успешно")
    else:
        print("❌ Не удалось подключиться к PostgreSQL")
        return
    
    # Создаем демо пользователей
    print("🔄 Создание демо пользователей...")
    initialize_demo_users()

if __name__ == "__main__":
    init_database()