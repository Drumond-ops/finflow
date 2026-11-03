from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401  (importar registra as tabelas no Base.metadata)
from config import CORS_ORIGINS
from database import Base, engine
from routers import (
    aportes,
    auth,
    cartoes,
    categorias,
    dashboard,
    faturas,
    objetivos,
    planejamentos,
    relatorios,
    transacoes,
    usuarios,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Roda UMA vez quando o servidor sobe: cria as tabelas que ainda não existem.
    # (Não altera tabelas que já existem — para isso, no futuro, usaríamos o Alembic.)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FinFlow API",
    description=(
        "API de Gestão Financeira Pessoal com FastAPI e PostgreSQL.\n\n"
        "**Como testar aqui:** crie uma conta em `POST /auth/registro`, depois clique em "
        "**Authorize** (cadeado no topo) e entre com o e-mail no campo *username* e a senha."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

# CORS: autoriza o frontend (que roda em outro endereço/porta) a chamar esta API pelo navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectando todos os roteadores modulares
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(categorias.router)
app.include_router(cartoes.router)
app.include_router(transacoes.router)
app.include_router(objetivos.router)
app.include_router(aportes.router)
app.include_router(planejamentos.router)
app.include_router(faturas.router)
app.include_router(dashboard.router)
app.include_router(relatorios.router)


@app.get("/", tags=["Status"])
def status_api():
    return {"status": "ok", "documentacao": "/docs"}
