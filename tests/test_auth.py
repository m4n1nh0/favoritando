from datetime import datetime

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import pegar_admin_atual, pegar_usuario_atual
from app.db.models.usuario_model import Usuario
from app.main import app

client = TestClient(app)


def test_register_user_success(mocker):
    mock_user = {
        "id": 1,
        "email": "teste@example.com",
        "perfil": "cliente",
        "cliente_id": 123,
        "created_at": datetime.utcnow().isoformat()
    }

    mocker.patch(
        "app.api.domain.usuario_domain.UsusarioDomain.criar_usuario",
        return_value=mock_user
    )

    response = client.post("/auth/registrar", json={
        "email": "teste@example.com",
        "password": "12345678",
        "perfil": "cliente"
    })

    assert response.status_code == 201


def test_registrar_usuario_com_perfil_invalido():
    response = client.post("/auth/registrar", json={
        "email": "admin@teste.com",
        "password": "12345678",
        "perfil": "admin"
    })

    assert response.status_code == 401
    assert response.json()["detail"] == "Acao nao autorizada!"


def test_registrar_usuario_por_admin(mocker):
    mock_usuario = {
        "id": 1,
        "email": "novo@teste.com",
        "perfil": "cliente",
        "cliente_id": None,
        "created_at": datetime.utcnow().isoformat()
    }

    mock_domain_instance = mocker.MagicMock()
    mock_domain_instance.criar_por_admin = mocker.AsyncMock(return_value=mock_usuario)

    mocker.patch("app.api.routers.auth_router.UsusarioDomain", return_value=mock_domain_instance)

    def fake_admin():
        return Usuario(id=1, email="admin@teste.com", perfil="admin")

    def fake_db():
        yield mocker.MagicMock()

    app.dependency_overrides[pegar_admin_atual] = fake_admin
    app.dependency_overrides[get_db] = fake_db

    response = client.post("/auth/admin_usuarios", json={
        "email": "novo@teste.com",
        "password": "12345678",
        "perfil": "cliente"
    })

    assert response.status_code == 201
    assert response.json()["email"] == "novo@teste.com"


def test_logar_usuario_sucesso(mocker):
    mock_usuario = Usuario(id=1, email="cliente@teste.com", perfil="cliente", cliente_id=1)
    mock_domain = mocker.MagicMock()
    mock_domain.autenticar_usuario.return_value = mock_usuario

    mocker.patch("app.api.routers.auth_router.UsusarioDomain", return_value=mock_domain)

    def fake_db():
        yield mocker.MagicMock()
    app.dependency_overrides[get_db] = fake_db

    response = client.post("/auth/logar", json={
        "email": "cliente@teste.com",
        "password": "12345678"
    })

    app.dependency_overrides = {}

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["perfil"] == "cliente"
    assert data["cliente_id"] == 1


def test_logar_usuario_falha(mocker):
    mock_domain = mocker.MagicMock()
    mock_domain.autenticar_usuario.return_value = None

    mocker.patch("app.api.routers.auth_router.UsusarioDomain", return_value=mock_domain)

    def fake_db():
        yield mocker.MagicMock()

    app.dependency_overrides[get_db] = fake_db

    response = client.post("/auth/logar", json={
        "email": "cliente@teste.com",
        "password": "senhaerrada"
    })

    app.dependency_overrides = {}

    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha incorretos."


def test_pegar_usuario_atual():
    def fake_usuario():
        return Usuario(
            id=1,
            email="cliente@teste.com",
            perfil="cliente",
            cliente_id=1,
            created_at=datetime.utcnow()
        )

    app.dependency_overrides[pegar_usuario_atual] = fake_usuario

    try:
        response = client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "cliente@teste.com"
    finally:
        app.dependency_overrides = {}
