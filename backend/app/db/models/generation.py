"""Modèles SQLAlchemy pour le service de génération."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.generation.models import ContentType, ContentTone


class GeneratedContent(Base):
    """Modèle de base de données pour les contenus générés."""
    
    __tablename__ = "generated_contents"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType))
    content: Mapped[str] = mapped_column(Text)
    prompt: Mapped[str] = mapped_column(Text)
    tone: Mapped[ContentTone] = mapped_column(Enum(ContentTone), nullable=True)
    model_used: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    
    # Relations avec les publications
    publications: Mapped[list["Publication"]] = relationship(
        "Publication", back_populates="generated_content", cascade="all, delete-orphan"
    )
