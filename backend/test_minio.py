# test_minio.py
from minio import Minio
from minio.error import S3Error

def test_minio_connection():
    try:
        # Подключаемся к MinIO
        client = Minio(
            "localhost:9000",
            access_key="admin",
            secret_key="password123",
            secure=False  # False для HTTP (локальная разработка)
        )
        
        print("✅ MinIO подключение успешно!")
        
        # Проверяем список bucket'ов
        buckets = client.list_buckets()
        print(f"✅ Найдено bucket'ов: {len(buckets)}")
        
        for bucket in buckets:
            print(f"   - {bucket.name} (создан: {bucket.creation_date})")
        
        # Проверяем существует ли наш bucket
        bucket_name = "user-files"
        if client.bucket_exists(bucket_name):
            print(f"✅ Bucket '{bucket_name}' существует")
        else:
            print(f"❌ Bucket '{bucket_name}' не существует")
            # Создаем bucket если его нет
            client.make_bucket(bucket_name)
            print(f"✅ Bucket '{bucket_name}' создан")
        
        # Тест загрузки файла
        test_file = "test_minio.txt"
        with open(test_file, "w") as f:
            f.write("Hello MinIO from Python!")
        
        client.fput_object(
            bucket_name, 
            "test/test_file.txt", 
            test_file
        )
        print("✅ Файл успешно загружен в MinIO")
        
        # Генерируем временную ссылку
        url = client.presigned_get_object(bucket_name, "test/test_file.txt")
        print(f"✅ Presigned URL: {url}")
        
        # Удаляем тестовый файл
        import os
        os.remove(test_file)
        
        return True
        
    except S3Error as e:
        print(f"❌ Ошибка MinIO: {e}")
        return False
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

if __name__ == "__main__":
    test_minio_connection()