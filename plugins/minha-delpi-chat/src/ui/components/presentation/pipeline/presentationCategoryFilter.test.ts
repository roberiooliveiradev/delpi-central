import { describe, expect, it } from "vitest";

import {
  applyCategoryFilter,
  applyPresentationRowPipeline,
  applyTableSearchFilter,
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
    expect(options.find((option) => option.key === "filial")?.mode).toBe("equality");
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
    const labeledRows = [
      { parent_code: "90260882", description: "Item A" },
      { parent_code: "50250258", description: "Item B" },
    ];
    const fieldLabels = {
      parent_code: "Código pai",
      description: "Descrição",
    };

    const options = buildCategoryFilterOptions(
      labeledRows,
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

  it("usa modo contains quando a coluna tem muitos valores distintos", () => {
    const manyRows = Array.from({ length: 45 }, (_, index) => ({
      parent_code: `C${String(index).padStart(4, "0")}`,
      type: index % 2 === 0 ? "PI" : "PA",
    }));

    const options = buildCategoryFilterOptions(manyRows, ["parent_code", "type"]);

    expect(options.find((option) => option.key === "parent_code")?.mode).toBe("contains");
    expect(options.find((option) => option.key === "parent_code")?.values).toEqual([]);
    expect(options.find((option) => option.key === "type")?.mode).toBe("equality");
  });

  it("filtra por substring no modo contains", () => {
    const filtered = applyCategoryFilter(
      [
        { description: "CHICOTE DE LIGACAO" },
        { description: "CABO PVC" },
      ],
      "description",
      "chicote",
      "contains",
    );

    expect(filtered).toHaveLength(1);
    expect(filtered[0]?.description).toBe("CHICOTE DE LIGACAO");
  });

  it("aplica busca global AND filtro de coluna", () => {
    const pipelineRows = [
      { code: "1008", description: "PROTETOR A", type: "MP" },
      { code: "2008", description: "PROTETOR B", type: "PI" },
      { code: "1009", description: "CABO", type: "MP" },
    ];

    const searched = applyTableSearchFilter(pipelineRows, "protetor", [
      "code",
      "description",
      "type",
    ]);
    expect(searched).toHaveLength(2);

    const combined = applyPresentationRowPipeline(pipelineRows, {
      searchQuery: "protetor",
      filterKey: "type",
      filterValue: "MP",
      filterMode: "equality",
      columnKeys: ["code", "description", "type"],
    });

    expect(combined).toHaveLength(1);
    expect(combined[0]?.code).toBe("1008");
  });
});
