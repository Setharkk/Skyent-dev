# backend/tests/test_analysis.py
from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_analysis_status():
    """Test que l'endpoint de statut d'analyse fonctionne correctement."""
    response = client.get("/analysis/")
    assert response.status_code == 200
    assert response.json() == {"module": "analysis", "status": "ok"}

def test_perform_analysis():
    """Test que l'analyse de données fonctionne correctement."""
    # Données de test
    test_data = {
        "code_size": 200,
        "complexity": "high",
        "language": "python"
    }
    
    # Envoyer la requête d'analyse
    response = client.post("/analysis/analyze", json=test_data)
    assert response.status_code == 200
    
    # Vérifier la structure de la réponse
    result = response.json()
    assert "analysis_id" in result
    assert "timestamp" in result
    assert "metrics" in result
    assert "status" in result
    assert result["status"] == "completed"
    
    # Vérifier que les métriques calculées sont cohérentes
    metrics = result["metrics"]
    assert metrics["lines_of_code"] == 200
    assert metrics["complexity"] == "high"
    assert 0 <= metrics["maintainability_index"] <= 100
    assert metrics["bugs_estimate"] > 0

def test_get_analysis_results():
    """Test la récupération des résultats d'analyse."""
    # Créer une analyse
    test_data = {"code_size": 150}
    response = client.post("/analysis/analyze", json=test_data)
    assert response.status_code == 200
    result = response.json()
    analysis_id = result["analysis_id"]
    
    # Récupérer cette analyse par son ID
    response = client.get(f"/analysis/results/{analysis_id}")
    assert response.status_code == 200
    retrieved = response.json()
    assert retrieved["analysis_id"] == analysis_id
    
    # Récupérer toutes les analyses
    response = client.get("/analysis/results")
    assert response.status_code == 200
    all_results = response.json()
    assert isinstance(all_results, list)
    assert len(all_results) >= 1  # Au moins l'analyse que nous venons de créer
    
    # Tester la récupération d'une analyse qui n'existe pas
    response = client.get("/analysis/results/nonexistent-id")
    assert response.status_code == 404
