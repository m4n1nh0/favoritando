from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.domain.cliente_domain import ClienteDomain
from app.api.schemas.cliente_schemas import (
    ClienteUpdate, ClienteResponse, ClienteCreateWithPassword)
from app.core.database import get_db
from app.core.logger import logger
from app.core.security import pegar_admin_atual

router = APIRouter(
    prefix="/clientes",
    tags=["clientes (Admin-only)"],
    dependencies=[Depends(pegar_admin_atual)],
    responses={
        403: {"description": "Acesso negado. Apenas administradores."},
        404: {"description": "Cliente não encontrado."}
    },
)


@router.post("/", response_model=ClienteResponse,
             status_code=status.HTTP_201_CREATED)
async def registrar_cliente(cliente_data: ClienteCreateWithPassword,
                            db: Session = Depends(get_db)):
    """
    Cria um novo cliente e um usuário de login associado para ele.

    - email: E-mail do cliente.
    - nome: Nome do cliente.
    - password: Senha para o usuário deste cliente (mínimo 8 caracteres).

    - return: Objeto do cliente criado, contendo ID, nome, e-mail e dados relacionados.
    """
    logger.info(f"Criação de cliente pelo usuario admin: "
                f"{cliente_data.email}")
    cliente_domain = ClienteDomain(db)

    return cliente_domain.registrar_cliente(cliente_data)


@router.get("/", response_model=List[ClienteResponse])
def listar_todos_clientes(a_partir: int = 0, limite: int = 100,
                          db: Session = Depends(get_db)):
    """
    Lista todos os clientes, com paginação opcional.

    - a_partir: Índice inicial para a listagem.
    - limite: Quantidade máxima de clientes a retornar.

    - return: Lista de objetos Cliente.
    """
    logger.info(f"Administrador solicitando todos os clientes "
                f"(a_partir={a_partir}, limit={limite}).")
    cliente_domain = ClienteDomain(db)
    clientes = cliente_domain.todos_clientes(a_partir=a_partir, limite=limite)
    return clientes


@router.get("/{cliente_id}", response_model=ClienteResponse)
def ler_cliente_por_id(cliente_id: int, db: Session = Depends(get_db)):
    """
    Retorna os dados do cliente correspondente ao ID informado.

    - cliente_id: ID do cliente.

    - return: Objeto Cliente com os dados do cliente.
    """
    logger.info(f"Administrador solicitando detalhes do "
                f"cliente para ID: {cliente_id}.")
    cliente_domain = ClienteDomain(db)
    db_client = cliente_domain.cliente_por_id(cliente_id=cliente_id)
    if db_client is None:
        logger.warning(f"Admin requested client ID {cliente_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cliente não encontrado.")
    return db_client


@router.put("/{cliente_id}", response_model=ClienteResponse)
def atualizar_cliente(cliente_id: int, cliente_update: ClienteUpdate,
                      db: Session = Depends(get_db)):
    """
    Atualiza os dados do cliente identificado pelo ID.

    - cliente_id: ID do cliente a ser atualizado.
    - cliente_update: Dados a serem atualizados no cliente.

    - return: Objeto Cliente atualizado.
    """
    logger.info(f"Administrador atualizando ID do cliente: {cliente_id}.")
    cliente_domain = ClienteDomain(db)
    db_cliente = cliente_domain.atualizar_cliente(cliente_id, cliente_update)
    if db_cliente is None:
        logger.warning(f"O administrador tentou atualizar um ID de "
                       f"cliente inexistente: {cliente_id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cliente não encontrado.")
    return db_cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """
    Remove o cliente identificado pelo ID.

    - cliente_id: ID do cliente a ser removido.

    - return: Mensagem de confirmação da remoção.
    """
    logger.info(f"Administrador excluindo ID do cliente: {cliente_id}.")
    cliente_domain = ClienteDomain(db)
    success = cliente_domain.deletar_cliente(cliente_id)
    if not success:
        logger.warning(f"O administrador tentou excluir um "
                       f"ID de cliente inexistente: {cliente_id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Cliente não encontrado.")
    return {"message": "Cliente removido com sucesso."}
