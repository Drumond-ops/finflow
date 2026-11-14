from conftest import id_categoria


def despesa(cat, valor=1000, data="2026-10-10", **extra):
    return {"tipo": "despesa", "valor": valor, "data": data, "id_categoria": cat, **extra}


# ==========================
# CATEGORIAS
# ==========================

def test_crud_categorias(cliente, ana):
    r = cliente.post("/categorias/", headers=ana, json={"nome": "Pets"})
    assert r.status_code == 201
    pets = r.json()["id"]

    assert cliente.post("/categorias/", headers=ana, json={"nome": "pets"}).status_code == 409  # repetida
    assert cliente.get(f"/categorias/{pets}", headers=ana).json()["nome"] == "Pets"

    r = cliente.put(f"/categorias/{pets}", headers=ana, json={"nome": "Animais"})
    assert r.status_code == 200 and r.json()["nome"] == "Animais"
    assert cliente.put(f"/categorias/{pets}", headers=ana, json={"nome": "Mercado"}).status_code == 409

    assert cliente.delete(f"/categorias/{pets}", headers=ana).status_code == 204
    assert cliente.get(f"/categorias/{pets}", headers=ana).status_code == 404


def test_apagar_categoria_em_uso_exige_mover(cliente, ana):
    lazer, outros = id_categoria(cliente, ana, "Lazer"), id_categoria(cliente, ana, "Outros")
    t = cliente.post("/transacoes/", headers=ana, json=despesa(lazer)).json()["id"]

    r = cliente.delete(f"/categorias/{lazer}", headers=ana)
    assert r.status_code == 409 and "mover_para" in r.json()["detail"]

    assert cliente.delete(f"/categorias/{lazer}?mover_para={outros}", headers=ana).status_code == 204
    assert cliente.get(f"/transacoes/{t}", headers=ana).json()["id_categoria"] == outros


def test_mover_categoria_soma_planejamentos_repetidos(cliente, ana):
    lazer, outros = id_categoria(cliente, ana, "Lazer"), id_categoria(cliente, ana, "Outros")
    cartao = cliente.post("/cartoes/", headers=ana, json={"nome": "Inter"}).json()["id"]
    for cat, valor in [(lazer, 300), (outros, 200)]:
        cliente.post("/planejamentos/", headers=ana,
                     json={"mes": 10, "ano": 2026, "valor": valor, "id_cartao": cartao, "id_categoria": cat})

    assert cliente.delete(f"/categorias/{lazer}?mover_para={outros}", headers=ana).status_code == 204
    planos = cliente.get("/planejamentos/?mes=10&ano=2026", headers=ana).json()
    assert len(planos) == 1 and planos[0]["valor"] == 500


# ==========================
# CARTÕES
# ==========================

def test_crud_cartoes(cliente, ana):
    r = cliente.post("/cartoes/", headers=ana, json={"nome": "Nubank", "dia_vencimento": 10, "dia_fechamento": 3})
    assert r.status_code == 201
    cartao = r.json()["id"]
    assert cliente.post("/cartoes/", headers=ana, json={"nome": "Nubank"}).status_code == 409
    assert cliente.post("/cartoes/", headers=ana, json={"nome": "X", "dia_vencimento": 40}).status_code == 422

    r = cliente.put(f"/cartoes/{cartao}", headers=ana, json={"nome": "Nubank Ultravioleta", "dia_vencimento": 15})
    assert r.json()["dia_vencimento"] == 15 and r.json()["dia_fechamento"] is None

    # Com compras registradas, não deixa apagar
    t = cliente.post("/transacoes/", headers=ana, json=despesa(id_categoria(cliente, ana), id_cartao=cartao)).json()
    assert cliente.delete(f"/cartoes/{cartao}", headers=ana).status_code == 409
    cliente.delete(f"/transacoes/{t['id']}", headers=ana)
    assert cliente.delete(f"/cartoes/{cartao}", headers=ana).status_code == 204


# ==========================
# TRANSAÇÕES
# ==========================

def test_crud_transacoes_e_filtros(cliente, ana):
    mercado, salario = id_categoria(cliente, ana, "Mercado"), id_categoria(cliente, ana, "Salário")
    cliente.post("/transacoes/", headers=ana, json=despesa(mercado, 2000, "2026-09-15"))
    t = cliente.post("/transacoes/", headers=ana, json=despesa(mercado, 3000, "2026-10-15")).json()
    cliente.post("/transacoes/", headers=ana,
                 json={"tipo": "receita", "valor": 500000, "data": "2026-10-05", "id_categoria": salario})

    todas = cliente.get("/transacoes/", headers=ana).json()
    assert [x["data"] for x in todas] == ["2026-10-15", "2026-10-05", "2026-09-15"]  # mais recente primeiro
    assert len(cliente.get("/transacoes/?mes=10&ano=2026", headers=ana).json()) == 2
    assert len(cliente.get("/transacoes/?tipo=receita", headers=ana).json()) == 1

    r = cliente.put(f"/transacoes/{t['id']}", headers=ana, json=despesa(mercado, 3500, "2026-10-16", descricao="Feira"))
    assert r.json()["valor"] == 3500 and r.json()["descricao"] == "Feira"

    assert cliente.delete(f"/transacoes/{t['id']}", headers=ana).status_code == 204
    assert cliente.get(f"/transacoes/{t['id']}", headers=ana).status_code == 404


def test_validacoes_de_transacao(cliente, ana):
    cat = id_categoria(cliente, ana)
    cartao = cliente.post("/cartoes/", headers=ana, json={"nome": "Nubank"}).json()["id"]
    assert cliente.post("/transacoes/", headers=ana, json=despesa(cat, valor=0)).status_code == 422
    receita_no_cartao = {"tipo": "receita", "valor": 10, "data": "2026-10-01", "id_categoria": cat, "id_cartao": cartao}
    assert cliente.post("/transacoes/", headers=ana, json=receita_no_cartao).status_code == 422
    assert cliente.post("/transacoes/", headers=ana, json=despesa(99999)).status_code == 404


# ==========================
# OBJETIVOS E APORTES
# ==========================

def test_objetivo_e_aportes_mantem_valores_consistentes(cliente, ana):
    obj = cliente.post("/objetivos/", headers=ana,
                       json={"nome": "Reserva", "valor_alvo": 100000, "valor_inicial": 10000}).json()
    assert obj["valor_atual"] == 10000 and obj["percentual_conclusao"] == 10.0

    ap = cliente.post("/aportes/", headers=ana, json={"valor": 5000, "data": "2026-10-01", "id_objetivo": obj["id"]})
    assert ap.status_code == 201
    ap = ap.json()
    assert cliente.get(f"/objetivos/{obj['id']}", headers=ana).json()["valor_atual"] == 15000

    # A despesa gerada caiu na categoria "Investimentos" e não pode ser editada direto
    t = cliente.get(f"/transacoes/{ap['id_transacao']}", headers=ana).json()
    assert t["id_categoria"] == id_categoria(cliente, ana, "Investimentos")
    assert cliente.delete(f"/transacoes/{t['id']}", headers=ana).status_code == 409

    # Editar o aporte ajusta objetivo e transação juntos
    cliente.put(f"/aportes/{ap['id']}", headers=ana, json={"valor": 8000, "data": "2026-10-02"})
    assert cliente.get(f"/objetivos/{obj['id']}", headers=ana).json()["valor_atual"] == 18000
    assert cliente.get(f"/transacoes/{t['id']}", headers=ana).json()["valor"] == 8000

    # Editar o objetivo recalcula valor_atual = inicial + aportes
    r = cliente.put(f"/objetivos/{obj['id']}", headers=ana,
                    json={"nome": "Reserva de emergência", "valor_alvo": 200000, "valor_inicial": 0})
    assert r.json()["valor_atual"] == 8000

    assert len(cliente.get(f"/objetivos/{obj['id']}/aportes", headers=ana).json()) == 1

    # Apagar o aporte desfaz tudo
    assert cliente.delete(f"/aportes/{ap['id']}", headers=ana).status_code == 204
    assert cliente.get(f"/objetivos/{obj['id']}", headers=ana).json()["valor_atual"] == 0
    assert cliente.get(f"/transacoes/{t['id']}", headers=ana).status_code == 404


def test_apagar_objetivo_mantem_despesas_dos_aportes(cliente, ana):
    obj = cliente.post("/objetivos/", headers=ana, json={"nome": "Carro", "valor_alvo": 1000}).json()
    ap = cliente.post("/aportes/", headers=ana, json={"valor": 100, "data": "2026-10-01", "id_objetivo": obj["id"]}).json()

    assert cliente.delete(f"/objetivos/{obj['id']}", headers=ana).status_code == 204
    assert cliente.get(f"/aportes/{ap['id']}", headers=ana).status_code == 404
    assert cliente.get(f"/transacoes/{ap['id_transacao']}", headers=ana).status_code == 200


# ==========================
# PLANEJAMENTOS
# ==========================

def test_crud_planejamentos(cliente, ana):
    cat = id_categoria(cliente, ana)
    cartao = cliente.post("/cartoes/", headers=ana, json={"nome": "Nubank"}).json()["id"]
    corpo = {"mes": 11, "ano": 2026, "valor": 150000, "id_cartao": cartao, "id_categoria": cat}

    r = cliente.post("/planejamentos/", headers=ana, json=corpo)
    assert r.status_code == 201
    plan = r.json()["id"]
    assert cliente.post("/planejamentos/", headers=ana, json=corpo).status_code == 409
    assert cliente.post("/planejamentos/", headers=ana, json={**corpo, "mes": 13}).status_code == 422

    assert cliente.put(f"/planejamentos/{plan}", headers=ana, json={"valor": 120000}).json()["valor"] == 120000
    assert len(cliente.get(f"/planejamentos/?id_cartao={cartao}", headers=ana).json()) == 1
    assert cliente.delete(f"/planejamentos/{plan}", headers=ana).status_code == 204
    assert cliente.get(f"/planejamentos/{plan}", headers=ana).status_code == 404
