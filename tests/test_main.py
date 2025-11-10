import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Смешивание изображений" in response.text

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_blend_endpoint_no_files():
    response = client.post("/blend", data={"alpha": 0.5})
    assert response.status_code == 200