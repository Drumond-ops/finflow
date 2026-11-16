// Testes das funções de js/util.js (dinheiro, datas, fatura, busca).
// Rodar na raiz do repositório:  node --test "frontend/testes/*.test.mjs"
// Só precisa do Node 22 ou mais novo; nenhuma biblioteca.
import assert from "node:assert/strict";
import { test } from "node:test";
import {
  dataBR, esc, faturaDaCompra, mesAnterior, mesSeguinte, paraBusca, paraCentavos, reais, reaisSemSimbolo,
} from "../js/util.js";

const semEspacoEspecial = (texto) => texto.replace(/\s/g, " "); // Intl usa espaço não separável depois do "R$"

test("esc protege o HTML", () => {
  assert.equal(esc(`<b>"Café" & 'Cia'</b>`), "&lt;b&gt;&quot;Café&quot; &amp; &#39;Cia&#39;&lt;/b&gt;");
  assert.equal(esc(null), "");
});

test("reais formata centavos", () => {
  assert.equal(semEspacoEspecial(reais(123456)), "R$ 1.234,56");
  assert.equal(semEspacoEspecial(reais(5)), "R$ 0,05");
  assert.equal(reaisSemSimbolo(123456), "1.234,56");
});

test("paraCentavos entende o que a pessoa digita", () => {
  assert.equal(paraCentavos("1.234,56"), 123456);
  assert.equal(paraCentavos("1234,56"), 123456);
  assert.equal(paraCentavos("1234.56"), 123456);
  assert.equal(paraCentavos("R$ 50"), 5000);
  assert.equal(paraCentavos("1.234"), 123400); // ponto como milhar
  assert.equal(paraCentavos("0,1"), 10);
  assert.ok(Number.isNaN(paraCentavos("")));
  assert.ok(Number.isNaN(paraCentavos("abc")));
});

test("datas e meses", () => {
  assert.equal(dataBR("2026-11-05"), "05/11/2026");
  assert.equal(dataBR(null), "—");
  assert.deepEqual(mesAnterior(1, 2026), { mes: 12, ano: 2025 });
  assert.deepEqual(mesSeguinte(12, 2026), { mes: 1, ano: 2027 });
});

// Mesmos exemplos de api-python/ciclo_fatura.py e tests/test_ciclo_fatura.py
test("fatura da compra: fecha dia 3, vence dia 10", () => {
  const cartao = { dia_fechamento: 3, dia_vencimento: 10 };
  assert.deepEqual(faturaDaCompra(cartao, "2026-10-04"), { mes: 11, ano: 2026 });
  assert.deepEqual(faturaDaCompra(cartao, "2026-11-03"), { mes: 11, ano: 2026 }); // no dia do fechamento ainda entra
  assert.deepEqual(faturaDaCompra(cartao, "2026-11-04"), { mes: 12, ano: 2026 });
  assert.deepEqual(faturaDaCompra(cartao, "2026-12-20"), { mes: 1, ano: 2027 }); // virada de ano
});

test("fatura da compra: fecha dia 25, vence dia 5 (fecha no mês anterior)", () => {
  const cartao = { dia_fechamento: 25, dia_vencimento: 5 };
  assert.deepEqual(faturaDaCompra(cartao, "2026-11-25"), { mes: 12, ano: 2026 });
  assert.deepEqual(faturaDaCompra(cartao, "2026-11-26"), { mes: 1, ano: 2027 });
});

test("fatura da compra: dia 31 em fevereiro vira o último dia do mês", () => {
  // Fecha 31 e vence 10: fecha no mês anterior ao vencimento. A fatura de março vai de 01/02 a 28/02.
  const cartao = { dia_fechamento: 31, dia_vencimento: 10 };
  assert.deepEqual(faturaDaCompra(cartao, "2026-02-01"), { mes: 3, ano: 2026 });
  assert.deepEqual(faturaDaCompra(cartao, "2026-02-28"), { mes: 3, ano: 2026 });
  assert.deepEqual(faturaDaCompra(cartao, "2026-03-01"), { mes: 4, ano: 2026 });
});

test("fatura da compra: sem fechamento usa o mês do calendário", () => {
  assert.deepEqual(faturaDaCompra({ dia_fechamento: null, dia_vencimento: null }, "2026-11-30"), { mes: 11, ano: 2026 });
});

test("paraBusca ignora acentos e maiúsculas", () => {
  assert.equal(paraBusca("Café & Cia"), "cafe & cia");
  assert.equal(paraBusca("AÇÚCAR"), "acucar");
  assert.equal(paraBusca(undefined), "");
});
