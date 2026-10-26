from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends
import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/aportes",
    tags=["aportes"]
)

DbSession = Annotated[Session, Depends(get_db)]

# ==========================
# ROTAS DE APORTES
# ==========================

@router.post("/", response_model=schemas.AporteResponse, status_code=status.HTTP_201_CREATED)
def criar_aporte(aporte: schemas.AporteCreate, db: DbSession):

    objetivo_existente = db.query(models.Objetivo).filter(models.Objetivo.id == aporte.id_objetivo).first()
    if not objetivo_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo inexistente")

    categoria_existente= db.query(models.Categoria).filter(models.Categoria.id == aporte.id_categoria).first()
    if not categoria_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria inexistente")

    nova_transacao = models.Transacao(
        tipo = "despesa",
        valor = aporte.valor,
        data = aporte.data,
        descricao = f'Aporte do dia {aporte.data} ao objetivo {objetivo_existente.nome}',
        id_usuario = objetivo_existente.id_usuario,
        id_cartao = None,
        id_categoria = aporte.id_categoria
    )

    db.add(nova_transacao)
    db.flush()

    novo_aporte = models.Aporte(
        valor = aporte.valor,
        data = aporte.data,
        id_objetivo = aporte.id_objetivo,
        id_transacao = nova_transacao.id
    )

    db.add(novo_aporte)

    objetivo_existente.valor_atual += aporte.valor

    db.commit()
    db.refresh(nova_transacao)
    db.refresh(novo_aporte)

    return novo_aporte