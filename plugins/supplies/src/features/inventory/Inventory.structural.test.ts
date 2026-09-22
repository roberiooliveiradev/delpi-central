import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { formatMoneyBr, formatQuantity } from "./query";
import { INVENTORY_CONTENT } from "./content";

const dir = dirname(fileURLToPath(import.meta.url));

function collectSourceFiles(root: string): string[] {
  const entries = readdirSync(root);
  const files: string[] = [];
  for (const entry of entries) {
    const full = join(root, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      files.push(...collectSourceFiles(full));
      continue;
    }
    if (/\.(ts|tsx)$/.test(entry) && !/\.(test|spec)\.(ts|tsx)$/.test(entry)) {
      files.push(full);
    }
  }
  return files;
}

describe("Inventory feature (E10.S3)", () => {
  it("App liga InventoryPage e remove placeholder de inventory", () => {
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    expect(app).toMatch(/InventoryPage/);
    expect(app).toMatch(/view === "inventory"/);
    expect(app).not.toMatch(/inventory:\s*\{\s*title:\s*"Estoque"/);
    expect(app).toMatch(/safety_stock:\s*\{/);
    expect(app).toMatch(/products:\s*\{/);
    expect(app).toMatch(/suppliers:\s*\{/);
  });

  it("cliente fala só com supplies-api inventory stock-balances", () => {
    const api = readFileSync(join(dir, "api.ts"), "utf8");
    expect(api).toMatch(/\/inventory\/stock-balances\/summary/);
    expect(api).toMatch(/\/inventory\/stock-balances\/items/);
    expect(api).toMatch(/suppliesApiUrl/);
    expect(api).not.toMatch(/api-delpi/);
    expect(api).not.toMatch(/only_positive/);
  });

  it("feature não aponta api-delpi nem esconde zero/negativo", () => {
    for (const file of collectSourceFiles(dir)) {
      const text = readFileSync(file, "utf8");
      expect(text).not.toMatch(/api-delpi/);
      expect(text).not.toMatch(/apiDelpiUrl/);
      expect(text).not.toMatch(/only_positive/);
      expect(text).not.toMatch(/quantity\s*>\s*0/);
      expect(text).not.toMatch(/Math\.max\(\s*[^,]+,\s*0\s*\)/);
      expect(text).not.toMatch(/filter\(\s*\([^)]*\)\s*=>\s*[^)]*quantity/);
    }
  });

  it("página kit-first com hero P0, filtros, estados e sem drill", () => {
    const page = readFileSync(join(dir, "InventoryPage.tsx"), "utf8");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("InventoryFilters");
    expect(page).toContain("SuppliesSectionCard");
    expect(page).toContain("listInventoryStockBalances");
    expect(page).toContain("getInventoryStockBalancesSummary");
    expect(page).toContain("SuppliesEmptyState");
    expect(page).toContain("SuppliesLoadingCard");
    expect(page).toContain("SuppliesStateBanner");
    expect(page).toContain("InventoryListTable");
    expect(page).toContain("heroProducts");
    expect(page).toContain("product_count");
    expect(page).toContain("warehouse_count");
    expect(page).toContain("total_stock_value");
    expect(page).not.toMatch(/total_quantity/);
    expect(page).not.toMatch(/total_stock_value_vatu1/);
    expect(page).not.toMatch(/onSelectRow/);
    expect(page).not.toMatch(/\/products/);

    const table = readFileSync(join(dir, "InventoryListTable.tsx"), "utf8");
    expect(table).toContain("SuppliesDataTable");
    expect(table).toContain("SuppliesCompactPagination");
    expect(table).toContain("formatWarehouseDisplay");
    expect(table).toContain("formatUnitOfMeasure");
    expect(table).toContain("nextServerSort");
    expect(table).not.toMatch(/onRowClick/);
  });

  it("copy empty não fala em saldo positivo", () => {
    expect(INVENTORY_CONTENT.emptyMessage).not.toMatch(/positivo/i);
    expect(INVENTORY_CONTENT.emptyMessage).toMatch(/posição de estoque/i);
    expect(INVENTORY_CONTENT.colQuantity).toBe("Saldo físico");
  });

  it("hero usa formatMoneyBr e formatQuantity preserva sinal", () => {
    expect(formatMoneyBr(12.5)).toMatch(/R\$/);
    expect(formatQuantity(-1)).toMatch(/-1/);
  });
});
