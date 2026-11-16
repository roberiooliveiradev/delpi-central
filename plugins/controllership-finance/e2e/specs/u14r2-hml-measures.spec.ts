/**
 * U14R2 K4 — medições HML anexáveis ao verificador.
 */
import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import path from "node:path";

import { loginAs, openEntryAuditHome } from "../helpers";

const ARTIFACT_DIR =
  process.env.CF_E2E_ARTIFACT_DIR || path.join("/tmp", "ui-review-u14r2");

function write(name: string, data: unknown): void {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
  fs.writeFileSync(
    path.join(ARTIFACT_DIR, name),
    JSON.stringify(data, null, 2),
    "utf8",
  );
}

async function openFirstAnalysis(page: Page): Promise<boolean> {
  await openEntryAuditHome(page);
  const row = page.locator("table tbody tr").first();
  if (!(await row.isVisible().catch(() => false))) return false;
  await row.click();
  await expect(page).toHaveURL(/\/entry-audit\/analyses\//, { timeout: 60_000 });
  await expect(page.getByRole("heading", { name: /^Panorama$/i })).toBeVisible({
    timeout: 60_000,
  });
  return true;
}

test.describe("U14R2 K4 — medições HML", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "cf_manage");
  });

  test("1440: panorama + pendentes + tabela + barras + axe", async ({ page }) => {
    test.skip(test.info().project.name !== "desktop", "desktop");
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
    test.skip(!opened, "sem análise");

    const panorama = await page.evaluate(() => {
      const card =
        document
          .querySelector(".cf-analysis-panorama")
          ?.closest(
            '[class*="section-card"], .cf-section-card, .delpi-ui-section-card',
          ) ?? document.querySelector(".cf-analysis-panorama")?.parentElement;
      const panoramaEl = document.querySelector(".cf-analysis-panorama");
      if (!card || !panoramaEl) throw new Error("panorama ausente");
      const cardRect = card.getBoundingClientRect();
      const dots = Array.from(
        panoramaEl.querySelectorAll('[class*="legend-dot"]'),
      ) as HTMLElement[];
      const legendDotMaxHeight = dots.reduce(
        (m, el) => Math.max(m, el.getBoundingClientRect().height),
        0,
      );
      let centerOutsideChart = 0;
      for (const chart of Array.from(
        panoramaEl.querySelectorAll('[class*="__chart"]'),
      ) as HTMLElement[]) {
        const chartRect = chart.getBoundingClientRect();
        for (const node of Array.from(
          chart.querySelectorAll(
            '[class*="__center"], [class*="__value"], [class*="__center-label"]',
          ),
        ) as HTMLElement[]) {
          const r = node.getBoundingClientRect();
          if (
            r.width > 0 &&
            (r.bottom < chartRect.top ||
              r.top > chartRect.bottom ||
              r.right < chartRect.left ||
              r.left > chartRect.right)
          ) {
            centerOutsideChart += 1;
          }
        }
      }
      return {
        panoramaCardHeight: Math.round(cardRect.height),
        legendDotMaxHeight: Math.round(legendDotMaxHeight * 10) / 10,
        centerOutsideChart,
      };
    });
    write("panorama-1440.json", panorama);
    expect(panorama.panoramaCardHeight).toBeLessThanOrEqual(520);
    expect(panorama.legendDotMaxHeight).toBeLessThanOrEqual(16);
    expect(panorama.centerOutsideChart).toBe(0);

    const pending = await page.evaluate(() => {
      const title = Array.from(
        document.querySelectorAll(
          ".cf-kpi-grid [class*='kpi-title'], .cf-kpi-grid [class*='kpi-card__label'], .cf-kpi-grid [class*='kpi-label']",
        ),
      ).find((node) => (node.textContent ?? "").trim() === "Pendentes") as
        | HTMLElement
        | undefined;
      if (!title) return null;
      return {
        text: title.textContent?.trim(),
        scrollWidth: title.scrollWidth,
        clientWidth: title.clientWidth,
      };
    });
    write("pending-title-1440.json", pending);
    expect(pending).toBeTruthy();
    expect(pending!.scrollWidth).toBeLessThanOrEqual(pending!.clientWidth + 1);

    await page.getByRole("tab", { name: /Ocorrências/i }).click().catch(() => undefined);
    await expect(page.locator("table").first()).toBeVisible({ timeout: 30_000 });
    const tableClean = await page.evaluate(() => {
      const root = document.querySelector(".cf-entry-audit-occurrences-table");
      const table = root?.querySelector("table") ?? document.querySelector("table");
      const wrap =
        (root?.querySelector(
          '[class*="table-wrap"]',
        ) as HTMLElement | null) ??
        (table?.closest('[class*="table-wrap"]') as HTMLElement | null) ??
        (table?.parentElement as HTMLElement | null);
      if (!wrap) throw new Error("tabela ausente");
      return { scrollWidth: wrap.scrollWidth, clientWidth: wrap.clientWidth };
    });
    write("table-width-clean.json", tableClean);
    expect(tableClean.scrollWidth).toBeLessThanOrEqual(tableClean.clientWidth + 1);

    const bars = await page.evaluate(() => {
      const group = document.querySelector(
        '[aria-label="Evolução diária de ocorrências"]',
      );
      const buttons = group
        ? Array.from(group.querySelectorAll('[role="button"]'))
        : [];
      return { barCount: buttons.length };
    });
    write("daily-bars-1440.json", bars);
    expect(bars.barCount).toBeGreaterThanOrEqual(2);

    const dayBtn = page
      .locator('[aria-label="Evolução diária de ocorrências"] [role="button"]')
      .nth(1);
    await dayBtn.click();
    await expect(page).toHaveURL(/day=/, { timeout: 15_000 });
    await dayBtn.click();
    await expect(page).not.toHaveURL(/day=/, { timeout: 15_000 });
    write("daily-bars-click.json", { toggleDay: "ok" });

    const axe = await new AxeBuilder({ page })
      .include(".dashboard-controllership-finance")
      .analyze();
    const serious = axe.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );
    write("axe-1440.json", {
      violationCount: axe.violations.length,
      seriousCritical: serious.map((v) => v.id),
    });
    expect(serious).toEqual([]);
  });

  test("1440 com v1 antiga: tabela cabe", async ({ page }) => {
    test.skip(test.info().project.name !== "desktop", "desktop");
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
    test.skip(!opened, "sem análise");
    await page.getByRole("tab", { name: /Ocorrências/i }).click().catch(() => undefined);
    await expect(page.locator("table").first()).toBeVisible({ timeout: 30_000 });
    const table = await page.evaluate(() => {
      const root = document.querySelector(".cf-entry-audit-occurrences-table");
      const t = root?.querySelector("table") ?? document.querySelector("table");
      const wrap =
        (root?.querySelector(
          '[class*="table-wrap"]',
        ) as HTMLElement | null) ??
        (t?.closest('[class*="table-wrap"]') as HTMLElement | null) ??
        (t?.parentElement as HTMLElement | null);
      if (!wrap) throw new Error("tabela ausente");
      return { scrollWidth: wrap.scrollWidth, clientWidth: wrap.clientWidth };
    });
    write("table-width-v1-legacy.json", table);
    expect(table.scrollWidth).toBeLessThanOrEqual(table.clientWidth + 1);
  });

  test("390: panorama geometria", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise");
    const report = await page.evaluate(() => {
      const panoramaEl = document.querySelector(".cf-analysis-panorama");
      if (!panoramaEl) throw new Error("panorama ausente");
      const dots = Array.from(
        panoramaEl.querySelectorAll('[class*="legend-dot"]'),
      ) as HTMLElement[];
      return {
        legendDotMaxHeight: dots.reduce(
          (m, el) => Math.max(m, el.getBoundingClientRect().height),
          0,
        ),
      };
    });
    write("panorama-390.json", report);
    expect(report.legendDotMaxHeight).toBeLessThanOrEqual(16);
  });
});
