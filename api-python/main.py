from contextlib import asynccontextmanager

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

import models  # noqa: F401  (importar registra as tabelas no Base.metadata)
from config import CORS_ORIGINS
from database import Base, engine
from routers import (
    aportes,
    auth,
    cartoes,
    categorias,
    compras_parceladas,
    dashboard,
    faturas,
    objetivos,
    orcamentos,
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

# Qualquer erro inesperado vira um 500 em JSON, e a API continua no ar.
# É registrado ANTES do CORS para que a resposta de erro também leve os cabeçalhos de CORS
# (senão o navegador mostraria um "erro de CORS" no lugar da mensagem real).
@app.middleware("http")
async def erro_inesperado_em_json(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logging.getLogger("finflow").exception("Erro inesperado em %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Erro interno no servidor. Tente novamente."})


# CORS: autoriza o frontend (que roda em outro endereço/porta) a chamar esta API pelo navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Os erros "esperados" (404, 409, 422...) já saem em JSON pelo HTTPException e pelo Pydantic.
@app.exception_handler(IntegrityError)
async def erro_de_integridade(request: Request, exc: IntegrityError):
    """Ex.: dois cadastros simultâneos violando uma restrição única do banco."""
    return JSONResponse(
        status_code=409,
        content={"detail": "A operação conflita com dados já existentes. Atualize a página e tente de novo."},
    )


# Conectando todos os roteadores modulares
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(categorias.router)
app.include_router(cartoes.router)
app.include_router(transacoes.router)
app.include_router(compras_parceladas.router)
app.include_router(objetivos.router)
app.include_router(aportes.router)
app.include_router(planejamentos.router)
app.include_router(orcamentos.router)
app.include_router(faturas.router)
app.include_router(dashboard.router)
app.include_router(relatorios.router)


@app.get("/", tags=["Status"])
def status_api():
    return {"status": "ok", "documentacao": "/docs"}
