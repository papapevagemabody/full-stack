# user_service.py
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from database import get_db_context
from models import User
from rbac_service import rbac_service
import secrets
import string
from datetime import datetime

class UserService:
    def __init__(self):
        print(f"✅ UserService initialized with PostgreSQL")
    
    def user_exists(self, username: str) -> bool:
        """Проверяет существование пользователя"""
        with get_db_context() as db:
            user = db.query(User).filter(User.username == username).first()
            exists = user is not None
            print(f"{'✅' if exists else '❌'} User exists in PostgreSQL: {username}")
            return exists

    def create_user(self, username: str, email: str, password_hash: str) -> Dict:
        """Создает нового пользователя"""
        print(f"🔄 Creating user in PostgreSQL: {username}")
        
        if self.user_exists(username):
            raise ValueError(f"User {username} already exists")
        
        with get_db_context() as db:
            # Генерируем MinIO credentials
            minio_access_key = f"user-{username}"
            minio_secret_key = self._generate_secret_key()
            
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                minio_access_key=minio_access_key,
                minio_secret_key=minio_secret_key,
                minio_folder=username,
                is_active=True,
                is_admin=(username == "admin")
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Назначаем роль "user" новым пользователям (если не admin)
            if not user.is_admin:
                try:
                    rbac_service.assign_role_to_user(username, "user")
                except Exception as e:
                    print(f"⚠️ Failed to assign role to user {username}: {e}")
            
            print(f"✅ User successfully created in PostgreSQL: {username}")
            return user.to_dict()

    def get_user(self, username: str) -> Optional[Dict]:
        """Получает пользователя по имени"""
        print(f"🔄 Getting user from PostgreSQL: {username}")
        with get_db_context() as db:
            user = db.query(User).filter(User.username == username).first()
            if user:
                # Явно загружаем роли
                user_dict = user.to_dict()
                # Получаем роли через rbac_service для гарантии актуальности
                roles = rbac_service.get_user_roles(username)
                user_dict["roles"] = roles
                print(f"✅ User retrieved successfully: {username} with roles: {roles}")
                return user_dict
            else:
                print(f"❌ User not found: {username}")
                return None

    def get_all_users(self) -> List[Dict]:
        """Получает всех пользователей"""
        with get_db_context() as db:
            users = db.query(User).all()
            result = []
            for user in users:
                user_dict = user.to_dict()
                # Добавляем роли для каждого пользователя
                roles = rbac_service.get_user_roles(user.username)
                user_dict["roles"] = roles
                result.append(user_dict)
            return result

    def update_user(self, username: str, update_data: Dict) -> Optional[Dict]:
        """Обновляет данные пользователя"""
        with get_db_context() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return None
            
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            db.commit()
            db.refresh(user)
            return user.to_dict()

    def delete_user(self, username: str) -> bool:
        """Удаляет пользователя"""
        with get_db_context() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return False
            
            db.delete(user)
            db.commit()
            return True

    def health_check(self) -> bool:
        """Проверяет подключение к PostgreSQL"""
        from database import check_connection
        return check_connection()

    def _generate_secret_key(self, length=32):
        """Генерирует безопасный секретный ключ"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def authenticate_user(self, username: str, password_hash: str) -> Optional[Dict]:
        """Аутентификация пользователя"""
        with get_db_context() as db:
            user = db.query(User).filter(
                User.username == username,
                User.password_hash == password_hash,
                User.is_active == True
            ).first()
            
            if user:
                return user.to_dict()
            return None

# Создаем экземпляр сервиса
user_service = UserService()