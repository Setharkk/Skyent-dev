# backend/tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app # Correction: app.main au lieu de ..app.main
from app.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok", 
        "app_name": settings.app_name, 
        "log_level": settings.log_level
    }

def test_read_main_settings_values():
    # This test is more of an integration test for settings loading
    assert settings.app_name == "Skyent API" # Default value
    assert settings.admin_email == "admin@skyent.dev"
    assert settings.items_per_user == 50
