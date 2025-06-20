from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.dto.favorito_dto import FavoritoDTO
from app.db.dto.cliente_dto import ClienteDTO
from app.db.models.favorito_model import Favorito
from app.api.schemas.favorito_schemas import FavoritoCreate
from app.services.product_service import ProdutoService
from app.core.logger import logger


class FavoritoDomain:
    def __init__(self, db: Session):
        """
        Inicializa o domínio responsável pela lógica de favoritos de produtos.

        Este domínio gerencia o relacionamento entre clientes e produtos favoritos,
        interagindo com DTOs, serviços externos e banco de dados.

        :param db: Sessão ativa do banco de dados (SQLAlchemy Session).
        """
        self.favorito_dto = FavoritoDTO(db)
        self.cliente_dto = ClienteDTO(db)
        self.produto_service = ProdutoService()
        self.db = db
        self.logger = logger

    async def adicionar_favorito(
            self, cliente_id: int, favorito_data: FavoritoCreate) -> Favorito:
        """
        Adiciona um novo produto à lista de favoritos de um cliente.

        Valida a existência do cliente e se o produto já está favoritado. Em caso
        positivo, impede a duplicação. Também consulta uma API externa para obter
        os detalhes do produto antes de salvar.

        :param cliente_id: ID do cliente que está favoritando o produto.
        :param favorito_data: Dados do produto a ser favoritado (ID do produto).
        :return: Objeto Favorito criado.
        :raises HTTPException: 404 se cliente não existir, 409 se produto já for favorito,
                               500 em caso de erro interno.
        """
        self.logger.info(f"Tentando adicionar favorito para ID "
                         f"do cliente {cliente_id}, ID do produto "
                         f"{favorito_data.produto_id}")
        db_cliente = self.cliente_dto.pegar_por_id(cliente_id)
        if not db_cliente:
            self.logger.warning(f"Falha ao adicionar favorito: ID do cliente "
                                f"{cliente_id} não encontrado.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Cliente não encontrado.")

        existe_favorito = self.favorito_dto.por_cliente_produto_id(
            cliente_id, favorito_data.produto_id)
        if existe_favorito:
            self.logger.warning(
                f"Falha ao adicionar favorito: Produto "
                f"{favorito_data.produto_id} ja favorito pelo "
                f"cliente {cliente_id}.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este produto já está na lista de "
                       "favoritos do cliente."
            )

        try:
            produto_detalhes = \
                await self.produto_service.pegar_produto_por_id_api(
                    favorito_data.produto_id)
        except HTTPException as e:
            self.logger.error(
                f"Falha ao buscar detalhes do produto da API externa para o "
                f"ID do produto {favorito_data.produto_id}: {e.detail}")
            raise e

        favorito_data_registro = {
            "cliente_id": cliente_id,
            "produto_id": favorito_data.produto_id,
            "titulo": produto_detalhes.get("title"),
            "imagem": produto_detalhes.get("image"),
            "preco": produto_detalhes.get("price"),
            "review": produto_detalhes.get("description", "")
        }

        try:
            db_favorito = self.favorito_dto.registrar(favorito_data_registro)
            self.logger.info(f"Favorito {db_favorito.id} adicionado com "
                             f"sucesso para o cliente {cliente_id}.")
            return db_favorito
        except Exception as e:
            self.logger.error(f"Erro ao adicionar favorito para cliente "
                              f"{cliente_id}, produto "
                              f"{favorito_data.produto_id}: {e}",
                              exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao adicionar favorito: {e}"
            )

    def favoritos_por_cliente(
            self, cliente_id: int, a_partir: int = 0) -> list[Favorito]:
        """
        Retorna todos os produtos favoritados por um cliente.

        A busca pontuada para ignorar registros a partir do codigo em skip.

        :param cliente_id: ID do cliente a ser consultado.
        :param a_partir: A partir de qual favorito vem a lista.
        :return: Lista de objeto Favorito.
        :raises HTTPException: 404 se o cliente não existir.
        """
        self.logger.debug(f"Recuperando favoritos para o ID "
                          f"do cliente {cliente_id}.")
        db_cliente = self.cliente_dto.pegar_por_id(cliente_id)
        if not db_cliente:
            self.logger.warning(f"Falha ao obter favoritos: ID do cliente "
                                f"{cliente_id} nao encontrado.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Cliente não encontrado.")
        return self.favorito_dto.todos_por_cliente(cliente_id, a_partir=a_partir)

    def favorito_por_id(self, cliente_id: int, favorite_id: int) -> Favorito | None:
        """
        Busca um favorito específico de um cliente pelo ID do favorito.

        Valida se o favorito pertence ao cliente indicado.

        :param cliente_id: ID do cliente.
        :param favorite_id: ID do favorito.
        :return: Objeto Favorito se encontrado e pertencente ao cliente, ou None.
        """
        self.logger.debug(f"Recuperando o favorito {favorite_id} para o ID "
                          f"do cliente {cliente_id}.")
        favorite = self.favorito_dto.pegar_id(favorite_id)
        if favorite and favorite.cliente_id == cliente_id:
            return favorite
        self.logger.warning(f"Favorito {favorite_id} nao encontrado ou nao "
                            f"pertence ao cliente {cliente_id}.")
        return None

    def remove_favorito(self, cliente_id: int, favorito_id: int) -> bool:
        """
        Remove um produto da lista de favoritos de um cliente.

        Verifica se o favorito existe e se pertence ao cliente antes de excluir.

        :param cliente_id: ID do cliente.
        :param favorito_id: ID do favorito a ser removido.
        :return: True se a remoção foi realizada com sucesso, False se não encontrado ou inválido.
        :raises HTTPException: 500 em caso de falha na exclusão.
        """
        self.logger.info(f"Tentativa de remover o favorito {favorito_id} "
                         f"do ID do cliente {cliente_id}.")
        db_favorito = self.favorito_dto.pegar_id(favorito_id)
        if not db_favorito or db_favorito.cliente_id != cliente_id:
            self.logger.warning(
                f"Falha na remoção do favorito: Favorito {favorito_id} não "
                f"encontrado ou nao pertence ao cliente {cliente_id}.")
            return False

        try:
            self.favorito_dto.deletar(db_favorito)
            self.logger.info(f"Favorito {favorito_id} removido com sucesso "
                             f"para o cliente {cliente_id}.")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao remover o favorito {favorito_id} "
                              f"do cliente {cliente_id}: {e}", exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao remover favorito: {e}"
            )
