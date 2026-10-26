from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends
import models
import schemas
import hashlib
from database import get_db

router = APIRouter(
    prefix="/objetivos",
    tags=["objetivos"]
)

DbSession = Annotated[Session, Depends(get_db)]

def existe_usuario(id_usuario: int, db: DbSession):
    return bool(db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first())

# ==========================
# ROTAS DE objetivos
# ==========================

@router.post("/", response_model=schemas.ObjetivoResponse, status_code=status.HTTP_201_CREATED)
def criar_objetivo(objetivo: schemas.ObjetivoCreate, db: DbSession):

    if not existe_usuario(objetivo.id_usuario, db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario não encontrado")

    valor_comeco = objetivo.valor_inicial or 0

    novo_objetivo = models.Objetivo(
        nome = objetivo.nome,
        valor_alvo = objetivo.valor_alvo,
        valor_atual = valor_comeco,
        valor_inicial = objetivo.valor_inicial,
        id_usuario = objetivo.id_usuario
    )

    db.add(novo_objetivo)
    db.commit()
    db.refresh(novo_objetivo)

    return novo_objetivo

@router.get("/", response_model=list[schemas.ObjetivoResponse], status_code=status.HTTP_200_OK)
def listar_objetivos(db: DbSession):

    objetivos = db.query(models.Objetivo).all()

    return objetivos