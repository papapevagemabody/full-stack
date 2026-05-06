# migrate_to_postgresql.py
import json
from minio import Minio
from config import settings
from user_service import user_service
from auth import get_password_hash

def migrate_from_minio_to_postgresql():
    """Мигрирует пользователей из MinIO в PostgreSQL"""
    print("🚀 Миграция пользователей из MinIO в PostgreSQL...")
    
    # Подключаемся к MinIO для чтения старых данных
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )
    
    bucket = "user-data"
    
    try:
        # Получаем всех пользователей из MinIO
        objects = minio_client.list_objects(bucket, prefix="users/", recursive=True)
        
        migrated_count = 0
        skipped_count = 0
        
        for obj in objects:
            if obj.object_name.endswith('.json'):
                try:
                    # Читаем данные пользователя из MinIO
                    response = minio_client.get_object(bucket, obj.object_name)
                    user_data = json.loads(response.read().decode('utf-8'))
                    response.close()
                    response.release_conn()
                    
                    username = user_data["username"]
                    
                    # Проверяем, существует ли уже в PostgreSQL
                    if not user_service.user_exists(username):
                        # Создаем пользователя в PostgreSQL
                        user_service.create_user(
                            username=user_data["username"],
                            email=user_data["email"],
                            password_hash=user_data["password_hash"]
                        )
                        print(f"✅ Мигрирован: {username}")
                        migrated_count += 1
                    else:
                        print(f"⚠️ Уже существует в PostgreSQL: {username}")
                        skipped_count += 1
                        
                except Exception as e:
                    print(f"❌ Ошибка при миграции {obj.object_name}: {e}")
        
        print(f"\n🎉 Миграция завершена!")
        print(f"   Успешно мигрировано: {migrated_count}")
        print(f"   Пропущено (уже существует): {skipped_count}")
        
    except Exception as e:
        print(f"❌ Ошибка при подключении к MinIO: {e}")

if __name__ == "__main__":
    migrate_from_minio_to_postgresql()