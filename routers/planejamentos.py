from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends
import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/planejamentos",
    tags=["planejamentos"]
)

DbSession = Annotated[Session, Depends(get_db)]


# ==========================
# ROTAS DE planejamento 
# ==========================

@router.post("/", response_model=schemas.PlanejamentoResponse, status_code=status.HTTP_201_CREATED)
def criar_planejamento(planejamento: schemas.PlanejamentoCreate, db: DbSession):

    cartao_existente = db.query(models.Cartao).filter(models.Cartao.id == planejamento.id_cartao).first()
    if not cartao_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cartão Inexistente")

    categoria_existente = db.query(models.Categoria).filter(
        models.Categoria.id == planejamento.id_categoria,
        models.Categoria.id_usuario == cartao_existente.id_usuario
        ).first()
    if not categoria_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria inexistente")

    existe_planejamento = db.query(models.Planejamento).filter(
        models.Planejamento.id_cartao == planejamento.id_cartao,
        models.Planejamento.id_categoria == planejamento.id_categoria,
        models.Planejamento.ano == planejamento.ano,
        models.Planejamento.mes == planejamento.mes
        ).first()

    if existe_planejamento:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ja existe um planejamento para essa categoria nesta fatura")

    novo_planejamento = models.Planejamento(
        mes = planejamento.mes,
        ano = planejamento.ano,
        valor = planejamento.valor,
        id_cartao = planejamento.id_cartao,
        id_categoria = planejamento.id_categoria
    )

    db.add(novo_planejamento)
    db.commit()
    db.refresh(novo_planejamento)

    return novo_planejamento

@router.get("/", response_model = list[schemas.PlanejamentoResponse], status_code=status.HTTP_200_OK)
def listar_planejamentos(db: DbSession):
    planejamentos = db.query(models.Planejamento).all()
    return planejamentos