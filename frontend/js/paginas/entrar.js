// Tela de entrada: login e criação de conta (API Python: /auth/login e /auth/registro).
import { python, sessao } from "../api.js";
import { ligarMostrarSenha } from "../ui.js";
import { esc } from "../util.js";

export default {
  render(raiz, { aoEntrar }) {
    raiz.innerHTML = `
      <main class="entrada">
        <section class="entrada-cartao" aria-labelledby="entrada-titulo">
          <div class="marca marca-grande"><span class="marca-celula" aria-hidden="true"></span>FinFlow</div>
          <h1 id="entrada-titulo" class="entrada-titulo">Suas finanças organizadas como uma planilha bem feita.</h1>
          <p class="entrada-sub">Lançamentos, faturas, orçamento do mês, assinaturas e objetivos num lugar só.</p>

          <div class="abas" role="tablist">
            <button role="tab" id="aba-entrar" aria-selected="true" aria-controls="form-entrar">Entrar</button>
            <button role="tab" id="aba-criar" aria-selected="false" aria-controls="form-criar">Criar conta</button>
          </div>

          <form id="form-entrar" class="entrada-form" role="tabpanel" aria-labelledby="aba-entrar" novalidate>
            <div class="campo">
              <label for="login-email">E-mail</label>
              <input id="login-email" name="email" type="email" autocomplete="email" required>
            </div>
            <div class="campo">
              <label for="login-senha">Senha</label>
              <input id="login-senha" name="senha" type="password" autocomplete="current-password" required>
            </div>
            <p class="janela-erro" role="alert" hidden></p>
            <button type="submit" class="botao botao-primario botao-largo">Entrar</button>
          </form>

          <form id="form-criar" class="entrada-form" role="tabpanel" aria-labelledby="aba-criar" hidden novalidate>
            <div class="campo">
              <label for="novo-nome">Nome</label>
              <input id="novo-nome" name="nome" autocomplete="name" maxlength="100" required>
            </div>
            <div class="campo">
              <label for="novo-email">E-mail</label>
              <input id="novo-email" name="email" type="email" autocomplete="email" required>
            </div>
            <div class="campo">
              <label for="novo-senha">Senha</label>
              <input id="novo-senha" name="senha" type="password" autocomplete="new-password" minlength="6" required>
              <p class="campo-ajuda">Pelo menos 6 caracteres.</p>
            </div>
            <p class="janela-erro" role="alert" hidden></p>
            <button type="submit" class="botao botao-primario botao-largo">Criar conta e entrar</button>
          </form>
        </section>

        <aside class="entrada-amostra" aria-hidden="true">
          ${amostra()}
        </aside>
      </main>`;

    const abas = raiz.querySelectorAll('[role="tab"]');
    abas.forEach((aba) => aba.addEventListener("click", () => {
      abas.forEach((a) => a.setAttribute("aria-selected", String(a === aba)));
      raiz.querySelector("#form-entrar").hidden = aba.id !== "aba-entrar";
      raiz.querySelector("#form-criar").hidden = aba.id !== "aba-criar";
      raiz.querySelector(aba.id === "aba-entrar" ? "#login-email" : "#novo-nome").focus();
    }));

    const login = async (email, senha) => {
      const { access_token } = await python.formulario("/auth/login", { username: email, password: senha });
      sessao.salvar(access_token);
      aoEntrar();
    };

    ligar(raiz.querySelector("#form-entrar"), async (d) => {
      if (!d.email || !d.senha) throw new Error("Preencha e-mail e senha.");
      await login(d.email, d.senha);
    });

    ligar(raiz.querySelector("#form-criar"), async (d) => {
      if (!d.nome || !d.email || !d.senha) throw new Error("Preencha nome, e-mail e senha.");
      if (d.senha.length < 6) throw new Error("A senha precisa ter pelo menos 6 caracteres.");
      await python.post("/auth/registro", { nome: d.nome, email: d.email, senha: d.senha });
      await login(d.email, d.senha);
    });

    ligarMostrarSenha(raiz);

    raiz.querySelector("#login-email").focus();
  },
};

function ligar(form, acao) {
  const erro = form.querySelector(".janela-erro");
  const botao = form.querySelector('button[type="submit"]');
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    erro.hidden = true;
    botao.disabled = true;
    botao.classList.add("carregando");
    try {
      await acao(Object.fromEntries(new FormData(form)));
    } catch (falha) {
      erro.textContent = falha.message;
      erro.hidden = false;
    } finally {
      botao.disabled = false;
      botao.classList.remove("carregando");
    }
  });
}

/** Pequena planilha ilustrativa ao lado do login. */
function amostra() {
  const linhas = [
    ["03/11", "Mercado", "Nubank", "-R$ 214,90"],
    ["05/11", "Salário", "Conta", "R$ 4.800,00"],
    ["07/11", "Farmácia", "Conta", "-R$ 38,50"],
    ["10/11", "Netflix", "Nubank", "-R$ 55,90"],
    ["12/11", "Aporte: viagem", "Conta", "-R$ 300,00"],
  ];
  return `
    <div class="amostra-planilha">
      <div class="amostra-linha amostra-cabecalho"><span></span><span>A</span><span>B</span><span>C</span><span>D</span></div>
      <div class="amostra-linha amostra-rotulos"><span>1</span><span>Data</span><span>Descrição</span><span>Forma</span><span>Valor</span></div>
      ${linhas.map((l, i) => `
        <div class="amostra-linha"><span>${i + 2}</span>${l.map((c, j) =>
          `<span class="${j === 3 ? (c.startsWith("-") ? "num" : "num positivo") : ""}">${esc(c)}</span>`).join("")}</div>`).join("")}
      <div class="amostra-linha amostra-total"><span>7</span><span></span><span>Saldo</span><span></span><span class="num selecionada">R$ 4.190,70</span></div>
    </div>`;
}
