"""
Orçamento mensal: um limite de gasto por categoria para o mês inteiro.

Diferente do "planejamento" (que é por cartão/fatura), o orçamento soma TODAS as
despesas do mês naquela categoria: pix, débito e cartão de crédito.
O mês considerado é o da data da compra.
"""
from calendar import monthrange
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func

import models
import schemas
from deps import Ano, DbSession, Mes, UsuarioAtual, buscar_do_usuario

router = APIRouter(prefix="/orcamentos", tags=["Orçamento mensal"])

PERCENTUAL_ATENCAO = 80  # a partir daqui o item fica com status "atencao"


def _status(percentual: float) -> str:
    if percentual > 100:
        return "estourado"
    if percentual >= PERCENTUAL_ATENCAO:
        return "atencao"
    return "ok"


def _checar_repetido(db, usuario, id_categoria: int, mes: int, ano: int):
    existe = (
        db.query(models.Orcamento)
        .filter(
            models.Orcamento.id_usuario == usuario.id,
            models.Orcamento.id_categoria == id_categoria,
            models.Orcamento.mes == mes,
            models.Orcamento.ano == ano,
        )
        .first()
    )
    if existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe orçamento para essa categoria em {mes:02d}/{ano} (id {existe.id}). Edite-o.",
        )


def calcular_resumo(db, usuario, mes: int, ano: int) -> dict:
    """Usado pela rota /orcamentos/resumo e pelo dashboard."""
    T = models.Transacao
    inicio, fim = date(ano, mes, 1), date(ano, mes, monthrange(ano, mes)[1])

    gasto_por_categoria = dict(
        db.query(T.id_categoria, func.sum(T.valor))
        .filter(T.id_usuario == usuario.id, T.tipo == "despesa", T.data.between(inicio, fim))
        .group_by(T.id_categoria)
        .all()
    )

    orcamentos = (
        db.query(models.Orcamento, models.Categoria.nome)
        .join(models.Categoria, models.Orcamento.id_categoria == models.Categoria.id)
        .filter(models.Orcamento.id_usuario == usuario.id, models.Orcamento.mes == mes, models.Orcamento.ano == ano)
        .order_by(models.Categoria.nome)
        .all()
    )

    itens = []
    for orc, nome_categoria in orcamentos:
        gasto = gasto_por_categoria.pop(orc.id_categoria, 0) or 0
        percentual = round(gasto / orc.valor * 100, 2)
        itens.append(
            {
                "id_orcamento": orc.id,
                "id_categoria": orc.id_categoria,
                "nome_categoria": nome_categoria,
                "valor_orcado": orc.valor,
                "valor_gasto": gasto,
                "saldo": orc.valor - gasto,
                "percentual": percentual,
                "status": _status(percentual),
            }
        )

    total_orcado = sum(i["valor_orcado"] for i in itens)
    total_gasto = sum(i["valor_gasto"] for i in itens)
    return {
        "mes": mes,
        "ano": ano,
        "total_orcado": total_orcado,
        "total_gasto": total_gasto,
        "saldo": total_orcado - total_gasto,
        "percentual": round(total_gasto / total_orcado * 100, 2) if total_orcado > 0 else 0.0,
        "gasto_fora_do_orcamento": sum(v or 0 for v in gasto_por_categoria.values()),  # o que sobrou no dict
        "itens": itens,
    }


# ==========================
# CREATE
# ==========================

@router.post("/", response_model=schemas.OrcamentoResponse, status_code=status.HTTP_201_CREATED)
def criar_orcamento(dados: schemas.OrcamentoCreate, usuario: UsuarioAtual, db: DbSession):
    buscar_do_usuario(db, models.Categoria, dados.id_categoria, usuario, "Categoria")
    _checar_repetido(db, usuario, dados.id_categoria, dados.mes, dados.ano)

    orcamento = models.Orcamento(**dados.model_dump(), id_usuario=usuario.id)
    db.add(orcamento)
    db.commit()
    db.refresh(orcamento)
    return orcamento


@router.post("/copiar", response_model=list[schemas.OrcamentoResponse], status_code=status.HTTP_201_CREATED)
def copiar_orcamento(
    usuario: UsuarioAtual,
    db: DbSession,
    de_mes: int = Query(ge=1, le=12),
    de_ano: int = Query(ge=2000, le=2100),
    para_mes: int = Query(ge=1, le=12),
    para_ano: int = Query(ge=2000, le=2100),
):
    """Copia os limites de um mês para outro. Categorias que já têm orçamento no destino não são alteradas."""
    if (de_mes, de_ano) == (para_mes, para_ano):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Origem e destino são o mesmo mês")

    O = models.Orcamento
    origem = db.query(O).filter(O.id_usuario == usuario.id, O.mes == de_mes, O.ano == de_ano).all()
    ja_no_destino = {
        id_cat
        for (id_cat,) in db.query(O.id_categoria).filter(O.id_usuario == usuario.id, O.mes == para_mes, O.ano == para_ano)
    }

    novos = [
        O(mes=para_mes, ano=para_ano, valor=o.valor, id_categoria=o.id_categoria, id_usuario=usuario.id)
        for o in origem
        if o.id_categoria not in ja_no_destino
    ]
    db.add_all(novos)
    db.commit()
    for o in novos:
        db.refresh(o)
    return novos


# ==========================
# RETRIEVE
# ==========================

@router.get("/", response_model=list[schemas.OrcamentoResponse])
def listar_orcamentos(
    usuario: UsuarioAtual,
    db: DbSession,
    mes: int | None = Query(default=None, ge=1, le=12),
    ano: int | None = Query(default=None, ge=2000, le=2100),
):
    consulta = db.query(models.Orcamento).filter(models.Orcamento.id_usuario == usuario.id)
    if mes is not None:
        consulta = consulta.filter(models.Orcamento.mes == mes)
    if ano is not None:
        consulta = consulta.filter(models.Orcamento.ano == ano)
    return consulta.order_by(models.Orcamento.ano, models.Orcamento.mes, models.Orcamento.id).all()


@router.get("/resumo", response_model=schemas.ResumoOrcamento)
def resumo_orcamento(mes: Mes, ano: Ano, usuario: UsuarioAtual, db: DbSession):
    """Orçado x gasto por categoria no mês, com status ok / atencao (80%+) / estourado."""
    return calcular_resumo(db, usuario, mes, ano)


@router.get("/{id_orcamento}", response_model=schemas.OrcamentoResponse)
def ler_orcamento(id_orcamento: int, usuario: UsuarioAtual, db: DbSession):
    return buscar_do_usuario(db, models.Orcamento, id_orcamento, usuario, "Orçamento")


# ==========================
# UPDATE
# ==========================

@router.put("/{id_orcamento}", response_model=schemas.OrcamentoResponse)
def atualizar_orcamento(id_orcamento: int, dados: schemas.OrcamentoUpdate, usuario: UsuarioAtual, db: DbSession):
    """Só o valor é editável. Para mudar categoria ou mês, apague e crie outro."""
    orcamento = buscar_do_usuario(db, models.Orcamento, id_orcamento, usuario, "Orçamento")
    orcamento.valor = dados.valor
    db.commit()
    db.refresh(orcamento)
    return orcamento


# ==========================
# DELETE
# ==========================

@router.delete("/{id_orcamento}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_orcamento(id_orcamento: int, usuario: UsuarioAtual, db: DbSession):
    orcamento = buscar_do_usuario(db, models.Orcamento, id_orcamento, usuario, "Orçamento")
    db.delete(orcamento)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
