import { expect, type Page } from "@playwright/test";

/** Credenciais HML (preferidas) ou DEV local. Nunca logar valores. */
export function portalCredentials(
  kind: "allowed" | "denied" = "allowed",
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
  kind: "allowed" | "denied" = "allowed",
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
}

export async function openEntryAuditHome(page: Page): Promise<void> {
  await page.goto("/apps/controllership-finance/entry-audit");
  await expect(
    page.getByRole("heading", { name: /Auditoria de Entradas/i }).first(),
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
