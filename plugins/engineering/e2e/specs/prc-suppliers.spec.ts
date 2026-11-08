import { expect, test, type Page } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
} from "../helpers";

const CREATE_PATH = "/apps/engineering/product-registration/new";

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page }) => {
  await loginAsDev(page);
});

async function gotoSheetStep(page: Page) {
  await page.goto(CREATE_PATH);
  await page.getByRole("button", { name: "Avançar" }).click();
  await expect(
    page.getByRole("button", { name: "Ficha técnica" }).first(),
  ).toBeVisible({ timeout: 20_000 });
}

async function expectWithinViewport(locator: ReturnType<Page["locator"]>) {
  const box = await locator.boundingBox();
  expect(box, "dropdown deve existir").not.toBeNull();
  const viewport = await locator.page().viewportSize();
  expect(viewport).not.toBeNull();
  /* 100% da área útil visível: sem clipping por overflow da tabela. */
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.y).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(viewport!.width);
  expect(box!.y + box!.height).toBeLessThanOrEqual(viewport!.height);
}

test("busca SA2 abre dropdown visível e seleciona fornecedor oficial", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-suppliers-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  await gotoSheetStep(page);
  await shot("table-empty");

  /* Uma linha de fornecedor. */
  await page.getByRole("button", { name: "+ Adicionar fornecedor" }).click();
  const input = page.getByRole("textbox", {
    name: "Buscar fornecedor por código ou nome",
  });
  await expect(input).toBeVisible();
  await shot("one-row");

  /* Busca por código — dropdown 100% visível com opção real SA2. */
  await input.fill("0001");
  const listbox = page.getByRole("listbox", {
    name: "Fornecedores sugeridos",
  });
  const firstOption = listbox.getByRole("option").first();
  await expect(firstOption).toBeVisible({ timeout: 15_000 });
  await expectWithinViewport(listbox);
  await shot("dropdown-open");

  /* Seleção preenche código + loja + razão social oficiais. */
  await firstOption.click();
  await expect(page.getByRole("listbox")).toHaveCount(0);
  const selected = page
    .locator(".engineering-prc__lookup-selected")
    .first();
  await expect(selected).toContainText(/\d+ \/ \d+ — .+/);
  await shot("supplier-selected");

  /* Segunda linha — busca por trecho de razão social fora da primeira
   * página: "TRES RIOS" casa BRITAGEM TRES RIOS LTDA (remoto, não
   * filtro local). Prova que a consulta roda antes da paginação. */
  await page.getByRole("button", { name: "+ Adicionar fornecedor" }).click();
  const inputs = page.getByRole("textbox", {
    name: "Buscar fornecedor por código ou nome",
  });
  await inputs.last().fill("TRES RIOS");
  const legalOption = listbox.getByRole("option", {
    name: /BRITAGEM TRES RIOS/,
  });
  await expect(
    legalOption,
    "razão social fora da página 1 deve aparecer",
  ).toBeVisible({ timeout: 15_000 });
  await expectWithinViewport(listbox);
  await shot("dropdown-last-row");

  /* Seleção confirma identidade oficial (código, loja, razão social). */
  await legalOption.click();
  const secondRow = page
    .locator(".engineering-prc__lookup-selected")
    .nth(1);
  await expect(secondRow).toContainText(/BRITAGEM TRES RIOS/);
  await expect(secondRow).toContainText(/\d+ \/ \d+/);

  /* Escape fecha o painel. */
  await page.keyboard.press("Escape");
  await expect(page.getByRole("listbox")).toHaveCount(0);

  /* Remover a linha não deixa dropdown órfão. */
  await page.getByRole("button", { name: "Remover" }).last().click();
  await expect(page.getByRole("listbox")).toHaveCount(0);

  expectNoFailures(forbidden, pageErrors);
});
