from conftest import id_categoria


def _despesa(cat, valor, data="2026-11-10", **extra):
    return {"tipo": "despesa", "valor": valor, "data": data, "id_categoria": cat, **extra}


def test_crud_orcamento(cliente, ana):
    mercado = id_categoria(cliente, ana, "Mercado")
    corpo = {"mes": 11, "ano": 2026, "valor": 80000, "id_categoria": mercado}

    r = cliente.post("/orcamentos/", headers=ana, json=corpo)
    assert r.status_code == 201
    orc = r.json()["id"]
    assert cliente.post("/orcamentos/", headers=ana, json=corpo).status_code == 409
    assert cliente.post("/orcamentos/", headers=ana, json={**corpo, "valor": 0}).status_code == 422

    assert cliente.get(f"/orcamentos/{orc}", headers=ana).json()["valor"] == 80000
    assert cliente.put(f"/orcamentos/{orc}", headers=ana, json={"valor": 90000}).json()["valor"] == 90000
    assert len(cliente.get("/orcamentos/?mes=11&ano=2026", headers=ana).json()) == 1

    assert cliente.delete(f"/orcamentos/{orc}", headers=ana).status_code == 204
    assert cliente.get(f"/orcamentos/{orc}", headers=ana).status_code == 404


def test_resumo_soma_conta_e_cartao_e_calcula_status(cliente, ana):
    mercado, lazer, saude = (id_categoria(cliente, ana, n) for n in ("Mercado", "Lazer", "Saúde"))
    cartao = cliente.post("/cartoes/", headers=ana, json={"nome": "Nubank", "dia_fechamento": 3}).json()["id"]

    for cat, valor in [(mercado, 100000), (lazer, 20000)]:
        cliente.post("/orcamentos/", headers=ana, json={"mes": 11, "ano": 2026, "valor": valor, "id_categoria": cat})

    lancamentos = [
        _despesa(mercado, 50000),  # pix
        _despesa(mercado, 35000, id_cartao=cartao),  # cartão também conta
        _despesa(lazer, 25000),  # estoura o limite de 200
        _despesa(saude, 7000),  # categoria sem orçamento
        _despesa(mercado, 99999, data="2026-12-01"),  # outro mês, não conta
        {"tipo": "receita", "valor": 500000, "data": "2026-11-05", "id_categoria": id_categoria(cliente, ana, "Salário")},
    ]
    for corpo in lancamentos:
        assert cliente.post("/transacoes/", headers=ana, json=corpo).status_code == 201

    r = cliente.get("/orcamentos/resumo?mes=11&ano=2026", headers=ana).json()
    itens = {i["nome_categoria"]: i for i in r["itens"]}

    assert itens["Mercado"]["valor_gasto"] == 85000 and itens["Mercado"]["status"] == "atencao"  # 85%
    assert itens["Lazer"]["valor_gasto"] == 25000 and itens["Lazer"]["status"] == "estourado"
    assert itens["Lazer"]["saldo"] == -5000
    assert r["total_orcado"] == 120000 and r["total_gasto"] == 110000
    assert r["gasto_fora_do_orcamento"] == 7000

    # O dashboard traz o mesmo resumo
    dash = cliente.get("/dashboard/?mes=11&ano=2026", headers=ana).json()
    assert dash["orcamento"]["total_gasto"] == 110000


def test_copiar_orcamento_para_o_mes_seguinte(cliente, ana):
    mercado, lazer = id_categoria(cliente, ana, "Mercado"), id_categoria(cliente, ana, "Lazer")
    for cat, valor in [(mercado, 100000), (lazer, 20000)]:
        cliente.post("/orcamentos/", headers=ana, json={"mes": 11, "ano": 2026, "valor": valor, "id_categoria": cat})
    # Lazer já tem orçamento em dezembro: não deve ser sobrescrito
    cliente.post("/orcamentos/", headers=ana, json={"mes": 12, "ano": 2026, "valor": 50000, "id_categoria": lazer})

    r = cliente.post("/orcamentos/copiar?de_mes=11&de_ano=2026&para_mes=12&para_ano=2026", headers=ana)
    assert r.status_code == 201 and len(r.json()) == 1

    dezembro = {o["id_categoria"]: o["valor"] for o in cliente.get("/orcamentos/?mes=12&ano=2026", headers=ana).json()}
    assert dezembro == {mercado: 100000, lazer: 50000}


def test_orcamento_isolado_entre_usuarios_e_mover_categoria(cliente, ana, bruno):
    lazer, outros = id_categoria(cliente, ana, "Lazer"), id_categoria(cliente, ana, "Outros")
    orc = cliente.post("/orcamentos/", headers=ana,
                       json={"mes": 11, "ano": 2026, "valor": 300, "id_categoria": lazer}).json()["id"]
    cliente.post("/orcamentos/", headers=ana, json={"mes": 11, "ano": 2026, "valor": 200, "id_categoria": outros})

    assert cliente.get(f"/orcamentos/{orc}", headers=bruno).status_code == 404
    assert cliente.get("/orcamentos/", headers=bruno).json() == []
    r = cliente.post("/orcamentos/", headers=bruno, json={"mes": 11, "ano": 2026, "valor": 1, "id_categoria": lazer})
    assert r.status_code == 404

    # Apagar "Lazer" movendo para "Outros" soma os limites do mês
    assert cliente.delete(f"/categorias/{lazer}?mover_para={outros}", headers=ana).status_code == 204
    orcs = cliente.get("/orcamentos/?mes=11&ano=2026", headers=ana).json()
    assert len(orcs) == 1 and orcs[0]["valor"] == 500
