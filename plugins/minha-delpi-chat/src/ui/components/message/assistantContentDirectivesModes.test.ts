import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "./assistantContentSegments";

const EXPECTED_TABLE_TITLES = [
  "Estrutura do produto (BOM)",
  "Fornecedores por matéria-prima",
  "Última compra por matéria-prima",
];

function directivesTablePresentations() {
  return [
    {
      type: "table" as const,
      title: "Estrutura do produto (BOM)",
      role: "structure",
      columns: [{ key: "component_code", label: "Componente" }],
      rows: [{ component_code: "50250258" }],
    },
    {
      type: "table" as const,
      title: "Fornecedores por matéria-prima",
      role: "list",
      columns: [{ key: "supplier_code", label: "Fornecedor" }],
      rows: [{ supplier_code: "000052" }],
    },
    {
      type: "table" as const,
      title: "Última compra por matéria-prima",
      role: "list",
      columns: [{ key: "invoice_number", label: "Nº nota" }],
      rows: [{ invoice_number: "015277" }],
    },
  ];
}

function buildDirectivesToolCalls(options: {
  sessionFormat?: "table" | "text";
  layoutMode: "stack" | "single";
  selected: string;
  renderPlanSegments: Array<Record<string, string>>;
}) {
  const tablePresentations = directivesTablePresentations();

  return [
    {
      name: "execute_external_action",
      metadata: {
        ok: true,
        path: "/products/directives/90260882",
        ...(options.sessionFormat
          ? {
              explicitSessionFormat: options.sessionFormat,
              preferredFormat: options.sessionFormat,
            }
          : {}),
        textPresentation: {
          markdown:
            "### Diretivas do produto — 90260882\n\nDiretivas do PA **90260882**: estrutura, fornecedores e última compra das MPs.",
          title: "Diretivas do produto — 90260882",
        },
        presentation:
          options.sessionFormat === "table"
            ? tablePresentations[1]
            : undefined,
        tablePresentations,
        presentationDecision: {
          selected: options.selected,
          layoutMode: options.layoutMode,
          presentationMode: "summary_then_evidence",
        },
        stackPresentationPlan: {
          presentationMode: "summary_then_evidence",
          profileFirst: false,
          highlightsAfterProfile: false,
          tableRoleOrder: ["structure", "list", "other"],
          tailVisualOrder: [],
          narrativeOrder: ["lead", "operationalTables"],
          renderHints: { textRenderMode: "compact", tailVisualPolicy: "allowlist" },
        },
        renderPlan: {
          version: 1,
          layoutMode: options.layoutMode,
          segments: options.renderPlanSegments,
        },
      },
    },
  ] as never;
}

function tableTitlesFromSegments(
  segments: ReturnType<typeof buildAssistantContentSegments>,
): string[] {
  return segments
    .filter((segment) => segment.kind === "table")
    .map((segment) => String(segment.presentation.title || ""));
}

describe("directives presentation modes (MFE)", () => {
  it("Automático — stack com 3 tabelas de evidência", () => {
    const content =
      "### Diretivas do produto — 90260882\n\nDiretivas do PA **90260882**: estrutura, fornecedores e última compra das MPs.";
    const toolCalls = buildDirectivesToolCalls({
      layoutMode: "stack",
      selected: "text",
      renderPlanSegments: [
        { kind: "markdown", slot: "lead", source: "textPresentation" },
        {
          kind: "table",
          slot: "operationalTables",
          source: "tablePresentations",
        },
      ],
    });

    const segments = buildAssistantContentSegments(content, toolCalls);
    const titles = tableTitlesFromSegments(segments);

    expect(segments.some((segment) => segment.kind === "markdown")).toBe(true);
    expect(titles).toEqual(EXPECTED_TABLE_TITLES);
  });

  it("Tabela — modo explícito com 3 tabelas", () => {
    const toolCalls = buildDirectivesToolCalls({
      sessionFormat: "table",
      layoutMode: "single",
      selected: "table",
      renderPlanSegments: [
        {
          kind: "table",
          slot: "operationalTables",
          source: "tablePresentations",
        },
      ],
    });

    const segments = buildAssistantContentSegments("", toolCalls);
    const titles = tableTitlesFromSegments(segments);

    expect(titles).toEqual(EXPECTED_TABLE_TITLES);
  });

  it("Texto — embute tabelas GFM no markdown", () => {
    const content =
      "### Diretivas do produto — 90260882\n\nDiretivas do PA **90260882**: estrutura, fornecedores e última compra das MPs.";
    const toolCalls = buildDirectivesToolCalls({
      sessionFormat: "text",
      layoutMode: "stack",
      selected: "text",
      renderPlanSegments: [
        { kind: "markdown", slot: "lead", source: "textPresentation" },
      ],
    });

    const segments = buildAssistantContentSegments(content, toolCalls);
    const markdown = segments
      .filter((segment) => segment.kind === "markdown")
      .map((segment) => segment.markdown)
      .join("\n\n");

    expect(segments.every((segment) => segment.kind === "markdown")).toBe(true);
    expect(markdown).toContain("Estrutura do produto (BOM)");
    expect(markdown).toContain("Fornecedores por matéria-prima");
    expect(markdown).toContain("Última compra por matéria-prima");
    expect(markdown.match(/\|[^\n]+\|/g)?.length ?? 0).toBeGreaterThanOrEqual(3);
  });
});
