# run_app.py
# Главный файл для запуска приложения
# Открывает браузер автоматически и запускает сервер Flask

import webbrowser
import threading
from app import create_app
import os

# Определяем пути к шаблонам и статическим файлам
template_dir = os.path.join(os.path.dirname(__file__), "app", "templates")
static_dir = os.path.join(os.path.dirname(__file__), "static")

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

# Создаём экземпляр приложения Flask
app = create_app(template_folder=template_dir, static_folder=static_dir)

if __name__ == "__main__":
    # Открываем браузер через 1 секунду после запуска сервера
    threading.Timer(1, open_browser).start()
    # Запускаем сервер Flask
    app.run(host='0.0.0.0', port=5000, debug=True)
