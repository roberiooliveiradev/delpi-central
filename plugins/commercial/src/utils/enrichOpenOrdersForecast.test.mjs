#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  enrichOpenOrdersWithOpForecast,
  lineHasAllocatedOp,
  resolveOpenOrderOpDetailItem,
} from "./enrichOpenOrdersForecast.ts";
import { getLineOpForecast } from "./opAllocation.ts";

const baseLine = {
  nome_cliente: "ACME",
  tipo_entidade: "CLIENTE",
  tipo_pedido: "N",
  pedido_cliente: "",
  filial: "01",
  pedido: "102723",
  linha: "03",
  produto: "90264231",
  codigo_cliente: "",
  codigo_cadastro: "C001",
  loja_cadastro: "01",
  quantidade: 10,
  entregue: 0,
  saldo: 10,
  data_despacho: null,
  data_entrega: "2026-07-31",
  no_estoque: 0,
  preco_venda: 10,
  valor_aberto: 100,
};

const opsData = {
  items: [
    {
      filial: "01",
      numero_op: "24655301001",
      produto: "90264231",
      descricao_produto: "Produto",
      tipo_produto: "PA",
      quantidade_op: 10,
      quantidade_produzida: 0,
      saldo_op: 10,
      data_emissao_op: "2026-01-10",
      data_inicio_prevista_op: "2026-01-15",
      data_fim_prevista_op: "2026-07-20",
      armazem: "01",
      observacao_op: "",
    },
  ],
  resumo: [],
};

describe("enrichOpenOrdersWithOpForecast", () => {
  it("sem OPs a linha fica sem opsUtilizadas (como o detalhe via API crua)", () => {
    const [line] = enrichOpenOrdersWithOpForecast([{ ...baseLine }], null);
    assert.equal(getLineOpForecast(line).opsUtilizadas.length, 0);
    assert.equal(lineHasAllocatedOp(line, "24655301001"), false);
  });

  it("com ops-abertas aloca a OP e resolve o detalhe da rota", () => {
    const matched = resolveOpenOrderOpDetailItem([{ ...baseLine }], opsData, {
      filial: "01",
      pedido: "102723",
      linha: "3",
      productionOrder: "24655301001",
    });
    assert.ok(matched);
    assert.equal(matched.linha, "03");
    assert.equal(lineHasAllocatedOp(matched, "24655301001"), true);
    assert.equal(matched.previsao_op?.opsUtilizadas[0]?.numero_op, "24655301001");
  });

  it("retorna null quando a OP não cobre a linha", () => {
    const matched = resolveOpenOrderOpDetailItem([{ ...baseLine }], opsData, {
      filial: "01",
      pedido: "102723",
      linha: "03",
      productionOrder: "99999999999",
    });
    assert.equal(matched, null);
  });
});
