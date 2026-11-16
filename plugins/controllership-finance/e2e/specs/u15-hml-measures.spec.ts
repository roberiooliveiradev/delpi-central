/**
 * U15 — medições HML (P1–P4) anexáveis ao verificador.
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

import { loginAs, openEntryAuditHome } from "../helpers";

const ARTIFACT_DIR =
  process.env.CF_E2E_ARTIFACT_DIR || path.join("/tmp", "ui-review-u15");

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
  await expect(page.getByRole("heading", { name: /Análise de/i })).toBeVisible({
    timeout: 60_000,
  });
  return true;
}

test.describe("U15 — medições HML", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "cf_manage");
  });

  test("1440: fundo do gráfico claro/escuro + day sem zerar série", async ({
    page,
  }) => {
    test.skip(test.info().project.name !== "desktop", "desktop");
    await page.setViewportSize({ width: 1440, height: 900 });
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise");

    await expect(
      page.locator('[aria-label="Evolução diária de ocorrências"]'),
    ).toBeVisible({ timeout: 60_000 });

    const measureFill = async (theme: "light" | "dark") => {
      await page.evaluate((t) => {
        document.documentElement.setAttribute("data-theme", t);
      }, theme);
      await page.waitForTimeout(400);
      return page.evaluate(() => {
        const chart = document.querySelector(
          '[aria-label="Evolução diária de ocorrências"]',
        );
        const paint =
          (chart?.querySelector(
            '[class*="series-chart"], [class*="plot"], svg',
          ) as HTMLElement | null) ?? (chart as HTMLElement | null);
        if (!paint) throw new Error("chart ausente");
        const cs = getComputedStyle(paint);
        const themeAttr =
          paint.closest("[data-theme]")?.getAttribute("data-theme") ??
          document.documentElement.getAttribute("data-theme");
        return {
          theme: themeAttr,
          backgroundColor: cs.backgroundColor,
          fill: cs.backgroundColor,
        };
      });
    };

    const light = await measureFill("light");
    const dark = await measureFill("dark");
    write("chart-bg-light.json", light);
    write("chart-bg-dark.json", dark);
    // Escuro não pode ser branco opaco (#fff / rgb(255,255,255)).
    expect(dark.backgroundColor).not.toMatch(/rgb\(\s*255\s*,\s*255\s*,\s*255\s*\)/);
    expect(dark.backgroundColor).not.toBe("rgba(255, 255, 255, 1)");

    await page.evaluate(() =>
      document.documentElement.setAttribute("data-theme", "light"),
    );

    const before = await page.evaluate(() => {
      const group = document.querySelector(
        '[aria-label="Evolução diária de ocorrências"]',
      );
      const buttons = group
        ? Array.from(group.querySelectorAll('[role="button"]'))
        : [];
      const positive = buttons.filter((btn) => {
        const label = btn.getAttribute("aria-label") || "";
        const m = label.match(/:\s*([\d.,]+)\s*$/);
        if (!m) return false;
        const n = Number(String(m[1]).replace(/\./g, "").replace(",", "."));
        return Number.isFinite(n) && n > 0;
      }).length;
      return { barCount: buttons.length, positiveCount: positive };
    });
    write("daily-before-day.json", before);
    expect(before.barCount).toBeGreaterThanOrEqual(2);

    const dayBtn = page
      .locator('[aria-label="Evolução diária de ocorrências"] [role="button"]')
      .nth(1);
    await expect(dayBtn).toBeVisible({ timeout: 15_000 });
    await dayBtn.click();
    await expect(page).toHaveURL(/day=/, { timeout: 15_000 });
    await page.waitForTimeout(1200);

    const after = await page.evaluate(() => {
      const group = document.querySelector(
        '[aria-label="Evolução diária de ocorrências"]',
      );
      const buttons = group
        ? Array.from(group.querySelectorAll('[role="button"]'))
        : [];
      const positive = buttons.filter((btn) => {
        const label = btn.getAttribute("aria-label") || "";
        const m = label.match(/:\s*([\d.,]+)\s*$/);
        if (!m) return false;
        const n = Number(String(m[1]).replace(/\./g, "").replace(",", "."));
        return Number.isFinite(n) && n > 0;
      }).length;
      return { barCount: buttons.length, positiveCount: positive };
    });
    write("daily-with-day.json", after);
    expect(after.positiveCount).toBe(before.positiveCount);
    expect(after.positiveCount).toBeGreaterThanOrEqual(2);
  });

  test("390: hero cabe + KPIs 2 colunas", async ({ page }) => {
    test.skip(test.info().project.name !== "desktop", "desktop");
    await page.setViewportSize({ width: 1440, height: 900 });
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise");
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.locator(".cf-page-hero, [class*='page-hero']").first()).toBeVisible({
      timeout: 30_000,
    });

    const report = await page.evaluate(() => {
      const hero = (document.querySelector(".cf-page-hero") ||
        document.querySelector('[class*="page-hero"]')) as HTMLElement | null;
      if (!hero) throw new Error("hero ausente");
      const heroRect = hero.getBoundingClientRect();
      const actions = Array.from(
        hero.querySelectorAll("button, a[role='button'], .cf-action-button, [class*='action-btn']"),
      ) as HTMLElement[];
      const outside = actions.filter((el) => {
        const r = el.getBoundingClientRect();
        return (
          r.width > 0 &&
          (r.right > heroRect.right + 2 ||
            r.left < heroRect.left - 2 ||
            r.bottom > window.innerHeight + 2)
        );
      }).length;
      const pathCurrent = document.querySelector(
        ".cf-page-path__current, [class*='page-path__current']",
      ) as HTMLElement | null;
      const kpiGrid = document.querySelector(".cf-kpi-grid") as HTMLElement | null;
      const style = kpiGrid ? getComputedStyle(kpiGrid) : null;
      const cols = style?.gridTemplateColumns?.split(" ").filter(Boolean).length ?? 0;
      return {
        heroScrollWidth: hero.scrollWidth,
        heroClientWidth: hero.clientWidth,
        actionsOutsideHero: outside,
        pathCurrentOverflow: pathCurrent
          ? pathCurrent.scrollWidth > pathCurrent.clientWidth + 1
          : null,
        kpiColumns: cols,
      };
    });
    write("hero-kpi-390.json", report);
    expect(report.heroScrollWidth).toBeLessThanOrEqual(report.heroClientWidth + 1);
    expect(report.actionsOutsideHero).toBe(0);
    // Reticências no current do PagePath: overflow do texto com ellipsis (não corte sem hint).
    expect(report.pathCurrentOverflow).toBe(true);
    expect(report.kpiColumns).toBe(2);
  });
});
