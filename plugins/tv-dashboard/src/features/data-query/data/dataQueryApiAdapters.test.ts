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
    expect(adaptPreviewResult({ preview: {} }).runtimeErrors).toEqual({
      count: 0,
      sample: [],
    });
  });
});
