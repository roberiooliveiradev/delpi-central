import { describe, expect, it } from "vitest";

import {
  CATALOG_ENTRIES,
  filterCatalogEntries,
  getCatalogEntryById,
  listCatalogFamilies,
  VISUAL_COMPONENTS,
} from "./componentRegistry";

describe("componentRegistry", () => {
  it("mantém ids únicos", () => {
    const ids = CATALOG_ENTRIES.map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("cobre 100% dos componentes visuais inventariados", () => {
    const inCatalog = new Set(CATALOG_ENTRIES.map((e) => e.exportName));
    const missing = VISUAL_COMPONENTS.filter((c) => !inCatalog.has(c.exportName)).map(
      (c) => c.exportName,
    );
    expect(missing).toEqual([]);
    expect(CATALOG_ENTRIES.length).toBeGreaterThanOrEqual(VISUAL_COMPONENTS.length);
  });

  it("lista famílias na ordem de primeira aparição", () => {
    const families = listCatalogFamilies();
    expect(families[0]).toBe("help");
    expect(families).toContain("data");
    expect(families).toContain("menu");
  });

  it("filtra por busca e família", () => {
    const dataOnly = filterCatalogEntries("", "data");
    expect(dataOnly.every((e) => e.family === "data")).toBe(true);
    expect(filterCatalogEntries("DataTable").some((e) => e.exportName === "DataTable")).toBe(true);
  });

  it("resolve entrada por id", () => {
    expect(getCatalogEntryById("help.HelpTooltip")?.title).toBe("HelpTooltip");
    expect(getCatalogEntryById("data.DataTable")?.exportName).toBe("DataTable");
  });
});
