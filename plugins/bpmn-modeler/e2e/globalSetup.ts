import { request } from "@playwright/test";

/**
 * Readiness gate da suíte E2E: "container running" não é readiness.
 * Sonda endpoints autoritativos antes de liberar os testes — falha
 * cedo e com diagnóstico claro em vez de timeouts difusos no meio
 * da suíte (flake class: COMPOSE_STARTUP).
 */
const BASE = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
const TIMEOUT_MS = 120_000;
const POLL_MS = 2_000;

const CHECKS: { name: string; url: string }[] = [
  { name: "portal", url: "/" },
  {
    name: "keycloak realm",
    url: "/auth/realms/delpi/.well-known/openid-configuration",
  },
  { name: "bpmn-modeler frontend", url: "/apps/bpmn-modeler/" },
  { name: "bpmn-modeler-api health", url: "/apps/bpmn-modeler-api/health" },
];

export default async function globalSetup(): Promise<void> {
  const ctx = await request.newContext({ baseURL: BASE });
  const deadline = Date.now() + TIMEOUT_MS;
  const failures: string[] = [];

  for (const check of CHECKS) {
    let lastError = "no attempt";
    for (;;) {
      try {
        const resp = await ctx.get(check.url, {
          maxRedirects: 0,
          timeout: 10_000,
        });
        // 2xx/3xx: portal redireciona para /login quando anônimo —
        // redirect ainda prova que o serviço está respondendo.
        if (resp.status() < 500) break;
        lastError = `HTTP ${resp.status()}`;
      } catch (error) {
        lastError = error instanceof Error ? error.message : String(error);
      }
      if (Date.now() > deadline) {
        failures.push(`${check.name} (${check.url}): ${lastError}`);
        break;
      }
      await new Promise((r) => setTimeout(r, POLL_MS));
    }
  }

  // Probe funcional: o discovery doc responder <500 não prova que o
  // fluxo de login está warm — pós-boot o KC pode servir metadata mas
  // falhar grants. Um password-grant real com o actor editor fecha a
  // janela "ready mas não funcional" observada em runs pós-restart.
  const user = process.env.BPMN_E2E_USER_EDITOR;
  const pass = process.env.BPMN_E2E_PASS_EDITOR;
  if (user && pass) {
    let lastError = "no attempt";
    let ok = false;
    while (Date.now() <= deadline) {
      try {
        const resp = await ctx.post(
          "/auth/realms/delpi/protocol/openid-connect/token",
          {
            form: {
              client_id: "delpi-central",
              grant_type: "password",
              username: user,
              password: pass,
            },
            timeout: 10_000,
          },
        );
        if (resp.ok()) {
          ok = true;
          break;
        }
        lastError = `HTTP ${resp.status()}`;
      } catch (error) {
        lastError = error instanceof Error ? error.message : String(error);
      }
      await new Promise((r) => setTimeout(r, POLL_MS));
    }
    if (!ok) failures.push(`keycloak token grant (editor): ${lastError}`);
  }

  await ctx.dispose();
  if (failures.length) {
    throw new Error(
      `E2E readiness gate falhou — serviços não prontos em ${TIMEOUT_MS}ms:\n` +
        failures.map((f) => `  - ${f}`).join("\n"),
    );
  }
}
