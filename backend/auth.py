# auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError  # Исправлено!
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import hashlib

from schemas import User
from user_service import user_service
from rbac_service import rbac_service
from config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль"""
    try:
        result = hash_password(plain_password) == hashed_password
        return result
    except Exception as e:
        print(f"❌ VERIFY ERROR: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Хеширует пароль"""
    if len(password) > 72:
        password = password[:72]
    return hash_password(password)

def hash_password(password: str) -> str:
    """Простое хеширование SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

# JWT конфигурация (секрет и TTL из настроек окружения)
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_user(username: str) -> Optional[dict]:
    """Получает пользователя из PostgreSQL"""
    return user_service.get_user(username)

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Аутентифицирует пользователя с данными из PostgreSQL"""
    print(f"🔐 AUTHENTICATION START: username={username}")
    
    user_data = get_user(username)
    if not user_data:
        print(f"❌ AUTH FAIL: User not found in PostgreSQL - {username}")
        return None
    
    stored_hash = user_data["password_hash"]
    
    password_match = verify_password(password, stored_hash)
    
    if not password_match:
        print(f"❌ AUTH FAIL: Password mismatch for {username}")
        return None
    
    print(f"🎉 AUTH SUCCESS: {username}")
    # Получаем роли пользователя
    roles = rbac_service.get_user_roles(username)
    return User(
        id=user_data.get("id"),
        username=user_data["username"],
        email=user_data["email"],
        created_at=user_data.get("created_at"),
        is_active=user_data.get("is_active", True),
        is_admin=user_data.get("is_admin", False),
        minio_bucket=user_data.get("minio_bucket"),
        minio_folder=user_data.get("minio_folder"),
        roles=roles
    )

def create_user(username: str, email: str, password: str) -> User:
    """Создает нового пользователя в PostgreSQL"""
    print(f"🔄 Starting user creation: {username}")
    
    # Проверяем существование пользователя
    if user_service.user_exists(username):
        print(f"❌ User already exists: {username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Валидация
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    if len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters"
        )
    
    # Хешируем пароль
    hashed_password = get_password_hash(password)
    print(f"🔑 Password hashed for: {username}")
    
    # Создаем пользователя в PostgreSQL
    try:
        user_data = user_service.create_user(username, email, hashed_password)
        
        # Проверяем, что пользователь действительно создан
        if not user_service.user_exists(username):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User creation failed - user not found after creation"
            )
        
        print(f"✅ User fully registered in PostgreSQL: {username}")
        # Получаем роли пользователя
        roles = rbac_service.get_user_roles(username)
        return User(
            id=user_data.get("id"),
            username=username,
            email=email,
            created_at=user_data.get("created_at"),
            is_active=user_data.get("is_active", True),
            is_admin=user_data.get("is_admin", False),
            minio_bucket=user_data.get("minio_bucket"),
            minio_folder=user_data.get("minio_folder"),
            roles=roles
        )
        
    except ValueError as e:
        print(f"❌ ValueError in user creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"❌ Unexpected error in user creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT токен"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Получает текущего пользователя из JWT токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception
    
    user_data = get_user(username=username)
    if user_data is None:
        raise credentials_exception
    
    # Получаем роли пользователя
    roles = rbac_service.get_user_roles(username)
    
    return User(
        id=user_data.get("id"),
        username=user_data["username"],
        email=user_data["email"],
        created_at=user_data.get("created_at"),
        is_active=user_data.get("is_active", True),
        is_admin=user_data.get("is_admin", False),
        minio_bucket=user_data.get("minio_bucket"),
        minio_folder=user_data.get("minio_folder"),
        roles=roles
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Функции для проверки прав доступа
def require_permission(permission_name: str):
    """Dependency для проверки разрешения у пользователя"""
    async def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        has_permission = rbac_service.user_has_permission(current_user.username, permission_name)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_name}"
            )
        return current_user
    return permission_checker

def require_role(role_name: str):
    """Dependency для проверки роли у пользователя"""
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        has_role = rbac_service.user_has_role(current_user.username, role_name)
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role_name}"
            )
        return current_user
    return role_checker

def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency для проверки, что пользователь является администратором"""
    if not current_user.is_admin and not rbac_service.user_has_role(current_user.username, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Функция для инициализации демо пользователей при первом запуске
def initialize_demo_users():
    """Создает демо пользователей если их нет в системе"""
    # Сначала инициализируем роли и разрешения
    try:
        rbac_service.initialize_roles()
        print("✅ Roles and permissions initialized")
    except Exception as e:
        print(f"⚠️ Failed to initialize roles: {e}")
    
    demo_users = [
        {"username": "admin", "email": "admin@example.com", "password": "secret123", "is_admin": True, "role": "admin"},
        {"username": "user", "email": "user@example.com", "password": "secret123", "is_admin": False, "role": "user"},
    ]
    
    for user_data in demo_users:
        if not user_service.user_exists(user_data["username"]):
            try:
                hashed_password = get_password_hash(user_data["password"])
                user_service.create_user(
                    user_data["username"],
                    user_data["email"],
                    hashed_password
                )
                # Назначаем роль
                if "role" in user_data:
                    rbac_service.assign_role_to_user(user_data["username"], user_data["role"])
                print(f"✅ Demo user created: {user_data['username']}")
            except Exception as e:
                print(f"❌ Failed to create demo user {user_data['username']}: {e}")
        else:
            # Убеждаемся, что у существующих пользователей есть роли
            if "role" in user_data:
                try:
                    rbac_service.assign_role_to_user(user_data["username"], user_data["role"])
                except Exception:
                    pass
            print(f"✅ Demo user already exists: {user_data['username']}")

# Инициализируем демо пользователей при импорте
#print("🔄 Initializing demo users...")
#initialize_demo_users()
#print("✅ Auth module initialized")
print("✅ Auth module loaded")