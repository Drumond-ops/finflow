from datetime import date
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, computed_field, model_validator

# Repare: nenhum schema de entrada recebe mais "id_usuario".
# O dono de cada registro agora vem do TOKEN de login (veja seguranca.py),
# então um usuário não consegue criar ou ler dados em nome de outro.


# ==========================
# SCHEMAS DE USUÁRIO / AUTENTICAÇÃO
# ==========================

def _validar_tamanho_senha(senha: str) -> str:
    # O bcrypt só considera os primeiros 72 BYTES da senha (acentos ocupam 2 bytes)
    if len(senha.encode("utf-8")) > 72:
        raise ValueError("A senha deve ter no máximo 72 bytes")
    return senha


SenhaValida = Annotated[str, Field(min_length=6), AfterValidator(_validar_tamanho_senha)]


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: EmailStr
    senha: SenhaValida  # senha pura; será guardada só como hash bcrypt


class UsuarioUpdate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: EmailStr


class TrocaSenha(BaseModel):
    senha_atual: str
    nova_senha: SenhaValida


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ==========================
# SCHEMAS DE CATEGORIA
# ==========================

class CategoriaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=50)


class CategoriaResponse(BaseModel):
    id: int
    nome: str

    model_config = ConfigDict(from_attributes=True)


# ==========================
# SCHEMAS DE CARTÃO
# ==========================

class CartaoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=50)
    dia_vencimento: int | None = Field(
        default=None, ge=1, le=31, description="Dia do mês do vencimento da fatura do cartão"
    )
    dia_fechamento: int | None = Field(
        default=None, ge=1, le=31, description="Dia do mês em que a fatura do cartão fecha"
    )


class CartaoResponse(BaseModel):
    id: int
    nome: str
    dia_vencimento: int | None
    dia_fechamento: int | None

    model_config = ConfigDict(from_attributes=True)


# ==========================
# SCHEMAS DE TRANSAÇÃO
# ==========================

class TransacaoCreate(BaseModel):
    tipo: Literal["receita", "despesa"]
    valor: int = Field(gt=0, description="Valor em centavos (R$ 12,34 = 1234)")
    data: date
    descricao: str | None = Field(default=None, max_length=100)
    id_cartao: int | None = None
    id_categoria: int

    @model_validator(mode="after")
    def receita_nao_vai_no_cartao(self):
        if self.tipo == "receita" and self.id_cartao is not None:
            raise ValueError("Receitas não podem ser lançadas em cartão de crédito")
        return self


class TransacaoResponse(BaseModel):
    id: int
    tipo: str
    valor: int
    data: date
    descricao: str | None
    id_cartao: int | None
    id_categoria: int

    model_config = ConfigDict(from_attributes=True)


# ==========================
# SCHEMAS DE OBJETIVOS
# ==========================

class ObjetivoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=50)
    valor_alvo: int = Field(gt=0, description="Valor meta a ser alcançado, em centavos")
    valor_inicial: int | None = Field(
        default=None, ge=0, description="Valor que já se tem guardado (se for o caso), em centavos"
    )


class ObjetivoResponse(BaseModel):
    id: int
    nome: str
    valor_alvo: int
    valor_atual: int
    valor_inicial: int | None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def percentual_conclusao(self) -> float:
        return round(self.valor_atual / self.valor_alvo * 100, 2) if self.valor_alvo > 0 else 0.0


# ==========================
# SCHEMAS DE APORTES
# ==========================

class AporteCreate(BaseModel):
    valor: int = Field(gt=0, description="Valor do aporte em centavos")
    data: date
    id_objetivo: int
    id_categoria: int | None = Field(
        default=None,
        description="Categoria da despesa gerada. Se omitida, usa (ou cria) a categoria 'Investimentos'",
    )


class AporteUpdate(BaseModel):
    valor: int = Field(gt=0, description="Valor do aporte em centavos")
    data: date


class AporteResponse(BaseModel):
    id: int
    valor: int
    data: date
    id_objetivo: int
    id_transacao: int

    model_config = ConfigDict(from_attributes=True)


# ==========================
# SCHEMAS DE PLANEJAMENTO
# ==========================

class PlanejamentoCreate(BaseModel):
    mes: int = Field(ge=1, le=12, description="Mês do planejamento (1 a 12)")
    ano: int = Field(ge=2000, le=2100, description="Ano do planejamento (ex: 2026)")
    valor: int = Field(gt=0, description="Limite orçado para a categoria em centavos")
    id_cartao: int
    id_categoria: int


class PlanejamentoUpdate(BaseModel):
    valor: int = Field(gt=0, description="Novo limite orçado em centavos")


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
    valor_total: int  # soma das despesas da fatura
    valor_planejado: int
    mes: int
    ano: int
    saldo: int
    detalhes_por_categoria: list[ItemFaturaCategoria]
    percentual_fatura: float


# ==========================
# SCHEMAS PARA DASHBOARD
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
    total_despesas: int  # despesas fora do cartão (conta/débito/pix)
    total_faturas: int  # soma das faturas dos cartões no mês
    saldo_mes: int  # receitas - despesas - faturas
    faturas: list[ResumoFatura]
    resumo_transacao: list[TransacaoResponse]
    gastos_categoria: list[GastosPorCategoria]  # inclui conta E cartão
    objetivos_resumo: list[ResumoObjetivo]
