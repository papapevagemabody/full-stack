# models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Таблица связи многие-ко-многим для User и Role
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# Таблица связи многие-ко-многим для Role и Permission
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Оставляем для обратной совместимости
    
    # MinIO related fields (for file storage)
    minio_access_key = Column(String(100), nullable=True)
    minio_secret_key = Column(String(255), nullable=True)
    minio_bucket = Column(String(100), default="user-files")
    minio_folder = Column(String(100), nullable=True)
    
    # Связь с ролями
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    refresh_sessions = relationship("RefreshSession", back_populates="user", cascade="all, delete-orphan")
    user_assets = relationship("UserAsset", back_populates="owner", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "minio_access_key": self.minio_access_key,
            "minio_bucket": self.minio_bucket,
            "minio_folder": self.minio_folder,
            "roles": [role.name for role in self.roles] if self.roles else []
        }
    
    def has_role(self, role_name: str) -> bool:
        """Проверяет, имеет ли пользователь указанную роль"""
        return any(role.name == role_name for role in self.roles) or self.is_admin
    
    def has_permission(self, permission_name: str) -> bool:
        """Проверяет, имеет ли пользователь указанное разрешение"""
        if self.is_admin:
            return True  # Администратор имеет все права
        for role in self.roles:
            if any(perm.name == permission_name for perm in role.permissions):
                return True
        return False

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "permissions": [perm.name for perm in self.permissions] if self.permissions else []
        }

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    resource = Column(String(50), nullable=False)  # files, users, censor, etc.
    action = Column(String(50), nullable=False)  # view, create, delete, manage, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с ролями
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "resource": self.resource,
            "action": self.action,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RefreshSession(Base):
    """Серверное хранение refresh-токенов (хеш) с семейством для ротации и отзыва при reuse."""
    __tablename__ = "refresh_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    family_id = Column(String(36), nullable=False, index=True)
    revoked = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="refresh_sessions")


class UserAsset(Base):
    """Метаданные пользовательского файла в объектном хранилище (MinIO)."""
    __tablename__ = "user_assets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=True)
    category = Column(String(50), nullable=False, index=True, default="general")
    object_name = Column(String(512), unique=True, nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(120), nullable=True)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="user_assets")