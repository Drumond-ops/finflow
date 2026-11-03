# 📗 FinFlow — Documentação da Fase 4: Autenticação, CRUD Completo e Projeto Replicável

Este documento registra o que mudou na **Fase 4**, **por que** cada mudança foi feita e os conceitos por trás dela — serve também como material de estudo para o grupo.

---

## 1. Onde Estamos no Projeto?

| Fase | Descrição | Status |
| :--- | :--- | :---: |
| **Fase 1** | Fundação & Infraestrutura: Docker, PostgreSQL 16, SQLAlchemy, 7 tabelas | ✅ |
| **Fase 2** | Schemas Pydantic, injeção de dependências, rotas de criação e listagem | ✅ |
| **Fase 3** | Tracking de fatura (RF06), objetivos (RF10), dashboard (RF11) | ✅ |
| **Fase 3.5** | Relatório PDF (RF12) e modularização em `routers/` | ✅ |
| **Fase 4** | **Login com JWT, CRUD completo (4 operações), isolamento entre usuários, `.env`, CORS, testes, README** | ✅ **Esta fase** |
| **Fase 5** | Frontend web (HTML, CSS e JS) consumindo a API | ⏳ Próxima |
| **Fase 6** | Assinaturas, ciclo correto da fatura (fechamento) e parcelamento | ⏳ |
| **Fase 7** | Importação de extrato/fatura em CSV com categorização automática | ⏳ |

---

## 2. CRUD: as 4 operações e o "idioma" do HTTP

O requisito mínimo do projeto é uma **API REST com as 4 operações de CRUD**. Antes desta fase, só existiam **C**reate e a listagem do **R**etrieve. Agora toda entidade tem as quatro:

| Operação | Verbo HTTP | Exemplo | Resposta de sucesso |
| :--- | :--- | :--- | :--- |
| **C**reate | `POST` | `POST /cartoes/` | `201 Created` + o objeto criado |
| **R**etrieve | `GET` | `GET /cartoes/` (lista) · `GET /cartoes/3` (um) | `200 OK` |
| **U**pdate | `PUT` | `PUT /cartoes/3` com o objeto completo | `200 OK` + o objeto atualizado |
| **D**elete | `DELETE` | `DELETE /cartoes/3` | `204 No Content` (sem corpo) |

### Códigos de erro usados (e quando)

| Código | Significado | Exemplo no FinFlow |
| :--- | :--- | :--- |
| `400 Bad Request` | Pedido logicamente inválido | Senha atual errada ao trocar senha |
| `401 Unauthorized` | Não sei quem você é | Sem token, token falso ou expirado |
| `404 Not Found` | Não existe **para você** | Id inexistente **ou** de outro usuário |
| `409 Conflict` | Conflita com o estado atual | E-mail já cadastrado; categoria em uso |
| `422 Unprocessable Entity` | Dados no formato errado (Pydantic) | `mes=13`, valor negativo, e-mail inválido |

> 💡 **Por que 409 e não 400 para duplicidade?** 400 diz "seu pedido está malformado". 409 diz "seu pedido está certo, mas conflita com algo que já existe". O frontend pode tratar cada um de um jeito.

---

## 3. Autenticação com JWT

### 3.1 O problema que existia
Toda rota recebia `id_usuario` no corpo da requisição. Ou seja, **qualquer pessoa podia mandar `"id_usuario": 7` e ler ou criar dados em nome do usuário 7**. Além disso, `GET /transacoes/` devolvia as transações de **todos** os usuários do sistema.

### 3.2 Como funciona agora

```text
 Frontend                                   API
    │  POST /auth/login (email + senha)       │
    │ ───────────────────────────────────────▶│ confere a senha com bcrypt
    │                 { access_token: "eyJ…" } │ cria um token assinado com a SECRET_KEY
    │ ◀───────────────────────────────────────│ dizendo "usuário 7, válido por 24h"
    │                                         │
    │  GET /transacoes/                       │
    │  Authorization: Bearer eyJ…             │
    │ ───────────────────────────────────────▶│ confere a assinatura e a validade,
    │            [ só as transações do 7 ]     │ descobre que é o usuário 7
    │ ◀───────────────────────────────────────│
```

- O token é como uma **pulseira de festa**: você mostra a identidade uma vez na entrada (login) e depois só mostra a pulseira.
- Ele é **assinado** com a `SECRET_KEY`: se alguém mudar o "7" para "8" dentro do token, a assinatura deixa de bater e a API recusa com 401.
- O token **não é criptografado** (dá para ler o conteúdo), por isso nunca colocamos dados sensíveis nele — só o id.

### 3.3 Como uma rota passa a exigir login
Basta receber o parâmetro `usuario: UsuarioAtual` (definido em `deps.py`):

```python
@router.get("/", response_model=list[schemas.CartaoResponse])
def listar_cartoes(usuario: UsuarioAtual, db: DbSession):
    return db.query(models.Cartao).filter(models.Cartao.id_usuario == usuario.id).all()
```

O FastAPI executa `get_usuario_atual` (em `seguranca.py`) **antes** da rota: lê o cabeçalho, valida o token e entrega o objeto `Usuario`. Se algo falhar, a rota nem chega a rodar e o cliente recebe 401.

### 3.4 Senhas: de SHA-256 para bcrypt

| | SHA-256 (antes) | bcrypt (agora) |
| :--- | :--- | :--- |
| Velocidade | Bilhões por segundo numa GPU | Lento de propósito (~0,1 s) |
| Sal | Não tinha: senhas iguais geravam hashes iguais | Sal aleatório embutido em cada hash |
| Ataque de dicionário | Trivial | Inviável em larga escala |

SHA-256 é ótimo para verificar integridade de arquivos, mas **ruim para senhas** justamente por ser rápido.

---

## 4. Isolamento entre usuários

Toda busca por id passa pela função `buscar_do_usuario` (em `deps.py`), que filtra **pelo id E pelo dono**:

```python
registro = db.query(modelo).filter(modelo.id == id_registro, modelo.id_usuario == usuario.id).first()
```

Se o registro é de outra pessoa, respondemos **404**, não 403. Com 403 ("proibido"), um atacante saberia que aquele id existe. Com 404, ele não descobre nada.

Entidades que não têm `id_usuario` descobrem o dono por **JOIN**: um planejamento pertence a quem é dono do cartão; um aporte, a quem é dono do objetivo.

---

## 5. Regras de integridade ao apagar

Apagar um registro que outros usam pode corromper os dados. A regra de cada entidade:

| Ao apagar… | O que acontece |
| :--- | :--- |
| **Categoria** em uso | `409`, a menos que se informe `?mover_para=<id>`: as transações vão para a outra categoria e os planejamentos são somados (RF03) |
| **Cartão** com compras | `409` — preserva o histórico de gastos. Os planejamentos do cartão são apagados junto. |
| **Transação** gerada por aporte | `409` — deve ser editada/apagada pelo aporte, senão o objetivo fica com valor errado |
| **Aporte** | Desfaz tudo: subtrai do objetivo e apaga a despesa gerada |
| **Objetivo** | Apaga os aportes; as despesas continuam no extrato (o dinheiro de fato saiu da conta) |
| **Conta do usuário** | Apaga **tudo** dele, via `ondelete="CASCADE"` nas chaves estrangeiras |

Também foi corrigida a consistência do `valor_atual` dos objetivos: ele nunca é editado diretamente. Ao editar um objetivo, ele é recalculado como `valor_inicial + soma dos aportes`.

---

## 6. Segredos fora do código (`.env`)

A senha do banco estava escrita em `database.py` e no `docker-compose.yml`, num **repositório público**. Agora:

- `config.py` lê tudo das **variáveis de ambiente**, carregadas do arquivo `.env`.
- O `.env` está no `.gitignore`: **nunca vai para o GitHub**.
- O `.env.example` vai para o GitHub, como modelo, com valores falsos.
- O `docker-compose.yml` lê as mesmas variáveis: a senha é definida num lugar só.

> ⚠️ A senha antiga continua no histórico do Git. Como é só um banco local de desenvolvimento, basta não reutilizá-la em nenhum outro lugar.

---

## 7. CORS — por que o navegador bloquearia o frontend

O navegador, por segurança, impede que uma página em `http://127.0.0.1:5500` (o frontend) leia respostas de `http://localhost:8000` (a API), porque são **origens diferentes**. A API precisa dizer explicitamente quais origens confia. Isso é o `CORSMiddleware` em `main.py`, configurado pela variável `CORS_ORIGINS` do `.env`.

Sem isso, o frontend da Fase 5 receberia um erro de CORS no console, mesmo com a API funcionando no `/docs`.

---

## 8. Projeto replicável

O critério **"Código replicável"** exige que qualquer pessoa consiga rodar o projeto do zero. Para isso:

- **`requirements.txt`**: lista as dependências. Basta rodar `pip install -r requirements.txt`.
- **Tabelas criadas automaticamente** no `lifespan` do `main.py`, sem precisar rodar `models.py` na mão.
- **`README.md`**: passo a passo de instalação, tabela de endpoints e problemas comuns.
- **Testes automatizados** (`pytest`): 21 testes cobrindo login, CRUD de todas as entidades, regras de integridade, dashboard, fatura, PDF e o mais importante, **isolamento entre usuários**. Eles rodam em SQLite em memória (sem Docker) e também passam no PostgreSQL 16.

---

## 9. Outras correções

| Problema | Correção |
| :--- | :--- |
| Criar categoria com usuário inexistente → erro 500 | O usuário vem do token; não existe mais esse caminho |
| Aporte aceitava categoria de outro usuário | Validação de dono; categoria agora é opcional (usa "Investimentos") |
| Gastos por categoria do dashboard ignoravam o cartão | Agora soma conta + cartão, ordenado do maior para o menor |
| "Últimas transações" ordenadas por id | Ordenadas por data |
| Receita podia ser lançada no cartão | Bloqueado com 422 |
| `mes=13` era aceito | Validação `1 ≤ mes ≤ 12` em todas as rotas |
| Uma consulta ao banco por categoria/cartão (problema N+1) | Consultas agregadas com `GROUP BY` e `JOIN` |
| Usuário novo começava sem categorias | 11 categorias padrão criadas no registro |
| Dashboard e PDF em `/usuarios/{id}/…` | Agora `/dashboard/` e `/relatorios/pdf`, usando o usuário do token |

---

## 10. Prévia da Fase 5: como o frontend vai usar a API

```js
// 1. Login (o padrão OAuth2 recebe formulário, não JSON)
const resp = await fetch("http://localhost:8000/auth/login", {
  method: "POST",
  body: new URLSearchParams({ username: email, password: senha }),
});
const { access_token } = await resp.json();
localStorage.setItem("token", access_token);

// 2. Qualquer outra chamada leva o token no cabeçalho
const dash = await fetch("http://localhost:8000/dashboard/?mes=10&ano=2026", {
  headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
}).then(r => r.json());
```
