// Componentes de interface reaproveitados: janelas (dialog), confirmação, avisos e formulários.
import { icone } from "./icones.js";
import { esc, paraCentavos, reaisSemSimbolo } from "./util.js";

// ---------- Avisos (toasts) ----------

export function avisar(mensagem, tipo = "ok") {
  const area = document.getElementById("avisos");
  const el = document.createElement("div");
  el.className = `aviso aviso-${tipo}`;
  el.setAttribute("role", tipo === "erro" ? "alert" : "status");
  el.textContent = mensagem;
  area.appendChild(el);
  setTimeout(() => {
    el.classList.add("saindo");
    setTimeout(() => el.remove(), 250);
  }, tipo === "erro" ? 6000 : 3200);
}

// ---------- Janela com formulário ----------

/**
 * Abre uma janela com formulário.
 *   campos: HTML dos campos (use os helpers campoTexto, campoDinheiro...)
 *   aoEnviar(dados, form): async; se lançar erro, a mensagem aparece na janela e ela continua aberta
 *   aoAbrir(form): para ligar comportamentos extras (ex.: dica dinâmica)
 */
export function abrirFormulario({ titulo, descricao = "", campos, botao = "Salvar", perigo = false, aoEnviar, aoAbrir }) {
  return new Promise((resolver) => {
    const dialogo = document.createElement("dialog");
    dialogo.className = "janela";
    dialogo.innerHTML = `
      <form method="dialog" novalidate>
        <header class="janela-topo">
          <h2>${esc(titulo)}</h2>
          <button type="button" class="botao-icone" data-fechar aria-label="Fechar">${icone("fechar")}</button>
        </header>
        ${descricao ? `<p class="janela-descricao">${descricao}</p>` : ""}
        <div class="janela-corpo">${campos}</div>
        <p class="janela-erro" role="alert" hidden></p>
        <footer class="janela-rodape">
          <button type="button" class="botao botao-secundario" data-fechar>Cancelar</button>
          <button type="submit" class="botao ${perigo ? "botao-perigo" : "botao-primario"}">${esc(botao)}</button>
        </footer>
      </form>`;
    document.body.appendChild(dialogo);

    const form = dialogo.querySelector("form");
    const erro = dialogo.querySelector(".janela-erro");
    const enviar = form.querySelector('button[type="submit"]');
    let resultado = null;

    const fechar = () => dialogo.close();
    dialogo.querySelectorAll("[data-fechar]").forEach((b) => b.addEventListener("click", fechar));
    dialogo.addEventListener("close", () => {
      dialogo.remove();
      resolver(resultado);
    });

    form.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      erro.hidden = true;
      enviar.disabled = true;
      enviar.classList.add("carregando");
      try {
        resultado = (await aoEnviar(lerFormulario(form), form)) ?? true;
        fechar();
      } catch (e) {
        erro.textContent = e.message;
        erro.hidden = false;
      } finally {
        enviar.disabled = false;
        enviar.classList.remove("carregando");
      }
    });

    if (aoAbrir) aoAbrir(form);
    dialogo.showModal();
    const primeiro = form.querySelector("input:not([type=hidden]):not([type=radio]), select, textarea");
    if (primeiro) primeiro.focus();
  });
}

/** Pergunta de confirmação (ex.: antes de excluir). Devolve true/false. */
export async function confirmar({ titulo, mensagem, botao = "Excluir", perigo = true }) {
  const ok = await abrirFormulario({
    titulo,
    campos: `<p class="texto-confirmacao">${mensagem}</p>`,
    botao,
    perigo,
    aoEnviar: async () => true,
  });
  return ok === true;
}

// ---------- Campos de formulário ----------

const idUnico = (() => { let n = 0; return (nome) => `campo-${nome}-${++n}`; })();

function rotulado(nome, rotulo, controle, ajuda = "") {
  const id = idUnico(nome);
  return `
    <div class="campo">
      <label for="${id}">${esc(rotulo)}</label>
      ${controle.replace("{{id}}", id)}
      ${ajuda ? `<p class="campo-ajuda" data-ajuda="${nome}">${ajuda}</p>` : ""}
    </div>`;
}

export function campoTexto(nome, rotulo, { valor = "", obrigatorio = true, max = 100, tipo = "text", placeholder = "", ajuda = "", autocomplete = "off" } = {}) {
  return rotulado(nome, rotulo,
    `<input id="{{id}}" name="${nome}" type="${tipo}" value="${esc(valor)}" maxlength="${max}" placeholder="${esc(placeholder)}" autocomplete="${autocomplete}" ${obrigatorio ? "required" : ""}>`,
    ajuda);
}

export function campoDinheiro(nome, rotulo, { valor = null, obrigatorio = true, ajuda = "" } = {}) {
  return rotulado(nome, rotulo,
    `<div class="campo-dinheiro"><span aria-hidden="true">R$</span><input id="{{id}}" name="${nome}" data-tipo="dinheiro" inputmode="decimal" placeholder="0,00" value="${valor == null ? "" : reaisSemSimbolo(valor)}" ${obrigatorio ? "required" : ""}></div>`,
    ajuda);
}

export function campoData(nome, rotulo, { valor = "", ajuda = "" } = {}) {
  return rotulado(nome, rotulo, `<input id="{{id}}" name="${nome}" type="date" value="${esc(valor)}" required>`, ajuda);
}

export function campoNumero(nome, rotulo, { valor = "", min = 1, max = 31, obrigatorio = false, ajuda = "", placeholder = "" } = {}) {
  return rotulado(nome, rotulo,
    `<input id="{{id}}" name="${nome}" data-tipo="inteiro" type="number" inputmode="numeric" min="${min}" max="${max}" value="${esc(valor ?? "")}" placeholder="${esc(placeholder)}" ${obrigatorio ? "required" : ""}>`,
    ajuda);
}

/** opcoes: [{ valor, texto }] */
export function campoSelecao(nome, rotulo, opcoes, { valor = "", ajuda = "", vazio = null } = {}) {
  const itens = [
    vazio !== null ? `<option value="">${esc(vazio)}</option>` : "",
    ...opcoes.map((o) => `<option value="${esc(o.valor)}" ${String(o.valor) === String(valor) ? "selected" : ""}>${esc(o.texto)}</option>`),
  ].join("");
  return rotulado(nome, rotulo, `<select id="{{id}}" name="${nome}" ${vazio === null ? "required" : ""}>${itens}</select>`, ajuda);
}

/** Botões segmentados (ex.: Despesa | Receita). opcoes: [{ valor, texto }] */
export function campoSegmentado(nome, rotulo, opcoes, valor) {
  return `
    <fieldset class="campo">
      <legend>${esc(rotulo)}</legend>
      <div class="segmentado">
        ${opcoes.map((o) => `
          <label><input type="radio" name="${nome}" value="${esc(o.valor)}" ${o.valor === valor ? "checked" : ""}><span>${esc(o.texto)}</span></label>`).join("")}
      </div>
    </fieldset>`;
}

export function campoMarcar(nome, texto, marcado = true) {
  return `<label class="campo-marcar"><input type="checkbox" name="${nome}" ${marcado ? "checked" : ""}><span>${esc(texto)}</span></label>`;
}

/** Lê o formulário convertendo dinheiro para centavos e números para inteiros. */
export function lerFormulario(form) {
  const dados = {};
  for (const el of form.elements) {
    if (!el.name || el.disabled) continue;
    if (el.type === "radio" && !el.checked) continue;
    if (el.type === "checkbox") { dados[el.name] = el.checked; continue; }
    const texto = el.value.trim();
    if (el.dataset.tipo === "dinheiro") dados[el.name] = texto === "" ? null : paraCentavos(texto);
    else if (el.dataset.tipo === "inteiro") dados[el.name] = texto === "" ? null : Number(texto);
    else dados[el.name] = texto;
  }
  return dados;
}

/** Validação simples feita antes de enviar à API (a API também valida). */
export function exigirValor(centavos, nome = "o valor") {
  if (centavos === null || Number.isNaN(centavos)) throw new Error(`Informe ${nome}, por exemplo 49,90.`);
  if (centavos <= 0) throw new Error(`${nome[0].toUpperCase()}${nome.slice(1)} precisa ser maior que zero.`);
}

// ---------- Blocos de página ----------

export function vazio({ titulo, texto, botao = "", acao = "" }) {
  return `
    <div class="vazio">
      <p class="vazio-titulo">${esc(titulo)}</p>
      <p class="vazio-texto">${texto}</p>
      ${botao ? `<button class="botao botao-primario" data-acao="${acao}">${icone("mais")}${esc(botao)}</button>` : ""}
    </div>`;
}

export function erroDeCarga(mensagem) {
  return `<div class="falha" role="alert"><strong>Não foi possível carregar.</strong> ${esc(mensagem)}</div>`;
}

export function carregando() {
  return `<div class="carregando-pagina" aria-busy="true"><span></span><span></span><span></span></div>`;
}

/** Selo que mostra de qual API veio um dado (ajuda a explicar a integração). */
export function seloApi(api) {
  return api === "java"
    ? `<span class="selo-api selo-java" title="Dados da API Java (Spring Boot, porta 8081)">API Java</span>`
    : `<span class="selo-api selo-python" title="Dados da API Python (FastAPI, porta 8000)">API Python</span>`;
}
