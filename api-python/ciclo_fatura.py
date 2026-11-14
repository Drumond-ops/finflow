"""
Ciclo da fatura do cartão de crédito.

Regra usada no FinFlow: a "fatura de novembro" é a fatura que VENCE em novembro,
porque é em novembro que o dinheiro sai da conta.

Exemplo: cartão que fecha dia 3 e vence dia 10.
  - A fatura de novembro fecha em 03/11 e vence em 10/11.
  - Ela contém as compras de 04/10 até 03/11.
  - Uma compra feita em 05/11 já cai na fatura de dezembro.

Se o cartão fecha DEPOIS do dia do vencimento (ex.: fecha dia 25, vence dia 5),
a fatura que vence em dezembro fechou em 25/11.

Se o cartão não tem dia de fechamento cadastrado, a fatura é o mês do calendário
(do dia 1 ao último dia), que era o comportamento antigo.
"""
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class PeriodoFatura:
    inicio: date  # primeira compra que entra nesta fatura (inclusive)
    fim: date  # última compra que entra nesta fatura (inclusive) = data de fechamento
    data_fechamento: date | None
    data_vencimento: date | None


def _dia_valido(ano: int, mes: int, dia: int) -> int:
    """Dia 31 em fevereiro vira 28/29, em abril vira 30 etc."""
    return min(dia, monthrange(ano, mes)[1])


def _mes_anterior(mes: int, ano: int) -> tuple[int, int]:
    return (12, ano - 1) if mes == 1 else (mes - 1, ano)


def _mes_seguinte(mes: int, ano: int) -> tuple[int, int]:
    return (1, ano + 1) if mes == 12 else (mes + 1, ano)


def _fecha_no_mes_anterior(dia_fechamento: int, dia_vencimento: int | None) -> bool:
    """True quando a fatura fecha no mês anterior ao do vencimento (ex.: fecha 25, vence 5)."""
    return dia_vencimento is not None and dia_fechamento >= dia_vencimento


def periodo_fatura(dia_fechamento: int | None, dia_vencimento: int | None, mes: int, ano: int) -> PeriodoFatura:
    """Datas de início e fim das compras da fatura que vence em mes/ano."""
    vencimento = date(ano, mes, _dia_valido(ano, mes, dia_vencimento)) if dia_vencimento else None

    if dia_fechamento is None:
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, monthrange(ano, mes)[1])
        return PeriodoFatura(inicio, fim, None, vencimento)

    mes_fech, ano_fech = (
        _mes_anterior(mes, ano) if _fecha_no_mes_anterior(dia_fechamento, dia_vencimento) else (mes, ano)
    )
    fechamento = date(ano_fech, mes_fech, _dia_valido(ano_fech, mes_fech, dia_fechamento))

    mes_ant, ano_ant = _mes_anterior(mes_fech, ano_fech)
    fechamento_anterior = date(ano_ant, mes_ant, _dia_valido(ano_ant, mes_ant, dia_fechamento))

    return PeriodoFatura(fechamento_anterior + timedelta(days=1), fechamento, fechamento, vencimento)


def fatura_da_compra(dia_fechamento: int | None, dia_vencimento: int | None, data_compra: date) -> tuple[int, int]:
    """Em qual fatura (mes, ano de vencimento) uma compra feita em data_compra vai cair."""
    if dia_fechamento is None:
        return data_compra.month, data_compra.year

    fechamento_deste_mes = _dia_valido(data_compra.year, data_compra.month, dia_fechamento)
    if data_compra.day <= fechamento_deste_mes:
        mes_fech, ano_fech = data_compra.month, data_compra.year
    else:
        mes_fech, ano_fech = _mes_seguinte(data_compra.month, data_compra.year)

    if _fecha_no_mes_anterior(dia_fechamento, dia_vencimento):
        return _mes_seguinte(mes_fech, ano_fech)
    return mes_fech, ano_fech


def periodo_do_cartao(cartao, mes: int, ano: int) -> PeriodoFatura:
    return periodo_fatura(cartao.dia_fechamento, cartao.dia_vencimento, mes, ano)


def soma_da_fatura(db, cartao, periodo: PeriodoFatura) -> int:
    """Total (em centavos) das compras do cartão dentro do período da fatura."""
    from sqlalchemy import func

    import models

    T = models.Transacao
    return (
        db.query(func.sum(T.valor))
        .filter(T.id_cartao == cartao.id, T.tipo == "despesa", T.data.between(periodo.inicio, periodo.fim))
        .scalar()
        or 0
    )
