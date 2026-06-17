import { describe, expect, it } from "vitest";

import { getPresentationInsightFromToolCalls } from "../chatPresentation";
import { hasMarkdownSyntax, prepareMarkdownContent } from "./chatMarkdown";

const FACTORY_INSIGHT =
  "Situação fabril: **PA PRODUZIDO / AGUARDANDO INSPEÇÃO FINAL** Produção **em andamento** — PA **Sim** · PI **Não**. Sem movimento de expedição/inspeção no intervalo consultado.";

describe("presentationDecision.insight (fabril)", () => {
  it("expõe markdown no insight humanizado", () => {
    const toolCalls = [
      {
        metadata: {
          presentationDecision: {
            selected: "dashboard",
            layoutMode: "stack",
            insight: FACTORY_INSIGHT,
          },
        },
      },
    ] as Parameters<typeof getPresentationInsightFromToolCalls>[0];

    expect(getPresentationInsightFromToolCalls(toolCalls)).toBe(FACTORY_INSIGHT);
    expect(hasMarkdownSyntax(FACTORY_INSIGHT)).toBe(true);
    expect(prepareMarkdownContent(FACTORY_INSIGHT)).toContain("**PA PRODUZIDO");
  });
});
