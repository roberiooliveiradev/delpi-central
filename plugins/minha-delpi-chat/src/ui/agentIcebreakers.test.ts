import { describe, expect, it } from "vitest";

import {
  agentIcebreakersUseDefaults,
  buildIcebreakerPlaceholderToken,
  clampIcebreakerHintDraft,
  clampIcebreakerTitle,
  clampIcebreakerTitleDraft,
  getIcebreakerGridDensityClass,
  icebreakerRequiresShortcutModal,
  normalizeAgentIcebreakerEntries,
  normalizeIcebreakerEntriesForSave,
  reorderIcebreakerEntries,
  reorderIcebreakers,
  resolveAgentIcebreakerEntries,
  resolveAgentIcebreakerEntriesForEditor,
  resolveAgentIcebreakersForDisplay,
  resolveIcebreakerPromptOptions,
} from "./agentIcebreakers";
import { DEFAULT_AGENT_ICEBREAKERS } from "./chatHomeStarters";

describe("agentIcebreakers", () => {
  it("usa padrões na home e no editor quando metadata está vazio", () => {
    expect(resolveAgentIcebreakersForDisplay({})).toEqual(DEFAULT_AGENT_ICEBREAKERS);
    expect(resolveAgentIcebreakerEntriesForEditor({})).toHaveLength(DEFAULT_AGENT_ICEBREAKERS.length);
    expect(agentIcebreakersUseDefaults({})).toBe(true);
  });

  it("respeita quebra-gelos configurados como string legada", () => {
    const metadata = {
      icebreakers: ["me fale do produto {{productCode}}"],
    };

    expect(resolveAgentIcebreakersForDisplay(metadata)).toEqual([
      "me fale do produto {{productCode}}",
    ]);
    expect(resolveAgentIcebreakerEntriesForEditor(metadata)[0]?.template).toBe(
      "me fale do produto {{productCode}}",
    );
    expect(agentIcebreakersUseDefaults(metadata)).toBe(false);
  });

  it("aceita objetos com label, hint e fields no metadata", () => {
    const metadata = {
      icebreakers: [
        {
          template: "qual o estoque do produto {{productCode}}?",
          label: "Estoque",
          hint: "Por filial",
          fields: [
            {
              id: "productCode",
              label: "Código do produto",
              fieldType: "productCode",
            },
          ],
        },
      ],
    };

    expect(resolveAgentIcebreakerEntries(metadata)).toEqual([
      {
        template: "qual o estoque do produto {{productCode}}?",
        label: "Estoque",
        hint: "Por filial",
        fields: [
          {
            id: "productCode",
            label: "Código do produto",
            fieldType: "productCode",
            required: true,
          },
        ],
      },
    ]);
    expect(normalizeAgentIcebreakerEntries(metadata)).toEqual(
      resolveAgentIcebreakerEntries(metadata),
    );
  });

  it("gera token de placeholder", () => {
    expect(buildIcebreakerPlaceholderToken("productCode")).toBe("{{productCode}}");
  });

  it("rascunho de título e subtítulo preserva espaços durante a digitação", () => {
    expect(clampIcebreakerTitleDraft("matéria-prima, produto ")).toBe(
      "matéria-prima, produto ",
    );
    expect(clampIcebreakerHintDraft("Estrutura, MPs, ")).toBe("Estrutura, MPs, ");
    expect(clampIcebreakerTitle("  título  ")).toBe("título");
  });

  it("usa grid 2x2 para quatro sugestões", () => {
    expect(getIcebreakerGridDensityClass(4)).toBe(
      "mdc-chat-agent-landing__prompts-grid--quad",
    );
  });

  it("preserva todos os quebra-gelos configurados sem truncar", () => {
    const many = Array.from({ length: 8 }, (_, index) => `sugestão ${index + 1}`);

    expect(resolveAgentIcebreakersForDisplay({ icebreakers: many })).toEqual(many);
  });

  it("reordena entradas preservando conteúdo", () => {
    const items = [
      { template: "a", label: "A" },
      { template: "b", label: "B" },
      { template: "c", label: "C" },
    ];

    expect(reorderIcebreakerEntries(items, 0, 2)).toEqual([
      { template: "b", label: "B" },
      { template: "c", label: "C" },
      { template: "a", label: "A" },
    ]);
  });

  it("reordena strings legadas", () => {
    const items = ["a", "b", "c"];

    expect(reorderIcebreakers(items, 0, 2)).toEqual(["b", "c", "a"]);
  });

  it("normaliza para salvar exigindo título e template", () => {
    const saved = normalizeIcebreakerEntriesForSave([
      { template: "pergunta {{productCode}}", label: "Título" },
      { template: "sem título", label: "" },
    ]);

    expect(saved).toHaveLength(1);
    expect(saved[0]?.label).toBe("Título");
  });

  it("resolve opções do diálogo a partir da entrada configurada", () => {
    const entry = {
      template: "me fale do produto {{productCode}}",
      label: "Consultar produto",
      hint: "Cadastro e estoque",
      fields: [
        {
          id: "productCode",
          label: "Código do produto",
          fieldType: "productCode",
          required: true,
        },
      ],
    };

    expect(resolveIcebreakerPromptOptions(entry)).toEqual({
      title: "Consultar produto",
      description: "Cadastro e estoque",
      fields: expect.arrayContaining([
        expect.objectContaining({ id: "productCode", label: "Código do produto" }),
      ]),
    });
    expect(icebreakerRequiresShortcutModal(entry)).toBe(true);
    expect(
      icebreakerRequiresShortcutModal({
        template: "o que você pode fazer?",
        label: "Capacidades",
      }),
    ).toBe(false);
  });
});
