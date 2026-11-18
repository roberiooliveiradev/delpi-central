import { test, expect, type Page } from "@playwright/test";

import {
  loginAsDev,
  trackPageErrors,
  expectNoFailures,
} from "../helpers";

/** Evidência E2E — Processos > Balanceamento de Linha (Yamazumi V3).
 *
 * Login SSO real → home do Portal Engenharia → card Processos → hub
 * compacto → ferramenta independente (sem Ficha do Produto) → consulta do
 * roteiro oficial por código → seleção explícita de filial/estágio →
 * parâmetros → análise oficial M1 → Yamazumi (postos, atribuição, gráfico
 * carga × takt) → cenário B → F5 restore → limpeza confirmada →
 * exportações → dark/light × viewports do config.
 *
 * Pré-condição: credenciais de teste (DEV_PORTAL_*) e stack no ar. */

const PRODUCT_WITH_ROUTING = "90264302";
const TOOL = "/apps/engineering/processes/line-balancing";
const SHOTS = "e2e/artifacts/processes-yamazumi";

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate(
    (t) => document.documentElement.setAttribute("data-theme", t),
    theme,
  );
  await page.waitForTimeout(400);
}

async function shot(page: Page, name: string) {
  await page.screenshot({
    path: `${SHOTS}/${name}-${test.info().project.name}.png`,
    fullPage: true,
  });
}

/** FilterSelect do kit: trigger button + listbox em portal (não é
 * <select> nativo). Escolhe a opção pelo texto visível. */
async function chooseOption(
  page: Page,
  triggerLabel: string,
  optionName: RegExp,
  triggerIndex = 0,
) {
  const trigger = page
    .getByRole("button", { name: triggerLabel, exact: true })
    .or(page.getByRole("combobox", { name: triggerLabel, exact: true }))
    .nth(triggerIndex);
  await trigger.click();
  const listbox = page.getByRole("listbox");
  await expect(listbox).toBeVisible({ timeout: 10_000 });
  await listbox
    .getByRole("option", { name: optionName })
    .or(listbox.getByRole("button", { name: optionName }))
    .first()
    .click();
  /* Em viewports estreitos o painel em portal pode permanecer aberto
   * após a seleção — fecha com Escape sem invalidar a escolha. */
  const closed = await page
    .getByRole("listbox")
    .waitFor({ state: "detached", timeout: 3_000 })
    .then(() => true)
    .catch(() => false);
  if (!closed) {
    await page.keyboard.press("Escape");
    await expect(page.getByRole("listbox")).toHaveCount(0);
  }
}

/** Abre a ferramenta, escolhe a origem oficial no card do Studio, carrega
 * o roteiro e seleciona o primeiro estágio (contexto sempre explícito). */
async function openToolAndLoadRouting(page: Page) {
  await page.goto(TOOL);
  await expect(
    page.getByRole("button", { name: /Produto DELPI/ }),
  ).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: /Produto DELPI/ }).click();
  await page.locator("#lb-product-code").fill(PRODUCT_WITH_ROUTING);
  await page.getByRole("button", { name: "Buscar roteiro" }).click();
  await expect(
    page.getByText(/Selecione a filial e o estágio produtivo/),
  ).toBeVisible({ timeout: 45_000 });
  await chooseOption(page, "Estágio produtivo", /^Estágio /);
  await expect(
    page.getByRole("heading", { name: "Operações oficiais do roteiro" }),
  ).toBeVisible({ timeout: 15_000 });
}

test.describe("Processos > Balanceamento de Linha — Yamazumi V3", () => {
  test.describe.configure({ mode: "serial" });

  let forbiddenCalls: string[] = [];

  test.beforeEach(async ({ page }) => {
    forbiddenCalls = [];
    page.on("request", (req) => {
      if (req.url().includes("/apps/api-delpi")) {
        forbiddenCalls.push(req.url());
      }
    });
    await loginAsDev(page);
  });

  test("card Processos no Início e hub de ferramentas", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await page.goto("/apps/engineering");
    await expect(
      page.getByText("Processos", { exact: true }).first(),
    ).toBeVisible({ timeout: 30_000 });
    await expect(
      page.getByRole("button", { name: /Balanceamento de Linha/ }).first(),
    ).toBeVisible();
    await shot(page, "lb-home-card-dark");

    /* Hub próprio — sem passar pela Ficha do Produto. */
    await page
      .getByRole("button", { name: /Engenharia de Processos/ })
      .first()
      .click();
    await expect(page).toHaveURL(/\/apps\/engineering\/processes$/, {
      timeout: 15_000,
    });
    await expect(
      page.getByRole("heading", { name: "Engenharia de Processos" }),
    ).toBeVisible({ timeout: 15_000 });
    await shot(page, "lb-hub-dark");

    await page.getByRole("button", { name: "Abrir ferramenta" }).click();
    await expect(page).toHaveURL(/processes\/line-balancing/);
    await expect(
      page.getByRole("heading", { name: "Balanceamento de Linha" }),
    ).toBeVisible();

    /* Hub compacto: só a ferramenta operacional — planejadas não ocupam a tela. */
    await page.goto("/apps/engineering/processes");
    await expect(
      page.getByRole("button", { name: "Abrir ferramenta" }),
    ).toBeVisible();
    await expect(page.getByText("Em planejamento")).toHaveCount(0);

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("consulta oficial, contexto explícito e operações deduplicadas", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await page.goto(TOOL);
    /* Entrada V4: dois cards grandes de origem + rail de métodos. */
    await expect(
      page.getByRole("button", { name: /Produto DELPI/ }),
    ).toBeVisible({ timeout: 30_000 });
    await expect(
      page.getByRole("button", { name: /Estudo manual/ }),
    ).toBeVisible();
    await shot(page, "lb-tool-idle");

    await page.getByRole("button", { name: /Produto DELPI/ }).click();
    await page.locator("#lb-product-code").fill(PRODUCT_WITH_ROUTING);
    await page.getByRole("button", { name: "Buscar roteiro" }).click();

    /* Contexto exigido: estágio precisa de seleção explícita. */
    await expect(
      page.getByText(/Selecione a filial e o estágio produtivo/),
    ).toBeVisible({ timeout: 45_000 });
    await chooseOption(page, "Estágio produtivo", /^Estágio /);
    await expect(
      page.getByRole("heading", { name: "Operações oficiais do roteiro" }),
    ).toBeVisible({ timeout: 15_000 });
    await shot(page, "lb-routing-loaded");

    /* Produto inexistente → estado honesto, nunca dados fictícios. */
    await page.getByRole("button", { name: "Trocar origem" }).click();
    await page.getByRole("button", { name: "Sim, trocar origem" }).click();
    await page.getByRole("button", { name: /Produto DELPI/ }).click();
    await page.locator("#lb-product-code").fill("00000000-INEXISTENTE");
    await page.getByRole("button", { name: "Buscar roteiro" }).click();
    await expect(
      page.getByText(/não encontrado|sem roteiro|vazio/i),
    ).toBeVisible({ timeout: 30_000 });
    await shot(page, "lb-not-found");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("catálogo M1–M6, análise oficial e Yamazumi do Studio", async ({
    page,
  }) => {
    const pageErrors = trackPageErrors(page);
    await openToolAndLoadRouting(page);

    /* Elemento do Line Balance Studio carregado com o estudo observado. */
    await expect(
      page.locator("delpi-line-balance-studio"),
    ).toBeAttached({ timeout: 15_000 });
    await expect(
      page.getByText(/Roteiro oficial · OBSERVED/),
    ).toBeVisible({ timeout: 15_000 });

    /* Rail interna de métodos: M5 ativo por padrão, recolhível. */
    const rail = page.locator(".delpi-ui-tool-rail");
    await expect(rail).toBeVisible();
    await expect(
      page.getByRole("button", { name: /M5 · Yamazumi/ }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Métodos de balanceamento" }),
    ).toHaveCount(0);
    if ((await rail.getAttribute("data-expanded")) === "true") {
      await page.getByRole("button", { name: "Recolher métodos" }).click();
      await expect(rail).toHaveAttribute("data-expanded", "false");
      await page.getByRole("button", { name: "Expandir métodos" }).click();
    }
    await shot(page, "lb-tool-entry");

    /* Troca de método conserva o estudo — painel M1 compartilha o
     * contexto (takt/cargas do mesmo estudo). */
    await page.getByRole("button", { name: /M1 · Capacidade e takt/ }).click();
    await expect(
      page.getByRole("heading", { name: "Capacidade e takt" }),
    ).toBeVisible();
    await expect(page.getByText(/Produto 90264302/).first()).toBeVisible();
    await page.getByRole("button", { name: /M5 · Yamazumi/ }).click();
    await expect(
      page.getByRole("heading", { name: "Yamazumi" }),
    ).toBeVisible();

    /* Condições no Studio → análise oficial M1 pelo contrato do domínio. */
    await page
      .getByRole("button", { name: "Condições de produção" })
      .click();
    await chooseOption(page, "Modo de turno", /^Minutos/);
    await page.getByLabel(/Duração \(min\)/).fill("480");
    await page.getByRole("button", { name: /Adicionar pausa/ }).click();
    await page.getByLabel(/Pausa 1 \(min\)/).fill("60");
    await page.getByLabel(/Demanda por turno/).fill("500");
    /* CommitInput do Studio confirma no blur — Tab garante o commit e o
     * study-change antes do clique (botão desabilitado até params.ok). */
    await page.getByLabel(/Demanda por turno/).press("Tab");
    const runBtn = page.getByRole("button", {
      name: "Executar análise oficial",
    });
    await expect(runBtn).toBeEnabled({ timeout: 10_000 });
    await runBtn.click();
    await expect(
      page.getByRole("heading", { name: /Análise oficial M1/ }),
    ).toBeVisible();
    await expect(page.getByText("Takt").first()).toBeVisible({
      timeout: 45_000,
    });
    await shot(page, "lb-m1-result");

    /* Yamazumi — postos e atribuição de operações (nome fica no input
     * CommitInput, não em texto). */
    await page
      .getByRole("button", { name: /Adicionar posto/ })
      .click();
    await page
      .getByRole("button", { name: /Adicionar posto/ })
      .click();
    await expect(page.getByLabel("Nome do posto 1")).toHaveValue("Posto 1");
    await expect(page.getByLabel("Nome do posto 2")).toHaveValue("Posto 2");

    /* Segunda operação local (PROVIDED) para distribuir entre postos —
     * o roteiro real tem uma única operação deduplicada. */
    await page
      .getByRole("button", { name: /Adicionar operação/ })
      .click();
    await chooseOption(page, "Posto da operação 1", /^Posto 1/);
    await chooseOption(page, "Posto da operação 2", /^Posto 2/);
    await shot(page, "lb-yamazumi-assigned");

    /* Reordenação por botão — alternativa acessível ao drag-and-drop. */
    await page
      .getByRole("button", { name: /Mover Posto 2 para cima/ })
      .click();
    await shot(page, "lb-yamazumi-reordered");

    /* Cenário B preserva o estudo A. */
    await page.getByRole("button", { name: /Novo cenário/ }).click();
    await expect(page.getByText("Cenário B").first()).toBeVisible();
    await shot(page, "lb-scenario-b");

    /* F5 → estudo restaurado no mesmo contexto (sessionStorage). */
    await page.reload();
    await page.getByRole("button", { name: /Produto DELPI/ }).click();
    await page.locator("#lb-product-code").fill(PRODUCT_WITH_ROUTING);
    await page.getByRole("button", { name: "Buscar roteiro" }).click();
    await expect(
      page.getByText(/Selecione a filial e o estágio produtivo/),
    ).toBeVisible({ timeout: 45_000 });
    await chooseOption(page, "Estágio produtivo", /^Estágio /);
    /* Rascunho restaurado: o seletor volta ao Cenário A e o B preservado
     * aparece como opção do seletor de cenários. */
    await expect(
      page.getByRole("combobox", { name: "Cenário" }),
    ).toContainText("Cenário", { timeout: 30_000 });
    await chooseOption(page, "Cenário", /^Cenário B/);
    await expect(
      page.getByRole("combobox", { name: "Cenário" }),
    ).toContainText("Cenário B");
    await shot(page, "lb-restored-after-f5");

    /* Limpar estudo → confirmação → rascunho removido. */
    await page.getByRole("button", { name: "Limpar estudo" }).click();
    await expect(
      page.getByText(/roteiro oficial consultado permanece intacto/),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Limpar", exact: true })
      .click();
    await expect(page.getByText("Cenário B")).toHaveCount(0);
    await shot(page, "lb-cleared");

    /* Estudo manual — segundo card, sem SKU, mesmo workspace. */
    await page.getByRole("button", { name: "Trocar origem" }).click();
    await page.getByRole("button", { name: "Sim, trocar origem" }).click();
    await page.getByRole("button", { name: /Estudo manual/ }).click();
    await page
      .getByLabel("Nome do estudo", { exact: true })
      .fill("Estudo manual E2E");
    await page.getByRole("button", { name: "Criar estudo" }).click();
    await expect(
      page.getByRole("heading", { name: "Yamazumi" }),
    ).toBeVisible({ timeout: 15_000 });
    await expect(
      page.getByText(/Estudo manual E2E/).first(),
    ).toBeVisible();
    await shot(page, "lb-manual-study");

    await setTheme(page, "light");
    await shot(page, "lb-tool-light");

    await expectNoFailures(pageErrors, forbiddenCalls);
  });

  test("exportações do Yamazumi e responsividade", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await openToolAndLoadRouting(page);

    await page.getByRole("button", { name: /Adicionar posto/ }).click();
    await chooseOption(page, "Posto da operação 1", /^Posto 1/);
    await expect(
      page.locator("delpi-line-balance-studio"),
    ).toBeAttached({ timeout: 15_000 });

    /* CSV / Excel / PDF pelo padrão corporativo de exportação. */
    const csvBtn = page.getByRole("button", { name: /CSV/ }).first();
    const xlsxBtn = page.getByRole("button", { name: /Excel/ }).first();
    const pdfBtn = page.getByRole("button", { name: /PDF/ }).first();
    await expect(csvBtn).toBeVisible();
    const [csvDl] = await Promise.all([
      page.waitForEvent("download", { timeout: 15_000 }),
      csvBtn.click(),
    ]);
    expect(csvDl.suggestedFilename()).toMatch(/\.csv$/i);
    const [xlsxDl] = await Promise.all([
      page.waitForEvent("download", { timeout: 15_000 }),
      xlsxBtn.click(),
    ]);
    expect(xlsxDl.suggestedFilename()).toMatch(/\.xlsx$/i);
    /* PDF corporativo usa iframe oculto de impressão (sem download). */
    await pdfBtn.click();
    const printFrame = page
      .frameLocator("iframe[data-delpi-document-print-frame]")
      .first();
    await expect(
      printFrame.getByText(/Balanceamento de Linha/i).first(),
    ).toBeAttached({ timeout: 15_000 });
    await shot(page, "lb-exports");

    /* Sem overflow horizontal da página no viewport atual. */
    const overflow = await page.evaluate(
      () =>
        document.documentElement.scrollWidth >
        document.documentElement.clientWidth + 4,
    );
    expect(overflow).toBe(false);

    await expectNoFailures(pageErrors, forbiddenCalls);
  });
});
