import { describe, expect, it } from "vitest";

import type { OpenOrdersTotvsItem } from "../../../types/openOrdersTotvs";
import {
  buildCustomerConversationPoints,
  buildOrderOpportunityContextSearch,
  findFirstNavigableOrderLine,
  findOrderProposalLine,
} from "./customerAccountActions";

function line(
  overrides: Partial<OpenOrdersTotvsItem> = {},
): OpenOrdersTotvsItem {
  return {
    nome_cliente: "Cliente",
    tipo_entidade: "CLIENTE",
    tipo_pedido: "N",
    pedido_cliente: "PC-1",
    filial: "01",
    pedido: "100",
    linha: "01",
    produto: "P1",
    codigo_cliente: "000001",
    codigo_cadastro: "000001",
    loja_cadastro: "01",
    quantidade: 1,
    entregue: 0,
    saldo: 1,
    data_despacho: null,
    data_entrega: null,
    no_estoque: 0,
    preco_venda: 10,
    valor_aberto: 10,
    ...overrides,
  };
}

describe("buildCustomerConversationPoints", () => {
  it("deriva badges apenas de fatos reais da conta", () => {
    expect(
      buildCustomerConversationPoints(
        {
          quantidadePedidosAtrasados: 2,
          maiorAtrasoDias: 7,
          valorTotalAberto: 1250,
        },
        true,
      ),
    ).toEqual([
      {
        id: "overdue",
        label: "2 pedidos atrasados · maior atraso 7 dias",
        variant: "danger",
      },
      {
        id: "partial-coverage",
        label: "Cobertura cadastral parcial",
        variant: "warning",
      },
      {
        id: "open-value",
        label: "R$ 1.250,00 em aberto",
        variant: "info",
      },
    ]);
  });

  it("mantém empty honesto sem atrasos, lacuna de cobertura ou valor aberto", () => {
    expect(
      buildCustomerConversationPoints(
        {
          quantidadePedidosAtrasados: 0,
          maiorAtrasoDias: 0,
          valorTotalAberto: 0,
        },
        false,
      ),
    ).toEqual([]);
  });
});

describe("drilldown da Conta 360", () => {
  it("abre somente a primeira linha com chaves nativas completas", () => {
    const first = line({ filial: "", linha: "" });
    const navigable = line({ filial: "02", pedido: "200", linha: "03" });
    expect(findFirstNavigableOrderLine([first, navigable])).toBe(navigable);
    expect(findFirstNavigableOrderLine([first])).toBeNull();
  });

  it("expõe OV somente quando o payload já traz proposal_number real", () => {
    const absent = line({ proposal_number: " " });
    const linked = line({ filial: "02", proposal_number: "OV-900" });
    expect(findOrderProposalLine([absent, linked])).toBe(linked);
    expect(findOrderProposalLine([absent])).toBeNull();
    expect(buildOrderOpportunityContextSearch(linked)).toBe(
      "?branch=02&search=OV-900",
    );
  });
});
