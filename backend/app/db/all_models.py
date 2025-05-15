"""Ce fichier importe tous les modèles SQLAlchemy pour Alembic."""
# Import explicite de tous les modèles SQLAlchemy
# Nécessaire pour qu'Alembic détecte correctement les modèles lors de la génération des migrations

# Import des modèles d'analyse
from app.db.models.analysis import Analysis, SentimentAnalysis, Keyword, Summary

# Import des modèles de génération
from app.db.models.generation import GeneratedContent

# Import des modèles de modération
from app.db.models.moderation import ModerationResult

# Import des modèles de publication
from app.db.models.publication import Publication

# Cette liste permet de s'assurer que tous les modèles sont importés
__all__ = [
    "Analysis", "SentimentAnalysis", "Keyword", "Summary",
    "GeneratedContent", "ModerationResult", "Publication"
]
