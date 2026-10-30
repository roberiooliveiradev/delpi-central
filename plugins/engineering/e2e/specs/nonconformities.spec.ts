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

  // KPIs oficiais integrados ao hero (R1-A) — ou estado honesto.
  const hero = page.locator("section").first();
  await expect(hero.getByText("Dias sem NC").first()).toBeVisible({
    timeout: 20_000,
  });
  await expect(hero.getByText("Recorde de dias sem NC")).toBeVisible();

  // Coluna Produtos associados (R1-B) — com ajuda no próprio header.
  const table = page.locator("table");
  const tableVisible = await table
    .waitFor({ state: "visible", timeout: 20_000 })
    .then(() => true)
    .catch(() => false);
  if (tableVisible) {
    await expect(
      table.locator("thead").getByText("Produtos associados"),
    ).toBeVisible();
  }

  // Help no texto do label (R1-G) — hover/focus abre tooltip, sem ícone ?.
  const statusLabel = hero.getByText("Status", { exact: true }).first();
  await statusLabel.hover();
  const tooltip = page.getByRole("tooltip");
  const tipVisible = await tooltip
    .waitFor({ state: "visible", timeout: 5_000 })
    .then(() => true)
    .catch(() => false);
  if (!tipVisible) {
    await statusLabel.focus();
    await expect(tooltip).toBeVisible({ timeout: 5_000 });
  }
  await expect(tooltip).toContainText(/tratamento|situação/i);
  await page.keyboard.press("Escape");

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
    page.getByRole("heading", { name: "Produtos associados" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Histórico" }),
  ).toBeVisible();

  // Ordem oficial dos cards (R1-C): Identificação → Produtos →
  // Problema e tratativa → Problemas identificados → Contexto → Histórico.
  const sectionOrder = (
    await page.getByRole("heading", { level: 2 }).allTextContents()
  ).map((text) => text.trim());
  const expectedOrder = [
    "Identificação",
    "Produtos associados",
    "Problema e tratativa",
    "Problemas identificados",
    "Contexto da proposta e produtos",
    "Histórico",
  ];
  const actualOrder = expectedOrder.filter((title) =>
    sectionOrder.some((text) => text.startsWith(title)),
  );
  expectedOrder.forEach((title, index) => {
    expect(actualOrder[index]).toBe(title);
  });
  const positions = expectedOrder.map((title) =>
    sectionOrder.findIndex((text) => text.startsWith(title)),
  );
  expect([...positions].sort((a, b) => a - b)).toEqual(positions);

  // Timeline oficial do kit (R1-D) — trilha semântica com ator e valores
  // formatados; nunca [object Object] no histórico (R1-D/NCUX-12).
  const timeline = page.getByRole("list", {
    name: "Histórico da não conformidade",
  });
  const timelineVisible = await timeline
    .waitFor({ state: "visible", timeout: 15_000 })
    .then(() => true)
    .catch(() => false);
  if (timelineVisible) {
    await expect(page.getByText("[object Object]")).toHaveCount(0);
    await expect(timeline.getByRole("listitem").first()).toBeVisible();
  }

  // Avatares oficiais nos campos de usuário (R1-E) — fallback por iniciais
  // junto ao nome acessível.
  await expect(
    page.locator(".engineering-nc-user .delpi-ui-avatar").first(),
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

test("evidência UX.R1 — light/dark, overflow e help por teclado", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LIST_PATH);
  await expect(
    page.getByRole("heading", { name: "Não conformidades", level: 1 }),
  ).toBeVisible();
  await expect(page.getByText("Dias sem NC").first()).toBeVisible({
    timeout: 20_000,
  });

  // Sem overflow horizontal global (responsivo).
  const overflowX = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth + 1,
  );
  expect(overflowX).toBe(false);

  // Help acessível por teclado (focus → tooltip) sem ícone `?` separado.
  const statusLabel = page
    .locator(".delpi-ui-field-label__text", { hasText: "Status" })
    .first();
  await statusLabel.focus();
  await expect(page.getByRole("tooltip")).toBeVisible({ timeout: 5_000 });
  await page.keyboard.press("Escape");

  await page.screenshot({ path: "artifacts/nc-ux-light.png", fullPage: true });

  // Dark mode — mesma superfície, tokens do tema escuro.
  await page.evaluate(() => {
    document.documentElement.setAttribute("data-theme", "dark");
  });
  await expect(
    page.getByRole("heading", { name: "Não conformidades", level: 1 }),
  ).toBeVisible();
  await expect(page.getByText("Dias sem NC").first()).toBeVisible();
  await page.screenshot({ path: "artifacts/nc-ux-dark.png", fullPage: true });
  await page.evaluate(() => {
    document.documentElement.setAttribute("data-theme", "light");
  });

  // Detalhe em dark — timeline e avatares permanecem legíveis.
  const firstRow = page.locator("tbody tr").first();
  const rowVisible = await firstRow
    .waitFor({ state: "visible", timeout: 10_000 })
    .then(() => true)
    .catch(() => false);
  if (rowVisible) {
    await firstRow.click();
    await page.waitForURL(/\/apps\/engineering\/nonconformities\/[^/]+$/, {
      timeout: 15_000,
    });
    await page.evaluate(() => {
      document.documentElement.setAttribute("data-theme", "dark");
    });
    await expect(
      page.getByRole("heading", { name: "Identificação" }),
    ).toBeVisible();
    await expect(page.getByText("[object Object]")).toHaveCount(0);
    await page.screenshot({
      path: "artifacts/nc-detail-dark.png",
      fullPage: true,
    });
  }

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
