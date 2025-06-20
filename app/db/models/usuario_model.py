from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.models.base import Base, pwd_context


class Usuario(Base):
    """
    Modelo ORM para a tabela 'usuarios'. Gerencia login e perfis.
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    perfil = Column(String, default="cliente", nullable=False)

    cliente_id = Column(Integer, ForeignKey("clientes.id",
                                            ondelete="CASCADE"),
                        unique=True, nullable=True)
    cliente = relationship("Cliente", back_populates="usuario",
                           uselist=False, cascade="all, delete-orphan",
                           single_parent=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def verify_password(self, password: str):
        """Verifica se a senha fornecida corresponde à senha hasheada."""
        return pwd_context.verify(password, self.hashed_password)
