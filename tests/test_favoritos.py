from fastapi.testclient import TestClient

from app.core.security import pegar_usuario_atual
from app.main import app
from app.db.models.usuario_model import Usuario

client = TestClient(app)


def fake_pegar_usuario_atual():
    return Usuario(id=10, perfil="cliente", cliente_id=1)


def test_criar_favorito_sucesso(mocker):
    mock_favorito = {
        "id": 101,
        "produto_id": 55,
        "cliente_id": 1,
        "created_at": "2025-06-20T11:00:00",
        "titulo": "Novo Produto",
        "imagem": "url_novo_produto.jpg",
        "preco": 150.0
    }

    async def fake_adicionar_favorito(cliente_id, favorito_data):
        return mock_favorito

    mocker.patch(
        "app.api.domain.favorito_domain.FavoritoDomain.adicionar_favorito",
        side_effect=fake_adicionar_favorito
    )

    app.dependency_overrides[pegar_usuario_atual] = fake_pegar_usuario_atual

    response = client.post(
        "/clientes/1/favoritos/",
        json={"produto_id": 55}
    )

    app.dependency_overrides = {}

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 101
    assert data["produto_id"] == 55
    assert data["cliente_id"] == 1
    assert data["titulo"] == "Novo Produto"


def test_ler_favorito_por_id_sucesso(mocker):
    mock_favorito = {
        "id": 100,
        "produto_id": 50,
        "cliente_id": 1,
        "created_at": "2025-06-20T10:00:00",
        "titulo": "Produto Teste",
        "imagem": "url_imagem_teste.jpg",
        "preco": 99.90
    }

    mocker.patch(
        "app.api.domain.favorito_domain.FavoritoDomain.favorito_por_id",
        return_value=mock_favorito
    )

    app.dependency_overrides[pegar_usuario_atual] = fake_pegar_usuario_atual

    response = client.get("/clientes/1/favoritos/100")

    app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 100
    assert data["titulo"] == "Produto Teste"


def test_ler_favorito_por_id_nao_autorizado(mocker):
    mocker.patch(
        "app.api.domain.favorito_domain.FavoritoDomain.favorito_por_id",
        return_value=None
    )

    def fake_usuario_outro_cliente():
        return Usuario(id=11, perfil="cliente", cliente_id=2)

    app.dependency_overrides[pegar_usuario_atual] = fake_usuario_outro_cliente

    response = client.get("/clientes/1/favoritos/100")

    app.dependency_overrides = {}

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Clientes só podem visualizar seus próprios favoritos."
    }


def test_deletar_favorito_sucesso(mocker):
    mocker.patch(
        "app.api.domain.favorito_domain.FavoritoDomain.remove_favorito",
        return_value=True
    )

    app.dependency_overrides[pegar_usuario_atual] = fake_pegar_usuario_atual

    response = client.delete("/clientes/1/favoritos/100")

    app.dependency_overrides = {}

    assert response.status_code == 204


def test_deletar_favorito_nao_autorizado(mocker):
    def fake_usuario_outro_cliente():
        return Usuario(id=11, perfil="cliente", cliente_id=2)

    app.dependency_overrides[pegar_usuario_atual] = fake_usuario_outro_cliente

    response = client.delete("/clientes/1/favoritos/100")

    app.dependency_overrides = {}

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Clientes só podem remover favoritos de sua própria lista."
    }


def test_deletar_favorito_nao_encontrado(mocker):
    mocker.patch(
        "app.api.domain.favorito_domain.FavoritoDomain.remove_favorito",
        return_value=False
    )

    app.dependency_overrides[pegar_usuario_atual] = fake_pegar_usuario_atual

    response = client.delete("/clientes/1/favoritos/999")

    app.dependency_overrides = {}

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Favorito não encontrado para este cliente."
    }
