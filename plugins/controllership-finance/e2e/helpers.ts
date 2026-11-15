import { expect, type Page } from "@playwright/test";

export type PortalCredentialKind =
  | "allowed"
  | "denied"
  | "cf_access"
  | "cf_manage"
  | "cf_lnf"
  | "cf_dre";

/** Credenciais HML (preferidas) ou DEV local. Nunca logar valores. */
export function portalCredentials(
  kind: PortalCredentialKind = "allowed",
): { user: string; pass: string } {
  if (kind === "denied") {
    const user =
      process.env.HML_DENIED_TEST_USERNAME || process.env.DEV_DENIED_USERNAME;
    const pass =
      process.env.HML_DENIED_TEST_PASSWORD || process.env.DEV_DENIED_PASSWORD;
    if (!user || !pass) {
      throw new Error(
        "HML_DENIED_TEST_USERNAME/PASSWORD (ou DEV_DENIED_*) ausentes.",
      );
    }
    return { user, pass };
  }
  if (kind === "cf_access") {
    const user = process.env.HML_CF_ACCESS_USERNAME || "cf-access";
    const pass = process.env.HML_CF_ACCESS_PASSWORD;
    if (!pass) throw new Error("HML_CF_ACCESS_PASSWORD ausente.");
    return { user, pass };
  }
  if (kind === "cf_manage") {
    const user = process.env.HML_CF_MANAGE_USERNAME || "cf-manage";
    const pass = process.env.HML_CF_MANAGE_PASSWORD;
    if (!pass) throw new Error("HML_CF_MANAGE_PASSWORD ausente.");
    return { user, pass };
  }
  if (kind === "cf_lnf") {
    const user = process.env.HML_CF_LNF_USERNAME || "cf-lnf";
    const pass = process.env.HML_CF_LNF_PASSWORD;
    if (!pass) throw new Error("HML_CF_LNF_PASSWORD ausente.");
    return { user, pass };
  }
  if (kind === "cf_dre") {
    const user = process.env.HML_CF_DRE_USERNAME || "cf-dre";
    const pass = process.env.HML_CF_DRE_PASSWORD;
    if (!pass) throw new Error("HML_CF_DRE_PASSWORD ausente.");
    return { user, pass };
  }
  const user =
    process.env.HML_TEST_USERNAME || process.env.DEV_PORTAL_USERNAME;
  const pass =
    process.env.HML_TEST_PASSWORD || process.env.DEV_PORTAL_PASSWORD;
  if (!user || !pass) {
    throw new Error(
      "HML_TEST_USERNAME/PASSWORD (ou DEV_PORTAL_*) ausentes.",
    );
  }
  return { user, pass };
}

export async function loginAs(
  page: Page,
  kind: PortalCredentialKind = "allowed",
): Promise<void> {
  const creds = portalCredentials(kind);
  await page.goto("/");
  if (!page.url().includes("/login")) {
    await page.waitForURL(/\/login/, { timeout: 30_000 }).catch(() => undefined);
  }
  await page.getByRole("button", { name: /Entrar com DELPI SSO/ }).click();
  const userField = page
    .getByRole("textbox", { name: /usuário|username|email/i })
    .first();
  const formShown = await userField
    .waitFor({ state: "visible", timeout: 15_000 })
    .then(() => true)
    .catch(() => false);
  if (formShown) {
    await userField.fill(creds.user);
    await page
      .getByRole("textbox", { name: /senha|password/i })
      .first()
      .fill(creds.pass);
    await page.getByRole("button", { name: /entrar|sign in|log in/i }).click();
  }
  await page.waitForURL(
    (url) =>
      !url.pathname.startsWith("/auth/") && !url.pathname.endsWith("/login"),
    { timeout: 45_000 },
  );
  await dismissPrivacyGate(page);
}

/** Primeiro login HML: aceita política/consentimentos se a tela aparecer. */
export async function dismissPrivacyGate(page: Page): Promise<void> {
  const privacyHeading = page.getByRole("heading", {
    name: /Política de Privacidade/i,
  });
  const shown = await privacyHeading
    .waitFor({ state: "visible", timeout: 5_000 })
    .then(() => true)
    .catch(() => false);
  if (!shown) return;

  // Role até o fim para habilitar o aceite (fluxo LGPD do Portal).
  for (let i = 0; i < 12; i += 1) {
    await page.keyboard.press("PageDown");
    await page.waitForTimeout(200);
  }
  const accept = page
    .getByRole("button", {
      name: /Aceitar|Concordo|Continuar|Li e aceito|Confirmar/i,
    })
    .first();
  if (await accept.isEnabled().catch(() => false)) {
    await accept.click();
  } else if (await accept.isVisible().catch(() => false)) {
    await accept.click({ force: true }).catch(() => undefined);
  }
  await privacyHeading
    .waitFor({ state: "hidden", timeout: 30_000 })
    .catch(() => undefined);
}

export async function openEntryAuditHome(page: Page): Promise<void> {
  await page.goto("/apps/controllership-finance/entry-audit");
  await expect(
    page
      .getByRole("heading", { name: /Auditoria de Entradas/i })
      .or(page.getByText("Executar auditoria"))
      .first(),
  ).toBeVisible({ timeout: 45_000 });
}

type Envelope<T> = { success: boolean; data: T };

/** Captura o summary da própria chamada Bearer do MFE (não re-fetch anônimo). */
export async function waitForSummaryKpis(
  page: Page,
): Promise<{ documents: number; high: number; occurrences: number }> {
  const response = await page.waitForResponse(
    (res) =>
      res.url().includes("/entry-audit/analyses/") &&
      res.url().includes("/summary") &&
      res.request().method() === "GET" &&
      res.ok(),
    { timeout: 45_000 },
  );
  const payload = (await response.json()) as Envelope<{
    kpis: { documents: number; high: number; occurrences: number };
  }>;
  return payload.data.kpis;
}
