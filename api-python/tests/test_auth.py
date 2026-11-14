from conftest import criar_conta


def test_registro_cria_usuario_e_categorias_padrao(cliente):
    r = cliente.post("/auth/registro", json={"nome": "Ana", "email": "Ana@Exemplo.com", "senha": "senha123"})
    assert r.status_code == 201
    assert r.json()["email"] == "ana@exemplo.com"  # e-mail normalizado
    assert "senha" not in r.json() and "senha_hash" not in r.json()

    login = cliente.post("/auth/login", data={"username": "ana@exemplo.com", "password": "senha123"})
    token = login.json()["access_token"]
    categorias = cliente.get("/categorias/", headers={"Authorization": f"Bearer {token}"}).json()
    assert {"Mercado", "Investimentos", "Salário"} <= {c["nome"] for c in categorias}


def test_email_repetido_da_409(cliente):
    criar_conta(cliente)
    r = cliente.post("/auth/registro", json={"nome": "X", "email": "ana@exemplo.com", "senha": "outra123"})
    assert r.status_code == 409


def test_email_invalido_e_senha_curta_dao_422(cliente):
    assert cliente.post("/auth/registro", json={"nome": "X", "email": "nao-e-email", "senha": "senha123"}).status_code == 422
    assert cliente.post("/auth/registro", json={"nome": "X", "email": "x@x.com", "senha": "123"}).status_code == 422


def test_login_com_senha_errada_da_401(cliente):
    criar_conta(cliente)
    r = cliente.post("/auth/login", data={"username": "ana@exemplo.com", "password": "errada"})
    assert r.status_code == 401
    r = cliente.post("/auth/login", data={"username": "ninguem@exemplo.com", "password": "senha123"})
    assert r.status_code == 401


def test_rotas_protegidas_exigem_token(cliente):
    assert cliente.get("/transacoes/").status_code == 401
    assert cliente.get("/dashboard/?mes=10&ano=2026").status_code == 401
    assert cliente.get("/categorias/", headers={"Authorization": "Bearer token-falso"}).status_code == 401


def test_me_atualizar_e_trocar_senha(cliente, ana):
    assert cliente.get("/usuarios/me", headers=ana).json()["nome"] == "Ana"

    r = cliente.put("/usuarios/me", headers=ana, json={"nome": "Ana Clara", "email": "ana.clara@exemplo.com"})
    assert r.status_code == 200 and r.json()["nome"] == "Ana Clara"

    r = cliente.put("/usuarios/me/senha", headers=ana, json={"senha_atual": "errada", "nova_senha": "nova12345"})
    assert r.status_code == 400
    r = cliente.put("/usuarios/me/senha", headers=ana, json={"senha_atual": "senha123", "nova_senha": "nova12345"})
    assert r.status_code == 204

    login = cliente.post("/auth/login", data={"username": "ana.clara@exemplo.com", "password": "nova12345"})
    assert login.status_code == 200


def test_apagar_conta_apaga_tudo_em_cascata(cliente, ana):
    from conftest import id_categoria

    cat = id_categoria(cliente, ana)
    cartao = cliente.post("/cartoes/", headers=ana, json={"nome": "Nubank"}).json()
    cliente.post("/transacoes/", headers=ana, json={"tipo": "despesa", "valor": 100, "data": "2026-10-01",
                                                    "id_categoria": cat, "id_cartao": cartao["id"]})
    cliente.post("/planejamentos/", headers=ana, json={"mes": 10, "ano": 2026, "valor": 1000,
                                                       "id_cartao": cartao["id"], "id_categoria": cat})
    obj = cliente.post("/objetivos/", headers=ana, json={"nome": "Viagem", "valor_alvo": 100000}).json()
    cliente.post("/aportes/", headers=ana, json={"valor": 500, "data": "2026-10-02", "id_objetivo": obj["id"]})

    assert cliente.delete("/usuarios/me", headers=ana).status_code == 204
    assert cliente.get("/usuarios/me", headers=ana).status_code == 401  # o token não serve mais
    assert cliente.post("/auth/login", data={"username": "ana@exemplo.com", "password": "senha123"}).status_code == 401
