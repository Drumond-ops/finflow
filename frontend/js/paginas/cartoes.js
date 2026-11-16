// Cartões e faturas. API Python: /cartoes, /cartoes/{id}/fatura, /planejamentos, /transacoes.
import { python } from "../api.js";
import { barraDeUso } from "../graficos.js";
import { icone } from "../icones.js";
import {
  abrirFormulario, avisar, campoDinheiro, campoNumero, campoSelecao, campoTexto, confirmar, exigirValor, vazio,
} from "../ui.js";
import { cls, dataBR, dataCurta, esc, nomeDoMes, porcento, reais } from "../util.js";

export default {
  async render(el, ctx) {
    const [cartoes, categorias] = await Promise.all([python.get("/cartoes/"), python.get("/categorias/")]);
    if (!ctx.aindaAtual()) return;

    if (!cartoes.length) {
      el.innerHTML = `<section class="planilha">${vazio({
        titulo: "Nenhum cartão cadastrado",
        texto: "Cadastre seus cartões com o dia de fechamento e de vencimento. O FinFlow separa cada compra na fatura certa.",
        botao: "Adicionar cartão", acao: "novo-cartao",
      })}</section>`;
      el.querySelector('[data-acao="novo-cartao"]').addEventListener("click", () => formularioCartao(ctx));
      return;
    }

    const selecionado = cartoes.find((c) => String(c.id) === ctx.parametro) || cartoes[0];
    // A fatura diz o período (fechamento anterior até o fechamento atual); as compras vêm desse período
    const fatura = await python.get(`/cartoes/${selecionado.id}/fatura/`, { mes: ctx.mes, ano: ctx.ano });
    const compras = await python.get("/transacoes/", {
      id_cartao: selecionado.id, data_inicio: fatura.periodo_inicio, data_fim: fatura.periodo_fim, tipo: "despesa",
    });
    if (!ctx.aindaAtual()) return;

    const nomeCategoria = Object.fromEntries(categorias.map((c) => [c.id, c.nome]));

    el.innerHTML = `
      <div class="grade-cartoes">
        <section class="planilha lista-cartoes">
          <header class="planilha-topo">
            <h2>Cartões</h2>
            <button class="botao botao-secundario botao-pequeno" data-acao="novo-cartao">${icone("mais")}Adicionar</button>
          </header>
          <table class="tabela tabela-selecionavel">
            <thead><tr><th scope="col">Cartão</th><th scope="col" class="num">Fecha</th><th scope="col" class="num">Vence</th></tr></thead>
            <tbody>
              ${cartoes.map((c) => `
                <tr class="${cls(c.id === selecionado.id && "selecionada")}">
                  <td><a class="link-linha" href="#/cartoes/${c.id}" ${c.id === selecionado.id ? 'aria-current="true"' : ""}>${esc(c.nome)}</a></td>
                  <td class="num suave">${c.dia_fechamento ? `dia ${c.dia_fechamento}` : "—"}</td>
                  <td class="num suave">${c.dia_vencimento ? `dia ${c.dia_vencimento}` : "—"}</td>
                </tr>`).join("")}
            </tbody>
          </table>
        </section>

        <div class="coluna">
          <section class="planilha">
            <header class="planilha-topo planilha-topo-grande">
              <div>
                <h2>Fatura ${esc(selecionado.nome)} de ${nomeDoMes(ctx.mes)}</h2>
                <p class="planilha-meta">${textoPeriodo(fatura, selecionado)}</p>
              </div>
              <div class="grupo-botoes">
                <button class="botao-icone" data-acao="editar-cartao" aria-label="Editar cartão" title="Editar cartão">${icone("editar")}</button>
                <button class="botao-icone" data-acao="excluir-cartao" aria-label="Excluir cartão" title="Excluir cartão">${icone("lixeira")}</button>
              </div>
            </header>
            <div class="resumo resumo-embutido">
              <div class="resumo-celula"><span class="resumo-rotulo">Total da fatura</span><span class="resumo-valor">${reais(fatura.valor_total)}</span></div>
              <div class="resumo-celula"><span class="resumo-rotulo">Planejado</span><span class="resumo-valor">${reais(fatura.valor_planejado)}</span></div>
              ${fatura.valor_planejado === 0
                ? `<div class="resumo-celula"><span class="resumo-rotulo">Sem planejamento</span><span class="resumo-valor suave">—</span></div>`
                : `<div class="resumo-celula"><span class="resumo-rotulo">${fatura.saldo < 0 ? "Acima do planejado" : "Ainda dentro do plano"}</span>
                    <span class="resumo-valor ${fatura.saldo < 0 ? "negativo" : ""}">${reais(Math.abs(fatura.saldo))}</span></div>`}
            </div>
          </section>

          <section class="planilha">
            <header class="planilha-topo">
              <h2>Planejado por categoria</h2>
              <button class="botao botao-secundario botao-pequeno" data-acao="planejar">${icone("mais")}Planejar categoria</button>
            </header>
            ${fatura.detalhes_por_categoria.length ? `
              <div class="rolagem">
                <table class="tabela">
                  <thead><tr>
                    <th scope="col">Categoria</th><th scope="col" class="num">Planejado</th><th scope="col" class="num">Gasto</th>
                    <th scope="col" class="num">Saldo</th><th scope="col" class="col-uso">Uso</th><th scope="col" class="col-acoes"><span class="sr">Ações</span></th>
                  </tr></thead>
                  <tbody>
                    ${fatura.detalhes_por_categoria.map((d) => {
                      const status = d.percentual > 100 ? "estourado" : d.percentual >= 80 ? "atencao" : "ok";
                      return `
                        <tr>
                          <td>${esc(d.nome_categoria)}</td>
                          <td class="num">${reais(d.valor_planejado)}</td>
                          <td class="num">${reais(d.valor_gasto)}</td>
                          <td class="num ${d.saldo < 0 ? "negativo" : ""}">${reais(d.saldo)}</td>
                          <td class="col-uso">${barraDeUso(d.percentual, status)}<span class="uso-numero">${porcento(d.percentual)}</span></td>
                          <td class="col-acoes">
                            <button class="botao-icone" data-editar-plano="${d.id_categoria}" aria-label="Editar planejamento de ${esc(d.nome_categoria)}">${icone("editar")}</button>
                            <button class="botao-icone" data-excluir-plano="${d.id_categoria}" aria-label="Excluir planejamento de ${esc(d.nome_categoria)}">${icone("lixeira")}</button>
                          </td>
                        </tr>`;
                    }).join("")}
                  </tbody>
                </table>
              </div>` : `<p class="planilha-vazia">Defina quanto pretende gastar em cada categoria neste cartão. Ex.: Mercado R$ 600,00.</p>`}
          </section>

          <section class="planilha">
            <header class="planilha-topo">
              <h2>Compras nesta fatura</h2>
              <span class="planilha-meta">${compras.length} ${compras.length === 1 ? "compra" : "compras"}</span>
            </header>
            ${compras.length ? `
              <div class="rolagem">
                <table class="tabela tabela-compacta">
                  <thead><tr><th scope="col" class="col-data">Data</th><th scope="col">Descrição</th><th scope="col">Categoria</th><th scope="col" class="num">Valor</th></tr></thead>
                  <tbody>
                    ${compras.map((t) => `
                      <tr>
                        <td class="col-data">${dataBR(t.data)}</td>
                        <td>${esc(t.descricao || "Compra")}${t.origem === "assinatura" ? ' <span class="etiqueta etiqueta-java">assinatura</span>' : ""}</td>
                        <td>${esc(nomeCategoria[t.id_categoria] || "—")}</td>
                        <td class="num">${reais(t.valor)}</td>
                      </tr>`).join("")}
                  </tbody>
                  <tfoot><tr class="total"><td colspan="3">Total da fatura</td><td class="num">${reais(fatura.valor_total)}</td></tr></tfoot>
                </table>
              </div>` : `<p class="planilha-vazia">Nenhuma compra neste período. Lance uma despesa escolhendo este cartão como forma de pagamento.</p>`}
          </section>
        </div>
      </div>`;

    // ---------- Ações ----------
    el.querySelector('[data-acao="novo-cartao"]').addEventListener("click", () => formularioCartao(ctx));
    el.querySelector('[data-acao="editar-cartao"]').addEventListener("click", () => formularioCartao(ctx, selecionado));
    el.querySelector('[data-acao="excluir-cartao"]').addEventListener("click", async () => {
      const ok = await confirmar({
        titulo: `Excluir o cartão ${esc(selecionado.nome)}?`,
        mensagem: "Os planejamentos dele também serão removidos. Cartões com compras registradas não podem ser excluídos.",
      });
      if (!ok) return;
      try {
        await python.del(`/cartoes/${selecionado.id}`);
        avisar("Cartão excluído.");
        ctx.irPara("cartoes");
      } catch (e) { avisar(e.message, "erro"); }
    });

    const planejamentosDoMes = () => python.get("/planejamentos/", { mes: ctx.mes, ano: ctx.ano, id_cartao: selecionado.id });

    el.querySelector('[data-acao="planejar"]').addEventListener("click", async () => {
      const existentes = new Set(fatura.detalhes_por_categoria.map((d) => d.id_categoria));
      const livres = categorias.filter((c) => !existentes.has(c.id));
      if (!livres.length) { avisar("Todas as categorias já têm planejamento nesta fatura.", "info"); return; }
      const ok = await abrirFormulario({
        titulo: "Planejar categoria",
        descricao: `Fatura ${esc(selecionado.nome)} que vence em ${nomeDoMes(ctx.mes)} de ${ctx.ano}.`,
        botao: "Salvar planejamento",
        campos: `
          ${campoSelecao("id_categoria", "Categoria", livres.map((c) => ({ valor: c.id, texto: c.nome })))}
          ${campoDinheiro("valor", "Quanto pretende gastar")}`,
        async aoEnviar(d) {
          exigirValor(d.valor);
          await python.post("/planejamentos/", {
            mes: ctx.mes, ano: ctx.ano, valor: d.valor, id_cartao: selecionado.id, id_categoria: Number(d.id_categoria),
          });
        },
      });
      if (ok) { avisar("Planejamento salvo."); ctx.recarregar(); }
    });

    el.querySelectorAll("[data-editar-plano]").forEach((b) => b.addEventListener("click", async () => {
      const idCategoria = Number(b.dataset.editarPlano);
      const plano = (await planejamentosDoMes()).find((p) => p.id_categoria === idCategoria);
      if (!plano) return;
      const ok = await abrirFormulario({
        titulo: `Planejado para ${esc(nomeCategoria[idCategoria])}`,
        botao: "Salvar",
        campos: campoDinheiro("valor", "Quanto pretende gastar", { valor: plano.valor }),
        async aoEnviar(d) {
          exigirValor(d.valor);
          await python.put(`/planejamentos/${plano.id}`, { valor: d.valor });
        },
      });
      if (ok) { avisar("Planejamento atualizado."); ctx.recarregar(); }
    }));

    el.querySelectorAll("[data-excluir-plano]").forEach((b) => b.addEventListener("click", async () => {
      const idCategoria = Number(b.dataset.excluirPlano);
      const ok = await confirmar({
        titulo: "Remover planejamento?",
        mensagem: `As compras continuam na fatura. Só o limite de ${esc(nomeCategoria[idCategoria])} deixa de existir.`,
        botao: "Remover",
      });
      if (!ok) return;
      try {
        const plano = (await planejamentosDoMes()).find((p) => p.id_categoria === idCategoria);
        await python.del(`/planejamentos/${plano.id}`);
        avisar("Planejamento removido.");
        ctx.recarregar();
      } catch (e) { avisar(e.message, "erro"); }
    }));
  },
};

function textoPeriodo(fatura, cartao) {
  const compras = `Compras de ${dataCurta(fatura.periodo_inicio)} a ${dataCurta(fatura.periodo_fim)}`;
  const vence = fatura.data_vencimento ? `, vence em ${dataBR(fatura.data_vencimento)}` : "";
  let dica = "";
  if (!cartao.dia_fechamento) dica = ". Cadastre o dia de fechamento para separar as faturas certinho";
  else if (!cartao.dia_vencimento) dica = ". Cadastre o dia de vencimento para ver quando ela vence";
  return `${compras}${vence}${dica}.`;
}

async function formularioCartao(ctx, cartao = null) {
  const salvo = await abrirFormulario({
    titulo: cartao ? `Editar ${esc(cartao.nome)}` : "Adicionar cartão",
    botao: cartao ? "Salvar alterações" : "Adicionar cartão",
    campos: `
      ${campoTexto("nome", "Nome", { valor: cartao?.nome || "", max: 50, placeholder: "Ex.: Nubank" })}
      <div class="campos-lado">
        ${campoNumero("dia_fechamento", "Dia do fechamento", { valor: cartao?.dia_fechamento ?? "", placeholder: "Ex.: 3" })}
        ${campoNumero("dia_vencimento", "Dia do vencimento", { valor: cartao?.dia_vencimento ?? "", placeholder: "Ex.: 10" })}
      </div>
      <p class="campo-ajuda">Compras feitas depois do fechamento vão para a fatura do mês seguinte.</p>`,
    async aoEnviar(d) {
      if (!d.nome) throw new Error("Dê um nome ao cartão.");
      for (const campo of ["dia_fechamento", "dia_vencimento"]) {
        if (d[campo] !== null && (d[campo] < 1 || d[campo] > 31)) throw new Error("Os dias precisam estar entre 1 e 31.");
      }
      const corpo = { nome: d.nome, dia_fechamento: d.dia_fechamento, dia_vencimento: d.dia_vencimento };
      return cartao ? python.put(`/cartoes/${cartao.id}`, corpo) : python.post("/cartoes/", corpo);
    },
  });
  if (salvo) {
    avisar(cartao ? "Cartão atualizado." : "Cartão adicionado.");
    ctx.irPara(`cartoes/${salvo.id}`);
  }
}
