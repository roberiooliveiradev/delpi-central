/**
 * PRC-REF-017 / D16-REF-02 — Flag azul + conclusão CREATE/UPDATE.
 * Não escreve no TOTVS. Homologação positiva CREATE real permanece
 * PENDING_TOTVS_OPERATOR quando não houver produto elegível.
 */
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

test("D16-REF-02 — Flag azul no hover e vermelha quando OPEN", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-ref017-flag-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

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
    test.skip(!hasCard, "Fila PRC vazia no DEV.");
    await card.click();
  }
  const sheetTab = page
    .getByRole("tab", { name: "Ficha técnica" })
    .or(page.getByRole("button", { name: "Ficha técnica" }))
    .first();
  await expect(sheetTab).toBeVisible({ timeout: 30_000 });
  await sheetTab.click();

  const field = page.locator("#prc-field-description");
  await expect(field).toBeVisible({ timeout: 15_000 });

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
  const addBtn = field.getByRole("button", {
    name: /Adicionar bandeira em Descrição/i,
  });
  await expect(addBtn).toBeVisible({ timeout: 10_000 });
  await expect(addBtn).toHaveClass(/field-flag--add/);
  await shot("blue-add");

  await addBtn.click();
  const modal = page.locator(".engineering-prc__flag-modal");
  await expect(modal).toBeVisible({ timeout: 10_000 });
  const title = `REF017 Flag ${Date.now()}`;
  await modal.getByRole("textbox", { name: "Título" }).fill(title);
  await modal
    .getByRole("textbox", { name: "Descrição" })
    .fill("Validação D16-REF-02 — Flag azul → vermelha.");
  await page.getByRole("button", { name: "Criar" }).click();
  const openBtn = field.getByRole("button", {
    name: /Bandeira aberta em Descrição/i,
  });
  await expect(openBtn).toBeVisible({ timeout: 15_000 });
  await expect(openBtn).toHaveClass(/field-flag--open/);
  await shot("red-open");

  await openBtn.click();
  await expect(modal).toBeVisible();
  await Promise.all([
    page.waitForResponse(
      (r) => r.url().includes("/actions/resolve") && r.ok(),
      { timeout: 20_000 },
    ),
    page.getByRole("button", { name: "Resolver" }).click(),
  ]);
  await expect(openBtn).toHaveCount(0, { timeout: 15_000 });
  await field.hover();
  await expect(addBtn).toBeVisible({ timeout: 10_000 });
  await shot("resolved-blue");

  expectNoFailures(forbidden, pageErrors);
});

test("PRC-REF-020 — diálogo Concluir atendimento distingue CREATE/UPDATE", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-ref020-complete-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  await page.goto(QUEUE_PATH);
  await ensureAuthenticated(page);

  const verifyBtn = page.getByRole("button", { name: /Concluir atendimento/i });
  const row = page.locator("tbody tr").filter({ hasText: /Atendimento|in_progress|Em atendimento/i }).first();
  const anyRow = page.locator("tbody tr").first();
  const anyCard = page.locator("[class*='interactive-data-card'], article").first();
  const hasInProgress = await row
    .waitFor({ state: "visible", timeout: 5_000 })
    .then(() => true)
    .catch(() => false);
  if (hasInProgress) {
    await row.click();
  } else {
    const hasAny = await anyRow
      .waitFor({ state: "visible", timeout: 5_000 })
      .then(() => true)
      .catch(() => false);
    if (hasAny) {
      await anyRow.click();
    } else {
      const hasCard = await anyCard
        .waitFor({ state: "visible", timeout: 8_000 })
        .then(() => true)
        .catch(() => false);
      test.skip(!hasCard, "Fila PRC vazia — sem caso para diálogo de conclusão.");
      await anyCard.click();
    }
  }
  await ensureAuthenticated(page);

  if (!(await verifyBtn.isVisible().catch(() => false))) {
    test.skip(true, "Caso aberto não está Em atendimento com complete permitido.");
  }

  await verifyBtn.click();
  await shot("confirm-dialog");

  const createLabel = page.getByLabel(/Código do produto criado no TOTVS/i);
  const updateLabel = page.getByLabel(/Código oficial TOTVS \(baseline\)/i);
  const isCreate = await createLabel.isVisible().catch(() => false);
  const isUpdate = await updateLabel.isVisible().catch(() => false);
  expect(isCreate || isUpdate).toBeTruthy();

  if (isCreate) {
    // Obrigatoriedade client-side sem código.
    await page
      .getByRole("button", { name: /^Concluir atendimento$/i })
      .last()
      .click();
    await expect(page.getByRole("alert")).toContainText(/código oficial/i);
    await shot("create-code-required");
  } else {
    const input = updateLabel;
    await expect(input).toHaveAttribute("readonly", "");
    await shot("update-code-locked");
  }

  // Aba Verificação TOTVS
  await page.keyboard.press("Escape").catch(() => undefined);
  const cancel = page.getByRole("button", { name: /Cancelar/i });
  if (await cancel.isVisible().catch(() => false)) {
    await cancel.click();
  }
  const verifyTab = page
    .getByRole("tab", { name: /Verificação TOTVS/i })
    .or(page.getByRole("button", { name: /Verificação TOTVS/i }))
    .first();
  if (await verifyTab.isVisible().catch(() => false)) {
    await verifyTab.click();
    await shot("verification-tab");
    await expect(
      page.getByText(/Verificação oficial TOTVS|Comparação campo a campo/i).first(),
    ).toBeVisible({ timeout: 10_000 });
  }

  expectNoFailures(forbidden, pageErrors);
});
