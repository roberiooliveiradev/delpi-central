import { expect, type Page } from "@playwright/test";

/** Credenciais do usuário dev autorizado (infra/.env.local). Nunca
 * logar valores — apenas presença. */
export function devCredentials(): { user: string; pass: string } {
  const user = process.env.DEV_PORTAL_USERNAME;
  const pass = process.env.DEV_PORTAL_PASSWORD;
  if (!user || !pass) {
    throw new Error(
      "DEV_PORTAL_USERNAME/DEV_PORTAL_PASSWORD ausentes — " +
        "carregue infra/.env.local antes do E2E.",
    );
  }
  return { user, pass };
}

/** Login real: portal /login → "Entrar com DELPI SSO" → Keycloak →
 * redirect autenticado (mesmo fluxo canônico do harness bpmn-modeler). */
export async function loginAsDev(page: Page): Promise<void> {
  const creds = devCredentials();
  await page.goto("/");
  if (!page.url().includes("/login")) {
    await page.waitForURL(/\/login/, { timeout: 30_000 });
  }
  await page.getByRole("button", { name: /Entrar com DELPI SSO/ }).click();
  const userField = page
    .getByRole("textbox", { name: /usuário|username|email/i })
    .first();
  const formShown = await userField
    .waitFor({ state: "visible", timeout: 10_000 })
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
    { timeout: 30_000 },
  );
}

/** Guard de boundary: nenhuma chamada do MFE pode ir direto à api-delpi
 *  — todo dado NC vem de /apps/engineering-api/*. */
export function trackForbiddenApiCalls(page: Page): string[] {
  const hits: string[] = [];
  page.on("request", (request) => {
    const url = request.url();
    if (url.includes("/apps/api-delpi/")) {
      hits.push(`${request.method()} ${url}`);
    }
  });
  return hits;
}

/** Coleta erros de página (uncaught) — T6 exige zero pageerrors. */
export function trackPageErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(String(error)));
  return errors;
}

export async function expectNoFailures(
  pageErrors: string[],
  forbiddenCalls: string[],
): Promise<void> {
  expect(forbiddenCalls, "chamadas diretas à api-delpi pelo MFE").toEqual([]);
  expect(pageErrors, "pageerrors uncaught").toEqual([]);
}
