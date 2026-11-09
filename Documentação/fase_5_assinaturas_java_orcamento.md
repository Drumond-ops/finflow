# 📙 FinFlow — Documentação da Fase 5: Serviço Java, Orçamento Mensal e Ciclo da Fatura

Este documento registra o que mudou na **Fase 5**, por que cada mudança foi feita e os conceitos por trás dela.

---

## 1. Onde Estamos no Projeto?

| Fase | Descrição | Status |
| :--- | :--- | :---: |
| **Fase 1** | Docker, PostgreSQL 16, SQLAlchemy, 7 tabelas | ✅ |
| **Fase 2** | Schemas Pydantic, injeção de dependências, rotas de criação e listagem | ✅ |
| **Fase 3** | Tracking de fatura (RF06), objetivos (RF10), dashboard (RF11) | ✅ |
| **Fase 3.5** | Relatório PDF (RF12) e modularização em `routers/` | ✅ |
| **Fase 4** | Login com JWT, CRUD completo, isolamento entre usuários, Docker, testes | ✅ |
| **Fase 5** | **Serviço de assinaturas em Java, orçamento mensal, fatura com dia de fechamento** | ✅ **Esta fase** |
| **Fase 6** | Frontend web (HTML, CSS e JS) consumindo as duas APIs | ⏳ Próxima |

---

## 2. Por que um serviço em Java?

O projeto exige endpoints em **framework Python** e em **framework Java**. Em vez de duplicar a mesma coisa nas duas linguagens, cada uma ficou com uma parte do sistema:

| Serviço | Linguagem | Porta | Responsabilidade |
| :--- | :--- | :--- | :--- |
| API principal | Python (FastAPI) | 8000 | Login, transações, cartões, faturas, orçamento, objetivos, dashboard, PDF |
| Assinaturas | Java (Spring Boot) | 8081 | Assinaturas recorrentes, próximas cobranças, lançamento das cobranças |

Isso é uma pequena **arquitetura de serviços**: cada serviço tem seu código, sua imagem Docker e suas rotas, mas os dois falam com o mesmo banco e aceitam o mesmo login.

### 2.1 Um login, duas APIs

O token JWT é gerado pela API Python e **assinado com a `SECRET_KEY`**. O serviço Java conhece a mesma chave (o `docker-compose.yml` passa a mesma variável para os dois), então consegue conferir a assinatura sozinho, sem perguntar nada para a API Python.

```text
1. Frontend  → POST /auth/login (Python)        → recebe o token
2. Frontend  → GET /assinaturas (Java)
              Authorization: Bearer <token>
3. Java      → confere a assinatura HMAC-SHA256 com a SECRET_KEY
              → lê o "sub" (id do usuário) e o "exp" (validade)
              → responde só com as assinaturas desse usuário
```

A verificação está em `seguranca/JwtService.java`. Ela foi escrita sem biblioteca de JWT, só com o que vem no Java (`javax.crypto.Mac`), para mostrar o que um JWT realmente é: `cabeçalho.conteúdo.assinatura`, onde a assinatura é um HMAC das duas primeiras partes. O teste `JwtServiceTest` usa um token **gerado de verdade pela API Python** para provar que as duas linguagens se entendem.

### 2.2 Um banco, duas linguagens

A API Python continua sendo a **dona do esquema**: as tabelas `assinaturas` e `assinatura_lancamentos` estão declaradas em `models.py`. O Java usa `spring.jpa.hibernate.ddl-auto=none`, ou seja, nunca cria nem altera tabelas.

Por que assim? Porque as chaves estrangeiras (assinatura → usuário, cartão, categoria) ficam no mesmo lugar que o resto do banco, e as regras de exclusão funcionam juntas:

| Quando apaga… | O que acontece com as assinaturas |
| :--- | :--- |
| O usuário | São apagadas junto (`ON DELETE CASCADE`) |
| O cartão | Ficam sem cartão (`ON DELETE SET NULL`) |
| A categoria | Ficam sem categoria (usam "Assinaturas"), ou vão para a categoria de destino se usar `?mover_para=` |
| A transação gerada | O registro de lançamento some junto, e a cobrança pode ser lançada de novo |

### 2.3 Como o Spring Boot está organizado

```text
servico-assinaturas/src/main/java/br/ime/finflow/assinaturas/
├── web/          → AssinaturaController (rotas), TratadorDeErros (formato {"detail": ...})
├── servico/      → AssinaturaService (regras), CalendarioCobranca (datas, sem banco)
├── dominio/      → Assinatura, LancamentoAssinatura (entidades JPA = tabelas)
├── repositorio/  → interfaces Spring Data (o SQL é gerado pelo nome do método)
├── dto/          → AssinaturaRequest (entrada validada), records de resposta
├── seguranca/    → JwtService, AutenticacaoInterceptor (exige token em /assinaturas)
└── config/       → WebConfig (CORS + registra o interceptor)
```

Comparando com o FastAPI:

| Conceito | FastAPI (Python) | Spring Boot (Java) |
| :--- | :--- | :--- |
| Rota | `@router.get("/")` | `@GetMapping` |
| Validação da entrada | Pydantic (`Field(gt=0)`) | Bean Validation (`@Positive`) |
| Tabela | `class X(Base)` (SQLAlchemy) | `@Entity` (JPA/Hibernate) |
| Consulta | `db.query(X).filter(...)` | `findByIdAndIdUsuario(...)` (Spring Data) |
| Usuário logado | `Depends(get_usuario_atual)` | `HandlerInterceptor` + `@RequestAttribute` |
| Documentação | `/docs` | `/swagger-ui.html` (springdoc) |

### 2.4 Lançamento das cobranças

`POST /assinaturas/lancamentos?mes=11&ano=2026` olha todas as assinaturas ativas e, para cada uma que cobra naquele mês, cria uma **despesa** na tabela `transacoes`, no cartão da assinatura, se tiver um. A partir daí, ela aparece normalmente na fatura, no dashboard, no orçamento e no PDF da API Python.

Para não lançar duas vezes, cada lançamento é anotado em `assinatura_lancamentos`, que tem uma restrição única por (assinatura, mês, ano). Rodar de novo responde quantas já tinham sido lançadas e não cria nada.

Regras de data (`CalendarioCobranca.java`):
- **Mensal**: cobra todo mês no dia da `data_inicio`. Dia 31 em fevereiro vira 28 (ou 29).
- **Anual**: cobra só no mês e dia da `data_inicio`.
- Nada é cobrado antes da `data_inicio`.

---

## 3. Fatura com dia de fechamento

### 3.1 O problema
O campo `dia_fechamento` era salvo, mas nunca usado: a "fatura de novembro" era simplesmente o que foi comprado de 1º a 30 de novembro. No mundo real não é assim, porque a fatura fecha num dia do mês e o que vem depois vai para a próxima.

### 3.2 A regra adotada
> A fatura de um mês é a que **vence** nesse mês (é quando o dinheiro sai da conta).
> Ela contém as compras **depois do fechamento anterior** até o **fechamento atual**.

| Cartão | Fatura de novembro/2026 | Compras incluídas |
| :--- | :--- | :--- |
| Fecha dia 3, vence dia 10 | fecha 03/11, vence 10/11 | 04/10 a 03/11 |
| Fecha dia 25, vence dia 5 | fecha 25/10, vence 05/11 | 26/09 a 25/10 |
| Sem dia de fechamento | — | 01/11 a 30/11 |

Toda a regra está em `ciclo_fatura.py` (sem banco, fácil de testar). O teste `test_toda_compra_cai_em_exatamente_uma_fatura` confere, para várias combinações de fechamento e vencimento, que **cada dia de dois anos inteiros** cai em exatamente uma fatura, sem buracos nem sobreposição.

A rota da fatura agora devolve também `periodo_inicio`, `periodo_fim`, `data_fechamento` e `data_vencimento`, para o frontend mostrar "compras de 04/10 a 03/11, vence 10/11".

---

## 4. Orçamento mensal

### 4.1 Planejamento × Orçamento

| | Planejamento (já existia) | Orçamento (novo) |
| :--- | :--- | :--- |
| Escopo | Uma fatura de um cartão | O mês inteiro |
| Conta | Só compras daquele cartão | Pix, débito **e** cartão |
| Mês considerado | Mês de vencimento da fatura | Mês da data da compra |
| Pergunta que responde | "Quanto posso gastar no Nubank este mês?" | "Quanto posso gastar com Mercado este mês?" |

### 4.2 Rotas
- CRUD em `/orcamentos` (um limite por categoria por mês; repetido dá `409`).
- `GET /orcamentos/resumo?mes=&ano=`: para cada categoria, mostra orçado, gasto, saldo, percentual e **status**:
  - `ok`: abaixo de 80% do limite
  - `atencao`: 80% ou mais
  - `estourado`: passou de 100%

  E também `gasto_fora_do_orcamento`, o quanto foi gasto em categorias sem limite definido.
- `POST /orcamentos/copiar?de_mes=&de_ano=&para_mes=&para_ano=`: copia os limites para o mês seguinte sem sobrescrever o que já existe.
- O **dashboard** passou a incluir o resumo do orçamento do mês.

---

## 5. Testes

| Onde | O que cobre | Como rodar |
| :--- | :--- | :--- |
| `tests/test_ciclo_fatura.py` | Regras de fechamento/vencimento, dia 31, propriedade "toda compra cai em uma fatura", fatura e dashboard pela API | `docker compose exec api pytest` |
| `tests/test_orcamentos.py` | CRUD, resumo (conta + cartão, status), copiar mês, isolamento entre usuários, mover categoria | idem |
| `servico-assinaturas/src/test/.../JwtServiceTest.java` | Token gerado pelo Python aceito; expirado, adulterado ou com outra chave recusado | roda no `docker compose up --build` |
| `servico-assinaturas/src/test/.../CalendarioCobrancaTest.java` | Mensal, anual, dia 31, antes do início, próximas cobranças | idem |

Total na API Python: **31 testes**. No serviço Java: **11 testes**.
