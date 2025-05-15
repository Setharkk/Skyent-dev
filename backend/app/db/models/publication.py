"""Modèles SQLAlchemy pour le service de publication."""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Enum, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.publication.models import SocialMediaPlatform, PublicationStatus


class Publication(Base):
    """Modèle de base de données pour les publications."""
    
    __tablename__ = "publications"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    content_id: Mapped[str] = mapped_column(String(36), ForeignKey("generated_contents.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    platform: Mapped[SocialMediaPlatform] = mapped_column(Enum(SocialMediaPlatform))
    status: Mapped[PublicationStatus] = mapped_column(Enum(PublicationStatus))
    platform_post_id: Mapped[str] = mapped_column(String(100), nullable=True)
    schedule_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    additional_options: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True
    )
    
    # Relations avec le contenu généré
    generated_content = relationship("GeneratedContent", back_populates="publications")
