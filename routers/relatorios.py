from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from typing import Annotated
from fastapi import Depends

import models
from database import get_db
from relatorio_pdf import gerar_pdf_mensal

router = APIRouter(
    prefix="/usuarios/{id_usuario}/relatorio-pdf",
    tags=["relatórios"]
)

DbSession = Annotated[Session, Depends(get_db)]

@router.get("/")
def baixar_relatorio_pdf(id_usuario: int, mes: int, ano: int, db: DbSession):
    # 1. Valida se o usuário existe
    usuario = db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    # 2. Busca as transações correntes (fora do cartão de crédito)
    transacoes = db.query(models.Transacao).filter(
        models.Transacao.id_usuario == id_usuario,
        models.Transacao.id_cartao == None,
        extract("month", models.Transacao.data) == mes,
        extract("year", models.Transacao.data) == ano
    ).order_by(models.Transacao.data).all()

    transacoes_correntes = []
    for t in transacoes:
        cat = db.query(models.Categoria).filter(models.Categoria.id == t.id_categoria).first()
        transacoes_correntes.append({
            "data": t.data,
            "descricao": t.descricao,
            "tipo": t.tipo,
            "valor": t.valor,
            "categoria_nome": cat.nome if cat else "Geral"
        })

    # 3. Busca faturas e planejamentos de cada cartão do usuário
    cartoes = db.query(models.Cartao).filter(models.Cartao.id_usuario == id_usuario).all()
    faturas_detalhadas = []

    for cartao in cartoes:
        compras_db = db.query(models.Transacao).filter(
            models.Transacao.id_cartao == cartao.id,
            models.Transacao.tipo == "despesa",
            extract("month", models.Transacao.data) == mes,
            extract("year", models.Transacao.data) == ano
        ).order_by(models.Transacao.data).all()

        compras = []
        total_fatura = 0
        for c in compras_db:
            cat = db.query(models.Categoria).filter(models.Categoria.id == c.id_categoria).first()
            compras.append({
                "data": c.data,
                "descricao": c.descricao,
                "categoria_nome": cat.nome if cat else "Geral",
                "valor": c.valor
            })
            total_fatura += c.valor

        plan_db = db.query(models.Planejamento).filter(
            models.Planejamento.id_cartao == cartao.id,
            models.Planejamento.mes == mes,
            models.Planejamento.ano == ano
        ).all()

        planejamentos = []
        for p in plan_db:
            cat = db.query(models.Categoria).filter(models.Categoria.id == p.id_categoria).first()
            gasto_cat = db.query(func.sum(models.Transacao.valor)).filter(
                models.Transacao.id_cartao == cartao.id,
                models.Transacao.id_categoria == p.id_categoria,
                models.Transacao.tipo == "despesa",
                extract("month", models.Transacao.data) == mes,
                extract("year", models.Transacao.data) == ano
            ).scalar() or 0

            planejamentos.append({
                "nome_categoria": cat.nome if cat else "Geral",
                "valor_planejado": p.valor,
                "valor_gasto": gasto_cat,
                "saldo": p.valor - gasto_cat,
                "percentual": round(gasto_cat / p.valor * 100, 2) if p.valor > 0 else 0.0
            })

        faturas_detalhadas.append({
            "nome_cartao": cartao.nome,
            "valor_total": total_fatura,
            "compras": compras,
            "planejamentos": planejamentos
        })

    pdf_bytes = gerar_pdf_mensal(usuario, mes, ano, transacoes_correntes, faturas_detalhadas)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=relatorio_finflow_{mes:02d}_{ano}.pdf"}
    )
