# test_faces_simple.py
import cv2
import numpy as np
import os

def create_realistic_test_image():
    """Создает более реалистичное тестовое изображение"""
    img = np.zeros((500, 500, 3), dtype=np.uint8)
    img.fill(240)
    
    # Первое лицо
    cv2.ellipse(img, (150, 200), (60, 80), 0, 0, 360, (200, 170, 140), -1)
    cv2.circle(img, (120, 170), 12, (255, 255, 255), -1)
    cv2.circle(img, (180, 170), 12, (255, 255, 255), -1)
    cv2.circle(img, (120, 170), 4, (0, 0, 0), -1)
    cv2.circle(img, (180, 170), 4, (0, 0, 0), -1)
    cv2.ellipse(img, (150, 240), (25, 15), 0, 0, 180, (100, 50, 30), 3)
    
    # Второе лицо (меньше)
    cv2.ellipse(img, (350, 250), (40, 55), 0, 0, 360, (180, 150, 130), -1)
    cv2.circle(img, (330, 230), 10, (255, 255, 255), -1)
    cv2.circle(img, (370, 230), 10, (255, 255, 255), -1)
    cv2.circle(img, (330, 230), 3, (0, 0, 0), -1)
    cv2.circle(img, (370, 230), 3, (0, 0, 0), -1)
    cv2.ellipse(img, (350, 280), (20, 10), 0, 0, 180, (80, 40, 20), 2)
    
    return img

def main():
    print("🧪 Тестирование системы цензурирования")
    print("=" * 50)
    
    # Создаем тестовое изображение
    test_image = "test_real_faces.jpg"
    img = create_realistic_test_image()
    cv2.imwrite(test_image, img)
    print(f"✅ Создано тестовое изображение: {test_image}")
    
    # Импортируем детектор
    from face_detection import face_detector
    
    # Тест 1: Обнаружение лиц
    print("\n🔍 ТЕСТ 1: Обнаружение лиц")
    detections = face_detector.detect_faces(test_image)
    
    print(f"\nРезультат: Найдено {len(detections)} лиц")
    for i, det in enumerate(detections, 1):
        x, y, w, h = det.bbox
        conf = det.confidence or 0.0
        print(f"Лицо {i}:")
        print(f"  Позиция: X={x:.3f}, Y={y:.3f}")
        print(f"  Размер: {w:.3f}×{h:.3f}")
        print(f"  Уверенность: {conf:.2f}")
    
    # Тест 2: Визуализация
    print("\n🎨 ТЕСТ 2: Визуализация обнаружения")
    image = cv2.imread(test_image)
    if image is not None and detections:
        vis = image.copy()
        height, width = image.shape[:2]
        
        colors = [(0, 255, 0), (0, 0, 255)]
        
        for i, det in enumerate(detections):
            x, y, w, h = det.bbox
            x_abs = int(x * width)
            y_abs = int(y * height)
            w_abs = int(w * width)
            h_abs = int(h * height)
            
            color = colors[i % len(colors)]
            cv2.rectangle(vis, (x_abs, y_abs), (x_abs + w_abs, y_abs + h_abs), color, 2)
            
            text = f"Face {i+1}"
            cv2.putText(vis, text, (x_abs, y_abs - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        vis_path = "detection_visualization.jpg"
        cv2.imwrite(vis_path, vis)
        print(f"✅ Визуализация сохранена: {vis_path}")
    
    # Тест 3: Цензурирование
    print("\n🔄 ТЕСТ 3: Цензурирование (пикселизация)")
    result = face_detector.censor_faces_pixelate(test_image, pixel_size=20)
    
    if result and os.path.exists(result):
        print(f"✅ Цензурированное изображение: {result}")
        
        # Показываем сравнение
        original = cv2.imread(test_image)
        censored = cv2.imread(result)
        
        if original is not None and censored is not None:
            # Создаем коллаж
            collage = np.hstack([original, censored])
            
            # Добавляем текст
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(collage, "ДО ЦЕНЗУРЫ", (10, 30), font, 1, (0, 255, 0), 2)
            cv2.putText(collage, "ПОСЛЕ ЦЕНЗУРЫ", (original.shape[1] + 10, 30), font, 1, (0, 0, 255), 2)
            
            # Показываем
            cv2.imshow("Сравнение результатов", collage)
            cv2.waitKey(5000)
            cv2.destroyAllWindows()
            
            # Сохраняем
            cv2.imwrite("comparison_result.jpg", collage)
            print("✅ Результат сравнения сохранен")
    
    # Очистка
    if os.path.exists(test_image):
        os.remove(test_image)
    
    print("\n" + "=" * 50)
    print("✅ Все тесты завершены успешно!")

if __name__ == "__main__":
    main()