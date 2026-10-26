from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends
import models
import schemas
import hashlib
from database import get_db

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)

DbSession = Annotated[Session, Depends(get_db)]

def gerar_hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

# ==========================
# ROTAS DE USUARIO
# ==========================

@router.post("/", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def criar_usuario(usuario: schemas.UsuarioCreate, db: DbSession):
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()

    if usuario_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este e-mail ja esta cadastrado no sistema")

    novo_usuario = models.Usuario(
        nome = usuario.nome, 
        email = usuario.email, 
        senha_hash=gerar_hash_senha(usuario.senha)
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return novo_usuario

@router.get("/", response_model=list[schemas.UsuarioResponse], status_code=status.HTTP_200_OK)
def listar_usuarios(db: DbSession):
    usuarios = db.query(models.Usuario).all()
    return usuarios