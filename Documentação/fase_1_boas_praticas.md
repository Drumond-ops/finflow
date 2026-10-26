# 📘 FinFlow — Documentação da Fase 1: Fundação, Infraestrutura e Modelagem

Este documento registra todas as decisões de arquitetura, configurações de ambiente e **boas práticas de engenharia de software** adotadas durante a Fase 1 do desenvolvimento do projeto **FinFlow**.

---

## 1. Infraestrutura e Banco de Dados (Docker & PostgreSQL 16)

### 1.1 Configuração do Container
* O banco de dados foi provisionado via **Docker Compose** utilizando a imagem oficial `postgres:16`.
* Configuração padronizada no `docker-compose.yml`:
  * **Usuário:** `admin_financas`
  * **Banco de dados:** `financeiro_db`
  * **Porta exposta:** `5432:5432`
  * **Volume persistente:** `postgres_data`

### 1.2 Boas Práticas e Lições de Infraestrutura
1. **Caracteres Especiais em URLs de Conexão:**
   * A anatomia de uma URL SQLAlchemy é: `postgresql+psycopg2://USUARIO:SENHA@HOST:PORTA/BANCO`.
   * **Lição aprendida:** O uso de caracteres reservados como `@` dentro da senha gera conflito na interpretação da URL (o parser divide a credencial do host no primeiro `@`). Evitou-se o uso de `@` na senha ou deve-se aplicar URL-encoding (`%40`).
2. **Ciclo de Vida dos Volumes Docker (`docker-compose down -v`):**
   * Ao alterar variáveis de ambiente de um container PostgreSQL já inicializado, os scripts de entrypoint pulam a inicialização se encontrarem uma pasta de dados existente (`PostgreSQL Database directory appears to contain a database; Skipping initialization`).
   * **Lição aprendida:** Para reinicializar credenciais em ambiente de desenvolvimento inicial, é necessário derrubar o container limpando os volumes com a flag `-v`.
3. **Escopo da `venv` vs Docker:**
   * A `venv` (Virtual Environment) atua estritamente no ecossistema Python (gerenciamento e isolamento de dependências via `pip`).
   * O Docker atua a nível de sistema operacional (daemon global do Linux). Comandos `docker` podem ser executados com a `venv` ativa sem interferência mútua.

---

## 2. Conexão com o Banco de Dados (`database.py`)

### 2.1 Padrão Lazy do SQLAlchemy Engine
* O `create_engine(...)` configura o pool de conexões de forma *lazy* (sob demanda).
* Conexões reais só ocorrem quando uma transação ou `engine.connect()` é chamado.
* Foi implementado um teste de integridade local via bloco `if __name__ == "__main__":` para validar o canal de comunicação antes do início das rotas.

### 2.2 Gerenciamento do Ciclo de Vida da Sessão (`get_db`)
* Implementação do padrão gerador com `yield` e bloco de limpeza `finally`:
  ```python
  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```
* **Boa Prática:** Garante que toda requisição HTTP abra sua própria sessão isolada e que a conexão seja devolvida ao pool ao término da requisição, evitando vazamento de conexões (*connection leaks*).

---

## 3. Modelagem Relacional & SQLAlchemy ORM (`models.py`)

A modelagem foi baseada no Diagrama Entidade-Relacionamento e no Esquema Lógico validados, resultando em 7 entidades persistidas no PostgreSQL:
`usuarios`, `categorias`, `cartoes`, `planejamentos`, `transacoes`, `objetivos`, `aportes`.

```
           [Usuario] (Raiz)
          /    |    \
         /     |     \
  [Categoria] [Cartao] [Objetivo]
       \       /          |
        \     /        [Aporte]
      [Transacao] <-------' (1:1 com aporte)
          |
    [Planejamento]
```

### 3.1 Boas Práticas de Engenharia Aplicadas aos Modelos

1. **Armazenamento de Valores Monetários em Centavos (`BigInteger`):**
   * Em vez de `Float` (que sofre com erros de arredondamento binário IEEE 754, ex: `0.1 + 0.2 = 0.30000000000000004`), todos os campos monetários (`valor`, `valor_alvo`, `valor_atual`, `valor_inicial`) foram definidos como `BigInteger` representando **centavos** (`R$ 10,50` é gravado como `1050`).
   * Esse é o mesmo padrão utilizado por plataformas financeiras e processadoras de pagamento globais (como Stripe).

2. **Índices vs Constraints de Unicidade (`unique=True`):**
   * No PostgreSQL, toda restrição de unicidade (`UNIQUE`) cria automaticamente um índice B-Tree subjacente para permitir validação em tempo \(O(\log N)\).
   * **Lição aprendida:** Declarar `unique=True` dispensa o uso de `index=True` no mesmo campo, evitando a criação redundante de dois índices idênticos na mesma tabela e economizando espaço em disco e custo de I/O em escritas.

3. **Segurança de Senhas (`senha_hash` com `String(255)`):**
   * Senhas puras nunca devem ser persistidas. O campo armazena hashes criptográficos (ex: Bcrypt / Argon2).
   * Hashes modernos exigem entre 60 e 100 caracteres. O limite foi definido com margem segura (`String(255)`).

4. **Flexibilidade de Transações (`Transacao.id_cartao` como `nullable=True`):**
   * Transações financeiras não são exclusivas de cartão de crédito. Permitir valores nulos viabiliza lançamentos em Pix, Dinheiro e Débito.

5. **Integridade de Aportes e Despesas (`Aporte.id_transacao` com `unique=True`):**
   * Para atender ao requisito de negócio onde *"todo aporte em um objetivo gera uma despesa no mês"*, a chave estrangeira `id_transacao` foi configurada com `unique=True`, garantindo uma relação estrita de 1 para 1.

6. **Manipulação de Datas e Consultas de Período (`Date`):**
   * Uso do tipo nativo `Date` na `Transacao`, viabilizando filtros eficientes por intervalo de datas (`between` aproveitando índices) ou pela função de extração temporal (`extract('month', ...)`).

---

## 4. Próxima Etapa: Fase 2 (Camada de Aplicação e API)

* **Objetivo:** Construção dos schemas de entrada e saída via **Pydantic** (`schemas.py`) e dos primeiros endpoints HTTP com **FastAPI** (`main.py`).
* **Princípio Central:** Separação entre modelos de persistência (SQLAlchemy) e contratos de tráfego de dados com tipagem estática (*Type Hints*).
