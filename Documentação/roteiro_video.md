# Roteiro do vídeo de demonstração (5 a 10 minutos)

Segue a ordem pedida no enunciado. Os tempos somam cerca de 8 minutos.
Antes de gravar: `docker compose down -v` (banco limpo), feche abas extras e deixe o navegador em tela cheia.

---

## 1. Apresentação (até 1 min)

- Quem somos: Drumond, Wilker e Negromonte, Grupo 6 de Laboratório de Programação II.
- O que é o FinFlow: controle financeiro pessoal. Mostra o mês (receitas, despesas, faturas e saldo), o orçamento por categoria, as faturas dos cartões respeitando o fechamento, as assinaturas e os objetivos.
- Arquitetura em uma frase: frontend em HTML/CSS/JS puro, API Python (FastAPI) com o núcleo financeiro e API Java (Spring Boot) com as assinaturas. As duas usam o mesmo banco e o mesmo login.

## 2. Execução (1 min)

No terminal, na pasta do projeto:

```bash
docker compose up -d --build
docker compose ps
```

Mostrar os quatro serviços `Up` e as portas: frontend 8080, API Python 8000, API Java 8081, banco 5433.
Abrir rapidamente `http://localhost:8000/docs` e `http://localhost:8081/swagger-ui.html` para mostrar que são duas APIs independentes.

## 3. Funcionalidades (3 min)

Em `http://localhost:8080`:

1. **Criar conta** e entrar.
2. **Cartões**: adicionar "Nubank", fecha dia 3, vence dia 10.
3. **Lançamentos**: Nova transação de R$ 4.800,00 de salário. Depois uma despesa no cartão Nubank com data depois do dia 3. Mostrar a dica "Entra na fatura que vence em…".
4. **Orçamento**: definir limite de Mercado e Lazer. Mostrar a barra de uso e a situação (dentro, perto, estourou).
5. **Assinaturas**: cadastrar Netflix (mensal, no cartão) e clicar em **Lançar cobranças do mês**.
6. **Cartões e faturas**: mostrar a fatura com o período, as compras (inclusive a Netflix lançada pela API Java) e o planejado × gasto.
7. **Objetivos**: criar "Viagem" e fazer um aporte. Mostrar que virou despesa em Lançamentos.
8. **Painel**: mostrar o resumo do mês, o gráfico por dia, os gastos por categoria e baixar o **relatório PDF**.
9. Erro tratado: tentar salvar uma transação com valor "abc" e mostrar a mensagem, sem quebrar nada.

## 4. Integração (1 min 30 s)

- Abrir o painel **Requisições** na barra inferior: em azul as chamadas da API Python (`:8000`), em laranja as da API Java (`:8081`).
- Abrir também o **DevTools → aba Network** e:
  - Na tela **Assinaturas**, mostrar `GET http://localhost:8081/assinaturas` (Java) e `GET http://localhost:8000/cartoes/` (Python, para o formulário).
  - Clicar em **Lançar cobranças** e mostrar o `POST :8081/assinaturas/lancamentos`. Depois, em Lançamentos, a despesa aparece vindo do `GET :8000/transacoes/`.
  - No **Painel**, mostrar que a mesma tela chama as duas APIs ao mesmo tempo (`/dashboard/` na 8000 e `/assinaturas/resumo` na 8081).
- Mostrar o cabeçalho `Authorization: Bearer …` igual nas duas: um login só.

## 5. Código (1 min 30 s)

Mostrar um trecho de cada parte:

| Parte | Arquivo | O que mostrar |
| :--- | :--- | :--- |
| API Python | `api-python/routers/orcamentos.py` | A rota `GET /orcamentos/resumo` e a função `calcular_resumo` (soma conta + cartão e define a situação) |
| API Java | `api-java/.../web/AssinaturaController.java` e `servico/AssinaturaService.java` | `@PostMapping("/lancamentos")` e o método `lancarCobrancas` (cria as despesas e não duplica) |
| Login compartilhado | `api-java/.../seguranca/JwtService.java` | Como o Java confere o token gerado pelo Python (HMAC-SHA256 com a mesma chave) |
| Frontend | `frontend/js/api.js` | A função `requisitar` (envia o token, trata erro e registra a requisição) e os clientes `python` e `java` |
| Frontend | `frontend/js/paginas/assinaturas.js` | `java.post("/assinaturas/lancamentos", …)` sendo chamado pelo botão |

## 6. Divisão do trabalho (30 s)

Cada integrante fala o que desenvolveu (a tabela está no `README.md`).
