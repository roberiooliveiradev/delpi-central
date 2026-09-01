import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function listSourceFiles(dir: string): string[] {
  const entries = readdirSync(dir);
  const files: string[] = [];
  for (const entry of entries) {
    const path = join(dir, entry);
    const stat = statSync(path);
    if (stat.isDirectory()) {
      files.push(...listSourceFiles(path));
      continue;
    }
    if (/\.(tsx|ts)$/.test(entry) && !entry.endsWith(".test.ts") && !entry.endsWith(".test.tsx")) {
      files.push(path);
    }
  }
  return files;
}

function readRelative(pathFromSrc: string): string {
  return readFileSync(join(root, pathFromSrc), "utf8");
}

describe("production-pulse kit contracts", () => {
  const sources = listSourceFiles(root).map((abs) => ({
    rel: relative(root, abs),
    source: readFileSync(abs, "utf8"),
  }));

  it("usa PpDataTable canônico — nunca DataTable cru do kit", () => {
    for (const { rel, source } of sources) {
      if (rel === "components/data/dataTableUi.tsx") continue;
      expect(source, rel).not.toMatch(/\bDataTable\b.*@delpi\/plugin-ui/);
      expect(source, rel).not.toMatch(/dataTableBemClasses\s*\(/);
    }
    expect(readRelative("components/DeviceTable.tsx")).toMatch(/PpDataTable/);
    expect(readRelative("components/data/dataTableUi.tsx")).toMatch(/labels={LABELS}/);
    expect(readRelative("components/data/dataTableUi.tsx")).toMatch(/loadingMessage:/);
  });

  it("usa FiltersRow canônico — sem flex externo que encolhe o shell", () => {
    for (const { rel, source } of sources) {
      expect(source, rel).not.toMatch(/pp-filters-wrap/);
      expect(source, rel).not.toMatch(/createFilterBarShell/);
    }
    const filtersBar = readRelative("components/DeviceFiltersBar.tsx");
    expect(filtersBar).toMatch(/PpFiltersRow/);
    expect(filtersBar).toMatch(/trailing=/);
    expect(filtersBar).not.toMatch(/PpFilterBarShell/);
    expect(readRelative("components/data/filtersUi.tsx")).toMatch(/PpFiltersRow/);
  });

  it("FilterInputField declara type explícito no painel", () => {
    const filtersBar = readRelative("components/DeviceFiltersBar.tsx");
    expect(filtersBar).toMatch(/type="search"/);
    expect(filtersBar).not.toMatch(/onChange=\{\(event\)/);
  });

  it("StateBox usa action singular do kit — não actions", () => {
    for (const { rel, source } of sources) {
      if (!source.includes("PpStateBox")) continue;
      const withoutPageHero = source.replace(/<PpPageHero[\s\S]*?\/>/g, "");
      expect(withoutPageHero, rel).not.toMatch(/<PpStateBox[\s\S]*?\bactions=/);
    }
  });
});
