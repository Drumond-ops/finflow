from fastapi import APIRouter
from fastapi.responses import Response
from sqlalchemy import extract, func

import models
from deps import Ano, DbSession, Mes, UsuarioAtual
from relatorio_pdf import gerar_pdf_mensal

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


# ==========================
# RF12 — RELATÓRIO MENSAL EM PDF
# ==========================

@router.get("/pdf", response_class=Response, responses={200: {"content": {"application/pdf": {}}}})
def baixar_relatorio_pdf(mes: Mes, ano: Ano, usuario: UsuarioAtual, db: DbSession):
    T = models.Transacao
    do_mes = (
        T.id_usuario == usuario.id,
        extract("month", T.data) == mes,
        extract("year", T.data) == ano,
    )

    # 1. Transações correntes (fora do cartão), já com o nome da categoria via JOIN
    transacoes = (
        db.query(T, models.Categoria.nome)
        .join(models.Categoria, T.id_categoria == models.Categoria.id)
        .filter(*do_mes, T.id_cartao.is_(None))
        .order_by(T.data, T.id)
        .all()
    )
    transacoes_correntes = [
        {
            "data": t.data,
            "descricao": t.descricao,
            "tipo": t.tipo,
            "valor": t.valor,
            "categoria_nome": nome_cat,
        }
        for t, nome_cat in transacoes
    ]

    # 2. Faturas e planejamentos de cada cartão do usuário
    cartoes = (
        db.query(models.Cartao).filter(models.Cartao.id_usuario == usuario.id).order_by(models.Cartao.nome).all()
    )
    faturas_detalhadas = []

    for cartao in cartoes:
        compras_db = (
            db.query(T, models.Categoria.nome)
            .join(models.Categoria, T.id_categoria == models.Categoria.id)
            .filter(*do_mes, T.id_cartao == cartao.id, T.tipo == "despesa")
            .order_by(T.data, T.id)
            .all()
        )
        compras = [
            {"data": c.data, "descricao": c.descricao, "categoria_nome": nome_cat, "valor": c.valor}
            for c, nome_cat in compras_db
        ]
        total_fatura = sum(c["valor"] for c in compras)

        gasto_por_categoria = {}
        for c, _ in compras_db:
            gasto_por_categoria[c.id_categoria] = gasto_por_categoria.get(c.id_categoria, 0) + c.valor

        plan_db = (
            db.query(models.Planejamento, models.Categoria.nome)
            .join(models.Categoria, models.Planejamento.id_categoria == models.Categoria.id)
            .filter(
                models.Planejamento.id_cartao == cartao.id,
                models.Planejamento.mes == mes,
                models.Planejamento.ano == ano,
            )
            .all()
        )
        planejamentos = []
        for p, nome_cat in plan_db:
            gasto_cat = gasto_por_categoria.get(p.id_categoria, 0)
            planejamentos.append(
                {
                    "nome_categoria": nome_cat,
                    "valor_planejado": p.valor,
                    "valor_gasto": gasto_cat,
                    "saldo": p.valor - gasto_cat,
                    "percentual": round(gasto_cat / p.valor * 100, 2) if p.valor > 0 else 0.0,
                }
            )

        faturas_detalhadas.append(
            {
                "nome_cartao": cartao.nome,
                "valor_total": total_fatura,
                "compras": compras,
                "planejamentos": planejamentos,
            }
        )

    pdf_bytes = gerar_pdf_mensal(usuario, mes, ano, transacoes_correntes, faturas_detalhadas)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=relatorio_finflow_{mes:02d}_{ano}.pdf"},
    )
