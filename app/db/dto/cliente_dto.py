from typing import Type

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.db.models.cliente_model import Cliente


class ClienteDTO:
    def __init__(self, db: Session):
        """
        Inicializa o DTO (Data Transfer Object) responsável pela manipulação
        direta de registros da tavela 'clientes' no banco de dados.

        :param db: Sessão ativa do SQLAlchemy.
        """
        self.db = db
        self.logger = logger

    def pegar_por_id(self, cliente_id: int) -> Cliente | None:
        """
        Recupera um cliente a partir do seu ID único.

        :param cliente_id: Identificador do cliente.
        :return: Objeto Cliente ou None se não encontrado.
        """
        self.logger.debug(f"Obtendo cliente por ID: {cliente_id}")
        return self.db.query(Cliente).filter(Cliente.id == cliente_id).first()

    def pegar_por_email(self, email: str) -> Cliente | None:
        """
        Recupera um cliente com base em seu e-mail.

        :param email: E-mail do cliente.
        :return: Objeto Cliente ou None se não encontrado.
        """
        self.logger.debug(f"Obtendo cliente por e-mail: {email}")
        return self.db.query(Cliente).filter(Cliente.email == email).first()

    def pegar_todos(self, a_partir: int = 0, limite: int = 100) -> (
            list)[Type[Cliente]]:
        """
        Retorna uma lista paginada de clientes existentes no sistema.

        :param a_partir: Quantidade de registros a ignorar (offset).
        :param limite: Quantidade máxima de clientes a retornar.
        :return: Lista de objetos Cliente.
        """
        self.logger.debug(f"Obtendo todos os clientes com "
                          f"a_partir={a_partir}, limite={limite}")
        return self.db.query(Cliente).offset(a_partir).limit(limite).all()

    def registrar(self, cliente_data: dict) -> Cliente:
        """
        Cria um novo registro de cliente no banco de dados.

        :param cliente_data: Dicionário com os dados do cliente.
        :return: Objeto Cliente criado.
        :raises Exception: Em caso de erro na criação.
        """
        self.logger.info(f"Criando novo cliente com email: "
                         f"{cliente_data.get('email')}")
        try:
            db_cliente = Cliente(**cliente_data)
            self.db.add(db_cliente)
            self.db.commit()
            self.db.refresh(db_cliente)
            self.logger.info(f"Cliente criado com sucesso com "
                             f"ID: {db_cliente.id}")
            return db_cliente
        except Exception as e:
            self.logger.error(f"Erro ao criar cliente: {e}", exc_info=True)
            raise

    def atualizar(self, db_cliente: Cliente, data: dict) -> Cliente:
        """
        Atualiza os dados de um cliente existente com os campos fornecidos.

        :param db_cliente: Objeto Cliente existente.
        :param data: Dicionário com os campos a atualizar.
        :return: Objeto Cliente atualizado.
        :raises Exception: Em caso de erro na atualização.
        """
        self.logger.info(f"Atualizando cliente com ID: {db_cliente.id}")
        try:
            for key, value in data.items():
                setattr(db_cliente, key, value)
            self.db.add(db_cliente)
            self.db.commit()
            self.db.refresh(db_cliente)
            self.logger.info(f"Cliente atualizado com sucesso: "
                             f"{db_cliente.id}")
            return db_cliente
        except Exception as e:
            self.logger.error(f"Erro ao atualizar o ID do cliente "
                              f"{db_cliente.id}: {e}", exc_info=True)
            raise

    def deletar(self, cliente: Cliente) -> None:
        """
        Remove um cliente do banco de dados.

        :param cliente: Objeto Cliente a ser removido.
        :return: None.
        :raises Exception: Em caso de erro durante a exclusão.
        """
        self.logger.info(f"Excluindo cliente com ID: {cliente.id}")
        try:
            self.db.delete(cliente)
            self.db.commit()
            self.logger.info(f"Cliente excluído com sucesso: {cliente.id}")
        except Exception as e:
            self.logger.error(f"Erro ao excluir o ID "
                              f"do cliente {cliente.id}: {e}", exc_info=True)
            raise
