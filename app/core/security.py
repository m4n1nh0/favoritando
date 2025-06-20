from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # Usaremos HTTPBearer
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.db.models.usuario_model import Usuario
from app.api.schemas.usuario_schemas import TokenData

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

http_bearer_scheme = HTTPBearer()


def criar_token_acesso(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Gera um token JWT para gerenciar a cessão web e liberar rotas.

    O token inclui a data de expiração e codificado.

    :param data: Dicionário com os dados a serem codificados no token.
    :param expires_delta: (Opcional) Tempo até a expiração do token.
    :return: String com o token JWT gerado.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def pegar_usuario_atual(
        credenciais: HTTPAuthorizationCredentials = Depends(http_bearer_scheme),
        db: Session = Depends(get_db)):
    """
    Decodifica o token JWT e retorna o usuário autenticado.

    A função valida o token, extrai o ID do usuário e o busca no banco de dados.

    :param credenciais: Credenciais extraídas do header Authorization (Bearer token).
    :param db: Sessão ativa do banco de dados.
    :return: Objeto Usuario autenticado.
    :raises HTTPException: 401 se o token for inválido, expirado ou o usuário não existir.
    """
    token = credenciais.credentials

    excessao_credencial = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais. Por favor, faça login.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise excessao_credencial

        usuario_id = int(user_id_str)
        cliente_id = int(payload.get("cliente_id")) if payload.get("cliente_id") else None

        token_data = TokenData(
            usuario_id=usuario_id,
            perfil=payload.get("perfil"),
            cliente_id=cliente_id
        )

    except jwt.exceptions.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido ou expirado. Detalhes: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError:
        raise excessao_credencial

    from app.db.dto.usuario_dto import UsuarioDTO
    user_dto = UsuarioDTO(db)
    user = user_dto.usuario_por_id(usuario_id=token_data.usuario_id)

    if user is None:
        raise excessao_credencial
    return user


async def pegar_admin_atual(usuario_atual: Usuario = Depends(pegar_usuario_atual)):
    """
    Checa se o usuário possui perfil de administrador.

    Usada como dependência em rotas que requerem permissão de admin.

    :param usuario_atual: Objeto Usuario previamente autenticado.
    :return: Objeto Usuario se for administrador.
    :raises HTTPException: 403 se o usuário não for admin.
    """
    if usuario_atual.perfil != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores podem realizar esta ação."
        )
    return usuario_atual
