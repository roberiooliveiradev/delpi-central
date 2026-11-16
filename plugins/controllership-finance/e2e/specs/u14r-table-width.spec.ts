/**
 * U14R H2 — tabela de ocorrências sem scroll horizontal em 1440
 * com storage limpo e com preferência v1 antiga (field:true).
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

import { loginAs, openEntryAuditHome } from "../helpers";

const ARTIFACT_DIR =
  process.env.CF_E2E_ARTIFACT_DIR || path.join("/tmp", "ui-review-u14r");
const OCC_V1 = "controllership-finance:entry-audit:occurrences:columns:v1";
const OCC_V2 = "controllership-finance:entry-audit:occurrences:columns:v2";

async function openFirstAnalysis(page: Page): Promise<boolean> {
  await openEntryAuditHome(page);
  const row = page.locator("table tbody tr").first();
  if (!(await row.isVisible().catch(() => false))) return false;
  await row.click();
  await expect(page).toHaveURL(/\/entry-audit\/analyses\//, { timeout: 60_000 });
  await expect(page.getByRole("tab", { name: /Ocorrências/i })).toBeVisible({
    timeout: 60_000,
  });
  return true;
}

async function measureTable(page: Page): Promise<{
  scrollWidth: number;
  clientWidth: number;
  prefsKeyPresent: { v1: boolean; v2: boolean };
}> {
  return page.evaluate(
    ({ v1, v2 }) => {
      const root = document.querySelector(".cf-entry-audit-occurrences-table");
      const table =
        root?.querySelector("table") ??
        document.querySelector(
          '[class*="data-table"] table, .cf-data-table table, table',
        ) ??
        document.querySelector("table");
      const wrap =
        (root?.querySelector(
          '[class*="table-wrap"]',
        ) as HTMLElement | null) ??
        (table?.closest('[class*="table-wrap"]') as HTMLElement | null) ??
        (table?.parentElement as HTMLElement | null);
      if (!wrap) throw new Error("tabela não encontrada");
      return {
        scrollWidth: wrap.scrollWidth,
        clientWidth: wrap.clientWidth,
        prefsKeyPresent: {
          v1: Boolean(localStorage.getItem(v1)),
          v2: Boolean(localStorage.getItem(v2)),
        },
      };
    },
    { v1: OCC_V1, v2: OCC_V2 },
  );
}

test.describe("U14R H2 — largura da tabela de ocorrências", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "cf_manage");
  });

  test("1440 storage limpo: scrollWidth ≤ clientWidth", async ({ page }) => {
    test.skip(test.info().project.name !== "desktop", "desktop only");
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.addInitScript(() => {
      localStorage.removeItem(
        "controllership-finance:entry-audit:occurrences:columns:v1",
      );
      localStorage.removeItem(
        "controllership-finance:entry-audit:occurrences:columns:v2",
      );
    });
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise HML");
    const report = await measureTable(page);
    fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
    fs.writeFileSync(
      path.join(ARTIFACT_DIR, "table-width-clean.json"),
      JSON.stringify(report, null, 2),
    );
    expect(report.scrollWidth).toBeLessThanOrEqual(report.clientWidth + 1);
  });

  test("1440 com v1 antiga (field:true): v2 aplica e cabe", async ({ page }) => {
    test.skip(test.info().project.name !== "desktop", "desktop only");
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.addInitScript(() => {
      localStorage.setItem(
        "controllership-finance:entry-audit:occurrences:columns:v1",
        JSON.stringify({
          severity: true,
          document: true,
          supplier: true,
          rule: true,
          field: true,
          protheus: true,
          xml: true,
          difference: true,
          status: true,
        }),
      );
    });
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise HML");
    const report = await measureTable(page);
    fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
    fs.writeFileSync(
      path.join(ARTIFACT_DIR, "table-width-v1-legacy.json"),
      JSON.stringify(report, null, 2),
    );
    expect(report.scrollWidth).toBeLessThanOrEqual(report.clientWidth + 1);
  });
});
