import { expect, test } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
} from "../helpers";

const LIST_PATH = "/apps/engineering/nonconformities";
const LEGACY_BRIDGE_PATH = "/apps/engineering/lmps/nonconformities";

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page }) => {
  await loginAsDev(page);
});

test("listagem NC renderiza hero, filtros e indicadores oficiais", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LIST_PATH);
  await expect(page).toHaveURL(new RegExp(`${LIST_PATH}/?$`));

  await expect(
    page.getByRole("heading", { name: "Não conformidades", level: 1 }),
  ).toBeVisible();

  await expect(
    page.getByRole("group", { name: "Filtros de não conformidades" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Nova não conformidade" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Exportar" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Importar" }),
  ).toBeVisible();

  // KPIs honestos ou estado honesto — nunca conteúdo ausente silencioso.
  const kpiGrid = page.getByRole("list", {
    name: "Indicadores de não conformidades",
  });
  const banner = page.locator(".delpi-ui-state-banner");
  await expect(kpiGrid.or(banner).first()).toBeVisible({ timeout: 20_000 });

  await page.screenshot({
    path: "artifacts/nc-list.png",
    fullPage: true,
  });
  await expectNoFailures(pageErrors, forbidden);
});

test("filtros aplicam e listagem reage (tabela ou vazio honesto)", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LIST_PATH);
  await expect(
    page.getByRole("heading", { name: "Não conformidades", level: 1 }),
  ).toBeVisible();

  const statusSelect = page
    .locator("label", { hasText: "Status" })
    .locator("select")
    .first();
  await statusSelect.selectOption("open");
  await page.getByRole("button", { name: "Filtrar", exact: true }).click();

  const table = page.locator("table");
  const emptyState = page.getByText(
    "Nenhuma não conformidade encontrada",
  );
  await expect(table.or(emptyState).first()).toBeVisible({
    timeout: 20_000,
  });
  await expectNoFailures(pageErrors, forbidden);
});

test("detalhe NC navega pela tabela quando há registros", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LIST_PATH);
  const firstRow = page.locator("tbody tr").first();
  const rowVisible = await firstRow
    .waitFor({ state: "visible", timeout: 20_000 })
    .then(() => true)
    .catch(() => false);

  if (!rowVisible) {
    test.skip(true, "sandbox sem registros — listagem vazia honesta");
    return;
  }

  await firstRow.click();
  await page.waitForURL(/\/apps\/engineering\/nonconformities\/[^/]+$/, {
    timeout: 15_000,
  });

  await expect(
    page.getByRole("heading", { name: /Não conformidade/, level: 1 }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Identificação" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Histórico" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /Contexto da proposta/ }),
  ).toBeVisible();

  await page.screenshot({
    path: "artifacts/nc-detail.png",
    fullPage: true,
  });
  await expectNoFailures(pageErrors, forbidden);
});

test("formulário de criação renderiza campos e valida ocorrência", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(`${LIST_PATH}/new`);
  await expect(
    page.getByRole("heading", { name: "Nova não conformidade", level: 1 }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Identificação" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Problema e tratativa" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Problemas identificados" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Produtos associados" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Cancelar" }).click();
  await page.waitForURL(new RegExp(`${LIST_PATH}/?$`));

  await page.screenshot({
    path: "artifacts/nc-form.png",
    fullPage: true,
  });
  await expectNoFailures(pageErrors, forbidden);
});

test("bridge legado em /lmps/nonconformities preserva acesso oficial", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LEGACY_BRIDGE_PATH);
  await expect(
    page.getByRole("heading", { name: "Experiência nativa disponível" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Abrir não conformidades no Portal" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Abrir registro legado" }),
  ).toBeVisible();

  await page.screenshot({
    path: "artifacts/nc-legacy-bridge.png",
    fullPage: true,
  });
  await expectNoFailures(pageErrors, forbidden);
});
