"""
Dependências e funções auxiliares compartilhadas por todos os routers.

Antes, cada router redefinia DbSession e existe_usuario. Centralizar aqui evita
código repetido (princípio DRY: Don't Repeat Yourself).
"""
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import models
from database import get_db
from seguranca import get_usuario_atual

# Sessão do banco, injetada em cada rota
DbSession = Annotated[Session, Depends(get_db)]

# Usuário logado, descoberto a partir do token. Qualquer rota que recebe
# `usuario: UsuarioAtual` passa a exigir login automaticamente.
UsuarioAtual = Annotated[models.Usuario, Depends(get_usuario_atual)]

# Parâmetros de período validados (?mes=10&ano=2026)
Mes = Annotated[int, Query(ge=1, le=12, description="Mês (1 a 12)")]
Ano = Annotated[int, Query(ge=2000, le=2100, description="Ano (ex: 2026)")]


def buscar_do_usuario(db: Session, modelo, id_registro: int, usuario: models.Usuario, nome: str):
    """
    Busca um registro pelo id GARANTINDO que ele pertence ao usuário logado.

    Se o registro não existe OU é de outro usuário, respondemos 404 nos dois casos.
    Assim um usuário mal-intencionado nem descobre se o id existe.
    """
    registro = (
        db.query(modelo)
        .filter(modelo.id == id_registro, modelo.id_usuario == usuario.id)
        .first()
    )
    if registro is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{nome} não encontrado(a)")
    return registro
