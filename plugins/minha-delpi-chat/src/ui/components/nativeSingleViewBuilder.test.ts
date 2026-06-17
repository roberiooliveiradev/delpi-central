import { describe, expect, it } from "vitest";

import { buildNativeSingleViewSegments } from "./nativeSingleViewBuilder";
import type { AssistantContentSegment } from "./message/assistantContentTypes";

describe("buildNativeSingleViewSegments", () => {
  it("inclui todas as tabelas quando renderPlan aponta tablePresentations", () => {
    const visuals: AssistantContentSegment[] = [
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Estrutura do produto (BOM)",
          role: "structure",
          columns: [],
          rows: [{ component_code: "50250258" }],
        },
      },
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Fornecedores por matéria-prima",
          role: "list",
          columns: [],
          rows: [{ supplier_code: "000052" }],
        },
      },
      {
        kind: "table",
        presentation: {
          type: "table",
          title: "Última compra por matéria-prima",
          role: "list",
          columns: [],
          rows: [{ invoice_number: "015277" }],
        },
      },
    ];
    const toolCalls = [
      {
        name: "execute_external_action",
        metadata: {
          explicitSessionFormat: "table",
          presentationDecision: {
            selected: "table",
            layoutMode: "single",
          },
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [
              {
                kind: "table",
                slot: "operationalTables",
                source: "tablePresentations",
              },
            ],
          },
        },
      },
    ] as never;

    const segments = buildNativeSingleViewSegments("", toolCalls, visuals);
    const tableTitles = (segments ?? [])
      .filter((segment) => segment.kind === "table")
      .map((segment) => segment.presentation.title);

    expect(tableTitles).toEqual([
      "Estrutura do produto (BOM)",
      "Fornecedores por matéria-prima",
      "Última compra por matéria-prima",
    ]);
  });
});
