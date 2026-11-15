import { expect, test, type Page } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
} from "../helpers";

/** Refinamento pós-HML (UX-P0/P1/P2): identidade pelo código
 * oficial, comparação presença-ciente, hero compacto, tema escuro,
 * zoom 200% e navegação por teclado. Massa HML:
 *  30190125 — V1 schema-2 com descrição literal '#'
 *  30190123 — V1 legado esparsa × V2 schema-2 populada. */
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

async function openProductDetail(
  page: Page,
  code: string,
): Promise<void> {
  await page.goto(`${QUEUE_PATH}?area=products&search=${code}`);
  await ensureAuthenticated(page);
  const row = page
    .getByRole("table")
    .locator("tbody tr")
    .filter({ hasText: code });
  await expect(row.first()).toBeVisible({ timeout: 20_000 });
  await row.first().click();
  await page.waitForURL(/product-registration\/products\//, {
    timeout: 15_000,
  });
  await ensureAuthenticated(page);
}

test("P0-01 — produto 30190125: código oficial é a identidade, '#' não vira título", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-refine-p001-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  await openProductDetail(page, "30190125");

  /* Identidade principal = heading com o código oficial. */
  await expect(
    page.getByRole("heading", { name: "30190125", exact: true }),
  ).toBeVisible({ timeout: 20_000 });

  /* Chip de versão acompanhada + metadados contextuais — também
   * espera o fade de entrada do page-hero antes da captura. */
  await expect(page.getByText("acompanhada")).toBeVisible();
  await expect(
    page.getByText("Última evolução técnica"),
  ).toBeVisible();
  await expect(page.getByText("Solicitação de origem")).toBeVisible();
  await shot("hero-official-code");

  await expectNoFailures(pageErrors, forbidden);
});

test("P0-02 — comparação V1×V2 do 30190123: «Sem dado» para campos não observados", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-refine-p002-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  await openProductDetail(page, "30190123");
  await page.getByRole("tab", { name: "Versões" }).click();
  await page.waitForURL(/tab=versions/, { timeout: 10_000 });
  await expect(
    page.getByRole("heading", { name: "Comparar versões" }),
  ).toBeVisible({ timeout: 20_000 });

  await page.getByLabel("Versão de origem").selectOption("1");
  await page.getByLabel("Versão de destino").selectOption("2");
  await page
    .getByRole("button", { name: "Comparar versões" })
    .click();

  /* V1 legado esparsa → campos não observados exibem «Sem dado
   * nesta versão» com a legenda explicativa — nunca '—' ambíguo
   * apresentado como remoção. */
  await expect(
    page.getByText(/Sem dado nesta versão/).first(),
  ).toBeVisible({ timeout: 20_000 });
  await expect(
    page.getByText(/não é remoção nem alteração comprovada/i),
  ).toBeVisible();
  await shot("compare-not-observed");

  /* Comparação agrupada pelos grupos canônicos da ficha. */
  await expect(
    page.getByRole("heading", { name: "Fornecedores" }).first(),
  ).toBeVisible();

  await expectNoFailures(pageErrors, forbidden);
});

test("UX — tema escuro + zoom 200% + teclado na área de produtos", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);

  /* Tema escuro via mecanismo canônico (localStorage 'theme'). */
  await page.addInitScript(() => {
    try {
      window.localStorage.setItem("theme", "dark");
    } catch {
      /* storage indisponível — mantém tema padrão */
    }
  });
  await page.goto(`${QUEUE_PATH}?area=products`);
  await ensureAuthenticated(page);
  await expect(page.getByRole("table")).toBeVisible({
    timeout: 20_000,
  });
  const theme = await page.evaluate(() =>
    document.documentElement.getAttribute("data-theme"),
  );
  expect(theme).toBe("dark");
  await page.screenshot({
    path: `e2e/artifacts/prc-refine-dark-${testInfo.project.name}.png`,
    fullPage: true,
  });

  /* Zoom 200% — sem overflow horizontal. */
  await page.evaluate(() => {
    document.documentElement.style.zoom = "200%";
  });
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth >
      document.documentElement.clientWidth + 2,
  );
  expect(overflow, "overflow horizontal em 200%").toBe(false);
  await page.screenshot({
    path: `e2e/artifacts/prc-refine-zoom200-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page.evaluate(() => {
    document.documentElement.style.zoom = "";
  });

  /* Teclado: Tab alcança o seletor de área e a busca; foco visível. */
  await page.getByRole("button", { name: "Solicitações", exact: true })
    .focus();
  await page.keyboard.press("Tab");
  const focused = await page.evaluate(
    () => document.activeElement?.tagName,
  );
  expect(["BUTTON", "INPUT", "A", "SELECT"]).toContain(focused);

  /* Enter no toggle alterna a área pela tecla. */
  await page.getByRole("button", { name: "Solicitações", exact: true })
    .focus();
  await page.keyboard.press("Enter");
  await page.waitForURL(
    (url) => !url.search.includes("area=products"),
    { timeout: 15_000 },
  );

  await expectNoFailures(pageErrors, forbidden);
});
