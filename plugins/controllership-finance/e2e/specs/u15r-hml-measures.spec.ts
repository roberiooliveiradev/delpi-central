/**
 * U15R — medições HML (R1–R3) anexáveis ao verificador.
 */
import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

import { loginAs, openEntryAuditHome } from "../helpers";

const ARTIFACT_DIR =
  process.env.CF_E2E_ARTIFACT_DIR || path.join("/tmp", "ui-review-u15r");

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

test.describe("U15R — medições HML", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "cf_manage");
  });

  test("1440: MultiType sem branco no escuro + day + tipo persistido", async ({
    page,
  }) => {
    test.skip(test.info().project.name !== "desktop", "desktop");
    await page.setViewportSize({ width: 1440, height: 900 });
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise");

    const chart = page.locator('[aria-label="Evolução diária de ocorrências"]');
    await expect(chart).toBeVisible({ timeout: 60_000 });

    const whiteScan = async (theme: "light" | "dark") => {
      await page.evaluate((t) => {
        document.documentElement.setAttribute("data-theme", t);
      }, theme);
      await page.waitForTimeout(500);
      return page.evaluate(() => {
        const root = document.querySelector(
          '[aria-label="Evolução diária de ocorrências"]',
        );
        if (!root) throw new Error("chart ausente");
        const whites: Array<{
          tag: string;
          className: string;
          fill: string;
          bg: string;
          w: number;
          h: number;
        }> = [];
        const opaqueWhite = (value: string | null | undefined) => {
          if (!value) return false;
          const v = value.trim().toLowerCase();
          if (v === "none" || v === "transparent") return false;
          if (v === "#fff" || v === "#ffffff" || v === "white") return true;
          return /^rgba?\(\s*255\s*,\s*255\s*,\s*255(\s*,\s*1(\.0+)?)?\s*\)$/.test(
            v,
          );
        };
        const nodes = [root, ...Array.from(root.querySelectorAll("*"))];
        for (const node of nodes) {
          const el = node as HTMLElement;
          const cs = getComputedStyle(el);
          if (cs.display === "none" || cs.visibility === "hidden") continue;
          if (Number(cs.opacity || "1") === 0) continue;
          const rect = el.getBoundingClientRect();
          // Só o que pinta na tela (H6): área zero não conta.
          if (rect.width < 1 || rect.height < 1) continue;
          const attrFill = el.getAttribute("fill");
          const fill = attrFill && attrFill !== "none" ? attrFill : cs.fill;
          const bg = cs.backgroundColor;
          if (opaqueWhite(fill) || opaqueWhite(bg)) {
            whites.push({
              tag: el.tagName.toLowerCase(),
              className: String(
                (el as SVGElement).className?.baseVal ?? el.className ?? "",
              ).slice(0, 160),
              fill: String(fill ?? ""),
              bg: String(bg ?? ""),
              w: Math.round(rect.width),
              h: Math.round(rect.height),
            });
          }
        }
        return {
          theme: document.documentElement.getAttribute("data-theme"),
          whiteCount: whites.length,
          whites: whites.slice(0, 20),
        };
      });
    };

    const dark = await whiteScan("dark");
    write("chart-white-dark.json", dark);
    expect(dark.whiteCount, `branco no escuro: ${JSON.stringify(dark.whites)}`).toBe(
      0,
    );

    const light = await whiteScan("light");
    write("chart-white-light.json", light);

    await page.evaluate(() =>
      document.documentElement.setAttribute("data-theme", "light"),
    );

    const categoriesBefore = await page.evaluate(() => {
      const root = document.querySelector(
        '[aria-label="Evolução diária de ocorrências"]',
      );
      const ticks = root
        ? Array.from(root.querySelectorAll(".recharts-cartesian-axis-tick-value"))
        : [];
      const bars = root
        ? Array.from(root.querySelectorAll(".recharts-bar-rectangle path, .recharts-rectangle"))
        : [];
      return {
        tickCount: ticks.length,
        barCount: bars.length,
        tickLabels: ticks.map((t) => (t.textContent || "").trim()).filter(Boolean),
      };
    });
    write("daily-categories-before.json", categoriesBefore);
    expect(categoriesBefore.tickCount).toBeGreaterThanOrEqual(2);

    // ChartTypeSegmentToggle = popover (trigger + catálogo Colunas/Linhas/Áreas).
    const typeTrigger = chart.getByRole("button", { name: /Tipo de gráfico/i });
    await expect(typeTrigger).toBeVisible({ timeout: 15_000 });
    await typeTrigger.click();
    const linhas = page.getByRole("menuitem", { name: /Linhas/i }).or(
      page.getByTitle("Linhas"),
    );
    await expect(linhas.first()).toBeVisible({ timeout: 10_000 });
    await linhas.first().click();
    await page.waitForTimeout(400);

    const typeAfter = await page.evaluate(() => {
      const trigger = document.querySelector(
        '[aria-label="Evolução diária de ocorrências"] [aria-label="Tipo de gráfico"]',
      );
      return {
        triggerText: (trigger?.textContent || "").trim(),
        storage: window.localStorage.getItem(
          "controllership-finance:entry-audit:daily",
        ),
      };
    });
    write("chart-type-after-toggle.json", typeAfter);
    expect(typeAfter.storage || "").toMatch(/line/);

    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(chart).toBeVisible({ timeout: 60_000 });
    const typeAfterF5 = await page.evaluate(() => {
      const trigger = document.querySelector(
        '[aria-label="Evolução diária de ocorrências"] [aria-label="Tipo de gráfico"]',
      );
      return {
        triggerText: (trigger?.textContent || "").trim(),
        storage: window.localStorage.getItem(
          "controllership-finance:entry-audit:daily",
        ),
      };
    });
    write("chart-type-after-f5.json", typeAfterF5);
    expect(typeAfterF5.storage).toBe(typeAfter.storage);
    expect(typeAfterF5.triggerText).toMatch(/Linha/i);

    // Volta para coluna para o clique por categoria (onCategoryClick nas barras).
    const typeTriggerAfterF5 = chart.getByRole("button", {
      name: /Tipo de gráfico/i,
    });
    await typeTriggerAfterF5.click();
    const colunas = page.getByRole("menuitem", { name: /Colunas/i }).or(
      page.getByTitle("Colunas"),
    );
    await expect(colunas.first()).toBeVisible({ timeout: 10_000 });
    await colunas.first().click();
    await page.waitForTimeout(400);

    const bar = chart.locator(".recharts-bar-rectangle path, .recharts-rectangle").nth(1);
    await expect(bar).toBeVisible({ timeout: 15_000 });
    await bar.click({ force: true });
    await expect(page).toHaveURL(/day=/, { timeout: 15_000 });
    await page.waitForTimeout(1000);

    const categoriesWithDay = await page.evaluate(() => {
      const root = document.querySelector(
        '[aria-label="Evolução diária de ocorrências"]',
      );
      const ticks = root
        ? Array.from(root.querySelectorAll(".recharts-cartesian-axis-tick-value"))
        : [];
      return {
        tickCount: ticks.length,
        url: window.location.search,
      };
    });
    write("daily-categories-with-day.json", categoriesWithDay);
    expect(categoriesWithDay.tickCount).toBe(categoriesBefore.tickCount);

    await bar.click({ force: true });
    await expect(page).not.toHaveURL(/day=/, { timeout: 15_000 });
  });

  test("1440+390: KPI sem reticências; ícone×título sem interseção", async ({
    page,
  }) => {
    test.skip(test.info().project.name !== "desktop", "desktop");
    await page.setViewportSize({ width: 1440, height: 900 });
    const opened = await openFirstAnalysis(page);
    test.skip(!opened, "sem análise");

    const measureKpis = async (width: number, height: number) => {
      await page.setViewportSize({ width, height });
      await page.waitForTimeout(500);
      return page.evaluate(() => {
        const cards = Array.from(
          document.querySelectorAll(".cf-kpi-grid .cf-kpi-card, .cf-kpi-grid .delpi-ui-kpi-card"),
        ) as HTMLElement[];
        const values = cards.map((card) => {
          const valueEl = card.querySelector(
            ".cf-kpi-card__value, .delpi-ui-kpi-value, [class*='kpi-value']",
          ) as HTMLElement | null;
          const text = (valueEl?.textContent || "").trim();
          const cs = valueEl ? getComputedStyle(valueEl) : null;
          return {
            text,
            hasEllipsisChar: text.includes("…") || text.includes("..."),
            textOverflow: cs?.textOverflow ?? null,
          };
        });
        const overlaps: Array<{ title: string }> = [];
        for (const card of cards) {
          const title = card.querySelector(
            ".cf-kpi-card__label, .cf-kpi-title, [class*='kpi-title'], [class*='kpi-card__label']",
          ) as HTMLElement | null;
          const icon = card.querySelector(
            ".cf-kpi-card__icon, .delpi-ui-kpi-icon, [class*='kpi-icon']",
          ) as HTMLElement | null;
          if (!title || !icon) continue;
          const a = title.getBoundingClientRect();
          const b = icon.getBoundingClientRect();
          const intersects = !(
            a.right <= b.left + 0.5 ||
            a.left >= b.right - 0.5 ||
            a.bottom <= b.top + 0.5 ||
            a.top >= b.bottom - 0.5
          );
          if (intersects && a.width > 0 && b.width > 0) {
            overlaps.push({ title: (title.textContent || "").trim() });
          }
        }
        return { values, overlaps };
      });
    };

    // Com day= força valores monetários menores no recorte (quando houver).
    const firstBar = page
      .locator('[aria-label="Evolução diária de ocorrências"] .recharts-rectangle, [aria-label="Evolução diária de ocorrências"] .recharts-bar-rectangle path')
      .nth(1);
    if (await firstBar.isVisible().catch(() => false)) {
      await firstBar.click({ force: true });
      await page.waitForTimeout(800);
    }

    const at1440 = await measureKpis(1440, 900);
    write("kpi-ellipsis-1440.json", at1440);
    expect(at1440.values.every((v) => !v.hasEllipsisChar)).toBe(true);

    const at390 = await measureKpis(390, 844);
    write("kpi-ellipsis-390.json", at390);
    write("kpi-icon-title-overlap-390.json", { overlaps: at390.overlaps });
    expect(at390.values.every((v) => !v.hasEllipsisChar)).toBe(true);
    expect(at390.overlaps).toEqual([]);
  });
});
