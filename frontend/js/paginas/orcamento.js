// Orçamento mensal por categoria. API Python: /orcamentos, /orcamentos/resumo, /orcamentos/copiar.
import { python } from "../api.js";
import { barraDeUso } from "../graficos.js";
import { icone } from "../icones.js";
import { abrirFormulario, avisar, campoDinheiro, campoSelecao, confirmar, exigirValor, vazio } from "../ui.js";
import { esc, mesAnterior, nomeDoMes, porcento, reais } from "../util.js";

const STATUS = { ok: "Dentro do limite", atencao: "Perto do limite", estourado: "Estourou" };

export default {
  async render(el, ctx) {
    const [resumo, categorias] = await Promise.all([
      python.get("/orcamentos/resumo", { mes: ctx.mes, ano: ctx.ano }),
      python.get("/categorias/"),
    ]);
    if (!ctx.aindaAtual()) return;

    const anterior = mesAnterior(ctx.mes, ctx.ano);
    const botaoCopiar = `<button class="botao botao-secundario" data-acao="copiar">${icone("copiar")}Copiar de ${nomeDoMes(anterior.mes)}</button>`;

    if (!resumo.itens.length) {
      el.innerHTML = `
        <section class="planilha">
          ${vazio({
            titulo: `Sem orçamento para ${nomeDoMes(ctx.mes)}`,
            texto: "Defina quanto pode gastar em cada categoria no mês. Contam as despesas da conta e do cartão.",
            botao: "Definir limite", acao: "novo",
          })}
          <div class="vazio-extra">${botaoCopiar}</div>
        </section>`;
    } else {
      el.innerHTML = `
        <div class="barra-acoes">
          <p class="barra-acoes-texto">Limites do mês por categoria, somando conta e cartão pela data da compra.</p>
          <div class="grupo-botoes">${botaoCopiar}<button class="botao botao-primario" data-acao="novo">${icone("mais")}Definir limite</button></div>
        </div>

        <section class="planilha resumo">
          <div class="resumo-celula"><span class="resumo-rotulo">Orçado</span><span class="resumo-valor">${reais(resumo.total_orcado)}</span></div>
          <div class="resumo-celula"><span class="resumo-rotulo">Gasto</span><span class="resumo-valor">${reais(resumo.total_gasto)}</span></div>
          <div class="resumo-celula"><span class="resumo-rotulo">${resumo.saldo < 0 ? "Acima do orçado" : "Ainda disponível"}</span>
            <span class="resumo-valor ${resumo.saldo < 0 ? "negativo" : ""}">${reais(Math.abs(resumo.saldo))}</span></div>
          <div class="resumo-celula"><span class="resumo-rotulo">Gasto sem orçamento</span><span class="resumo-valor suave">${reais(resumo.gasto_fora_do_orcamento)}</span></div>
        </section>

        <section class="planilha">
          <div class="rolagem">
            <table class="tabela">
              <thead><tr>
                <th scope="col">Categoria</th><th scope="col" class="num">Orçado</th><th scope="col" class="num">Gasto</th>
                <th scope="col" class="num">Saldo</th><th scope="col" class="col-uso">Uso</th><th scope="col">Situação</th>
                <th scope="col" class="col-acoes"><span class="sr">Ações</span></th>
              </tr></thead>
              <tbody>
                ${resumo.itens.map((i) => `
                  <tr>
                    <td>${esc(i.nome_categoria)}</td>
                    <td class="num">${reais(i.valor_orcado)}</td>
                    <td class="num">${reais(i.valor_gasto)}</td>
                    <td class="num ${i.saldo < 0 ? "negativo" : ""}">${reais(i.saldo)}</td>
                    <td class="col-uso">${barraDeUso(i.percentual, i.status)}<span class="uso-numero">${porcento(i.percentual)}</span></td>
                    <td><span class="situacao situacao-${i.status}">${STATUS[i.status]}</span></td>
                    <td class="col-acoes">
                      <button class="botao-icone" data-editar="${i.id_orcamento}" aria-label="Editar limite de ${esc(i.nome_categoria)}">${icone("editar")}</button>
                      <button class="botao-icone" data-excluir="${i.id_orcamento}" aria-label="Excluir limite de ${esc(i.nome_categoria)}">${icone("lixeira")}</button>
                    </td>
                  </tr>`).join("")}
              </tbody>
              <tfoot><tr class="total">
                <td>Total</td><td class="num">${reais(resumo.total_orcado)}</td><td class="num">${reais(resumo.total_gasto)}</td>
                <td class="num ${resumo.saldo < 0 ? "negativo" : ""}">${reais(resumo.saldo)}</td>
                <td class="col-uso">${barraDeUso(resumo.percentual, resumo.percentual > 100 ? "estourado" : resumo.percentual >= 80 ? "atencao" : "ok")}<span class="uso-numero">${porcento(resumo.percentual)}</span></td>
                <td></td><td></td>
              </tr></tfoot>
            </table>
          </div>
        </section>`;
    }

    // ---------- Ações ----------
    el.querySelectorAll('[data-acao="novo"]').forEach((b) => b.addEventListener("click", async () => {
      const usadas = new Set(resumo.itens.map((i) => i.id_categoria));
      const livres = categorias.filter((c) => !usadas.has(c.id) && c.nome !== "Salário");
      if (!livres.length) { avisar("Todas as categorias já têm limite neste mês.", "info"); return; }
      const ok = await abrirFormulario({
        titulo: `Limite para ${nomeDoMes(ctx.mes)}`,
        botao: "Salvar limite",
        campos: `
          ${campoSelecao("id_categoria", "Categoria", livres.map((c) => ({ valor: c.id, texto: c.nome })))}
          ${campoDinheiro("valor", "Limite no mês")}`,
        async aoEnviar(d) {
          exigirValor(d.valor, "o limite");
          await python.post("/orcamentos/", { mes: ctx.mes, ano: ctx.ano, valor: d.valor, id_categoria: Number(d.id_categoria) });
        },
      });
      if (ok) { avisar("Limite salvo."); ctx.recarregar(); }
    }));

    el.querySelector('[data-acao="copiar"]').addEventListener("click", async (evento) => {
      const botao = evento.currentTarget;
      botao.disabled = true; // evita copiar duas vezes com clique duplo
      try {
        const copiados = await python.post("/orcamentos/copiar", undefined, {
          de_mes: anterior.mes, de_ano: anterior.ano, para_mes: ctx.mes, para_ano: ctx.ano,
        });
        if (copiados.length) {
          avisar(`${copiados.length} ${copiados.length === 1 ? "limite copiado" : "limites copiados"} de ${nomeDoMes(anterior.mes)}.`);
          ctx.recarregar();
        } else {
          avisar(`Nada para copiar: ${nomeDoMes(anterior.mes)} não tem limites novos para este mês.`, "info");
        }
      } catch (e) { avisar(e.message, "erro"); } finally { botao.disabled = false; }
    });

    el.querySelectorAll("[data-editar]").forEach((b) => b.addEventListener("click", async () => {
      const item = resumo.itens.find((i) => i.id_orcamento === Number(b.dataset.editar));
      const ok = await abrirFormulario({
        titulo: `Limite de ${esc(item.nome_categoria)}`,
        botao: "Salvar",
        campos: campoDinheiro("valor", `Limite em ${nomeDoMes(ctx.mes)}`, { valor: item.valor_orcado }),
        async aoEnviar(d) {
          exigirValor(d.valor, "o limite");
          await python.put(`/orcamentos/${item.id_orcamento}`, { valor: d.valor });
        },
      });
      if (ok) { avisar("Limite atualizado."); ctx.recarregar(); }
    }));

    el.querySelectorAll("[data-excluir]").forEach((b) => b.addEventListener("click", async () => {
      const item = resumo.itens.find((i) => i.id_orcamento === Number(b.dataset.excluir));
      const ok = await confirmar({
        titulo: "Remover limite?",
        mensagem: `${esc(item.nome_categoria)} deixa de ter limite em ${nomeDoMes(ctx.mes)}. Os gastos continuam registrados.`,
        botao: "Remover",
      });
      if (!ok) return;
      try {
        await python.del(`/orcamentos/${item.id_orcamento}`);
        avisar("Limite removido.");
        ctx.recarregar();
      } catch (e) { avisar(e.message, "erro"); }
    }));
  },
};
