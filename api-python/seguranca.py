"""
Tudo que envolve segurança: hash de senha (bcrypt) e login por token (JWT).

Como funciona o login com JWT, em 3 passos:
  1. O usuário manda e-mail + senha para POST /auth/login.
  2. Se estiverem certos, a API devolve um "token": um texto assinado com a SECRET_KEY
     que diz "este é o usuário 7, válido até amanhã".
  3. Em toda requisição seguinte, o frontend manda o cabeçalho
        Authorization: Bearer <token>
     e a API descobre QUEM está pedindo sem precisar da senha de novo.
Ninguém consegue falsificar o token sem conhecer a SECRET_KEY.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import models
from config import ALGORITMO_JWT, MINUTOS_EXPIRACAO_TOKEN, SECRET_KEY
from database import get_db

# Diz ao FastAPI onde fica a rota de login (isso também cria o botão "Authorize" no /docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------- Senhas ----------

def gerar_hash_senha(senha: str) -> str:
    """bcrypt gera um 'sal' aleatório e é lento de propósito: dificulta ataques de força bruta."""
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:  # hash em formato inválido (ex.: senha antiga em SHA-256)
        return False


# ---------- Tokens ----------

def criar_token(id_usuario: int) -> str:
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": str(id_usuario),  # "subject": de quem é o token
        "iat": agora,  # quando foi emitido
        "exp": agora + timedelta(minutes=MINUTOS_EXPIRACAO_TOKEN),  # quando expira
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITMO_JWT)


def get_usuario_atual(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> models.Usuario:
    """Dependência usada em todas as rotas protegidas: devolve o usuário dono do token."""
    erro_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado. Faça login novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO_JWT])
        id_usuario = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise erro_credenciais

    usuario = db.get(models.Usuario, id_usuario)
    if usuario is None:  # token válido, mas o usuário foi apagado
        raise erro_credenciais
    return usuario
