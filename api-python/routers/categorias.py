from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func

import models
import schemas
from deps import DbSession, UsuarioAtual, buscar_do_usuario

router = APIRouter(prefix="/categorias", tags=["Categorias"])


def _checar_nome_repetido(db, usuario, nome: str, ignorar_id: int | None = None):
    """Impede duas categorias com o mesmo nome (sem diferenciar maiúsculas) para o mesmo usuário."""
    consulta = db.query(models.Categoria).filter(
        models.Categoria.id_usuario == usuario.id,
        func.lower(models.Categoria.nome) == nome.strip().lower(),
    )
    if ignorar_id is not None:
        consulta = consulta.filter(models.Categoria.id != ignorar_id)
    if consulta.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe uma categoria com esse nome")


# ==========================
# CREATE
# ==========================

@router.post("/", response_model=schemas.CategoriaResponse, status_code=status.HTTP_201_CREATED)
def criar_categoria(categoria: schemas.CategoriaCreate, usuario: UsuarioAtual, db: DbSession):
    _checar_nome_repetido(db, usuario, categoria.nome)

    nova_categoria = models.Categoria(nome=categoria.nome.strip(), id_usuario=usuario.id)
    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)
    return nova_categoria


# ==========================
# RETRIEVE
# ==========================

@router.get("/", response_model=list[schemas.CategoriaResponse])
def listar_categorias(usuario: UsuarioAtual, db: DbSession):
    return (
        db.query(models.Categoria)
        .filter(models.Categoria.id_usuario == usuario.id)
        .order_by(models.Categoria.nome)
        .all()
    )


@router.get("/{id_categoria}", response_model=schemas.CategoriaResponse)
def ler_categoria(id_categoria: int, usuario: UsuarioAtual, db: DbSession):
    return buscar_do_usuario(db, models.Categoria, id_categoria, usuario, "Categoria")


# ==========================
# UPDATE
# ==========================

@router.put("/{id_categoria}", response_model=schemas.CategoriaResponse)
def atualizar_categoria(id_categoria: int, dados: schemas.CategoriaCreate, usuario: UsuarioAtual, db: DbSession):
    categoria = buscar_do_usuario(db, models.Categoria, id_categoria, usuario, "Categoria")
    _checar_nome_repetido(db, usuario, dados.nome, ignorar_id=categoria.id)

    categoria.nome = dados.nome.strip()
    db.commit()
    db.refresh(categoria)
    return categoria


# ==========================
# DELETE
# ==========================

@router.delete("/{id_categoria}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_categoria(
    id_categoria: int,
    usuario: UsuarioAtual,
    db: DbSession,
    mover_para: int | None = Query(
        default=None,
        description="Se a categoria estiver em uso, move as transações e planejamentos para esta outra categoria antes de apagar",
    ),
):
    categoria = buscar_do_usuario(db, models.Categoria, id_categoria, usuario, "Categoria")

    transacoes = db.query(models.Transacao).filter(models.Transacao.id_categoria == categoria.id)
    qtd_transacoes = transacoes.count()

    if qtd_transacoes > 0 and mover_para is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A categoria tem {qtd_transacoes} transação(ões). "
                "Informe ?mover_para=<id> para transferi-las para outra categoria antes de apagar."
            ),
        )

    if mover_para is not None:
        if mover_para == categoria.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Escolha uma categoria diferente")
        destino = buscar_do_usuario(db, models.Categoria, mover_para, usuario, "Categoria de destino")

        transacoes.update({models.Transacao.id_categoria: destino.id}, synchronize_session=False)

        # Planejamentos: se o destino já tem planejamento no mesmo cartão/mês, somamos os limites
        planejamentos = db.query(models.Planejamento).filter(models.Planejamento.id_categoria == categoria.id).all()
        for plan in planejamentos:
            existente = (
                db.query(models.Planejamento)
                .filter(
                    models.Planejamento.id_categoria == destino.id,
                    models.Planejamento.id_cartao == plan.id_cartao,
                    models.Planejamento.mes == plan.mes,
                    models.Planejamento.ano == plan.ano,
                )
                .first()
            )
            if existente:
                existente.valor += plan.valor
                db.delete(plan)
            else:
                plan.id_categoria = destino.id

        # Orçamentos: mesma ideia, somando os limites quando o destino já tem orçamento no mês
        orcamentos = db.query(models.Orcamento).filter(models.Orcamento.id_categoria == categoria.id).all()
        for orc in orcamentos:
            existente = (
                db.query(models.Orcamento)
                .filter(
                    models.Orcamento.id_categoria == destino.id,
                    models.Orcamento.mes == orc.mes,
                    models.Orcamento.ano == orc.ano,
                )
                .first()
            )
            if existente:
                existente.valor += orc.valor
                db.delete(orc)
            else:
                orc.id_categoria = destino.id

        # Assinaturas (serviço Java) passam a usar a categoria de destino
        db.query(models.Assinatura).filter(models.Assinatura.id_categoria == categoria.id).update(
            {models.Assinatura.id_categoria: destino.id}, synchronize_session=False
        )
        db.flush()  # grava as mudanças acima antes do DELETE em massa abaixo

    # Planejamentos que ainda apontam para esta categoria são apagados junto com ela
    db.query(models.Planejamento).filter(models.Planejamento.id_categoria == categoria.id).delete(
        synchronize_session=False
    )
    db.query(models.Orcamento).filter(models.Orcamento.id_categoria == categoria.id).delete(
        synchronize_session=False
    )
    db.delete(categoria)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
