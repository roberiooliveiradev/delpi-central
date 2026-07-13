import { describe, expect, it } from "vitest";

import {
  buildCatalogEntries,
  CATALOG_ENTRIES,
  filterCatalogEntries,
  getCatalogEntryById,
  listCatalogFamilies,
  listRecentEntries,
  resolveLifecycle,
  sortByUpdatedAtDesc,
  VISUAL_COMPONENTS,
} from "./componentRegistry";
import { isIsoDate } from "./catalogLifecycle";
import { CATALOG_EXPAND_DATE, PACKAGE_INITIAL_DATE } from "./visualComponents";
import type { CatalogEntry } from "./types";

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

  it("exige addedAt ISO válido em todo VISUAL_COMPONENTS", () => {
    for (const spec of VISUAL_COMPONENTS) {
      expect(isIsoDate(spec.addedAt), `${spec.exportName}.addedAt`).toBe(true);
      if (spec.updatedAt !== undefined) {
        expect(isIsoDate(spec.updatedAt), `${spec.exportName}.updatedAt`).toBe(true);
        expect(spec.updatedAt >= spec.addedAt, `${spec.exportName}: updatedAt >= addedAt`).toBe(
          true,
        );
      }
    }
  });

  it("merge metadados do inventário nas entradas do catálogo", () => {
    const dataTable = getCatalogEntryById("data.DataTable");
    expect(dataTable?.addedAt).toBe(PACKAGE_INITIAL_DATE);
    expect(dataTable?.updatedAt).toBe(CATALOG_EXPAND_DATE);
    expect(dataTable?.changeNote).toMatch(/LMPS/i);
    expect(dataTable?.lifecycle).toBeTruthy();
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

  it("filtra por lifecycle new/updated e ordena por updatedAt desc", () => {
    const fixture: CatalogEntry[] = [
      {
        id: "a.OldStable",
        family: "help",
        exportName: "OldStable",
        title: "OldStable",
        demos: [{ id: "d", label: "d", render: () => null }],
        addedAt: "2025-01-01",
        updatedAt: "2025-01-01",
        lifecycle: "stable",
      },
      {
        id: "a.BrandNew",
        family: "help",
        exportName: "BrandNew",
        title: "BrandNew",
        demos: [{ id: "d", label: "d", render: () => null }],
        addedAt: "2026-07-01",
        updatedAt: "2026-07-01",
        lifecycle: "new",
      },
      {
        id: "a.RecentlyUpdated",
        family: "data",
        exportName: "RecentlyUpdated",
        title: "RecentlyUpdated",
        demos: [{ id: "d", label: "d", render: () => null }],
        addedAt: "2025-01-01",
        updatedAt: "2026-07-10",
        changeNote: "fix",
        lifecycle: "updated",
      },
      {
        id: "a.OlderUpdate",
        family: "data",
        exportName: "OlderUpdate",
        title: "OlderUpdate",
        demos: [{ id: "d", label: "d", render: () => null }],
        addedAt: "2025-01-01",
        updatedAt: "2026-07-05",
        lifecycle: "updated",
      },
    ];

    const news = filterCatalogEntries("", "all", "new", fixture);
    expect(news.map((e) => e.exportName)).toEqual(["BrandNew"]);

    const updated = filterCatalogEntries("", "all", "updated", fixture);
    expect(updated.map((e) => e.exportName)).toEqual(["RecentlyUpdated", "OlderUpdate"]);
  });

  it("listRecentEntries e sortByUpdatedAtDesc", () => {
    const entries = buildCatalogEntries(CATALOG_EXPAND_DATE);
    const recent = listRecentEntries(entries);
    expect(recent.every((e) => e.lifecycle === "new" || e.lifecycle === "updated")).toBe(true);
    expect(sortByUpdatedAtDesc(entries)[0]?.updatedAt >= sortByUpdatedAtDesc(entries).at(-1)!.updatedAt).toBe(
      true,
    );
  });

  it("resolve entrada por id", () => {
    expect(getCatalogEntryById("help.HelpTooltip")?.title).toBe("HelpTooltip");
    expect(getCatalogEntryById("data.DataTable")?.exportName).toBe("DataTable");
  });
});

describe("resolveLifecycle", () => {
  it("marca new dentro de 30 dias desde addedAt", () => {
    expect(resolveLifecycle("2026-07-01", undefined, "2026-07-13")).toBe("new");
    expect(resolveLifecycle("2026-06-13", undefined, "2026-07-13")).toBe("new");
  });

  it("marca updated quando não é new e updatedAt recente", () => {
    expect(resolveLifecycle("2026-01-01", "2026-07-10", "2026-07-13")).toBe("updated");
  });

  it("marca stable fora das janelas", () => {
    expect(resolveLifecycle("2026-01-01", undefined, "2026-07-13")).toBe("stable");
    expect(resolveLifecycle("2026-01-01", "2026-06-01", "2026-07-13")).toBe("stable");
  });

  it("prioriza new sobre updated quando ambos se aplicariam", () => {
    expect(resolveLifecycle("2026-07-01", "2026-07-10", "2026-07-13")).toBe("new");
  });
});
