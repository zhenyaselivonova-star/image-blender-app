from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import io
import base64


def blend_images(img1: Image.Image, img2: Image.Image, alpha: float) -> Image.Image:
    """Смешивание двух изображений с заданным коэффициентом"""
    # Приведение к одинаковому размеру
    img2_resized = img2.resize(img1.size)

    # Преобразование в numpy arrays
    arr1 = np.array(img1, dtype=np.float32)
    arr2 = np.array(img2_resized, dtype=np.float32)

    # Смешивание
    blended = alpha * arr1 + (1 - alpha) * arr2
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    return Image.fromarray(blended)


def create_histogram(img: Image.Image, title: str) -> str:
    """Создание гистограммы распределения цветов"""
    plt.figure(figsize=(8, 4))

    # Конвертируем в numpy array
    img_array = np.array(img)

    colors = ['red', 'green', 'blue']
    for i, color in enumerate(colors):
        plt.hist(img_array[:, :, i].ravel(), bins=50, alpha=0.7,
                 color=color, label=color.upper())

    plt.title(f"Гистограмма цветов - {title}")
    plt.xlabel("Значение пикселя")
    plt.ylabel("Частота")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Сохранение в base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    plt.close()

    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{image_base64}"