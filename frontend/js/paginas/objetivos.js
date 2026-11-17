// Objetivos de investimento e aportes. API Python: /objetivos, /aportes.
import { python } from "../api.js";
import { barraDeUso } from "../graficos.js";
import { icone } from "../icones.js";
import { abrirFormulario, avisar, campoData, campoDinheiro, campoSelecao, campoTexto, confirmar, exigirValor, vazio } from "../ui.js";
import { dataBR, esc, hojeISO, porcento, reais } from "../util.js";

export default {
  usaMes: false,

  async render(el, ctx) {
    const [objetivos, aportes] = await Promise.all([python.get("/objetivos/"), python.get("/aportes/")]);
    if (!ctx.aindaAtual()) return;

    const nomeObjetivo = Object.fromEntries(objetivos.map((o) => [o.id, o.nome]));
    const guardado = objetivos.reduce((s, o) => s + o.valor_atual, 0);
    const metas = objetivos.reduce((s, o) => s + o.valor_alvo, 0);

    el.innerHTML = objetivos.length ? `
      <div class="barra-acoes">
        <p class="barra-acoes-texto">Cada aporte vira uma despesa do mês (categoria Investimentos) e soma no objetivo.</p>
        <div class="grupo-botoes">
          <button class="botao botao-secundario" data-acao="aportar">${icone("porquinho")}Novo aporte</button>
          <button class="botao botao-primario" data-acao="novo">${icone("mais")}Novo objetivo</button>
        </div>
      </div>

      <section class="planilha">
        <div class="rolagem">
          <table class="tabela">
            <thead><tr>
              <th scope="col">Objetivo</th><th scope="col" class="num">Guardado</th><th scope="col" class="num">Meta</th>
              <th scope="col" class="col-uso">Progresso</th><th scope="col" class="num">Falta</th>
              <th scope="col" class="col-acoes"><span class="sr">Ações</span></th>
            </tr></thead>
            <tbody>
              ${objetivos.map((o) => `
                <tr>
                  <td>${esc(o.nome)}${o.percentual_conclusao >= 100 ? ' <span class="etiqueta etiqueta-ok">concluído</span>' : ""}</td>
                  <td class="num">${reais(o.valor_atual)}</td>
                  <td class="num">${reais(o.valor_alvo)}</td>
                  <td class="col-uso">${barraDeUso(o.percentual_conclusao, "meta")}<span class="uso-numero">${porcento(o.percentual_conclusao)}</span></td>
                  <td class="num">${reais(Math.max(0, o.valor_alvo - o.valor_atual))}</td>
                  <td class="col-acoes">
                    <button class="botao-icone" data-aportar="${o.id}" aria-label="Aportar em ${esc(o.nome)}" title="Aportar">${icone("porquinho")}</button>
                    <button class="botao-icone" data-editar="${o.id}" aria-label="Editar ${esc(o.nome)}">${icone("editar")}</button>
                    <button class="botao-icone" data-excluir="${o.id}" aria-label="Excluir ${esc(o.nome)}">${icone("lixeira")}</button>
                  </td>
                </tr>`).join("")}
            </tbody>
            <tfoot><tr class="total">
              <td>Total</td><td class="num">${reais(guardado)}</td><td class="num">${reais(metas)}</td>
              <td class="col-uso">${barraDeUso(metas ? (guardado / metas) * 100 : 0, "meta")}<span class="uso-numero">${porcento(metas ? (guardado / metas) * 100 : 0)}</span></td>
              <td class="num">${reais(Math.max(0, metas - guardado))}</td><td></td>
            </tr></tfoot>
          </table>
        </div>
      </section>

      <section class="planilha">
        <header class="planilha-topo"><h2>Aportes</h2><span class="planilha-meta">${aportes.length} no total</span></header>
        ${aportes.length ? `
          <div class="rolagem">
            <table class="tabela tabela-compacta">
              <thead><tr><th scope="col" class="col-data">Data</th><th scope="col">Objetivo</th><th scope="col" class="num">Valor</th><th scope="col" class="col-acoes"><span class="sr">Ações</span></th></tr></thead>
              <tbody>
                ${aportes.map((a) => `
                  <tr>
                    <td class="col-data">${dataBR(a.data)}</td>
                    <td>${esc(nomeObjetivo[a.id_objetivo] || "—")}</td>
                    <td class="num">${reais(a.valor)}</td>
                    <td class="col-acoes">
                      <button class="botao-icone" data-editar-aporte="${a.id}" aria-label="Editar aporte de ${dataBR(a.data)} em ${esc(nomeObjetivo[a.id_objetivo] || "objetivo")}">${icone("editar")}</button>
                      <button class="botao-icone" data-excluir-aporte="${a.id}" aria-label="Desfazer aporte de ${dataBR(a.data)} em ${esc(nomeObjetivo[a.id_objetivo] || "objetivo")}">${icone("lixeira")}</button>
                    </td>
                  </tr>`).join("")}
              </tbody>
            </table>
          </div>` : `<p class="planilha-vazia">Nenhum aporte ainda. Use Novo aporte para guardar dinheiro num objetivo.</p>`}
      </section>` : `
      <section class="planilha">${vazio({
        titulo: "Nenhum objetivo ainda",
        texto: "Crie metas como reserva de emergência ou viagem e acompanhe quanto já guardou em cada uma.",
        botao: "Novo objetivo", acao: "novo",
      })}</section>`;

    // ---------- Ações ----------
    el.querySelectorAll('[data-acao="novo"]').forEach((b) => b.addEventListener("click", () => formularioObjetivo(ctx)));
    el.querySelectorAll("[data-editar]").forEach((b) => b.addEventListener("click", () =>
      formularioObjetivo(ctx, objetivos.find((o) => o.id === Number(b.dataset.editar)))));

    const aportar = (idObjetivo = null) => formularioAporte(ctx, objetivos, null, idObjetivo);
    el.querySelector('[data-acao="aportar"]')?.addEventListener("click", () => aportar());
    el.querySelectorAll("[data-aportar]").forEach((b) => b.addEventListener("click", () => aportar(Number(b.dataset.aportar))));
    el.querySelectorAll("[data-editar-aporte]").forEach((b) => b.addEventListener("click", () =>
      formularioAporte(ctx, objetivos, aportes.find((a) => a.id === Number(b.dataset.editarAporte)))));

    el.querySelectorAll("[data-excluir]").forEach((b) => b.addEventListener("click", async () => {
      const o = objetivos.find((x) => x.id === Number(b.dataset.excluir));
      const ok = await confirmar({
        titulo: `Excluir ${esc(o.nome)}?`,
        mensagem: "O objetivo e o histórico de aportes somem. As despesas dos aportes continuam nos lançamentos, porque o dinheiro saiu da conta.",
      });
      if (!ok) return;
      try { await python.del(`/objetivos/${o.id}`); avisar("Objetivo excluído."); ctx.recarregar(); } catch (e) { avisar(e.message, "erro"); }
    }));

    el.querySelectorAll("[data-excluir-aporte]").forEach((b) => b.addEventListener("click", async () => {
      const a = aportes.find((x) => x.id === Number(b.dataset.excluirAporte));
      const ok = await confirmar({
        titulo: "Desfazer aporte?",
        mensagem: `${reais(a.valor)} saem de ${esc(nomeObjetivo[a.id_objetivo])} e a despesa de ${dataBR(a.data)} é apagada.`,
        botao: "Desfazer aporte",
      });
      if (!ok) return;
      try { await python.del(`/aportes/${a.id}`); avisar("Aporte desfeito."); ctx.recarregar(); } catch (e) { avisar(e.message, "erro"); }
    }));
  },
};

async function formularioObjetivo(ctx, objetivo = null) {
  const salvo = await abrirFormulario({
    titulo: objetivo ? `Editar ${esc(objetivo.nome)}` : "Novo objetivo",
    botao: objetivo ? "Salvar alterações" : "Criar objetivo",
    campos: `
      ${campoTexto("nome", "Nome", { valor: objetivo?.nome || "", max: 50, placeholder: "Ex.: Reserva de emergência" })}
      <div class="campos-lado">
        ${campoDinheiro("valor_alvo", "Meta", { valor: objetivo?.valor_alvo ?? null })}
        ${campoDinheiro("valor_inicial", "Já tenho guardado", { valor: objetivo?.valor_inicial ?? null, obrigatorio: false })}
      </div>`,
    async aoEnviar(d) {
      if (!d.nome) throw new Error("Dê um nome ao objetivo.");
      exigirValor(d.valor_alvo, "a meta");
      if (d.valor_inicial !== null && (Number.isNaN(d.valor_inicial) || d.valor_inicial < 0)) throw new Error("O valor guardado não pode ser negativo.");
      const corpo = { nome: d.nome, valor_alvo: d.valor_alvo, valor_inicial: d.valor_inicial };
      return objetivo ? python.put(`/objetivos/${objetivo.id}`, corpo) : python.post("/objetivos/", corpo);
    },
  });
  if (salvo) { avisar(objetivo ? "Objetivo atualizado." : "Objetivo criado."); ctx.recarregar(); }
}

async function formularioAporte(ctx, objetivos, aporte = null, idObjetivo = null) {
  const salvo = await abrirFormulario({
    titulo: aporte ? "Editar aporte" : "Novo aporte",
    descricao: aporte ? "" : "O valor sai da conta como despesa (categoria Investimentos) e entra no objetivo.",
    botao: aporte ? "Salvar alterações" : "Aportar",
    campos: `
      ${aporte ? "" : campoSelecao("id_objetivo", "Objetivo", objetivos.map((o) => ({ valor: o.id, texto: o.nome })), { valor: idObjetivo ?? "" })}
      <div class="campos-lado">
        ${campoDinheiro("valor", "Valor", { valor: aporte?.valor ?? null })}
        ${campoData("data", "Data", { valor: aporte?.data || hojeISO() })}
      </div>`,
    async aoEnviar(d) {
      exigirValor(d.valor);
      if (!d.data) throw new Error("Informe a data.");
      if (aporte) return python.put(`/aportes/${aporte.id}`, { valor: d.valor, data: d.data });
      return python.post("/aportes/", { valor: d.valor, data: d.data, id_objetivo: Number(d.id_objetivo) });
    },
  });
  if (salvo) { avisar(aporte ? "Aporte atualizado." : "Aporte registrado."); ctx.recarregar(); }
}
