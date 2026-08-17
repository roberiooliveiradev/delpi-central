import { describe, expect, it } from "vitest";

import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { sortPedidosItems } from "./sortItems";
import { getLineStatus, getLineStatusSortRank } from "./statusBadges";
import { isSortableTableColumnKey } from "./tableColumns";
import { parseOpenOrdersListUrlState } from "./openOrdersDeepLink";

function baseItem(overrides: Partial<OpenOrdersTotvsItem>): OpenOrdersTotvsItem {
  return {
    nome_cliente: "ACME",
    tipo_entidade: "C",
    tipo_pedido: "N",
    pedido_cliente: "",
    filial: "01",
    pedido: "1",
    linha: "01",
    produto: "P1",
    codigo_cliente: "C1",
    codigo_cadastro: "C1",
    loja_cadastro: "01",
    quantidade: 10,
    entregue: 0,
    saldo: 10,
    data_despacho: null,
    data_entrega: "2099-12-31",
    no_estoque: 0,
    estoque_alocado: 0,
    preco_venda: 1,
    valor_aberto: 10,
    ...overrides,
  };
}

describe("sortPedidosItems by status", () => {
  it("coluna status é sortable e aceita deep link sort=status", () => {
    expect(isSortableTableColumnKey("status")).toBe(true);
    const state = parseOpenOrdersListUrlState("?sort=status&dir=asc", {
      allowSellerId: false,
      validSellerIds: [],
    });
    expect(state.sortKey).toBe("status");
    expect(state.sortDirection).toBe("asc");
  });

  it("asc coloca urgência operacional primeiro", () => {
    const podeFaturar = baseItem({
      pedido: "A",
      estoque_alocado: 10,
      data_entrega: "2099-12-31",
    });
    const parcial = baseItem({
      pedido: "B",
      estoque_alocado: 3,
      data_entrega: "2099-12-31",
    });
    const semEstoque = baseItem({
      pedido: "C",
      estoque_alocado: 0,
      data_entrega: "2099-12-31",
    });
    const atrasado = baseItem({
      pedido: "D",
      estoque_alocado: 0,
      data_entrega: "2020-01-01",
    });

    expect(getLineStatus(podeFaturar).kind).toBe("pode_faturar");
    expect(getLineStatus(parcial).kind).toBe("estoque_parcial");
    expect(getLineStatus(semEstoque).kind).toBe("sem_estoque");
    expect(getLineStatus(atrasado).kind).toBe("atrasado_sem_estoque");

    const asc = sortPedidosItems(
      [podeFaturar, parcial, semEstoque, atrasado],
      "status",
      "asc",
    ).map((item) => item.pedido);
    expect(asc).toEqual(["D", "C", "B", "A"]);

    const desc = sortPedidosItems(
      [podeFaturar, parcial, semEstoque, atrasado],
      "status",
      "desc",
    ).map((item) => item.pedido);
    expect(desc).toEqual(["A", "B", "C", "D"]);
  });

  it("rank cresce do atraso sem estoque até pode faturar", () => {
    expect(
      getLineStatusSortRank(
        baseItem({ estoque_alocado: 0, data_entrega: "2020-01-01" }),
      ),
    ).toBeLessThan(
      getLineStatusSortRank(
        baseItem({ estoque_alocado: 10, data_entrega: "2099-12-31" }),
      ),
    );
  });
});
