#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { scoreProposal } from "./resolveProposalForOpenOrder.ts";

const baseItem = {
  nome_cliente: "ACME",
  tipo_entidade: "C",
  tipo_pedido: "N",
  pedido_cliente: "X",
  filial: "01",
  pedido: "000123",
  linha: "01",
  produto: "90AAAA",
  codigo_cliente: "01001",
  codigo_cadastro: "01001",
  loja_cadastro: "01",
  quantidade: 1,
  entregue: 0,
  saldo: 1,
  data_despacho: null,
  data_entrega: null,
  no_estoque: 0,
  preco_venda: 1,
  valor_aberto: 1,
};

describe("scoreProposal OV↔pedido", () => {
  it("prioriza número OV = pedido + filial + cliente", () => {
    const exact = {
      branch: "01",
      proposal_number: "000123",
      revision: "001",
      customer_code: "01001",
      customer_store: "01",
      status_category: "open",
    };
    const weak = {
      branch: "02",
      proposal_number: "999999",
      revision: "001",
      customer_code: "99999",
      customer_store: "01",
      status_category: "lost",
    };
    assert.ok(scoreProposal(exact, baseItem) > scoreProposal(weak, baseItem));
    assert.ok(scoreProposal(exact, baseItem) >= 40);
  });

  it("exige limiar mínimo para match só por filial", () => {
    const onlyBranch = {
      branch: "01",
      proposal_number: "888",
      revision: "001",
    };
    assert.equal(scoreProposal(onlyBranch, baseItem), 40);
  });
});
