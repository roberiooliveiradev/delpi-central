import { describe, expect, it } from "vitest";

import {
  resolveAssistantPresentationTitle,
  resolveAssistantRenderableMarkdown,
  resolveAssistantStreamingProseState,
  shouldBypassIncrementalTextReveal,
  shouldRenderPresentationHeading,
  stripLeadingMarkdownTitleSafely,
} from "./assistantProseRendering";

describe("assistantProseRendering", () => {
  it("não trata saudação com negrito como título de apresentação", () => {
    const greeting = "Olá! Sou o **Agente Minha DELPI**. O que vamos consultar?";

    expect(resolveAssistantPresentationTitle(greeting, [])).toBe("");
    expect(shouldRenderPresentationHeading(greeting)).toBe(false);
    expect(resolveAssistantRenderableMarkdown(greeting, [])).toBe(greeting);
  });

  it("não remove o corpo quando título coincide com a mensagem inteira", () => {
    const body = "Olá! Sou o **Agente Minha DELPI**.";

    expect(stripLeadingMarkdownTitleSafely(body, body)).toBe(body);
  });

  it("remove apenas cabeçalho real distinto do corpo", () => {
    const body = "### Estoque\n\n| Filial | Qtd |\n| --- | --- |";

    expect(stripLeadingMarkdownTitleSafely(body, "Estoque")).toBe(
      "| Filial | Qtd |\n| --- | --- |",
    );
  });

  it("desliga reveal incremental quando há markdown parcial", () => {
    expect(shouldBypassIncrementalTextReveal("Olá! Sou o **Agente")).toBe(true);
    expect(shouldBypassIncrementalTextReveal("Texto simples.")).toBe(false);
  });

  it("streaming com markdown usa ChatMarkdown imediatamente", () => {
    const answer = "Olá! Sou o **Agente Minha DELPI**.";

    expect(
      resolveAssistantStreamingProseState({
        answer,
        revealedAnswer: "Olá! Sou o *",
        suppressRichPresentation: false,
        isGenerating: true,
        isPlayback: false,
      }),
    ).toEqual({
      markdownContent: answer,
      enableCharReveal: false,
      captionUsesMarkdown: true,
    });
  });

  it("streaming sem markdown mantém reveal incremental", () => {
    expect(
      resolveAssistantStreamingProseState({
        answer: "Consulta concluída.",
        revealedAnswer: "Consulta con",
        suppressRichPresentation: false,
        isGenerating: true,
        isPlayback: false,
      }),
    ).toEqual({
      markdownContent: "Consulta con",
      enableCharReveal: true,
      captionUsesMarkdown: false,
    });
  });
});
