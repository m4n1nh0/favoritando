from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UsuarioBase(BaseModel):
    email: EmailStr
    perfil: str = "cliente"


class UsuarioCreate(UsuarioBase):
    """
    Schama para criação de registro publico de clientes, pergil sempre 'cliente'
    """
    password: str = Field(..., min_length=8, description="Senha do usuário (mínimo 8 caracteres)")


class UsuarioAdminCreate(UsuarioCreate):
    """
    Schema para admin criar outros usuarios permitindo escolher perfil.
    """
    perfil: str = Field(..., pattern="^(admin|cliente)$", description="Perfil do usuário (admin ou cliente)")


class UsuarioCreateSocial(UsuarioBase):
    """
    Schema para criação de usuário a partir de login social.
    Não exige 'password', mas sim o 'hashed_password' já processado.
    """
    hashed_password: str


class UsuarioResponse(BaseModel):
    id: int
    email: EmailStr
    perfil: str
    cliente_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    usuario_id: Optional[int] = None
    perfil: Optional[str] = None
    cliente_id: Optional[int] = None
