import { describe, expect, it } from "vitest";

import { csvCell } from "../../../../export/primitives";
import {
  buildChartExportPayload,
  buildKpiExportPayload,
  buildTableExportPayload,
  resolveTableExportColumns,
  sanitizeSheetName,
} from "./exportUtils";

describe("exportUtils payloads", () => {
  it("prefere exportColumns e mantém campo oculto na exportação CSV", () => {
    const presentation = {
      type: "table" as const,
      title: "Planejamento",
      columns: [
        { key: "product_code", label: "Produto" },
        { key: "warehouse", label: "Depósito" },
        { key: "planned_qty", label: "Qtd. planejada" },
      ],
      exportColumns: [
        { key: "product_code", label: "Produto" },
        { key: "warehouse", label: "Depósito" },
        { key: "planned_qty", label: "Qtd. planejada" },
        { key: "unit", label: "Unidade" },
      ],
      config: { hiddenFields: ["unit"] },
      rows: [{ product_code: "P1", warehouse: "W1", planned_qty: 10, unit: "UN" }],
    };

    expect(resolveTableExportColumns(presentation).map((column) => column.key)).toEqual([
      "product_code",
      "warehouse",
      "planned_qty",
      "unit",
    ]);

    const payload = buildTableExportPayload(presentation);
    const header = payload.columns.map((column) => column.label).join(";");
    const body = payload.rows
      .map((row) => payload.columns.map((column) => csvCell(row[column.key])).join(";"))
      .join("\n");

    expect(header).toBe("Produto;Depósito;Qtd. planejada;Unidade");
    expect(body).toContain("UN");
  });

  it("monta payload tabular com linhas filtradas", () => {
    const payload = buildTableExportPayload(
      {
        type: "table",
        title: "Estoque",
        columns: [
          { key: "filial", label: "Filial" },
          { key: "saldo", label: "Saldo" },
        ],
        rows: [
          { filial: "01", saldo: 10 },
          { filial: "02", saldo: 20 },
        ],
      },
      [{ filial: "01", saldo: 10 }],
    );

    expect(payload.rows).toHaveLength(1);
    expect(payload.columns.map((column) => column.label)).toEqual(["Filial", "Saldo"]);
  });

  it("humaniza colunas de gráfico com fieldLabels", () => {
    const payload = buildChartExportPayload({
      type: "chart",
      title: "Eficiência",
      chartType: "bar",
      data: [{ nome_operador: "Ana", eficiencia_percentual: 80 }],
      config: {
        fieldLabels: {
          nome_operador: "Operador",
          eficiencia_percentual: "Eficiência (%)",
        },
      },
    });

    expect(payload.columns).toEqual([
      { key: "nome_operador", label: "Operador" },
      { key: "eficiencia_percentual", label: "Eficiência (%)" },
    ]);
  });

  it("monta payload de KPI", () => {
    const payload = buildKpiExportPayload({
      type: "kpi",
      title: "Resumo",
      cards: [{ label: "OPs abertas", value: 12, unit: "un." }],
    });

    expect(payload.rows[0]?.label).toBe("OPs abertas");
    expect(payload.columns[0]?.label).toBe("Indicador");
  });
});

describe("sanitizeSheetName", () => {
  it("remove caracteres inválidos do Excel (ex.: barra no título de estoque)", () => {
    expect(sanitizeSheetName("Estoque por filial/armazém")).toBe(
      "Estoque por filial armazém",
    );
  });

  it("limita a 31 caracteres", () => {
    const long = "A".repeat(40);
    expect(sanitizeSheetName(long).length).toBeLessThanOrEqual(31);
  });

  it("retorna fallback quando vazio", () => {
    expect(sanitizeSheetName("   ///   ")).toBe("Dados");
  });
});
