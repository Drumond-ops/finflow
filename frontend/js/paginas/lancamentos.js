// Lançamentos (receitas e despesas) do mês. API Python: /transacoes, /categorias, /cartoes.
import { python } from "../api.js";
import { icone } from "../icones.js";
import {
  abrirFormulario, avisar, campoData, campoDinheiro, campoSegmentado, campoSelecao, campoTexto,
  confirmar, exigirValor, vazio,
} from "../ui.js";
import { dataBR, dataPadraoDoMes, esc, faturaDaCompra, nomeDoMes, paraBusca, reais, somar } from "../util.js";

const filtros = { tipo: "", categoria: "", forma: "", busca: "" };

// Ordem da tabela. coluna null = a ordem em que a API devolve. Fica guardada ao trocar de mês, como os filtros.
const ordem = { coluna: null, crescente: true };
const COLUNAS = [
  { chave: "data", nome: "Data", classe: "col-data" },
  { chave: "descricao", nome: "Descrição" },
  { chave: "categoria", nome: "Categoria" },
  { chave: "forma", nome: "Forma" },
  { chave: "valor", nome: "Valor", classe: "num" },
];

/** Cabeçalho que ordena: um botão dentro do <th> (funciona no teclado) e aria-sort para o leitor de tela. */
function cabecalho({ chave, nome, classe = "" }) {
  const ativa = ordem.coluna === chave;
  const sentido = ordem.crescente ? "ascending" : "descending";
  return `<th scope="col" class="${classe}"${ativa ? ` aria-sort="${sentido}"` : ""}>
    <button type="button" class="ordenar" data-ordenar="${chave}" title="Ordenar por ${nome.toLowerCase()}">${nome}${
      ativa ? `<span class="ordenar-seta" aria-hidden="true">${ordem.crescente ? "↑" : "↓"}</span>` : ""}</button></th>`;
}

export default {
  async render(el, ctx) {
    const [transacoes, categorias, cartoes] = await Promise.all([
      python.get("/transacoes/", { mes: ctx.mes, ano: ctx.ano }),
      python.get("/categorias/"),
      python.get("/cartoes/"),
    ]);
    if (!ctx.aindaAtual()) return;

    const nomeCategoria = Object.fromEntries(categorias.map((c) => [c.id, c.nome]));
    const nomeCartao = Object.fromEntries(cartoes.map((c) => [c.id, c.nome]));

    // O que comparar em cada coluna. Despesa conta como negativa, igual ao que a tabela mostra.
    const chaveDe = {
      data: (t) => t.data, // "AAAA-MM-DD" já ordena certo como texto
      descricao: (t) => t.descricao || (t.tipo === "receita" ? "Receita" : "Despesa"),
      categoria: (t) => nomeCategoria[t.id_categoria] || "",
      forma: (t) => (t.id_cartao ? nomeCartao[t.id_cartao] || "Cartão" : "Conta"),
      valor: (t) => (t.tipo === "receita" ? t.valor : -t.valor),
    };
    const comparar = (a, b) => (typeof a === "number" ? a - b : a.localeCompare(b, "pt-BR", { sensitivity: "base" }));

    el.innerHTML = `
      <div class="barra-acoes">
        <div class="filtros" role="search">
          <label class="busca">${icone("busca")}<input type="search" data-filtro="busca" placeholder="Buscar descrição" value="${esc(filtros.busca)}" aria-label="Buscar pela descrição"></label>
          <select data-filtro="tipo" aria-label="Tipo">
            <option value="">Receitas e despesas</option>
            <option value="receita">Só receitas</option>
            <option value="despesa">Só despesas</option>
          </select>
          <select data-filtro="categoria" aria-label="Categoria">
            <option value="">Todas as categorias</option>
            ${categorias.map((c) => `<option value="${c.id}">${esc(c.nome)}</option>`).join("")}
          </select>
          <select data-filtro="forma" aria-label="Forma de pagamento">
            <option value="">Conta e cartões</option>
            <option value="conta">Só conta (pix/débito)</option>
            ${cartoes.map((c) => `<option value="${c.id}">${esc(c.nome)}</option>`).join("")}
          </select>
        </div>
        <button class="botao botao-primario" data-acao="nova">${icone("mais")}Nova transação</button>
      </div>
      <section class="planilha" data-tabela></section>`;

    el.querySelectorAll("[data-filtro]").forEach((campo) => {
      campo.value = filtros[campo.dataset.filtro];
      campo.addEventListener("input", () => {
        filtros[campo.dataset.filtro] = campo.value;
        desenhar();
      });
    });

    const abrir = (t) => abrirTransacao({ ctx, categorias, cartoes, transacao: t });

    const limparFiltros = () => {
      Object.keys(filtros).forEach((k) => { filtros[k] = ""; });
      el.querySelectorAll("[data-filtro]").forEach((campo) => { campo.value = ""; });
      desenhar();
      el.querySelector('[data-filtro="busca"]').focus(); // o botão some; o foco não pode se perder
    };

    let listaAtual = transacoes; // o que está na tela, já filtrado (é o que o CSV exporta)
    const exportarCsv = () => {
      const csv = paraCsv(listaAtual, nomeCategoria, nomeCartao);
      const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
      const link = Object.assign(document.createElement("a"), { href: url, download: `finflow_lancamentos_${String(ctx.mes).padStart(2, "0")}_${ctx.ano}.csv` });
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
      avisar("CSV baixado.");
    };

    function desenhar() {
      const busca = paraBusca(filtros.busca);
      const lista = transacoes.filter((t) =>
        (!filtros.tipo || t.tipo === filtros.tipo)
        && (!filtros.categoria || String(t.id_categoria) === filtros.categoria)
        && (!filtros.forma || (filtros.forma === "conta" ? t.id_cartao === null : String(t.id_cartao) === filtros.forma))
        && (!busca || paraBusca(t.descricao).includes(busca) || paraBusca(nomeCategoria[t.id_categoria]).includes(busca)));

      listaAtual = lista;
      const filtrado = Object.values(filtros).some(Boolean);

      const alvo = el.querySelector("[data-tabela]");
      if (!transacoes.length) {
        alvo.innerHTML = vazio({
          titulo: `Nenhum lançamento em ${nomeDoMes(ctx.mes)}`,
          texto: "Registre o salário, as compras do mês e as contas pagas para ver o saldo e os gráficos.",
          botao: "Nova transação", acao: "nova",
        });
        return;
      }

      if (ordem.coluna) {
        const chave = chaveDe[ordem.coluna];
        lista.sort((a, b) => comparar(chave(a), chave(b)) * (ordem.crescente ? 1 : -1)); // sort é estável: empates mantêm a ordem da API
      }

      const receitas = somar(lista.filter((t) => t.tipo === "receita"), "valor");
      const despesas = somar(lista.filter((t) => t.tipo === "despesa"), "valor");

      alvo.innerHTML = `
        <header class="planilha-topo planilha-topo-fino">
          <span class="planilha-meta">${filtrado
            ? `${lista.length} de ${transacoes.length} lançamentos`
            : `${transacoes.length} ${transacoes.length === 1 ? "lançamento" : "lançamentos"}`}</span>
          <div class="grupo-botoes">
            ${filtrado ? `<button class="botao botao-secundario botao-pequeno" data-limpar-filtros>Limpar filtros</button>` : ""}
            <button class="botao botao-secundario botao-pequeno" data-exportar ${lista.length ? "" : "disabled"}>${icone("baixar")}Exportar CSV</button>
          </div>
        </header>
        <div class="rolagem">
          <table class="tabela">
            <thead>
              <tr>
                ${COLUNAS.map(cabecalho).join("")}
                <th scope="col" class="col-acoes"><span class="sr">Ações</span></th>
              </tr>
            </thead>
            <tbody>
              ${lista.map((t) => `
                <tr>
                  <td class="col-data">${dataBR(t.data)}</td>
                  <td>${esc(t.descricao || (t.tipo === "receita" ? "Receita" : "Despesa"))}${seloOrigem(t)}</td>
                  <td>${esc(nomeCategoria[t.id_categoria] || "—")}</td>
                  <td class="suave">${t.id_cartao ? esc(nomeCartao[t.id_cartao] || "Cartão") : "Conta"}</td>
                  <td class="num ${t.tipo === "receita" ? "positivo" : ""}">${t.tipo === "receita" ? "" : "−"}${reais(t.valor)}</td>
                  <td class="col-acoes">
                    ${t.origem === "aporte"
                      ? `<span class="dica-linha" title="Gerada por um aporte. Edite pelo objetivo.">pelo objetivo</span>`
                      : `<button class="botao-icone" data-editar="${t.id}" aria-label="Editar ${esc(t.descricao || nomeCategoria[t.id_categoria] || "lançamento")} de ${dataBR(t.data)}">${icone("editar")}</button>
                         <button class="botao-icone" data-excluir="${t.id}" aria-label="Excluir ${esc(t.descricao || nomeCategoria[t.id_categoria] || "lançamento")} de ${dataBR(t.data)}">${icone("lixeira")}</button>`}
                  </td>
                </tr>`).join("") || `<tr><td colspan="6" class="tabela-sem-resultado">Nenhum lançamento com esses filtros.</td></tr>`}
            </tbody>
            <tfoot>
              <tr><td colspan="4">Receitas</td><td class="num positivo">${reais(receitas)}</td><td></td></tr>
              <tr><td colspan="4">Despesas</td><td class="num">−${reais(despesas)}</td><td></td></tr>
              <tr class="total"><td colspan="4">Saldo ${lista.length !== transacoes.length ? "(filtrado)" : ""}</td>
                <td class="num ${receitas - despesas < 0 ? "negativo" : ""}">${reais(receitas - despesas)}</td><td></td></tr>
            </tfoot>
          </table>
        </div>`;

      alvo.querySelectorAll("[data-editar]").forEach((b) =>
        b.addEventListener("click", () => abrir(transacoes.find((t) => t.id === Number(b.dataset.editar)))));
      alvo.querySelectorAll("[data-excluir]").forEach((b) =>
        b.addEventListener("click", async () => {
          const t = transacoes.find((x) => x.id === Number(b.dataset.excluir));
          const ok = await confirmar({
            titulo: "Excluir lançamento?",
            mensagem: `“${esc(t.descricao || nomeCategoria[t.id_categoria])}” de ${reais(t.valor)} em ${dataBR(t.data)} será removido.`,
          });
          if (!ok) return;
          try {
            await python.del(`/transacoes/${t.id}`);
            avisar("Lançamento excluído.");
            ctx.recarregar();
          } catch (e) { avisar(e.message, "erro"); }
        }));
      alvo.querySelectorAll("[data-ordenar]").forEach((b) => b.addEventListener("click", () => {
        const coluna = b.dataset.ordenar;
        ordem.crescente = ordem.coluna === coluna ? !ordem.crescente : true;
        ordem.coluna = coluna;
        desenhar();
        el.querySelector(`[data-ordenar="${coluna}"]`).focus(); // a tabela foi redesenhada: o foco volta ao mesmo cabeçalho
      }));
    }

    // Um ouvinte só para a página: os botões da tabela são redesenhados a cada filtro
    el.addEventListener("click", (e) => {
      if (e.target.closest('[data-acao="nova"]')) abrir(null);
      else if (e.target.closest("[data-limpar-filtros]")) limparFiltros();
      else if (e.target.closest("[data-exportar]")) exportarCsv();
    });
    desenhar();
  },
};

/**
 * CSV no padrão do Excel em português: separador ";", vírgula decimal e BOM para os acentos.
 * Texto que começa com = + - @ ganha um ' na frente para a planilha não executar como fórmula.
 */
export function paraCsv(lista, nomeCategoria, nomeCartao) {
  const celula = (valor, texto = true) => {
    let v = String(valor ?? "");
    if (texto && /^[=+\-@\t\r]/.test(v)) v = `'${v}`;
    return /[;"\n\r]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
  };
  const valor = (c) => `${Math.floor(c / 100)},${String(c % 100).padStart(2, "0")}`;
  const linhas = lista.map((t) => [
    celula(dataBR(t.data), false),
    celula(t.descricao || ""),
    celula(nomeCategoria[t.id_categoria] || ""),
    celula(t.id_cartao ? nomeCartao[t.id_cartao] || "Cartão" : "Conta"),
    t.tipo === "receita" ? "Receita" : "Despesa",
    valor(t.valor),
  ].join(";"));
  return "﻿" + ["Data;Descrição;Categoria;Forma;Tipo;Valor", ...linhas].join("\r\n") + "\r\n";
}

function seloOrigem(t) {
  if (t.origem === "aporte") return ` <span class="etiqueta">aporte</span>`;
  if (t.origem === "assinatura") return ` <span class="etiqueta etiqueta-java" title="Lançada pela API Java">assinatura</span>`;
  return "";
}

/** Janela de nova transação / edição. Também usada pelo Painel. */
export async function abrirTransacao({ ctx, categorias, cartoes, transacao = null }) {
  const t = transacao || { tipo: "despesa", data: dataPadraoDoMes(ctx.mes, ctx.ano), id_cartao: null, id_categoria: null };
  const padraoCategoria = t.id_categoria ?? categorias.find((c) => c.nome === (t.tipo === "receita" ? "Salário" : "Mercado"))?.id;

  const salvo = await abrirFormulario({
    titulo: transacao ? "Editar lançamento" : "Nova transação",
    botao: transacao ? "Salvar alterações" : "Adicionar",
    campos: `
      ${campoSegmentado("tipo", "Tipo", [{ valor: "despesa", texto: "Despesa" }, { valor: "receita", texto: "Receita" }], t.tipo)}
      <div class="campos-lado">
        ${campoDinheiro("valor", "Valor", { valor: transacao ? t.valor : null })}
        ${campoData("data", "Data", { valor: t.data })}
      </div>
      ${campoTexto("descricao", "Descrição", { valor: t.descricao || "", obrigatorio: false, placeholder: "Ex.: compras da semana" })}
      ${campoSelecao("id_categoria", "Categoria", categorias.map((c) => ({ valor: c.id, texto: c.nome })), { valor: padraoCategoria })}
      ${campoSelecao("forma", "Forma de pagamento",
        [{ valor: "", texto: "Conta (pix, débito, dinheiro)" }, ...cartoes.map((c) => ({ valor: c.id, texto: `Cartão ${c.nome}` }))],
        { valor: t.id_cartao ?? "", ajuda: " " })}`,
    aoAbrir(form) {
      const forma = form.elements.forma;
      const ajuda = form.querySelector('[data-ajuda="forma"]');
      const atualizar = () => {
        const receita = form.querySelector('input[name="tipo"]:checked').value === "receita";
        forma.disabled = receita;
        if (receita) forma.value = "";
        const cartao = cartoes.find((c) => String(c.id) === forma.value);
        if (cartao && form.elements.data.value) {
          const f = faturaDaCompra(cartao, form.elements.data.value);
          ajuda.textContent = `Entra na fatura que vence em ${nomeDoMes(f.mes)} de ${f.ano}${cartao.dia_vencimento ? ` (dia ${cartao.dia_vencimento})` : ""}.`;
        } else {
          ajuda.textContent = receita ? "Receitas entram na conta." : "Sai direto da conta.";
        }
      };
      form.addEventListener("change", atualizar);
      form.elements.data.addEventListener("input", atualizar);
      atualizar();
    },
    async aoEnviar(d) {
      exigirValor(d.valor);
      if (!d.data) throw new Error("Informe a data.");
      const corpo = {
        tipo: d.tipo,
        valor: d.valor,
        data: d.data,
        descricao: d.descricao || null,
        id_categoria: Number(d.id_categoria),
        id_cartao: d.tipo === "receita" || !d.forma ? null : Number(d.forma),
      };
      if (transacao) await python.put(`/transacoes/${transacao.id}`, corpo);
      else await python.post("/transacoes/", corpo);
      return corpo;
    },
  });

  if (salvo) {
    avisar(transacao ? "Lançamento atualizado." : "Transação adicionada.");
    const [ano, mes] = salvo.data.split("-").map(Number);
    if (!transacao && (mes !== ctx.mes || ano !== ctx.ano)) {
      avisar(`Ela ficou em ${nomeDoMes(mes)} de ${ano}.`, "info");
    }
    ctx.recarregar();
  }
}

