"""Marcar a fatura do cartão como paga (tabela faturas_pagas)."""
from conftest import id_categoria


def _cartao_com_compra(cliente, headers, valor=10000, data="2026-11-02"):
    """Cartão que fecha dia 3 e vence dia 10, com uma compra que cai na fatura de novembro."""
    cartao = cliente.post(
        "/cartoes/", headers=headers, json={"nome": "Nubank", "dia_fechamento": 3, "dia_vencimento": 10}
    ).json()["id"]
    cliente.post("/transacoes/", headers=headers, json={
        "tipo": "despesa", "valor": valor, "data": data, "id_categoria": id_categoria(cliente, headers), "id_cartao": cartao,
    })
    return cartao


def test_marcar_e_desmarcar_fatura_paga(cliente, ana):
    cartao = _cartao_com_compra(cliente, ana)
    url = f"/cartoes/{cartao}/fatura/pagamento?mes=11&ano=2026"

    antes = cliente.get(f"/cartoes/{cartao}/fatura/?mes=11&ano=2026", headers=ana).json()
    assert antes["paga"] is False and antes["data_pagamento"] is None

    r = cliente.post(url, headers=ana, json={"data_pagamento": "2026-11-09"})
    assert r.status_code == 200, r.text
    assert r.json()["paga"] is True
    assert r.json()["data_pagamento"] == "2026-11-09"
    assert r.json()["valor_pago"] == 10000

    # O painel mostra a fatura como paga, mas o saldo do mês NÃO muda (a fatura já era descontada)
    painel = cliente.get("/dashboard/?mes=11&ano=2026", headers=ana).json()
    assert painel["faturas"][0]["paga"] is True
    assert painel["total_faturas"] == 10000

    assert cliente.delete(url, headers=ana).status_code == 204
    assert cliente.get(f"/cartoes/{cartao}/fatura/?mes=11&ano=2026", headers=ana).json()["paga"] is False
    assert cliente.delete(url, headers=ana).status_code == 404  # já não estava paga


def test_sem_data_usa_hoje_e_pagar_de_novo_atualiza(cliente, ana):
    cartao = _cartao_com_compra(cliente, ana)
    url = f"/cartoes/{cartao}/fatura/pagamento?mes=11&ano=2026"

    r = cliente.post(url, headers=ana)  # sem corpo
    assert r.status_code == 200, r.text
    assert r.json()["data_pagamento"] is not None

    r = cliente.post(url, headers=ana, json={"data_pagamento": "2026-11-10"})
    assert r.json()["data_pagamento"] == "2026-11-10"  # não cria um segundo registro, atualiza o mesmo


def test_compra_depois_do_pagamento_deixa_valor_pago_diferente(cliente, ana):
    cartao = _cartao_com_compra(cliente, ana, valor=10000)
    cliente.post(f"/cartoes/{cartao}/fatura/pagamento?mes=11&ano=2026", headers=ana)

    # Compra esquecida, lançada depois, mas que cai no mesmo período da fatura
    cliente.post("/transacoes/", headers=ana, json={
        "tipo": "despesa", "valor": 2500, "data": "2026-11-03", "id_categoria": id_categoria(cliente, ana), "id_cartao": cartao,
    })
    fatura = cliente.get(f"/cartoes/{cartao}/fatura/?mes=11&ano=2026", headers=ana).json()
    assert fatura["paga"] is True
    assert (fatura["valor_total"], fatura["valor_pago"]) == (12500, 10000)


def test_fatura_sem_compras_nao_pode_ser_paga(cliente, ana):
    cartao = cliente.post("/cartoes/", headers=ana, json={"nome": "Inter", "dia_fechamento": 3, "dia_vencimento": 10}).json()["id"]
    r = cliente.post(f"/cartoes/{cartao}/fatura/pagamento?mes=11&ano=2026", headers=ana)
    assert r.status_code == 409


def test_nao_paga_fatura_de_outra_pessoa(cliente, ana, bruno):
    cartao_da_ana = _cartao_com_compra(cliente, ana)
    url = f"/cartoes/{cartao_da_ana}/fatura/pagamento?mes=11&ano=2026"
    assert cliente.post(url, headers=bruno).status_code == 404
    assert cliente.delete(url, headers=bruno).status_code == 404


def test_mes_invalido_e_recusado(cliente, ana):
    cartao = _cartao_com_compra(cliente, ana)
    assert cliente.post(f"/cartoes/{cartao}/fatura/pagamento?mes=13&ano=2026", headers=ana).status_code == 422
