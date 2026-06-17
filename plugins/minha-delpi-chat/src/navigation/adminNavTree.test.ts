import { describe, expect, it } from "vitest";

import {
  buildAdminNavTree,
  filterAdminNavTree,
  getAdminNavBreadcrumb,
  isAdminNavTargetActive,
} from "./adminNavTree";

describe("adminNavTree", () => {
  it("monta árvore com folhas aninhadas em aprendizagem", () => {
    const tree = buildAdminNavTree();
    const knowledge = tree.find((item) => item.key === "knowledge");
    const learning = knowledge?.nodes.find((node) => node.id === "knowledge/learning");

    expect(learning?.children).toHaveLength(6);
    expect(learning?.children?.[0]?.label).toBe("Pipeline");
    expect(learning?.children?.[1]?.label).toBe("Candidatos");
  });

  it("filtra por texto da busca em nível profundo", () => {
    const filtered = filterAdminNavTree(buildAdminNavTree(), "regressao");
    const knowledge = filtered.find((item) => item.key === "knowledge");
    const learning = knowledge?.nodes.find((node) => node.id === "knowledge/learning");

    expect(learning?.children?.some((child) => child.label === "Regressão")).toBe(true);
  });

  it("filtra nó por conteúdo indexado (ex.: chips em métricas)", () => {
    const filtered = filterAdminNavTree(buildAdminNavTree(), "chips");
    const quality = filtered.find((item) => item.key === "quality");
    const metrics = quality?.nodes.find((node) => node.id === "quality/metrics");

    expect(metrics).toBeDefined();
  });

  it("identifica alvo ativo com página", () => {
    expect(
      isAdminNavTargetActive(
        { section: "knowledge", subTab: "learning", page: "memory" },
        { section: "knowledge", subTab: "learning", page: "memory" },
      ),
    ).toBe(true);
  });

  it("formata breadcrumb com três níveis", () => {
    expect(
      getAdminNavBreadcrumb({
        section: "knowledge",
        subTab: "learning",
        page: "vocabulary",
      }),
    ).toBe("Conhecimento · Aprendizagem · Vocabulário");
  });
});
