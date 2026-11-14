// Assinaturas. Os dados desta tela vêm da API JAVA (Spring Boot, porta 8081):
//   GET/POST/PUT/DELETE /assinaturas, GET /assinaturas/resumo, POST /assinaturas/lancamentos
// Cartões e categorias (para os formulários) vêm da API Python.
import { java, python } from "../api.js";
import { icone } from "../icones.js";
import {
  abrirFormulario, avisar, campoData, campoDinheiro, campoMarcar, campoSegmentado, campoSelecao, campoTexto,
  confirmar, erroDeCarga, exigirValor, seloApi, vazio,
} from "../ui.js";
import { cls, dataBR, dataCurta, esc, hojeISO, nomeDoMes, reais } from "../util.js";

export default {
  async render(el, ctx) {
    const [cartoes, categorias] = await Promise.all([python.get("/cartoes/"), python.get("/categorias/")]);
    let assinaturas, resumo;
    try {
      [assinaturas, resumo] = await Promise.all([java.get("/assinaturas"), java.get("/assinaturas/resumo", { dias: 30 })]);
    } catch (e) {
      if (!ctx.aindaAtual()) return;
      el.innerHTML = `${erroDeCarga(e.message)}
        <p class="nota">As assinaturas ficam na API Java. Confira se o container <code>finflow_api_java</code> está rodando
        (<code>docker compose ps</code>) e veja os logs com <code>docker compose logs api-java</code>.</p>`;
      return;
    }
    if (!ctx.aindaAtual()) return;

    const nomeCartao = Object.fromEntries(cartoes.map((c) => [c.id, c.nome]));
    const cobrancaNoMes = (a) => a.ativa && cobraEm(a, ctx.mes, ctx.ano);
    const doMes = assinaturas.filter(cobrancaNoMes);

    el.innerHTML = `
      <div class="barra-acoes">
        <p class="barra-acoes-texto">Serviços que cobram todo mês ou todo ano. ${seloApi("java")}</p>
        <div class="grupo-botoes">
          <button class="botao botao-secundario" data-acao="lancar" ${doMes.length ? "" : "disabled"}>${icone("raio")}Lançar cobranças de ${nomeDoMes(ctx.mes)}</button>
          <button class="botao botao-primario" data-acao="nova">${icone("mais")}Nova assinatura</button>
        </div>
      </div>

      ${assinaturas.length ? `
        <section class="planilha resumo">
          <div class="resumo-celula"><span class="resumo-rotulo">Ativas</span><span class="resumo-valor">${resumo.quantidade_ativas}</span></div>
          <div class="resumo-celula"><span class="resumo-rotulo">Custo por mês</span><span class="resumo-valor">${reais(resumo.custo_mensal)}</span></div>
          <div class="resumo-celula"><span class="resumo-rotulo">Custo por ano</span><span class="resumo-valor">${reais(resumo.custo_anual)}</span></div>
          <div class="resumo-celula"><span class="resumo-rotulo">Cobram em ${nomeDoMes(ctx.mes)}</span><span class="resumo-valor">${reais(doMes.reduce((s, a) => s + a.valor, 0))}</span></div>
        </section>

        <div class="grade-painel grade-assinaturas">
          <section class="planilha">
            <div class="rolagem">
              <table class="tabela">
                <thead><tr>
                  <th scope="col">Serviço</th><th scope="col" class="num">Valor</th><th scope="col">Cobrança</th>
                  <th scope="col">Próxima</th><th scope="col">Forma</th><th scope="col" class="num">Por mês</th>
                  <th scope="col" class="col-acoes"><span class="sr">Ações</span></th>
                </tr></thead>
                <tbody>
                  ${assinaturas.map((a) => `
                    <tr class="${cls(!a.ativa && "inativa")}">
                      <td>${esc(a.nome)}${a.ativa ? "" : ' <span class="etiqueta">pausada</span>'}</td>
                      <td class="num">${reais(a.valor)}</td>
                      <td class="suave">${descricaoCobranca(a)}</td>
                      <td>${a.proxima_cobranca ? dataBR(a.proxima_cobranca) : "—"}</td>
                      <td class="suave">${a.id_cartao ? esc(nomeCartao[a.id_cartao] || "Cartão") : "Conta"}</td>
                      <td class="num">${reais(a.custo_mensal)}</td>
                      <td class="col-acoes">
                        <button class="botao-icone" data-alternar="${a.id}" aria-label="${a.ativa ? "Pausar" : "Reativar"}" title="${a.ativa ? "Pausar" : "Reativar"}">${icone(a.ativa ? "pausar" : "tocar")}</button>
                        <button class="botao-icone" data-editar="${a.id}" aria-label="Editar">${icone("editar")}</button>
                        <button class="botao-icone" data-excluir="${a.id}" aria-label="Excluir">${icone("lixeira")}</button>
                      </td>
                    </tr>`).join("")}
                </tbody>
                <tfoot><tr class="total"><td colspan="5">Total das ativas por mês</td><td class="num">${reais(resumo.custo_mensal)}</td><td></td></tr></tfoot>
              </table>
            </div>
          </section>

          <section class="planilha">
            <header class="planilha-topo"><h2>Próximos 30 dias</h2></header>
            ${resumo.proximas_cobrancas.length ? `
              <ol class="agenda">
                ${resumo.proximas_cobrancas.map((c) => `
                  <li>
                    <span class="agenda-dia">${dataCurta(c.data)}</span>
                    <span class="agenda-nome">${esc(c.nome)}</span>
                    <span class="num">${reais(c.valor)}</span>
                  </li>`).join("")}
              </ol>` : `<p class="planilha-vazia">Nenhuma cobrança nos próximos 30 dias.</p>`}
            <p class="planilha-rodape">“Lançar cobranças” cria as despesas do mês nos lançamentos e nas faturas. Pode clicar de novo sem medo: nada é lançado duas vezes.</p>
          </section>
        </div>` : `
        <section class="planilha">${vazio({
          titulo: "Nenhuma assinatura cadastrada",
          texto: "Cadastre streaming, música, academia e outros serviços para ver quanto eles custam por mês e por ano.",
          botao: "Nova assinatura", acao: "nova",
        })}</section>`}`;

    // ---------- Ações ----------
    const abrir = (a) => formularioAssinatura({ ctx, cartoes, categorias, assinatura: a });
    el.querySelectorAll('[data-acao="nova"]').forEach((b) => b.addEventListener("click", () => abrir(null)));
    el.querySelectorAll("[data-editar]").forEach((b) =>
      b.addEventListener("click", () => abrir(assinaturas.find((a) => a.id === Number(b.dataset.editar)))));

    el.querySelectorAll("[data-alternar]").forEach((b) => b.addEventListener("click", async () => {
      const a = assinaturas.find((x) => x.id === Number(b.dataset.alternar));
      try {
        await java.put(`/assinaturas/${a.id}`, { ...corpoDe(a), ativa: !a.ativa });
        avisar(a.ativa ? `${a.nome} pausada.` : `${a.nome} reativada.`);
        ctx.recarregar();
      } catch (e) { avisar(e.message, "erro"); }
    }));

    el.querySelectorAll("[data-excluir]").forEach((b) => b.addEventListener("click", async () => {
      const a = assinaturas.find((x) => x.id === Number(b.dataset.excluir));
      const ok = await confirmar({
        titulo: `Excluir ${esc(a.nome)}?`,
        mensagem: "As cobranças já lançadas continuam nos lançamentos. Para só parar de contar, use pausar.",
      });
      if (!ok) return;
      try {
        await java.del(`/assinaturas/${a.id}`);
        avisar("Assinatura excluída.");
        ctx.recarregar();
      } catch (e) { avisar(e.message, "erro"); }
    }));

    const lancar = el.querySelector('[data-acao="lancar"]');
    if (lancar) lancar.addEventListener("click", async () => {
      lancar.disabled = true;
      try {
        const r = await java.post("/assinaturas/lancamentos", undefined, { mes: ctx.mes, ano: ctx.ano });
        const n = r.lancadas.length;
        if (n) avisar(`${n} ${n === 1 ? "cobrança lançada" : "cobranças lançadas"} como despesa em ${nomeDoMes(ctx.mes)}.`);
        else avisar(`As cobranças de ${nomeDoMes(ctx.mes)} já estavam lançadas.`, "info");
      } catch (e) {
        avisar(e.message, "erro");
      } finally {
        lancar.disabled = false;
      }
    });
  },
};

// Mesmas regras do CalendarioCobranca.java, só para exibir na tela
function cobraEm(a, mes, ano) {
  const [anoInicio, mesInicio] = a.data_inicio.split("-").map(Number);
  if (ano * 12 + mes < anoInicio * 12 + mesInicio) return false;
  return a.periodicidade === "MENSAL" || mes === mesInicio;
}

function descricaoCobranca(a) {
  const [, mes, dia] = a.data_inicio.split("-").map(Number);
  return a.periodicidade === "ANUAL" ? `Todo ano, ${dia} de ${nomeDoMes(mes)}` : `Todo mês, dia ${dia}`;
}

const corpoDe = (a) => ({
  nome: a.nome, valor: a.valor, periodicidade: a.periodicidade, data_inicio: a.data_inicio,
  id_cartao: a.id_cartao, id_categoria: a.id_categoria, ativa: a.ativa,
});

async function formularioAssinatura({ ctx, cartoes, categorias, assinatura }) {
  const a = assinatura || { periodicidade: "MENSAL", data_inicio: hojeISO(), ativa: true, id_cartao: null, id_categoria: null };
  const salvo = await abrirFormulario({
    titulo: assinatura ? `Editar ${esc(assinatura.nome)}` : "Nova assinatura",
    botao: assinatura ? "Salvar alterações" : "Adicionar assinatura",
    campos: `
      ${campoTexto("nome", "Serviço", { valor: a.nome || "", max: 60, placeholder: "Ex.: Netflix" })}
      ${campoSegmentado("periodicidade", "Cobrança", [{ valor: "MENSAL", texto: "Mensal" }, { valor: "ANUAL", texto: "Anual" }], a.periodicidade)}
      <div class="campos-lado">
        ${campoDinheiro("valor", "Valor de cada cobrança", { valor: assinatura ? a.valor : null })}
        ${campoData("data_inicio", "Primeira cobrança", { valor: a.data_inicio })}
      </div>
      <p class="campo-ajuda">O dia da primeira cobrança se repete todo mês (ou todo ano, no mesmo mês).</p>
      ${campoSelecao("id_cartao", "Forma de pagamento",
        [{ valor: "", texto: "Conta (pix, débito)" }, ...cartoes.map((c) => ({ valor: c.id, texto: `Cartão ${c.nome}` }))],
        { valor: a.id_cartao ?? "" })}
      ${campoSelecao("id_categoria", "Categoria", categorias.map((c) => ({ valor: c.id, texto: c.nome })),
        { valor: a.id_categoria ?? "", vazio: "Assinaturas (padrão)" })}
      ${campoMarcar("ativa", "Ativa (entra no resumo e nos lançamentos)", a.ativa)}`,
    async aoEnviar(d) {
      if (!d.nome) throw new Error("Informe o nome do serviço.");
      exigirValor(d.valor);
      if (!d.data_inicio) throw new Error("Informe a data da primeira cobrança.");
      const corpo = {
        nome: d.nome,
        valor: d.valor,
        periodicidade: d.periodicidade,
        data_inicio: d.data_inicio,
        id_cartao: d.id_cartao ? Number(d.id_cartao) : null,
        id_categoria: d.id_categoria ? Number(d.id_categoria) : null,
        ativa: d.ativa,
      };
      return assinatura ? java.put(`/assinaturas/${assinatura.id}`, corpo) : java.post("/assinaturas", corpo);
    },
  });
  if (salvo) { avisar(assinatura ? "Assinatura atualizada." : "Assinatura adicionada."); ctx.recarregar(); }
}
