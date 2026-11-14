// Minha conta e situação da plataforma. API Python: /usuarios/me. Situação: GET / das duas APIs.
import { APIS, apiNoAr, python, sessao } from "../api.js";
import { abrirFormulario, avisar, campoTexto, confirmar } from "../ui.js";
import { esc } from "../util.js";

export default {
  usaMes: false,

  async render(el, ctx) {
    const [usuario, situacao] = await Promise.all([
      python.get("/usuarios/me"),
      Promise.all(Object.values(APIS).map(async (api) => ({ api, ...(await apiNoAr(api)) }))),
    ]);
    if (!ctx.aindaAtual()) return;

    el.innerHTML = `
      <div class="grade-conta">
        <section class="planilha">
          <header class="planilha-topo"><h2>Perfil</h2></header>
          <form class="formulario-pagina" data-perfil novalidate>
            ${campoTexto("nome", "Nome", { valor: usuario.nome, autocomplete: "name" })}
            ${campoTexto("email", "E-mail", { valor: usuario.email, tipo: "email", max: 150, autocomplete: "email" })}
            <p class="janela-erro" role="alert" hidden></p>
            <div><button class="botao botao-primario" type="submit">Salvar perfil</button></div>
          </form>
        </section>

        <section class="planilha">
          <header class="planilha-topo"><h2>Senha</h2></header>
          <form class="formulario-pagina" data-senha novalidate>
            ${campoTexto("senha_atual", "Senha atual", { tipo: "password", autocomplete: "current-password" })}
            ${campoTexto("nova_senha", "Nova senha", { tipo: "password", autocomplete: "new-password", ajuda: "Pelo menos 6 caracteres." })}
            <p class="janela-erro" role="alert" hidden></p>
            <div><button class="botao botao-secundario" type="submit">Trocar senha</button></div>
          </form>
        </section>

        <section class="planilha">
          <header class="planilha-topo"><h2>Plataforma</h2></header>
          <table class="tabela tabela-compacta">
            <thead><tr><th scope="col">Serviço</th><th scope="col">Endereço</th><th scope="col">Situação</th><th scope="col" class="num">Resposta</th></tr></thead>
            <tbody>
              ${situacao.map(({ api, ok, ms }) => `
                <tr>
                  <td><span class="selo-api selo-${api.id}">${api.nome}</span></td>
                  <td><code>${esc(api.base)}</code></td>
                  <td>${ok ? '<span class="situacao situacao-ok">No ar</span>' : '<span class="situacao situacao-estourado">Sem resposta</span>'}</td>
                  <td class="num suave">${ok ? `${ms} ms` : "—"}</td>
                </tr>`).join("")}
              <tr><td><span class="selo-api selo-front">Frontend</span></td><td><code>${esc(location.origin)}</code></td><td><span class="situacao situacao-ok">No ar</span></td><td class="num suave">—</td></tr>
            </tbody>
          </table>
          <p class="planilha-rodape">Documentação interativa: <a class="link" href="${APIS.python.base}/docs" target="_blank" rel="noopener">API Python (/docs)</a> e
            <a class="link" href="${APIS.java.base}/swagger-ui.html" target="_blank" rel="noopener">API Java (/swagger-ui.html)</a>.</p>
        </section>

        <section class="planilha zona-perigo">
          <header class="planilha-topo"><h2>Excluir conta</h2></header>
          <p class="planilha-texto">Apaga você e todos os seus dados: lançamentos, cartões, orçamentos, objetivos e assinaturas. Não dá para desfazer.</p>
          <div class="planilha-texto"><button class="botao botao-perigo" data-excluir-conta>Excluir minha conta</button></div>
        </section>
      </div>`;

    enviar(el.querySelector("[data-perfil]"), async (d) => {
      if (!d.nome || !d.email) throw new Error("Preencha nome e e-mail.");
      await python.put("/usuarios/me", { nome: d.nome, email: d.email });
      avisar("Perfil salvo.");
      const nome = document.querySelector("[data-usuario]");
      if (nome) nome.textContent = d.nome;
    });

    enviar(el.querySelector("[data-senha]"), async (d, form) => {
      if (!d.senha_atual || !d.nova_senha) throw new Error("Preencha a senha atual e a nova.");
      if (d.nova_senha.length < 6) throw new Error("A nova senha precisa ter pelo menos 6 caracteres.");
      await python.put("/usuarios/me/senha", d);
      form.reset();
      avisar("Senha trocada.");
    });

    el.querySelector("[data-excluir-conta]").addEventListener("click", async () => {
      const ok = await confirmar({
        titulo: "Excluir sua conta?",
        mensagem: `Todos os dados de <strong>${esc(usuario.email)}</strong> serão apagados nas duas APIs.`,
        botao: "Excluir conta",
      });
      if (!ok) return;
      try {
        await python.del("/usuarios/me");
        sessao.sair();
        avisar("Conta excluída.");
        ctx.irPara("entrar");
      } catch (e) { avisar(e.message, "erro"); }
    });
  },
};

function enviar(form, acao) {
  const erro = form.querySelector(".janela-erro");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    erro.hidden = true;
    const botao = form.querySelector('button[type="submit"]');
    botao.disabled = true;
    try {
      await acao(Object.fromEntries(new FormData(form)), form);
    } catch (falha) {
      erro.textContent = falha.message;
      erro.hidden = false;
    } finally {
      botao.disabled = false;
    }
  });
}
