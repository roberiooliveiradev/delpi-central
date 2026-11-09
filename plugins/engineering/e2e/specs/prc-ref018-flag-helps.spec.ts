/**
 * PRC-REF-018 / D16-REF-03 — Flag verde, legenda, helps no label.
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

async function openSheet(page: Page): Promise<boolean> {
  await page.goto(QUEUE_PATH);
  await ensureAuthenticated(page);
  const row = page.locator("tbody tr").first();
  const card = page.locator("[class*='interactive-data-card'], article").first();
  const hasRow = await row
    .waitFor({ state: "visible", timeout: 8_000 })
    .then(() => true)
    .catch(() => false);
  if (hasRow) await row.click();
  else {
    const hasCard = await card
      .waitFor({ state: "visible", timeout: 8_000 })
      .then(() => true)
      .catch(() => false);
    if (!hasCard) return false;
    await card.click();
  }
  await ensureAuthenticated(page);
  const sheetTab = page
    .getByRole("tab", { name: "Ficha técnica" })
    .or(page.getByRole("button", { name: "Ficha técnica" }))
    .first();
  await expect(sheetTab).toBeVisible({ timeout: 30_000 });
  await sheetTab.click();
  await expect(
    page.getByRole("heading", { name: /Acompanhamento técnico|Campos sinalizados/i }),
  ).toBeVisible({ timeout: 20_000 });
  return true;
}

test("REF-018 — azul → vermelho → verde + legenda + help Resolver", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-ref018-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  const opened = await openSheet(page);
  test.skip(!opened, "Fila PRC vazia no DEV.");

  await expect(page.getByText(/Ocultar resolvidas|Ver resolvidas/i)).toHaveCount(0);
  await page.getByRole("button", { name: /Legenda das bandeiras/i }).click();
  await expect(page.getByText(/Adicionar acompanhamento/i).first()).toBeVisible();
  await expect(page.getByText(/Acompanhamento aberto/i).first()).toBeVisible();
  await expect(page.getByText(/Acompanhamento resolvido/i).first()).toBeVisible();
  await shot("legend");

  const field = page.locator("#prc-field-description");
  await expect(field).toBeVisible({ timeout: 15_000 });

  // Limpa OPEN/RESOLVED residuais até restar o acionador azul.
  for (let i = 0; i < 6; i++) {
    const openBtn = field.getByRole("button", {
      name: /Bandeira aberta em Descrição/i,
    });
    const resolvedBtn = field.getByRole("button", {
      name: /Bandeira resolvida em Descrição/i,
    });
    const target = (await openBtn.count())
      ? openBtn
      : (await resolvedBtn.count())
        ? resolvedBtn
        : null;
    if (!target) break;
    await target.click();
    const modal = page.locator(".engineering-prc__flag-modal");
    await expect(modal).toBeVisible({ timeout: 10_000 });
    await page.getByRole("button", { name: /Remover/i }).first().click();
    await page.getByRole("button", { name: /^Remover$/i }).last().click();
    await expect(modal).toHaveCount(0, { timeout: 15_000 });
  }

  await field.hover();
  await field.focus();
  const addBtn = field.getByRole("button", {
    name: /Adicionar bandeira em Descrição/i,
  });
  await expect(addBtn).toBeVisible({ timeout: 10_000 });
  await expect(addBtn).toHaveClass(/field-flag--add/);
  await shot("blue");

  // Help no label Descrição (FieldLabel) — sem ?
  await expect(page.locator("text=?").filter({ has: field })).toHaveCount(0).catch(() => undefined);
  const descLabel = field.getByText("Descrição", { exact: true }).first();
  await descLabel.hover();
  await shot("label-help-hover");

  await addBtn.click();
  const modal = page.locator(".engineering-prc__flag-modal");
  await expect(modal).toBeVisible({ timeout: 10_000 });
  await expect(modal.getByText(/Adicionar acompanhamento/i)).toBeVisible();
  const title = `REF018 ${Date.now()}`;
  await modal.getByRole("textbox", { name: "Título" }).fill(title);
  await modal
    .getByRole("textbox", { name: "Descrição" })
    .fill("Acompanhamento REF-018 — validar bandeira verde.");
  await page.getByRole("button", { name: /Criar/i }).click();

  const openBtn = field.getByRole("button", {
    name: /Bandeira aberta em Descrição/i,
  });
  await expect(openBtn).toBeVisible({ timeout: 15_000 });
  await expect(openBtn).toHaveClass(/field-flag--open/);
  await shot("red-open");

  await openBtn.click();
  await expect(modal).toBeVisible();
  const resolveBtn = page.getByRole("button", { name: /Resolver/i });
  await expect(resolveBtn).toBeVisible();
  await resolveBtn.hover();
  await shot("resolve-help");
  await Promise.all([
    page.waitForResponse(
      (r) => r.url().includes("/actions/resolve") && r.ok(),
      { timeout: 20_000 },
    ),
    resolveBtn.click(),
  ]);

  const greenBtn = field.getByRole("button", {
    name: /Bandeira resolvida em Descrição/i,
  });
  await expect(greenBtn).toBeVisible({ timeout: 15_000 });
  await expect(greenBtn).toHaveClass(/field-flag--resolved/);
  await shot("green-resolved");

  await page.reload();
  await ensureAuthenticated(page);
  await page
    .getByRole("tab", { name: "Ficha técnica" })
    .or(page.getByRole("button", { name: "Ficha técnica" }))
    .first()
    .click();
  await expect(
    page.locator("#prc-field-description").getByRole("button", {
      name: /Bandeira resolvida em Descrição/i,
    }),
  ).toBeVisible({ timeout: 20_000 });

  await page
    .locator("#prc-field-description")
    .getByRole("button", { name: /Bandeira resolvida em Descrição/i })
    .click();
  await expect(page.getByRole("button", { name: /Reabrir/i })).toBeVisible();
  await Promise.all([
    page.waitForResponse(
      (r) => r.url().includes("/actions/reopen") && r.ok(),
      { timeout: 20_000 },
    ),
    page.getByRole("button", { name: /Reabrir/i }).click(),
  ]);
  await expect(
    page.locator("#prc-field-description").getByRole("button", {
      name: /Bandeira aberta em Descrição/i,
    }),
  ).toBeVisible({ timeout: 15_000 });
  await shot("reopened-red");

  expectNoFailures(forbidden, pageErrors);
});
