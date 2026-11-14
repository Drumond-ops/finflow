/**
 * Comunicação com as duas APIs do FinFlow.
 *
 *   python.get("/dashboard/", { mes: 11, ano: 2026 })   -> API Python (FastAPI, porta 8000)
 *   java.post("/assinaturas", { nome: "Netflix", ... })  -> API Java (Spring Boot, porta 8081)
 *
 * Toda chamada:
 *   - envia o token de login no cabeçalho Authorization (o mesmo token vale nas duas APIs);
 *   - transforma a resposta JSON em objeto, ou o erro {"detail": ...} em uma mensagem legível;
 *   - é registrada no painel de requisições (barra inferior), para mostrar qual API respondeu.
 */
import { CONFIG } from "./config.js";

const CHAVE_TOKEN = "finflow.token";

export const APIS = {
  python: { id: "python", nome: "API Python", base: CONFIG.API_PYTHON },
  java: { id: "java", nome: "API Java", base: CONFIG.API_JAVA },
};

// ---------- Sessão ----------

export const sessao = {
  get token() {
    try { return localStorage.getItem(CHAVE_TOKEN); } catch { return null; }
  },
  salvar(token) {
    try { localStorage.setItem(CHAVE_TOKEN, token); } catch { /* navegador sem armazenamento */ }
  },
  sair() {
    try { localStorage.removeItem(CHAVE_TOKEN); } catch { /* idem */ }
  },
};

// ---------- Registro de requisições (painel inferior) ----------

export const registro = {
  itens: [],
  ouvintes: new Set(),
  adicionar(item) {
    this.itens.unshift(item);
    this.itens.length = Math.min(this.itens.length, 80);
    this.ouvintes.forEach((fn) => fn(item));
  },
  ouvir(fn) {
    this.ouvintes.add(fn);
    return () => this.ouvintes.delete(fn);
  },
};

// ---------- Erros ----------

export class ErroApi extends Error {
  constructor(mensagem, status, api) {
    super(mensagem);
    this.status = status;
    this.api = api;
  }
}

/** FastAPI devolve {"detail": "texto"} ou {"detail": [{loc, msg}, ...]} (validação). */
function mensagemDoErro(corpo, status) {
  const detalhe = corpo && corpo.detail;
  if (typeof detalhe === "string") return detalhe;
  if (Array.isArray(detalhe) && detalhe.length) {
    return detalhe
      .map((e) => {
        const campo = Array.isArray(e.loc) ? e.loc.filter((p) => p !== "body" && p !== "query").join(".") : "";
        return campo ? `${campo}: ${e.msg}` : e.msg;
      })
      .join("; ");
  }
  return `A requisição falhou (código ${status}).`;
}

// ---------- Requisição ----------

let aoExpirarSessao = () => {};
export function quandoSessaoExpirar(fn) {
  aoExpirarSessao = fn;
}

async function requisitar(api, metodo, caminho, { corpo, formulario, consulta, arquivo } = {}) {
  const url = new URL(api.base + caminho);
  Object.entries(consulta || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  });

  const cabecalhos = { Accept: arquivo ? "application/pdf" : "application/json" };
  if (sessao.token) cabecalhos.Authorization = `Bearer ${sessao.token}`;

  let body;
  if (formulario) {
    body = new URLSearchParams(formulario);
  } else if (corpo !== undefined) {
    cabecalhos["Content-Type"] = "application/json";
    body = JSON.stringify(corpo);
  }

  const inicio = performance.now();
  const item = { api: api.id, metodo, caminho: url.pathname + url.search, hora: new Date(), status: 0, ms: 0 };

  let resposta;
  try {
    resposta = await fetch(url, { method: metodo, headers: cabecalhos, body });
  } catch {
    item.ms = Math.round(performance.now() - inicio);
    registro.adicionar(item);
    const endereco = api.base.replace(/^https?:\/\//, "");
    throw new ErroApi(`Não foi possível falar com a ${api.nome} (${endereco}). Ela está rodando?`, 0, api.id);
  }

  item.status = resposta.status;
  item.ms = Math.round(performance.now() - inicio);
  registro.adicionar(item);

  if (resposta.status === 401 && caminho !== "/auth/login") {
    sessao.sair();
    aoExpirarSessao();
    throw new ErroApi("Sua sessão expirou. Entre de novo.", 401, api.id);
  }

  if (!resposta.ok) {
    let corpoErro = null;
    try { corpoErro = await resposta.json(); } catch { /* resposta sem JSON */ }
    throw new ErroApi(mensagemDoErro(corpoErro, resposta.status), resposta.status, api.id);
  }

  if (resposta.status === 204) return null;
  if (arquivo) return resposta.blob();
  return resposta.json();
}

function cliente(api) {
  return {
    get: (caminho, consulta) => requisitar(api, "GET", caminho, { consulta }),
    post: (caminho, corpo, consulta) => requisitar(api, "POST", caminho, { corpo, consulta }),
    put: (caminho, corpo) => requisitar(api, "PUT", caminho, { corpo }),
    del: (caminho, consulta) => requisitar(api, "DELETE", caminho, { consulta }),
    formulario: (caminho, dados) => requisitar(api, "POST", caminho, { formulario: dados }),
    arquivo: (caminho, consulta) => requisitar(api, "GET", caminho, { consulta, arquivo: true }),
  };
}

export const python = cliente(APIS.python);
export const java = cliente(APIS.java);

/** Usado pelos indicadores de status no menu lateral. */
export async function apiNoAr(api) {
  const inicio = performance.now();
  try {
    const r = await fetch(api.base + "/", { headers: { Accept: "application/json" } });
    return { ok: r.ok, ms: Math.round(performance.now() - inicio) };
  } catch {
    return { ok: false, ms: 0 };
  }
}
