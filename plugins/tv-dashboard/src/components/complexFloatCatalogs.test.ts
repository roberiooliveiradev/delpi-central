import { describe, expect, it } from "vitest";
import { KPI_ELEMENT_CATALOG, TABLE_ELEMENT_CATALOG } from "@delpi/tv-dashboard-presentation";

import { TABLE_STYLE_RECIPES } from "../content/tableStyleRecipes";

/**
 * Smoke: catálogos usados pelos menus da float (+ / pincel) não ficam vazios.
 */
describe("float toolbar catalogs", () => {
  it("KPI e tabela têm elementos para o botão +", () => {
    expect(KPI_ELEMENT_CATALOG.length).toBeGreaterThan(0);
    expect(TABLE_ELEMENT_CATALOG.length).toBeGreaterThan(0);
  });

  it("tabela tem recipes para o pincel", () => {
    expect(TABLE_STYLE_RECIPES.length).toBeGreaterThan(0);
  });
});
