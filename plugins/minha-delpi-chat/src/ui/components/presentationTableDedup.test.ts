import { describe, expect, it } from "vitest";

import {
  dedupeTablePresentations,
  dedupeTableSegments,
  isSameTablePresentation,
} from "./presentationTableDedup";
import type { AssistantContentSegment } from "./message/assistantContentTypes";

const profileTable = {
  type: "table" as const,
  title: "Produto 90260149",
  columns: [{ key: "campo", label: "Campo" }],
  rows: [{ campo: "Código", valor: "90260149" }],
};

describe("presentationTableDedup", () => {
  it("remove tabelas de cadastro duplicadas", () => {
    const tables = dedupeTablePresentations([profileTable, { ...profileTable }]);

    expect(tables).toHaveLength(1);
    expect(isSameTablePresentation(tables[0], profileTable)).toBe(true);
  });

  it("deduplica segmentos de tabela na pilha", () => {
    const segments: AssistantContentSegment[] = [
      { kind: "table", presentation: profileTable },
      { kind: "table", presentation: { ...profileTable } },
      {
        kind: "markdown",
        markdown: "**Pontos de atenção**\n\n1. Alerta.",
      },
    ];

    expect(dedupeTableSegments(segments)).toHaveLength(2);
  });
});
