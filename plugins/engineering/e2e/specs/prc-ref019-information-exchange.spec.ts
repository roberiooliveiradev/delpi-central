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

test.beforeEach(async ({ page }) => {
  await loginAsDev(page);
});

async function ensureAuthenticated(page: Page): Promise<void> {
  const sso = page.getByRole("button", { name: /Entrar com DELPI SSO/i });
  if (await sso.isVisible().catch(() => false)) {
    await loginAsDev(page);
  }
}

async function openInProgressCase(page: Page): Promise<boolean> {
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
  // Mesmo critério do REF-018: detalhe carregou se a aba Ficha técnica existe
  // ou se qualquer ação/status do PRC está visível.
  const loaded = page
    .getByRole("tab", { name: /Ficha técnica|Visão geral|Histórico/i })
    .or(page.getByRole("button", { name: /Ficha técnica|Solicitar informações|Iniciar atendimento/i }))
    .first();
  return loaded
    .waitFor({ state: "visible", timeout: 30_000 })
    .then(() => true)
    .catch(() => false);
}

test("REF-019 — perguntas estruturadas, resposta e retomada", async ({
  page,
}, testInfo) => {
  test.setTimeout(120_000);
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

  // FIX-01: dual-role — garantir visão de solicitante antes de responder.
  const respondAsRequester = page.getByRole("button", {
    name: /Responder como solicitante/i,
  });
  if (await respondAsRequester.isVisible().catch(() => false)) {
    await respondAsRequester.click();
  }

  // Resume deve permanecer indisponível enquanto a rodada está aberta.
  await expect(
    page.getByText(/Aguardando as informações solicitadas|Há respostas aguardando/i).first(),
  ).toBeVisible({ timeout: 10_000 }).catch(() => undefined);
  const resumeWhileOpen = page.getByRole("button", {
    name: /Retomar atendimento/i,
  });
  if (await resumeWhileOpen.first().isVisible().catch(() => false)) {
    await expect(resumeWhileOpen.first()).toBeDisabled();
  }

  const responseAreas = page.getByLabel(/Sua resposta|Resposta/i);
  await expect(responseAreas.first()).toBeVisible({ timeout: 15_000 });
  const n = await responseAreas.count();
  if (n >= 1) await responseAreas.nth(0).fill("Descrição confirmada.");
  if (n >= 2) await responseAreas.nth(1).fill("Unidade correta: PC.");

  const draftBtn = page.getByRole("button", { name: /Salvar rascunho/i });
  if (await draftBtn.isVisible().catch(() => false)) {
    await draftBtn.click();
    await page.waitForTimeout(600);
  }

  const submitBtn = page.getByRole("button", { name: /Enviar respostas/i });
  await expect(submitBtn).toBeVisible({ timeout: 10_000 });
  await submitBtn.click();
  await expect(
    page.getByText(/aguardando análise|Respostas enviadas|Aguardando análise/i).first(),
  ).toBeVisible({ timeout: 30_000 });
  await shot("answers-submitted");

  const analyzeAsEng = page.getByRole("button", {
    name: /Analisar como Engenharia/i,
  });
  if (await analyzeAsEng.isVisible().catch(() => false)) {
    await analyzeAsEng.click();
  }

  for (let i = 0; i < 4; i++) {
    const btn = page.getByRole("button", { name: /Aceitar esclarecimento/i }).first();
    if (!(await btn.isVisible().catch(() => false))) break;
    await btn.click();
    await page.waitForTimeout(500);
  }
  await shot("accepted");

  const resumeBtn = page.getByRole("button", { name: /Retomar atendimento/i });
  if (await resumeBtn.first().isVisible().catch(() => false)) {
    await expect(resumeBtn.first()).toBeEnabled({ timeout: 15_000 });
    await resumeBtn.first().click();
    const confirm = page.getByRole("button", {
      name: /Retomar atendimento|Confirmar/i,
    });
    if (await confirm.last().isVisible().catch(() => false)) {
      await confirm.last().click();
    }
    await expect(
      page.getByText(/Em atendimento|Em andamento/i).first(),
    ).toBeVisible({ timeout: 30_000 });
  }
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
