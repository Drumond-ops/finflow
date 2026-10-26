from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

# ==========================
# SCHEMAS DE USUÁRIO
# ==========================

# O que o usuário envia para se cadastrar
class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str  # Recebemos a senha pura aqui para depois gerar o hash!

# O que a API devolve (repare: NUNCA devolvemos a senha!)
class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str

    model_config = ConfigDict(from_attributes=True)


# ==========================
# SCHEMAS DE CATEGORIA
# ==========================

# O que o cliente envia para criar uma categoria
class CategoriaCreate(BaseModel):
    nome: str
    id_usuario: int

# O que a API devolve
class CategoriaResponse(BaseModel):
    id: int
    nome: str
    id_usuario: int

    model_config = ConfigDict(from_attributes=True)

# ==========================
# SCHEMAS DE CARTÃO
# ==========================

class CartaoCreate(BaseModel): 
    nome: str 
    dia_vencimento: int | None = Field(
        default=None,
        ge = 1,
        le = 31,
        description="Dia do mes do vencimento da fatura do cartão"
    )
    dia_fechamento: int | None = Field(
        default=None,
        ge=1,
        le=31,
        description="Dia do mes em que a fatura do cartão fecha"
    )
    id_usuario: int

class CartaoResponse(BaseModel):
    id: int
    nome: str
    dia_vencimento: int | None
    dia_fechamento: int | None
    id_usuario: int

    model_config = ConfigDict(from_attributes=True)


# ==========================
# SCHEMAS DE CARTÃO
# ==========================

class TransacaoCreate(BaseModel): 
    tipo: Literal["receita", "despesa"]
    valor: int = Field(gt=0, description="Valor em 'cents' ")
    data: date
    descricao: str | None = None
    id_usuario: int
    id_cartao: int | None = None
    id_categoria: int

class TransacaoResponse(BaseModel):
    id: int
    tipo: str 
    valor: int 
    data: date
    descricao: str | None
    id_usuario: int
    id_cartao: int | None
    id_categoria: int

    model_config = ConfigDict(from_attributes=True)


# ==========================
# SCHEMAS DE OBJETIVOS
# ==========================

class ObjetivoCreate(BaseModel):
    nome: str
    valor_alvo: int = Field(gt=0, description="Valor meta a ser alcançado")
    valor_inicial: int | None = Field(default=None, gt=0, description="valor que ja se tem guardado (se for o caso)" )
    id_usuario: int

class ObjetivoResponse(BaseModel):
    id: int
    nome: str 
    valor_alvo: int
    valor_atual: int
    id_usuario: int
    model_config = ConfigDict(from_attributes=True)


# ==========================
# SCHEMAS DE APORTES
# ==========================

class AporteCreate(BaseModel):
    valor: int = Field(gt=0, description="Valor do aporte")
    data: date
    id_objetivo: int
    id_categoria: int

class AporteResponse(BaseModel):
    id: int
    valor: int
    data: date
    id_objetivo: int
    id_transacao: int

    model_config = ConfigDict(from_attributes=True)


# ==========================
# SCHEMAS DE APORTES
# ==========================

class PlanejamentoCreate(BaseModel):
    mes: int = Field(ge=1, le=12, description="Mês do planejamento (1 a 12)")
    ano: int = Field(ge=2024, le=2100, description="Ano do planejamento (ex: 2026)")
    valor: int = Field(gt=0, description="Limite orçado para a categoria em centavos")
    id_cartao: int
    id_categoria: int

class PlanejamentoResponse(BaseModel):
    id: int
    mes: int
    ano: int
    valor: int
    id_cartao: int
    id_categoria: int
    model_config = ConfigDict(from_attributes=True)

# ==========================
# SCHEMAS PARA FATURAS
# ==========================

class ItemFaturaCategoria(BaseModel):
    id_categoria: int
    nome_categoria: str
    valor_planejado: int
    valor_gasto: int
    saldo: int
    percentual: float

class FaturaTrackingResponse(BaseModel):
    id_cartao: int
    nome_cartao: str
    valor_total: int #soma das despesas da fatura
    valor_planejado: int
    mes: int
    ano: int
    saldo: int
    detalhes_por_categoria: list[ItemFaturaCategoria]
    percentual_fatura: float


# ==========================
# SCHEMAS PARA DASHBORD
# ==========================

class GastosPorCategoria(BaseModel):
    id_categoria: int
    nome_categoria: str
    valor_gasto: int

class ResumoObjetivo(BaseModel):
    id_objetivo: int
    nome_objetivo: str
    valor_alvo: int
    valor_atual: int
    percentual_conclusao: float

class ResumoFatura(BaseModel):
    id_cartao: int
    nome_cartao: str
    valor_planejado: int
    valor_fatura: int
    percentual: float

class DashBoardResponse(BaseModel):
    mes: int
    ano: int
    total_receitas: int
    total_despesas: int
    total_faturas: int
    faturas: list[ResumoFatura]
    resumo_transacao: list[TransacaoResponse]
    gastos_categoria: list[GastosPorCategoria]
    objetivos_resumo: list[ResumoObjetivo]