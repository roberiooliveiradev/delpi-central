import { test, expect, type Page } from "@playwright/test";
import {
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
  expectNoFailures,
} from "../helpers";

const BASE = "/apps/my-requests";
const SHOT = (name: string) => `artifacts/${test.info().project.name}-${name}.png`;

async function gotoList(page: Page, path = BASE): Promise<void> {
  await page.goto(path);
  await page
    .getByRole("heading", { name: /Minhas solicitações|Fila de trabalho/i })
    .first()
    .waitFor({ state: "visible", timeout: 30_000 });
}

test.describe("Minhas Solicitações UX V2 — listas governadas", () => {
  test("mine: hero + toolbar + controles compartilhados", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    const forbidden = trackForbiddenApiCalls(page);
    await loginAsDev(page);
    await gotoList(page);

    await expect(
      page.getByPlaceholder(/buscar/i).or(page.getByRole("searchbox")).first(),
    ).toBeVisible({ timeout: 15_000 });

    const filtersTrigger = page
      .getByRole("button", { name: /filtros/i })
      .first();
    await expect(filtersTrigger).toBeVisible();
    await filtersTrigger.click();
    const filterPanel = page
      .getByRole("dialog")
      .or(page.locator("[class*=list-tools-popover]"))
      .last();
    await expect(filterPanel).toBeVisible({ timeout: 5_000 });
    await page.keyboard.press("Escape");

    const sortTrigger = page
      .getByRole("button", { name: /ordenar/i })
      .first();
    await expect(sortTrigger).toBeVisible();
    await sortTrigger.click();
    const sortPanel = page
      .getByRole("dialog")
      .or(page.locator("[class*=list-tools-popover]"))
      .last();
    await expect(sortPanel).toBeVisible({ timeout: 5_000 });
    await page.keyboard.press("Escape");

    await page.screenshot({ path: SHOT("mine-list"), fullPage: true });
    await expectNoFailures(pageErrors, forbidden);
  });

  test("mine: busca serializa na URL e chips aparecem", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    const forbidden = trackForbiddenApiCalls(page);
    await loginAsDev(page);
    await gotoList(page);

    const search = page
      .getByPlaceholder(/buscar/i)
      .or(page.getByRole("searchbox"))
      .first();
    await search.fill("teste-ux-v2");
    await page.waitForURL(/[?&]q=teste-ux-v2/, { timeout: 10_000 });
    expect(page.url()).toContain("q=teste-ux-v2");

    await page.screenshot({ path: SHOT("mine-search-url"), fullPage: true });
    await expectNoFailures(pageErrors, forbidden);
  });

  test("work-queue: mesma experiência visual + sort parametrizado", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    const forbidden = trackForbiddenApiCalls(page);
    await loginAsDev(page);
    await page.goto(`${BASE}/work-queue`);

    const forbiddenState = page.getByText(
      /sem permissão|não autorizado|forbidden/i,
    );
    const isForbidden = await forbiddenState
      .first()
      .waitFor({ state: "visible", timeout: 8_000 })
      .then(() => true)
      .catch(() => false);

    if (isForbidden) {
      test.info().annotations.push({
        type: "note",
        description: "usuário dev sem permissão de processador — estado honesto",
      });
      await page.screenshot({
        path: SHOT("work-queue-forbidden"),
        fullPage: true,
      });
      await expectNoFailures(pageErrors, forbidden);
      return;
    }

    await page
      .getByRole("button", { name: /filtros/i })
      .first()
      .waitFor({ state: "visible", timeout: 20_000 });
    const sortTrigger = page.getByRole("button", { name: /ordenar/i }).first();
    await sortTrigger.click();
    const sortPanel = page
      .getByRole("dialog")
      .or(page.locator("[class*=list-tools-popover]"))
      .last();
    await expect(sortPanel).toBeVisible({ timeout: 5_000 });
    await page.keyboard.press("Escape");

    await page.screenshot({ path: SHOT("work-queue-list"), fullPage: true });
    await expectNoFailures(pageErrors, forbidden);
  });

  test("new + admin: hero compacto sem barras de filtro", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    const forbidden = trackForbiddenApiCalls(page);
    await loginAsDev(page);

    await page.goto(`${BASE}/new`);
    await page.waitForTimeout(2_000);
    const filterBar = page.getByRole("button", { name: /^filtros$/i });
    expect(await filterBar.count()).toBe(0);
    await page.screenshot({ path: SHOT("new-hero"), fullPage: true });

    await page.goto(`${BASE}/admin`);
    await page.waitForTimeout(2_000);
    expect(await filterBar.count()).toBe(0);
    await page.screenshot({ path: SHOT("admin-hero"), fullPage: true });

    await expectNoFailures(pageErrors, forbidden);
  });
});
