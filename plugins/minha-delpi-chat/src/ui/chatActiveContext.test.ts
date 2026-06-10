import { describe, expect, it } from "vitest";

import {
  collectActiveContextChips,
  contextChipKey,
  mergeContextChips,
  resolvePresentationFormatForSend,
} from "./chatActiveContext";

describe("chatActiveContext", () => {
  it("deduplica e ordena chips por tipo", () => {
    const merged = mergeContextChips([
      [
        { label: "Tom direto", kind: "tone", value: "direct" },
        { label: "10080001", kind: "context", value: "10080001" },
      ],
      [{ label: "02", kind: "context", value: "02" }],
    ]);

    expect(merged.map((chip) => chip.kind)).toEqual(["context", "context", "tone"]);
  });

  it("agrega chips de várias mensagens do assistente", () => {
    const chips = collectActiveContextChips([
      { role: "user", metadata: {} },
      {
        role: "assistant",
        metadata: {
          contextChips: [{ label: "Produto 10080022", kind: "product", value: "10080022" }],
        },
      },
      {
        role: "assistant",
        metadata: {
          contextChips: [{ label: "Filial 02", kind: "branch", value: "02" }],
        },
      },
    ]);

    expect(chips).toHaveLength(2);
    const keys = chips.map((chip) => contextChipKey(chip)).sort();
    expect(keys).toEqual(["branch:02", "product:10080022"]);
  });
});

import {
  buildActiveContextSummary,
  extractActivePreferenceHint,
} from "./chatActiveContext";

describe("context summary", () => {
  it("monta resumo com separador", () => {
    const summary = buildActiveContextSummary([
      { label: "Produto 10080001", kind: "product", value: "10080001" },
      { label: "Últimos 30 dias", kind: "period", value: "last_30_days" },
    ]);

    expect(summary).toBe("Produto 10080001 · Últimos 30 dias");
  });

  it("extrai hint de preferência", () => {
    const hint = extractActivePreferenceHint([
      { label: "Produto 10080001", kind: "product", value: "10080001" },
      { label: "Respostas curtas", kind: "preference", value: "short" },
    ]);

    expect(hint).toContain("Respostas curtas");
  });
});

describe("resolvePresentationFormatForSend", () => {
  it("usa chip format quando dropdown está em auto", () => {
    expect(
      resolvePresentationFormatForSend("auto", [
        { label: "Tabela", kind: "format", value: "table" },
      ]),
    ).toBe("table");
  });

  it("prioriza dropdown explícito sobre chip", () => {
    expect(
      resolvePresentationFormatForSend("text", [
        { label: "Tabela", kind: "format", value: "table" },
      ]),
    ).toBe("text");
  });
});
