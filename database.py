from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

# O engine é o motor que gerencia as conexões com o banco de dados.
# A URL vem do .env (veja config.py) — nunca escreva senha direto no código.
engine = create_engine(DATABASE_URL)

# SessionLocal é uma fábrica de sessões. Cada requisição na API terá sua própria sessão isolada.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base é a classe mãe que todos os nossos modelos vão herdar
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    try:
        with engine.connect() as conexao:
            print("Conexão com PostgreSQL realizada com sucesso")
    except Exception as e:
        print(f"Erro ao se conectar: {e}")
