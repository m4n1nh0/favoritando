from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.models.base import Base


class Cliente(Base):
    """
    Modelo ORM para a tabela 'clientes'.
    Representa a entidade de negócio que possui favoritos.
    Um cliente está associado a um usuário do tipo 'cliente'.
    """
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    usuario = relationship("Usuario", back_populates="cliente")
    favoritos = relationship("Favorito", back_populates="cliente", cascade="all, delete-orphan")
