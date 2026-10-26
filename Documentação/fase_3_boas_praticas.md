# 📙 FinFlow — Documentação da Fase 3: Inteligência de Negócio, Agregações e Dashboards

Este documento registra todas as decisões de arquitetura analítica, otimizações de consultas ao banco de dados e **boas práticas de engenharia de software** adotadas durante a **Fase 3** do projeto **FinFlow**.

---

## 1. Onde Estamos no Projeto?

Concluímos **100% da inteligência analítica e das métricas do Backend**! Veja a linha do tempo atualizada do projeto:

| Fase | Descrição | Status |
| :--- | :--- | :---: |
| **Fase 1** | **Fundação & Infraestrutura:** Docker, PostgreSQL 16, conexão SQLAlchemy e mapeamento relacional das 7 tabelas. |  **100% Concluída** |
| **Fase 2** | **Camada de Aplicação & CRUDs Core:** Pydantic v2, injeção de dependências (`Annotated`), integridade referencial cruzada e endpoints para todas as 7 entidades. |  **100% Concluída** |
| **Fase 3** | **Inteligência de Negócio & Agregações:** Tracking de Faturas (**RF06**), Métricas de Objetivos (**RF10**) e Dashboard Consolidado da Página Inicial (**RF11**). |  **100% Concluída hoje!** |
| **Fase 4** | **Relatório em PDF (RF12) & Modularização (`APIRouter`):** Fechamento completo do Backend e arquitetura limpa em pastas. | ⏳ **A seguir** |
| **Fase 5** | **Frontend Web Mobile-First:** Interface responsiva, gráficos interativos (Chart.js/Recharts) e consumo da API. | ⏳ *Próxima etapa* |

---

## 2. Consultas Agregadas de Alta Performance (`func.sum` e `extract`)

### 2.1 Por que delegar somas e filtros para o PostgreSQL?
* **Má Prática Comum:** Buscar centenas ou milhares de linhas do banco para a memória RAM do Python e somar manualmente (`sum([t.valor for t in transacoes])`).
* **Padrão Adotado (Boa Prática):** Uso da coleção de funções SQL do SQLAlchemy (`func.sum` e `extract`), delegando o cálculo diretamente para o motor em C do PostgreSQL.
  ```python
  from sqlalchemy import func, extract

  total_fatura = db.query(func.sum(models.Transacao.valor)).filter(
      models.Transacao.id_cartao == id_cartao,
      extract("month", models.Transacao.data) == mes,
      extract("year", models.Transacao.data) == ano,
      models.Transacao.tipo == "despesa"
  ).scalar() or 0
  ```

### 2.2 A Proteção Essencial do `.scalar() or 0`
* O método `.scalar()` devolve o valor puro da primeira coluna da primeira linha.
* **A Pegadinha:** Quando o banco não encontra nenhuma linha para somar, o SQL devolve `NULL` (`None` no Python).
* Se tentarmos realizar operações matemáticas (`+`, `-`, `/`) com `None`, o Python estoura um erro fatal `TypeError: unsupported operand type(s)`.
* **Solução:** O uso sistemático de `.scalar() or 0` garante que valores nulos sejam convertidos no inteiro `0`, blindando o sistema contra quebras.

---

## 3. Tracking de Faturas em Tempo Real (RF06)

O endpoint `GET /cartoes/{id_cartao}/fatura/?mes={mes}&ano={ano}` calcula a situação financeira de um cartão de crédito em tempo real.

### 3.1 Anatomia do Cálculo por Categoria Planejada
Para cada categoria orçada no mês, a API executa:
1. `valor_planejado`: limite estipulado pelo usuário em `planejamentos`.
2. `valor_gasto`: soma de despesas do cartão naquela categoria específica no período.
3. `saldo`: `valor_planejado - valor_gasto` (valores negativos sinalizam que o usuário estourou o teto previsto).
4. `percentual`: porcentagem consumida do orçamento, com proteção contra divisão por zero:
   ```python
   percentual = round(gasto / plan.valor * 100, 2) if plan.valor > 0 else 0.0
   ```

### 3.2 Por que `ConfigDict(from_attributes=True)` foi dispensado?
* No tracking de faturas e no dashboard, **não existe uma tabela física `faturas` no banco de dados**.
* O resultado é construído como um **dicionário Python puro (`dict`)** calculado em tempo de execução.
* Como o Pydantic já possui suporte nativo a dicionários, a diretiva `from_attributes=True` (necessária para ler atributos de classes do SQLAlchemy) torna-se desnecessária nesses schemas de agregação.

---

## 4. Dashboard Consolidado da Página Inicial (RF11 & RF10)

Para alimentar a interface inicial do usuário sem sobrecarregar o cliente com múltiplas requisições HTTP, foi implementado o endpoint:
`GET /usuarios/{id_usuario}/dashboard?mes={mes}&ano={ano}`.

### 4.1 Estrutura do Payload Entregue ao Frontend

```
DashboardResponse
├── Metadados: mes, ano
├── KPIs Globais:
│   ├── total_receitas (centavos)
│   ├── total_despesas (despesas correntes fora de fatura)
│   └── total_faturas (soma de todas as faturas do mês)
├── Módulo de Cartões (faturas):
│   └── Lista de cartões com valor_planejado, valor_fatura e percentual individual (para múltiplos gráficos de pizza)
├── Módulo de Categorias (gastos_categoria):
│   └── Gastos correntes por categoria
├── Módulo de Metas (objetivos_resumo - RF10):
│   └── Metas do usuário com valor_alvo, valor_atual e percentual_conclusao
└── Extrato Rápido (resumo_transacao):
    └── As 5 últimas movimentações com ordenação decrescente: models.Transacao.id.desc()
```

### 4.2 Lições de Código e Cuidados de Sintaxe Aprendidos
1. **Escopo e Indentação de Retorno:**
   * Garantir que o comando `return` fique estritamente fora do loop de iteração de categorias (`for cat in categorias:`), evitando que o processamento seja interrompido na primeira categoria.
2. **Compatibilidade Rigorosa entre Dicionários e Schemas:**
   * Qualquer discrepância tipográfica entre a chave do dicionário de retorno (ex: `"valor_planejado"`) e o nome do campo no Pydantic impede a validação e gera erro 500.
3. **Tipagem Correta de Valores Monetários:**
   * Garantir que campos monetários agregados sejam tipados como `int` (centavos), mantendo o padrão Stripe em toda a cadeia da aplicação.

---

## 5. Status dos Requisitos do Projeto

Com a conclusão da Fase 3, cobrimos **11 dos 12 Requisitos Funcionais** especificados para o FinFlow:

* [x] **RF01:** Lançamento de Transações (Receitas e Despesas).
* [x] **RF02:** Categorização de despesas.
* [x] **RF03:** Gerenciamento de Categorias e Cartões de Crédito.
* [x] **RF04:** Associação de despesas a faturas de cartões.
* [x] **RF05:** Planejamento orçamentário por categoria na próxima fatura.
* [x] **RF06:** Tracking e acompanhamento em tempo real do saldo de fatura.
* [x] **RF07:** Cadastro de Objetivos financeiros.
* [x] **RF08:** Registro de Aportes com atualização de saldo e geração atômica de despesa.
* [x] **RF09:** Painel de Objetivos.
* [x] **RF10:** Métricas de acompanhamento de metas (alvo, atual e percentual).
* [x] **RF11:** Dashboard da página inicial com faturas, categorias e extrato.
* [ ] **RF12:** **Geração de Relatório mensal em PDF** *(Próxima etapa!)*
