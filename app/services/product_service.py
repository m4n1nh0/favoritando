import httpx
from fastapi import HTTPException, status
from typing import Dict, Any, List
from app.core.config import settings
from app.core.logger import logger


class ProdutoService:
    def __init__(self):
        self.logger = logger
        pass

    async def pegar_produtos_api(self) -> List[Dict[str, Any]]:
        self.logger.debug(f"Listando produtos a partir da API externa.")
        url = f"{settings.FAKE_STORE_API_BASE_URL}/products"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                dados_produto = response.json()
                self.logger.info(f"Produtos {len(dados_produto)} "
                                 f"obtidos da API externa.")
                return dados_produto
        except httpx.HTTPStatusError as e:
            self.logger.error(
                f"Erro HTTP ao buscar produtos da API externa: "
                f"{e.response.status_code} - {e.response.text}",
                exc_info=True)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Erro ao buscar produtos na API externa: {e.response.text}"
            )
        except httpx.RequestError as e:
            self.logger.critical(f"Erro de conexão com API externa ao buscar "
                                 f"produtos: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Não foi possível conectar à API externa de produtos: {e}"
            )

    async def pegar_produto_por_id_api(self, produto_id: int) -> Dict[str, Any]:
        self.logger.debug(f"Buscando o produto {produto_id} da API externa.")
        url = f"{settings.FAKE_STORE_API_BASE_URL}/products/{produto_id}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                dados_produto = response.json()
                self.logger.info(f"Produto {produto_id} obtido com sucesso da API externa.")
                return dados_produto
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"Produto {produto_id} não encontrado na API externa.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Produto com ID {produto_id} não encontrado na API externa."
                )
            self.logger.error(
                f"Erro HTTP ao buscar o produto {produto_id} da API externa: "
                f"{e.response.status_code} - {e.response.text}",
                exc_info=True)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Erro ao buscar produto na API externa: {e.response.text}"
            )
        except httpx.RequestError as e:
            self.logger.critical(f"Erro de conexão com a API externa ao "
                                 f"buscar o produto {produto_id}: {e}",
                                 exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Não foi possível conectar à API externa de produtos: {e}"
            )
