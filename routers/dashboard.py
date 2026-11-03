from fastapi import APIRouter
from sqlalchemy import extract, func

import models
import schemas
from deps import Ano, DbSession, Mes, UsuarioAtual

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ==========================
# RF11 — DASHBOARD DA PÁGINA INICIAL
# ==========================

@router.get("/", response_model=schemas.DashBoardResponse)
def exibir_dashboard(mes: Mes, ano: Ano, usuario: UsuarioAtual, db: DbSession):
    T = models.Transacao
    do_mes = (
        T.id_usuario == usuario.id,
        extract("month", T.data) == mes,
        extract("year", T.data) == ano,
    )

    total_receitas = db.query(func.sum(T.valor)).filter(*do_mes, T.tipo == "receita").scalar() or 0

    # Despesas "correntes": fora do cartão (conta, débito, pix)
    total_despesas = (
        db.query(func.sum(T.valor)).filter(*do_mes, T.tipo == "despesa", T.id_cartao.is_(None)).scalar() or 0
    )

    # ---------- Faturas ----------
    fatura_por_cartao = dict(
        db.query(T.id_cartao, func.sum(T.valor))
        .filter(*do_mes, T.tipo == "despesa", T.id_cartao.is_not(None))
        .group_by(T.id_cartao)
        .all()
    )
    planejado_por_cartao = dict(
        db.query(models.Planejamento.id_cartao, func.sum(models.Planejamento.valor))
        .join(models.Cartao, models.Planejamento.id_cartao == models.Cartao.id)
        .filter(
            models.Cartao.id_usuario == usuario.id,
            models.Planejamento.mes == mes,
            models.Planejamento.ano == ano,
        )
        .group_by(models.Planejamento.id_cartao)
        .all()
    )

    cartoes = (
        db.query(models.Cartao).filter(models.Cartao.id_usuario == usuario.id).order_by(models.Cartao.nome).all()
    )
    faturas = []
    for cartao in cartoes:
        valor_fatura = fatura_por_cartao.get(cartao.id, 0) or 0
        valor_plan = planejado_por_cartao.get(cartao.id, 0) or 0
        faturas.append(
            {
                "id_cartao": cartao.id,
                "nome_cartao": cartao.nome,
                "valor_planejado": valor_plan,
                "valor_fatura": valor_fatura,
                "percentual": round(valor_fatura / valor_plan * 100, 2) if valor_plan > 0 else 0.0,
            }
        )
    total_faturas = sum(f["valor_fatura"] for f in faturas)

    # ---------- Últimas transações (por DATA, não por id) ----------
    ultimas_trans = (
        db.query(T).filter(T.id_usuario == usuario.id).order_by(T.data.desc(), T.id.desc()).limit(5).all()
    )

    # ---------- Gastos por categoria (conta + cartão), do maior para o menor ----------
    gastos = (
        db.query(models.Categoria.id, models.Categoria.nome, func.sum(T.valor).label("total"))
        .join(T, T.id_categoria == models.Categoria.id)
        .filter(*do_mes, T.tipo == "despesa")
        .group_by(models.Categoria.id, models.Categoria.nome)
        .order_by(func.sum(T.valor).desc())
        .all()
    )
    gastos_categoria = [
        {"id_categoria": id_cat, "nome_categoria": nome, "valor_gasto": total} for id_cat, nome, total in gastos
    ]

    # ---------- Objetivos ----------
    objetivos = (
        db.query(models.Objetivo).filter(models.Objetivo.id_usuario == usuario.id).order_by(models.Objetivo.id).all()
    )
    objetivos_resumo = [
        {
            "id_objetivo": obj.id,
            "nome_objetivo": obj.nome,
            "valor_alvo": obj.valor_alvo,
            "valor_atual": obj.valor_atual,
            "percentual_conclusao": round(obj.valor_atual / obj.valor_alvo * 100, 2) if obj.valor_alvo > 0 else 0.0,
        }
        for obj in objetivos
    ]

    return {
        "mes": mes,
        "ano": ano,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "total_faturas": total_faturas,
        "saldo_mes": total_receitas - total_despesas - total_faturas,
        "faturas": faturas,
        "resumo_transacao": ultimas_trans,
        "gastos_categoria": gastos_categoria,
        "objetivos_resumo": objetivos_resumo,
    }
