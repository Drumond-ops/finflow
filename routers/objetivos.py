from fastapi import APIRouter, Response, status
from sqlalchemy import func

import models
import schemas
from deps import DbSession, UsuarioAtual, buscar_do_usuario

router = APIRouter(prefix="/objetivos", tags=["Objetivos"])


@router.post("/", response_model=schemas.ObjetivoResponse, status_code=status.HTTP_201_CREATED)
def criar_objetivo(objetivo: schemas.ObjetivoCreate, usuario: UsuarioAtual, db: DbSession):
    novo_objetivo = models.Objetivo(
        nome=objetivo.nome,
        valor_alvo=objetivo.valor_alvo,
        valor_atual=objetivo.valor_inicial or 0,
        valor_inicial=objetivo.valor_inicial,
        id_usuario=usuario.id,
    )
    db.add(novo_objetivo)
    db.commit()
    db.refresh(novo_objetivo)
    return novo_objetivo


@router.get("/", response_model=list[schemas.ObjetivoResponse])
def listar_objetivos(usuario: UsuarioAtual, db: DbSession):
    return (
        db.query(models.Objetivo)
        .filter(models.Objetivo.id_usuario == usuario.id)
        .order_by(models.Objetivo.id)
        .all()
    )


@router.get("/{id_objetivo}", response_model=schemas.ObjetivoResponse)
def ler_objetivo(id_objetivo: int, usuario: UsuarioAtual, db: DbSession):
    return buscar_do_usuario(db, models.Objetivo, id_objetivo, usuario, "Objetivo")


@router.get("/{id_objetivo}/aportes", response_model=list[schemas.AporteResponse])
def listar_aportes_do_objetivo(id_objetivo: int, usuario: UsuarioAtual, db: DbSession):
    objetivo = buscar_do_usuario(db, models.Objetivo, id_objetivo, usuario, "Objetivo")
    return (
        db.query(models.Aporte)
        .filter(models.Aporte.id_objetivo == objetivo.id)
        .order_by(models.Aporte.data.desc())
        .all()
    )


@router.put("/{id_objetivo}", response_model=schemas.ObjetivoResponse)
def atualizar_objetivo(id_objetivo: int, dados: schemas.ObjetivoCreate, usuario: UsuarioAtual, db: DbSession):
    objetivo = buscar_do_usuario(db, models.Objetivo, id_objetivo, usuario, "Objetivo")

    objetivo.nome = dados.nome
    objetivo.valor_alvo = dados.valor_alvo
    objetivo.valor_inicial = dados.valor_inicial

    # valor_atual nunca é editado direto: é sempre "valor inicial + soma dos aportes"
    soma_aportes = (
        db.query(func.sum(models.Aporte.valor)).filter(models.Aporte.id_objetivo == objetivo.id).scalar() or 0
    )
    objetivo.valor_atual = (dados.valor_inicial or 0) + soma_aportes

    db.commit()
    db.refresh(objetivo)
    return objetivo


@router.delete("/{id_objetivo}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_objetivo(id_objetivo: int, usuario: UsuarioAtual, db: DbSession):
    """
    Apaga o objetivo e os registros de aporte dele.
    As despesas que os aportes geraram CONTINUAM no extrato: o dinheiro de fato saiu da conta.
    """
    objetivo = buscar_do_usuario(db, models.Objetivo, id_objetivo, usuario, "Objetivo")

    db.query(models.Aporte).filter(models.Aporte.id_objetivo == objetivo.id).delete(synchronize_session=False)
    db.delete(objetivo)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
