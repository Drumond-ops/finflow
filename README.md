# FinFlow 💸

Plataforma de controle financeiro pessoal: o usuário acompanha seu orçamento mensal, lança despesas e fontes de renda, controla faturas de cartão com planejamento por categoria, acompanha objetivos de investimento e gera relatórios mensais em PDF.

Projeto de **Laboratório de Programação II — IME** (Grupo 6: Drumond, Wilker e Negromonte).

| Camada | Tecnologia |
| :--- | :--- |
| Backend (API REST) | Python 3.14, FastAPI, SQLAlchemy 2, Pydantic v2 |
| Banco de dados | PostgreSQL 16 (via Docker) |
| Autenticação | JWT (PyJWT) + senhas com bcrypt |
| Relatórios | fpdf2 |
| Testes | pytest |
| Execução | Docker Compose (banco + API) |

---

## 🚀 Como rodar na sua máquina

Tudo roda dentro do Docker: o banco (PostgreSQL 16) e a API (Python 3.14). Você **não precisa** instalar Python nem bibliotecas no seu computador.

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

**3. Suba o banco e a API**
```bash
docker compose up --build
```
Na primeira vez demora alguns minutos (baixa o Python 3.14 e instala as dependências). Está pronto quando aparecer `Application startup complete`.
As tabelas são criadas automaticamente. Depois de mudar o código, rode `docker compose up --build` de novo para a API pegar as mudanças.
Para parar: `Ctrl+C` no terminal (ou `docker compose down` em outro terminal).

**4. Teste pelo navegador:** abra **http://localhost:8000/docs**
1. Em `POST /auth/registro`, clique em *Try it out* e crie uma conta.
2. Clique no botão **Authorize** 🔒 no topo da página e entre com o e-mail (no campo *username*) e a senha.
3. Pronto: todas as rotas agora funcionam como o seu usuário.

### Rodando os testes automatizados
Com o projeto rodando (passo 3), em **outro terminal**:
```bash
docker compose exec api pytest
```
Os testes usam um banco SQLite temporário em memória, então não mexem nos seus dados.

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
| Planejamentos | `POST /planejamentos/` | `GET /planejamentos/?mes=&ano=&id_cartao=` · `GET /planejamentos/{id}` | `PUT /planejamentos/{id}` | `DELETE /planejamentos/{id}` |

**Consultas analíticas**

| Rota | O que faz |
| :--- | :--- |
| `GET /dashboard/?mes=10&ano=2026` | Resumo do mês: receitas, despesas, faturas, saldo, gastos por categoria, últimas transações, objetivos (RF11) |
| `GET /cartoes/{id}/fatura/?mes=10&ano=2026` | Fatura do cartão: planejado × gasto por categoria (RF06) |
| `GET /relatorios/pdf?mes=10&ano=2026` | Baixa o relatório mensal em PDF (RF12) |

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
├── relatorio_pdf.py     # montagem do PDF
├── routers/             # uma rota por recurso (auth, transacoes, cartoes...)
├── tests/               # testes automatizados (pytest)
├── Dockerfile           # imagem da API (Python 3.14)
├── docker-compose.yml   # sobe banco (PostgreSQL 16) + API
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
| No PowerShell: "execução de scripts foi desabilitada" | Rode uma vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
