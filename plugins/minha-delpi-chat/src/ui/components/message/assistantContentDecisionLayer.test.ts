import { describe, expect, it } from "vitest";

import {
  stripHighlightsSectionFromMarkdown,
  stripQuickLayerFromMarkdown,
  stripSummarySectionFromMarkdown,
  withDecisionLayer,
} from "./assistantContentDecisionLayer";

describe("assistantContentDecisionLayer", () => {
  it("remove seção de destaques quando o card de decisão está ativo", () => {
    const markdown =
      "### Escopo\n\n" +
      "<!-- section:summary -->\n\n**Resumo**\n\nSaldo confortável.\n\n" +
      "<!-- section:highlights -->\n\n**Destaques**\n\n- Um destaque.\n\n" +
      "<!-- section:attention -->\n\n**Pontos de atenção**\n\n1. Atenção.";

    const stripped = stripHighlightsSectionFromMarkdown(
      stripSummarySectionFromMarkdown(markdown),
    );

    expect(stripped).not.toContain("<!-- section:highlights -->");
    expect(stripped).not.toContain("**Destaques**");
    expect(stripped).toContain("**Pontos de atenção**");
  });

  it("remove camada rápida duplicada do markdown narrativo", () => {
    const markdown =
      "### Status fabril\n\n" +
      "<!-- section:scope -->\n\n" +
      "Situação consolidada.\n\n" +
      "**Resumo**\n\n" +
      "Leitura repetida.\n\n" +
      "Status geral: **OK** — sem bloqueio.\n\n" +
      "<!-- section:guide -->\n\n" +
      "Produção no período.";

    const stripped = stripQuickLayerFromMarkdown(markdown);

    expect(stripped).not.toContain("**Resumo**");
    expect(stripped).not.toContain("Status geral:");
    expect(stripped).toContain("<!-- section:guide -->");
    expect(stripped).toContain("Produção no período.");
  });

  it("não injeta card quando o modo é summary_then_evidence", () => {
    const segments = withDecisionLayer(
      [{ kind: "markdown", markdown: "Situação consolidada na fábrica." }],
      [
        {
          name: "execute_external_action",
          metadata: {
            presentationDecision: { presentationMode: "summary_then_evidence" },
            storyPresentation: {
              type: "story",
              title: "Status fabril",
              blocks: [{ kind: "verdict", text: "Leitura.", status: "ok" }],
            },
          },
        } as never,
      ],
    );

    expect(segments).toHaveLength(1);
    expect(segments[0]?.kind).toBe("markdown");
  });

  it("injeta card de decisão e remove resumo/destaques duplicados", () => {
    const segments = withDecisionLayer(
      [
        {
          kind: "markdown",
          markdown:
            "<!-- section:summary -->\n\n**Resumo**\n\nLeitura.\n\n" +
            "<!-- section:highlights -->\n\n**Destaques**\n\n- Repetido.",
        },
      ],
      [
        {
          name: "execute_external_action",
          metadata: {
            storyPresentation: {
              type: "story",
              title: "Status fabril",
              blocks: [{ kind: "verdict", text: "Leitura.", status: "ok" }],
            },
          },
        } as never,
      ],
    );

    expect(segments[0]?.kind).toBe("decision");
    expect(segments[1]?.kind).toBe("markdown");
    expect(segments[1]?.kind === "markdown" ? segments[1].markdown : "").not.toContain(
      "**Destaques**",
    );
  });
});
