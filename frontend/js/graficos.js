// Gráficos em SVG puro (sem bibliotecas).
import { esc, reais } from "./util.js";

/**
 * Colunas de gasto por dia do mês.
 *   valores: array com o total (centavos) de cada dia, índice 0 = dia 1
 *   hoje: número do dia atual (destacado), ou null
 */
export function colunasPorDia(valores, { hoje = null } = {}) {
  const largura = 720;
  const altura = 168;
  const margemBase = 22;
  const util = altura - margemBase - 8;
  const maximo = Math.max(...valores, 1);
  const passo = largura / valores.length;
  const larguraBarra = Math.max(4, passo * 0.62);

  // Linha de referência na média dos dias com gasto
  const comGasto = valores.filter((v) => v > 0);
  const media = comGasto.length ? comGasto.reduce((a, b) => a + b, 0) / comGasto.length : 0;
  const yMedia = 8 + util - (media / maximo) * util;

  const barras = valores.map((v, i) => {
    const h = v > 0 ? Math.max(2, (v / maximo) * util) : 0;
    const x = i * passo + (passo - larguraBarra) / 2;
    const y = 8 + util - h;
    const dia = i + 1;
    const classe = dia === hoje ? "barra barra-hoje" : "barra";
    return `<rect class="${classe}" x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${larguraBarra.toFixed(1)}" height="${h.toFixed(1)}" rx="1.5"><title>Dia ${dia}: ${esc(reais(v))}</title></rect>`;
  }).join("");

  const rotulos = valores.map((_, i) => {
    const dia = i + 1;
    if (dia !== 1 && dia % 5 !== 0 && dia !== valores.length) return "";
    const x = i * passo + passo / 2;
    return `<text x="${x.toFixed(1)}" y="${altura - 6}" text-anchor="middle">${dia}</text>`;
  }).join("");

  return `
    <svg class="grafico-dias" viewBox="0 0 ${largura} ${altura}" preserveAspectRatio="none" role="img" aria-label="Despesas por dia do mês">
      <line class="grafico-base" x1="0" x2="${largura}" y1="${8 + util + 0.5}" y2="${8 + util + 0.5}"/>
      ${media ? `<line class="grafico-media" x1="0" x2="${largura}" y1="${yMedia.toFixed(1)}" y2="${yMedia.toFixed(1)}"/>` : ""}
      ${barras}
      <g class="grafico-rotulos">${rotulos}</g>
    </svg>`;
}

/** Barra de progresso (como a formatação condicional de uma planilha). */
export function barraDeUso(percentual, status = "ok") {
  const largura = Math.max(0, Math.min(100, percentual));
  return `<span class="uso uso-${status}" role="img" aria-label="${Math.round(percentual)}% usado"><span style="width:${largura}%"></span></span>`;
}
