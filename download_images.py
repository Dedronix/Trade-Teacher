# download_images.py
import os
import requests

# Список картинок для курса (можно добавить свои ссылки)
images = {
    "day1": "https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg",
    "day2": "https://upload.wikimedia.org/wikipedia/commons/6/6e/Golde33443.jpg",
    "day3": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Pizigai.jpg",
    "day4": "https://upload.wikimedia.org/wikipedia/commons/1/17/Google-flutter-logo.png",
    "day5": "https://upload.wikimedia.org/wikipedia/commons/3/3f/JPEG_example_flower.jpg"
}

# Создаём папку, если её нет
os.makedirs("images", exist_ok=True)

# Скачиваем картинки
for name, url in images.items():
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(f"images/{name}.jpg", "wb") as f:
                f.write(response.content)
            print(f"{name} - скачано")
        else:
            print(f"{name} - ошибка загрузки ({response.status_code})")
    except Exception as e:
        print(f"{name} - ошибка: {e}")

print("✅ Все картинки обработаны")
