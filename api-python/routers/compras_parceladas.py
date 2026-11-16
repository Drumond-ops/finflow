"""
Compra parcelada no cartão: uma compra vira N transações (uma por parcela), cada uma na fatura seguinte.

Exemplo: notebook de R$ 1.000,00 em 3x no cartão que fecha dia 3, comprado em 20/11.
  -> 3 transações "Notebook (1/3)", "(2/3)", "(3/3)" de R$ 333,34 / 333,33 / 333,33,
     nas faturas que vencem em dezembro, janeiro e fevereiro.
"""
from fastapi import APIRouter, Response, status

import models
import schemas
from ciclo_fatura import datas_das_parcelas, dividir_valor, fatura_da_compra
from deps import DbSession, UsuarioAtual, buscar_do_usuario

router = APIRouter(prefix="/compras-parceladas", tags=["Compras parceladas"])


def _resposta(db, compra: models.CompraParcelada) -> dict:
    """Monta a compra com suas parcelas e a fatura em que cada uma entra."""
    linhas = (
        db.query(models.Parcela, models.Transacao)
        .join(models.Transacao, models.Parcela.id_transacao == models.Transacao.id)
        .filter(models.Parcela.id_compra == compra.id)
        .order_by(models.Parcela.numero)
        .all()
    )
    cartoes = {}
    parcelas = []
    for parcela, transacao in linhas:
        cartao = cartoes.get(transacao.id_cartao) or db.get(models.Cartao, transacao.id_cartao)
        cartoes[transacao.id_cartao] = cartao
        mes, ano = fatura_da_compra(cartao.dia_fechamento, cartao.dia_vencimento, transacao.data)
        parcelas.append(
            {
                "numero": parcela.numero,
                "id_transacao": transacao.id,
                "valor": transacao.valor,
                "data": transacao.data,
                "fatura_mes": mes,
                "fatura_ano": ano,
            }
        )
    return {
        "id": compra.id,
        "descricao": compra.descricao,
        "valor_total": compra.valor_total,
        "quantidade": compra.quantidade,
        "data_compra": compra.data_compra,
        "parcelas": parcelas,
    }


@router.post("/", response_model=schemas.CompraParceladaResponse, status_code=status.HTTP_201_CREATED)
def criar_compra_parcelada(dados: schemas.CompraParceladaCreate, usuario: UsuarioAtual, db: DbSession):
    cartao = buscar_do_usuario(db, models.Cartao, dados.id_cartao, usuario, "Cartão")
    buscar_do_usuario(db, models.Categoria, dados.id_categoria, usuario, "Categoria")

    compra = models.CompraParcelada(
        descricao=dados.descricao,
        valor_total=dados.valor_total,
        quantidade=dados.parcelas,
        data_compra=dados.data,
        id_usuario=usuario.id,
    )
    db.add(compra)
    db.flush()  # gera o id da compra sem fechar a transação do banco: ou grava tudo, ou nada

    datas = datas_das_parcelas(cartao.dia_fechamento, cartao.dia_vencimento, dados.data, dados.parcelas)
    valores = dividir_valor(dados.valor_total, dados.parcelas)
    for numero, (data_parcela, valor) in enumerate(zip(datas, valores), start=1):
        transacao = models.Transacao(
            tipo="despesa",
            valor=valor,
            data=data_parcela,
            descricao=f"{dados.descricao} ({numero}/{dados.parcelas})",
            id_usuario=usuario.id,
            id_cartao=cartao.id,
            id_categoria=dados.id_categoria,
        )
        db.add(transacao)
        db.flush()
        db.add(models.Parcela(numero=numero, id_compra=compra.id, id_transacao=transacao.id))

    db.commit()
    return _resposta(db, compra)


@router.get("/{id_compra}", response_model=schemas.CompraParceladaResponse)
def ler_compra_parcelada(id_compra: int, usuario: UsuarioAtual, db: DbSession):
    compra = buscar_do_usuario(db, models.CompraParcelada, id_compra, usuario, "Compra parcelada")
    return _resposta(db, compra)


@router.delete("/{id_compra}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_compra_parcelada(id_compra: int, usuario: UsuarioAtual, db: DbSession):
    """Apaga a compra e TODAS as parcelas (as transações somem de todas as faturas)."""
    compra = buscar_do_usuario(db, models.CompraParcelada, id_compra, usuario, "Compra parcelada")
    ids_transacoes = [i for (i,) in db.query(models.Parcela.id_transacao).filter(models.Parcela.id_compra == compra.id)]
    # Apagar a transação apaga a linha em "parcelas" (ondelete CASCADE); depois sai a compra
    db.query(models.Transacao).filter(models.Transacao.id.in_(ids_transacoes)).delete(synchronize_session=False)
    db.delete(compra)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
