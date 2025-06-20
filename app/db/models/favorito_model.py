from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.models.base import Base


class Favorito(Base):
    """
    Modelo ORM para a tabela 'favoritos'.
    Armazena os produtos favoritos de um cliente.
    """
    __tablename__ = "favoritos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), index=True, nullable=False)
    produto_id = Column(Integer, index=True, nullable=False)
    titulo = Column(String, nullable=False)
    imagem = Column(String, nullable=False)
    preco = Column(Numeric(10, 2), nullable=False)
    review = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    cliente = relationship("Cliente", back_populates="favoritos")

    __table_args__ = (
        UniqueConstraint('cliente_id', 'produto_id', name='uq_cliente_produto'),
    )
