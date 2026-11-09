/**
 * PRC-REF-019 — rodadas de esclarecimento analista ↔ solicitante.
 * Fluxo com o mesmo usuário DEV (criador = solicitante = operador).
 */
import { expect, test, type Page } from "@playwright/test";

import {
  expectNoFailures,
  loginAsDev,
  trackForbiddenApiCalls,
  trackPageErrors,
} from "../helpers";

const QUEUE_PATH = "/apps/engineering/product-registration";

/** Casos elegíveis criados via API oficial (DEV) — CSV de UUIDs. */
function seededRequestIds(): string[] {
  return (process.env.PRC_REF019_REQUEST_IDS || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

test.beforeEach(async ({ page }) => {
  await loginAsDev(page);
});

async function ensureAuthenticated(page: Page): Promise<void> {
  const sso = page.getByRole("button", { name: /Entrar com DELPI SSO/i });
  if (await sso.isVisible().catch(() => false)) {
    await loginAsDev(page);
  }
}

async function detailLoaded(page: Page): Promise<boolean> {
  const loaded = page
    .getByRole("tab", { name: /Ficha técnica|Visão geral|Histórico/i })
    .or(
      page.getByRole("button", {
        name: /Ficha técnica|Solicitar informações|Iniciar atendimento/i,
      }),
    )
    .first();
  return loaded
    .waitFor({ state: "visible", timeout: 30_000 })
    .then(() => true)
    .catch(() => false);
}

async function openInProgressCase(page: Page): Promise<boolean> {
  const seeded = seededRequestIds();
  for (const id of seeded) {
    await page.goto(`${QUEUE_PATH}/${id}`);
    await ensureAuthenticated(page);
    if (await detailLoaded(page)) return true;
  }

  await page.goto(QUEUE_PATH);
  await ensureAuthenticated(page);
  const row = page.locator("tbody tr").first();
  const card = page.locator("[class*='interactive-data-card'], article").first();
  const hasRow = await row
    .waitFor({ state: "visible", timeout: 15_000 })
    .then(() => true)
    .catch(() => false);
  if (hasRow) {
    await row.click();
  } else {
    const hasCard = await card
      .waitFor({ state: "visible", timeout: 10_000 })
      .then(() => true)
      .catch(() => false);
    if (!hasCard) return false;
    await card.click();
  }
  await ensureAuthenticated(page);
  return detailLoaded(page);
}

test("REF-019 — perguntas estruturadas, resposta e retomada", async ({
  page,
}, testInfo) => {
  test.setTimeout(180_000);
  const forbidden = trackForbiddenApiCalls(page);
  const pageErrors = trackPageErrors(page);
  const shot = (name: string) =>
    page.screenshot({
      path: `e2e/artifacts/prc-ref019-${name}-${testInfo.project.name}.png`,
      fullPage: true,
    });

  const opened = await openInProgressCase(page);
  test.skip(!opened, "Fila in_progress vazia no DEV.");

  const startBtn = page.getByRole("button", { name: /Iniciar atendimento/i });
  if (await startBtn.isVisible().catch(() => false)) {
    await startBtn.click();
    await expect(startBtn).toHaveCount(0, { timeout: 20_000 });
  }

  const requestInfoBtn = page.getByRole("button", {
    name: /Solicitar informações/i,
  });
  test.skip(
    !(await requestInfoBtn.isVisible().catch(() => false)),
    "Caso sem request_information.",
  );

  await requestInfoBtn.click();
  await expect(
    page.getByRole("heading", { name: /Solicitar informações/i }),
  ).toBeVisible({ timeout: 10_000 });

  await page.getByLabel(/^Pergunta$/i).first().fill(
    "Confirme a descrição técnica correta do produto.",
  );
  await page.getByRole("button", { name: /Adicionar pergunta/i }).click();
  const questionFields = page.getByLabel(/^Pergunta$/i);
  await expect(questionFields).toHaveCount(2, { timeout: 5_000 });
  await questionFields.nth(1).fill("A unidade correta é MI ou PC?");

  await shot("analyst-modal");
  await page
    .getByRole("button", { name: /^Solicitar informações$/i })
    .last()
    .click();

  await expect(
    page
      .getByText(/Aguardando informações|Esclarecimentos com o solicitante/i)
      .first(),
  ).toBeVisible({ timeout: 30_000 });
  await shot("awaiting-requester");

  // FIX-02: sem toggle de papéis — formulário aparece automaticamente.
  await expect(
    page.getByRole("button", { name: /Responder como solicitante|Analisar como Engenharia/i }),
  ).toHaveCount(0);

  const resumeWhileOpen = page.getByRole("button", {
    name: /^Retomar atendimento$/i,
  });
  await expect(resumeWhileOpen).toHaveCount(0);

  const responseAreas = page.getByLabel(/Sua resposta/i);
  await expect(responseAreas.first()).toBeVisible({ timeout: 15_000 });
  const n = await responseAreas.count();
  if (n >= 1) await responseAreas.nth(0).fill("Descrição confirmada.");
  if (n >= 2) await responseAreas.nth(1).fill("Unidade correta: PC.");

  const draftBtn = page.getByRole("button", { name: /Salvar rascunho/i });
  await expect(draftBtn).toBeVisible();
  await draftBtn.click();
  await page.waitForTimeout(600);
  await page.reload();
  await ensureAuthenticated(page);
  await expect(page.getByLabel(/Sua resposta/i).first()).toBeVisible({
    timeout: 20_000,
  });
  await expect(page.getByLabel(/Sua resposta/i).first()).toHaveValue(
    /Descrição confirmada/,
  );

  const submitBtn = page.getByRole("button", { name: /Enviar respostas/i });
  await expect(submitBtn).toBeVisible({ timeout: 10_000 });
  await submitBtn.click();
  await expect(
    page.getByText(/Aguardando análise|Respostas enviadas|analisando os esclarecimentos/i).first(),
  ).toBeVisible({ timeout: 30_000 });
  await shot("answers-submitted");

  // Análise aparece automaticamente (sem trocar visão).
  await expect(
    page.getByRole("button", { name: /Aceitar esclarecimento/i }).first(),
  ).toBeVisible({ timeout: 20_000 });

  for (let i = 0; i < 6; i++) {
    const btn = page.getByRole("button", { name: /Aceitar esclarecimento/i }).first();
    const visible = await btn.isVisible().catch(() => false);
    if (!visible) break;
    await btn.click({ timeout: 5_000 }).catch(() => undefined);
    await page.waitForTimeout(800);
  }
  await expect(
    page.getByText(/avaliadas|Esclarecimento aceito|Histórico de esclarecimentos|pode ser retomado/i).first(),
  ).toBeVisible({ timeout: 30_000 });
  await shot("accepted");

  // Uma ação principal de retomada (cabeçalho).
  const resumeBtn = page.getByRole("button", { name: /^Retomar atendimento$/i });
  await expect(resumeBtn).toHaveCount(1, { timeout: 20_000 });
  await expect(resumeBtn).toBeEnabled();
  await resumeBtn.click();
  const dialogConfirm = page
    .locator('[role="dialog"], .delpi-ui-modal')
    .getByRole("button", { name: /^Retomar atendimento$/i })
    .last();
  if (await dialogConfirm.isVisible().catch(() => false)) {
    await dialogConfirm.click({ timeout: 10_000 });
  }
  await expect(
    page.getByText(/Em atendimento|Em andamento/i).first(),
  ).toBeVisible({ timeout: 30_000 });
  await shot("resumed");
  await expectNoFailures(pageErrors, forbidden);
});

test("REF-019 — modal valida pergunta vazia", async ({ page }, testInfo) => {
  const opened = await openInProgressCase(page);
  test.skip(!opened, "Fila in_progress vazia no DEV.");

  const startBtn = page.getByRole("button", { name: /Iniciar atendimento/i });
  if (await startBtn.isVisible().catch(() => false)) {
    await startBtn.click();
    await expect(startBtn).toHaveCount(0, { timeout: 20_000 });
  }

  const requestInfoBtn = page.getByRole("button", {
    name: /Solicitar informações/i,
  });
  test.skip(
    !(await requestInfoBtn.isVisible().catch(() => false)),
    "Sem request_information.",
  );

  await requestInfoBtn.click();
  await page
    .getByRole("button", { name: /^Solicitar informações$/i })
    .last()
    .click();
  await expect(page.getByText(/Escreva a pergunta/i).first()).toBeVisible({
    timeout: 5_000,
  });
  await page.screenshot({
    path: `e2e/artifacts/prc-ref019-validation-${testInfo.project.name}.png`,
    fullPage: true,
  });
});
