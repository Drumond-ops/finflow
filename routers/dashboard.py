from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from typing import Annotated
from fastapi import Depends
import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/usuarios/{id_usuario}/dashboard",
    tags=["dashboard"]
)

DbSession = Annotated[Session, Depends(get_db)]

def existe_usuario(id_usuario: int, db: DbSession):
    return bool(db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first())

# ==========================
# ROTAS PARA DASHBOARD
# ==========================

@router.get("/", response_model=schemas.DashBoardResponse, status_code=status.HTTP_200_OK)
def exibir_dashBoard(id_usuario: int, mes: int, ano: int, db: DbSession):

    if not existe_usuario(id_usuario, db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario não encontrado")

    total_receitas = db.query(func.sum(models.Transacao.valor)).filter(
        models.Transacao.id_usuario == id_usuario,
        extract("month", models.Transacao.data) == mes,
        extract("year", models.Transacao.data) == ano,
        models.Transacao.tipo == "receita"
    ).scalar() or 0

    total_despesas = db.query(func.sum(models.Transacao.valor)).filter(
        models.Transacao.id_usuario == id_usuario,
        extract("month", models.Transacao.data) == mes,
        extract("year", models.Transacao.data) == ano,
        models.Transacao.tipo == "despesa",
        models.Transacao.id_cartao == None
    ).scalar() or 0

    cartoes = db.query(models.Cartao).filter(
        models.Cartao.id_usuario == id_usuario
    ).all()

    faturas = []
    total_faturas = 0

    for cartao in cartoes:
        id_cartao = cartao.id
        nome_cartao = cartao.nome
        valor_plan = db.query(func.sum(models.Planejamento.valor)).filter(
            models.Planejamento.id_cartao == id_cartao,
            models.Planejamento.mes == mes,
            models.Planejamento.ano == ano
        ).scalar() or 0

        valor_fatura = db.query(func.sum(models.Transacao.valor)).filter(
            models.Transacao.id_cartao == id_cartao,
            models.Transacao.tipo == "despesa",
            extract("month", models.Transacao.data) == mes,
            extract("year", models.Transacao.data) == ano,
        ).scalar() or 0

        percentual = round(valor_fatura/valor_plan * 100, 2) if valor_plan > 0 else 0.0

        faturas.append({
            "id_cartao":id_cartao,
            "nome_cartao":nome_cartao,
            "valor_planejado":valor_plan,
            "valor_fatura":valor_fatura,            
            "percentual":percentual 
        })

        total_faturas += valor_fatura

    ultimas_trans = db.query(models.Transacao).filter(
        models.Transacao.id_usuario == id_usuario
    ).order_by(models.Transacao.id.desc()).limit(5).all()

    objetivos = db.query(models.Objetivo).filter(
        models.Objetivo.id_usuario == id_usuario
    ).all()

    lista_objetivos = []

    for objetivo in objetivos:
        id_objetivo = objetivo.id
        nome_objetivo = objetivo.nome
        alvo = objetivo.valor_alvo
        atual = objetivo.valor_atual
        percent = round(atual/alvo * 100,2) if alvo > 0 else 0.0
        
        lista_objetivos.append({
            "id_objetivo":id_objetivo,
            "nome_objetivo":nome_objetivo,
            "valor_alvo":alvo,
            "valor_atual":atual,
            "percentual_conclusao":percent
        })

    categorias = db.query(models.Categoria).filter(
        models.Categoria.id_usuario == id_usuario
    ).all()

    gastos_categoria = []

    for cat in categorias:

        id_cat = cat.id
        nome_cat = cat.nome
        total_cat = db.query(func.sum(models.Transacao.valor)).filter(
            extract("month", models.Transacao.data) == mes,
            extract("year", models.Transacao.data) == ano,
            models.Transacao.tipo == "despesa",
            models.Transacao.id_cartao == None,
            models.Transacao.id_categoria == id_cat
        ).scalar() or 0

        gastos_categoria.append({
            "id_categoria":id_cat,
            "nome_categoria":nome_cat,
            "valor_gasto":total_cat
        })

    return {
        "mes":mes,
        "ano":ano,
        "total_receitas":total_receitas,
        "total_despesas":total_despesas,
        "total_faturas":total_faturas,
        "faturas":faturas,
        "resumo_transacao":ultimas_trans,
        "gastos_categoria":gastos_categoria,
        "objetivos_resumo":lista_objetivos
    }