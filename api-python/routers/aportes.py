from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func

import models
import schemas
from deps import DbSession, UsuarioAtual, buscar_do_usuario

router = APIRouter(prefix="/aportes", tags=["Aportes"])

NOME_CATEGORIA_INVESTIMENTOS = "Investimentos"


def _buscar_aporte(db, id_aporte: int, usuario) -> models.Aporte:
    """Aporte não tem id_usuario: o dono é descoberto pelo objetivo (JOIN)."""
    aporte = (
        db.query(models.Aporte)
        .join(models.Objetivo, models.Aporte.id_objetivo == models.Objetivo.id)
        .filter(models.Aporte.id == id_aporte, models.Objetivo.id_usuario == usuario.id)
        .first()
    )
    if aporte is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aporte não encontrado")
    return aporte


def _categoria_investimentos(db, usuario) -> models.Categoria:
    """Busca a categoria 'Investimentos' do usuário; se não existir, cria."""
    categoria = (
        db.query(models.Categoria)
        .filter(
            models.Categoria.id_usuario == usuario.id,
            func.lower(models.Categoria.nome) == NOME_CATEGORIA_INVESTIMENTOS.lower(),
        )
        .first()
    )
    if categoria is None:
        categoria = models.Categoria(nome=NOME_CATEGORIA_INVESTIMENTOS, id_usuario=usuario.id)
        db.add(categoria)
        db.flush()
    return categoria


@router.post("/", response_model=schemas.AporteResponse, status_code=status.HTTP_201_CREATED)
def criar_aporte(aporte: schemas.AporteCreate, usuario: UsuarioAtual, db: DbSession):
    """
    RF08: registra o aporte, gera uma DESPESA no mês do aporte e soma o valor no objetivo.
    Tudo acontece numa única transação do banco: ou grava tudo, ou nada.
    """
    objetivo = buscar_do_usuario(db, models.Objetivo, aporte.id_objetivo, usuario, "Objetivo")

    if aporte.id_categoria is not None:
        categoria = buscar_do_usuario(db, models.Categoria, aporte.id_categoria, usuario, "Categoria")
    else:
        categoria = _categoria_investimentos(db, usuario)

    nova_transacao = models.Transacao(
        tipo="despesa",
        valor=aporte.valor,
        data=aporte.data,
        descricao=f"Aporte: {objetivo.nome}"[:100],
        id_usuario=usuario.id,
        id_cartao=None,
        id_categoria=categoria.id,
    )
    db.add(nova_transacao)
    db.flush()  # gera o id da transação para ligarmos ao aporte

    novo_aporte = models.Aporte(
        valor=aporte.valor,
        data=aporte.data,
        id_objetivo=objetivo.id,
        id_transacao=nova_transacao.id,
    )
    db.add(novo_aporte)

    objetivo.valor_atual += aporte.valor

    db.commit()
    db.refresh(novo_aporte)
    return novo_aporte


@router.get("/", response_model=list[schemas.AporteResponse])
def listar_aportes(usuario: UsuarioAtual, db: DbSession, id_objetivo: int | None = None):
    consulta = (
        db.query(models.Aporte)
        .join(models.Objetivo, models.Aporte.id_objetivo == models.Objetivo.id)
        .filter(models.Objetivo.id_usuario == usuario.id)
    )
    if id_objetivo is not None:
        consulta = consulta.filter(models.Aporte.id_objetivo == id_objetivo)
    return consulta.order_by(models.Aporte.data.desc(), models.Aporte.id.desc()).all()


@router.get("/{id_aporte}", response_model=schemas.AporteResponse)
def ler_aporte(id_aporte: int, usuario: UsuarioAtual, db: DbSession):
    return _buscar_aporte(db, id_aporte, usuario)


@router.put("/{id_aporte}", response_model=schemas.AporteResponse)
def atualizar_aporte(id_aporte: int, dados: schemas.AporteUpdate, usuario: UsuarioAtual, db: DbSession):
    """Ao editar o aporte, a despesa gerada e o total do objetivo são ajustados juntos."""
    aporte = _buscar_aporte(db, id_aporte, usuario)
    objetivo = db.get(models.Objetivo, aporte.id_objetivo)
    transacao = db.get(models.Transacao, aporte.id_transacao)

    objetivo.valor_atual += dados.valor - aporte.valor  # aplica só a diferença

    aporte.valor = dados.valor
    aporte.data = dados.data
    transacao.valor = dados.valor
    transacao.data = dados.data

    db.commit()
    db.refresh(aporte)
    return aporte


@router.delete("/{id_aporte}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_aporte(id_aporte: int, usuario: UsuarioAtual, db: DbSession):
    """Desfaz o aporte por completo: tira o valor do objetivo e apaga a despesa gerada."""
    aporte = _buscar_aporte(db, id_aporte, usuario)
    objetivo = db.get(models.Objetivo, aporte.id_objetivo)
    transacao = db.get(models.Transacao, aporte.id_transacao)

    objetivo.valor_atual -= aporte.valor
    db.delete(aporte)
    db.flush()  # apaga o aporte primeiro, porque ele aponta para a transação
    db.delete(transacao)

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
