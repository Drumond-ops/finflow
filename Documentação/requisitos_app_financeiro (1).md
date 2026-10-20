# Documento de Requisitos - App Web de Controle Financeiro Pessoal

## 1. Visão Geral

O sistema é uma aplicação web responsiva (mobile-first) focada no controle de finanças pessoais. O aplicativo permite o lançamento de receitas e despesas, gerenciamento detalhado de cartões de crédito (com planejamento de faturas por categoria) e um módulo em formato de dashboard para acompanhamento de metas financeiras e investimentos.

## 2. Requisitos Funcionais (RF)

### Módulo de Lançamentos e Categorias

* **RF01 - Lançamento de Transações:** O usuário deve ser capaz de lançar receitas (entradas) e despesas (saídas).

* **RF02 - Categorização:** Toda despesa deve ser vinculada a uma categoria (ex: Mercado, Lazer, Transporte).

* RF03 - O usuario deve ser capaz de apagar uma categoria ou adicionar uma nova categoria a qualquer momento.

### Módulo de Cartões de Crédito

* **RF03 - Cadastro de Cartões:** O usuário deve poder cadastrar diferentes cartões de crédito, informando o nome do cartão e a data de vencimento da fatura (e opcionalmente a data de fechamento).

* **RF04 - Lançamento na Fatura:** O usuário deve conseguir associar uma despesa a um cartão de crédito específico, alocando esse gasto na fatura do mês correspondente.

* **RF05 - Planejamento da Próxima Fatura:** O sistema deve ter uma área para planejar a *próxima* fatura de um cartão, onde o usuário define um limite de gastos desejado por categoria (ex: "Mercado: R\$ 1500,00").

* **RF06 - Tracking da Fatura (Acompanhamento):** O sistema deve exibir o rastreamento em tempo real da fatura atual/próxima, comparando o que foi gasto até o momento com o valor planejado (orçado) para cada categoria, exibindo o saldo restante.

### Módulo de Objetivos e Investimentos

* **RF07 - Cadastro de Objetivos:** O usuário deve poder criar novos objetivos financeiros (ex: "Viagem de Férias", "Reserva de Emergência"), definindo um nome, um Valor Alvo (meta) a ser atingido e um valor inicial ja guradado (opcional). 

* **RF08 - Registro de Aportes:** O sistema deve permitir que o usuário adicione "aportes" (depósitos/transferências) a um objetivo específico. A cada aporte, o valor total guardado daquele objetivo deve ser atualizado automaticamente. Para cada novo aporte uma despesa deve ser gerada para aquele respectivo mes.

* **RF09 - Dashboard de Objetivos:** A área de investimentos deve funcionar como um painel visual (dashboard).

* **RF10 - Gráficos de Acompanhamento:** Cada objetivo no dashboard deve exibir um gráfico de pizza mostrando:

  * Valor absoluto já guardado.

  * Valor alvo (meta total).

  * Porcentagem de conclusão do objetivo.

Apresentacao dos dados

* RF11 - A pagina inicial padrao do app deve ser um dashboard com as despesas mais recentes, dados de economia do mes, dando preferencia para graficos.

* RF12 - O usuario deve ser capaz de gerar um relatorio em PDF que contenha os dados do mes solicitado. Nesse relatorio deve constar um extrato de receitas e despesas correntes, um extrato de fatura por cartao e se houver um planejamento feito para um determinado cartao deve ser mostrado a quantidade utilizada de cada categoria e o restante.

## 3. Requisitos Não Funcionais (RNF)

* **RNF01 - Responsividade (Mobile):** A aplicação web deve ser construída com design *Mobile-First*, garantindo que a interface, botões e gráficos funcionem e sejam perfeitamente renderizados no navegador do celular.

* **RNF02 - Usabilidade Visual:** O dashboard de investimentos deve utilizar bibliotecas de gráficos (como Chart.js ou Recharts) para renderizar os gráficos de pizza de forma clara e interativa.

## 4. Estrutura de Dados Sugerida

* **Usuario:** `id`, `nome`, `email`, `senha`

* **Categoria:** `id`, `nome`

* **CartaoCredito:** `id`, `id_usuario`, `nome`, `dia_vencimento`

* **Transacao:** `id`, `id_usuario`, `tipo(receita/despesa)`, `valor`, `data`, `id_categoria`, `id_cartao(null se não for no crédito)`

* **PlanejamentoFatura:** `id`, `id_cartao`, `mes_ano`, `id_categoria`, `valor_planejado`

* **Objetivo:** `id`, `id_usuario`, `nome`, `valor_alvo`, `valor_guardado_atual`

* **Aporte:** `id`, `id_objetivo`, `data`, `valor`