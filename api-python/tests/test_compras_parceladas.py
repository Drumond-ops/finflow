"""Compra parcelada no cartão: uma compra vira N transações, uma em cada fatura."""
from datetime import date, timedelta
from itertools import product

from ciclo_fatura import datas_das_parcelas, dividir_valor, fatura_da_compra, somar_meses
from conftest import id_categoria


# ==========================
# Regras de data e valor (sem banco)
# ==========================

def _seguinte(mes, ano):
    return (1, ano + 1) if mes == 12 else (mes + 1, ano)


def test_cada_parcela_cai_na_fatura_seguinte_a_anterior():
    """Para várias combinações de fechamento/vencimento e todo dia de 2 anos: parcela i na fatura (1ª + i)."""
    for fechamento, vencimento in product([None, 1, 3, 15, 28, 30, 31], [None, 1, 5, 10, 31]):
        dia = date(2026, 1, 1)
        while dia <= date(2027, 12, 31):
            datas = datas_das_parcelas(fechamento, vencimento, dia, 12)
            assert datas[0] == dia, "a 1ª parcela é a própria compra"
            esperada = fatura_da_compra(fechamento, vencimento, dia)
            for i, d in enumerate(datas):
                assert fatura_da_compra(fechamento, vencimento, d) == esperada, (fechamento, vencimento, dia, i)
                esperada = _seguinte(*esperada)
            dia += timedelta(days=1)


def test_dia_31_nao_junta_duas_parcelas_na_mesma_fatura():
    # Fecha dia 30: 31/01 entra na fatura que fecha em 28/02. Somar 1 mês daria 28/02 -> mesma fatura.
    datas = datas_das_parcelas(30, 10, date(2026, 1, 31), 3)
    faturas = [fatura_da_compra(30, 10, d) for d in datas]
    assert faturas == [(3, 2026), (4, 2026), (5, 2026)]


def test_somar_meses_usa_o_ultimo_dia_quando_o_mes_e_curto():
    assert somar_meses(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert somar_meses(date(2026, 11, 15), 3) == date(2027, 2, 15)


def test_dividir_valor_nao_perde_centavo():
    assert dividir_valor(100000, 3) == [33334, 33333, 33333]
    assert dividir_valor(1000, 4) == [250, 250, 250, 250]
    for total, partes in product([2, 99, 1001, 123457], range(2, 25)):
        if total < partes:
            continue
        valores = dividir_valor(total, partes)
        assert sum(valores) == total and max(valores) - min(valores) <= 1


# ==========================
# Pela API
# ==========================

def _cartao(cliente, headers):
    return cliente.post(
        "/cartoes/", headers=headers, json={"nome": "Nubank", "dia_fechamento": 3, "dia_vencimento": 10}
    ).json()["id"]


def _compra(cliente, headers, cartao, **extra):
    corpo = {
        "descricao": "Notebook", "valor_total": 100000, "parcelas": 3, "data": "2026-11-20",
        "id_cartao": cartao, "id_categoria": id_categoria(cliente, headers),
    } | extra
    return cliente.post("/compras-parceladas/", headers=headers, json=corpo)


def test_cria_uma_transacao_por_parcela_em_faturas_seguidas(cliente, ana):
    cartao = _cartao(cliente, ana)
    r = _compra(cliente, ana, cartao)
    assert r.status_code == 201, r.text
    compra = r.json()
    assert [(p["numero"], p["valor"], p["fatura_mes"], p["fatura_ano"]) for p in compra["parcelas"]] == [
        (1, 33334, 12, 2026),  # 20/11 é depois do fechamento (dia 3): 1ª parcela na fatura de dezembro
        (2, 33333, 1, 2027),
        (3, 33333, 2, 2027),
    ]

    for mes, ano, valor in [(12, 2026, 33334), (1, 2027, 33333), (2, 2027, 33333)]:
        fatura = cliente.get(f"/cartoes/{cartao}/fatura/?mes={mes}&ano={ano}", headers=ana).json()
        assert fatura["valor_total"] == valor

    transacoes = cliente.get("/transacoes/", headers=ana).json()
    assert sorted(t["descricao"] for t in transacoes) == ["Notebook (1/3)", "Notebook (2/3)", "Notebook (3/3)"]
    assert {(t["origem"], t["id_compra_parcelada"]) for t in transacoes} == {("parcela", compra["id"])}


def test_parcela_nao_e_editada_nem_apagada_sozinha(cliente, ana):
    cartao = _cartao(cliente, ana)
    compra = _compra(cliente, ana, cartao).json()
    id_transacao = compra["parcelas"][1]["id_transacao"]

    r = cliente.put(f"/transacoes/{id_transacao}", headers=ana, json={
        "tipo": "despesa", "valor": 1, "data": "2026-12-20", "id_categoria": id_categoria(cliente, ana), "id_cartao": cartao,
    })
    assert r.status_code == 409
    assert cliente.delete(f"/transacoes/{id_transacao}", headers=ana).status_code == 409


def test_apagar_a_compra_apaga_todas_as_parcelas(cliente, ana):
    cartao = _cartao(cliente, ana)
    compra = _compra(cliente, ana, cartao).json()

    assert cliente.delete(f"/compras-parceladas/{compra['id']}", headers=ana).status_code == 204
    assert cliente.get("/transacoes/", headers=ana).json() == []
    assert cliente.get(f"/compras-parceladas/{compra['id']}", headers=ana).status_code == 404


def test_validacoes(cliente, ana):
    cartao = _cartao(cliente, ana)
    assert _compra(cliente, ana, cartao, parcelas=1).status_code == 422  # 1x não é parcelado
    assert _compra(cliente, ana, cartao, parcelas=25).status_code == 422
    assert _compra(cliente, ana, cartao, valor_total=2, parcelas=3).status_code == 422  # menos de 1 centavo por parcela
    assert _compra(cliente, ana, cartao, descricao="").status_code == 422


def test_isolamento_entre_usuarios(cliente, ana, bruno):
    cartao_da_ana = _cartao(cliente, ana)
    compra = _compra(cliente, ana, cartao_da_ana).json()

    assert cliente.get(f"/compras-parceladas/{compra['id']}", headers=bruno).status_code == 404
    assert cliente.delete(f"/compras-parceladas/{compra['id']}", headers=bruno).status_code == 404
    # Bruno também não consegue lançar uma compra no cartão da Ana
    assert _compra(cliente, bruno, cartao_da_ana).status_code == 404


def test_painel_nao_mostra_parcelas_futuras_como_ultimos_lancamentos(cliente, ana):
    # Compra feita hoje em 6x: as parcelas 2 a 6 têm data futura e não são "últimos lançamentos"
    hoje = date.today()
    cartao = _cartao(cliente, ana)
    _compra(cliente, ana, cartao, data=hoje.isoformat(), parcelas=6)

    painel = cliente.get(f"/dashboard/?mes={hoje.month}&ano={hoje.year}", headers=ana).json()
    assert [t["descricao"] for t in painel["resumo_transacao"]] == ["Notebook (1/6)"]
