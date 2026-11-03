from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import extract

import models
import schemas
from deps import DbSession, UsuarioAtual, buscar_do_usuario

router = APIRouter(prefix="/transacoes", tags=["Transações"])


def _validar_vinculos(db, usuario, dados: schemas.TransacaoCreate):
    """Garante que categoria e cartão informados existem E pertencem ao usuário logado."""
    buscar_do_usuario(db, models.Categoria, dados.id_categoria, usuario, "Categoria")
    if dados.id_cartao is not None:
        buscar_do_usuario(db, models.Cartao, dados.id_cartao, usuario, "Cartão")


def _bloquear_se_for_aporte(db, transacao: models.Transacao):
    """Transações geradas por aporte devem ser alteradas pelo aporte, senão o objetivo fica inconsistente."""
    aporte = db.query(models.Aporte).filter(models.Aporte.id_transacao == transacao.id).first()
    if aporte:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Esta transação foi gerada pelo aporte {aporte.id}. Edite ou apague o aporte.",
        )


@router.post("/", response_model=schemas.TransacaoResponse, status_code=status.HTTP_201_CREATED)
def criar_transacao(transacao: schemas.TransacaoCreate, usuario: UsuarioAtual, db: DbSession):
    _validar_vinculos(db, usuario, transacao)

    nova_transacao = models.Transacao(**transacao.model_dump(), id_usuario=usuario.id)
    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)
    return nova_transacao


@router.get("/", response_model=list[schemas.TransacaoResponse])
def listar_transacoes(
    usuario: UsuarioAtual,
    db: DbSession,
    mes: int | None = Query(default=None, ge=1, le=12),
    ano: int | None = Query(default=None, ge=2000, le=2100),
    tipo: Literal["receita", "despesa"] | None = None,
    id_categoria: int | None = None,
    id_cartao: int | None = None,
    limite: int = Query(default=200, ge=1, le=1000),
):
    """Lista as transações do usuário, das mais recentes para as mais antigas, com filtros opcionais."""
    consulta = db.query(models.Transacao).filter(models.Transacao.id_usuario == usuario.id)

    if mes is not None:
        consulta = consulta.filter(extract("month", models.Transacao.data) == mes)
    if ano is not None:
        consulta = consulta.filter(extract("year", models.Transacao.data) == ano)
    if tipo is not None:
        consulta = consulta.filter(models.Transacao.tipo == tipo)
    if id_categoria is not None:
        consulta = consulta.filter(models.Transacao.id_categoria == id_categoria)
    if id_cartao is not None:
        consulta = consulta.filter(models.Transacao.id_cartao == id_cartao)

    return consulta.order_by(models.Transacao.data.desc(), models.Transacao.id.desc()).limit(limite).all()


@router.get("/{id_transacao}", response_model=schemas.TransacaoResponse)
def ler_transacao(id_transacao: int, usuario: UsuarioAtual, db: DbSession):
    return buscar_do_usuario(db, models.Transacao, id_transacao, usuario, "Transação")


@router.put("/{id_transacao}", response_model=schemas.TransacaoResponse)
def atualizar_transacao(id_transacao: int, dados: schemas.TransacaoCreate, usuario: UsuarioAtual, db: DbSession):
    transacao = buscar_do_usuario(db, models.Transacao, id_transacao, usuario, "Transação")
    _bloquear_se_for_aporte(db, transacao)
    _validar_vinculos(db, usuario, dados)

    for campo, valor in dados.model_dump().items():
        setattr(transacao, campo, valor)

    db.commit()
    db.refresh(transacao)
    return transacao


@router.delete("/{id_transacao}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_transacao(id_transacao: int, usuario: UsuarioAtual, db: DbSession):
    transacao = buscar_do_usuario(db, models.Transacao, id_transacao, usuario, "Transação")
    _bloquear_se_for_aporte(db, transacao)

    db.delete(transacao)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
