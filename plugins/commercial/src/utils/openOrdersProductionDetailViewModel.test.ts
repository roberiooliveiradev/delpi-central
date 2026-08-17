import { describe, expect, it } from "vitest";

import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { buildOpenOrdersProductionDetailViewModel } from "./openOrdersProductionDetailViewModel";

function representativeOpenOrder(): OpenOrdersTotvsItem {
  return {
    nome_cliente: "Indústria Exemplo",
    tipo_entidade: "cliente",
    tipo_pedido: "venda",
    pedido_cliente: "PC-42",
    filial: "01",
    pedido: "000123",
    linha: "02",
    produto: "PROD-9000",
    codigo_cliente: "C-10",
    codigo_cadastro: "000010",
    loja_cadastro: "01",
    quantidade: 120,
    entregue: 20,
    saldo: 100,
    data_despacho: "2026-08-12",
    data_entrega: "2026-08-20",
    no_estoque: 35,
    estoque_alocado: 35,
    preco_venda: 42.5,
    valor_aberto: 4_250,
    previsao_op: {
      kind: "coberto",
      saldoNecessarioProducao: 65,
      saldoCobertoPorOp: 65,
      saldoFaltanteProducao: 0,
      previsaoData: "2026-08-18",
      previsaoLabel: "18/08/2026",
      opsUtilizadas: [
        {
          numero_op: "OP-100",
          saldo_op_total: 80,
          saldo_alocado: 65,
          data_fim_prevista_op: "2026-08-18",
          observacao_op: "Prioridade comercial",
          quantidade_op: 100,
          quantidade_produzida: 20,
          data_emissao_op: "2026-08-01",
          data_inicio_prevista_op: "2026-08-10",
          armazem: "99",
          descricao_produto: "Produto acabado",
        },
      ],
    },
  };
}

describe("paridade funcional do detalhe de produção", () => {
  it("projeta os mesmos blocos e dados para as páginas da linha e da OP", () => {
    const item = representativeOpenOrder();
    const lineProjection = buildOpenOrdersProductionDetailViewModel(item);
    const pageProjection = buildOpenOrdersProductionDetailViewModel(item, "OP-100");

    expect(pageProjection.sections).toEqual(lineProjection.sections);
    expect(pageProjection.sections.map((section) => section.id)).toEqual([
      "snapshot",
      "factory",
      "metrics",
      "coverage_deadline",
      "production_order",
      "product_structure",
    ]);
    expect(pageProjection.selectedProductionOrder).toBe("OP-100");
    expect(pageProjection.metrics).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ id: "order_balance", value: "100,000" }),
        expect.objectContaining({ id: "allocated_stock", value: "35,000" }),
        expect.objectContaining({ id: "open_value", value: "R$ 4.250,00" }),
      ]),
    );
    expect(
      pageProjection.sections.find((section) => section.id === "production_order")?.data,
    ).toEqual({
      selectedProductionOrder: "OP-100",
      operations: item.previsao_op?.opsUtilizadas,
    });
  });

  it("mantém a OP explicitamente selecionada quando há mais de uma opção", () => {
    const item = representativeOpenOrder();
    const forecast = item.previsao_op;
    if (!forecast) throw new Error("Fixture sem previsão de OP.");
    forecast.opsUtilizadas.push({
      ...forecast.opsUtilizadas[0],
      numero_op: "OP-200",
      saldo_alocado: 10,
    });

    const projection = buildOpenOrdersProductionDetailViewModel(item, " OP-200 ");

    expect(projection.selectedProductionOrder).toBe("OP-200");
    expect(
      projection.sections.find((section) => section.id === "factory")?.data,
    ).toEqual(expect.objectContaining({ productionOrder: "OP-200" }));
  });
});
