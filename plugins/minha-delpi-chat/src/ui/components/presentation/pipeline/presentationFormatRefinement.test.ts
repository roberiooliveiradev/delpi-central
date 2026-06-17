import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "../../message/assistantContentSegments";
import { resolveAssistantContentLayout, shouldShowAllVisualSegments } from "../../message/assistantContentLayout";
import {
  hasRichStackPresentation,
  resolveCommentaryTextBody,
} from "../../chatPresentation";
import { resolveAvailableVisualFormatOptions } from "../../message/assistantContentVisualFormats";
import { fixtureToolCalls } from "../../message/testFixtures";

describe("presentationFormatRefinement", () => {
  const stockTableRefinement = fixtureToolCalls([
    {
      name: "execute_external_action",
      metadata: {
        ok: true,
        path: "/products/10080077/stock",
        preferredFormat: "table",
        presentationDecision: {
          layoutMode: "single",
          selected: "table",
          availableViews: ["table"],
        },
        presentation: {
          type: "table",
          title: "Estoque do produto 10080077",
          columns: [
            { key: "branch", label: "Filial" },
            { key: "current_quantity", label: "Qtd." },
          ],
          rows: [{ branch: "01", current_quantity: 100 }],
        },
        textPresentation: {
          type: "markdown",
          markdown: "### Estoque\n\n**Destaques**\n\n- Saldo disponível.",
        },
      },
    },
  ]);

  it("refinamento para tabela única não empilha modo stack", () => {
    expect(resolveAssistantContentLayout("", stockTableRefinement)).not.toBe("stack");
    expect(shouldShowAllVisualSegments(stockTableRefinement)).toBe(false);
  });

  it("renderiza tabela nativa após pedido de formato tabela", () => {
    const segments = buildAssistantContentSegments("", stockTableRefinement);
    const kinds = segments.map((segment) => segment.kind);

    expect(kinds).toContain("table");
    expect(kinds.filter((kind) => kind === "table")).toHaveLength(1);
  });

  it("mantém destaques no texto sem duplicar linhas da tabela", () => {
    const commentary = resolveCommentaryTextBody("", stockTableRefinement);

    expect(commentary).toContain("**Destaques**");
    expect(commentary).not.toContain("| Filial |");
  });

  const treeRefinement = fixtureToolCalls([
    {
      name: "execute_external_action",
      metadata: {
        ok: true,
        path: "/products/90260149/structure",
        preferredFormat: "tree",
        presentationDecision: {
          layoutMode: "single",
          selected: "tree",
          availableViews: ["text", "table", "tree"],
        },
        presentation: {
          type: "tree",
          title: "Estrutura do produto 90260149",
          root: { id: "90260149", label: "90260149", children: [] },
        },
        textPresentation: {
          type: "markdown",
          markdown: "### Estrutura\n\nUse a **árvore** abaixo.",
        },
      },
    },
  ]);

  it("refinamento para árvore prioriza segmento tree", () => {
    const segments = buildAssistantContentSegments("", treeRefinement);
    const options = resolveAvailableVisualFormatOptions(segments, treeRefinement);

    expect(segments.some((segment) => segment.kind === "tree")).toBe(true);
    expect(options.some((option) => option.kind === "tree")).toBe(true);
    expect(hasRichStackPresentation(treeRefinement)).toBe(false);
  });
});
