"""
Script pour créer manuellement les tables dans la base de données.
Utiliser ce script si les migrations Alembic ne fonctionnent pas correctement.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine

# Import la classe Base et les modèles
from app.db.base import Base
from app.db.all_models import *  # Import tous les modèles

# Import la configuration
from app.config import settings

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables():
    """Crée toutes les tables définies dans les modèles."""
    # Créer le moteur de base de données
    engine = create_async_engine(
        settings.database_url,
        echo=True  # Pour afficher les requêtes SQL
    )
    
    # Créer les tables
    async with engine.begin() as conn:
        logger.info("Suppression des tables existantes...")
        await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Création des nouvelles tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Tables créées avec succès!")

if __name__ == "__main__":
    logger.info(f"Création des tables dans la base de données: {settings.database_url}")
    asyncio.run(create_tables())
