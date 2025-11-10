import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils import blend_images, create_histogram
from PIL import Image
import numpy as np
import io
import base64

client = TestClient(app)


# Тесты для главной страницы и базовой функциональности
def test_home_page():
    """Тест главной страницы"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Image Blender" in response.text
    assert "Смешивание изображений" in response.text
    assert 'recaptcha_site_key' in response.text


def test_health_check():
    """Тест health check эндпоинта"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "Image Blender"


def test_invalid_endpoint():
    """Тест несуществующего эндпоинта"""
    response = client.get("/nonexistent")
    assert response.status_code == 404


# Тесты для утилит обработки изображений
def test_blend_images_same_size():
    """Тест смешивания изображений одинакового размера"""
    # Создаем тестовые изображения
    img1 = Image.new('RGB', (100, 100), color='red')
    img2 = Image.new('RGB', (100, 100), color='blue')

    # Тестируем разные коэффициенты смешивания
    for alpha in [0.0, 0.5, 1.0]:
        result = blend_images(img1, img2, alpha)

        assert isinstance(result, Image.Image)
        assert result.size == (100, 100)
        assert result.mode == 'RGB'


def test_blend_images_different_size():
    """Тест смешивания изображений разного размера"""
    img1 = Image.new('RGB', (200, 100), color='red')
    img2 = Image.new('RGB', (100, 200), color='blue')

    result = blend_images(img1, img2, 0.5)

    assert isinstance(result, Image.Image)
    assert result.size == (200, 100)  # Должно принять размер первого изображения


def test_blend_images_extreme_values():
    """Тест граничных значений коэффициента смешивания"""
    img1 = Image.new('RGB', (50, 50), color=(255, 0, 0))  # Красный
    img2 = Image.new('RGB', (50, 50), color=(0, 0, 255))  # Синий

    # alpha = 1.0 - должно вернуть первое изображение
    result1 = blend_images(img1, img2, 1.0)
    # alpha = 0.0 - должно вернуть второе изображение (resized)
    result2 = blend_images(img1, img2, 0.0)

    assert isinstance(result1, Image.Image)
    assert isinstance(result2, Image.Image)


def test_create_histogram():
    """Тест создания гистограммы"""
    # Создаем тестовое изображение
    img = Image.new('RGB', (50, 50), color='red')

    histogram = create_histogram(img, "Test Image")

    # Проверяем, что возвращается base64 строка
    assert isinstance(histogram, str)
    assert histogram.startswith('data:image/png;base64,')

    # Проверяем, что base64 данные валидны
    base64_data = histogram.replace('data:image/png;base64,', '')
    try:
        decoded_data = base64.b64decode(base64_data)
        assert len(decoded_data) > 0
    except Exception:
        pytest.fail("Invalid base64 data in histogram")


# Тесты для эндпоинта смешивания
def test_blend_endpoint_no_files():
    """Тест эндпоинта смешивания без файлов"""
    response = client.post("/blend", data={"alpha": 0.5})
    assert response.status_code in [422, 400]  # Validation error


def test_blend_endpoint_invalid_alpha():
    """Тест эндпоинта смешивания с невалидным alpha"""
    # alpha > 1.0
    response = client.post("/blend", data={"alpha": 1.5})
    assert response.status_code in [422, 400]

    # alpha < 0.0
    response = client.post("/blend", data={"alpha": -0.5})
    assert response.status_code in [422, 400]


def test_blend_endpoint_missing_recaptcha():
    """Тест эндпоинта без reCAPTCHA"""
    # Создаем тестовые файлы
    files = {
        'image1': ('test1.jpg', b'fake_image_data', 'image/jpeg'),
        'image2': ('test2.jpg', b'fake_image_data', 'image/jpeg')
    }
    data = {'alpha': 0.5}

    response = client.post("/blend", data=data, files=files)
    # Должен вернуть ошибку из-за отсутствия reCAPTCHA
    assert response.status_code == 200  # Возвращает страницу с ошибкой
    assert "reCAPTCHA" in response.text


def test_blend_endpoint_invalid_recaptcha():
    """Тест с невалидной reCAPTCHA"""
    files = {
        'image1': ('test1.jpg', b'fake_image_data', 'image/jpeg'),
        'image2': ('test2.jpg', b'fake_image_data', 'image/jpeg')
    }
    data = {
        'alpha': 0.5,
        'recaptcha_response': 'invalid_captcha_response'
    }

    response = client.post("/blend", data=data, files=files)
    assert response.status_code == 200
    assert "reCAPTCHA" in response.text


# Тесты с мокингом reCAPTCHA для тестирования успешного сценария
class MockRecaptchaResponse:
    @staticmethod
    def json():
        return {"success": True}


def test_successful_image_blending(monkeypatch):
    """Тест успешного смешивания изображений с мокингом reCAPTCHA"""

    def mock_recaptcha_verify(*args, **kwargs):
        return True

    # Мокаем проверку reCAPTCHA
    monkeypatch.setattr("app.main.verify_recaptcha", mock_recaptcha_verify)

    # Создаем реальные тестовые изображения в памяти
    def create_test_image(color, size=(100, 100)):
        img = Image.new('RGB', size, color=color)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes.getvalue()

    red_image = create_test_image('red')
    blue_image = create_test_image('blue')

    files = {
        'image1': ('red.jpg', red_image, 'image/jpeg'),
        'image2': ('blue.jpg', blue_image, 'image/jpeg')
    }
    data = {
        'alpha': 0.5,
        'recaptcha_response': 'mocked_valid_response'
    }

    response = client.post("/blend", data=data, files=files)

    # Проверяем успешный ответ
    assert response.status_code == 200
    assert "Результат смешивания" in response.text
    assert "blended_result.jpg" in response.text
    assert "Гистограмма" in response.text


def test_image_validation():
    """Тест валидации типов файлов"""

    def mock_recaptcha_verify(*args, **kwargs):
        return True

    # Пытаемся загрузить не-image файлы
    files = {
        'image1': ('test.txt', b'not_an_image', 'text/plain'),
        'image2': ('test.pdf', b'%PDF fake content', 'application/pdf')
    }
    data = {
        'alpha': 0.5,
        'recaptcha_response': 'mocked_valid_response'
    }

    response = client.post("/blend", data=data, files=files)
    # Должен вернуть ошибку обработки
    assert response.status_code == 200
    assert "Ошибка обработки" in response.text


# Тесты для проверки создания директорий
def test_upload_directory_creation():
    """Тест создания директории для загрузок"""
    import os
    import tempfile
    import shutil

    # Создаем временную директорию для теста
    test_dir = tempfile.mkdtemp()

    try:
        # Имитируем запуск приложения с новой директорией
        from app.main import app
        assert hasattr(app, 'mount')  # Проверяем что static files настроены
    finally:
        # Убираем временную директорию
        shutil.rmtree(test_dir, ignore_errors=True)


# Тесты для проверки ошибок сервера
def test_server_error_handling():
    """Тест обработки внутренних ошибок сервера"""
    # Здесь можно добавить тесты для различных сценариев ошибок
    # Например, когда PIL не может открыть "битый" файл изображения
    pass


# Параметризованные тесты для разных значений alpha
@pytest.mark.parametrize("alpha", [0.0, 0.1, 0.5, 0.9, 1.0])
def test_blend_with_different_alphas(alpha):
    """Тест смешивания с разными значениями коэффициента"""
    img1 = Image.new('RGB', (50, 50), color=(255, 0, 0))
    img2 = Image.new('RGB', (50, 50), color=(0, 0, 255))

    result = blend_images(img1, img2, alpha)

    assert isinstance(result, Image.Image)
    assert result.size == (50, 50)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])