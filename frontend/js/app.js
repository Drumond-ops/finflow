/**
 * Casca da aplicação: menu lateral, seletor de mês, rotas (#/painel, #/lancamentos...),
 * barra de status com as requisições e os indicadores das duas APIs.
 */
import { APIS, apiNoAr, python, quandoSessaoExpirar, registro, sessao } from "./api.js";
import { icone } from "./icones.js";
import { avisar, carregando, erroDeCarga } from "./ui.js";
import { cls, esc, mesAnterior, mesSeguinte, tituloDoMes } from "./util.js";

import entrar from "./paginas/entrar.js";
import painel from "./paginas/painel.js";
import lancamentos from "./paginas/lancamentos.js";
import cartoes from "./paginas/cartoes.js";
import orcamento from "./paginas/orcamento.js";
import assinaturas from "./paginas/assinaturas.js";
import objetivos from "./paginas/objetivos.js";
import categorias from "./paginas/categorias.js";
import conta from "./paginas/conta.js";

// Ordem = ordem no menu. "api" indica quem fornece os dados da tela.
const PAGINAS = [
  { rota: "painel", nome: "Painel", icone: "painel", modulo: painel },
  { rota: "lancamentos", nome: "Lançamentos", icone: "lancamentos", modulo: lancamentos },
  { rota: "cartoes", nome: "Cartões e faturas", icone: "cartao", modulo: cartoes },
  { rota: "orcamento", nome: "Orçamento", icone: "orcamento", modulo: orcamento },
  { rota: "assinaturas", nome: "Assinaturas", icone: "assinaturas", modulo: assinaturas, api: "java" },
  { rota: "objetivos", nome: "Objetivos", icone: "objetivos", modulo: objetivos },
  { rota: "categorias", nome: "Categorias", icone: "categorias", modulo: categorias },
  { rota: "conta", nome: "Minha conta", icone: "conta", modulo: conta },
];

// ---------- Estado: mês selecionado (vale para todas as telas) ----------

const estado = (() => {
  const hoje = new Date();
  let salvo = null;
  try { salvo = JSON.parse(sessionStorage.getItem("finflow.mes")); } catch { /* sem armazenamento */ }
  return {
    mes: salvo?.mes || hoje.getMonth() + 1,
    ano: salvo?.ano || hoje.getFullYear(),
    usuario: null,
  };
})();

function mudarMes({ mes, ano }) {
  estado.mes = mes;
  estado.ano = ano;
  try { sessionStorage.setItem("finflow.mes", JSON.stringify({ mes, ano })); } catch { /* idem */ }
  renderizarPagina();
}

// ---------- Rotas ----------

function rotaAtual() {
  const [rota, ...resto] = location.hash.replace(/^#\/?/, "").split("/");
  return { rota: rota || "painel", parametro: resto.join("/") || null };
}

/** Vai para a rota; se já estiver nela, só redesenha. */
export function irPara(rota) {
  const alvo = `#/${rota}`;
  if (location.hash === alvo) renderizarPagina();
  else location.hash = alvo;
}

quandoSessaoExpirar(() => {
  estado.usuario = null;
  if (rotaAtual().rota !== "entrar") {
    avisar("Sua sessão expirou. Entre de novo.", "erro");
    irPara("entrar");
  }
});

// ---------- Casca (menu + topo + barra de status) ----------

const raiz = document.getElementById("app");

function montarCasca() {
  raiz.innerHTML = `
    <a class="pular" href="#conteudo">Pular para o conteúdo</a>
    <aside class="lateral">
      <a class="marca" href="#/painel" aria-label="FinFlow, ir para o painel">
        <span class="marca-celula" aria-hidden="true"></span>FinFlow
      </a>
      <nav class="menu" aria-label="Seções">
        ${PAGINAS.map((p) => `
          <a href="#/${p.rota}" data-rota="${p.rota}">
            ${icone(p.icone)}<span>${p.nome}</span>
          </a>`).join("")}
      </nav>
      <div class="lateral-rodape">
        <div class="saude" aria-label="Situação das APIs">
          <span class="saude-item" data-saude="python" title="${APIS.python.base}"><i></i>API Python <small>:8000</small></span>
          <span class="saude-item" data-saude="java" title="${APIS.java.base}"><i></i>API Java <small>:8081</small></span>
        </div>
        <div class="usuario">
          <span class="usuario-nome" data-usuario></span>
          <button class="botao-icone" data-sair title="Sair" aria-label="Sair">${icone("sair")}</button>
        </div>
      </div>
    </aside>

    <div class="area">
      <header class="topo">
        <div class="topo-titulo">
          <h1 data-titulo></h1>
        </div>
        <div class="seletor-mes" data-seletor-mes>
          <button class="botao-icone" data-mes="-1" aria-label="Mês anterior" title="Mês anterior ([)">${icone("esquerda")}</button>
          <span class="seletor-mes-nome" data-mes-nome aria-live="polite"></span>
          <button class="botao-icone" data-mes="+1" aria-label="Próximo mês" title="Próximo mês (])">${icone("direita")}</button>
          <button class="botao botao-secundario botao-pequeno" data-mes-hoje hidden>Hoje</button>
        </div>
      </header>
      <main id="conteudo" class="conteudo" tabindex="-1"></main>
    </div>

    <footer class="status">
      <span class="status-ultima" data-ultima>Nenhuma requisição ainda</span>
      <button class="status-botao" data-abrir-registro aria-expanded="false" aria-controls="registro">
        ${icone("rede")}Requisições <span data-contador>0</span>
      </button>
    </footer>

    <section id="registro" class="registro" hidden aria-label="Requisições feitas pelo frontend">
      <header>
        <h2>Requisições</h2>
        <p>Cada ação da tela chama uma das APIs. Azul é a API Python (porta 8000), laranja é a API Java (porta 8081).</p>
        <button class="botao-icone" data-fechar-registro aria-label="Fechar">${icone("fechar")}</button>
      </header>
      <div class="registro-lista" data-registro-lista></div>
    </section>`;

  raiz.querySelector("[data-sair]").addEventListener("click", () => {
    sessao.sair();
    estado.usuario = null;
    irPara("entrar");
  });

  raiz.querySelectorAll("[data-mes]").forEach((b) =>
    b.addEventListener("click", () => {
      const fn = b.dataset.mes === "-1" ? mesAnterior : mesSeguinte;
      mudarMes(fn(estado.mes, estado.ano));
    }));
  raiz.querySelector("[data-mes-hoje]").addEventListener("click", () => {
    const hoje = new Date();
    mudarMes({ mes: hoje.getMonth() + 1, ano: hoje.getFullYear() });
  });

  const painelRegistro = raiz.querySelector("#registro");
  const botaoRegistro = raiz.querySelector("[data-abrir-registro]");
  const alternarRegistro = (abrir) => {
    painelRegistro.hidden = !abrir;
    botaoRegistro.setAttribute("aria-expanded", String(abrir));
    if (abrir) desenharRegistro();
  };
  botaoRegistro.addEventListener("click", () => alternarRegistro(painelRegistro.hidden));
  raiz.querySelector("[data-fechar-registro]").addEventListener("click", () => alternarRegistro(false));

  registro.ouvir(() => {
    atualizarStatus();
    if (!painelRegistro.hidden) desenharRegistro();
  });
  atualizarStatus();
  verificarApis();
}

function linhaDeRegistro(r, compacta = false) {
  const api = APIS[r.api];
  const situacao = r.status === 0 ? "sem resposta" : r.status;
  const classeStatus = r.status >= 200 && r.status < 400 ? "ok" : "erro";
  const hora = r.hora.toLocaleTimeString("pt-BR");
  const porta = new URL(api.base).port;
  if (compacta) {
    return `<span class="selo-api selo-${r.api}">${api.nome}</span>
      <code>${esc(r.metodo)} ${esc(r.caminho)}</code>
      <span class="status-codigo status-${classeStatus}">${situacao}</span>
      <span class="status-ms">${r.ms} ms</span>`;
  }
  return `
    <div class="registro-linha">
      <span class="registro-hora">${hora}</span>
      <span class="selo-api selo-${r.api}">${api.nome} <small>:${porta}</small></span>
      <code class="registro-metodo metodo-${r.metodo.toLowerCase()}">${esc(r.metodo)}</code>
      <code class="registro-caminho">${esc(r.caminho)}</code>
      <span class="status-codigo status-${classeStatus}">${situacao}</span>
      <span class="status-ms">${r.ms} ms</span>
    </div>`;
}

function atualizarStatus() {
  const ultima = registro.itens[0];
  raiz.querySelector("[data-ultima]").innerHTML = ultima ? linhaDeRegistro(ultima, true) : "Nenhuma requisição ainda";
  raiz.querySelector("[data-contador]").textContent = registro.itens.length;
}

function desenharRegistro() {
  raiz.querySelector("[data-registro-lista]").innerHTML =
    registro.itens.map((r) => linhaDeRegistro(r)).join("") || `<p class="registro-vazio">Nenhuma requisição ainda.</p>`;
}

async function verificarApis() {
  for (const api of Object.values(APIS)) {
    const el = raiz.querySelector(`[data-saude="${api.id}"]`);
    if (!el) return;
    const { ok, ms } = await apiNoAr(api);
    el.classList.toggle("no-ar", ok);
    el.classList.toggle("fora", !ok);
    el.title = ok ? `${api.nome} respondendo em ${api.base} (${ms} ms)` : `${api.nome} não responde em ${api.base}`;
  }
}
setInterval(() => { if (sessao.token) verificarApis(); }, 30000);

async function carregarUsuario() {
  if (estado.usuario) return;
  try {
    estado.usuario = await python.get("/usuarios/me");
    const el = raiz.querySelector("[data-usuario]");
    if (el) el.textContent = estado.usuario.nome;
  } catch { /* a página mostra o erro */ }
}

/**
 * No celular o menu vira uma faixa que rola para o lado e só o item ativo mostra o nome.
 * Centraliza esse item; senão, em várias páginas ele ficava fora da tela.
 * No computador o menu não rola, então nada muda.
 */
function centralizarItemAtivo() {
  const menu = raiz.querySelector(".menu");
  const ativo = menu?.querySelector("a.ativo");
  if (!ativo || menu.scrollWidth <= menu.clientWidth) return;
  const m = menu.getBoundingClientRect();
  const a = ativo.getBoundingClientRect();
  menu.scrollLeft += (a.left - m.left) - (m.width - a.width) / 2;
}

// ---------- Renderização das páginas ----------

let renderizacao = 0;

// Quando a página não carrega (ex.: a API ainda está subindo), dá para tentar de novo sem recarregar o navegador
const BOTAO_TENTAR = `<div class="tentar-de-novo"><button class="botao botao-secundario" data-tentar>Tentar de novo</button></div>`;

async function renderizarPagina() {
  const { rota, parametro } = rotaAtual();
  const minhaVez = ++renderizacao;

  if (rota === "entrar" || !sessao.token) {
    if (rota !== "entrar") { irPara("entrar"); return; }
    if (sessao.token) { irPara("painel"); return; }
    document.body.classList.add("modo-entrada");
    raiz.innerHTML = "";
    entrar.render(raiz, { aoEntrar: () => { estado.usuario = null; irPara("painel"); } });
    return;
  }

  const pagina = PAGINAS.find((p) => p.rota === rota);
  if (!pagina) { irPara("painel"); return; }

  if (document.body.classList.contains("modo-entrada") || !raiz.querySelector(".lateral")) {
    document.body.classList.remove("modo-entrada");
    montarCasca();
  }
  carregarUsuario();

  raiz.querySelectorAll(".menu a").forEach((a) => {
    const ativo = a.dataset.rota === rota;
    a.classList.toggle("ativo", ativo);
    if (ativo) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
  centralizarItemAtivo();

  const usaMes = pagina.modulo.usaMes !== false;
  raiz.querySelector("[data-titulo]").textContent = pagina.nome;
  raiz.querySelector("[data-seletor-mes]").hidden = !usaMes;
  raiz.querySelector("[data-mes-nome]").textContent = tituloDoMes(estado.mes, estado.ano);
  const hoje = new Date();
  raiz.querySelector("[data-mes-hoje]").hidden = estado.mes === hoje.getMonth() + 1 && estado.ano === hoje.getFullYear();
  document.title = `${pagina.nome} · FinFlow`;

  const conteudo = raiz.querySelector("#conteudo");
  conteudo.className = cls("conteudo", `pagina-${rota}`);
  conteudo.innerHTML = carregando();

  const contexto = {
    mes: estado.mes,
    ano: estado.ano,
    parametro,
    usuario: estado.usuario,
    recarregar: () => renderizarPagina(),
    aindaAtual: () => minhaVez === renderizacao, // evita desenhar uma tela antiga depois de trocar de mês
    mudarMes,
    irPara,
  };

  // Cada renderização desenha numa "folha" nova: assim os eventos da tela anterior não se acumulam.
  const folha = document.createElement("div");
  folha.className = "folha";
  try {
    await pagina.modulo.render(folha, contexto);
    if (minhaVez === renderizacao) conteudo.replaceChildren(folha);
    folha.querySelectorAll(SELETOR_NOVO).forEach((b) => { b.title ||= `${b.textContent.trim()} (N)`; });
  } catch (e) {
    if (minhaVez !== renderizacao) return;
    conteudo.innerHTML = `${erroDeCarga(e.message)}${BOTAO_TENTAR}`;
    conteudo.querySelector("[data-tentar]").addEventListener("click", () => renderizarPagina());
  }
}

// ---------- Atalhos de teclado ----------
// N = botão "Nova/Novo" da página; [ e ] = mês anterior/próximo.
// Não valem digitando num campo, com Ctrl/Alt/Cmd apertado nem com uma janela aberta.

const SELETOR_NOVO = '[data-acao="nova"], [data-acao="novo"]';

document.addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.altKey || e.metaKey || e.repeat) return;
  const alvo = e.target;
  if (alvo.closest?.("input, select, textarea, [contenteditable]") || document.querySelector("dialog[open]")) return;
  if (document.body.classList.contains("modo-entrada")) return;

  if (e.key === "n" || e.key === "N") {
    const botao = raiz.querySelector("#conteudo")?.querySelector(SELETOR_NOVO);
    if (botao && !botao.disabled) { e.preventDefault(); botao.click(); }
  } else if (e.key === "[" || e.key === "]") {
    const seletor = raiz.querySelector("[data-seletor-mes]");
    if (!seletor || seletor.hidden) return;
    e.preventDefault();
    mudarMes((e.key === "[" ? mesAnterior : mesSeguinte)(estado.mes, estado.ano));
  }
});

window.addEventListener("hashchange", renderizarPagina);
renderizarPagina();
