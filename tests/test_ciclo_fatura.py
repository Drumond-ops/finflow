from datetime import date, timedelta
from itertools import product

from ciclo_fatura import fatura_da_compra, periodo_fatura
from conftest import id_categoria


# ==========================
# Regras de data (sem banco)
# ==========================

def test_fecha_antes_do_vencimento():
    # Fecha dia 3, vence dia 10: a fatura de novembro vai de 04/10 a 03/11
    p = periodo_fatura(3, 10, 11, 2026)
    assert (p.inicio, p.fim) == (date(2026, 10, 4), date(2026, 11, 3))
    assert p.data_vencimento == date(2026, 11, 10)


def test_fecha_no_mes_anterior_ao_vencimento():
    # Fecha dia 25, vence dia 5: a fatura que vence em dezembro fechou em 25/11
    p = periodo_fatura(25, 5, 12, 2026)
    assert (p.inicio, p.fim) == (date(2026, 10, 26), date(2026, 11, 25))
    assert p.data_vencimento == date(2026, 12, 5)


def test_dia_31_em_fevereiro_vira_ultimo_dia_do_mes():
    p = periodo_fatura(31, 10, 3, 2026)
    assert (p.inicio, p.fim) == (date(2026, 2, 1), date(2026, 2, 28))


def test_sem_fechamento_usa_o_mes_do_calendario():
    p = periodo_fatura(None, None, 2, 2028)
    assert (p.inicio, p.fim) == (date(2028, 2, 1), date(2028, 2, 29))


def test_toda_compra_cai_em_exatamente_uma_fatura():
    """Para várias combinações de fechamento/vencimento, cada dia de 2 anos cai no período da sua fatura."""
    for fechamento, vencimento in product([None, 1, 3, 15, 28, 30, 31], [None, 1, 5, 10, 31]):
        dia = date(2026, 1, 1)
        while dia <= date(2027, 12, 31):
            mes, ano = fatura_da_compra(fechamento, vencimento, dia)
            p = periodo_fatura(fechamento, vencimento, mes, ano)
            assert p.inicio <= dia <= p.fim, (fechamento, vencimento, dia)
            dia += timedelta(days=1)


# ==========================
# Pela API
# ==========================

def test_compra_depois_do_fechamento_vai_para_a_proxima_fatura(cliente, ana):
    cat = id_categoria(cliente, ana)
    cartao = cliente.post(
        "/cartoes/", headers=ana, json={"nome": "Nubank", "dia_fechamento": 3, "dia_vencimento": 10}
    ).json()["id"]

    for data, valor in [("2026-10-04", 100), ("2026-11-03", 200), ("2026-11-04", 400)]:
        cliente.post("/transacoes/", headers=ana,
                     json={"tipo": "despesa", "valor": valor, "data": data, "id_categoria": cat, "id_cartao": cartao})

    novembro = cliente.get(f"/cartoes/{cartao}/fatura/?mes=11&ano=2026", headers=ana).json()
    assert novembro["valor_total"] == 300  # 04/10 e 03/11
    assert novembro["periodo_inicio"] == "2026-10-04" and novembro["periodo_fim"] == "2026-11-03"
    assert novembro["data_vencimento"] == "2026-11-10"

    dezembro = cliente.get(f"/cartoes/{cartao}/fatura/?mes=12&ano=2026", headers=ana).json()
    assert dezembro["valor_total"] == 400  # 04/11 já é da fatura seguinte

    dash = cliente.get("/dashboard/?mes=11&ano=2026", headers=ana).json()
    assert dash["total_faturas"] == 300
    assert dash["faturas"][0]["data_vencimento"] == "2026-11-10"
