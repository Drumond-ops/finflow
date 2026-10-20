from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# String de conexão com o PostgreSQL
# Formato: postgresql+psycopg2://usuario:senha@host:porta/nome_do_banco
URL_BANCO_DADOS = "postgresql+psycopg2://admin_financas:macaco01@localhost:5432/financeiro_db"

# O engine é o motor que gerencia as conexões com o banco de dados
engine = create_engine(URL_BANCO_DADOS)

# SessionLocal é uma fábrica de sessões. Cada requisição na API terá sua própria sessão isolada.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base é a classe mãe que todos os nossos modelos vão herdar
Base = declarative_base()