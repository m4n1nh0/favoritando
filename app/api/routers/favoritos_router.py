from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import pegar_usuario_atual
from app.api.schemas.favorito_schemas import FavoritoCreate, FavoritoResponse
from app.db.models.usuario_model import Usuario
from app.api.domain.favorito_domain import FavoritoDomain
from app.core.logger import logger
from app.util.metrics import FAVORITES_ADDED_TOTAL

router = APIRouter(
    prefix="/clientes/{cliente_id}/favoritos",
    tags=["favoritos"],
    responses={
        403: {"description": "Acesso negado."},
        404: {"description": "Cliente ou Favorito não encontrado."},
        409: {"description": "Produto já favoritado."}
    },
)


@router.post("/", response_model=FavoritoResponse,
             status_code=status.HTTP_201_CREATED)
async def criar_favorito(
        cliente_id: int,
        favorito_data: FavoritoCreate,
        db: Session = Depends(get_db),
        usuario_atual: Usuario = Depends(pegar_usuario_atual)
):
    """
    Adiciona um novo favorito à lista do cliente.

    - cliente_id: ID do cliente para quem será adicionado o favorito.
    - favorito_data: Dados do favorito a ser adicionado.
    - db: Sessão ativa com o banco de dados.
    - usuario_atual: Usuário autenticado fazendo a requisição.

    - return: Objeto do favorito recém-criado.
    """
    logger.info(f"Usuario {usuario_atual.id} adicionando favorito para o "
                f"ID do cliente {cliente_id}.")
    if (usuario_atual.perfil == "cliente" and
            usuario_atual.cliente_id != cliente_id):
        logger.warning(f"O cliente {usuario_atual.id} tentou adicionar "
                       f"favorito para outro cliente {cliente_id}.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clientes só podem adicionar favoritos à sua própria lista."
        )

    favorito_domain = FavoritoDomain(db)
    novo_favorito = await favorito_domain.adicionar_favorito(
        cliente_id, favorito_data)
    FAVORITES_ADDED_TOTAL.inc()
    return novo_favorito


@router.get("/", response_model=List[FavoritoResponse])
def ler_favoritos_por_cliente(
        cliente_id: int,
        a_partir: int = 0,
        db: Session = Depends(get_db),
        usuario_atual: Usuario = Depends(pegar_usuario_atual)
):
    """
    Retorna a lista de favoritos do cliente, com paginação opcional.

    - cliente_id: ID do cliente cujos favoritos serão listados.
    - a_partir: Índice inicial para paginação.
    - db: Sessão ativa com o banco de dados.
    - usuario_atual: Usuário autenticado fazendo a requisição.

    - return: Lista de favoritos do cliente.
    """
    logger.info(f"Usuario {usuario_atual.id} solicitando favoritos para o "
                f"ID do cliente {cliente_id}.")
    if usuario_atual.perfil == "cliente" and usuario_atual.cliente_id != cliente_id:
        logger.warning(f"O cliente {usuario_atual.id} tentou visualizar os "
                       f"favoritos de outro cliente {cliente_id}.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clientes só podem visualizar seus próprios favoritos."
        )

    favorito_domain = FavoritoDomain(db)
    favoritos = favorito_domain.favoritos_por_cliente(cliente_id, a_partir=a_partir)
    return favoritos


@router.get("/{favorito_id}", response_model=FavoritoResponse)
def ler_favorito_id(
        cliente_id: int,
        favorito_id: int,
        db: Session = Depends(get_db),
        usuario_atual: Usuario = Depends(pegar_usuario_atual)
):
    """
    Retorna um favorito específico do cliente.

    - cliente_id: ID do cliente dono do favorito.
    - favorito_id: ID do favorito a ser retornado.
    - db: Sessão ativa com o banco de dados.
    - usuario_atual: Usuário autenticado fazendo a requisição.

    - return: Objeto do favorito solicitado.
    """
    logger.info(f"Usuario {usuario_atual.id} solicitando favorito "
                f"{favorito_id} para o ID do cliente {cliente_id}.")
    if (usuario_atual.perfil == "cliente"
            and usuario_atual.cliente_id != cliente_id):
        logger.warning(
            f"O cliente {usuario_atual.id} tentou visualizar o "
            f"favorito {favorito_id} de outro cliente {cliente_id}.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clientes só podem visualizar seus próprios favoritos."
        )

    favorito_domain = FavoritoDomain(db)
    favorito = favorito_domain.favorito_por_id(cliente_id, favorito_id)
    if favorito is None:
        logger.warning(f"Favorito {favorito_id} nao encontrado ou "
                       f"não pertence ao cliente {cliente_id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Favorito não encontrado para "
                                   "este cliente.")
    return favorito


@router.delete("/{favorito_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_favorito_por_cliente(
        cliente_id: int,
        favorito_id: int,
        db: Session = Depends(get_db),
        usuario_atual: Usuario = Depends(pegar_usuario_atual)
):
    """
    Remove um favorito da lista do cliente.

    - cliente_id: ID do cliente dono do favorito.
    - favorito_id: ID do favorito a ser removido.
    - db: Sessão ativa com o banco de dados.
    - usuario_atual: Usuário autenticado fazendo a requisição.

    - return: Mensagem confirmando a remoção.
    """
    logger.info(f"Usuario {usuario_atual.id} tentando excluir o favorito "
                f"{favorito_id} para o ID do cliente {cliente_id}.")
    if usuario_atual.perfil == "cliente" and usuario_atual.cliente_id != cliente_id:
        logger.warning(
            f"O cliente {usuario_atual.id} tentou excluir o favorito "
            f"{favorito_id} de outro cliente {cliente_id}.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clientes só podem remover favoritos de sua própria lista."
        )

    favorito_domain = FavoritoDomain(db)
    success = favorito_domain.remove_favorito(cliente_id, favorito_id)
    if not success:
        logger.warning(f"Falha na exclusao: Favorito {favorito_id} nao "
                       f"encontrado ou nao pertence ao cliente {cliente_id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Favorito não encontrado para este cliente.")
    return {"message": "Favorito removido com sucesso."}
