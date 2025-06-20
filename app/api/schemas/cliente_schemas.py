from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class ClienteCreate(BaseModel):
    """
    Schema para admins criarem clientes diretamente.
    """
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr


class ClienteCreateWithPassword(ClienteCreate):
    password: str = Field(..., min_length=8,
                          description="Senha do usuário para o novo cliente (mínimo 8 caracteres)")


class ClienteUpdate(BaseModel):
    """
    Schema para atualização de cliente (campos opcionais).
    """
    nome: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None


class ClienteResponse(BaseModel):
    """
    Schema para resposta de cliente.
    """
    id: int
    nome: str
    email: EmailStr
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
