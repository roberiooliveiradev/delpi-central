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
    expect(section).toMatch(
      /DeckRibbonTilePopover[\s\S]*KpiColorsStylesMenu|inSectionPopover[\s\S]*KpiColorsStylesMenu/,
    );
  });

  it("menu KPI usa thumbs estilo gráfico e não mistura tom em aparência", () => {
    const menu = readFileSync(join(here, "KpiColorsStylesMenu.tsx"), "utf8");
    expect(menu).toContain("td-chart-style-menu__style-thumb--kpi-");
    expect(menu).toContain("td-chart-style-menu__hint");
    expect(menu).toContain("KPI_TONE_OPTIONS");
    expect(menu).toContain("KPI_APPEARANCE_RECIPES");
    const appearanceBlock = menu.slice(
      menu.indexOf("Estilos de aparência"),
      menu.indexOf(">Tom</h4>"),
    );
    expect(appearanceBlock).toContain("KPI_APPEARANCE_RECIPES");
    expect(appearanceBlock).toContain("style-thumb--kpi-${recipe.id}");
    expect(appearanceBlock).not.toContain("KPI_TONE_OPTIONS");
    expect(appearanceBlock).not.toContain("Positivo");
  });

  it("Organizar usa rótulo curto Igualar (evita ellipsis Mesmo tam…)", () => {
    const organize = readFileSync(
      join(here, "formatRibbon/FormatRibbonOrganizeGroup.tsx"),
      "utf8",
    );
    expect(organize).toContain('label="Igualar"');
    expect(organize).toContain("menuAriaLabel={H.sameSize}");
  });
});
