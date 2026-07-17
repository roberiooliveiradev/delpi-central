import { describe, expect, it } from "vitest";

import { adaptPreviewResult } from "./dataQueryApiAdapters";

describe("adaptPreviewResult", () => {
  it("preserva erros M localizados por linha e coluna", () => {
    const result = adaptPreviewResult({
      preview: {
        columns: [{ key: "valor", label: "Valor", type: "number" }],
        rows: [
          {
            valor: {
              error: {
                stepName: "Tipo alterado",
                code: "m.invalid_cast",
                message: "Texto não é número.",
                rowIndex: 0,
                column: "valor",
              },
            },
          },
        ],
      },
      query: {
        runtimeErrors: {
          count: 1,
          sample: [
            {
              stepName: "Tipo alterado",
              code: "m.invalid_cast",
              message: "Texto não é número.",
              rowIndex: 0,
              column: "valor",
            },
          ],
        },
      },
    });

    expect(result.runtimeErrors).toEqual({
      count: 1,
      sample: [
        {
          stepName: "Tipo alterado",
          code: "m.invalid_cast",
          message: "Texto não é número.",
          rowIndex: 0,
          column: "valor",
        },
      ],
    });
    expect(result.rows[0]?.valor).toMatchObject({
      error: { code: "m.invalid_cast" },
    });
  });

  it("normaliza contrato ausente para coleção vazia", () => {
    const result = adaptPreviewResult({ preview: {} });
    expect(result.sourceColumns).toEqual([]);
    expect(result.runtimeErrors).toEqual({
      count: 0,
      sample: [],
    });
  });

  it("mantém schema da Fonte separado do schema transformado", () => {
    const result = adaptPreviewResult({
      preview: {
        sourceColumns: [
          { key: "periodo", label: "periodo", type: "text" },
          { key: "value", label: "value", type: "number" },
        ],
        columns: [
          { key: "periodo_teste", label: "periodo_teste", type: "text" },
          { key: "value", label: "value", type: "number" },
        ],
        rows: [{ periodo_teste: "01/01/26", value: null }],
      },
    });

    expect(result.sourceColumns.map((column) => column.key)).toEqual([
      "periodo",
      "value",
    ]);
    expect(result.columns.map((column) => column.key)).toEqual([
      "periodo_teste",
      "value",
    ]);
  });
});
