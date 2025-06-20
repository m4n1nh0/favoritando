from fastapi.testclient import TestClient

from app.core.security import pegar_admin_atual
from app.main import app

client = TestClient(app)


def fake_pegar_admin_atual():
    return {"username": "admin_teste"}


def test_registrar_cliente(mocker):
    cliente_mock = {
        "id": 1,
        "nome": "Cliente Teste",
        "email": "cliente@example.com",
        "created_at": "2025-06-19T12:00:00",
        "updated_at": None
    }
    mocker.patch(
        "app.api.domain.cliente_domain.ClienteDomain.registrar_cliente",
        return_value=cliente_mock
    )
    app.dependency_overrides[pegar_admin_atual] = fake_pegar_admin_atual

    cliente_data = {
        "nome": "Cliente Teste",
        "email": "cliente@example.com",
        "password": "senhaSegura123"
    }
    response = client.post("/clientes/", json=cliente_data)

    app.dependency_overrides = {}

    assert response.status_code == 201
    assert response.json() == cliente_mock


def test_listar_clientes(mocker):
    mocker.patch(
        "app.api.domain.cliente_domain.ClienteDomain.todos_clientes",
        return_value=[{
            "id": 1,
            "nome": "Cliente Teste",
            "email": "cliente@example.com",
            "created_at": "2025-06-19T12:00:00",
            "updated_at": None
        }]
    )

    app.dependency_overrides[pegar_admin_atual] = fake_pegar_admin_atual

    response = client.get("/clientes/")

    app.dependency_overrides = {}

    assert response.status_code == 200
    assert response.json() == [{
        "id": 1,
        "nome": "Cliente Teste",
        "email": "cliente@example.com",
        "created_at": "2025-06-19T12:00:00",
        "updated_at": None
    }]


def test_ler_cliente_por_id(mocker):
    cliente_mock = {
        "id": 1,
        "nome": "Cliente Teste",
        "email": "cliente@example.com",
        "created_at": "2025-06-19T12:00:00",
        "updated_at": None
    }
    mocker.patch(
        "app.api.domain.cliente_domain.ClienteDomain.cliente_por_id",
        return_value=cliente_mock
    )
    app.dependency_overrides[pegar_admin_atual] = fake_pegar_admin_atual

    response = client.get("/clientes/1")

    app.dependency_overrides = {}

    assert response.status_code == 200
    assert response.json() == cliente_mock


def test_atualizar_cliente(mocker):
    cliente_mock = {
        "id": 1,
        "nome": "Cliente Atualizado",
        "email": "cliente@example.com",
        "created_at": "2025-06-19T12:00:00",
        "updated_at": "2025-06-20T12:00:00"
    }
    mocker.patch(
        "app.api.domain.cliente_domain.ClienteDomain.atualizar_cliente",
        return_value=cliente_mock
    )
    app.dependency_overrides[pegar_admin_atual] = fake_pegar_admin_atual

    cliente_update = {
        "nome": "Cliente Atualizado"
    }
    response = client.put("/clientes/1", json=cliente_update)

    app.dependency_overrides = {}

    assert response.status_code == 200
    assert response.json() == cliente_mock


def test_deletar_cliente(mocker):
    mocker.patch(
        "app.api.domain.cliente_domain.ClienteDomain.deletar_cliente",
        return_value=True
    )
    app.dependency_overrides[pegar_admin_atual] = fake_pegar_admin_atual

    response = client.delete("/clientes/1")

    app.dependency_overrides = {}

    assert response.status_code == 204
    assert response.content == b""
