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

  /* Abertura por mouse — o trigger está no fim da página e não
   * sobe com scroll: sem espaço abaixo o kit inverte para cima
   * (comportamento especificado); com espaço abre abaixo. Ambos
   * os ramos são verificados. */
  const fromTrigger = page.getByLabel("Versão de origem", {
    exact: true,
  });
  await expect(fromTrigger).toBeVisible();
  await fromTrigger.evaluate((el) =>
    el.scrollIntoView({ block: "nearest" }),
  );
  await page.waitForTimeout(400);
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
  const vw = await page.evaluate(() => window.innerWidth);
  const vh = await page.evaluate(() => window.innerHeight);
  /* Painel sempre dentro da viewport e ancorado ao campo — abaixo
   * quando há espaço, invertido acima quando não há (§6 do pacote). */
  expect(panelBox!.x).toBeGreaterThanOrEqual(0);
  expect(panelBox!.x + panelBox!.width).toBeLessThanOrEqual(vw + 1);
  expect(panelBox!.y).toBeGreaterThanOrEqual(0);
  expect(panelBox!.y + panelBox!.height).toBeLessThanOrEqual(vh + 1);
  const fitsBelow =
    triggerBox!.y + triggerBox!.height + panelBox!.height <= vh - 8;
  const anchored =
    Math.abs(panelBox!.y - (triggerBox!.y + triggerBox!.height)) < 24 ||
    Math.abs(triggerBox!.y - (panelBox!.y + panelBox!.height)) < 24;
  expect(anchored, "painel desconectado do campo").toBe(true);
  if (fitsBelow) {
    expect(
      panelBox!.y,
      "painel deveria abrir abaixo quando há espaço",
    ).toBeGreaterThanOrEqual(triggerBox!.y + triggerBox!.height - 24);
    const overlapsHeading =
      panelBox!.x < headingBox!.x + headingBox!.width &&
      panelBox!.x + panelBox!.width > headingBox!.x &&
      panelBox!.y < headingBox!.y + headingBox!.height &&
      panelBox!.y + panelBox!.height > headingBox!.y;
    expect(overlapsHeading, "painel cobre o título da seção").toBe(false);
  }

  /* Escape fecha o painel. */
  await page.keyboard.press("Escape");
  await expect(page.getByRole("listbox")).toHaveCount(0);
  await expect(fromTrigger).toBeVisible();

  /* Com espaço real abaixo (viewport mais alta), o painel abre
   * para baixo sem cobrir o título — ramo preferencial do §6. */
  if (!fitsBelow) {
    await page.setViewportSize({ width: vw, height: vh + 400 });
    await fromTrigger.evaluate((el) =>
      el.scrollIntoView({ block: "nearest" }),
    );
    await page.waitForTimeout(400);
    await fromTrigger.click();
    const list2 = page.getByRole("listbox").last();
    await expect(list2).toBeVisible();
    const [panel2, head2, trig2] = await Promise.all([
      list2.boundingBox(),
      heading.boundingBox(),
      fromTrigger.boundingBox(),
    ]);
    expect(
      panel2!.y,
      "com espaço, painel deve abrir abaixo do campo",
    ).toBeGreaterThanOrEqual(trig2!.y + trig2!.height - 24);
    const overlaps2 =
      panel2!.x < head2!.x + head2!.width &&
      panel2!.x + panel2!.width > head2!.x &&
      panel2!.y < head2!.y + head2!.height &&
      panel2!.y + panel2!.height > head2!.y;
    expect(
      overlaps2,
      "painel cobre o título mesmo com espaço abaixo",
    ).toBe(false);
    await shot("open-below");
    await page.keyboard.press("Escape");
    await expect(page.getByRole("listbox")).toHaveCount(0);
    await page.setViewportSize({ width: vw, height: vh });
  }

  /* Teclado: ArrowDown abre focando a 1ª opção («Selecione» —
   * allowEmpty); ArrowDown navega; Enter seleciona e devolve o
   * foco ao trigger. */
  await fromTrigger.focus();
  await page.keyboard.press("ArrowDown");
  const kbList = page.getByRole("listbox").last();
  await expect(kbList).toBeVisible();
  await expect(
    kbList.getByRole("button", { name: "Selecione", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
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

test("G5 — breadcrumb reflete a área: raiz, solicitações, produtos e detalhes", async ({
  page,
}, testInfo) => {
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-refine-g5-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });
  const crumbs = () => page.getByRole("navigation", { name: "Caminho da página" });

  /* Em viewports compactos o PagePath canônico recolhe ancestrais no
   * menu «…» (overflow). O helper resolve o link onde quer que esteja. */
  const crumbLink = async (nav: ReturnType<typeof crumbs>, name: string) => {
    const direct = nav.getByRole("link", { name });
    const overflow = nav.getByRole("button", {
      name: "Mostrar páginas anteriores",
    });
    await expect(direct.or(overflow)).toBeVisible({ timeout: 20_000 });
    if (await direct.isVisible().catch(() => false)) return direct;
    if ((await overflow.getAttribute("aria-expanded")) !== "true") {
      await overflow.click();
    }
    const item = page.getByRole("menuitem", { name });
    await expect(item).toBeVisible();
    return item;
  };

  /* 1) Fila: Início / C&CP / Solicitações. */
  await page.goto(QUEUE_PATH);
  await ensureAuthenticated(page);
  const navQueue = crumbs();
  await expect(
    navQueue.getByRole("link", { name: "Início" }),
  ).toBeVisible({ timeout: 20_000 });
  await crumbLink(navQueue, "Controle e Cadastro de Produtos");
  await expect(
    navQueue.locator('[aria-current="page"]'),
  ).toHaveText("Solicitações");

  /* 2) Área produtos: mesma raiz, segmento corrente troca. */
  await page.goto(`${QUEUE_PATH}?area=products`);
  await ensureAuthenticated(page);
  const navProducts = crumbs();
  await crumbLink(navProducts, "Controle e Cadastro de Produtos");
  await expect(
    navProducts.locator('[aria-current="page"]'),
  ).toHaveText("Produtos acompanhados", { timeout: 20_000 });
  await shot("breadcrumb-products");

  /* 3) Detalhe de produto: raiz + Produtos acompanhados + código. */
  await openProductDetail(page, "30190123");
  const navDetail = crumbs();
  await crumbLink(navDetail, "Controle e Cadastro de Produtos");
  const productsLink = await crumbLink(navDetail, "Produtos acompanhados");
  await expect(
    navDetail.locator('[aria-current="page"]'),
  ).toHaveText("30190123");

  /* 4) Link intermediário retorna à área correta (?area=products). */
  await productsLink.click();
  await page.waitForURL(/area=products/, { timeout: 15_000 });
  await expect(
    crumbs().locator('[aria-current="page"]'),
  ).toHaveText("Produtos acompanhados", { timeout: 20_000 });
  await shot("breadcrumb-back-to-products");

  /* 5) Detalhe de solicitação: raiz + Solicitações + #id. */
  await page.goto(QUEUE_PATH);
  await ensureAuthenticated(page);
  const firstEntry = page
    .getByRole("table")
    .locator("tbody tr")
    .first()
    .or(page.getByRole("button", { name: /Solicitação #/ }).first());
  await expect(firstEntry).toBeVisible({ timeout: 20_000 });
  await firstEntry.click();
  await page.waitForURL(/product-registration\/[0-9a-f-]{36}/, {
    timeout: 15_000,
  });
  const navReq = crumbs();
  const requestsLink = await crumbLink(navReq, "Solicitações");
  await expect(navReq.locator('[aria-current="page"]')).toHaveText(/^#/);

  /* 6) «Solicitações» volta à fila sem parâmetro de área (padrão). */
  await requestsLink.click();
  await page.waitForURL(/product-registration(\?|$)/, { timeout: 15_000 });
  await expect(
    crumbs().locator('[aria-current="page"]'),
  ).toHaveText("Solicitações", { timeout: 20_000 });

  await expectNoFailures(pageErrors, forbidden);
});
