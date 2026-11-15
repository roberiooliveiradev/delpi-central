import { test, expect, type Page, type Locator } from "@playwright/test";
import {
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
  expectNoFailures,
} from "../helpers";

/**
 * UX-V2 — hero/toolbar/sort parity (MYREQ-UX-V2-HERO-TOOLBAR-HEADER-SORT).
 *
 * AC02: toolbar real fisicamente dentro do hero (portal do kit).
 * AC03: grade logo abaixo, embedded, sem card redundante.
 * AC04: clique no cabeçalho → backend ordena, alterna dir, URL + aria-sort.
 * AC05: popup Ordenar reflete o sort do cabeçalho (sem estado velho).
 * AC06: só colunas do contrato têm affordance.
 */

const BASE = "/apps/my-requests";
const SHOT = (name: string) =>
  `artifacts/${test.info().project.name}-v2hero-${name}.png`;

const HERO = ".delpi-ui-page-hero";
const TOOLBAR_HOST = '[data-testid="request-list-toolbar-host"]';
const TOOLBAR = ".delpi-ui-table-toolbar";
const SECTION = ".delpi-ui-table-section--embedded";

async function loginAndGoto(page: Page, path: string): Promise<void> {
  await loginAsDev(page);
  await page.goto(path);
  await page
    .locator(HERO)
    .first()
    .waitFor({ state: "visible", timeout: 30_000 });
}

/** Usuário pode não ter permissão de processador — estado honesto. */
async function isForbidden(page: Page): Promise<boolean> {
  return page
    .getByText(/sem permissão|não autorizado|forbidden/i)
    .first()
    .waitFor({ state: "visible", timeout: 6_000 })
    .then(() => true)
    .catch(() => false);
}

async function expectInsideRect(
  inner: Locator,
  outer: Locator,
  label: string,
): Promise<void> {
  const i = await inner.boundingBox();
  const o = await outer.boundingBox();
  expect(i, `${label}: toolbar host sem rect`).toBeTruthy();
  expect(o, `${label}: hero sem rect`).toBeTruthy();
  expect(i!.x).toBeGreaterThanOrEqual(o!.x - 1);
  expect(i!.y).toBeGreaterThanOrEqual(o!.y - 1);
  expect(i!.x + i!.width).toBeLessThanOrEqual(o!.x + o!.width + 1);
  expect(i!.y + i!.height).toBeLessThanOrEqual(o!.y + o!.height + 1);
}

/** Prova de backend: página 1 asc e desc devem trazer conjuntos
 *  diferentes quando há mais de uma página de dados. */
async function firstColumnTexts(page: Page, columnIndex: number) {
  return page.locator(`tbody tr td:nth-child(${columnIndex})`).allInnerTexts();
}

test.describe("UX-V2 — hero × grade × header-sort", () => {
  test("mine: controles dentro do hero, grade embedded abaixo", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    const forbidden = trackForbiddenApiCalls(page);
    await loginAndGoto(page, BASE);

    const hero = page.locator(HERO).first();
    const host = page.locator(TOOLBAR_HOST);
    await expect(host).toHaveCount(1);
    await expectInsideRect(host, hero, "mine/hero-toolbar");

    /* Uma única toolbar no documento — nenhuma duplicada na grade. */
    await expect(page.locator(TOOLBAR)).toHaveCount(1);
    await expect(page.locator(`${TOOLBAR_HOST} ${TOOLBAR}`)).toHaveCount(1);

    /* Controles exigidos no hero: busca, Filtros, Ordenar, Colunas,
     * itens/página, chips, Tabela|Cards. */
    const heroToolbar = page.locator(`${TOOLBAR_HOST} ${TOOLBAR}`);
    await expect(
      heroToolbar.getByRole("searchbox").or(heroToolbar.locator("input[type=search]")),
    ).toHaveCount(1);
    await expect(
      heroToolbar.getByRole("button", { name: /filtros/i }),
    ).toBeVisible();
    await expect(
      heroToolbar.getByRole("button", { name: /ordenar/i }),
    ).toBeVisible();
    await expect(
      heroToolbar.getByRole("button", { name: /colunas/i }),
    ).toBeVisible();
    await expect(
      heroToolbar.getByRole("button", {
        name: /quantidade de itens por página/i,
      }),
    ).toBeVisible();
    await expect(
      heroToolbar.getByRole("button", { name: /tabela|cards/i }).first(),
    ).toBeVisible();

    /* Grade logo abaixo do hero, embedded, sem seção-card duplicada. */
    const section = page.locator(SECTION);
    await expect(section).toHaveCount(1);
    const heroBox = await hero.boundingBox();
    const sectionBox = await section.boundingBox();
    expect(sectionBox).toBeTruthy();
    expect(sectionBox!.y).toBeGreaterThanOrEqual(heroBox!.y + heroBox!.height - 2);

    /* Breadcrumb navegável acima do hero. */
    const path = page
      .locator("nav[class*=page-path], [class*=page-path]")
      .first();
    const pathBox = await path.boundingBox();
    expect(pathBox).toBeTruthy();
    expect(pathBox!.y + pathBox!.height).toBeLessThanOrEqual(heroBox!.y + 2);

    /* AC06 — fonte mesclada: só a coluna Data é ordenável. */
    await expect(page.locator("th[aria-sort]")).toHaveCount(1);

    await page.screenshot({ path: SHOT("mine-hero"), fullPage: true });
    await expectNoFailures(pageErrors, forbidden);
  });

  test("mine: header Data alterna dir, URL e aria-sort; popup sincroniza", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    const forbidden = trackForbiddenApiCalls(page);
    await loginAndGoto(page, BASE);

    const th = page.locator("th[aria-sort]", { hasText: "Data" });
    await expect(th).toBeVisible();

    /* Padrão created_at:desc — primeiro clique alterna para asc. */
    const urlSort = () =>
      new URL(page.url()).searchParams.get("sort") ?? "";

    await th.getByRole("button").click();
    await expect.poll(urlSort).toBe("created_at:asc");
    await expect(th).toHaveAttribute("aria-sort", "ascending");
    await expect(th.getByRole("button")).toContainText("↑");

    await th.getByRole("button").click();
    await expect.poll(urlSort).toBe("created_at:desc");
    await expect(th).toHaveAttribute("aria-sort", "descending");
    await expect(th.getByRole("button")).toContainText("↓");

    /* Popup reflete o sort do cabeçalho (estado aplicado, não draft). */
    await page
      .getByRole("button", { name: /^Ordenar/i })
      .first()
      .click();
    const panel = page
      .locator("[class*=list-tools-popover], [role=dialog]")
      .last();
    await expect(panel).toBeVisible({ timeout: 5_000 });
    await expect(panel.getByText("Data").first()).toBeVisible();
    await page.keyboard.press("Escape");

    /* F5 preserva o sort via URL. */
    await page.reload();
    await page.locator(HERO).first().waitFor({ state: "visible" });
    await expect(page.locator("th[aria-sort]", { hasText: "Data" })).toHaveAttribute(
      "aria-sort",
      "descending",
    );

    await page.screenshot({ path: SHOT("mine-header-sort"), fullPage: true });
    await expectNoFailures(pageErrors, forbidden);
  });

  test("mine: itens por página real → page_size na URL", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    const forbidden = trackForbiddenApiCalls(page);
    await loginAndGoto(page, BASE);

    const sizeBtn = page.getByRole("button", {
      name: /quantidade de itens por página/i,
    });
    await sizeBtn.click();
    const listbox = page.getByRole("listbox").last();
    await expect(listbox).toBeVisible({ timeout: 5_000 });
    await listbox.getByRole("option", { name: "10" }).click();

    await expect.poll(() => page.url()).toContain("page_size=10");
    await expect
      .poll(async () => page.locator("tbody tr").count())
      .toBeLessThanOrEqual(10);

    await page.screenshot({ path: SHOT("mine-page-size"), fullPage: true });
    await expectNoFailures(pageErrors, forbidden);
  });

  test("work-queue: header Número ordena no backend (asc/desc)", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    const forbidden = trackForbiddenApiCalls(page);
    await loginAndGoto(page, `${BASE}/work-queue`);

    if (await isForbidden(page)) {
      test.info().annotations.push({
        type: "note",
        description:
          "usuário sem permissão de processador — estado forbidden honesto",
      });
      await page.screenshot({ path: SHOT("wq-forbidden"), fullPage: true });
      await expectNoFailures(pageErrors, forbidden);
      return;
    }

    const hero = page.locator(HERO).first();
    const host = page.locator(TOOLBAR_HOST);
    await expect(host).toHaveCount(1);
    await expectInsideRect(host, hero, "work-queue/hero-toolbar");
    await expect(page.locator(TOOLBAR)).toHaveCount(1);
    await expect(page.locator(SECTION)).toHaveCount(1);

    /* AC06 — 5 colunas ordenáveis (number/type/status/branch/date);
     * title/requester/completed_by sem affordance. */
    await expect(page.locator("th[aria-sort]")).toHaveCount(5);
    await expect(
      page.locator("th", { hasText: "Assunto" }).getByRole("button"),
    ).toHaveCount(0);
    await expect(
      page.locator("th", { hasText: "Solicitante" }).getByRole("button"),
    ).toHaveCount(0);
    await expect(
      page.locator("th", { hasText: "Concluída por" }).getByRole("button"),
    ).toHaveCount(0);

    const th = page.locator("th[aria-sort]", { hasText: "Número" });
    const rowCount = await page.locator("tbody tr").count();
    if (rowCount < 2) {
      test.info().annotations.push({
        type: "note",
        description: "menos de 2 linhas — ordenação visual não verificável",
      });
      return;
    }

    const urlSort = () =>
      new URL(page.url()).searchParams.get("sort") ?? "";

    /* asc: primeiro clique (campo texto → asc). */
    await th.getByRole("button").click();
    await expect.poll(urlSort).toBe("request_number:asc");
    await expect(th).toHaveAttribute("aria-sort", "ascending");

    const ascNumbers = (await firstColumnTexts(page, 1))
      .map((t) => t.trim())
      .filter(Boolean);
    const ascSorted = [...ascNumbers].sort((a, b) => a.localeCompare(b, "pt-BR"));
    expect(ascNumbers).toEqual(ascSorted);

    /* desc: segundo clique — backend traz outro conjunto de página 1. */
    await th.getByRole("button").click();
    await expect.poll(urlSort).toBe("request_number:desc");
    await expect(th).toHaveAttribute("aria-sort", "descending");

    const descNumbers = (await firstColumnTexts(page, 1))
      .map((t) => t.trim())
      .filter(Boolean);
    const descSorted = [...descNumbers].sort((a, b) =>
      b.localeCompare(a, "pt-BR"),
    );
    expect(descNumbers).toEqual(descSorted);

    /* Se há mais de uma página, asc/desc trazem conjuntos diferentes —
     * prova de ordenação global (não só da página carregada). */
    const pagination = page.getByText(/de \d+|of \d+|\d+ registros/i).first();
    await pagination.isVisible().catch(() => false);
    expect(ascNumbers[0]).not.toBe(descNumbers[0]);

    await page.screenshot({ path: SHOT("wq-header-sort"), fullPage: true });
    await expectNoFailures(pageErrors, forbidden);
  });

  test("work-queue: sem overflow horizontal", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    const forbidden = trackForbiddenApiCalls(page);
    await loginAndGoto(page, `${BASE}/work-queue`);
    if (await isForbidden(page)) return;

    const overflow = await page.evaluate(
      () =>
        document.documentElement.scrollWidth -
        document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
    await page.screenshot({ path: SHOT("wq-list"), fullPage: true });
    await expectNoFailures(pageErrors, forbidden);
  });
});
