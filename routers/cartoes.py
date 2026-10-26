from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends
import models
import schemas
import hashlib
from database import get_db

router = APIRouter(
    prefix="/cartoes",
    tags=["cartoes"]
)

DbSession = Annotated[Session, Depends(get_db)]

def existe_usuario(id_usuario: int, db: DbSession):
    return bool(db.query(models.Usuario).filter(models.Usuario.id == id_usuario).first())

# ==========================
# ROTAS DE CARTAO
# ==========================

@router.post("/", response_model=schemas.CartaoResponse, status_code=status.HTTP_201_CREATED)
def criar_cartao(cartao: schemas.CartaoCreate, db: DbSession):

    if not existe_usuario(cartao.id_usuario, db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario não encontrado")

    cartao_existente = db.query(models.Cartao).filter(models.Cartao.id_usuario == cartao.id_usuario, models.Cartao.nome == cartao.nome).first()
    if cartao_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esse cartao ja existe")
    

    novo_cartao = models.Cartao(
        nome = cartao.nome,
        dia_vencimento = cartao.dia_vencimento,
        dia_fechamento = cartao.dia_fechamento,
        id_usuario = cartao.id_usuario
    )

    db.add(novo_cartao)
    db.commit()
    db.refresh(novo_cartao)
    return novo_cartao

@router.get("/", response_model = list[schemas.CartaoResponse], status_code=status.HTTP_200_OK)
def listar_cartoes(db: DbSession):
    cartoes = db.query(models.Cartao).all()
    return cartoes