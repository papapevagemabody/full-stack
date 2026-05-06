# pixelate_faces.py
import cv2
import numpy as np
import os

class FacePixelator:
    def __init__(self):
        self.cascade = None
        self._load_cascade()
    
    def _load_cascade(self):
        """Загружает каскад для обнаружения лиц"""
        try:
            # Пробуем разные пути к каскаду
            possible_paths = [
                # Стандартный путь OpenCV
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml',
                # Путь в установке Python
                os.path.join(os.path.dirname(cv2.__file__), 'data', 'haarcascades', 'haarcascade_frontalface_default.xml'),
                # Относительный путь (если скачали файл)
                'haarcascade_frontalface_default.xml',
                # Полный путь для Windows
                'C:/opencv/build/etc/haarcascades/haarcascade_frontalface_default.xml'
            ]
            
            for cascade_path in possible_paths:
                if os.path.exists(cascade_path):
                    cascade = cv2.CascadeClassifier(cascade_path)
                    if not cascade.empty():
                        self.cascade = cascade
                        print(f"✅ Каскад загружен: {cascade_path}")
                        return
            
            print("⚠️ Каскад не найден, создаем простой детектор")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки каскада: {e}")
    
    def detect_faces_simple(self, image):
        """Простое обнаружение лиц по цвету кожи"""
        try:
            height, width = image.shape[:2]
            faces = []
            
            # Конвертируем в HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Диапазон цвета кожи
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            
            # Маска цвета кожи
            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            
            # Улучшаем маску
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.erode(mask, kernel, iterations=1)
            mask = cv2.dilate(mask, kernel, iterations=2)
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            
            # Находим контуры
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Фильтруем по размеру
                if 1000 < area < (width * height * 0.5):
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Проверяем пропорции (лицо)
                    aspect_ratio = w / h
                    if 0.6 < aspect_ratio < 1.6:
                        faces.append((x, y, w, h))
            
            return faces
            
        except Exception as e:
            print(f"❌ Ошибка простого обнаружения: {e}")
            return []
    
    def detect_faces(self, image_path):
        """Обнаружение лиц на изображении"""
        try:
            # Читаем изображение
            image = cv2.imread(image_path)
            if image is None:
                print(f"❌ Не удалось прочитать изображение: {image_path}")
                return None, []
            
            faces = []
            
            # Пробуем использовать каскад если он загружен
            if self.cascade is not None:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)
                
                detected = self.cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                for (x, y, w, h) in detected:
                    faces.append((x, y, w, h))
            
            # Если каскад не нашел лиц, используем простой метод
            if not faces:
                print("🔄 Каскад не нашел лиц, использую цветовое обнаружение...")
                faces = self.detect_faces_simple(image)
            
            print(f"✅ Найдено лиц: {len(faces)}")
            return image, faces
            
        except Exception as e:
            print(f"❌ Ошибка обнаружения лиц: {e}")
            return None, []
    
    def pixelate_face(self, face_region, pixel_size=15):
        """Пикселизирует область лица"""
        try:
            # Получаем размеры области
            h, w = face_region.shape[:2]
            
            # Уменьшаем
            small = cv2.resize(face_region, (pixel_size, pixel_size), 
                             interpolation=cv2.INTER_LINEAR)
            
            # Увеличиваем обратно (создаем эффект пикселизации)
            pixelated = cv2.resize(small, (w, h), 
                                 interpolation=cv2.INTER_NEAREST)
            
            return pixelated
            
        except Exception as e:
            print(f"❌ Ошибка пикселизации: {e}")
            return face_region
    
    def process_image(self, image_path, pixel_size=15, output_path=None):
        """
        Основная функция: загружает изображение, находит лица и пикселизирует их
        """
        print(f"\n🎭 Обработка изображения: {image_path}")
        print(f"Размер пикселя: {pixel_size}")
        
        # Обнаружение лиц
        image, faces = self.detect_faces(image_path)
        
        if image is None:
            print("❌ Не удалось обработать изображение")
            return None
        
        if not faces:
            print("⚠️ Лица не обнаружены")
            return image_path
        
        # Копируем изображение для обработки
        processed = image.copy()
        
        # Пикселизируем каждое лицо
        for i, (x, y, w, h) in enumerate(faces):
            print(f"  Лицо {i+1}: x={x}, y={y}, w={w}, h={h}")
            
            # Извлекаем область лица
            face_region = processed[y:y+h, x:x+w]
            
            # Пикселизируем
            pixelated_face = self.pixelate_face(face_region, pixel_size)
            
            # Вставляем обратно
            processed[y:y+h, x:x+w] = pixelated_face
        
        # Генерируем имя для выходного файла
        if output_path is None:
            original_dir = os.path.dirname(image_path)
            original_name = os.path.basename(image_path)
            name, ext = os.path.splitext(original_name)
            output_path = os.path.join(original_dir, f"{name}_pixelated{ext}")
        
        # Сохраняем результат
        cv2.imwrite(output_path, processed)
        print(f"✅ Результат сохранен: {output_path}")
        
        return output_path
    
    def show_comparison(self, original_path, processed_path):
        """Показывает сравнение оригинального и обработанного изображения"""
        try:
            original = cv2.imread(original_path)
            processed = cv2.imread(processed_path)
            
            if original is None or processed is None:
                print("❌ Не удалось загрузить изображения для сравнения")
                return
            
            # Объединяем изображения горизонтально
            comparison = np.hstack([original, processed])
            
            # Добавляем текст
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(comparison, "ОРИГИНАЛ", (10, 30), font, 1, (0, 255, 0), 2)
            cv2.putText(comparison, "ПИКСЕЛИЗИРОВАНО", 
                       (original.shape[1] + 10, 30), font, 1, (0, 0, 255), 2)
            
            # Показываем
            cv2.imshow("Сравнение: Оригинал vs Пикселизировано", comparison)
            print("\n👀 Изображение открыто. Нажмите любую клавишу чтобы закрыть...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
        except Exception as e:
            print(f"❌ Ошибка при показе сравнения: {e}")

def main():
    """Основная функция для запуска из командной строки"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Пикселизация лиц на изображении')
    parser.add_argument('image', help='Путь к изображению для обработки')
    parser.add_argument('--pixel-size', type=int, default=15, 
                       help='Размер пикселя (по умолчанию: 15)')
    parser.add_argument('--output', help='Путь для сохранения результата')
    parser.add_argument('--show', action='store_true', 
                       help='Показать сравнение до/после')
    
    args = parser.parse_args()
    
    # Проверяем существование файла
    if not os.path.exists(args.image):
        print(f"❌ Файл не найден: {args.image}")
        return
    
    # Создаем пикселизатор
    pixelator = FacePixelator()
    
    # Обрабатываем изображение
    result_path = pixelator.process_image(
        args.image,
        pixel_size=args.pixel_size,
        output_path=args.output
    )
    
    # Показываем сравнение если нужно
    if args.show and result_path:
        pixelator.show_comparison(args.image, result_path)
    
    print(f"\n✅ Готово! Обработанное изображение: {result_path}")

if __name__ == "__main__":
    main()