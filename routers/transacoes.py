from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends
import models
import schemas
import hashlib
from database import get_db

router = APIRouter(
    prefix="/transacoes",
    tags=["trasacoes"]
)

DbSession = Annotated[Session, Depends(get_db)]

def existe_usuario(id_usuario: int, db: DbSession):
    return bool(db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first())

# ==========================
# ROTAS DE TRANSAÇÃO
# ==========================

@router.post("/", response_model = schemas.TransacaoResponse, status_code=status.HTTP_201_CREATED)
def criar_trasacao(transacao: schemas.TransacaoCreate, db: DbSession):

    if not existe_usuario(transacao.id_usuario, db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado")

    categoria = db.query(models.Categoria).filter(models.Categoria.id == transacao.id_categoria,models.Categoria.id_usuario == transacao.id_usuario).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada para este usuário")

    if transacao.id_cartao is not None:
        cartao = db.query(models.Cartao).filter(models.Cartao.id == transacao.id_cartao,models.Cartao.id_usuario == transacao.id_usuario).first()
        if not cartao:
            raise HTTPException(status_code=404, detail="Cartão não encontrado para este usuário")

    nova_transacao = models.Transacao(
        tipo = transacao.tipo,
        valor = transacao.valor,
        data = transacao.data,
        descricao = transacao.descricao,
        id_usuario = transacao.id_usuario,
        id_cartao = transacao.id_cartao,
        id_categoria = transacao.id_categoria,
    )

    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)

    return nova_transacao

@router.get("/", response_model = list[schemas.TransacaoResponse], status_code=status.HTTP_200_OK)
def listar_transacoes(db: DbSession):
    transacaoes = db.query(models.Transacao).all()
    return transacaoes