import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "../../message/assistantContentSegments";
import {
  filterSegmentsWithoutHierarchyTableDuplicates,
  isHierarchyDuplicateTable,
  toolCallsHaveTree,
} from "./presentationStructureDedup";
import { fixtureToolCalls } from "../../testFixtures";

describe("presentationStructureDedup", () => {
  const structureTable = {
    type: "table" as const,
    title: "Componentes da estrutura 90260149",
    columns: [
      { key: "parent_code", label: "PI pai" },
      { key: "component_code", label: "Componente" },
    ],
    rows: [{ parent_code: "A", component_code: "B" }],
  };

  const tree = {
    type: "tree" as const,
    title: "Estrutura do produto 90260149",
    root: { id: "90260149", label: "90260149", children: [] },
  };

  it("detecta tabela plana de componentes da estrutura", () => {
    expect(isHierarchyDuplicateTable(structureTable)).toBe(true);
  });

  it("confia no metadata quando structureDedupApplied está true", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          structureDedupApplied: true,
          presentation: tree,
          tablePresentation: structureTable,
        },
      },
    ]);

    const segments = filterSegmentsWithoutHierarchyTableDuplicates(
      [
        { kind: "tree", presentation: tree },
        { kind: "table", presentation: structureTable },
      ],
      toolCalls,
    );

    expect(segments.some((segment) => segment.kind === "table")).toBe(true);
  });

  it("não monta tabela de estrutura quando a árvore já está no turno", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          presentation: tree,
          tablePresentation: structureTable,
          tablePresentations: [
            {
              type: "table",
              title: "Produto 90260149",
              columns: [{ key: "campo", label: "Campo" }],
              rows: [{ campo: "Código", valor: "90260149" }],
            },
            structureTable,
          ],
        },
      },
    ]);

    expect(toolCallsHaveTree(toolCalls)).toBe(true);

    const segments = buildAssistantContentSegments("", toolCalls);
    const tableTitles = segments
      .filter((segment) => segment.kind === "table")
      .map((segment) => segment.presentation.title);

    expect(segments.some((segment) => segment.kind === "tree")).toBe(true);
    expect(tableTitles).not.toContain("Componentes da estrutura 90260149");
    expect(tableTitles).toContain("Produto 90260149");
  });
});
