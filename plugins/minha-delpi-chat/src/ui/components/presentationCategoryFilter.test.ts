import { describe, expect, it } from "vitest";

import {
  applyCategoryFilter,
  buildCategoryFilterOptions,
} from "./presentationCategoryFilter";

describe("presentationCategoryFilter", () => {
  const rows = [
    { filial: "01", nome_operador: "A", eficiencia_percentual: 80 },
    { filial: "02", nome_operador: "B", eficiencia_percentual: 54 },
    { filial: "02", nome_operador: "C", eficiencia_percentual: 120 },
  ];

  it("lista colunas categóricas filtráveis", () => {
    const options = buildCategoryFilterOptions(rows);

    expect(options.some((option) => option.key === "filial")).toBe(true);
    expect(options.find((option) => option.key === "filial")?.values).toEqual(["01", "02"]);
  });

  it("filtra linhas por valor", () => {
    const filtered = applyCategoryFilter(rows, "filial", "02");

    expect(filtered).toHaveLength(2);
    expect(filtered.every((row) => row.filial === "02")).toBe(true);
  });

  it("tolera rows indefinido no filtro e nas opções", () => {
    expect(buildCategoryFilterOptions(undefined)).toEqual([]);
    expect(applyCategoryFilter(undefined, "filial", "01")).toEqual([]);
  });

  it("usa rótulos da apresentação quando fieldLabels informado", () => {
    const rows = [
      { parent_code: "90260882", description: "Item A" },
      { parent_code: "50250258", description: "Item B" },
    ];
    const fieldLabels = {
      parent_code: "Código pai",
      description: "Descrição",
    };

    const options = buildCategoryFilterOptions(
      rows,
      ["parent_code", "description"],
      fieldLabels,
    );

    expect(options.find((option) => option.key === "parent_code")?.label).toBe(
      "Código pai",
    );
    expect(options.find((option) => option.key === "description")?.label).toBe(
      "Descrição",
    );
  });
});
