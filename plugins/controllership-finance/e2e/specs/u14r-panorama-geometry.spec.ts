/**
 * U14R H1 — geometria do Panorama (não screenshot-only).
 * Em 1440 e 390: legend-dot ≤ 16px; rótulo central dentro do gráfico;
 * nada do Panorama fora do card; card Panorama ≤ 520px em 1440.
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

import { loginAs, openEntryAuditHome } from "../helpers";

const ARTIFACT_DIR =
  process.env.CF_E2E_ARTIFACT_DIR || path.join("/tmp", "ui-review-u14r");

type GeometryReport = {
  viewport: { width: number; height: number };
  panoramaCardHeight: number;
  legendDotMaxHeight: number;
  centerOutsideChart: number;
  elementsOutsideCard: number;
  measurements: Record<string, number>;
};

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

async function measurePanorama(page: Page): Promise<GeometryReport> {
  return page.evaluate(() => {
    const card =
      document
        .querySelector(".cf-analysis-panorama")
        ?.closest(
          '[class*="section-card"], .cf-section-card, .delpi-ui-section-card',
        ) ?? document.querySelector(".cf-analysis-panorama")?.parentElement;
    const panorama = document.querySelector(".cf-analysis-panorama");
    if (!card || !panorama) {
      throw new Error("Panorama card não encontrado");
    }
    const cardRect = card.getBoundingClientRect();
    const dots = Array.from(
      panorama.querySelectorAll(
        '[class*="legend-dot"], [class*="__legend-dot"]',
      ),
    ) as HTMLElement[];
    const legendDotMaxHeight = dots.reduce(
      (max, el) => Math.max(max, el.getBoundingClientRect().height),
      0,
    );

    const charts = Array.from(
      panorama.querySelectorAll('[class*="__chart"]'),
    ) as HTMLElement[];
    let centerOutsideChart = 0;
    for (const chart of charts) {
      const chartRect = chart.getBoundingClientRect();
      const centers = chart.querySelectorAll(
        '[class*="__center"], [class*="__value"], [class*="__center-label"]',
      );
      for (const node of Array.from(centers)) {
        const r = (node as HTMLElement).getBoundingClientRect();
        if (
          r.width === 0 ||
          r.height === 0 ||
          r.bottom < chartRect.top ||
          r.top > chartRect.bottom ||
          r.right < chartRect.left ||
          r.left > chartRect.right
        ) {
          centerOutsideChart += 1;
        }
      }
    }

    const all = Array.from(panorama.querySelectorAll("*")) as HTMLElement[];
    let elementsOutsideCard = 0;
    for (const el of all) {
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      if (
        r.top < cardRect.top - 1 ||
        r.bottom > cardRect.bottom + 1 ||
        r.left < cardRect.left - 1 ||
        r.right > cardRect.right + 1
      ) {
        elementsOutsideCard += 1;
      }
    }

    return {
      viewport: { width: window.innerWidth, height: window.innerHeight },
      panoramaCardHeight: Math.round(cardRect.height),
      legendDotMaxHeight: Math.round(legendDotMaxHeight * 10) / 10,
      centerOutsideChart,
      elementsOutsideCard,
      measurements: {
        cardWidth: Math.round(cardRect.width),
        cardHeight: Math.round(cardRect.height),
        legendDotCount: dots.length,
      },
    };
  });
}

function writeReport(name: string, report: GeometryReport): void {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
  fs.writeFileSync(
    path.join(ARTIFACT_DIR, name),
    JSON.stringify(report, null, 2),
    "utf8",
  );
}

test.describe("U14R H1 — geometria Panorama", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "cf_manage");
  });

  test("1440: legendas, centro e altura do card", async ({ page }) => {
    test.skip(
      test.info().project.name !== "desktop",
      "viewport desktop only",
    );
    await page.setViewportSize({ width: 1440, height: 900 });
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise na lista HML");
    const report = await measurePanorama(page);
    writeReport("panorama-geometry-1440.json", report);
    expect(report.legendDotMaxHeight).toBeLessThanOrEqual(16);
    expect(report.centerOutsideChart).toBe(0);
    expect(report.elementsOutsideCard).toBe(0);
    expect(report.panoramaCardHeight).toBeLessThanOrEqual(520);
  });

  test("390: legendas e centro dentro do gráfico/card", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise na lista HML");
    const report = await measurePanorama(page);
    writeReport("panorama-geometry-390.json", report);
    expect(report.legendDotMaxHeight).toBeLessThanOrEqual(16);
    expect(report.centerOutsideChart).toBe(0);
    expect(report.elementsOutsideCard).toBe(0);
  });
});
