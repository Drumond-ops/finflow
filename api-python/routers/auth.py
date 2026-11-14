from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import models
import schemas
from deps import DbSession
from seguranca import criar_token, gerar_hash_senha, verificar_senha

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Categorias criadas automaticamente para todo usuário novo,
# para ele já conseguir lançar transações sem configurar nada.
CATEGORIAS_PADRAO = [
    "Alimentação",
    "Mercado",
    "Moradia",
    "Transporte",
    "Saúde",
    "Educação",
    "Lazer",
    "Assinaturas",
    "Investimentos",
    "Salário",
    "Outros",
]


@router.post("/registro", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar(usuario: schemas.UsuarioCreate, db: DbSession):
    email = usuario.email.lower()
    if db.query(models.Usuario).filter(models.Usuario.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este e-mail já está cadastrado")

    novo_usuario = models.Usuario(
        nome=usuario.nome,
        email=email,
        senha_hash=gerar_hash_senha(usuario.senha),
    )
    db.add(novo_usuario)
    db.flush()  # gera o id do usuário sem fechar a transação

    db.add_all(models.Categoria(nome=nome, id_usuario=novo_usuario.id) for nome in CATEGORIAS_PADRAO)

    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


@router.post("/login", response_model=schemas.Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    """
    Recebe os dados como formulário (padrão OAuth2): campos `username` (o e-mail) e `password`.
    Devolve o token que deve ir no cabeçalho `Authorization: Bearer <token>`.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.email == form.username.lower()).first()

    # Mesma mensagem para "e-mail não existe" e "senha errada": não damos pista a atacantes
    if usuario is None or not verificar_senha(form.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": criar_token(usuario.id), "token_type": "bearer"}
