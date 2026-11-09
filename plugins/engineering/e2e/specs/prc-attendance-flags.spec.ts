import { expect, test, type Page } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
} from "../helpers";

const QUEUE_PATH = "/apps/engineering/product-registration";

test.beforeEach(async ({ page }) => {
  await loginAsDev(page);
});

async function ensureAuthenticated(page: Page): Promise<void> {
  const sso = page.getByRole("button", { name: /Entrar com DELPI SSO/i });
  if (await sso.isVisible().catch(() => false)) {
    await loginAsDev(page);
  }
}

async function openFirstRequestSheet(page: Page): Promise<boolean> {
  const envRid = (process.env.PRC_REQUEST_ID || "").trim();
  if (!envRid) {
    await page.goto(QUEUE_PATH);
    await ensureAuthenticated(page);
    const row = page.locator("tbody tr").first();
    const card = page.locator("[class*='interactive-data-card'], article").first();
    const hasRow = await row
      .waitFor({ state: "visible", timeout: 8_000 })
      .then(() => true)
      .catch(() => false);
    if (hasRow) {
      await row.click();
    } else {
      const hasCard = await card
        .waitFor({ state: "visible", timeout: 8_000 })
        .then(() => true)
        .catch(() => false);
      if (!hasCard) return false;
      await card.click();
    }
  } else {
    await page.goto(`${QUEUE_PATH}/${envRid}?tab=draft`);
    await ensureAuthenticated(page);
    if (!page.url().includes(envRid)) {
      await page.goto(`${QUEUE_PATH}/${envRid}?tab=draft`);
    }
  }

  await ensureAuthenticated(page);
  const sheetTab = page
    .getByRole("tab", { name: "Ficha técnica" })
    .or(page.getByRole("button", { name: "Ficha técnica" }))
    .first();
  await expect(sheetTab).toBeVisible({ timeout: 30_000 });
  await sheetTab.click();
  await expect(
    page.getByRole("heading", { name: "Campos sinalizados" }),
  ).toBeVisible({ timeout: 20_000 });
  return true;
}

test("D16-REF-01 — bandeira contextual em Descrição (CRUD + persistência)", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-flags-ref01-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  const opened = await openFirstRequestSheet(page);
  test.skip(!opened, "Fila PRC vazia no DEV — sem caso para validar bandeiras.");

  await shot("sheet");

  const field = page.locator("#prc-field-description");
  await expect(field).toBeVisible({ timeout: 15_000 });
  // Limpa OPEN residual de execuções anteriores (DEV compartilhado).
  const residualOpen = field.getByRole("button", {
    name: /Bandeira aberta em Descrição/i,
  });
  if (await residualOpen.count()) {
    await residualOpen.click();
    await page.getByRole("button", { name: "Remover" }).click();
    await page.getByRole("button", { name: "Remover" }).last().click();
    await expect(residualOpen).toHaveCount(0, { timeout: 15_000 });
  }
  await field.hover();
  await field.focus();
  const addBtn = field.getByRole("button", {
    name: /Adicionar bandeira em Descrição/i,
  });
  await expect(addBtn).toBeVisible({ timeout: 10_000 });
  await addBtn.click();

  const title = `REF01 Descrição ${Date.now()}`;
  const modal = page.locator(".engineering-prc__flag-modal");
  await expect(modal).toBeVisible({ timeout: 10_000 });
  await modal.getByRole("textbox", { name: "Título" }).fill(title);
  await modal
    .getByRole("textbox", { name: "Descrição" })
    .fill("Confirmar descrição técnica com o solicitante.");
  await page.getByRole("button", { name: "Criar" }).click();

  await expect(
    field.getByRole("button", { name: /Bandeira aberta em Descrição/i }),
  ).toBeVisible({ timeout: 15_000 });
  await shot("created-open-icon");

  await page.reload();
  await page
    .getByRole("tab", { name: "Ficha técnica" })
    .or(page.getByRole("button", { name: "Ficha técnica" }))
    .first()
    .click();
  await expect(
    page.locator("#prc-field-description").getByRole("button", {
      name: /Bandeira aberta em Descrição/i,
    }),
  ).toBeVisible({ timeout: 20_000 });

  const openIcon = () =>
    page.locator("#prc-field-description").getByRole("button", {
      name: /Bandeira aberta em Descrição/i,
    });
  const modalRoot = () => page.locator(".engineering-prc__flag-modal");

  await openIcon().click();
  await expect(modalRoot()).toBeVisible();
  await modalRoot()
    .getByRole("textbox", { name: "Descrição" })
    .fill("Texto editado — validar descrição recebida.");
  await Promise.all([
    page.waitForResponse(
      (r) =>
        r.request().method() === "PATCH" &&
        r.url().includes("/flags/") &&
        r.ok(),
      { timeout: 20_000 },
    ),
    page.getByRole("button", { name: "Salvar" }).click(),
  ]);
  await expect(modalRoot()).toHaveCount(0, { timeout: 15_000 });
  await expect(openIcon()).toBeVisible({ timeout: 15_000 });

  await openIcon().click();
  await expect(modalRoot()).toBeVisible();
  await expect(modalRoot().getByText("Aberta")).toBeVisible();
  await Promise.all([
    page.waitForResponse(
      (r) => r.url().includes("/actions/resolve") && r.ok(),
      { timeout: 20_000 },
    ),
    page.getByRole("button", { name: "Resolver" }).click(),
  ]);
  await expect(modalRoot()).toHaveCount(0, { timeout: 15_000 });
  await expect(openIcon()).toHaveCount(0, { timeout: 15_000 });
  await page.locator("#prc-field-description").hover();
  await expect(
    page.locator("#prc-field-description").getByRole("button", {
      name: /Adicionar bandeira em Descrição/i,
    }),
  ).toBeVisible({ timeout: 15_000 });
  await shot("resolved");

  await page.getByRole("button", { name: /Ver resolvidas/i }).click();
  await page.getByRole("button", { name: title }).first().click();
  await expect(modalRoot()).toBeVisible();
  await Promise.all([
    page.waitForResponse(
      (r) => r.url().includes("/actions/reopen") && r.ok(),
      { timeout: 20_000 },
    ),
    page.getByRole("button", { name: "Reabrir" }).click(),
  ]);
  await expect(modalRoot()).toHaveCount(0, { timeout: 15_000 });
  await expect(openIcon()).toBeVisible({ timeout: 15_000 });
  await shot("reopened");

  await openIcon().click();
  await expect(modalRoot()).toBeVisible();
  await page.getByRole("button", { name: "Remover" }).click();
  await Promise.all([
    page.waitForResponse(
      (r) =>
        r.request().method() === "DELETE" &&
        r.url().includes("/flags/") &&
        r.ok(),
      { timeout: 20_000 },
    ),
    page.getByRole("button", { name: "Remover" }).last().click(),
  ]);
  await expect(modalRoot()).toHaveCount(0, { timeout: 15_000 });
  await expect(openIcon()).toHaveCount(0, { timeout: 15_000 });
  await page.locator("#prc-field-description").hover();
  await expect(
    page.locator("#prc-field-description").getByRole("button", {
      name: /Adicionar bandeira em Descrição/i,
    }),
  ).toBeVisible({ timeout: 15_000 });
  await shot("deleted");

  await expectNoFailures(pageErrors, forbidden);
});

test("D16-REF-01 — painel operacional transversal na fila", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  await page.goto(QUEUE_PATH);
  await ensureAuthenticated(page);
  await page
    .getByRole("button", { name: /Campos sinalizados \/ bandeiras/i })
    .click();
  await expect(
    page.getByText(/bandeira\(s\)|Nenhuma bandeira/i).first(),
  ).toBeVisible({ timeout: 20_000 });
  await page.screenshot({
    path: `e2e/artifacts/prc-flags-ref01-ops-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await expectNoFailures(pageErrors, forbidden);
});
