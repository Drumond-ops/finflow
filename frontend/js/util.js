// Formatação, datas e pequenas ajudas usadas por todas as telas.

// ---------- Texto seguro em HTML ----------

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
/** Sempre use esc() ao colocar dados do usuário dentro de HTML. */
export const esc = (valor) => String(valor ?? "").replace(/[&<>"']/g, (c) => ESCAPES[c]);

// ---------- Dinheiro (a API trabalha em centavos) ----------

const formatoReal = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const formatoNumero = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** 123456 -> "R$ 1.234,56" */
export const reais = (centavos) => formatoReal.format((centavos || 0) / 100);

/** 123456 -> "1.234,56" (para preencher campos de formulário) */
export const reaisSemSimbolo = (centavos) => formatoNumero.format((centavos || 0) / 100);

/**
 * Lê o que a pessoa digitou e devolve centavos.
 * Aceita "1.234,56", "1234,56", "1234.56", "R$ 50" e "50". Devolve NaN se não entender.
 */
export function paraCentavos(texto) {
  let t = String(texto || "").replace(/[R$\s]/g, "");
  if (!t) return NaN;
  if (t.includes(",")) t = t.replace(/\./g, "").replace(",", ".");
  else if (/^\d{1,3}(\.\d{3})+$/.test(t)) t = t.replace(/\./g, ""); // "1.234" = mil e duzentos
  const numero = Number(t);
  return Number.isFinite(numero) ? Math.round(numero * 100) : NaN;
}

export const porcento = (valor) => `${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(valor || 0)}%`;

// ---------- Datas (a API usa "AAAA-MM-DD") ----------

export const MESES = [
  "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];
const MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

export const nomeDoMes = (mes) => MESES[mes - 1];
export const tituloDoMes = (mes, ano) => `${MESES[mes - 1][0].toUpperCase()}${MESES[mes - 1].slice(1)} de ${ano}`;

/** "2026-11-05" -> "05/11/2026" */
export function dataBR(iso) {
  if (!iso) return "—";
  const [a, m, d] = iso.split("-");
  return `${d}/${m}/${a}`;
}

/** "2026-11-05" -> "5 nov" */
export function dataCurta(iso) {
  if (!iso) return "—";
  const [, m, d] = iso.split("-").map(Number);
  return `${d} ${MESES_CURTOS[m - 1]}`;
}

const doisDigitos = (n) => String(n).padStart(2, "0");
export const isoDe = (ano, mes, dia) => `${ano}-${doisDigitos(mes)}-${doisDigitos(dia)}`;

export function hojeISO() {
  const d = new Date();
  return isoDe(d.getFullYear(), d.getMonth() + 1, d.getDate());
}

export const diasNoMes = (ano, mes) => new Date(ano, mes, 0).getDate();

/** Data sugerida para um lançamento no mês selecionado: hoje, se for o mês atual; senão, dia 1. */
export function dataPadraoDoMes(mes, ano) {
  const hoje = new Date();
  if (hoje.getFullYear() === ano && hoje.getMonth() + 1 === mes) return hojeISO();
  return isoDe(ano, mes, 1);
}

export function mesAnterior(mes, ano) {
  return mes === 1 ? { mes: 12, ano: ano - 1 } : { mes: mes - 1, ano };
}
export function mesSeguinte(mes, ano) {
  return mes === 12 ? { mes: 1, ano: ano + 1 } : { mes: mes + 1, ano };
}

/**
 * Em qual fatura cai uma compra no cartão (mesma regra da API Python, ciclo_fatura.py):
 * a fatura de um mês é a que VENCE nesse mês; compras depois do fechamento vão para a próxima.
 */
export function faturaDaCompra(cartao, iso) {
  const [ano, mes, dia] = iso.split("-").map(Number);
  const fechamento = cartao.dia_fechamento;
  const vencimento = cartao.dia_vencimento;
  if (!fechamento) return { mes, ano };

  let ref = dia <= Math.min(fechamento, diasNoMes(ano, mes)) ? { mes, ano } : mesSeguinte(mes, ano);
  if (vencimento && fechamento >= vencimento) ref = mesSeguinte(ref.mes, ref.ano);
  return ref;
}

// ---------- Diversos ----------

/** Junta classes CSS ignorando as vazias: cls("a", cond && "b") */
export const cls = (...nomes) => nomes.filter(Boolean).join(" ");

/** Texto para comparar em buscas: sem acento e em minúsculas ("Café" -> "cafe"). */
export const paraBusca = (texto) => String(texto ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

export const somar = (lista, campo) => lista.reduce((total, item) => total + (item[campo] || 0), 0);
