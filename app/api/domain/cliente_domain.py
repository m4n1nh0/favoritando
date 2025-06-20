from typing import List, Type

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.dto.cliente_dto import ClienteDTO
from app.db.dto.usuario_dto import UsuarioDTO
from app.db.models.base import pwd_context
from app.db.models.cliente_model import Cliente
from app.api.schemas.cliente_schemas import ClienteCreate, ClienteUpdate
from app.core.logger import logger


class ClienteDomain:
    def __init__(self, db: Session):
        """
        Inicializa o domínio responsável pela lógica de negócios relacionada a clientes.

        Este domínio atua como camada intermediária entre os esquemas (schemas) e os DTOs,
        orquestrando a criação, recuperação, atualização e exclusão de clientes.

        :param db: Sessão do banco de dados (SQLAlchemy Session).
        """
        self.cliente_dto = ClienteDTO(db)
        self.usuario_dto = UsuarioDTO(db)
        self.db = db
        self.logger = logger

    def registrar_cliente(self, cliente_data: ClienteCreate) -> Cliente:
        """
        Cria um novo cliente e um usuário associado com perfil 'cliente'.

        O cliente será criado com base nas informações fornecidas. Caso o e-mail já esteja
        vinculado a outro cliente, a operação será interrompida com erro HTTP 409.

        :param cliente_data: Dados do cliente a ser registrado.
        :return: Cliente data.
        :raises HTTPException: 409 se e-mail já estiver em uso, 500 em caso de erro interno.
        """
        self.logger.info(f"Administrador criando novo cliente com o "
                         f"usuário: {cliente_data.email}")
        cliente_existente = self.cliente_dto.pegar_por_email(
            cliente_data.email)
        if cliente_existente:
            self.logger.warning(f"Falha na criacao do cliente com usuario: "
                                f"Email {cliente_data.email} ja "
                                f"existe como cliente.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado para outro cliente."
            )

        cliente_existente = self.cliente_dto.pegar_por_email(
            cliente_data.email)
        if cliente_existente:
            self.logger.warning(f"Falha ao criar usuario: Email "
                                f"{cliente_data.email} email já existe.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já cadastrado para outro cliente."
            )
        try:
            cliente_data_dto = {"nome": cliente_data.nome,
                                "email": cliente_data.email}
            db_clientee = self.cliente_dto.registrar(cliente_data_dto)

            hashed_password = pwd_context.hash(cliente_data.password)
            user_create_data_dto = {
                "email": cliente_data.email,
                "hashed_password": hashed_password,
                "perfil": "cliente",
                "cliente_id": db_clientee.id
            }
            db_usuario = self.usuario_dto.registrar(user_create_data_dto)

            self.logger.info(f"Cliente {db_clientee.id} e "
                             f"Usuario {db_usuario.id} criado por admin.")
            return db_clientee
        except Exception as e:
            self.logger.error(f"Erro ao criar cliente independente "
                              f"{cliente_data.email}: {e}", exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar cliente: {e}"
            )

    def todos_clientes(self, a_partir: int = 0, limite: int = 100) -> (
            list)[Type[Cliente]]:
        """
        Recupera uma lista paginada de clientes existentes no sistema.

        :param a_partir: Quantidade de registros a pular (offset).
        :param limite: Quantidade máxima de clientes a retornar.
        :return: Lista de objetos Cliente.
        """
        self.logger.debug(f"Recuperando todos os clientes com "
                          f"skip={a_partir}, limite={limite}")
        return self.cliente_dto.pegar_todos(a_partir=a_partir, limite=limite)

    def cliente_por_id(self, cliente_id: int) -> Cliente | None:
        """
        Retorna um cliente a partir do seu ID único.

        Se o cliente não for encontrado, retorna None.

        :param cliente_id: Identificador do cliente.
        :return: Cliente correspondente ou None se não encontrado.
        """
        self.logger.debug(f"Pegando cliente por ID: {cliente_id}")
        return self.cliente_dto.pegar_por_id(cliente_id)

    def atualizar_cliente(
            self, cliente_id: int, cliente_update: ClienteUpdate) -> (
            Cliente | None):
        """
        Atualiza os dados de um cliente existente.

        Caso o e-mail seja alterado, atualiza também o e-mail do usuário vinculado.
        Se o novo e-mail estiver em uso por outro cliente, será lançado erro HTTP 409.

        :param cliente_id: ID do cliente a ser atualizado.
        :param cliente_update: Dados a serem atualizados.
        :return: Cliente atualizado ou None se não encontrado.
        :raises HTTPException: 409 se o novo e-mail já estiver em uso.
        """
        self.logger.info(f"Tentando atualizar o ID do cliente: {cliente_id}")
        db_cliente = self.cliente_dto.pegar_por_id(cliente_id)
        if not db_cliente:
            self.logger.warning(f"Falha na atualizacao: ID do cliente "
                                f"{cliente_id} não encontrado.")
            return None

        if cliente_update.email and cliente_update.email != db_cliente.email:
            cliente_existente_with_new_email = self.cliente_dto.pegar_por_email(
                cliente_update.email)
            if (cliente_existente_with_new_email and
                    cliente_existente_with_new_email.id != cliente_id):
                self.logger.warning(f"Falha na atualizacao: Novo e-mail "
                                    f"{cliente_update.email} ja em uso por "
                                    f"outro cliente.")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Novo e-mail já cadastrado para outro cliente."
                )

            db_usuario = self.usuario_dto.pegar_por_cliente_id(cliente_id)
            if db_usuario:
                self.logger.info(f"Atualizando email do usuario "
                                 f"associado do cliente {cliente_id}.")
                self.usuario_dto.aualizacao(
                    db_usuario, {"email": cliente_update.email})

        try:
            return self.cliente_dto.atualizar(
                db_cliente, cliente_update.model_dump(exclude_unset=True))
        except Exception as e:
            self.logger.error(f"Erro ao atualizar o ID do cliente "
                              f"{cliente_id}: {e}", exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao atualizar cliente: {e}"
            )

    def deletar_cliente(self, cliente_id: int) -> bool:
        """
        Exclui um cliente e, se houver, o usuário associado a ele.

        Caso o cliente não seja encontrado, retorna False. Em caso de erro durante
        a exclusão, lança erro HTTP 500.

        :param cliente_id: ID do cliente a ser removido.
        :return: True se excluído com sucesso, False se cliente não for encontrado.
        :raises HTTPException: 500 em caso de falha na exclusão.
        """
        self.logger.info(f"Tentando excluir ID do cliente: {cliente_id}")
        db_cliente = self.cliente_dto.pegar_por_id(cliente_id)
        if not db_cliente:
            self.logger.warning(f"Falha na exclusao: ID do cliente "
                                f"{cliente_id} nao encontrado.")
            return False

        try:
            db_usuario = self.usuario_dto.pegar_por_cliente_id(cliente_id)
            if db_usuario:
                self.logger.info(f"Excluindo usuario associado "
                                 f"{db_usuario.id} para cliente "
                                 f"{cliente_id}.")
                self.usuario_dto.deletar(db_usuario)
            else:
                self.logger.info(f"Nenhum usuario associado encontrado "
                                 f"para o cliente {cliente_id}. "
                                 f"Excluindo cliente diretamente.")
                self.cliente_dto.deletar(db_cliente)

            return True
        except Exception as e:
            self.logger.error(f"Erro ao excluir o ID do cliente "
                              f"{cliente_id}: {e}", exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao deletar cliente: {e}"
            )
