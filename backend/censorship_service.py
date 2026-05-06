# censorship_service.py
import cv2
import numpy as np
import os
from typing import Optional, Tuple
from face_detection import face_detector

class CensorshipService:
    def __init__(self):
        print("✅ Censorship Service инициализирован")
    
    def pixelate_face(self, image_path: str, pixel_size: int = 15) -> Optional[str]:
        """
        Пикселизация лиц на изображении
        Возвращает путь к обработанному файлу
        """
        try:
            return face_detector.censor_faces_pixelate(image_path, pixel_size)
        except Exception as e:
            print(f"❌ Ошибка в цензурировании: {e}")
            return None
    
    def blur_faces(self, image_path: str, blur_strength: int = 31) -> Optional[str]:

        try:
            # Читаем изображение
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # Обнаруживаем лица
            detections = face_detector.detect_faces(image_path)
            
            if not detections:
                return None
            
            # Получаем размеры
            height, width = image.shape[:2]
            
            # Применяем размытие к каждому лицу
            for detection in detections:
                x_rel, y_rel, w_rel, h_rel = detection.bbox
                
                # Конвертируем в абсолютные координаты
                x = int(x_rel * width)
                y = int(y_rel * height)
                w = int(w_rel * width)
                h = int(h_rel * height)
                
                # Обрезаем координаты
                x = max(0, min(x, width - 1))
                y = max(0, min(y, height - 1))
                w = max(1, min(w, width - x))
                h = max(1, min(h, height - y))
                
                # Извлекаем и размываем область
                face_region = image[y:y+h, x:x+w]
                blurred = cv2.GaussianBlur(face_region, (blur_strength, blur_strength), 0)
                image[y:y+h, x:x+w] = blurred
            
            # Сохраняем
            output_path = face_detector._generate_output_path(image_path, "blurred")
            cv2.imwrite(output_path, image)
            
            return output_path
            
        except Exception as e:
            print(f"❌ Ошибка при размытии: {e}")
            return None
    
    def apply_black_bar(self, image_path: str) -> Optional[str]:
        """
        Наложение черных полос на лица
        """
        try:
            # Читаем изображение
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # Обнаруживаем лица
            detections = face_detector.detect_faces(image_path)
            
            if not detections:
                return None
            
            # Применяем черные полосы
            height, width = image.shape[:2]
            
            for detection in detections:
                x_rel, y_rel, w_rel, h_rel = detection.bbox
                
                x = int(x_rel * width)
                y = int(y_rel * height)
                w = int(w_rel * width)
                h = int(h_rel * height)
                
                # Рисуем черный прямоугольник
                cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 0), -1)
            
            # Сохраняем
            output_path = face_detector._generate_output_path(image_path, "censored")
            cv2.imwrite(output_path, image)
            
            return output_path
            
        except Exception as e:
            print(f"❌ Ошибка при наложении черных полос: {e}")
            return None

# Создаем экземпляр сервиса
censorship_service = CensorshipService()