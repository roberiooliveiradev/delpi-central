import { describe, expect, it } from "vitest";

import { collectVisualSegments } from "./visualSegmentCollector";
import { fixtureToolCalls } from "../../message/testFixtures";

describe("collectVisualSegments", () => {
  it("não monta dashboard quando a API omitiu dashboardPresentation", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            tailVisualPolicy: "allowlist",
            tailVisualOrder: ["tree", "chart"],
            renderHints: {
              suppressedKinds: ["dashboard"],
            },
          },
          treePresentation: {
            type: "tree",
            title: "Estrutura fabril",
            root: { id: "90262404", label: "90262404", children: [] },
          },
        },
      },
    ]);

    const kinds = collectVisualSegments(toolCalls).map((segment) => segment.kind);

    expect(kinds).toContain("tree");
    expect(kinds).not.toContain("dashboard");
  });

  it("mantém dashboard quando a API envia dashboardPresentation", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          explicitSessionFormat: "dashboard",
          presentationDecision: {
            presentationMode: "summary_then_evidence",
            layoutMode: "stack",
          },
          stackPresentationPlan: {
            presentationMode: "summary_then_evidence",
            tailVisualPolicy: "allowlist",
            tailVisualOrder: ["dashboard"],
          },
          dashboardPresentation: {
            type: "dashboard",
            title: "Painel fabril",
            panels: [],
          },
        },
      },
    ]);

    const kinds = collectVisualSegments(toolCalls).map((segment) => segment.kind);

    expect(kinds).toContain("dashboard");
  });

  it("ignora visuais latentes quando renderPlan v1 não os inclui", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "textPresentation" },
              { kind: "tree", slot: "tailVisuals", source: "treePresentation" },
            ],
          },
          treePresentation: {
            type: "tree",
            title: "Estrutura fabril",
            root: { id: "90262404", label: "90262404", children: [] },
          },
          dashboardPresentation: {
            type: "dashboard",
            title: "Painel latente",
            panels: [],
          },
        },
      },
    ]);

    const kinds = collectVisualSegments(toolCalls).map((segment) => segment.kind);

    expect(kinds).toEqual(["tree"]);
  });

  it("ignora KPI suprimido quando renderPlan só entrega dashboard", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "textPresentation" },
              { kind: "dashboard", slot: "tailVisuals", source: "dashboardPresentation" },
            ],
          },
          stackPresentationPlan: {
            tailVisualOrder: ["dashboard"],
            renderHints: {
              suppressedKinds: ["kpi", "table"],
            },
          },
          kpiPresentation: {
            type: "kpi",
            title: "Indicadores consolidados",
            cards: [],
          },
          tablePresentation: {
            type: "table",
            title: "Impacto de MPs",
            columns: [],
            rows: [],
          },
          dashboardPresentation: {
            type: "dashboard",
            title: "Painel consolidado",
            panels: [],
          },
        },
      },
    ]);

    const kinds = collectVisualSegments(toolCalls).map((segment) => segment.kind);

    expect(kinds).toEqual(["dashboard"]);
  });

  it("coleta tabela do renderPlan mesmo se suppressedKinds listar table por engano", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          explicitSessionFormat: "table",
          presentationDecision: {
            layoutMode: "single",
            selected: "table",
          },
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [{ kind: "table", slot: "primary", source: "presentation" }],
          },
          stackPresentationPlan: {
            layoutMode: "single",
            renderHints: {
              suppressedKinds: ["chart", "table", "tree"],
            },
          },
          presentation: {
            type: "table",
            title: "Estrutura do produto",
            columns: [{ key: "code", label: "Código" }],
            rows: [{ code: "50231850" }],
          },
          treePresentation: {
            type: "tree",
            title: "Estrutura",
            root: { id: "90261565", label: "90261565", children: [] },
          },
        },
      },
    ]);

    const kinds = collectVisualSegments(toolCalls).map((segment) => segment.kind);

    expect(kinds).toEqual(["table"]);
  });

  it("coleta tabela de /system/tables/.../columns (não suprime por path)", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/system/tables/SB1010/columns",
          preferredFormat: "table",
          presentationDecision: {
            layoutMode: "single",
            selected: "table",
          },
          renderPlan: {
            version: 1,
            layoutMode: "single",
            segments: [
              { kind: "decision", slot: "lead", source: "dataAnswer" },
              { kind: "table", slot: "primary", source: "presentation" },
            ],
          },
          presentation: {
            type: "table",
            title: "Colunas (SX3)",
            columns: [
              { key: "X3_CAMPO", label: "Campo" },
              { key: "X3_TITULO", label: "Título" },
            ],
            rows: [{ X3_CAMPO: "B1_COD", X3_TITULO: "Codigo" }],
          },
        },
      },
    ]);

    const kinds = collectVisualSegments(toolCalls).map((segment) => segment.kind);

    expect(kinds).toEqual(["table"]);
  });

  it("ainda suprime visuais com sqlSchemaPrefetch explícito", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/system/tables/SB1010/columns",
          sqlSchemaPrefetch: true,
          presentation: {
            type: "table",
            title: "Colunas (SX3)",
            columns: [{ key: "X3_CAMPO", label: "Campo" }],
            rows: [{ X3_CAMPO: "B1_COD" }],
          },
        },
      },
    ]);

    expect(collectVisualSegments(toolCalls)).toEqual([]);
  });
});
