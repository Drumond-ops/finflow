from conftest import id_categoria


def _cenario(cliente, h):
    """Outubro/2026: salário 5.000, mercado no pix 300, cartão com 400 de mercado + 100 de lazer."""
    mercado, lazer, salario = (id_categoria(cliente, h, n) for n in ("Mercado", "Lazer", "Salário"))
    cartao = cliente.post("/cartoes/", headers=h, json={"nome": "Nubank"}).json()["id"]

    lancamentos = [
        {"tipo": "receita", "valor": 500000, "data": "2026-10-05", "id_categoria": salario},
        {"tipo": "despesa", "valor": 30000, "data": "2026-10-06", "id_categoria": mercado},
        {"tipo": "despesa", "valor": 40000, "data": "2026-10-07", "id_categoria": mercado, "id_cartao": cartao},
        {"tipo": "despesa", "valor": 10000, "data": "2026-10-08", "id_categoria": lazer, "id_cartao": cartao},
        {"tipo": "despesa", "valor": 99999, "data": "2026-11-01", "id_categoria": lazer},  # outro mês
    ]
    for corpo in lancamentos:
        assert cliente.post("/transacoes/", headers=h, json=corpo).status_code == 201

    cliente.post("/planejamentos/", headers=h,
                 json={"mes": 10, "ano": 2026, "valor": 50000, "id_cartao": cartao, "id_categoria": mercado})
    return cartao, mercado, lazer


def test_fatura_compara_planejado_com_gasto(cliente, ana):
    cartao, mercado, _ = _cenario(cliente, ana)
    f = cliente.get(f"/cartoes/{cartao}/fatura/?mes=10&ano=2026", headers=ana).json()

    assert f["valor_total"] == 50000
    assert f["valor_planejado"] == 50000
    item = f["detalhes_por_categoria"][0]
    assert item["id_categoria"] == mercado and item["valor_gasto"] == 40000 and item["saldo"] == 10000
    assert item["percentual"] == 80.0


def test_dashboard(cliente, ana):
    _, mercado, lazer = _cenario(cliente, ana)
    d = cliente.get("/dashboard/?mes=10&ano=2026", headers=ana).json()

    assert d["total_receitas"] == 500000
    assert d["total_despesas"] == 30000  # só fora do cartão
    assert d["total_faturas"] == 50000
    assert d["saldo_mes"] == 500000 - 30000 - 50000
    # gastos por categoria agora incluem o cartão, do maior para o menor
    assert [(g["id_categoria"], g["valor_gasto"]) for g in d["gastos_categoria"]] == [(mercado, 70000), (lazer, 10000)]
    assert d["resumo_transacao"][0]["data"] == "2026-11-01"  # mais recente primeiro


def test_dashboard_valida_mes(cliente, ana):
    assert cliente.get("/dashboard/?mes=13&ano=2026", headers=ana).status_code == 422


def test_relatorio_pdf(cliente, ana):
    _cenario(cliente, ana)
    r = cliente.get("/relatorios/pdf?mes=10&ano=2026", headers=ana)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
