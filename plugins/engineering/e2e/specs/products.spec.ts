import { expect, test } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
} from "../helpers";

const LIST_PATH = "/apps/engineering/products";

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page }) => {
  await loginAsDev(page);
});

test("catálogo do Início exibe Produtos com ícone e navega", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto("/apps/engineering");

  const card = page
    .locator("a, button")
    .filter({ hasText: "Produtos" })
    .first();
  await expect(card).toBeVisible({ timeout: 20_000 });
  await expect(card.locator("svg").first()).toBeVisible();

  await card.click();
  await expect(page).toHaveURL(/\/apps\/engineering\/products\/?$/);
  await expect(
    page.getByRole("heading", { name: "Catálogo de produtos", level: 1 }),
  ).toBeVisible({ timeout: 20_000 });

  expectNoFailures(forbidden, pageErrors);
});

test("listagem renderiza filtros reativos, multiselects e Limpar", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LIST_PATH);

  await expect(
    page.getByRole("group", { name: "Filtros de produtos" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Limpar filtros" }),
  ).toBeVisible();
  // Busca reativa — não existe botão Filtrar.
  await expect(
    page.getByRole("button", { name: "Filtrar", exact: true }),
  ).toHaveCount(0);

  // Multiselects oficiais de Grupo e Tipo.
  const triggers = page.locator('button[aria-haspopup="listbox"]');
  await expect(triggers).toHaveCount(2, { timeout: 20_000 });

  // Resultado oficial OU estado honesto — nunca tela quebrada.
  const table = page.locator("table");
  const settled = await Promise.race([
    table.waitFor({ state: "visible", timeout: 30_000 }).then(() => "table"),
    page
      .getByText("Nenhum produto encontrado para os filtros aplicados.")
      .waitFor({ state: "visible", timeout: 30_000 })
      .then(() => "empty"),
    page
      .getByText(/Catálogo de produtos indisponível|Acesso negado|indisponível/)
      .first()
      .waitFor({ state: "visible", timeout: 30_000 })
      .then(() => "state"),
  ]);
  expect(["table", "empty", "state"]).toContain(settled);

  if (settled === "table") {
    await expect(table.locator("thead").getByText("Código")).toBeVisible();
    await expect(table.locator("thead").getByText("Descrição")).toBeVisible();
    await expect(table.locator("thead").getByText("Situação")).toBeVisible();
  }

  expectNoFailures(forbidden, pageErrors);
});

test("busca por código é reativa e sincroniza a URL", async ({ page }) => {
  await page.goto(LIST_PATH);
  await expect(
    page.getByRole("group", { name: "Filtros de produtos" }),
  ).toBeVisible({ timeout: 30_000 });

  const codeField = page.getByPlaceholder("Código do produto");
  await codeField.fill("ZZZ-NAO-EXISTE-TESTE");

  // Debounce → URL reflete o filtro sem ação explícita.
  await expect(page).toHaveURL(/code=ZZZ-NAO-EXISTE-TESTE/, {
    timeout: 10_000,
  });

  // Filtro impossível → vazio honesto (ou estado oficial de indisponível).
  const outcome = await Promise.race([
    page
      .getByText("Nenhum produto encontrado para os filtros aplicados.")
      .waitFor({ state: "visible", timeout: 45_000 })
      .then(() => "empty"),
    page
      .getByText(/indisponível|Acesso negado/)
      .first()
      .waitFor({ state: "visible", timeout: 45_000 })
      .then(() => "state"),
  ]);
  expect(["empty", "state"]).toContain(outcome);

  // Limpar restaura URL e filtros.
  await page.getByRole("button", { name: "Limpar filtros" }).click();
  await expect(page).toHaveURL(/\/apps\/engineering\/products\/?$/);
  await expect(codeField).toHaveValue("");
});

test("multiselect de Tipo aplica seleção na URL", async ({ page }) => {
  await page.goto(LIST_PATH);
  await expect(
    page.getByRole("group", { name: "Filtros de produtos" }),
  ).toBeVisible({ timeout: 30_000 });

  const triggers = page.locator('button[aria-haspopup="listbox"]');
  await expect(triggers).toHaveCount(2, { timeout: 20_000 });

  // Segundo trigger = Tipo.
  const typeTrigger = triggers.nth(1);
  await typeTrigger.click();

  const listbox = page.getByRole("listbox");
  await expect(listbox).toBeVisible({ timeout: 15_000 });

  const optionLabels = listbox.locator("li label");
  const count = await optionLabels.count();
  test.skip(count === 0, "Catálogo de tipos indisponível neste ambiente.");

  // Seleciona a primeira opção oficial — commit imediato na URL.
  await optionLabels.nth(0).click({ timeout: 10_000 });

  await expect(page).toHaveURL(/types=/, { timeout: 10_000 });

  // Limpar também remove seleções múltiplas.
  await page.getByRole("button", { name: "Limpar filtros" }).click();
  await expect(page).toHaveURL(/\/apps\/engineering\/products\/?$/);
});

test("ficha do produto renderiza abas oficiais com URL (?tab=)", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LIST_PATH);

  const firstRow = page.locator("table tbody tr").first();
  const hasRows = await firstRow
    .waitFor({ state: "visible", timeout: 30_000 })
    .then(() => true)
    .catch(() => false);
  test.skip(!hasRows, "Catálogo dev sem linhas — estado vazio já coberto.");

  await firstRow.click();
  await expect(page).toHaveURL(/\/apps\/engineering\/products\/.+/);
  await expect(
    page.getByRole("heading", { name: "Ficha do Produto", level: 1 }),
  ).toBeVisible({ timeout: 30_000 });

  // Seis abas oficiais na ordem da spec 61.
  const tabs = page.getByRole("tab");
  await expect(tabs).toHaveCount(6, { timeout: 30_000 });
  for (const label of [
    "Visão geral",
    "Estrutura",
    "Onde é usado",
    "Fornecedores",
    "Desenhos",
    "Histórico",
  ]) {
    await expect(
      page.getByRole("tab", { name: label }),
    ).toBeVisible();
  }

  // Modo Editar honestamente bloqueado (sem contrato WRITE — doc 63 §2.8).
  const editButton = page.getByRole("button", { name: /Editar/ }).first();
  await expect(editButton).toBeVisible();
  await expect(editButton).toBeDisabled();

  // Troca de aba → URL com ?tab= (histórico navegável).
  await page.getByRole("tab", { name: "Estrutura" }).click();
  await expect(
    page.getByRole("tab", { name: "Estrutura" }),
  ).toHaveAttribute("aria-selected", "true");
  await expect(page).toHaveURL(/tab=structure/);

  // Voltar → retorna à aba anterior.
  await page.goBack();
  await expect(page).not.toHaveURL(/tab=structure/, { timeout: 15_000 });

  // Avançar → aba volta.
  await page.goForward();
  await expect(page).toHaveURL(/tab=structure/, { timeout: 15_000 });

  // Aba inválida → normaliza para Visão geral (URL corrigida).
  const invalidUrl = page
    .url()
    .replace(/tab=\w+/, "tab=inexistente");
  await page.goto(invalidUrl);
  await expect(
    page.getByRole("tab", { name: "Visão geral" }),
  ).toHaveAttribute("aria-selected", "true", { timeout: 20_000 });

  // Deep link direto em aba específica.
  const base = page.url().split("?")[0];
  await page.goto(`${base}?tab=suppliers`);
  await expect(
    page.getByRole("tab", { name: "Fornecedores" }),
  ).toHaveAttribute("aria-selected", "true", { timeout: 20_000 });

  expectNoFailures(forbidden, pageErrors);
});
