import { describe, expect, it } from "vitest";

import {
  CATALOG_ENTRIES,
  filterCatalogEntries,
  getCatalogEntryById,
  listCatalogFamilies,
} from "./componentRegistry";

describe("componentRegistry", () => {
  it("mantém ids únicos", () => {
    const ids = CATALOG_ENTRIES.map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("lista famílias na ordem de primeira aparição", () => {
    const families = listCatalogFamilies();
    expect(families[0]).toBe("help");
    expect(families).toContain("sandbox");
  });

  it("filtra por busca e família", () => {
    const helpOnly = filterCatalogEntries("", "help");
    expect(helpOnly.every((e) => e.family === "help")).toBe(true);
    expect(filterCatalogEntries("HelpTooltip").some((e) => e.exportName === "HelpTooltip")).toBe(
      true,
    );
  });

  it("resolve entrada por id", () => {
    expect(getCatalogEntryById("help.HelpTooltip")?.title).toBe("HelpTooltip");
  });
});
