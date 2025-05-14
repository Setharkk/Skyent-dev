# app/db/models/analysis.py
import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Integer, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Analysis(Base):
    """Modèle de base de données pour les analyses de contenu."""
    
    __tablename__ = "analyses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    original_content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relations avec d'autres modèles
    sentiment_analyses: Mapped[list["SentimentAnalysis"]] = relationship(
        "SentimentAnalysis", back_populates="analysis", cascade="all, delete-orphan"
    )
    keywords: Mapped[list["Keyword"]] = relationship(
        "Keyword", back_populates="analysis", cascade="all, delete-orphan"
    )
    summary: Mapped[Optional["Summary"]] = relationship(
        "Summary", back_populates="analysis", uselist=False, cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"Analysis(id={self.id}, content_hash={self.content_hash}, created_at={self.created_at})"


class SentimentAnalysis(Base):
    """Modèle pour l'analyse de sentiment d'un contenu."""
    
    __tablename__ = "sentiment_analyses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"))
    positive_score: Mapped[float] = mapped_column(Float)
    negative_score: Mapped[float] = mapped_column(Float)
    neutral_score: Mapped[float] = mapped_column(Float)
    compound_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    
    # Relation avec l'analyse parente
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="sentiment_analyses")
    
    def __repr__(self) -> str:
        return f"SentimentAnalysis(id={self.id}, analysis_id={self.analysis_id}, compound_score={self.compound_score})"


class Keyword(Base):
    """Modèle pour les mots-clés extraits d'un contenu."""
    
    __tablename__ = "keywords"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"))
    text: Mapped[str] = mapped_column(String(100))
    score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    
    # Relation avec l'analyse parente
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="keywords")
    
    def __repr__(self) -> str:
        return f"Keyword(id={self.id}, analysis_id={self.analysis_id}, text={self.text}, score={self.score})"


class Summary(Base):
    """Modèle pour le résumé d'un contenu."""
    
    __tablename__ = "summaries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), unique=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    
    # Relation avec l'analyse parente
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="summary")
    
    def __repr__(self) -> str:
        return f"Summary(id={self.id}, analysis_id={self.analysis_id})"
