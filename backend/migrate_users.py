from auth import fake_users_db  # Старая база
from user_service import user_service

def migrate_users():
    """Мигрирует пользователей из памяти в MinIO"""
    print("🚀 Миграция пользователей в MinIO...")
    
    for username, user_data in fake_users_db.items():
        if not user_service.user_exists(username):
            try:
                user_service.create_user(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=user_data["password"]
                )
                print(f"✅ Мигрирован: {username}")
            except Exception as e:
                print(f"❌ Ошибка миграции {username}: {e}")
        else:
            print(f"⚠️ Уже существует: {username}")
    
    print("🎉 Миграция завершена!")

if __name__ == "__main__":
    migrate_users()