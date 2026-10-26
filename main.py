from fastapi import FastAPI
from routers import (
    usuarios,
    categorias,
    cartoes,
    transacoes,
    objetivos,
    aportes,
    planejamentos,
    faturas,
    dashboard,
    relatorios,
)

app = FastAPI(
    title="FinFlow API",
    description="API de Gestão Financeira Pessoal com FastAPI e PostgreSQL",
    version="0.1.0",
)

# Conectando todos os roteadores modulares
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
