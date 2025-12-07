# README

Веб-приложение для смешивания изображений с использованием нейросетей и анализа цветовых распределений.

## Возможности
- Смешивание двух изображений с регулируемым коэффициентом
- Анализ цветовых распределений (гистограммы)
- Защита reCAPTCHA


##  Технологии

- **Backend:** FastAPI, Python
- **Frontend:** HTML, Jinja2, Bootstrap Superhero
- **Обработка изображений:** Pillow, NumPy, Matplotlib
- **Безопасность:** reCAPTCHA
- **Деплой:** Uvicorn

##  Установка и запуск

```bash
# Клонировать репозиторий
git clone https://github.com/zhenyaselivonova-star/image-blender-app.git

# Установить зависимости
pip install -r requirements.txt

# Запустить сервер
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Версия пайтона
python-3.11.0

# Конфигурационные файлы
fastapi==0.104.1
uvicorn==0.24.0
pillow==10.1.0
matplotlib==3.8.2
numpy==1.24.3
python-multipart==0.0.6
