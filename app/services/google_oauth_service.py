import uuid

import jwt
from authlib.integrations.starlette_client import OAuth
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse

from app.api.domain.usuario_domain import UsusarioDomain
from app.api.schemas.usuario_schemas import UsuarioCreateSocial
from app.core.config import settings
from app.core.logger import logger
from app.db.models.base import pwd_context


class GoogleOAuthService:
    def __init__(self):
        """
        Serviço responsável por gerenciar o fluxo de autenticação com o Google OAuth.

        Registra o cliente OAuth utilizando as configurações fornecidas na aplicação.
        """
        self.oauth = OAuth()
        self.oauth.register(
            name='google',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url=settings.GOOGLE_METADATA_URI,
            client_kwargs={'scope': 'openid email profile'},
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        self.google_oauth_client = self.oauth.google
        self.logger = logger

    async def authorize_redirect(self, request: Request) -> RedirectResponse:
        """
        Inicia o fluxo de autenticação com Google OAuth,
        redirecionando o usuário para a página de login do Google.

        :param request: Objeto de requisição do FastAPI/Starlette.
        :return: Redirecionamento HTTP para o Google OAuth.
        """
        self.logger.info("Servico: iniciando o fluxo de login do Google OAuth.")
        return await self.google_oauth_client.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)

    async def handle_google_callback(self, request: Request, user_domain: UsusarioDomain):
        """
        Trata o retorno (callback) do Google após a autenticação do usuário.

        Decodifica as informações do token, obtém o e-mail e nome do usuário,
        e cria um novo usuário no sistema se ainda não existir.

        :param request: Objeto de requisição contendo o token de autenticação.
        :param user_domain: Domínio responsável pela lógica de criação de usuários.
        :return: Objeto do usuário autenticado (já existente ou recém-criado).
        :raises HTTPException: Em caso de falhas na autenticação ou ao obter dados do usuário.
        """
        self.logger.info("Servico: Tratamento de retorno de chamada do Google OAuth.")
        try:
            token = await self.google_oauth_client.authorize_access_token(request)

            self.logger.debug(f"Servico: resposta completa do token do Google: {token}")
            userinfo = token.get('userinfo')
            if not userinfo and 'id_token' in token:
                try:
                    userinfo = jwt.decode(token['id_token'],
                                          options={"verify_signature": False})
                    self.logger.warning("Servico: 'userinfo' não diretamente no token. "
                                        "Decodificado de 'id_token' manualmente.")
                except Exception as e:
                    self.logger.error(f"Servico: Falha ao decodificar manualmente"
                                      f" 'id_token': {e}", exc_info=True)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Erro ao decodificar ID Token do Google."
                    )
            elif not userinfo:
                self.logger.error("Servico: nem 'userinfo' nem 'id_token' "
                                  "foram encontrados/decodificados na resposta"
                                  " do Google OAuth.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Informações do usuário não obtidas na resposta do Google."
                )

            google_email = userinfo.get('email')
            google_name = userinfo.get('name', google_email.split('@')[0])

            if not google_email:
                self.logger.warning("Servico: falha no retorno de chamada do "
                                    "Google: nenhum e-mail obtido das "
                                    "informacoes do usuario.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Não foi possível obter o e-mail do Google."
                )

            fake_hashed_password = pwd_context.hash(str(uuid.uuid4()))

            user_create_social_data = UsuarioCreateSocial(
                email=google_email,
                hashed_password=fake_hashed_password,
                perfil="cliente"
            )

            user_db = await user_domain.criar_usuario_social(user_create_social_data, google_name)
            self.logger.info(f"Servico: Google OAuth bem-sucedido para "
                             f"o usuario: {user_db.email} (ID: {user_db.id})")

            return user_db

        except HTTPException as e:
            self.logger.error(f"Servico: HTTPException no retorno de "
                              f"chamada do Google OAuth: {e.detail}",
                              exc_info=True)
            raise e
        except Exception as e:
            self.logger.critical(f"Servico: erro nao tratado no retorno"
                                 f" de chamada do Google OAuth: {e}",
                                 exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro no processamento do login Google: {e}"
            )
