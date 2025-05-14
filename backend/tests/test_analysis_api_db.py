# backend/tests/test_analysis_api_db.py
import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db_session

# Base de données en mémoire pour les tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Créer une nouvelle boucle d'événements pour chaque session de test."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def test_app():
    """Créer une instance de test de l'application."""
    # Configuration d'une base de données en mémoire pour les tests
    engine = create_async_engine(TEST_DB_URL, echo=False)
    test_async_session = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )
    
    # Créer les tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Remplacer la dépendance de session de base de données
    async def override_get_db():
        async with test_async_session() as session:
            yield session
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    yield app
    
    # Nettoyer après les tests
    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_analyze_content_endpoint(test_app):
    """Tester l'endpoint d'analyse de contenu avec base de données."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.post(
            "/analysis/db/analyze",
            json={
                "content": "Ceci est un contenu de test pour l'API d'analyse avec base de données.",
                "analyze_sentiment": True,
                "extract_keywords": True,
                "create_summary": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] > 0
        assert "content_hash" in data
        
        # Vérifier la présence d'une analyse de sentiment
        assert "sentiment" in data
        assert data["sentiment"] is not None
        assert "positive_score" in data["sentiment"]
        
        # Vérifier la présence de mots-clés
        assert "keywords" in data
        assert isinstance(data["keywords"], list)
        assert len(data["keywords"]) > 0
        
        # Vérifier la présence d'un résumé
        assert "summary" in data
        assert data["summary"] is not None
        assert "text" in data["summary"]

@pytest.mark.asyncio
async def test_get_analysis_by_id(test_app):
    """Tester l'endpoint de récupération d'une analyse par ID avec base de données."""
    # D'abord, créer une analyse
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response_create = await client.post(
            "/analysis/db/analyze",
            json={
                "content": "Un autre contenu de test pour la récupération par ID.",
                "analyze_sentiment": True,
                "extract_keywords": True,
                "create_summary": True
            }
        )
        
        assert response_create.status_code == 200
        data_create = response_create.json()
        analysis_id = data_create["id"]
        
        # Ensuite, récupérer l'analyse par ID
        response_get = await client.get(f"/analysis/db/results/{analysis_id}")
        
        assert response_get.status_code == 200
        data_get = response_get.json()
        assert "id" in data_get
        assert data_get["id"] == analysis_id
        
        # Vérifier que la récupération d'un ID inexistant renvoie une erreur 404
        response_not_found = await client.get("/analysis/db/results/99999")
        assert response_not_found.status_code == 404

@pytest.mark.asyncio
async def test_list_analyses(test_app):
    """Tester l'endpoint de liste des analyses avec base de données."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # D'abord, créer quelques analyses
        for i in range(3):
            await client.post(
                "/analysis/db/analyze",
                json={
                    "content": f"Contenu de test {i+1} pour la liste des analyses.",
                    "analyze_sentiment": True,
                    "extract_keywords": True,
                    "create_summary": True
                }
            )
        
        # Récupérer la liste des analyses
        response = await client.get("/analysis/db/results")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # Au moins les 3 analyses que nous venons de créer