# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .config import settings
from .analysis.router import router as analysis_router
from .analysis.router_db import router as analysis_db_router
from .analysis.campaign_router import router as analysis_campaign_router
from .generation.router import router as generation_router
from .builder.router import router as builder_router
from .publication.router import router as publication_router
from .tracking.router import router as tracking_router
from .profiling.router import router as profiling_router
from .model_selector.router import router as model_selector_router
from .websearch.router import router as websearch_router
from .db.base import Base
from .db.session import async_engine


@asynccontextmanager
async def lifespan(app_: FastAPI):
    # Startup events
    print(f"Starting up {settings.app_name}...")
    print(f"Log level set to: {settings.log_level}")
    
    # Créer les tables dans la base de données
    try:
        print("Initializing database tables...")
        # Créer les tables si elles n'existent pas déjà
        # En production, vous devriez utiliser Alembic pour les migrations
        # mais en développement, c'est pratique pour des tests rapides
        async with async_engine.begin() as conn:
            if settings.database_url.startswith(("sqlite", "postgresql")):
                # Crée toutes les tables définies dans les modèles SQLAlchemy
                await conn.run_sync(Base.metadata.create_all)
                print("Database tables created successfully")
            else:
                print(f"Database initialization skipped for URL type: {settings.database_url.split(':', 1)[0]}")
    except Exception as e:
        print(f"Error initializing database: {e}")
        # En production, vous devriez utiliser un système de journalisation approprié
        # et potentiellement arrêter le démarrage de l'application
    
    yield
    
    # Shutdown events
    print(f"Shutting down {settings.app_name}...")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app_name": settings.app_name, "log_level": settings.log_level}

# Include routers from submodules
app.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
app.include_router(analysis_db_router, prefix="/analysis", tags=["Analysis DB"])
app.include_router(analysis_campaign_router, tags=["Campaign Analysis"])
app.include_router(generation_router, prefix="/generation", tags=["Generation"])
app.include_router(builder_router, prefix="/builder", tags=["Builder"])
app.include_router(publication_router, prefix="/publication", tags=["Publication"])
app.include_router(tracking_router, prefix="/tracking", tags=["Tracking"])
app.include_router(profiling_router, prefix="/profiling", tags=["Profiling"])
app.include_router(model_selector_router, prefix="/model-selector", tags=["Model Selector"])
app.include_router(websearch_router, prefix="/websearch", tags=["Web Search"])

