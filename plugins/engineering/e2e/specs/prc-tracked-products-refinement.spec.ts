import { expect, test, type Page } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  selectKitOption,
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

  await selectKitOption(page, "Versão de origem", "V1");
  await selectKitOption(page, "Versão de destino", "V2");
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

  /* Comparação em tabela única: grupos canônicos como rowheader
   * (`scope="rowgroup"`), sem repetir o thead por grupo. */
  await expect(
    page
      .getByRole("rowheader", { name: "Fornecedores" })
      .first(),
  ).toBeVisible();
  await expect(
    page.getByRole("rowheader", {
      name: /Identificação e classificação/,
    }),
  ).toBeVisible();

  await expectNoFailures(pageErrors, forbidden);
});

test("G1 — timeline do 30190123 classifica cobertura, não «mudança técnica»", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-final-timeline-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  await openProductDetail(page, "30190123");
  await page.getByRole("tab", { name: "Versões" }).click();
  await page.waitForURL(/tab=versions/, { timeout: 10_000 });
  await expect(
    page.getByRole("heading", { name: "Histórico de versões" }),
  ).toBeVisible({ timeout: 20_000 });

  /* V2 — «N diferenças registradas» com ressalva de cobertura:
   * nunca «N mudanças técnicas» quando a V1 é legado esparso. */
  const v2 = page
    .locator(".engineering-prc__vtimeline-item")
    .filter({ hasText: "V2" })
    .first();
  await expect(
    v2.getByText(/diferenças registradas/),
  ).toBeVisible();
  await expect(
    v2.getByText(/sem informação comparável na versão anterior/),
  ).toBeVisible();
  await expect(
    v2.getByText(/mudança\(s\) técnica\(s\)/),
  ).toHaveCount(0);

  /* V1 — baseline honesta: «campos registrados», nunca criação
   * TOTVS nem alteração do usuário. */
  const v1 = page
    .locator(".engineering-prc__vtimeline-item")
    .filter({ hasText: "V1" })
    .first();
  await expect(
    v1.getByText(/Primeiro acompanhamento confirmado/),
  ).toBeVisible();
  await expect(
    v1.getByText(/registrado/),
  ).toBeVisible();
  await shot("semantics");

  await expectNoFailures(pageErrors, forbidden);
});

test("G2 — ficha consolidada em density compact usa a largura", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-final-sheet-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  await openProductDetail(page, "30190123");
  /* Aba Ficha (default) — grid compacta auto-fit: ≥2 colunas em
   * viewports largos, 1 coluna em mobile, sem overflow. */
  const grid = page.locator(".delpi-prc__sheet-grid").first();
  await expect(grid).toBeVisible({ timeout: 20_000 });
  const columns = await grid.evaluate(
    (el) =>
      getComputedStyle(el).gridTemplateColumns
        .split(" ")
        .filter(Boolean).length,
  );
  const vw = await page.evaluate(() => window.innerWidth);
  if (vw >= 1024) {
    expect(columns).toBeGreaterThanOrEqual(3);
  } else if (vw <= 640) {
    expect(columns).toBe(1);
  } else {
    expect(columns).toBeGreaterThanOrEqual(2);
  }
  const overflow = await page.evaluate(
    () =>
      document.documentElement.scrollWidth >
      document.documentElement.clientWidth + 2,
  );
  expect(overflow, "overflow horizontal na ficha").toBe(false);
  await shot("compact-grid");

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

test("G4 — seletor de versões do kit: painel ancorado, teclado e Escape", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-select-${name}-${testInfo.project.name}.png`,
    });

  await openProductDetail(page, "30190123");
  await page.getByRole("tab", { name: "Versões" }).click();
  await page.waitForURL(/tab=versions/, { timeout: 10_000 });

  const heading = page.getByRole("heading", { name: "Comparar versões" });
  await expect(heading).toBeVisible({ timeout: 20_000 });

  /* Abertura por mouse — painel ancorado ao campo, sem cobrir o
   * título da seção e dentro da viewport (posicionamento do kit). */
  const fromTrigger = page.getByLabel("Versão de origem", {
    exact: true,
  });
  await expect(fromTrigger).toBeVisible();
  await fromTrigger.click();
  const listbox = page.getByRole("listbox").last();
  await expect(listbox).toBeVisible();
  await shot("open");

  const [panelBox, headingBox, triggerBox] = await Promise.all([
    listbox.boundingBox(),
    heading.boundingBox(),
    fromTrigger.boundingBox(),
  ]);
  expect(panelBox).not.toBeNull();
  expect(headingBox).not.toBeNull();
  expect(triggerBox).not.toBeNull();
  const overlapsHeading =
    panelBox!.x < headingBox!.x + headingBox!.width &&
    panelBox!.x + panelBox!.width > headingBox!.x &&
    panelBox!.y < headingBox!.y + headingBox!.height &&
    panelBox!.y + panelBox!.height > headingBox!.y;
  expect(overlapsHeading, "painel cobre o título da seção").toBe(false);
  const vw = await page.evaluate(() => window.innerWidth);
  expect(panelBox!.x).toBeGreaterThanOrEqual(0);
  expect(panelBox!.x + panelBox!.width).toBeLessThanOrEqual(vw + 1);
  const anchored =
    Math.abs(panelBox!.y - (triggerBox!.y + triggerBox!.height)) < 24 ||
    Math.abs(triggerBox!.y - (panelBox!.y + panelBox!.height)) < 24;
  expect(anchored, "painel desconectado do campo").toBe(true);

  /* Escape fecha o painel. */
  await page.keyboard.press("Escape");
  await expect(page.getByRole("listbox")).toHaveCount(0);
  await expect(fromTrigger).toBeVisible();

  /* Teclado: ArrowDown abre focando a 1ª opção; Enter seleciona e
   * devolve o foco ao trigger. */
  await fromTrigger.focus();
  await page.keyboard.press("ArrowDown");
  const kbList = page.getByRole("listbox").last();
  await expect(kbList).toBeVisible();
  await expect(
    kbList.getByRole("button", { name: "V1", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("listbox")).toHaveCount(0);
  await expect(fromTrigger).toContainText("V1");

  /* Destino + comparação server-side preservadas. */
  await selectKitOption(page, "Versão de destino", "V2");
  await page.getByRole("button", { name: "Comparar versões" }).click();
  await expect(
    page.getByRole("columnheader", { name: /Antes \(V/ }).first(),
  ).toBeVisible({ timeout: 20_000 });
  await shot("compared");

  await expectNoFailures(pageErrors, forbidden);
});
