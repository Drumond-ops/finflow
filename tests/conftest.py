"""
Configuração compartilhada dos testes (o pytest carrega este arquivo sozinho).

Por padrão os testes usam um SQLite em memória: rodam em segundos e não precisam do Docker.
Para rodar contra o Postgres de verdade, defina TEST_DATABASE_URL, por exemplo:
    TEST_DATABASE_URL=postgresql+psycopg2://admin_financas:senha@localhost:5432/finflow_testes pytest
(use um banco SEPARADO: os testes apagam todas as tabelas a cada teste!)
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app

URL_TESTE = os.getenv("TEST_DATABASE_URL", "sqlite://")

if URL_TESTE.startswith("sqlite"):
    engine_teste = create_engine(URL_TESTE, connect_args={"check_same_thread": False}, poolclass=StaticPool)

    # O SQLite vem com as chaves estrangeiras DESLIGADAS; ligamos para se comportar como o Postgres
    @event.listens_for(engine_teste, "connect")
    def _ligar_fk(conexao, _):
        conexao.execute("PRAGMA foreign_keys=ON")
else:
    engine_teste = create_engine(URL_TESTE)

SessaoTeste = sessionmaker(autocommit=False, autoflush=False, bind=engine_teste)


def get_db_teste():
    db = SessaoTeste()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def cliente():
    """Um cliente HTTP falso ligado à API, com o banco zerado a cada teste."""
    Base.metadata.drop_all(bind=engine_teste)
    Base.metadata.create_all(bind=engine_teste)
    app.dependency_overrides[get_db] = get_db_teste
    yield TestClient(app)
    app.dependency_overrides.clear()


def criar_conta(cliente, email="ana@exemplo.com", senha="senha123", nome="Ana") -> dict:
    """Registra um usuário, faz login e devolve o cabeçalho Authorization pronto para usar."""
    r = cliente.post("/auth/registro", json={"nome": nome, "email": email, "senha": senha})
    assert r.status_code == 201, r.text
    r = cliente.post("/auth/login", data={"username": email, "password": senha})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def id_categoria(cliente, headers, nome="Mercado") -> int:
    """Pega o id de uma das categorias padrão criadas no registro."""
    categorias = cliente.get("/categorias/", headers=headers).json()
    return next(c["id"] for c in categorias if c["nome"] == nome)


@pytest.fixture()
def ana(cliente):
    return criar_conta(cliente)


@pytest.fixture()
def bruno(cliente):
    return criar_conta(cliente, email="bruno@exemplo.com", nome="Bruno")
