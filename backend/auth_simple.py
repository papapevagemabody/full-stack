from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import secrets

# Простая база пользователей
users_db = {
    "admin": "secret",
    "user": "secret"
}

class User(BaseModel):
    username: str

security = HTTPBasic()

def verify_user(credentials: HTTPBasicCredentials):
    correct_password = users_db.get(credentials.username)
    if not correct_password:
        return False
    if not secrets.compare_digest(credentials.password.encode('utf-8'), correct_password.encode('utf-8')):
        return False
    return User(username=credentials.username)

async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = verify_user(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user