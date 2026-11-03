from fastapi import APIRouter
from sqlalchemy import extract, func

import models
import schemas
from deps import Ano, DbSession, Mes, UsuarioAtual, buscar_do_usuario

router = APIRouter(prefix="/cartoes/{id_cartao}/fatura", tags=["Faturas"])


# ==========================
# RF06 — TRACKING DA FATURA (planejado x gasto por categoria)
# ==========================

@router.get("/", response_model=schemas.FaturaTrackingResponse)
def get_fatura(id_cartao: int, mes: Mes, ano: Ano, usuario: UsuarioAtual, db: DbSession):
    cartao = buscar_do_usuario(db, models.Cartao, id_cartao, usuario, "Cartão")

    filtro_fatura = (
        models.Transacao.id_cartao == cartao.id,
        models.Transacao.tipo == "despesa",
        extract("month", models.Transacao.data) == mes,
        extract("year", models.Transacao.data) == ano,
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
        "saldo": total_planejado - total_fatura,
        "detalhes_por_categoria": detalhes,
        "percentual_fatura": round(total_fatura / total_planejado * 100, 2) if total_planejado > 0 else 0.0,
    }
