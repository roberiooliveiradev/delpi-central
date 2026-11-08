import { expect, test } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
} from "../helpers";

const CREATE_PATH = "/apps/engineering/product-registration/new";
const CATALOG_FIELDS = [
  "Grupo",
  "Unidade",
  "Armazém padrão",
  "Conta contábil",
];
const ENUM_FIELDS = ["Tipo", "Produto de terceiros"];

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page }) => {
  await loginAsDev(page);
});

test("ficha técnica carrega catálogos TOTVS reais nos Selects do kit", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(CREATE_PATH);

  /* Etapa 2 — Ficha técnica. */
  await page.getByRole("button", { name: "Avançar" }).click();
  await expect(
    page.getByRole("button", { name: "Ficha técnica" }).first(),
  ).toBeVisible({ timeout: 20_000 });

  /* Catálogos TOTVS: trigger habilitado = success com opções reais;
   * nenhum campo pode ficar em loading eterno nem texto livre. */
  for (const label of CATALOG_FIELDS) {
    const trigger = page.getByRole("button", {
      name: new RegExp(`^${label}`),
    });
    await expect(
      trigger,
      `${label} deve habilitar com opções reais`,
    ).toBeEnabled({ timeout: 30_000 });
    await expect(
      page.getByText("Catálogo oficial indisponível"),
      `${label} não pode estar em erro`,
    ).toHaveCount(0);
  }

  /* Abre o painel de Grupo — lista real do SBM010 com código+descrição. */
  await page
    .getByRole("button", { name: /^Grupo/ })
    .click();
  const groupList = page.getByRole("listbox").first();
  await expect(groupList).toBeVisible({ timeout: 10_000 });
  await expect(
    groupList.getByRole("button").first(),
  ).toBeVisible({ timeout: 10_000 });
  await page.screenshot({
    path: `e2e/artifacts/prc-catalogs-group-open-${testInfo.project.name}.png`,
    fullPage: true,
  });
  /* Fecha o painel: Escape primeiro; se ainda aberto, re-clica no
   * trigger (toggle) — nunca clica em coordenada arbitrária. */
  await page.keyboard.press("Escape");
  if (await groupList.isVisible().catch(() => false)) {
    await page.getByRole("button", { name: /^Grupo/ }).click();
  }
  await expect(groupList).not.toBeVisible({ timeout: 5_000 });

  /* Enums do domínio: Tipo (MP/PA/PI) e Produto de terceiros (1/2). */
  for (const label of ENUM_FIELDS) {
    const trigger = page.getByRole("button", {
      name: new RegExp(`^${label}`),
    });
    await expect(
      trigger,
      `${label} deve ser um Select habilitado`,
    ).toBeEnabled({ timeout: 15_000 });
  }

  await page.screenshot({
    path: `e2e/artifacts/prc-catalogs-ficha-${testInfo.project.name}.png`,
    fullPage: true,
  });

  expectNoFailures(forbidden, pageErrors);
});
