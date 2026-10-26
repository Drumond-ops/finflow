# 📙 FinFlow — Documentação da Fase 2: Schemas, FastAPI e Regras de Negócio Core

Este documento registra todas as decisões arquiteturais, padrões de validação e **boas práticas de engenharia de software** adotadas durante a **Fase 2** do projeto **FinFlow**.

---

## 1. Onde Estamos no Projeto?

Concluímos **100% da Fase 2**! Veja a linha do tempo do projeto:

* **Fase 1: Fundação & Infraestrutura** ✅ *(Concluída)*
  * Container PostgreSQL 16 no Docker, conexão SQLAlchemy e mapeamento relacional das 7 tabelas (`models.py`).
* **Fase 2: Camada de Aplicação, Schemas & CRUDs Core** ✅ *(Concluída nesta etapa!)*
  * Implementação de contratos Pydantic v2, injeção de dependências, tratamento de exceções HTTP e todas as 7 rotas com regras de integridade.
* **Fase 3: Inteligência de Negócio, Agregações & Refatoração** ⏳ *(Próxima etapa)*
  * Endpoint de Tracking da Fatura (RF06), Dashboard Resolidado (RF11), modularização em `routers/` e filtros de busca.
* **Fase 4: Frontend Web Mobile-First** ⏳
  * Telas interativas, gráficos (Chart.js/Recharts) e consumo da API.
* **Fase 5: Relatórios em PDF (RF12) & Polimento** ⏳

---

## 2. Padrões de Arquitetura de Software Implementados

### 2.1 A Jornada dos Dados: Modelos (SQLAlchemy) vs Schemas (Pydantic v2)
Uma das decisões mais importantes da aplicação foi a separação estrita de responsabilidades:
* **Modelos (`models.py`):** Definem a estrutura física das tabelas no PostgreSQL.
* **Schemas (`schemas.py`):** Definem o contrato de tráfego pela rede HTTP (JSON) e validação em tempo de execução.

```text
[Cliente / Frontend]
        │  (1) Envia JSON com validações de tipo e regras
        ▼
[Pydantic: SchemaCreate] ──(Barra dados inválidos com erro 422 na entrada)
        │  (2) Dados validados chegam à rota Python
        ▼
[Lógica de Negócio / Regras]
        │  (3) Tradução do Schema para o Modelo do Banco
        ▼
[SQLAlchemy: Modelo] ──(Gravação física no PostgreSQL via db.commit)
        │  (4) Retorno filtrado pelo response_model
        ▼
[Pydantic: SchemaResponse] ──(Garante que senhas e dados sensíveis NUNCA vazem)
```

### 2.2 Schemas com Atributos que Não Existem no Modelo
* **Conceito Chave:** O schema de entrada modela a **intenção da ação do usuário**, e não necessariamente uma tabela isolada.
* **Caso Prático (`AporteCreate`):** O schema recebe `id_categoria`, embora a tabela `aportes` não tenha essa coluna. Essa informação é utilizada pela regra de negócio para gerar automaticamente uma despesa vinculada na tabela `transacoes`.

### 2.3 Gerenciamento de Sessão e Injeção de Dependências (`Annotated`)
* O padrão `get_db` fornece a sessão com `yield` e garante o encerramento no `finally: db.close()`.
* **Resolução do Aviso Ruff (B008):** Em vez da sintaxe legada `db: Session = Depends(get_db)` (que dispara avisos de linters por executar chamadas de função em valores padrão de argumentos), foi adotada a sintaxe padrão-ouro moderna:
  ```python
  DbSession = Annotated[Session, Depends(get_db)]
  ```
  Isso elimina avisos de análise estática e padroniza a tipagem em todas as funções de rota.

---

## 3. Boas Práticas e Validações Declarativas no Pydantic

1. **Uso de `Field` para Validações Numéricas e Metadados:**
   * Limitação de dias de vencimento e fechamento de cartão: `Field(ge=1, le=31)`.
   * Limitação de meses em planejamentos: `Field(ge=1, le=12)`.
   * Valores monetários estritamente positivos: `Field(gt=0)`.
   * **Benefício:** Elimina a necessidade de dezenas de blocos `if/else` manuais e documenta os limites automaticamente no Swagger UI.

2. **Tipagem Fechada com `Literal`:**
   * O campo `tipo` da transação foi tipado como `Literal["receita", "despesa"]`.
   * Bloqueia qualquer entrada fora desse conjunto e renderiza um menu suspenso (*dropdown*) interativo no Swagger.

3. **Diferença entre `campo: str | None` e `campo: str | None = None`:**
   * Sem valor padrão (`= None`), o Pydantic exige a presença da chave no JSON (mesmo que com valor `null`).
   * Com o valor padrão (`= None`), o cliente pode omitir a propriedade inteira da requisição sem erro de validação.

4. **Operações Financeiras Exclusivamente em Centavos:**
   * A API opera apenas com inteiros (`valor: int`), representando centavos. A conversão de moeda (divisão/multiplicação por 100) é responsabilidade da camada de apresentação (Frontend), seguindo o padrão de processadoras globais como a Stripe.

---

## 4. Regras de Integridade Relacional e Segurança

1. **Prevenção de Referência Insegura a Objetos (Anti-IDOR):**
   * Em todas as criações (`Transacao`, `Planejamento`, `Aporte`), a API valida se as entidades associadas (categoria, cartão) pertencem **ao mesmo usuário** proprietário da operação.
   * Impede que o Usuário 1 vincule gastos aos cartões ou categorias do Usuário 2.

2. **Substituição de Erros de Banco (500) por Respostas Amigáveis (404):**
   * Antes de acionar o banco, as chaves estrangeiras recebidas são verificadas. Se um ID inexistente for passado, a API responde com `404 Not Found` em vez de permitir que o PostgreSQL aborte a transação com um erro interno `500`.

3. **O Papel do `db.flush()` em Operações Atômicas Complexas (RF08):**
   * No cadastro de `Aporte`:
     1. A `Transacao` é criada e adicionada (`db.add(nova_transacao)`).
     2. Executa-se `db.flush()`. O SQLAlchemy envia a inserção para o PostgreSQL dentro da mesma transação, gerando o `nova_transacao.id` sem fechar o ciclo.
     3. O `Aporte` é instanciado recebendo esse ID gerado.
     4. O saldo acumulado da meta é incrementado: `objetivo.valor_atual += aporte.valor`.
     5. O `db.commit()` final grava todas as tabelas atomicamente.

4. **Garantia de Unicidade Composta em Planejamentos (RF05):**
   * A rota `POST /planejamentos/` valida a combinação quádrupla `(id_cartao, id_categoria, ano, mes)`, retornando `400 Bad Request` caso o usuário tente duplicar um orçamento já existente.

---

## 5. Tabela Resumo dos Endpoints Implementados

| Módulo | Método | Rota | Descrição | Regras Aplicadas |
| :--- | :---: | :--- | :--- | :--- |
| **Usuários** | `POST` | `/usuarios/` | Cadastro de usuário | Hash SHA-256 de senha, unicidade de e-mail |
| **Usuários** | `GET` | `/usuarios/` | Listagem geral | Omissão de campos sensíveis via Schema |
| **Categorias** | `POST` | `/categorias/` | Nova categoria | Unicidade por usuário (`id_usuario` + `nome`) |
| **Categorias** | `GET` | `/categorias` | Listagem geral | Retorno tipado em lista de Schemas |
| **Cartões** | `POST` | `/cartoes/` | Novo cartão de crédito | Validação de dias (1-31), checagem de usuário |
| **Cartões** | `GET` | `/cartoes/` | Listagem de cartões | Retorno de cartões cadastrados |
| **Transações** | `POST` | `/transacoes/` | Lançamento de receita/despesa | Validação cruzada (usuário + categoria + cartão opcional) |
| **Transações** | `GET` | `/transacoes/` | Extrato de transações | Visualização de todas as movimentações |
| **Objetivos** | `POST` | `/objetivos/` | Criação de meta financeira | Saldo inicial automático, meta > 0 |
| **Objetivos** | `GET` | `/objetivos/` | Listagem de metas | Retorno de metas e valores acumulados |
| **Aportes** | `POST` | `/aportes/` | Depósito em meta (RF08) | Criação atômica de despesa, `db.flush()`, saldo atualizado |
| **Planejamento** | `POST` | `/planejamentos/` | Teto de fatura por categoria | Validação de mês/ano, checagem de duplicidade |
| **Planejamento** | `GET` | `/planejamentos/` | Listagem de orçamentos | Visualização dos limites cadastrados |
