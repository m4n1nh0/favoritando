from typing import List, Dict, Any

from fastapi import APIRouter, Depends

from app.core.logger import logger
from app.core.security import pegar_usuario_atual
from app.services.product_service import ProdutoService

router = APIRouter(
    prefix="/produtos",
    tags=["produtos"],
    dependencies=[Depends(pegar_usuario_atual)],
    responses={
        401: {"description": "Não autenticado"},
        403: {"description": "Acesso negado"},
        500: {"description": "Erro interno do servidor ou erro na API externa"}
    },
)


@router.get("/", response_model=List[Dict[str, Any]])
async def listar_produtos(
        produto_service: ProdutoService = Depends(ProdutoService)
):
    """
    Retorna a lista de produtos disponíveis.

    - produto_service: Serviço que realiza a chamada à API externa de produtos.

    - return: Lista de dicionários contendo informações dos produtos.
    """
    logger.info(f"Solicitacao para listar produtos")
    return await produto_service.pegar_produtos_api()


@router.get("/{produto_id}", response_model=Dict[str, Any])
async def produto_por_id(
        produto_id: int,
        produto_service: ProdutoService = Depends(ProdutoService)
):
    """
    Retorna os detalhes de um produto específico pelo seu ID.

    - produto_id: ID do produto a ser consultado.
    - produto_service: Serviço que realiza a chamada à API externa para buscar o produto.

    - return: Dicionário com as informações detalhadas do produto.
    """
    logger.info(f"Solicitacao para obter o produto por ID: {produto_id}.")
    return await produto_service.pegar_produto_por_id_api(produto_id)
