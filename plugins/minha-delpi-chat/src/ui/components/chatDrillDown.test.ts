import { describe, expect, it } from "vitest";

import {
  buildChartPointMenuActions,
  buildDrillDownQuery,
  buildTableRowMenuActions,
} from "./chatDrillDown";

const stockColumns = [
  { key: "branch", label: "Filial" },
  { key: "warehouse", label: "Armazém" },
  { key: "product_code", label: "Produto" },
  { key: "available_quantity", label: "Qtd. disponível" },
];

describe("buildDrillDownQuery", () => {
  it("monta filtro de estoque com filial, armazém e produto", () => {
    const query = buildDrillDownQuery(
      {
        branch: "2",
        warehouse: "1",
        product_code: "10080022",
        available_quantity: 10,
      },
      stockColumns,
    );

    expect(query).toBe("filtre filial 02 armazém 01 do produto 10080022");
  });

  it("monta filtro só com filial quando armazém não existe", () => {
    const query = buildDrillDownQuery(
      { branch: "01", product_code: "10080022" },
      [
        { key: "branch", label: "Filial" },
        { key: "product_code", label: "Produto" },
      ],
    );

    expect(query).toBe("filtre filial 01 do produto 10080022");
  });

  it("usa código quando não há colunas operacionais", () => {
    const query = buildDrillDownQuery(
      { code: "90260077", description: "Parafuso" },
      [
        { key: "code", label: "Código" },
        { key: "description", label: "Descrição" },
      ],
    );

    expect(query).toBe("Detalhe do item 90260077 (Parafuso)");
  });

  it("não assume produto em colunas genéricas: interpreta o último resultado", () => {
    const query = buildDrillDownQuery(
      { A1_COD: "000224", A1_NOME: "ACRILMASTER INDUSTRIA DE ACRILICOS LTDA" },
      [
        { key: "A1_COD", label: "A1 cod" },
        { key: "A1_NOME", label: "A1 nome" },
      ],
    );

    expect(query).toBe(
      "detalhe este registro do último resultado — A1 cod: 000224; " +
        "A1 nome: ACRILMASTER INDUSTRIA DE ACRILICOS LTDA",
    );
  });
});

describe("buildTableRowMenuActions", () => {
  it("inclui detalhar e consultas de produto quando há código", () => {
    const actions = buildTableRowMenuActions(
      { product_code: "10080001", description: "Item teste" },
      [
        { key: "product_code", label: "Produto" },
        { key: "description", label: "Descrição" },
      ],
    );

    const labels = actions.map((action) => action.label);

    expect(labels).toContain("Detalhar item");
    expect(labels).toContain("Ver estoque");
    expect(labels).toContain("Ver fornecedores");
    expect(actions.find((a) => a.id === "stock")?.query).toBe(
      "qual o estoque do produto 10080001?",
    );
  });
});

describe("buildChartPointMenuActions", () => {
  it("monta detalhe e ver como tabela para categoria do eixo X", () => {
    const actions = buildChartPointMenuActions(
      { month: "Março 2026", sales: 1200 },
      "month",
    );

    const labels = actions.map((action) => action.label);

    expect(labels).toContain("Ver detalhe");
    expect(labels).toContain("Ver como tabela");
    expect(actions.find((a) => a.id === "chart-detail")?.query).toBe(
      "detalhe Março 2026 deste gráfico",
    );
  });

  it("inclui ações de produto quando o eixo X parece código", () => {
    const actions = buildChartPointMenuActions(
      { product: "10080001", qty: 5 },
      "product",
    );

    expect(actions.map((a) => a.label)).toContain("Ver estoque");
  });
});
