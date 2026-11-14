from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func

import models
import schemas
from deps import DbSession, UsuarioAtual, buscar_do_usuario

router = APIRouter(prefix="/cartoes", tags=["Cartões"])


def _checar_nome_repetido(db, usuario, nome: str, ignorar_id: int | None = None):
    consulta = db.query(models.Cartao).filter(
        models.Cartao.id_usuario == usuario.id,
        func.lower(models.Cartao.nome) == nome.strip().lower(),
    )
    if ignorar_id is not None:
        consulta = consulta.filter(models.Cartao.id != ignorar_id)
    if consulta.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um cartão com esse nome")


@router.post("/", response_model=schemas.CartaoResponse, status_code=status.HTTP_201_CREATED)
def criar_cartao(cartao: schemas.CartaoCreate, usuario: UsuarioAtual, db: DbSession):
    _checar_nome_repetido(db, usuario, cartao.nome)

    novo_cartao = models.Cartao(
        nome=cartao.nome.strip(),
        dia_vencimento=cartao.dia_vencimento,
        dia_fechamento=cartao.dia_fechamento,
        id_usuario=usuario.id,
    )
    db.add(novo_cartao)
    db.commit()
    db.refresh(novo_cartao)
    return novo_cartao


@router.get("/", response_model=list[schemas.CartaoResponse])
def listar_cartoes(usuario: UsuarioAtual, db: DbSession):
    return (
        db.query(models.Cartao)
        .filter(models.Cartao.id_usuario == usuario.id)
        .order_by(models.Cartao.nome)
        .all()
    )


@router.get("/{id_cartao}", response_model=schemas.CartaoResponse)
def ler_cartao(id_cartao: int, usuario: UsuarioAtual, db: DbSession):
    return buscar_do_usuario(db, models.Cartao, id_cartao, usuario, "Cartão")


@router.put("/{id_cartao}", response_model=schemas.CartaoResponse)
def atualizar_cartao(id_cartao: int, dados: schemas.CartaoCreate, usuario: UsuarioAtual, db: DbSession):
    cartao = buscar_do_usuario(db, models.Cartao, id_cartao, usuario, "Cartão")
    _checar_nome_repetido(db, usuario, dados.nome, ignorar_id=cartao.id)

    cartao.nome = dados.nome.strip()
    cartao.dia_vencimento = dados.dia_vencimento
    cartao.dia_fechamento = dados.dia_fechamento
    db.commit()
    db.refresh(cartao)
    return cartao


@router.delete("/{id_cartao}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_cartao(id_cartao: int, usuario: UsuarioAtual, db: DbSession):
    cartao = buscar_do_usuario(db, models.Cartao, id_cartao, usuario, "Cartão")

    qtd_compras = db.query(models.Transacao).filter(models.Transacao.id_cartao == cartao.id).count()
    if qtd_compras > 0:
        # Apagar o cartão apagaria o histórico de gastos; preferimos bloquear com uma mensagem clara
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O cartão tem {qtd_compras} compra(s) registrada(s). Apague-as antes de remover o cartão.",
        )

    db.query(models.Planejamento).filter(models.Planejamento.id_cartao == cartao.id).delete(
        synchronize_session=False
    )
    db.delete(cartao)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
