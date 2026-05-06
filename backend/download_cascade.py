# download_cascade.py
import urllib.request
import os

# Скачиваем файл каскада
url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
filename = "haarcascade_frontalface_default.xml"

print("📥 Скачиваю каскад с GitHub...")
urllib.request.urlretrieve(url, filename)

if os.path.exists(filename):
    print(f"✅ Файл скачан: {filename}")
    print("📁 Разместите его в папке с вашим скриптом")
else:
    print("❌ Не удалось скачать файл")