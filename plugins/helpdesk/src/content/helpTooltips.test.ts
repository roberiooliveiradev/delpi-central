import { describe, expect, it } from "vitest";

import { helpTooltips } from "./helpTooltips";

const SECTION_MAX = 160;
const FIELD_MAX = 120;

function collectStrings(value: unknown, path = ""): Array<{ path: string; text: string }> {
  if (typeof value === "string") return [{ path: path || "root", text: value }];
  if (value && typeof value === "object") {
    return Object.entries(value as Record<string, unknown>).flatMap(([key, child]) =>
      collectStrings(child, path ? `${path}.${key}` : key),
    );
  }
  return [];
}

describe("helpTooltips budget", () => {
  const entries = collectStrings(helpTooltips);

  it("seções principais cabem em uma frase curta", () => {
    for (const key of ["list", "link", "create", "detail"] as const) {
      expect(helpTooltips[key].length, key).toBeLessThanOrEqual(SECTION_MAX);
    }
  });

  it("nenhum tooltip passa do teto de campo", () => {
    const oversized = entries.filter((entry) => entry.text.length > FIELD_MAX);
    expect(oversized).toEqual([]);
  });

  it("cobre anexar/colar/arrastar na abertura e na resposta", () => {
    expect(helpTooltips.createUi.attach).toMatch(/anex|arrastar/i);
    expect(helpTooltips.createUi.description).toMatch(/cole|clipe|anex|arrastar|@|mencion/i);
    expect(helpTooltips.detailUi.attach).toMatch(/anex|arrastar/i);
    expect(helpTooltips.detailUi.reply).toMatch(/cole|clipe|anex|arrastar|@|mencion/i);
    expect(helpTooltips.detailUi.attachments).toMatch(/arquivo/i);
  });

  it("cobre atribuição de técnico na abertura e no detalhe", () => {
    expect(helpTooltips.createUi.assignee).toMatch(/técnico|perfil/i);
    expect(helpTooltips.detailUi.assignee).toMatch(/técnico|atribu/i);
    expect(helpTooltips.detailUi.assigneeAction).toMatch(/atribui/i);
  });

  it("cobre ciclo H10 aceitar/recusar/satisfação", () => {
    expect(helpTooltips.detailUi.acceptSolution).toMatch(/aceit|fecha/i);
    expect(helpTooltips.detailUi.rejectSolution).toMatch(/recus|reabre/i);
    expect(helpTooltips.detailUi.submitSatisfaction).toMatch(/nota|1 a 5|avalia/i);
  });

  it("não reintroduz o bloco filters órfão da FiltersRow antiga", () => {
    expect(helpTooltips).not.toHaveProperty("filters");
  });
});
