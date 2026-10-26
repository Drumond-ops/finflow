from sqlalchemy import BigInteger, Column, Date, ForeignKey, Integer, String
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable = False)
    email = Column(String(150), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)


class Cartao(Base):
    __tablename__ = "cartoes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    dia_vencimento = Column(Integer, nullable=True)
    dia_fechamento = Column(Integer, nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)


class Objetivo(Base):
    __tablename__ = "objetivos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False)
    valor_alvo = Column(BigInteger, nullable=False)
    valor_atual = Column(BigInteger, default=0, nullable=False)
    valor_inicial = Column(BigInteger, nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

class Planejamento(Base):
    __tablename__ = "planejamentos"

    id = Column(Integer, primary_key=True, index=True)
    mes = Column(Integer, nullable=False)
    ano = Column(Integer, nullable = False)
    valor = Column(BigInteger, nullable=False)
    id_cartao = Column(Integer, ForeignKey("cartoes.id"), nullable=False)
    id_categoria = Column(Integer, ForeignKey("categorias.id"), nullable= False)


class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False)
    valor = Column(BigInteger, nullable=False)
    data = Column(Date, nullable=False)
    descricao = Column(String(100), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    id_cartao = Column(Integer, ForeignKey("cartoes.id"), nullable=True)
    id_categoria = Column(Integer, ForeignKey("categorias.id"), nullable=False)


class Aporte(Base):
    __tablename__ = "aportes"

    id = Column(Integer, primary_key=True, index=True)
    valor = Column(BigInteger, nullable=False)
    data = Column(Date, nullable=False)
    id_objetivo = Column(Integer, ForeignKey("objetivos.id"), nullable=False)
    id_transacao = Column(Integer, ForeignKey("transacoes.id"), unique=True, nullable=False)

if __name__ == "__main__":
    from database import engine
    print("Conectando e criando tabelas no PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Todas as tabelas foram criadas com sucesso!")
