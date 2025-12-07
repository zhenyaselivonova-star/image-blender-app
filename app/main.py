from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from PIL import Image
import numpy as np
import io
import matplotlib.pyplot as plt
import base64
import requests
from .utils import blend_images, create_histogram

app = FastAPI(title="Image Blender", version="1.0.0")

#КЛЮЧИ reCAPTCHA
RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

# Настройка путей
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Создаем папку для загрузок
os.makedirs("static/uploads", exist_ok=True)


async def verify_recaptcha(recaptcha_response: str) -> bool:
    """Проверка reCAPTCHA response"""
    if not recaptcha_response:
        return False

    try:
        verification_url = "https://www.google.com/recaptcha/api/siteverify"
        payload = {
            "secret": RECAPTCHA_SECRET_KEY,
            "response": recaptcha_response
        }
        response = requests.post(verification_url, data=payload, timeout=10)
        result = response.json()
        print(f"reCAPTCHA verification result: {result}")
        return result.get("success", False)
    except Exception as e:
        print(f"reCAPTCHA verification error: {e}")
        return False


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recaptcha_site_key": RECAPTCHA_SITE_KEY
    })


@app.post("/blend", response_class=HTMLResponse)
async def blend_images_endpoint(
        request: Request,
        image1: UploadFile = File(...),
        image2: UploadFile = File(...),
        alpha: float = Form(..., ge=0, le=1),
        recaptcha_response: str = Form(...)
):
    print(f"Received reCAPTCHA response: {recaptcha_response[:50]}...")

    # Проверка reCAPTCHA
    is_valid_captcha = await verify_recaptcha(recaptcha_response)
    print(f"reCAPTCHA valid: {is_valid_captcha}")

    if not is_valid_captcha:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "recaptcha_site_key": RECAPTCHA_SITE_KEY,
            "error": "Пожалуйста, пройдите проверку"
        })

    try:
        # Чтение и валидация изображений
        contents1 = await image1.read()
        contents2 = await image2.read()

        img1 = Image.open(io.BytesIO(contents1)).convert("RGB")
        img2 = Image.open(io.BytesIO(contents2)).convert("RGB")

        # Смешивание изображений
        blended_img = blend_images(img1, img2, alpha)

        # Создание гистограмм
        hist1 = create_histogram(img1, "график 1")
        hist2 = create_histogram(img2, "график 2")
        hist_blended = create_histogram(blended_img, "результат смешивания графиков")

        # Сохранение результата
        blended_path = "static/uploads/blended_result.jpg"
        blended_img.save(blended_path)

        return templates.TemplateResponse("result.html", {
            "request": request,
            "blended_image": f"/{blended_path}",
            "histogram1": hist1,
            "histogram2": hist2,
            "histogram_blended": hist_blended,
            "alpha": alpha
        })

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "recaptcha_site_key": RECAPTCHA_SITE_KEY,
            "error": f"Ошибка обработки: {str(e)}"
        })


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Image Blender"}
