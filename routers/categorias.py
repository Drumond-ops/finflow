from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends
import models
import schemas
import hashlib
from database import get_db

router = APIRouter(
    prefix="/categorias",
    tags=["categorias"]
)

DbSession = Annotated[Session, Depends(get_db)]

# ==========================
# ROTAS DE CATEGORIA
# ==========================

@router.post("/", response_model=schemas.CategoriaResponse, status_code=status.HTTP_201_CREATED)
def criar_categoria(categoria: schemas.CategoriaCreate, db: DbSession):
    categoria_existente = db.query(models.Categoria).filter(models.Categoria.id_usuario == categoria.id_usuario, models.Categoria.nome == categoria.nome).first()
    if categoria_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta categoria ja existe")

    nova_categoria = models.Categoria(
        nome = categoria.nome,
        id_usuario = categoria.id_usuario
    )

    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)

    return nova_categoria

@router.get("/", response_model=list[schemas.CategoriaResponse], status_code=status.HTTP_200_OK)
def listar_categorias(db: DbSession):
    categorias = db.query(models.Categoria).all()
    return categorias