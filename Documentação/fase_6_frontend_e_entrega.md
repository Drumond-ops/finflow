# 📒 FinFlow — Documentação da Fase 6: Frontend e Ajustes para a Entrega

---

## 1. Onde Estamos no Projeto?

| Fase | Descrição | Status |
| :--- | :--- | :---: |
| **Fases 1 a 3.5** | Banco, rotas, fatura, dashboard, PDF | ✅ |
| **Fase 4** | Login com JWT, CRUD completo, Docker, testes | ✅ |
| **Fase 5** | API Java de assinaturas, orçamento mensal, ciclo da fatura | ✅ |
| **Fase 6** | **Frontend completo, estrutura de pastas do enunciado, erros em JSON** | ✅ **Esta fase** |

---

## 2. Conferência com o enunciado

| Exigência do enunciado | Como o FinFlow atende |
| :--- | :--- |
| API REST em Python com pelo menos 2 endpoints reais | `api-python/`, FastAPI, mais de 40 endpoints usados pela plataforma |
| API REST em Java (Spring Boot) com pelo menos 2 endpoints reais | `api-java/`, 8 endpoints (status + 7 de assinaturas), usados pelo frontend |
| Front-end que consome as duas APIs | `frontend/`. O Painel e a tela de Assinaturas chamam as duas |
| APIs independentes, em portas diferentes | Python na 8000, Java na 8081, cada uma com sua imagem Docker |
| Respostas em JSON e erros básicos tratados sem derrubar | `{"detail": ...}` com 401, 404, 409, 422 e 500 nas duas APIs; há teste automático para o 500 |
| Rodar seguindo apenas o README | `docker compose up -d --build`, ou cada parte separadamente (opção 2 do README) |
| Pastas separadas: api-python, api-java, frontend, README | Estrutura reorganizada nesta fase |
| README com nome, integrantes, tecnologias, passo a passo e endpoints | Ver `README.md` |
| Não subir node_modules, target, ambientes virtuais, senhas | `.gitignore` cobre `target/`, `node_modules/`, `.venv/`, `.env` |
| Vídeo | Roteiro em `Documentação/roteiro_video.md` |

---

## 3. Mudanças nas APIs nesta fase

- **Estrutura**: o código Python foi para `api-python/` e o Java para `api-java/`. O `docker-compose.yml` agora sobe quatro serviços: `db`, `api-python`, `api-java` e `frontend`.
- **Erros sempre em JSON**:
  - Python: um middleware transforma qualquer erro inesperado num `500 {"detail": ...}`. Ele é registrado antes do CORS para que o navegador receba a mensagem, e não um "erro de CORS". `IntegrityError` do banco vira `409`.
  - Java: o `TratadorDeErros` também responde `409` para conflitos do banco e `500` em JSON para o inesperado, mantendo o código certo dos erros do próprio Spring (rota inexistente = 404, método errado = 405).
- **`GET /transacoes/`** ganhou os filtros `data_inicio` e `data_fim`, usados para listar as compras de uma fatura pelo período exato, e o campo `origem` (`manual`, `aporte` ou `assinatura`). O frontend usa esse campo para não deixar editar uma despesa gerada por aporte.
- **Configuração alinhada**: as duas APIs têm os mesmos valores padrão (senha do banco, chave do JWT, porta 5433 para rodar fora do Docker).

---

## 4. Como o frontend está organizado

```text
frontend/
├── index.html           só a "casca"; o conteúdo é montado pelo JavaScript
├── css/app.css          todo o visual
└── js/
    ├── config.js        endereços das duas APIs
    ├── api.js           python.get(...) e java.post(...): token, erros e registro de requisições
    ├── app.js           menu, rotas (#/painel, #/lancamentos...), seletor de mês, barra de status
    ├── ui.js            janelas, confirmações, avisos e campos de formulário
    ├── util.js          dinheiro (centavos ↔ R$), datas, regra da fatura no navegador
    ├── graficos.js      gráfico de despesas por dia e barras de uso, em SVG
    ├── icones.js        ícones em SVG
    └── paginas/         uma tela por arquivo, cada uma com uma função render()
```

- **Sem framework e sem build**: são módulos ES (`import`/`export`) que o navegador entende direto. Por isso precisa ser aberto por um servidor (nginx no Docker, ou `python -m http.server`), não por `file://`.
- **Segurança**: todo dado vindo do usuário passa por `esc()` antes de ir para o HTML, o que evita injeção de código.
- **Dinheiro**: a pessoa digita "1.234,56", o frontend envia `123456` (centavos), e a exibição usa `Intl.NumberFormat("pt-BR")`.
- **Visual de planilha**: tabelas com linhas de grade, números alinhados à direita com algarismos de mesma largura, totais com sublinhado duplo de contabilidade e barras de dados nas células. A "célula selecionada" (contorno verde com o quadradinho no canto) marca o item ativo do menu e o saldo do mês.
- **Painel de requisições**: cada chamada fica registrada na barra inferior, em azul para a API Python e em laranja para a API Java. Isso atende ao item "Integração" do vídeo.
- **Responsivo**: no celular o menu vira uma barra no topo e as tabelas rolam dentro do próprio quadro, sem a página inteira rolar para os lados.

---

## 5. Testes desta fase

- `api-python/tests/test_erros_e_filtros.py`: erros 401, 404 e 422 em JSON; erro inesperado vira 500 em JSON e a API continua respondendo; filtro por período bate com o total da fatura; campo `origem`.
- O frontend foi testado de ponta a ponta num navegador automatizado (Playwright): cadastro, cartão, transação no cartão depois do fechamento, validação de valor inválido, assinatura e lançamento das cobranças, orçamento, objetivos e exclusão de categoria em uso, além de checar que nenhuma tela rola para os lados num celular de 390 px.
