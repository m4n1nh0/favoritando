from fastapi.testclient import TestClient
from app.core.security import pegar_usuario_atual

from app.main import app
from app.db.models.usuario_model import Usuario

client = TestClient(app)


def fake_pegar_usuario_atual():
    return Usuario(id=10, perfil="cliente", cliente_id=1)


def test_listar_produtos(mocker):
    mocker.patch(
        "app.services.product_service.ProdutoService.pegar_produtos_api",
        return_value=[{"id": 1, "nome": "Produto Teste"}]
    )

    app.dependency_overrides[pegar_usuario_atual] = fake_pegar_usuario_atual

    response = client.get("/produtos/")

    app.dependency_overrides = {}

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_produto_por_id(mocker):
    mocker.patch(
        "app.services.product_service.ProdutoService.pegar_produto_por_id_api",
        return_value={"id": 1, "nome": "Produto Teste", "descricao": "Descrição do produto"}
    )

    app.dependency_overrides[pegar_usuario_atual] = fake_pegar_usuario_atual

    response = client.get("/produtos/1")

    app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["nome"] == "Produto Teste"
    assert "descricao" in data
