import { describe, expect, it } from "vitest";

import { buildDrillDownQuery } from "./chatDrillDown";

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
});
