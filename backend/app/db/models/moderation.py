"""Modèles SQLAlchemy pour le service de modération."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Boolean, Float, Enum, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.moderation.models import ModerationType


class ModerationResult(Base):
    """Modèle de base de données pour les résultats de modération."""
    
    __tablename__ = "moderation_results"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    moderation_type: Mapped[ModerationType] = mapped_column(Enum(ModerationType))
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    categories: Mapped[dict] = mapped_column(JSON, nullable=True)
    category_scores: Mapped[dict] = mapped_column(JSON, nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
