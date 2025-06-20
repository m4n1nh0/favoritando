from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.api.domain.usuario_domain import UsusarioDomain
from app.api.schemas.auth_schemas import LoginRequest, Token
from app.api.schemas.usuario_schemas import (UsuarioCreate,
                                             UsuarioResponse,
                                             UsuarioAdminCreate)
from app.core.database import get_db
from app.core.logger import logger
from app.core.security import (criar_token_acesso,
                               ACCESS_TOKEN_EXPIRE_MINUTES,
                               pegar_usuario_atual,
                               pegar_admin_atual)
from app.db.models.usuario_model import Usuario
from app.services.google_oauth_service import GoogleOAuthService
from app.util.metrics import USERS_REGISTERED_TOTAL

router = APIRouter(
    prefix="/auth",
    tags=["autenticacao"]
)


@router.post("/registrar", response_model=UsuarioResponse,
             status_code=status.HTTP_201_CREATED)
async def registrar_usuario(
        user_in: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Registra um novo usuário via auto-serviço (público).
    Apenas para clintes e não para administradores.

    - email: E-mail único para o usuário.
    - password: Senha para o usuário (mínimo 8 caracteres).

    """
    logger.info(f"Registrando usuario publico (cliente): {user_in.email}")
    user_domain = UsusarioDomain(db)
    if user_in.perfil != "cliente":
        logger.warning(f"Tentativa de burlar tipo de persil: {user_in.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acao nao autorizada!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    new_user = await user_domain.criar_usuario(user_in)
    USERS_REGISTERED_TOTAL.inc()
    return new_user


@router.post("/admin_usuarios", response_model=UsuarioResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(pegar_admin_atual)])
async def registrar_usuario_por_admin(
        user_in: UsuarioAdminCreate, db: Session = Depends(get_db)
):
    """
    Cria um novo usuário (cliente ou admin) por um administrador.
    Usuários criados por esta rota não têm cliente associado automaticamente.

    - email: E-mail único para o usuário.
    - password: Senha para o usuário.
    - perfil: Perfil do usuário ('admin' ou 'cliente').

    - return: Objeto do usuário recém-criado, com ID, e-mail e perfil.
    """
    logger.info(f"Administrador criando um usuario: "
                f"{user_in.email} com perfil {user_in.perfil}")
    user_domain = UsusarioDomain(db)
    new_user = await user_domain.criar_por_admin(user_in)
    USERS_REGISTERED_TOTAL.inc()
    return new_user


@router.post("/logar", response_model=Token)
async def logar(
        request_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica um usuário com e-mail e senha, retornando um JWT de acesso.

    - email: E-mail do usuário.
    - password: Senha do usuário.

    - return: Token JWT contendo access_token, perfil e cliente_id.
    """
    logger.info(f"Tentativa de login do usuario: {request_data.email}")
    ususario_domain = UsusarioDomain(db)
    usuario_db = ususario_domain.autenticar_usuario(
        request_data.email, request_data.password)
    if not usuario_db:
        logger.warning(f"Falha de login para o usuario: {request_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": str(usuario_db.id),
        "perfil": usuario_db.perfil,
        "cliente_id": usuario_db.cliente_id
    }
    access_token = criar_token_acesso(
        token_data, expires_delta=access_token_expires
    )
    logger.info(f"Usuario {usuario_db.id} logado com sucesso.")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "perfil": usuario_db.perfil,
        "cliente_id": usuario_db.cliente_id
    }


@router.get("/me", response_model=UsuarioResponse)
async def pegar_usuario_atual(
        usuario_atual: Usuario = Depends(pegar_usuario_atual)):
    """
    Retorna as informações do usuário autenticado.

    - return: Objeto com os dados do usuário logado (ID, e-mail, perfil, cliente_id).
    """
    logger.debug(f"PEgando insormacao do usuario: {usuario_atual.id}")
    return usuario_atual


@router.get("/google/login")
async def google_login(request: Request):
    """
    Inicia o fluxo de login social com o Google.

    - return: Redirecionamento para a tela de consentimento do Google.
    """
    logger.info("Inciando login com Google.")
    google_oauth_service = GoogleOAuthService()
    return await google_oauth_service.authorize_redirect(request)


@router.get("/google/callback", response_model=Token)
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Manipula o retorno do login Google OAuth 2.0.

    Cria o usuário (se não existir) e retorna um token JWT.

    - return: Token JWT com access_token, perfil e cliente_id.
    """
    logger.info("Recebendo retono de login com Google.")
    google_oauth_service = GoogleOAuthService()
    usuario_domain = UsusarioDomain(db)
    try:
        usuario_db = await google_oauth_service.handle_google_callback(
            request, usuario_domain)

        if usuario_db.perfil != "cliente" or usuario_db.cliente_id is None:
            logger.warning(f"Falha no login do Google para o usuário "
                           f"{usuario_db.id}: não é um cliente ou não é "
                           f"client_id.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas usuarios com perfil 'cliente' "
                       "podem usar o login social."
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data = {
            "sub": str(usuario_db.id),
            "perfil": usuario_db.perfil,
            "cliente_id": usuario_db.cliente_id
        }
        access_token = criar_token_acesso(
            token_data, expires_delta=access_token_expires
        )
        logger.info(f"Login com Google realizado com suceso para o "
                    f"usuario {usuario_db.id}.")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "perfil": usuario_db.perfil,
            "cliente_id": usuario_db.cliente_id
        }

    except HTTPException as e:
        logger.error(f"Erro http durante retorno do "
                     f"Google: {e.detail}", exc_info=True)
        raise e
    except Exception as e:
        logger.critical(f"Erro desconhecido no retorno "
                        f"do Google: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro sem retono de chamada do Google OAuth. "
                   f"Tente novamente ou use o login tradicional."
        )
