# rbac_service.py
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from database import get_db_context
from models import Role, Permission, User, user_roles, role_permissions

class RBACService:
    """Сервис для управления ролями и разрешениями"""
    
    # Определяем стандартные разрешения
    PERMISSIONS = {
        # Файлы
        "files.view_own": {"resource": "files", "action": "view_own", "description": "Просмотр своих файлов"},
        "files.view_all": {"resource": "files", "action": "view_all", "description": "Просмотр всех файлов"},
        "files.upload": {"resource": "files", "action": "upload", "description": "Загрузка файлов"},
        "files.delete_own": {"resource": "files", "action": "delete_own", "description": "Удаление своих файлов"},
        "files.delete_all": {"resource": "files", "action": "delete_all", "description": "Удаление любых файлов"},
        
        # Цензурирование
        "censor.use": {"resource": "censor", "action": "use", "description": "Использование цензурирования"},
        
        # Пользователи
        "users.view": {"resource": "users", "action": "view", "description": "Просмотр списка пользователей"},
        "users.manage": {"resource": "users", "action": "manage", "description": "Управление пользователями"},
        "users.delete": {"resource": "users", "action": "delete", "description": "Удаление пользователей"},
        # Каталог пользовательских материалов (метаданные + MinIO)
        "catalog.view": {"resource": "catalog", "action": "view", "description": "Просмотр каталога своих материалов"},
        "catalog.manage": {"resource": "catalog", "action": "manage", "description": "Создание и изменение записей каталога"},
    }
    
    # Определяем стандартные роли и их разрешения
    ROLES = {
        "guest": {
            "description": "Неавторизованный пользователь",
            "permissions": []
        },
        "user": {
            "description": "Обычный пользователь",
            "permissions": [
                "files.view_own",
                "files.upload",
                "files.delete_own",
                "censor.use",
                "catalog.view",
                "catalog.manage",
            ]
        },
        "admin": {
            "description": "Администратор",
            "permissions": [
                "files.view_own",
                "files.view_all",
                "files.upload",
                "files.delete_own",
                "files.delete_all",
                "censor.use",
                "users.view",
                "users.manage",
                "users.delete",
                "catalog.view",
                "catalog.manage",
            ]
        }
    }
    
    def __init__(self):
        print("✅ RBACService initialized")
    
    def initialize_permissions(self):
        """Инициализирует все разрешения в базе данных"""
        with get_db_context() as db:
            for perm_name, perm_data in self.PERMISSIONS.items():
                existing = db.query(Permission).filter(Permission.name == perm_name).first()
                if not existing:
                    permission = Permission(
                        name=perm_name,
                        description=perm_data["description"],
                        resource=perm_data["resource"],
                        action=perm_data["action"]
                    )
                    db.add(permission)
                    print(f"✅ Permission created: {perm_name}")
            db.commit()
    
    def initialize_roles(self):
        """Инициализирует все роли и их разрешения в базе данных"""
        with get_db_context() as db:
            # Сначала создаем разрешения
            self.initialize_permissions()
            
            for role_name, role_data in self.ROLES.items():
                # Создаем или получаем роль
                role = db.query(Role).filter(Role.name == role_name).first()
                if not role:
                    role = Role(
                        name=role_name,
                        description=role_data["description"]
                    )
                    db.add(role)
                    db.flush()  # Получаем ID роли
                    print(f"✅ Role created: {role_name}")
                
                # Добавляем разрешения к роли
                for perm_name in role_data["permissions"]:
                    permission = db.query(Permission).filter(Permission.name == perm_name).first()
                    if permission and permission not in role.permissions:
                        role.permissions.append(permission)
                        print(f"✅ Permission {perm_name} added to role {role_name}")
            
            db.commit()
    
    def assign_role_to_user(self, username: str, role_name: str) -> bool:
        """Назначает роль пользователю"""
        with get_db_context() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                print(f"❌ User not found: {username}")
                return False
            
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                print(f"❌ Role not found: {role_name}")
                return False
            
            if role not in user.roles:
                user.roles.append(role)
                db.commit()
                print(f"✅ Role {role_name} assigned to user {username}")
                return True
            else:
                print(f"⚠️ User {username} already has role {role_name}")
                return False
    
    def remove_role_from_user(self, username: str, role_name: str) -> bool:
        """Удаляет роль у пользователя"""
        with get_db_context() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return False
            
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                return False
            
            if role in user.roles:
                user.roles.remove(role)
                db.commit()
                print(f"✅ Role {role_name} removed from user {username}")
                return True
            return False
    
    def get_user_roles(self, username: str) -> List[str]:
        """Получает список ролей пользователя"""
        with get_db_context() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return []
            return [role.name for role in user.roles]
    
    def get_user_permissions(self, username: str) -> List[str]:
        """Получает список разрешений пользователя"""
        with get_db_context() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return []
            
            # Администратор имеет все права
            if user.is_admin:
                return list(self.PERMISSIONS.keys())
            
            permissions = set()
            for role in user.roles:
                for perm in role.permissions:
                    permissions.add(perm.name)
            return list(permissions)
    
    def user_has_permission(self, username: str, permission_name: str) -> bool:
        """Проверяет, имеет ли пользователь указанное разрешение"""
        with get_db_context() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return False
            
            # Администратор имеет все права
            if user.is_admin:
                return True
            
            for role in user.roles:
                if any(perm.name == permission_name for perm in role.permissions):
                    return True
            return False
    
    def user_has_role(self, username: str, role_name: str) -> bool:
        """Проверяет, имеет ли пользователь указанную роль"""
        with get_db_context() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return False
            
            # is_admin считается как роль admin
            if role_name == "admin" and user.is_admin:
                return True
            
            return any(role.name == role_name for role in user.roles)
    
    def get_all_roles(self) -> List[Dict]:
        """Получает все роли"""
        with get_db_context() as db:
            roles = db.query(Role).all()
            return [role.to_dict() for role in roles]
    
    def get_all_permissions(self) -> List[Dict]:
        """Получает все разрешения"""
        with get_db_context() as db:
            permissions = db.query(Permission).all()
            return [perm.to_dict() for perm in permissions]
    
    def get_users_with_role(self, role_name: str) -> List[Dict]:
        """Получает всех пользователей с указанной ролью"""
        with get_db_context() as db:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                return []
            
            users = []
            for user in role.users:
                users.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active
                })
            return users

# Создаем экземпляр сервиса
rbac_service = RBACService()

