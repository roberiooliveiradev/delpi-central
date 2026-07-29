import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * Regressão: Design/Layout tipados sumiam com coluna/série selecionada porque
 * SelectionTypedWithTailHost intersectava `only` com resolveSelectionSections
 * (modo parte → só partFormat). Sidebar ficava só com lista de colunas.
 */
describe("SelectionTypedWithTailHost declared sections", () => {
  it("usa sectionSource=declared para não filtrar Design no modo parte", () => {
    const source = readFileSync(resolve(__dirname, "./SelectionCommonHosts.tsx"), "utf8");
    expect(source).toContain('sectionSource="declared"');
    expect(source).toMatch(/SelectionTypedWithTailHost[\s\S]*sectionSource="declared"/);
  });

  it("SelectionSectionsHost honra sectionSource declared sem intersect resolve", () => {
    const source = readFileSync(resolve(__dirname, "./SelectionSectionsHost.tsx"), "utf8");
    expect(source).toContain('sectionSource = "resolved"');
    expect(source).toMatch(
      /sectionSource === "declared"[\s\S]*only\.filter\(\(id\) => SHARED_HOST_SECTIONS\.has\(id\)\)/,
    );
  });
});
