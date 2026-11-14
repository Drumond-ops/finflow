from sqlalchemy import BigInteger, Boolean, Column, Date, ForeignKey, Integer, String, UniqueConstraint

from database import Base

# ondelete="CASCADE": quando o "pai" é apagado no banco, os "filhos" vão junto.
# Ex.: apagar um usuário apaga automaticamente suas categorias, cartões, transações...
# Onde NÃO há cascade (ex.: transação -> categoria), o banco impede apagar o pai
# enquanto existirem filhos, e a API trata isso com uma mensagem clara (erro 409).


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)


class Cartao(Base):
    __tablename__ = "cartoes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    dia_vencimento = Column(Integer, nullable=True)
    dia_fechamento = Column(Integer, nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)


class Objetivo(Base):
    __tablename__ = "objetivos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    valor_alvo = Column(BigInteger, nullable=False)
    valor_atual = Column(BigInteger, default=0, nullable=False)
    valor_inicial = Column(BigInteger, nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)


class Planejamento(Base):
    __tablename__ = "planejamentos"

    id = Column(Integer, primary_key=True, index=True)
    mes = Column(Integer, nullable=False)
    ano = Column(Integer, nullable=False)
    valor = Column(BigInteger, nullable=False)
    id_cartao = Column(Integer, ForeignKey("cartoes.id", ondelete="CASCADE"), nullable=False, index=True)
    id_categoria = Column(Integer, ForeignKey("categorias.id", ondelete="CASCADE"), nullable=False)


class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False)
    valor = Column(BigInteger, nullable=False)
    data = Column(Date, nullable=False, index=True)
    descricao = Column(String(100), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    id_cartao = Column(Integer, ForeignKey("cartoes.id"), nullable=True)
    id_categoria = Column(Integer, ForeignKey("categorias.id"), nullable=False)


class Aporte(Base):
    __tablename__ = "aportes"

    id = Column(Integer, primary_key=True, index=True)
    valor = Column(BigInteger, nullable=False)
    data = Column(Date, nullable=False)
    id_objetivo = Column(Integer, ForeignKey("objetivos.id", ondelete="CASCADE"), nullable=False, index=True)
    id_transacao = Column(
        Integer, ForeignKey("transacoes.id", ondelete="CASCADE"), unique=True, nullable=False
    )


class Orcamento(Base):
    """Limite de gasto de uma categoria no mês, valendo para conta E cartão."""

    __tablename__ = "orcamentos"
    __table_args__ = (UniqueConstraint("id_usuario", "id_categoria", "mes", "ano", name="uq_orcamento_categoria_mes"),)

    id = Column(Integer, primary_key=True, index=True)
    mes = Column(Integer, nullable=False)
    ano = Column(Integer, nullable=False)
    valor = Column(BigInteger, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    id_categoria = Column(Integer, ForeignKey("categorias.id", ondelete="CASCADE"), nullable=False)


# ==========================
# Tabelas do SERVIÇO DE ASSINATURAS (Java / Spring Boot)
# ==========================
# A API em Java lê e grava estas tabelas. Elas são declaradas aqui para que o banco inteiro
# seja criado num lugar só e para que apagar um usuário/cartão/categoria funcione em cascata.

class Assinatura(Base):
    __tablename__ = "assinaturas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(60), nullable=False)
    valor = Column(BigInteger, nullable=False)  # centavos
    periodicidade = Column(String(10), nullable=False, default="MENSAL")  # MENSAL ou ANUAL
    data_inicio = Column(Date, nullable=False)  # data da 1ª cobrança; define o dia (e o mês, se anual)
    ativa = Column(Boolean, nullable=False, default=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    id_cartao = Column(Integer, ForeignKey("cartoes.id", ondelete="SET NULL"), nullable=True)
    id_categoria = Column(Integer, ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True)


class LancamentoAssinatura(Base):
    """Registra que a cobrança de uma assinatura num mês já virou transação (evita lançar duas vezes)."""

    __tablename__ = "assinatura_lancamentos"
    __table_args__ = (UniqueConstraint("id_assinatura", "mes", "ano", name="uq_lancamento_assinatura_mes"),)

    id = Column(Integer, primary_key=True, index=True)
    mes = Column(Integer, nullable=False)
    ano = Column(Integer, nullable=False)
    id_assinatura = Column(Integer, ForeignKey("assinaturas.id", ondelete="CASCADE"), nullable=False, index=True)
    id_transacao = Column(Integer, ForeignKey("transacoes.id", ondelete="CASCADE"), nullable=False, unique=True)
