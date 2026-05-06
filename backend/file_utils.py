import os
import uuid
from fastapi import UploadFile, HTTPException
from config import settings

class FileUtils:
    @staticmethod
    def validate_file(file: UploadFile) -> bool:
        if not file.filename: return False
        file_extension = os.path.splitext(file.filename)[1].lower()
        return file_extension in settings.ALLOWED_EXTENSIONS
    
    @staticmethod
    def generate_filename(original_filename: str) -> str:
        file_extension = os.path.splitext(original_filename)[1]
        return f"{uuid.uuid4()}{file_extension}"
    
    @staticmethod
    async def save_upload_file(file: UploadFile, directory: str) -> str:
        if not FileUtils.validate_file(file):
            raise HTTPException(status_code=400, detail="Неподдерживаемый формат файла")
        
        filename = FileUtils.generate_filename(file.filename)
        file_path = os.path.join(directory, filename)
        
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Файл слишком большой")
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        return filename
    
    @staticmethod
    def delete_file(filename: str, directory: str) -> bool:
        try:
            file_path = os.path.join(directory, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

file_utils = FileUtils()