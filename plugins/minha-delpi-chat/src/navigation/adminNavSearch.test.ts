import { describe, expect, it } from "vitest";

import { buildAdminNavTree } from "./adminNavTree";
import { searchAdminContentHits, searchAdminNavigation } from "./adminNavSearch";

describe("adminNavSearch", () => {
  it("encontra blocos de conteúdo por palavra-chave", () => {
    const hits = searchAdminContentHits("chips");

    expect(hits.some((hit) => hit.title.includes("Interatividade"))).toBe(true);
    expect(hits[0]?.target).toEqual({ section: "quality", subTab: "metrics" });
  });

  it("encontra rbac no painel", () => {
    const hits = searchAdminContentHits("rbac");

    expect(hits.some((hit) => hit.id === "overview-rbac")).toBe(true);
  });

  it("filtra árvore e retorna hits de conteúdo juntos", () => {
    const tree = buildAdminNavTree();
    const result = searchAdminNavigation(tree, "vocabulário");

    expect(result.hasQuery).toBe(true);
    expect(result.contentHits.length).toBeGreaterThan(0);
    expect(
      result.tree.some((section) => section.key === "knowledge"),
    ).toBe(true);
  });
});
