# FinFlow 💸

Plataforma de controle financeiro pessoal: o usuário acompanha seu orçamento mensal, lança despesas e fontes de renda, controla faturas de cartão com planejamento por categoria, acompanha objetivos de investimento e gera relatórios mensais em PDF.

Projeto de **Laboratório de Programação II — IME** (Grupo 6: Drumond, Wilker e Negromonte).

| Camada | Tecnologia |
| :--- | :--- |
| API principal | Python 3.14, FastAPI, SQLAlchemy 2, Pydantic v2 |
| Serviço de assinaturas | Java 21, Spring Boot 3.5 (Web, Data JPA, Validation), springdoc (Swagger) |
| Banco de dados | PostgreSQL 16 (via Docker) |
| Autenticação | JWT (PyJWT) + senhas com bcrypt |
| Relatórios | fpdf2 |
| Testes | pytest (Python) e JUnit 5 (Java) |
| Execução | Docker Compose (banco + API Python + API Java) |

### Arquitetura

```text
                 ┌──────────────────────────────┐
                 │  Frontend (HTML/CSS/JS)      │
                 └──────┬───────────────┬───────┘
          token JWT     │               │     mesmo token JWT
                        ▼               ▼
   ┌─────────────────────────┐   ┌──────────────────────────────┐
   │ API Python (FastAPI)    │   │ Serviço de assinaturas (Java)│
   │ :8000                   │   │ Spring Boot  :8081           │
   │ login, transações,      │   │ assinaturas, próximas        │
   │ cartões, faturas,       │   │ cobranças, lançamento das    │
   │ orçamento, dashboard,   │   │ cobranças como despesas      │
   │ objetivos, PDF          │   │                              │
   └───────────┬─────────────┘   └──────────────┬───────────────┘
               └──────────────┬─────────────────┘
                              ▼
                   ┌──────────────────────┐
                   │ PostgreSQL 16 (:5432)│
                   └──────────────────────┘
```

- O usuário faz login **uma vez** na API Python. O serviço Java confere o mesmo token (mesma `SECRET_KEY`).
- As duas APIs usam o **mesmo banco**. A API Python cria todas as tabelas (`models.py`); o Java só usa.
- As cobranças das assinaturas viram despesas comuns, então aparecem na fatura, no dashboard e no orçamento.

---

## 🚀 Como rodar na sua máquina

Tudo roda dentro do Docker: o banco (PostgreSQL 16), a API em Python 3.14 e o serviço em Java 21. Você **não precisa** instalar Python, Java nem bibliotecas no seu computador.

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — precisa estar **aberto** enquanto você usa o projeto
- [Git](https://git-scm.com/downloads)

### Passo a passo

**1. Baixe o projeto e entre na pasta**
```bash
git clone https://github.com/Drumond-ops/finflow.git
cd finflow
```

**2. (Opcional) Configure senhas próprias**
O projeto já funciona com senhas de desenvolvimento. Para usar as suas, copie `.env.example` para `.env` e troque `POSTGRES_PASSWORD` e `SECRET_KEY`.

**3. Suba tudo**
```bash
docker compose up -d --build
```
Na primeira vez demora alguns minutos (baixa o Python, o Java e as bibliotecas). Confira com `docker compose ps`: os três containers (`postgres_financas`, `finflow_api`, `finflow_assinaturas`) devem estar `Up`.
As tabelas são criadas automaticamente. Depois de mudar o código, rode `docker compose up --build` de novo para a API pegar as mudanças.
Para ver os logs: `docker compose logs -f api` ou `docker compose logs -f assinaturas`. Para parar: `docker compose down`.

**4. Teste a API Python:** abra **http://localhost:8000/docs**
1. Em `POST /auth/registro`, clique em *Try it out* e crie uma conta.
2. Clique no botão **Authorize** 🔒 no topo da página e entre com o e-mail (no campo *username*) e a senha.
3. Pronto: todas as rotas agora funcionam como o seu usuário.

**5. Teste o serviço Java:** abra **http://localhost:8081/swagger-ui.html**
1. Na API Python, rode `POST /auth/login` (Try it out, e-mail em *username*) e copie o `access_token` da resposta.
2. No Swagger do Java, clique em **Authorize**, cole o token e confirme.
3. Teste `POST /assinaturas`, `GET /assinaturas/resumo` e `POST /assinaturas/lancamentos?mes=11&ano=2026`.

### Rodando os testes automatizados
Python, com o projeto rodando:
```bash
docker compose exec api pytest
```
Os testes usam um banco SQLite temporário em memória, então não mexem nos seus dados.

Java: os testes rodam sozinhos toda vez que a imagem é construída (`docker compose up --build`). Se algum falhar, o build para e mostra qual.

### (Opcional) Rodar sem Docker
Funciona com o Python **oficial** do python.org (3.11 a 3.14). O Python que vem com o MSYS2/MinGW não serve, porque não existem versões prontas das bibliotecas para ele.
```bash
# antes, adicione ao serviço "db" do docker-compose.yml:   ports: ["5432:5432"]
docker compose up -d db          # sobe só o banco
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows (PowerShell) — no Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
fastapi dev main.py
```

---

## 🧭 Endpoints

Todos os valores em dinheiro são **inteiros em centavos** (R$ 12,34 = `1234`), para evitar erros de arredondamento com `float`.
Todas as rotas (exceto `/auth/*`) exigem o cabeçalho `Authorization: Bearer <token>`.

| Recurso | Create | Retrieve | Update | Delete |
| :--- | :--- | :--- | :--- | :--- |
| Autenticação | `POST /auth/registro` · `POST /auth/login` | | | |
| Usuário logado | (registro) | `GET /usuarios/me` | `PUT /usuarios/me` · `PUT /usuarios/me/senha` | `DELETE /usuarios/me` |
| Categorias | `POST /categorias/` | `GET /categorias/` · `GET /categorias/{id}` | `PUT /categorias/{id}` | `DELETE /categorias/{id}?mover_para={id}` |
| Cartões | `POST /cartoes/` | `GET /cartoes/` · `GET /cartoes/{id}` | `PUT /cartoes/{id}` | `DELETE /cartoes/{id}` |
| Transações | `POST /transacoes/` | `GET /transacoes/?mes=&ano=&tipo=&id_categoria=&id_cartao=` · `GET /transacoes/{id}` | `PUT /transacoes/{id}` | `DELETE /transacoes/{id}` |
| Objetivos | `POST /objetivos/` | `GET /objetivos/` · `GET /objetivos/{id}` · `GET /objetivos/{id}/aportes` | `PUT /objetivos/{id}` | `DELETE /objetivos/{id}` |
| Aportes | `POST /aportes/` | `GET /aportes/?id_objetivo=` · `GET /aportes/{id}` | `PUT /aportes/{id}` | `DELETE /aportes/{id}` |
| Planejamentos (por fatura) | `POST /planejamentos/` | `GET /planejamentos/?mes=&ano=&id_cartao=` · `GET /planejamentos/{id}` | `PUT /planejamentos/{id}` | `DELETE /planejamentos/{id}` |
| Orçamento mensal | `POST /orcamentos/` · `POST /orcamentos/copiar?de_mes=&de_ano=&para_mes=&para_ano=` | `GET /orcamentos/?mes=&ano=` · `GET /orcamentos/{id}` | `PUT /orcamentos/{id}` | `DELETE /orcamentos/{id}` |

**Consultas analíticas**

| Rota | O que faz |
| :--- | :--- |
| `GET /dashboard/?mes=10&ano=2026` | Resumo do mês: receitas, despesas, faturas, saldo, gastos por categoria, últimas transações, objetivos e orçamento (RF11) |
| `GET /cartoes/{id}/fatura/?mes=10&ano=2026` | Fatura que **vence** no mês, respeitando o dia de fechamento: planejado × gasto por categoria (RF06) |
| `GET /orcamentos/resumo?mes=10&ano=2026` | Orçado × gasto por categoria no mês (conta + cartão), com status `ok`, `atencao` (80%+) ou `estourado` |
| `GET /relatorios/pdf?mes=10&ano=2026` | Baixa o relatório mensal em PDF (RF12) |

### Serviço de assinaturas (Java) — `http://localhost:8081`

Mesmo token da API Python no cabeçalho `Authorization: Bearer <token>`. JSON em snake_case, valores em centavos.

| Operação | Rota |
| :--- | :--- |
| Create | `POST /assinaturas` |
| Retrieve | `GET /assinaturas` · `GET /assinaturas/{id}` |
| Update | `PUT /assinaturas/{id}` (use `"ativa": false` para pausar) |
| Delete | `DELETE /assinaturas/{id}` |
| Resumo | `GET /assinaturas/resumo?dias=30`: custo mensal e anual das ativas e próximas cobranças |
| Lançar cobranças | `POST /assinaturas/lancamentos?mes=11&ano=2026`: cria as despesas do mês (no cartão da assinatura, se houver). Rodar de novo não duplica. |

Exemplo de corpo do `POST /assinaturas`:
```json
{
  "nome": "Netflix",
  "valor": 5590,
  "periodicidade": "MENSAL",
  "data_inicio": "2026-01-15",
  "id_cartao": 1
}
```
`periodicidade` é `MENSAL` ou `ANUAL`. A `data_inicio` define o dia da cobrança (e o mês, se for anual). Sem `id_categoria`, a despesa vai para a categoria "Assinaturas".

### Regra da fatura

A fatura "de novembro" é a que **vence** em novembro. Ela contém as compras entre o fechamento anterior e o fechamento atual. Exemplo: cartão que fecha dia 3 e vence dia 10 → a fatura de novembro tem as compras de 04/10 a 03/11, e uma compra em 05/11 já cai na fatura de dezembro. Cartão sem dia de fechamento usa o mês do calendário.

---

## 📁 Estrutura

```text
finflow/
├── main.py              # cria o app, CORS, cria tabelas e registra os routers
├── config.py            # lê as configurações do .env
├── database.py          # conexão com o banco (engine, sessão)
├── models.py            # tabelas (SQLAlchemy)
├── schemas.py           # formato dos dados que entram e saem (Pydantic)
├── seguranca.py         # hash de senha (bcrypt) e tokens JWT
├── deps.py              # dependências compartilhadas: sessão, usuário logado, buscas seguras
├── ciclo_fatura.py      # regra de datas da fatura (fechamento/vencimento)
├── relatorio_pdf.py     # montagem do PDF
├── routers/             # uma rota por recurso (auth, transacoes, cartoes...)
├── tests/               # testes automatizados (pytest)
├── Dockerfile           # imagem da API (Python 3.14)
├── docker-compose.yml   # sobe banco + API Python + serviço Java
├── servico-assinaturas/ # serviço em Java (Spring Boot)
│   ├── pom.xml          # dependências (Maven)
│   ├── Dockerfile       # compila com Maven e roda com Java 21
│   └── src/main/java/br/ime/finflow/assinaturas/
│       ├── web/         # controllers (rotas REST) e tratamento de erros
│       ├── servico/     # regras de negócio e calendário de cobranças
│       ├── dominio/     # entidades JPA (tabelas)
│       ├── repositorio/ # acesso ao banco (Spring Data)
│       ├── dto/         # formatos de entrada e saída
│       ├── seguranca/   # validação do token JWT
│       └── config/      # CORS e registro do interceptor de login
├── .env.example         # modelo das variáveis de ambiente
└── Documentação/        # requisitos, modelos do banco e registro de cada fase
```

---

## 🛠️ Problemas comuns

| Sintoma | Solução |
| :--- | :--- |
| `password authentication failed` | O volume do Docker guardou a senha antiga. Rode `docker compose down -v` (**apaga os dados do banco**) e depois `docker compose up -d`. |
| `port 5432 is already allocated` | Só acontece se você expôs a porta do banco: já existe outro Postgres na sua máquina. Use `"5433:5432"` no `ports` do serviço `db`. |
| `ModuleNotFoundError` ao rodar sem Docker | O ambiente virtual não está ativado. |
| `pg_config executable not found` ao instalar sem Docker | Seu Python não é o oficial (ex.: MSYS2). Use o Docker (passo 3) ou instale o Python do python.org. |
| Mudei o `requirements.txt` e a API não achou o pacote novo | Rode `docker compose up --build` para reconstruir a imagem. |
| Erro de CORS no navegador | Adicione o endereço do seu frontend em `CORS_ORIGINS` no `.env` e rode `docker compose up -d` de novo. |
| `finflow_assinaturas` reiniciando sem parar | Veja o motivo com `docker compose logs assinaturas`. Se for erro de conexão com o banco, espere o `db` ficar saudável e rode `docker compose up -d` de novo. |
| Swagger do Java responde 401 nas rotas | Faltou o token: faça login na API Python e cole o `access_token` em **Authorize**. |
| No PowerShell: "execução de scripts foi desabilitada" | Rode uma vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
