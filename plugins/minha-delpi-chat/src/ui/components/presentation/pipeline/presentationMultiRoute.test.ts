import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "../../message/assistantContentSegments";
import {
  buildMultiRouteStackSegments,
  collectProductRouteBlocks,
  groupSegmentsByRouteSections,
  isMultiRouteProductPresentation,
  routeKeyFromPath,
  routeKeyFromSectionId,
} from "./presentationMultiRoute";
import {
  filterSegmentsByVisualKind,
  resolveAvailableVisualFormatOptions,
} from "../../message/assistantContentVisualFormats";
import {
  getDataCoverageNoticeFromToolCall,
  getDataCoverageNoticeFromToolCalls,
} from "../../chatPresentation";
import { fixtureToolCalls } from "../../testFixtures";

describe("presentationMultiRoute", () => {
  it("detecta múltiplas rotas de produto", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/90260149/structure",
          presentation: {
            type: "tree",
            title: "Estrutura",
            root: { id: "1", label: "1", children: [] },
          },
        },
      },
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/90260149/stock",
          tablePresentation: {
            type: "table",
            title: "Estoque",
            columns: [{ key: "branch", label: "Filial" }],
            rows: [{ branch: "01" }],
          },
          chartPresentation: {
            type: "chart",
            chartType: "bar",
            title: "Estoque",
            data: [{ branch: "01", qtd: 1 }],
          },
        },
      },
    ]);

    expect(isMultiRouteProductPresentation(toolCalls)).toBe(true);
    expect(collectProductRouteBlocks(toolCalls).map((block) => block.routeKey)).toEqual([
      "structure",
      "stock",
    ]);
  });

  it("ordena visuais por rota — árvore não fica entre tabela e gráfico de estoque", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/90260149/stock",
          tablePresentation: {
            type: "table",
            title: "Estoque",
            columns: [{ key: "branch", label: "Filial" }],
            rows: [{ branch: "01" }],
          },
          chartPresentation: {
            type: "chart",
            chartType: "bar",
            title: "Estoque",
            data: [{ branch: "01", qtd: 1 }],
          },
        },
      },
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/90260149/structure",
          presentation: {
            type: "tree",
            title: "Estrutura",
            root: { id: "1", label: "1", children: [] },
          },
        },
      },
    ]);

    const commentary = [
      "### Estoque",
      "",
      "Resumo do estoque.",
      "",
      "### Estrutura (BOM)",
      "",
      "Resumo da estrutura.",
    ].join("\n");

    const segments = buildMultiRouteStackSegments(commentary, toolCalls, (target, segment) => {
      target.push(segment);
    });

    expect(segments).not.toBeNull();

    const kinds = (segments ?? []).map((segment) => segment.kind);
    const stockSectionIndex = kinds.indexOf("stackSection");
    const tableIndex = kinds.indexOf("table");
    const chartIndex = kinds.indexOf("chart");
    const treeIndex = kinds.indexOf("tree");

    expect(stockSectionIndex).toBeGreaterThanOrEqual(0);
    expect(tableIndex).toBeGreaterThan(stockSectionIndex);
    expect(chartIndex).toBeGreaterThan(tableIndex);
    expect(treeIndex).toBeGreaterThan(chartIndex);
  });

  it("integra no buildAssistantContentSegments", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/90260149/guide",
          presentationDecision: { layoutMode: "stack", selected: "table" },
          tablePresentation: {
            type: "table",
            title: "Roteiro",
            columns: [{ key: "op", label: "Op" }],
            rows: [{ op: "01" }],
          },
        },
      },
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/90260149/structure",
          presentationDecision: { layoutMode: "stack", selected: "tree" },
          presentation: {
            type: "tree",
            title: "Estrutura",
            root: { id: "1", label: "1", children: [] },
          },
        },
      },
    ]);

    const segments = buildAssistantContentSegments("### Roteiro\n\nTexto.\n\n### Estrutura\n\nBOM.", toolCalls);
    const routeSections = segments.filter((segment) => segment.kind === "stackSection");

    expect(routeSections.length).toBe(2);
    expect(routeSections[0]?.kind === "stackSection" && routeSections[0].section.title).toContain(
      "Roteiro",
    );
  });

  it("mapeia segmentos de path", () => {
    expect(routeKeyFromPath("/products/1/stock")).toBe("stock");
    expect(routeKeyFromPath("/products/1/guide")).toBe("guide");
    expect(routeKeyFromPath("/products/1/structure")).toBe("structure");
    expect(routeKeyFromSectionId("route-stock")).toBe("stock");
  });

  it("agrupa segmentos por seção de rota e não expõe toolbar global", () => {
    const toolCalls = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/10070011/stock",
          tablePresentation: {
            type: "table",
            title: "Estoque",
            columns: [{ key: "branch", label: "Filial" }],
            rows: [{ branch: "01" }],
          },
          chartPresentation: {
            type: "chart",
            chartType: "bar",
            title: "Estoque",
            data: [{ branch: "01", qtd: 0 }],
          },
        },
      },
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/10070011/parents",
          presentation: {
            type: "tree",
            title: "Onde é usado",
            root: { id: "1", label: "1", children: [] },
          },
        },
      },
    ]);

    const segments = buildAssistantContentSegments(
      "### Estoque\n\nResumo estoque.\n\n### Onde é usado\n\nResumo pais.",
      toolCalls,
    );
    const grouped = groupSegmentsByRouteSections(segments);

    expect(grouped.sections).toHaveLength(2);
    expect(grouped.sections[0]?.section.id).toMatch(/^route-stock-/);
    expect(grouped.sections[1]?.section.id).toMatch(/^route-parents-/);
    expect(grouped.sections[0]?.section.title).toContain("10070011");
    expect(grouped.sections[1]?.segments.some((segment) => segment.kind === "tree")).toBe(
      true,
    );
    expect(resolveAvailableVisualFormatOptions(segments, toolCalls)).toEqual([]);

    const stockSection = grouped.sections[0]?.segments ?? [];
    const stockBody = stockSection.filter((segment) => segment.kind !== "stackSection");
    const textBody = filterSegmentsByVisualKind(stockBody, "text");

    expect(textBody.some((segment) => segment.kind === "markdown")).toBe(true);
    expect(stockBody.some((segment) => segment.kind === "table")).toBe(true);
    expect(stockSection.some((segment) => segment.kind === "stackSection")).toBe(true);
  });

  it("aviso de parcial fica ligado à tool call da rota (não à primeira da lista)", () => {
    const stockCall = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/10080022/stock",
          tablePresentation: {
            type: "table",
            title: "Estoque",
            columns: [{ key: "branch", label: "Filial" }],
            rows: [{ branch: "01" }],
          },
        },
      },
    ])[0];

    const parentsCall = fixtureToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          ok: true,
          path: "/products/10080022/parents",
          dataCoverageNotice: {
            kind: "pagination",
            message:
              "Parcial · Produtos pai parcial: página 1 de 3 (200 de 419 registro(s) nesta resposta).",
            details: {
              pagination: { page: 1, pageSize: 200, total: 419, totalPages: 3 },
            },
          },
          presentation: {
            type: "tree",
            title: "Onde é usado",
            root: { id: "1", label: "1", children: [] },
          },
        },
      },
    ])[0];

    expect(getDataCoverageNoticeFromToolCall(stockCall)).toBeNull();
    expect(getDataCoverageNoticeFromToolCall(parentsCall)?.message).toContain(
      "Produtos pai parcial",
    );
    expect(getDataCoverageNoticeFromToolCalls([stockCall, parentsCall])?.message).toContain(
      "Produtos pai parcial",
    );
  });
});
