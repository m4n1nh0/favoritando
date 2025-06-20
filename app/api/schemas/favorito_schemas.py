from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FavoritoBase(BaseModel):
    """
    Schema base para criação de favorito.
    """
    produto_id: int = Field(..., gt=0, description="ID do produto da Fake Store API")


class FavoritoCreate(FavoritoBase):
    """
    Schema para criação de favorito (apenas o produto_id é fornecido na entrada).
    """
    pass


class FavoritoResponse(BaseModel):
    """
    Schema para resposta de favorito (inclui detalhes do produto).
    """
    id: int
    cliente_id: int
    produto_id: int
    titulo: str
    imagem: str
    preco: float
    review: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
