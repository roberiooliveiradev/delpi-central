import { expect, test, type Page } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
} from "../helpers";

const QUEUE_PATH = "/apps/engineering/product-registration";

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page }) => {
  await loginAsDev(page);
});

async function openFirstRequestSheet(page: Page): Promise<boolean> {
  await page.goto(QUEUE_PATH);
  const row = page.locator("a[href*='/product-registration/']").first();
  const visible = await row
    .waitFor({ state: "visible", timeout: 20_000 })
    .then(() => true)
    .catch(() => false);
  if (!visible) return false;
  await row.click();
  await expect(
    page.getByRole("button", { name: "Ficha técnica" }).first(),
  ).toBeVisible({ timeout: 20_000 });
  await page.getByRole("button", { name: "Ficha técnica" }).first().click();
  await expect(
    page.getByRole("heading", { name: "Bandeiras de acompanhamento" }),
  ).toBeVisible({ timeout: 20_000 });
  return true;
}

test("CRUD de bandeiras na ficha técnica — persistência e histórico", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-flags-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  const opened = await openFirstRequestSheet(page);
  test.skip(!opened, "Fila PRC vazia no DEV — sem caso para validar bandeiras.");

  await shot("section-empty-or-list");

  const title = `Revisar descrição ${Date.now()}`;
  await page.getByRole("button", { name: "+ Nova bandeira" }).click();
  await page.getByLabel("Título").fill(title);
  await page
    .getByLabel("Descrição")
    .fill("Confirmar descrição técnica com o solicitante.");
  await page.getByRole("button", { name: "Salvar" }).click();

  await expect(page.getByText(title).first()).toBeVisible({ timeout: 15_000 });
  await shot("created");

  await page.reload();
  await page.getByRole("button", { name: "Ficha técnica" }).first().click();
  await expect(page.getByText(title).first()).toBeVisible({ timeout: 20_000 });

  const card = page.locator(".engineering-prc__flag-card", {
    hasText: title,
  });
  await card.getByRole("button", { name: /Editar bandeira/ }).click();
  await page
    .getByLabel("Descrição")
    .fill("Texto editado — validar descrição recebida.");
  await page.getByRole("button", { name: "Salvar" }).click();
  await expect(page.getByText("Texto editado").first()).toBeVisible({
    timeout: 15_000,
  });

  await card.getByRole("button", { name: /Resolver bandeira/ }).click();
  await expect(card.getByText("Resolvida")).toBeVisible({ timeout: 15_000 });
  await shot("resolved");

  await page.getByRole("button", { name: /Mostrar resolvidas/ }).click();
  await expect(page.getByText(title).first()).toBeVisible();
  await card.getByRole("button", { name: /Reabrir bandeira/ }).click();
  await expect(card.getByText("Aberta")).toBeVisible({ timeout: 15_000 });

  await card.getByRole("button", { name: /Mais ações/ }).click();
  await page.getByRole("menuitem", { name: "Remover" }).click();
  await page.getByRole("button", { name: "Remover" }).click();
  await expect(page.getByText(title)).toHaveCount(0, { timeout: 15_000 });
  await shot("deleted");

  await page.getByRole("button", { name: "Histórico" }).click();
  await expect(page.getByText(/Bandeira/i).first()).toBeVisible({
    timeout: 15_000,
  });
  await shot("timeline");

  await expectNoFailures(pageErrors, forbidden);
});
