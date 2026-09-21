import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { mapDeliveriesFetchError } from "./content";
import {
  buildListSearchParams,
  createDefaultQuery,
  nextServerSort,
} from "./query";

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

describe("Deliveries feature (E9.S3)", () => {
  it("App liga página real em vez do placeholder", () => {
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    expect(app).toMatch(/DeliveriesPage/);
    expect(app).toMatch(/view === "deliveries"/);
    expect(app).not.toMatch(/deliveries:\s*\{\s*title:\s*"Entregas"/);
  });

  it("cliente fala só com supplies-api /deliveries/late", () => {
    const api = readFileSync(join(dir, "api.ts"), "utf8");
    expect(api).toMatch(/suppliesApiUrl\(`\/deliveries\/late/);
    expect(api).toMatch(/listLateDeliveries/);
    expect(api).not.toMatch(/api-delpi/);
    expect(api).not.toMatch(/apiDelpiUrl/);
    expect(api).not.toMatch(/purchase-orders\//);
  });

  it("feature não aponta api-delpi nem calcula DIAS localmente", () => {
    for (const file of collectSourceFiles(dir)) {
      const text = readFileSync(file, "utf8");
      expect(text).not.toMatch(/api-delpi/);
      expect(text).not.toMatch(/apiDelpiUrl/);
      expect(text).not.toMatch(/days_diff\s*[<>=]/);
      expect(text).not.toMatch(/DIAS/);
    }
  });

  it("página kit-first com filtros, estados e sem drill", () => {
    const page = readFileSync(join(dir, "DeliveriesPage.tsx"), "utf8");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("DeliveriesFilters");
    expect(page).toContain("SuppliesSectionCard");
    expect(page).toContain("mapDeliveriesFetchError");
    expect(page).toContain("listLateDeliveries");
    expect(page).toContain("SuppliesEmptyState");
    expect(page).toContain("SuppliesLoadingCard");
    expect(page).toContain("SuppliesStateBanner");
    expect(page).toContain("DeliveriesListTable");
    expect(page).not.toMatch(/buildPurchaseOrderDetailPath/);
    expect(page).not.toMatch(/onSelectRow/);
    expect(page).not.toMatch(/navigatePluginPath/);

    const table = readFileSync(join(dir, "DeliveriesListTable.tsx"), "utf8");
    expect(table).toContain("SuppliesDataTable");
    expect(table).toContain("SuppliesCompactPagination");
    expect(table).toContain("SuppliesStatusBadge");
    expect(table).toContain("nextServerSort");
    expect(table).not.toMatch(/onRowClick/);
    expect(table).not.toMatch(/SuppliesEntityLink/);
    expect(table).not.toMatch(/buildPurchaseOrderDetailPath/);
    expect(table).not.toMatch(/ExcelExport/);
  });

  it("filtros P0: unidade, período digitação, status; page=1 ao mudar", () => {
    const filters = readFileSync(join(dir, "DeliveriesFilters.tsx"), "utf8");
    expect(filters).toContain("SuppliesMultiSelectField");
    expect(filters).toContain("SuppliesSelectField");
    expect(filters).toContain("SuppliesDateField");
    expect(filters).toContain("start_date");
    expect(filters).toContain("end_date");
    expect(filters).toContain("page: 1");
    expect(filters).toContain("SP_HELP.deliveriesPeriod");
    expect(filters).not.toMatch(/\border_number\b/);
    expect(filters).not.toMatch(/\bbusca\b/i);
    expect(filters).not.toMatch(/ExcelExport|exportPurchase|onExport/);
  });

  it("Todas não envia branch; sort reseta page", () => {
    const params = buildListSearchParams(createDefaultQuery());
    expect(params.getAll("branch")).toEqual([]);
    expect(params.get("status")).toBe("late");

    const sorted = nextServerSort(
      { ...createDefaultQuery(), page: 5, sort_by: "branch", sort_dir: "asc" },
      "branch",
    );
    expect(sorted?.page).toBe(1);
  });

  it("403 mapeado sem sugerir permission nova", () => {
    const text = mapDeliveriesFetchError("403 Forbidden");
    expect(text).not.toMatch(/supplies\.deliveries/);
    expect(text).not.toMatch(/permission de entregas/i);
  });

  it("estados loading/empty/error/403/retry presentes na página", () => {
    const page = readFileSync(join(dir, "DeliveriesPage.tsx"), "utf8");
    const content = readFileSync(join(dir, "content.ts"), "utf8");
    expect(page).toContain("SuppliesLoadingCard");
    expect(page).toContain("SuppliesEmptyState");
    expect(page).toContain("SuppliesStateBanner");
    expect(page).toContain("C.retry");
    expect(page).toContain("mapDeliveriesFetchError");
    expect(page).toContain("items.length === 0");
    expect(page).toContain("emptyClearAction");
    expect(page).toContain('navigatePluginView("help"');
    expect(page).toContain('addEventListener("popstate"');
    expect(page).toContain("pushState");
    expect(content).toContain("emptyTitle");
    expect(content).toContain("forbiddenUnit");
    expect(content).toContain("retry");
    expect(content).not.toMatch(/permission de entregas/i);
  });

  it("summary só de campos do contrato (sem KPI inventado)", () => {
    const page = readFileSync(join(dir, "DeliveriesPage.tsx"), "utf8");
    expect(page).toContain("summary.total_lines");
    expect(page).toContain("late_lines");
    expect(page).toContain("on_time_lines");
    expect(page).not.toMatch(/purchase_order_otd_pct/);
    expect(page).not.toMatch(/late_percentage/);
  });

  it("Help período explicita digitação; sem drill na copy da página", () => {
    const help = readFileSync(join(dir, "../../content/helpTooltips.ts"), "utf8");
    expect(help).toMatch(/deliveriesPeriod:[\s\S]*digitação\/entrada/);
    expect(help).toMatch(/deliveries:[\s\S]*matéria-prima/);
    expect(help).not.toMatch(/atrasos do dia/);
    const page = readFileSync(join(dir, "DeliveriesPage.tsx"), "utf8");
    expect(page).not.toMatch(/clique no pedido|abrir a ficha/i);
  });
});
