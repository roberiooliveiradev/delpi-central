import { describe, expect, it } from "vitest";

import { searchBpmnPalette } from "../model/bpmnNodeCatalog";

describe("searchBpmnPalette", () => {
  it("retorna vazio sem query", () => {
    expect(searchBpmnPalette("")).toEqual([]);
    expect(searchBpmnPalette("   ")).toEqual([]);
  });

  it("encontra por rótulo sem acento e prioriza prefixo", () => {
    const hits = searchBpmnPalette("tempor");
    expect(hits.some((hit) => hit.type === "start_timer")).toBe(true);
    expect(hits[0]?.label.toLowerCase()).toContain("tempor");
  });

  it("desambigua Mensagem pela categoria", () => {
    const hits = searchBpmnPalette("mensagem");
    const categories = new Set(hits.map((hit) => hit.category));
    expect(categories.size).toBeGreaterThan(1);
    expect(hits.every((hit) => hit.categoryLabel.length > 0)).toBe(true);
  });

  it("respeita o limite", () => {
    expect(searchBpmnPalette("a", 3)).toHaveLength(3);
  });
});
