from fastapi import APIRouter, HTTPException, Query, Response, status

import models
import schemas
from deps import DbSession, UsuarioAtual, buscar_do_usuario

router = APIRouter(prefix="/planejamentos", tags=["Planejamentos"])


def _buscar_planejamento(db, id_planejamento: int, usuario) -> models.Planejamento:
    """Planejamento não tem id_usuario: o dono é descoberto pelo cartão (JOIN)."""
    plan = (
        db.query(models.Planejamento)
        .join(models.Cartao, models.Planejamento.id_cartao == models.Cartao.id)
        .filter(models.Planejamento.id == id_planejamento, models.Cartao.id_usuario == usuario.id)
        .first()
    )
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planejamento não encontrado")
    return plan


@router.post("/", response_model=schemas.PlanejamentoResponse, status_code=status.HTTP_201_CREATED)
def criar_planejamento(planejamento: schemas.PlanejamentoCreate, usuario: UsuarioAtual, db: DbSession):
    buscar_do_usuario(db, models.Cartao, planejamento.id_cartao, usuario, "Cartão")
    buscar_do_usuario(db, models.Categoria, planejamento.id_categoria, usuario, "Categoria")

    existe = (
        db.query(models.Planejamento)
        .filter(
            models.Planejamento.id_cartao == planejamento.id_cartao,
            models.Planejamento.id_categoria == planejamento.id_categoria,
            models.Planejamento.ano == planejamento.ano,
            models.Planejamento.mes == planejamento.mes,
        )
        .first()
    )
    if existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um planejamento para essa categoria nesta fatura (id {existe.id}). Edite-o.",
        )

    novo_planejamento = models.Planejamento(**planejamento.model_dump())
    db.add(novo_planejamento)
    db.commit()
    db.refresh(novo_planejamento)
    return novo_planejamento


@router.get("/", response_model=list[schemas.PlanejamentoResponse])
def listar_planejamentos(
    usuario: UsuarioAtual,
    db: DbSession,
    mes: int | None = Query(default=None, ge=1, le=12),
    ano: int | None = Query(default=None, ge=2000, le=2100),
    id_cartao: int | None = None,
):
    consulta = (
        db.query(models.Planejamento)
        .join(models.Cartao, models.Planejamento.id_cartao == models.Cartao.id)
        .filter(models.Cartao.id_usuario == usuario.id)
    )
    if mes is not None:
        consulta = consulta.filter(models.Planejamento.mes == mes)
    if ano is not None:
        consulta = consulta.filter(models.Planejamento.ano == ano)
    if id_cartao is not None:
        consulta = consulta.filter(models.Planejamento.id_cartao == id_cartao)
    return consulta.order_by(models.Planejamento.ano, models.Planejamento.mes, models.Planejamento.id).all()


@router.get("/{id_planejamento}", response_model=schemas.PlanejamentoResponse)
def ler_planejamento(id_planejamento: int, usuario: UsuarioAtual, db: DbSession):
    return _buscar_planejamento(db, id_planejamento, usuario)


@router.put("/{id_planejamento}", response_model=schemas.PlanejamentoResponse)
def atualizar_planejamento(
    id_planejamento: int, dados: schemas.PlanejamentoUpdate, usuario: UsuarioAtual, db: DbSession
):
    """Só o limite (valor) é editável. Para mudar mês, cartão ou categoria, apague e crie outro."""
    plan = _buscar_planejamento(db, id_planejamento, usuario)
    plan.valor = dados.valor
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{id_planejamento}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_planejamento(id_planejamento: int, usuario: UsuarioAtual, db: DbSession):
    plan = _buscar_planejamento(db, id_planejamento, usuario)
    db.delete(plan)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
