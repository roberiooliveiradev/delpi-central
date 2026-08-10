import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

/**
 * «Colunas do visual» — HostContainedDialog centralizado (paridade ChartSelectDataModal).
 */
describe("TableColumnsSelectModal contract", () => {
  it("usa HostContainedDialog e TableColumnsMultiSelect", () => {
    const source = readFileSync(join(here, "TableColumnsSelectModal.tsx"), "utf8");
    expect(source).toContain("HostContainedDialog");
    expect(source).toContain("TableColumnsMultiSelect");
    expect(source).toContain('title="Colunas do visual"');
    expect(source).toContain("reconcileTablePartsForVisibleKeys");
  });

  it("float abre o modal em Colunas do visual (não só scroll da sidebar)", () => {
    const source = readFileSync(join(here, "TableSelectionFloatToolbar.tsx"), "utf8");
    expect(source).toContain("TableColumnsSelectModal");
    expect(source).toContain("setColumnsModalOpen(true)");
    expect(source).toMatch(/actionId === "columns"[\s\S]*?setColumnsModalOpen\(true\)/);
  });
});
