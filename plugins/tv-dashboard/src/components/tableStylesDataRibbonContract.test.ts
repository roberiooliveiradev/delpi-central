import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("table styles/data ribbon parity", () => {
  it("ribbon e float compartilham TableStylesMenu e TableDataMenu", () => {
    const sections = readFileSync(join(here, "selectionSections/TableDesignSections.tsx"), "utf8");
    const floatToolbar = readFileSync(join(here, "TableSelectionFloatToolbar.tsx"), "utf8");
    expect(sections).toContain("TableStylesMenu");
    expect(sections).toContain("TableDataMenu");
    expect(sections).toContain("Alterar estilos");
    expect(sections).toContain("Selecionar dados");
    expect(floatToolbar).toContain("TableStylesMenu");
    expect(floatToolbar).toContain("TableDataMenu");
    expect(floatToolbar).not.toContain("FloatChecklist");
  });

  it("float não aninha outro popover--style (scroll duplo)", () => {
    const floatToolbar = readFileSync(join(here, "TableSelectionFloatToolbar.tsx"), "utf8");
    expect(floatToolbar).not.toMatch(/td-chart-float__popover--style/);
    const css = readFileSync(join(here, "../index.css"), "utf8");
    expect(css).toMatch(
      /\.td-chart-float__popover--style\s*\{[^}]*max-height:\s*min\(calc\(100dvh - 24px\),\s*92vh\)/s,
    );
    expect(css).toMatch(
      /\.td-chart-float__popover \.td-chart-float__popover\s*\{[^}]*overflow:\s*visible/s,
    );
  });
});
