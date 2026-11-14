// Painel do mês. Junta dados das DUAS APIs:
//   API Python: /dashboard, /transacoes, /categorias, /cartoes, /relatorios/pdf
//   API Java:   /assinaturas/resumo
import { java, python } from "../api.js";
import { barraDeUso, colunasPorDia } from "../graficos.js";
import { icone } from "../icones.js";
import { avisar, seloApi } from "../ui.js";
import { dataBR, dataCurta, diasNoMes, esc, nomeDoMes, porcento, reais } from "../util.js";
import { abrirTransacao } from "./lancamentos.js";

export default {
  async render(el, ctx) {
    const [painel, transacoes, categorias, cartoes, assinaturas] = await Promise.all([
      python.get("/dashboard/", { mes: ctx.mes, ano: ctx.ano }),
      python.get("/transacoes/", { mes: ctx.mes, ano: ctx.ano }),
      python.get("/categorias/"),
      python.get("/cartoes/"),
      // Se a API Java estiver fora do ar, o painel continua funcionando sem esse bloco
      java.get("/assinaturas/resumo", { dias: 30 }).catch((e) => ({ erro: e.message })),
    ]);
    if (!ctx.aindaAtual()) return;

    const nomeCategoria = Object.fromEntries(categorias.map((c) => [c.id, c.nome]));
    const nomeCartao = Object.fromEntries(cartoes.map((c) => [c.id, c.nome]));

    // Despesas por dia (pela data da compra, incluindo cartão)
    const porDia = Array(diasNoMes(ctx.ano, ctx.mes)).fill(0);
    transacoes.filter((t) => t.tipo === "despesa").forEach((t) => { porDia[Number(t.data.slice(8, 10)) - 1] += t.valor; });
    const totalDoMes = porDia.reduce((a, b) => a + b, 0);
    const hoje = new Date();
    const diaDeHoje = hoje.getFullYear() === ctx.ano && hoje.getMonth() + 1 === ctx.mes ? hoje.getDate() : null;

    const gastos = painel.gastos_categoria;
    const totalGastos = gastos.reduce((s, g) => s + g.valor_gasto, 0);
    const maiorGasto = Math.max(...gastos.map((g) => g.valor_gasto), 1);

    el.innerHTML = `
      <div class="barra-acoes">
        <p class="barra-acoes-texto">Resumo de ${nomeDoMes(ctx.mes)}: o que entrou, o que saiu e o que ainda vence.</p>
        <div class="grupo-botoes">
          <button class="botao botao-secundario" data-acao="pdf">${icone("baixar")}Relatório em PDF</button>
          <button class="botao botao-primario" data-acao="nova">${icone("mais")}Nova transação</button>
        </div>
      </div>

      <section class="planilha resumo" aria-label="Resumo do mês">
        <div class="resumo-celula">
          <span class="resumo-rotulo">Receitas</span>
          <span class="resumo-valor positivo">${reais(painel.total_receitas)}</span>
        </div>
        <div class="resumo-celula">
          <span class="resumo-rotulo">Despesas na conta</span>
          <span class="resumo-valor">${reais(painel.total_despesas)}</span>
        </div>
        <div class="resumo-celula">
          <span class="resumo-rotulo">Faturas que vencem no mês</span>
          <span class="resumo-valor">${reais(painel.total_faturas)}</span>
        </div>
        <div class="resumo-celula resumo-saldo">
          <span class="resumo-rotulo">Saldo do mês</span>
          <span class="resumo-valor ${painel.saldo_mes < 0 ? "negativo" : ""}">${reais(painel.saldo_mes)}</span>
        </div>
      </section>

      <div class="grade-painel">
        <div class="coluna">
          <section class="planilha">
            <header class="planilha-topo">
              <h2>Despesas por dia</h2>
              <span class="planilha-meta">${reais(totalDoMes)} no mês, contando compras no cartão</span>
            </header>
            <div class="grafico">${colunasPorDia(porDia, { hoje: diaDeHoje })}</div>
          </section>

          <section class="planilha">
            <header class="planilha-topo">
              <h2>Gastos por categoria</h2>
              <a class="link" href="#/lancamentos">Ver lançamentos</a>
            </header>
            ${gastos.length ? `
              <div class="rolagem"><table class="tabela tabela-compacta">
                <thead><tr><th scope="col">Categoria</th><th scope="col" class="num">Valor</th><th scope="col" class="num col-pct">Parte</th></tr></thead>
                <tbody>
                  ${gastos.map((g) => `
                    <tr>
                      <td>${esc(g.nome_categoria)}</td>
                      <td class="num celula-barra" style="--barra:${((g.valor_gasto / maiorGasto) * 100).toFixed(1)}%">${reais(g.valor_gasto)}</td>
                      <td class="num col-pct suave">${porcento((g.valor_gasto / totalGastos) * 100)}</td>
                    </tr>`).join("")}
                </tbody>
                <tfoot><tr class="total"><td>Total</td><td class="num">${reais(totalGastos)}</td><td class="num col-pct">100%</td></tr></tfoot>
              </table></div>` : `<p class="planilha-vazia">Sem despesas em ${nomeDoMes(ctx.mes)}.</p>`}
          </section>
        </div>

        <div class="coluna">
          ${blocoOrcamento(painel.orcamento, ctx)}
          ${blocoFaturas(painel.faturas)}
          ${blocoAssinaturas(assinaturas)}
          ${blocoObjetivos(painel.objetivos_resumo)}
        </div>
      </div>

      <section class="planilha">
        <header class="planilha-topo">
          <h2>Últimos lançamentos</h2>
          <a class="link" href="#/lancamentos">Ver todos</a>
        </header>
        ${painel.resumo_transacao.length ? `
          <div class="rolagem">
            <table class="tabela tabela-compacta">
              <thead><tr><th scope="col" class="col-data">Data</th><th scope="col">Descrição</th><th scope="col">Categoria</th><th scope="col">Forma</th><th scope="col" class="num">Valor</th></tr></thead>
              <tbody>
                ${painel.resumo_transacao.map((t) => `
                  <tr>
                    <td class="col-data">${dataBR(t.data)}</td>
                    <td>${esc(t.descricao || (t.tipo === "receita" ? "Receita" : "Despesa"))}</td>
                    <td>${esc(nomeCategoria[t.id_categoria] || "—")}</td>
                    <td class="suave">${t.id_cartao ? esc(nomeCartao[t.id_cartao] || "Cartão") : "Conta"}</td>
                    <td class="num ${t.tipo === "receita" ? "positivo" : ""}">${t.tipo === "receita" ? "" : "−"}${reais(t.valor)}</td>
                  </tr>`).join("")}
              </tbody>
            </table>
          </div>` : `<p class="planilha-vazia">Nenhum lançamento ainda. Comece pelo botão Nova transação.</p>`}
      </section>`;

    el.querySelector('[data-acao="nova"]').addEventListener("click", () => abrirTransacao({ ctx, categorias, cartoes }));
    el.querySelector('[data-acao="pdf"]').addEventListener("click", async (e) => {
      const botao = e.currentTarget;
      botao.disabled = true;
      try {
        const pdf = await python.arquivo("/relatorios/pdf", { mes: ctx.mes, ano: ctx.ano });
        const url = URL.createObjectURL(pdf);
        const link = Object.assign(document.createElement("a"), { href: url, download: `finflow_${String(ctx.mes).padStart(2, "0")}_${ctx.ano}.pdf` });
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 2000);
        avisar("Relatório baixado.");
      } catch (falha) {
        avisar(falha.message, "erro");
      } finally {
        botao.disabled = false;
      }
    });
  },
};

function blocoOrcamento(orc, ctx) {
  const corpo = orc.itens.length
    ? `<ul class="lista-uso">
        ${orc.itens.slice().sort((a, b) => b.percentual - a.percentual).slice(0, 5).map((i) => `
          <li>
            <div class="lista-uso-linha"><span>${esc(i.nome_categoria)}</span><span class="num">${reais(i.valor_gasto)} <span class="suave">de ${reais(i.valor_orcado)}</span></span></div>
            ${barraDeUso(i.percentual, i.status)}
          </li>`).join("")}
       </ul>
       <p class="planilha-rodape">${reais(orc.total_gasto)} de ${reais(orc.total_orcado)} orçados (${porcento(orc.percentual)})</p>`
    : `<p class="planilha-vazia">Sem limites para ${nomeDoMes(ctx.mes)}. <a class="link" href="#/orcamento">Definir orçamento</a></p>`;
  return `
    <section class="planilha">
      <header class="planilha-topo"><h2>Orçamento</h2><a class="link" href="#/orcamento">Abrir</a></header>
      ${corpo}
    </section>`;
}

function blocoFaturas(faturas) {
  const corpo = faturas.length
    ? `<div class="rolagem"><table class="tabela tabela-compacta">
        <thead><tr><th scope="col">Cartão</th><th scope="col">Vence</th><th scope="col" class="num">Fatura</th></tr></thead>
        <tbody>
          ${faturas.map((f) => `
            <tr>
              <td><a class="link-linha" href="#/cartoes/${f.id_cartao}">${esc(f.nome_cartao)}</a></td>
              <td class="suave">${f.data_vencimento ? dataCurta(f.data_vencimento) : "—"}</td>
              <td class="num">${reais(f.valor_fatura)}</td>
            </tr>`).join("")}
        </tbody>
       </table></div>`
    : `<p class="planilha-vazia">Nenhum cartão cadastrado. <a class="link" href="#/cartoes">Adicionar cartão</a></p>`;
  return `
    <section class="planilha">
      <header class="planilha-topo"><h2>Faturas</h2><a class="link" href="#/cartoes">Abrir</a></header>
      ${corpo}
    </section>`;
}

function blocoAssinaturas(resumo) {
  let corpo;
  if (resumo.erro) {
    corpo = `<p class="planilha-vazia aviso-inline">${esc(resumo.erro)}</p>`;
  } else if (!resumo.quantidade_ativas) {
    corpo = `<p class="planilha-vazia">Nenhuma assinatura ativa. <a class="link" href="#/assinaturas">Cadastrar</a></p>`;
  } else {
    corpo = `
      <div class="par-valores">
        <div><span class="resumo-rotulo">Por mês</span><span class="valor-medio">${reais(resumo.custo_mensal)}</span></div>
        <div><span class="resumo-rotulo">Por ano</span><span class="valor-medio">${reais(resumo.custo_anual)}</span></div>
      </div>
      ${resumo.proximas_cobrancas.length ? `
        <div class="rolagem"><table class="tabela tabela-compacta">
          <thead><tr><th scope="col">Próximas cobranças</th><th scope="col">Dia</th><th scope="col" class="num">Valor</th></tr></thead>
          <tbody>
            ${resumo.proximas_cobrancas.slice(0, 4).map((c) => `
              <tr><td>${esc(c.nome)}</td><td class="suave">${dataCurta(c.data)}</td><td class="num">${reais(c.valor)}</td></tr>`).join("")}
          </tbody>
        </table></div>` : ""}`;
  }
  return `
    <section class="planilha">
      <header class="planilha-topo"><h2>Assinaturas</h2>${seloApi("java")}</header>
      ${corpo}
    </section>`;
}

function blocoObjetivos(objetivos) {
  const corpo = objetivos.length
    ? `<ul class="lista-uso">
        ${objetivos.slice(0, 4).map((o) => `
          <li>
            <div class="lista-uso-linha"><span>${esc(o.nome_objetivo)}</span><span class="num">${porcento(o.percentual_conclusao)}</span></div>
            ${barraDeUso(o.percentual_conclusao, "meta")}
            <div class="lista-uso-detalhe suave">${reais(o.valor_atual)} de ${reais(o.valor_alvo)}</div>
          </li>`).join("")}
       </ul>`
    : `<p class="planilha-vazia">Nenhum objetivo ainda. <a class="link" href="#/objetivos">Criar objetivo</a></p>`;
  return `
    <section class="planilha">
      <header class="planilha-topo"><h2>Objetivos</h2><a class="link" href="#/objetivos">Abrir</a></header>
      ${corpo}
    </section>`;
}
