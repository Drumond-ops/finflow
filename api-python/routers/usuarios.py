from fastapi import APIRouter, HTTPException, Response, status

import models
import schemas
from deps import DbSession, UsuarioAtual
from seguranca import gerar_hash_senha, verificar_senha

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

# O "Create" do usuário é o POST /auth/registro.
# Aqui ficam Retrieve, Update e Delete — sempre do PRÓPRIO usuário logado ("me").
# Não existe mais rota que lista todos os usuários: isso vazava e-mails de todo mundo.


@router.get("/me", response_model=schemas.UsuarioResponse)
def ler_meu_usuario(usuario: UsuarioAtual):
    return usuario


@router.put("/me", response_model=schemas.UsuarioResponse)
def atualizar_meu_usuario(dados: schemas.UsuarioUpdate, usuario: UsuarioAtual, db: DbSession):
    email = dados.email.lower()
    outro = (
        db.query(models.Usuario)
        .filter(models.Usuario.email == email, models.Usuario.id != usuario.id)
        .first()
    )
    if outro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este e-mail já está em uso")

    usuario.nome = dados.nome
    usuario.email = email
    db.commit()
    db.refresh(usuario)
    return usuario


@router.put("/me/senha", status_code=status.HTTP_204_NO_CONTENT)
def trocar_senha(dados: schemas.TrocaSenha, usuario: UsuarioAtual, db: DbSession):
    if not verificar_senha(dados.senha_atual, usuario.senha_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha atual incorreta")

    usuario.senha_hash = gerar_hash_senha(dados.nova_senha)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def apagar_minha_conta(usuario: UsuarioAtual, db: DbSession):
    # O ondelete="CASCADE" dos models faz o banco apagar todos os dados do usuário junto
    db.delete(usuario)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
