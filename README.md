# FinFlow

Plataforma web de controle financeiro pessoal. O usuário acompanha o orçamento do mês, lança despesas e fontes de renda, controla as faturas dos cartões (respeitando o dia de fechamento), acompanha as assinaturas cobradas no cartão e guarda dinheiro para objetivos.

**Laboratório de Programação II — IME — Grupo 6**

| Integrantes |
| :--- |
| Drumond |
| Wilker |
| Negromonte |

---

## Como as partes se conectam

```text
                    ┌──────────────────────────────────┐
                    │  frontend/   HTML, CSS e JS puro  │
                    │  http://localhost:8080            │
                    └───────┬───────────────────┬──────┘
                            │                   │
           login, lançamentos,                  │  assinaturas
           cartões, orçamento...                │  (mesmo token de login)
                            ▼                   ▼
          ┌──────────────────────────┐   ┌──────────────────────────┐
          │ api-python/  FastAPI     │   │ api-java/  Spring Boot   │
          │ http://localhost:8000    │   │ http://localhost:8081    │
          └────────────┬─────────────┘   └─────────────┬────────────┘
                       └──────────────┬────────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │ PostgreSQL 16 (Docker)  │
                         │ localhost:5433          │
                         └─────────────────────────┘
```

- As duas APIs são **independentes**: cada uma tem seu código, sua porta e sua imagem Docker.
- O login é feito na API Python, que devolve um token JWT. A API Java confere o **mesmo token** (as duas usam a mesma `SECRET_KEY`), então o usuário entra uma vez só.
- As cobranças das assinaturas (API Java) viram despesas comuns. Assim, aparecem nas faturas, no painel e no orçamento da API Python.
- Todas as respostas são JSON. Os erros também: `{"detail": "mensagem"}`, com o código HTTP certo (401, 404, 409, 422 ou 500), sem derrubar a API.

## Tecnologias

| Parte | Tecnologias |
| :--- | :--- |
| `api-python/` | Python 3.14, FastAPI, SQLAlchemy 2, Pydantic 2, PyJWT, bcrypt, fpdf2, pytest |
| `api-java/` | Java 21, Spring Boot 3.5 (Web, Data JPA, Validation), springdoc-openapi (Swagger), JUnit 5, Maven |
| `frontend/` | HTML, CSS e JavaScript puro (módulos ES), sem framework; gráficos em SVG; servido pelo nginx |
| Banco | PostgreSQL 16 |
| Execução | Docker e Docker Compose |

---

## Como executar

### Opção 1: tudo com Docker (recomendado)

Só precisa do [Docker Desktop](https://www.docker.com/products/docker-desktop/) aberto e do [Git](https://git-scm.com/downloads). Não é preciso instalar Python, Java nem Node.

```bash
git clone https://github.com/Drumond-ops/finflow.git
cd finflow
docker compose up -d --build
```

Na primeira vez demora alguns minutos, porque baixa as imagens e compila o Java. Depois confira:

```bash
docker compose ps
```

Os quatro serviços precisam estar `Up`:

| Serviço | Endereço | O que é |
| :--- | :--- | :--- |
| `frontend` | **http://localhost:8080** | A plataforma (abra no navegador) |
| `api-python` | http://localhost:8000/docs | API Python e sua documentação interativa |
| `api-java` | http://localhost:8081/swagger-ui.html | API Java e sua documentação interativa |
| `db` | localhost:5433 | PostgreSQL (usuário `admin_financas`, senha `finflow_dev`, banco `financeiro_db`) |

Abra **http://localhost:8080**, clique em **Criar conta** e use a plataforma.

Outros comandos úteis:

```bash
docker compose logs -f api-python      # logs de um serviço (api-python, api-java, frontend, db)
docker compose down                    # desliga tudo (os dados continuam salvos)
docker compose down -v                 # desliga e APAGA os dados do banco
docker compose up -d --build           # depois de mudar o código, reconstrói e sobe de novo
```

> Configuração opcional: sem nada configurado, o projeto usa valores de desenvolvimento. Para usar senha e chave próprias, copie `.env.example` para `.env` e edite. O `.env` não vai para o GitHub.

### Opção 2: cada parte separadamente (sem Docker para as APIs)

Útil para desenvolver. O banco continua no Docker.

**1. Banco de dados** (porta 5433)
```bash
docker compose up -d db
```

**2. API Python** (porta 8000). Requer o [Python 3.11 ou mais novo](https://www.python.org/downloads/) oficial.
```bash
cd api-python
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows (PowerShell). No Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
fastapi dev main.py
```
As tabelas são criadas automaticamente ao subir. Testes: `pytest` (dentro de `api-python/`).

**3. API Java** (porta 8081). Requer [JDK 21](https://adoptium.net/) e [Maven 3.9](https://maven.apache.org/download.cgi). Suba depois da API Python, que é quem cria as tabelas.
```bash
cd api-java
mvn spring-boot:run
```
Testes: `mvn test` (dentro de `api-java/`).

**4. Frontend** (porta 8080). Qualquer servidor de arquivos estáticos serve. Com Python:
```bash
cd frontend
python -m http.server 8080
```
Também funciona com a extensão Live Server do VS Code (porta 5500). Os endereços das APIs ficam em `frontend/js/config.js`.

> Abrir o `index.html` direto pelo explorador de arquivos (`file://`) não funciona, porque o navegador bloqueia módulos JavaScript fora de um servidor.

---

## Endpoints

Valores em dinheiro são **inteiros em centavos** (R$ 12,34 = `1234`). Datas no formato `AAAA-MM-DD`.
Exceto login, cadastro e status, todas as rotas exigem o cabeçalho `Authorization: Bearer <token>`.

### API Python — `http://localhost:8000`

| Método | Rota | O que faz |
| :--- | :--- | :--- |
| GET | `/` | Status da API |
| POST | `/auth/registro` | Cria conta (e 11 categorias padrão) |
| POST | `/auth/login` | Login (formulário `username` + `password`); devolve o token JWT |
| GET, PUT, DELETE | `/usuarios/me` | Ler, editar e excluir a própria conta |
| PUT | `/usuarios/me/senha` | Trocar senha |
| GET, POST | `/categorias/` | Listar e criar categorias |
| GET, PUT, DELETE | `/categorias/{id}` | Ler, renomear e excluir (`?mover_para={id}` se estiver em uso) |
| GET, POST | `/cartoes/` | Listar e criar cartões |
| GET, PUT, DELETE | `/cartoes/{id}` | Ler, editar e excluir cartão |
| GET | `/cartoes/{id}/fatura/?mes=&ano=` | Fatura que vence no mês: período, total e planejado × gasto por categoria |
| GET, POST | `/transacoes/` | Listar (filtros `mes`, `ano`, `tipo`, `id_categoria`, `id_cartao`, `data_inicio`, `data_fim`) e criar |
| GET, PUT, DELETE | `/transacoes/{id}` | Ler, editar e excluir lançamento |
| GET, POST | `/planejamentos/` | Listar e criar limites por categoria numa fatura |
| GET, PUT, DELETE | `/planejamentos/{id}` | Ler, editar e excluir planejamento |
| GET, POST | `/orcamentos/` | Listar e criar limites mensais por categoria |
| GET | `/orcamentos/resumo?mes=&ano=` | Orçado × gasto do mês (conta + cartão) com situação ok, atenção ou estourado |
| POST | `/orcamentos/copiar?de_mes=&de_ano=&para_mes=&para_ano=` | Copia os limites de um mês para outro |
| GET, PUT, DELETE | `/orcamentos/{id}` | Ler, editar e excluir limite |
| GET, POST | `/objetivos/` | Listar e criar objetivos |
| GET, PUT, DELETE | `/objetivos/{id}` | Ler, editar e excluir objetivo |
| GET | `/objetivos/{id}/aportes` | Aportes de um objetivo |
| GET, POST | `/aportes/` | Listar e criar aportes (cada aporte gera uma despesa) |
| GET, PUT, DELETE | `/aportes/{id}` | Ler, editar e desfazer aporte |
| GET | `/dashboard/?mes=&ano=` | Resumo do mês: receitas, despesas, faturas, saldo, gastos por categoria, orçamento e objetivos |
| GET | `/relatorios/pdf?mes=&ano=` | Relatório mensal em PDF |

### API Java — `http://localhost:8081`

| Método | Rota | O que faz |
| :--- | :--- | :--- |
| GET | `/` | Status da API |
| GET, POST | `/assinaturas` | Listar e cadastrar assinaturas |
| GET, PUT, DELETE | `/assinaturas/{id}` | Ler, editar (inclusive pausar com `"ativa": false`) e excluir |
| GET | `/assinaturas/resumo?dias=30` | Custo mensal e anual das ativas e próximas cobranças |
| POST | `/assinaturas/lancamentos?mes=&ano=` | Lança as cobranças do mês como despesas (não duplica se repetir) |

Exemplo de corpo do `POST /assinaturas`:
```json
{ "nome": "Netflix", "valor": 5590, "periodicidade": "MENSAL", "data_inicio": "2026-01-15", "id_cartao": 1 }
```

### Respostas de erro (as duas APIs)

| Situação | Resposta |
| :--- | :--- |
| Sem login ou token vencido | `401 {"detail": "Token inválido ou expirado. Faça login novamente."}` |
| Item inexistente ou de outro usuário | `404 {"detail": "Transação não encontrado(a)"}` |
| Dado inválido (ex.: valor negativo, mês 13) | `422 {"detail": ...}` |
| Conflito (ex.: e-mail já cadastrado, categoria em uso) | `409 {"detail": ...}` |
| Erro inesperado | `500 {"detail": "Erro interno no servidor. Tente novamente."}`, e a API continua no ar |

---

## Frontend

| Tela | O que faz | API usada |
| :--- | :--- | :--- |
| Entrar | Login e cadastro | Python |
| Painel | Resumo do mês, despesas por dia, gastos por categoria, orçamento, faturas, assinaturas, objetivos e relatório PDF | Python **e** Java |
| Lançamentos | Receitas e despesas do mês, com filtros, totais e edição | Python |
| Cartões e faturas | Cartões e fatura do mês com período, planejado × gasto e compras | Python |
| Orçamento | Limites do mês por categoria, situação e cópia do mês anterior | Python |
| Assinaturas | Cadastro, pausa, custos, próximas cobranças e lançamento das cobranças | **Java** (cartões e categorias vêm da Python) |
| Objetivos | Metas, progresso e aportes | Python |
| Categorias | Criar, renomear e excluir (movendo os lançamentos) | Python |
| Minha conta | Perfil, senha, situação das APIs e exclusão da conta | Python |

A barra inferior mostra cada requisição feita pela tela: em azul as da API Python, em laranja as da API Java. O botão **Requisições** abre o histórico completo.

---

## Estrutura do repositório

```text
finflow/
├── api-python/            API em Python (FastAPI)
│   ├── main.py            cria o app, CORS, tratamento de erros, registra as rotas
│   ├── config.py          lê as configurações (.env)
│   ├── database.py        conexão com o banco
│   ├── models.py          tabelas (todas, inclusive as usadas pela API Java)
│   ├── schemas.py         formatos de entrada e saída (Pydantic)
│   ├── seguranca.py       bcrypt e JWT
│   ├── deps.py            usuário logado e buscas seguras
│   ├── ciclo_fatura.py    regra de fechamento e vencimento da fatura
│   ├── relatorio_pdf.py   montagem do PDF
│   ├── routers/           uma rota por recurso
│   ├── tests/             testes (pytest)
│   ├── requirements.txt
│   └── Dockerfile
├── api-java/              API em Java (Spring Boot)
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/main/java/br/ime/finflow/assinaturas/
│       ├── web/           controllers (rotas) e tratamento de erros
│       ├── servico/       regras de negócio e calendário de cobranças
│       ├── dominio/       entidades JPA
│       ├── repositorio/   acesso ao banco (Spring Data)
│       ├── dto/           formatos de entrada e saída
│       ├── seguranca/     validação do token JWT
│       └── config/        CORS e interceptor de login
├── frontend/              HTML, CSS e JS puro
│   ├── index.html
│   ├── css/app.css
│   ├── js/api.js          chamadas às duas APIs (token, erros, registro de requisições)
│   ├── js/app.js          menu, rotas e seletor de mês
│   ├── js/paginas/        uma tela por arquivo
│   └── Dockerfile         nginx
├── Documentação/          requisitos, modelos do banco, registro de cada fase e roteiro do vídeo
├── docker-compose.yml     sobe banco, API Python, API Java e frontend
└── .env.example           modelo de configuração (opcional)
```

---

## Divisão do trabalho

| Integrante | O que desenvolveu |
| :--- | :--- |
| Drumond | Modelagem do banco e estrutura inicial da API Python (rotas, dashboard, fatura, relatório PDF) |
| Wilker | Login com JWT, CRUD completo, Docker, API Java de assinaturas, orçamento, ciclo da fatura e frontend |
| Negromonte | Ajustes no frontend: correção do título de janela escapado duas vezes, botão "Hoje" no seletor de mês, mostrar/ocultar senha, limpar filtros, contador e exportação CSV nos lançamentos, atalhos de teclado (N, [ e ]), modo escuro automático e comparação com o mês anterior no painel |

---

## Problemas comuns

| Sintoma | Solução |
| :--- | :--- |
| `port is already allocated` | Outro programa usa a porta (8000, 8080, 8081 ou 5433). Feche-o ou troque a porta da esquerda no `docker-compose.yml`. |
| A tela mostra "Não foi possível falar com a API…" | A API não está no ar. Veja `docker compose ps` e `docker compose logs api-python` (ou `api-java`). |
| `password authentication failed` | O banco guardou uma senha antiga. Rode `docker compose down -v` (**apaga os dados**) e suba de novo. |
| Containers antigos com outros nomes ainda rodando | `docker compose up -d --build --remove-orphans` |
| Erro de CORS no navegador | Abra o frontend por `http://localhost:8080` (não pelo `file://`). Para outra porta, adicione-a em `CORS_ORIGINS` no `.env`. |
| `pg_config executable not found` no `pip install` | O Python não é o oficial (ex.: MSYS2). Use a opção com Docker ou instale o Python do python.org. |
| PowerShell: "execução de scripts foi desabilitada" | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
