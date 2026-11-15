/**
 * U12 W2 — teste estrutural: toda DataTableSection do MFE deve ter
 * columnPreferencesKey e ao menos uma coluna sortable (exceto lista nomeada).
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";

const SRC = join(__dirname, "..");

/**
 * Exceções nomeadas (T7 / matriz): HTML local ou DataTableSection ainda
 * fora do padrão — motivo registrado na matriz W0.
 * Paths relativos a `src/` (features/…).
 */
const EXCEPTIONS: Record<string, string> = {
  "features/closing/ReportsMatrixPanel.tsx":
    "matriz R01–R15 (não lista de registros)",
  "features/closing/ReportSharedSections.tsx":
    "tabelas de conciliação/corte (T7)",
  "features/closing/P3CutoffPanel.tsx": "tabela de corte P3 (T7)",
  "features/closing/PackagesPage.tsx":
    "cf-pend-table legado → migrar em fatia própria",
  "features/closing/PendenciesPage.tsx":
    "cf-pend-table legado → migrar em fatia própria",
};

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name.startsWith(".")) continue;
    const path = join(dir, name);
    const st = statSync(path);
    if (st.isDirectory()) walk(path, out);
    else if (/\.(tsx|ts)$/.test(name) && !name.includes(".test.")) out.push(path);
  }
  return out;
}

describe("U12 W2 DataTableSection structure", () => {
  it("exige columnPreferencesKey + sortable em cada DataTableSection (exceto lista)", () => {
    const files = walk(SRC);
    const failures: string[] = [];
    for (const file of files) {
      const rel = relative(SRC, file).replace(/\\/g, "/");
      if (EXCEPTIONS[rel]) continue;
      const text = readFileSync(file, "utf8");
      if (!text.includes("DataTableSection")) continue;
      // Uma ou mais seções no arquivo
      const sectionCount =
        (text.match(/<DataTableSection(?:<|[\s>])/g) || []).length;
      if (sectionCount === 0) continue;
      const prefs = (text.match(/columnPreferencesKey=/g) || []).length;
      const cards = (text.match(/renderCard=/g) || []).length;
      const sortable = (text.match(/sortable:\s*true/g) || []).length;
      if (prefs < sectionCount) {
        failures.push(
          `${rel}: ${sectionCount} DataTableSection, ${prefs} columnPreferencesKey`,
        );
      }
      if (cards < sectionCount) {
        failures.push(
          `${rel}: ${sectionCount} DataTableSection, ${cards} renderCard`,
        );
      }
      if (sortable < 1) {
        failures.push(`${rel}: nenhuma coluna sortable: true`);
      }
    }
    expect(failures, failures.join("\n")).toEqual([]);
  });

  it("documenta exceções nomeadas", () => {
    expect(Object.keys(EXCEPTIONS).length).toBeGreaterThan(0);
  });
});
