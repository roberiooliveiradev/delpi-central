import { describe, expect, it } from "vitest";

import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { resolveLineCoverage } from "./openOrdersLineVisual";

function item(partial: Partial<OpenOrdersTotvsItem>): OpenOrdersTotvsItem {
  return {
    nome_cliente: "",
    tipo_entidade: "",
    tipo_pedido: "",
    pedido_cliente: "",
    filial: "01",
    pedido: "1",
    linha: "01",
    produto: "P",
    codigo_cliente: "",
    codigo_cadastro: "",
    loja_cadastro: "",
    quantidade: 0,
    entregue: 0,
    saldo: 2,
    unidade: "MI",
    data_despacho: null,
    data_entrega: null,
    no_estoque: 1,
    estoque_alocado: 1,
    preco_venda: 0,
    valor_aberto: 0,
    ...partial,
  };
}

describe("resolveLineCoverage", () => {
  it("converts MI quantities in pieces mode for the quantity label", () => {
    const coverage = resolveLineCoverage(item({}), "pieces");
    expect(coverage.ratio).toBe(0.5);
    expect(coverage.quantityLabel).toBe("1.000,000 / 2.000,000 PC");
  });

  it("keeps catalog MI in the quantity label", () => {
    const coverage = resolveLineCoverage(item({}), "catalog");
    expect(coverage.quantityLabel).toBe("1,000 / 2,000 MI");
  });
});
