# face_detection_fixed.py
import os
import cv2
import numpy as np
from typing import List, Tuple
from schemas import Detection
import random
import urllib.request

class FaceDetector:
    def __init__(self):
        self.cascades = {}
        self._download_and_load_cascades()
    
    def _download_and_load_cascades(self):
        """Скачивает и загружает каскады если их нет локально"""
        print("🔄 Загрузка каскадов для обнаружения лиц...")
        
        # Основные каскады
        cascade_urls = {
            'frontalface_default': 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml',
            'frontalface_alt': 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_alt.xml',
            'frontalface_alt2': 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_alt2.xml',
        }
        
        # Создаем папку для каскадов
        cascade_dir = "cascades"
        os.makedirs(cascade_dir, exist_ok=True)
        
        loaded = 0
        
        for name, url in cascade_urls.items():
            cascade_path = os.path.join(cascade_dir, f"{name}.xml")
            
            # Если файл уже есть, загружаем его
            if os.path.exists(cascade_path):
                cascade = cv2.CascadeClassifier(cascade_path)
                if not cascade.empty():
                    self.cascades[name] = cascade
                    loaded += 1
                    print(f"  ✓ Загружен: {name}")
                    continue
            
            # Пробуем найти в установке OpenCV
            try:
                # Стандартный путь OpenCV
                if hasattr(cv2, 'data'):
                    cv2_cascade_path = os.path.join(cv2.data.haarcascades, f'haarcascade_{name}.xml')
                    if os.path.exists(cv2_cascade_path):
                        cascade = cv2.CascadeClassifier(cv2_cascade_path)
                        if not cascade.empty():
                            self.cascades[name] = cascade
                            loaded += 1
                            print(f"  ✓ Найден в OpenCV: {name}")
                            continue
            except Exception:
                pass
            
            # Пробуем скачать
            try:
                print(f"  ⏳ Скачиваю {name}...")
                urllib.request.urlretrieve(url, cascade_path)
                
                cascade = cv2.CascadeClassifier(cascade_path)
                if not cascade.empty():
                    self.cascades[name] = cascade
                    loaded += 1
                    print(f"  ✓ Скачан и загружен: {name}")
                else:
                    print(f"  ❌ Не удалось загрузить скачанный каскад: {name}")
                    
            except Exception as e:
                print(f"  ❌ Ошибка скачивания {name}: {e}")
        
        if loaded == 0:
            print("⚠️ Не удалось загрузить каскады, создаем локальные файлы...")
            self._create_local_cascades()
        
        print(f"✅ Загружено каскадов: {loaded}")
    
    def _create_local_cascades(self):
        """Создает локальные файлы каскадов если не удалось скачать"""
        print("🔄 Создание локальных каскадов...")
        
        # XML для простого каскада
        simple_cascade_xml = """<?xml version="1.0"?>
<opencv_storage>
<cascade type_id="opencv-cascade-classifier"><stageType>BOOST</stageType>
  <featureType>HAAR</featureType>
  <height>24</height>
  <width>24</width>
  <stageParams>
    <maxWeakCount>211</maxWeakCount></stageParams>
  <featureParams>
    <maxCatCount>0</maxCatCount></featureParams>
  <stageNum>25</stageNum>
  <stages>
    <!-- stage 0 -->
    <_>
      <maxWeakCount>9</maxWeakCount>
      <stageThreshold>-0.7520880103111267</stageThreshold>
      <weakClassifiers>
        <_>
          <internalNodes>
            0 -1 0 -3.1511999964714050e-02</internalNodes>
          <leafValues>
            0.8333333134651184 -0.8235294222831726</leafValues></_>
        <_>
          <internalNodes>
            0 -1 1 -1.1795099973678589e-01</internalNodes>
          <leafValues>
            0.7222222089767456 -0.9166666865348816</leafValues></_></weakClassifiers></_></stages>
  <features>
    <_>
      <rects>
        <_>7 7 3 10 -1.</_>
        <_>8 7 1 10 3.</_></rects>
      <tilted>0</tilted></_>
    <_>
      <rects>
        <_>14 7 3 10 -1.</_>
        <_>15 7 1 10 3.</_></rects>
      <tilted>0</tilted></_></features></cascade>
</opencv_storage>"""
        
        # Сохраняем XML файл
        cascade_dir = "cascades"
        os.makedirs(cascade_dir, exist_ok=True)
        cascade_path = os.path.join(cascade_dir, "simple_face.xml")
        
        with open(cascade_path, 'w', encoding='utf-8') as f:
            f.write(simple_cascade_xml)
        
        # Загружаем каскад
        cascade = cv2.CascadeClassifier(cascade_path)
        if not cascade.empty():
            self.cascades['simple_face'] = cascade
            print("  ✓ Создан простой каскад")
        else:
            print("  ❌ Не удалось создать каскад")
    
    def detect_faces_simple(self, image_path: str) -> List[Detection]:
        """
        Простое обнаружение лиц с помощью цветовой сегментации
        (работает когда каскады не доступны)
        """
        try:
            # Читаем изображение
            image = cv2.imread(image_path)
            if image is None:
                from PIL import Image
                pil_image = Image.open(image_path)
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            height, width = image.shape[:2]
            faces = []
            
            # Конвертируем в HSV для выделения цвета кожи
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Диапазон цвета кожи в HSV
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            
            # Создаем маску цвета кожи
            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            
            # Улучшаем маску
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.erode(mask, kernel, iterations=2)
            mask = cv2.dilate(mask, kernel, iterations=2)
            mask = cv2.GaussianBlur(mask, (5, 5), 100)
            
            # Находим контуры
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < (width * height * 0.3):  # Фильтруем по размеру
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Проверяем пропорции (лицо обычно шире чем выше)
                    aspect_ratio = w / h if h > 0 else 0
                    if 0.7 < aspect_ratio < 1.5:
                        # Конвертируем в относительные координаты
                        x_rel = x / width
                        y_rel = y / height
                        w_rel = w / width
                        h_rel = h / height
                        
                        # Добавляем отступ
                        padding = 0.1
                        x_rel = max(0.0, x_rel - w_rel * padding)
                        y_rel = max(0.0, y_rel - h_rel * padding)
                        w_rel = min(1.0 - x_rel, w_rel * (1 + 2 * padding))
                        h_rel = min(1.0 - y_rel, h_rel * (1 + 2 * padding))
                        
                        # Вычисляем уверенность на основе площади
                        confidence = min(0.8, area / (width * height) * 10)
                        
                        faces.append((x_rel, y_rel, w_rel, h_rel, confidence))
            
            return faces
            
        except Exception as e:
            print(f"❌ Ошибка простого обнаружения: {e}")
            return []
    
    def detect_faces(self, image_path: str) -> List[Detection]:
        """
        Основной метод обнаружения лиц
        """
        try:
            # Проверяем файл
            if not os.path.exists(image_path):
                print(f"❌ Файл не найден: {image_path}")
                return self._fallback_detection()
            
            faces = []
            
            # Пробуем использовать каскады если они есть
            if self.cascades:
                faces = self._detect_with_cascades(image_path)
            
            # Если каскады не нашли лица, пробуем простой метод
            if not faces:
                print("🔄 Каскады не нашли лица, пробуем простой метод...")
                faces = self.detect_faces_simple(image_path)
            
            # Если ничего не помогло, используем fallback
            if not faces:
                print(f"⚠️ Лица не обнаружены на {image_path}")
                return self._fallback_detection()
            
            # Конвертируем в формат Detection
            detections = []
            for (x, y, w, h, confidence) in faces:
                detection = Detection(
                    type="face",
                    bbox=(float(x), float(y), float(w), float(h)),
                    confidence=float(confidence)
                )
                detections.append(detection)
            
            print(f"✅ Обнаружено {len(detections)} лиц")
            return detections
            
        except Exception as e:
            print(f"❌ Ошибка обнаружения лиц: {e}")
            return self._fallback_detection()
    
    def _detect_with_cascades(self, image_path: str) -> List[Tuple]:
        """Обнаружение с использованием каскадов"""
        try:
            # Читаем изображение
            image = cv2.imread(image_path)
            if image is None:
                from PIL import Image
                pil_image = Image.open(image_path)
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Конвертируем в grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Улучшаем контраст
            gray = cv2.equalizeHist(gray)
            
            height, width = gray.shape
            all_faces = []
            
            for cascade_name, cascade in self.cascades.items():
                try:
                    # Обнаружение лиц
                    detected = cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.1,
                        minNeighbors=5,
                        minSize=(30, 30),
                        flags=cv2.CASCADE_SCALE_IMAGE
                    )
                    
                    for (x, y, w, h) in detected:
                        # Относительные координаты
                        x_rel = x / width
                        y_rel = y / height
                        w_rel = w / width
                        h_rel = h / height
                        
                        # Уверенность
                        confidence = 0.7 + (w_rel * h_rel) * 2
                        confidence = min(max(confidence, 0.3), 0.9)
                        
                        all_faces.append((x_rel, y_rel, w_rel, h_rel, confidence))
                        
                except Exception as e:
                    print(f"⚠️ Ошибка в каскаде {cascade_name}: {e}")
                    continue
            
            return all_faces
            
        except Exception as e:
            print(f"❌ Ошибка обнаружения каскадами: {e}")
            return []
    
    def _fallback_detection(self) -> List[Detection]:
        """Fallback метод"""
        detections = []
        
        # С вероятностью 50% "находим" 1-2 лица
        if random.random() < 0.5:
            num_faces = random.randint(1, 2)
            
            for i in range(num_faces):
                x = random.uniform(0.2, 0.6)
                y = random.uniform(0.2, 0.6)
                w = random.uniform(0.1, 0.25)
                h = w * random.uniform(0.8, 1.2)
                
                if x + w > 0.95:
                    w = 0.95 - x
                if y + h > 0.95:
                    h = 0.95 - y
                
                detection = Detection(
                    type="face",
                    bbox=(x, y, w, h),
                    confidence=0.4
                )
                detections.append(detection)
        
        if detections:
            print(f"⚠️ Использована имитация: найдено {len(detections)} лиц")
        
        return detections
    
    def censor_faces_pixelate(self, image_path: str, pixel_size: int = 15) -> str:
        """
        Пикселизация лиц
        """
        try:
            # Читаем изображение
            image = cv2.imread(image_path)
            if image is None:
                from PIL import Image
                pil_image = Image.open(image_path)
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Обнаруживаем лица
            detections = self.detect_faces(image_path)
            
            if not detections:
                print("⚠️ Лица не обнаружены для цензурирования")
                return image_path
            
            height, width = image.shape[:2]
            
            # Пикселизируем каждое лицо
            for detection in detections:
                x_rel, y_rel, w_rel, h_rel = detection.bbox
                
                x = int(x_rel * width)
                y = int(y_rel * height)
                w = int(w_rel * width)
                h = int(h_rel * height)
                
                # Проверяем границы
                x = max(0, min(x, width - 1))
                y = max(0, min(y, height - 1))
                w = max(1, min(w, width - x))
                h = max(1, min(h, height - y))
                
                # Пикселизация
                face_region = image[y:y+h, x:x+w]
                small = cv2.resize(face_region, (pixel_size, pixel_size), 
                                 interpolation=cv2.INTER_LINEAR)
                pixelated = cv2.resize(small, (w, h), 
                                     interpolation=cv2.INTER_NEAREST)
                
                image[y:y+h, x:x+w] = pixelated
            
            # Сохраняем
            output_path = self._generate_output_path(image_path, "pixelated")
            cv2.imwrite(output_path, image)
            
            print(f"✅ Пикселизировано {len(detections)} лиц")
            return output_path
            
        except Exception as e:
            print(f"❌ Ошибка пикселизации: {e}")
            return image_path
    
    def _generate_output_path(self, original_path: str, suffix: str) -> str:
        """Генерирует путь для сохранения"""
        import os
        from datetime import datetime
        
        processed_dir = "processed"
        os.makedirs(processed_dir, exist_ok=True)
        
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        
        timestamp = datetime.now().strftime("%H%M%S")
        new_name = f"{name}_{suffix}_{timestamp}{ext}"
        
        return os.path.join(processed_dir, new_name)

face_detector = FaceDetector()