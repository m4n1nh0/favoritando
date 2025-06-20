from sqlalchemy.orm import Session

from app.core.logger import logger
from app.db.models.favorito_model import Favorito


class FavoritoDTO:
    def __init__(self, db: Session):
        """
        Inicializa o DTO (Data Transfer Object) responsável pelas operações
        diretas com a tabela de 'favoritos' no banco de dados.

        :param db: Sessão ativa do banco de dados.
        """
        self.db = db
        self.logger = logger

    def pegar_id(self, favorito_id: int) -> Favorito | None:
        """
        Busca um favorito pelo seu ID único.

        :param favorito_id: Identificador do favorito.
        :return: Objeto Favorito se encontrado, ou None.
        """
        self.logger.debug(f"Obtendo favorito por ID: {favorito_id}")
        return self.db.query(Favorito).filter(
            Favorito.id == favorito_id).first()

    def todos_por_cliente(
            self, cliente_id: int, a_partir: int = 0) -> list[Favorito]:
        """
        Retorna todos os favoritos de um cliente específico.

        :param cliente_id: ID do cliente.
        :param a_partir: A partir de qual registro iniciar.
        :return: Lista de objetos Favorito.
        """
        self.logger.debug(f"Obtendo favoritos para o ID do "
                          f"cliente {cliente_id} com a_partir={a_partir}")
        return self.db.query(Favorito).filter(
            Favorito.cliente_id == cliente_id).offset(a_partir).all()

    def por_cliente_produto_id(
            self, cliente_id: int, produto_id: int) -> Favorito | None:
        """
        Verifica se um produto já está na lista de favoritos de um cliente.

        :param cliente_id: ID do cliente.
        :param produto_id: ID do produto.
        :return: Objeto Favorito se encontrado, ou None.
        """
        self.logger.debug(f"Verificando favorito existente para ID do "
                          f"cliente {cliente_id}, ID do produto {produto_id}")
        return self.db.query(Favorito).filter(
            Favorito.cliente_id == cliente_id,
            Favorito.produto_id == produto_id
        ).first()

    def registrar(self, favorito_data: dict) -> Favorito:
        """
        Registra um favorito no banco de dados.

        :param favorito_data: Dicionário com os dados do favorito.
        :return: Objeto Favorito criado.
        :raises Exception: Em caso de erro durante a criação.
        """
        self.logger.info(
            f"Criando novo favorito para ID do cliente: "
            f"{favorito_data.get('cliente_id')}, ID do produto: "
            f"{favorito_data.get('produto_id')}")
        try:
            db_favorito = Favorito(**favorito_data)
            self.db.add(db_favorito)
            self.db.commit()
            self.db.refresh(db_favorito)
            self.logger.info(f"Favorito criado com sucesso "
                             f"com ID: {db_favorito.id}")
            return db_favorito
        except Exception as e:
            self.logger.error(f"Erro ao criar favorito: {e}", exc_info=True)
            raise

    def deletar(self, favorito: Favorito) -> None:
        """
        Remove um favorito do banco de dados.

        :param favorito: Objeto Favorito a ser removido.
        :return: None.
        :raises Exception: Em caso de falha na exclusão.
        """
        self.logger.info(f"Excluindo favorito com ID: {favorito.id}")
        try:
            self.db.delete(favorito)
            self.db.commit()
            self.logger.info(f"Favorito excluído com sucesso: {favorito.id}")
        except Exception as e:
            self.logger.error(f"Erro ao excluir o ID do "
                              f"favorito {favorito.id}: {e}", exc_info=True)
            raise
