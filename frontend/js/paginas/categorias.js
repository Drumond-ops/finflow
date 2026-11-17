// Categorias. API Python: /categorias (e /transacoes para contar o uso).
import { python } from "../api.js";
import { icone } from "../icones.js";
import { abrirFormulario, avisar, campoSelecao, campoTexto, confirmar } from "../ui.js";
import { esc, nomeDoMes, reais } from "../util.js";

export default {
  async render(el, ctx) {
    const [categorias, transacoes] = await Promise.all([
      python.get("/categorias/"),
      python.get("/transacoes/", { mes: ctx.mes, ano: ctx.ano }),
    ]);
    if (!ctx.aindaAtual()) return;

    const uso = {};
    transacoes.forEach((t) => {
      uso[t.id_categoria] ??= { qtd: 0, total: 0 };
      uso[t.id_categoria].qtd += 1;
      uso[t.id_categoria].total += t.tipo === "despesa" ? -t.valor : t.valor;
    });

    el.innerHTML = `
      <div class="barra-acoes">
        <p class="barra-acoes-texto">Use as categorias para agrupar lançamentos, planejar faturas e montar o orçamento.</p>
        <button class="botao botao-primario" data-acao="nova">${icone("mais")}Nova categoria</button>
      </div>
      <section class="planilha planilha-estreita">
        <table class="tabela">
          <thead><tr>
            <th scope="col">Categoria</th><th scope="col" class="num">Lançamentos em ${nomeDoMes(ctx.mes)}</th>
            <th scope="col" class="num">Movimento no mês</th><th scope="col" class="col-acoes"><span class="sr">Ações</span></th>
          </tr></thead>
          <tbody>
            ${categorias.map((c) => `
              <tr>
                <td>${esc(c.nome)}</td>
                <td class="num suave">${uso[c.id]?.qtd || "—"}</td>
                <td class="num ${uso[c.id]?.total > 0 ? "positivo" : ""}">${uso[c.id] ? reais(uso[c.id].total) : "—"}</td>
                <td class="col-acoes">
                  <button class="botao-icone" data-editar="${c.id}" aria-label="Renomear ${esc(c.nome)}">${icone("editar")}</button>
                  <button class="botao-icone" data-excluir="${c.id}" aria-label="Excluir ${esc(c.nome)}">${icone("lixeira")}</button>
                </td>
              </tr>`).join("")}
          </tbody>
        </table>
      </section>`;

    const formulario = async (categoria = null) => {
      const salvo = await abrirFormulario({
        titulo: categoria ? `Renomear ${categoria.nome}` : "Nova categoria",
        botao: categoria ? "Salvar" : "Criar categoria",
        campos: campoTexto("nome", "Nome", { valor: categoria?.nome || "", max: 50, placeholder: "Ex.: Pets" }),
        async aoEnviar(d) {
          if (!d.nome) throw new Error("Dê um nome à categoria.");
          return categoria ? python.put(`/categorias/${categoria.id}`, { nome: d.nome }) : python.post("/categorias/", { nome: d.nome });
        },
      });
      if (salvo) { avisar(categoria ? "Categoria renomeada." : "Categoria criada."); ctx.recarregar(); }
    };

    el.querySelector('[data-acao="nova"]').addEventListener("click", () => formulario());
    el.querySelectorAll("[data-editar]").forEach((b) => b.addEventListener("click", () =>
      formulario(categorias.find((c) => c.id === Number(b.dataset.editar)))));

    el.querySelectorAll("[data-excluir]").forEach((b) => b.addEventListener("click", async () => {
      const categoria = categorias.find((c) => c.id === Number(b.dataset.excluir));
      const ok = await confirmar({ titulo: `Excluir ${categoria.nome}?`, mensagem: "Limites e planejamentos desta categoria também serão removidos." });
      if (!ok) return;
      try {
        await python.del(`/categorias/${categoria.id}`);
        avisar("Categoria excluída.");
        ctx.recarregar();
      } catch (e) {
        if (e.status !== 409) { avisar(e.message, "erro"); return; }
        // Categoria em uso: pergunta para onde mover os lançamentos (a API exige ?mover_para=)
        const destinos = categorias.filter((c) => c.id !== categoria.id);
        const movido = await abrirFormulario({
          titulo: `${categoria.nome} está em uso`,
          descricao: "Escolha para qual categoria mover os lançamentos, limites e planejamentos antes de excluir.",
          botao: "Mover e excluir",
          perigo: true,
          campos: campoSelecao("destino", "Mover para", destinos.map((c) => ({ valor: c.id, texto: c.nome }))),
          async aoEnviar(d) {
            await python.del(`/categorias/${categoria.id}`, { mover_para: d.destino });
          },
        });
        if (movido) { avisar("Lançamentos movidos e categoria excluída."); ctx.recarregar(); }
      }
    }));
  },
};
