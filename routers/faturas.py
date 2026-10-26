from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from typing import Annotated
from fastapi import Depends
import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/cartoes/{id_cartao}/fatura",
    tags=["faturas"]
)

DbSession = Annotated[Session, Depends(get_db)]

# ==========================
# ROTAS DE FATURA MENSAL
# ==========================

@router.get("/", response_model=schemas.FaturaTrackingResponse, status_code=status.HTTP_200_OK)
def get_fatura(id_cartao: int, mes: int, ano: int, db: DbSession):
    cartao_existente = db.query(models.Cartao).filter(models.Cartao.id == id_cartao).first()
    if not cartao_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartao inexistente")

    planejamentos = db.query(models.Planejamento).filter(
        models.Planejamento.id_cartao == id_cartao,
        models.Planejamento.ano == ano,
        models.Planejamento.mes == mes
    ).all()

    total_fatura = db.query(func.sum(models.Transacao.valor)).filter(
        models.Transacao.id_cartao == cartao_existente.id,
        extract("month", models.Transacao.data) == mes,
        extract("year", models.Transacao.data) == ano,
        models.Transacao.tipo == "despesa"
    ).scalar() or 0

    detalhes = []
    total_planejado = 0

    for plan in planejamentos:
        categoria = db.query(models.Categoria).filter(models.Categoria.id == plan.id_categoria).first()
        nome_cat = categoria.nome if categoria else "Desconhecida"
        id_categoria = plan.id_categoria
        plan_categoria = plan.valor
        gasto = db.query(func.sum(models.Transacao.valor)).filter(
            models.Transacao.id_categoria == id_categoria,
            models.Transacao.id_cartao == cartao_existente.id,
            models.Transacao.tipo == "despesa",
            extract("month", models.Transacao.data) == mes,
            extract("year", models.Transacao.data) == ano,
        ).scalar() or 0
        saldo_categoria = plan_categoria - gasto
        percent_cat =  round(gasto/plan_categoria * 100, 2) if plan_categoria > 0 else 0.0

        detalhes.append({
            "id_categoria": id_categoria,
            "nome_categoria": nome_cat,
            "valor_planejado": plan_categoria,
            "valor_gasto": gasto,
            "saldo": saldo_categoria,
            "percentual": percent_cat
        })

        total_planejado += plan.valor

    saldo_fatura = total_planejado - total_fatura
    percent_fatura = round(total_fatura/total_planejado * 100, 2) if total_planejado > 0 else 0.0

    return {
        "id_cartao":cartao_existente.id,
        "nome_cartao":cartao_existente.nome,
        "valor_total":total_fatura,
        "valor_planejado":total_planejado,
        "mes":mes,
        "ano":ano,
        "saldo":saldo_fatura,
        "detalhes_por_categoria":detalhes,
        "percentual_fatura":percent_fatura
    }