from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.dto.usuario_dto import UsuarioDTO
from app.db.dto.cliente_dto import ClienteDTO
from app.db.models.usuario_model import Usuario
from app.db.models.base import pwd_context
from app.api.schemas.usuario_schemas import UsuarioCreate, UsuarioCreateSocial, UsuarioAdminCreate
from app.core.logger import logger


class UsusarioDomain:
    def __init__(self, db: Session):
        """
        Inicializa o domínio responsável pelas operações de usuários no sistema.

        Este domínio gerencia a criação, a checagem de autenticação e recuperação de usuários,
        incluindo o vínculo com clientes quando necessário.

        :param db: Sessão ativa do banco de dados (SQLAlchemy Session).
        """
        self.usuario_dto = UsuarioDTO(db)
        self.cliente_dto = ClienteDTO(db)
        self.db = db
        self.logger = logger

    async def criar_usuario(self, usuario_data: UsuarioCreate) -> Usuario:
        """
        Cria um novo usuário com perfil de cliente, incluindo o cliente vinculado.

        Caso o e-mail já esteja em uso, a criação é abortada com erro 409. Um nome
        padrão é gerado para o cliente com base no e-mail informado.

        :param usuario_data: Dados de cadastro do usuário.
        :return: Objeto Usuario criado com sucesso.
        :raises HTTPException: 409 se o e-mail já estiver em uso, 500 em caso de erro interno.
        """
        self.logger.info(f"Criando usuario: {usuario_data.email}")
        usuario_existente = self.usuario_dto.pegar_por_email(usuario_data.email)
        if usuario_existente:
            self.logger.warning(f"Falha ao criar usuario: "
                                f"Email {usuario_data.email} ja registrado.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado."
            )

        hashed_password = pwd_context.hash(usuario_data.password)
        user_create_data = {
            "email": usuario_data.email,
            "hashed_password": hashed_password,
            "perfil": "cliente"
        }

        try:
            cliente_data = {
                "nome": f"Cliente {usuario_data.email.split('@')[0]}",
                "email": usuario_data.email
            }
            db_cliente = self.cliente_dto.registrar(cliente_data)

            db_usuario = self.usuario_dto.registrar(user_create_data)
            db_usuario.cliente_id = db_cliente.id
            self.usuario_dto.db.add(db_usuario)
            self.usuario_dto.db.commit()
            self.usuario_dto.db.refresh(db_usuario)
            self.usuario_dto.db.refresh(db_cliente)

            self.logger.info(f"Usuario {db_usuario.id} criado com sucesso.")
            return db_usuario
        except Exception as e:
            self.logger.error(f"Erro ao criar usuario "
                              f"{usuario_data.email}: {e}", exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar usuário: {e}"
            )

    async def criar_por_admin(
            self, usuario_data: UsuarioAdminCreate) -> Usuario:
        """
        Cria usuário a partir de uma requisição feita por um perfil admin.

        Permite definir o perfil do usuário ('admin' ou 'cliente'), mas não
        vincula ou cria cliente automaticamente.

        :param usuario_data: Dados do novo usuário, incluindo o perfil desejado.
        :return: Objeto Usuario criado.
        :raises HTTPException: 409 se e-mail já estiver em uso, 500 em caso de falha interna.
        """
        self.logger.info(f"Administrador criando usuário: "
                         f"{usuario_data.email} com seguinte perfil "
                         f"{usuario_data.perfil}")

        usuario_existente = self.usuario_dto.pegar_por_email(usuario_data.email)
        if usuario_existente:
            self.logger.warning(f"Criacao de usuario deu errado: "
                                f"Email {usuario_data.email} já registrado.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado."
            )

        hashed_password = pwd_context.hash(usuario_data.password)
        user_create_data = {
            "email": usuario_data.email,
            "hashed_password": hashed_password,
            "perfil": usuario_data.perfil
        }

        try:
            db_usuario = self.usuario_dto.registrar(user_create_data)
            self.logger.info(f"Usuario {db_usuario.id} com perfil "
                             f"{db_usuario.perfil} criado pelo "
                             f"administrador.")
            return db_usuario
        except Exception as e:
            self.logger.error(f"Error creating user by admin for "
                              f"{usuario_data.email}: {e}", exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar usuário por admin: {e}"
            )

    async def criar_usuario_social(self, usuario_data: UsuarioCreateSocial,
                                   google_name: str) -> Usuario:
        """
        Cria ou atualiza um usuário que realiza login social via Google.

        Se o e-mail já estiver registrado para um perfil 'cliente', o login é
        permitido e o nome do cliente pode ser atualizado. Caso esteja vinculado a
        outro perfil, a criação será bloqueada.

        :param usuario_data: Dados recebidos da autenticação social (Google).
        :param google_name: Nome do usuário obtido do perfil do Google.
        :return: Objeto Usuario existente ou criado.
        :raises HTTPException: 409 se o e-mail pertencer a outro perfil, 500 em caso de erro.
        """
        self.logger.info(f"Criando usuario de rede "
                         f"social para: {usuario_data.email}")
        usuario_existente = self.usuario_dto.pegar_por_email(usuario_data.email)
        if usuario_existente:
            self.logger.info(f"Usuario {usuario_data.email} ja existe. "
                             f"Continuando com o login do usuário existente.")
            if usuario_existente.perfil != "cliente":
                self.logger.warning(f"Login social para {usuario_data.email} "
                                    f"negado: o usuário não é um 'cliente'.")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="E-mail já está em uso por um usuário não-cliente. "
                           "Login social não permitido."
                )
            if usuario_existente.cliente_id:
                db_client = self.cliente_dto.pegar_por_id(
                    usuario_existente.cliente_id)
                if db_client and db_client.nome != google_name:
                    self.logger.info(f"Atualizando o nome do cliente para o "
                                     f"usuário social existente "
                                     f"{usuario_existente.id}.")
                    self.cliente_dto.atualizar(db_client,
                                               {"nome": google_name,
                                               "email": usuario_data.email})
            return usuario_existente

        self.logger.info(f"Criando usaurio de rede social: "
                         f"{usuario_data.email}")
        user_create_data = {
            "email": usuario_data.email,
            "hashed_password": usuario_data.hashed_password,
            "perfil": usuario_data.perfil
        }

        try:
            cliente_data = {
                "nome": f"Cliente {usuario_data.email.split('@')[0]}",
                "email": usuario_data.email
            }
            db_cliente = self.cliente_dto.registrar(cliente_data)

            db_usuario = self.usuario_dto.registrar(user_create_data)
            db_usuario.cliente_id = db_cliente.id
            self.usuario_dto.db.add(db_usuario)
            self.usuario_dto.db.commit()
            self.usuario_dto.db.refresh(db_usuario)
            self.usuario_dto.db.refresh(db_cliente)

            self.logger.info(f"Usuario rede social {db_usuario.id} "
                             f"criado com sucesso.")
            return db_usuario
        except Exception as e:
            self.logger.error(f"Error in create_user_from_social for "
                              f"{usuario_data.email}: {e}", exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno ao criar usuário via login social: {e}"
            )

    def autenticar_usuario(
            self, email: str, password: str) -> Usuario | None:
        """
        Autentica um usuário a partir do e-mail e da senha fornecidos.

        Verifica se o usuário existe e se a senha está correta.

        :param email: E-mail do usuário.
        :param password: Senha fornecida para autenticação.
        :return: Objeto Usuario autenticado ou None se falhar.
        """
        self.logger.debug(f"Autenticando usuario: {email}")
        user = self.usuario_dto.pegar_por_email(email)
        if not user or not user.verify_password(password):
            self.logger.warning(f"Falha na autenticacao para o "
                                f"usuario: {email}")
            return None
        self.logger.info(f"Usuario {user.id} autenticado com sucesso.")
        return user

    def usuario_por_id(self, user_id: int) -> Usuario | None:
        """
        Recupera um usuário pelo seu ID numérico.

        :param user_id: Identificador único do usuário.
        :return: Objeto Usuario correspondente ou None se não encontrado.
        """
        self.logger.debug(f"Recuperando usuario por ID: {user_id}")
        return self.usuario_dto.usuario_por_id(user_id)
