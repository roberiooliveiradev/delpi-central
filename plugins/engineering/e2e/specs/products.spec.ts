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

test("listagem renderiza hero, filtros e estado oficial", async ({
  page,
}) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  await page.goto(LIST_PATH);

  await expect(
    page.getByRole("group", { name: "Filtros de produtos" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Filtrar" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Limpar" }),
  ).toBeVisible();

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

test("busca por código aplica filtro oficial", async ({ page }) => {
  await page.goto(LIST_PATH);
  await expect(
    page.getByRole("group", { name: "Filtros de produtos" }),
  ).toBeVisible({ timeout: 30_000 });

  const codeField = page.getByPlaceholder("Código do produto");
  await codeField.fill("ZZZ-NAO-EXISTE-TESTE");
  await page.getByRole("button", { name: "Filtrar" }).click();

  // Filtro impossível → vazio honesto (ou estado oficial de indisponível).
  // A tabela anterior permanece durante o reload; o estado final correto
  // é vazio/banner — nunca linhas para código inexistente na fonte.
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
});

test("ficha do produto renderiza abas oficiais quando há dados", async ({
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

  // Troca de aba: lazy load ou estado honesto.
  await page.getByRole("tab", { name: "Estrutura" }).click();
  await expect(
    page.getByRole("tab", { name: "Estrutura" }),
  ).toHaveAttribute("aria-selected", "true");

  expectNoFailures(forbidden, pageErrors);
});
