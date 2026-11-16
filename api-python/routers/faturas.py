from datetime import date

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func

import models
import schemas
from ciclo_fatura import periodo_do_cartao, soma_da_fatura
from deps import Ano, DbSession, Mes, UsuarioAtual, buscar_do_usuario

router = APIRouter(prefix="/cartoes/{id_cartao}/fatura", tags=["Faturas"])


# ==========================
# RF06 — TRACKING DA FATURA (planejado x gasto por categoria)
# ==========================

@router.get("/", response_model=schemas.FaturaTrackingResponse)
def get_fatura(id_cartao: int, mes: Mes, ano: Ano, usuario: UsuarioAtual, db: DbSession):
    """
    Fatura que VENCE em mes/ano. Respeita o dia de fechamento do cartão:
    entram as compras feitas entre o fechamento anterior e o fechamento desta fatura.
    """
    cartao = buscar_do_usuario(db, models.Cartao, id_cartao, usuario, "Cartão")
    periodo = periodo_do_cartao(cartao, mes, ano)

    filtro_fatura = (
        models.Transacao.id_cartao == cartao.id,
        models.Transacao.tipo == "despesa",
        models.Transacao.data.between(periodo.inicio, periodo.fim),
    )

    total_fatura = db.query(func.sum(models.Transacao.valor)).filter(*filtro_fatura).scalar() or 0

    # Uma única consulta com GROUP BY em vez de uma consulta por categoria
    gasto_por_categoria = dict(
        db.query(models.Transacao.id_categoria, func.sum(models.Transacao.valor))
        .filter(*filtro_fatura)
        .group_by(models.Transacao.id_categoria)
        .all()
    )

    planejamentos = (
        db.query(models.Planejamento, models.Categoria.nome)
        .join(models.Categoria, models.Planejamento.id_categoria == models.Categoria.id)
        .filter(
            models.Planejamento.id_cartao == cartao.id,
            models.Planejamento.ano == ano,
            models.Planejamento.mes == mes,
        )
        .all()
    )

    detalhes = []
    total_planejado = 0
    for plan, nome_categoria in planejamentos:
        gasto = gasto_por_categoria.get(plan.id_categoria, 0) or 0
        detalhes.append(
            {
                "id_categoria": plan.id_categoria,
                "nome_categoria": nome_categoria,
                "valor_planejado": plan.valor,
                "valor_gasto": gasto,
                "saldo": plan.valor - gasto,
                "percentual": round(gasto / plan.valor * 100, 2) if plan.valor > 0 else 0.0,
            }
        )
        total_planejado += plan.valor

    return {
        "id_cartao": cartao.id,
        "nome_cartao": cartao.nome,
        "valor_total": total_fatura,
        "valor_planejado": total_planejado,
        "mes": mes,
        "ano": ano,
        "periodo_inicio": periodo.inicio,
        "periodo_fim": periodo.fim,
        "data_fechamento": periodo.data_fechamento,
        "data_vencimento": periodo.data_vencimento,
        "saldo": total_planejado - total_fatura,
        "detalhes_por_categoria": detalhes,
        "percentual_fatura": round(total_fatura / total_planejado * 100, 2) if total_planejado > 0 else 0.0,
        **_situacao_pagamento(db, cartao.id, mes, ano),
    }


# ==========================
# PAGAMENTO DA FATURA
# ==========================
# Marcar como paga NÃO muda o saldo do mês: a fatura que vence no mês já é descontada do saldo
# (o dinheiro sai da conta naquele mês, pago ou não). O que muda é a situação: "a pagar" ou "paga".

def _buscar_pagamento(db, id_cartao: int, mes: int, ano: int):
    return (
        db.query(models.FaturaPaga)
        .filter(models.FaturaPaga.id_cartao == id_cartao, models.FaturaPaga.mes == mes, models.FaturaPaga.ano == ano)
        .first()
    )


def _situacao_pagamento(db, id_cartao: int, mes: int, ano: int) -> dict:
    pagamento = _buscar_pagamento(db, id_cartao, mes, ano)
    if not pagamento:
        return {"paga": False, "data_pagamento": None, "valor_pago": None}
    return {"paga": True, "data_pagamento": pagamento.data_pagamento, "valor_pago": pagamento.valor_pago}


@router.post("/pagamento", response_model=schemas.FaturaTrackingResponse)
def marcar_fatura_como_paga(
    id_cartao: int,
    mes: Mes,
    ano: Ano,
    usuario: UsuarioAtual,
    db: DbSession,
    dados: schemas.PagamentoFaturaCreate | None = None,
):
    """Marca como paga a fatura que vence em mes/ano. Chamar de novo atualiza a data e o valor pago."""
    cartao = buscar_do_usuario(db, models.Cartao, id_cartao, usuario, "Cartão")
    total = soma_da_fatura(db, cartao, periodo_do_cartao(cartao, mes, ano))
    if total == 0:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Esta fatura não tem compras: não há o que pagar.")

    pagamento = _buscar_pagamento(db, cartao.id, mes, ano) or models.FaturaPaga(id_cartao=cartao.id, mes=mes, ano=ano)
    pagamento.data_pagamento = (dados.data_pagamento if dados and dados.data_pagamento else None) or date.today()
    pagamento.valor_pago = total
    db.add(pagamento)
    db.commit()
    return get_fatura(id_cartao, mes, ano, usuario, db)


@router.delete("/pagamento", status_code=status.HTTP_204_NO_CONTENT)
def desmarcar_pagamento(id_cartao: int, mes: Mes, ano: Ano, usuario: UsuarioAtual, db: DbSession):
    """Desfaz a marcação de paga (a fatura volta a ficar "a pagar")."""
    cartao = buscar_do_usuario(db, models.Cartao, id_cartao, usuario, "Cartão")
    pagamento = _buscar_pagamento(db, cartao.id, mes, ano)
    if not pagamento:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Esta fatura não está marcada como paga.")
    db.delete(pagamento)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
