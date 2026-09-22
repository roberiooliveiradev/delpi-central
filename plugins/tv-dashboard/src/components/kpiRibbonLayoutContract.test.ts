import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

/**
 * Faixa Elemento do KPI — molde table/chart: tile + popover fora da band de 112px.
 * Regressão: embutir `KpiColorsStylesMenu` inline quebrava a ribbon (overflow / TOM cortado).
 */
describe("kpi ribbon layout contract", () => {
  it("kpiAppearance usa DeckRibbonTilePopover e não embute o menu na band", () => {
    const section = readFileSync(
      join(here, "selectionSections/KpiAppearanceSection.tsx"),
      "utf8",
    );
    expect(section).toContain("DeckRibbonTilePopover");
    expect(section).toContain('groupId="kpi-appearance"');
    expect(section).toContain('label="Alterar estilos"');
    expect(section).toContain("useRibbonSectionPopoverSurface");
    expect(section).not.toContain("td-deck-ribbon__kpi-appearance");
    /* Menu só dentro do popover / surface colapsada — não como filho direto da band. */
    expect(section).toMatch(
      /DeckRibbonTilePopover[\s\S]*KpiColorsStylesMenu|inSectionPopover[\s\S]*KpiColorsStylesMenu/,
    );
  });
});
