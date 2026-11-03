"""
Configurações da aplicação, lidas de variáveis de ambiente.

Nada de senha ou chave secreta escrita no código: tudo vem do arquivo `.env`
(que NÃO vai para o GitHub). O arquivo `.env.example` mostra quais variáveis existem.
"""
import os
import warnings

from dotenv import load_dotenv
from sqlalchemy import URL

# Lê o arquivo .env (se existir) e joga os valores em os.environ
load_dotenv()

# ---------- Banco de dados ----------
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin_financas")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_DB = os.getenv("POSTGRES_DB", "financeiro_db")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Se DATABASE_URL vier pronta, usamos ela; senão montamos a partir das partes acima.
# URL.create cuida de caracteres especiais na senha (como @, # ou /), que quebrariam uma URL montada na mão.
DATABASE_URL = os.getenv("DATABASE_URL") or URL.create(
    drivername="postgresql+psycopg2",
    username=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=POSTGRES_DB,
)

# ---------- Autenticação (JWT) ----------
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    SECRET_KEY = "chave-de-desenvolvimento-insegura"
    warnings.warn("SECRET_KEY não definida no .env — usando uma chave insegura de desenvolvimento.")

ALGORITMO_JWT = "HS256"
MINUTOS_EXPIRACAO_TOKEN = int(os.getenv("MINUTOS_EXPIRACAO_TOKEN", "1440"))  # 24h

# ---------- CORS ----------
# Endereços de onde o frontend pode chamar a API (separados por vírgula)
CORS_ORIGINS = [
    origem.strip()
    for origem in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if origem.strip()
]
