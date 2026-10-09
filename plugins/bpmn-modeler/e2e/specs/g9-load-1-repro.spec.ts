import { request } from "@playwright/test";
import { test, expect, apiToken, loginAs } from "../helpers";

/**
 * G9-LOAD-1 — reprodução real do carregamento infinito do BPMN no
 * Transformômetro. Spec DIAGNÓSTICA: instrumenta network/console e
 * reporta o estágio exato onde o fluxo trava (document / working-copy /
 * viewer-create / import-xml / fit-viewport / remount loop).
 *
 * Runtime real: gateway + MFE transformometro + transformometro-api.
 */

const TM_API = "/apps/transformometro-api/transformometro";
const BASE = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
const RUN = `g9load-${Date.now().toString(36)}`;

type Actor = "manager" | "viewer" | "editor";

const XML = [
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"',
  ' xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"',
  ' xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"',
  ' xmlns:di="http://www.omg.org/spec/DD/20100524/DI"',
  ' id="Defs_g9load" targetNamespace="http://bpmn.io/schema/bpmn">',
  '<bpmn:process id="Proc_g9load" isExecutable="false">',
  '<bpmn:startEvent id="Start_1" name="Início"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent>',
  '<bpmn:task id="Task_1" name="Dados são tratados e indicadores calculados automaticamente">',
  "<bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:task>",
  '<bpmn:endEvent id="End_1" name="Fim"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent>',
  '<bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="Task_1"/>',
  '<bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="End_1"/>',
  "</bpmn:process>",
  '<bpmndi:BPMNDiagram id="Diag_1"><bpmndi:BPMNPlane id="Plane_1" bpmnElement="Proc_g9load">',
  '<bpmndi:BPMNShape id="Start_1_di" bpmnElement="Start_1"><dc:Bounds x="100" y="100" width="36" height="36"/></bpmndi:BPMNShape>',
  '<bpmndi:BPMNShape id="Task_1_di" bpmnElement="Task_1"><dc:Bounds x="200" y="78" width="220" height="80"/></bpmndi:BPMNShape>',
  '<bpmndi:BPMNShape id="End_1_di" bpmnElement="End_1"><dc:Bounds x="480" y="100" width="36" height="36"/></bpmndi:BPMNShape>',
  '<bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1"><di:waypoint x="136" y="118"/><di:waypoint x="200" y="118"/></bpmndi:BPMNEdge>',
  '<bpmndi:BPMNEdge id="Flow_2_di" bpmnElement="Flow_2"><di:waypoint x="420" y="118"/><di:waypoint x="480" y="118"/></bpmndi:BPMNEdge>',
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>",
  "</bpmn:definitions>",
].join("");

async function api(
  actor: Actor,
  method: string,
  path: string,
  body?: unknown,
) {
  const token = await apiToken(actor);
  const ctx = await request.newContext({ baseURL: BASE });
  return ctx.fetch(path, {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    data: body ? JSON.stringify(body) : undefined,
  });
}

/** Telemetria de página: requests BPMN + console + pageerror. */
function instrument(page: import("@playwright/test").Page) {
  const log: string[] = [];
  const counts = { doc: 0, wc: 0 };
  const t0 = Date.now();
  const mark = (m: string) => {
    const line = `[${String(Date.now() - t0).padStart(5)}ms] ${m}`;
    log.push(line);
    console.log(`    [repro] ${line}`);
  };
  page.on("request", (r) => {
    const u = r.url();
    if (u.includes("/bpmn-document") && !u.includes("working-copy")) {
      counts.doc += 1;
      mark(`REQ document #${counts.doc} ${r.method()}`);
    }
    if (u.includes("/bpmn-document/working-copy")) {
      counts.wc += 1;
      mark(`REQ working-copy #${counts.wc} ${r.method()}`);
    }
  });
  page.on("response", (r) => {
    const u = r.url();
    if (u.includes("/bpmn-document")) {
      mark(`RES ${r.status()} ${u.includes("working-copy") ? "working-copy" : "document"}`);
    }
  });
  page.on("pageerror", (e) => mark(`PAGEERROR ${e.name}: ${e.message}`));
  page.on("console", (m) => {
    if (m.type() === "error" || m.type() === "warning") {
      mark(`CONSOLE.${m.type()} ${m.text().slice(0, 300)}`);
    }
  });
  return { log, counts };
}

async function gotoPage(page: import("@playwright/test").Page, url: string) {
  await page.goto(url);
  const sso = page.getByRole("button", { name: /Entrar com DELPI SSO/ });
  const landed = await Promise.race([
    page
      .locator(".bpmnm-page, [data-testid='bpmn-preview'], [data-testid='bpmn-card']")
      .first()
      .waitFor({ state: "visible", timeout: 25_000 })
      .then(() => "app" as const)
      .catch(() => null),
    sso
      .waitFor({ state: "visible", timeout: 25_000 })
      .then(() => "login" as const)
      .catch(() => null),
  ]);
  if (landed === "login") {
    await loginAs(page, "manager");
    await page.goto(url);
  }
}

test.describe("G9-LOAD-1 — reprodução do carregamento infinito", () => {
  test.describe.configure({ mode: "serial" });
  test.use({ actor: "manager", viewport: { width: 1440, height: 900 } });
  test.setTimeout(240_000);

  let processoId = "";

  test.beforeAll(async () => {
    // G9_PROC_ID: reutiliza um processo real já provisionado no runtime
    // (ex.: doc com lanes/participant) em vez de criar fixture nova.
    const existing = process.env.G9_PROC_ID;
    if (existing) {
      processoId = existing;
      const doc = await api(
        "manager",
        "GET",
        `${TM_API}/processos/${processoId}/bpmn-document`,
      );
      expect(doc.status(), `bpmn-document: ${await doc.text()}`).toBe(200);
      return;
    }
    const proc = await api("manager", "POST", `${TM_API}/processos`, {
      nome_processo: `G9-LOAD-1 ${RUN}`,
      status_processo: "ativo",
    });
    expect(proc.status()).toBe(201);
    processoId = (await proc.json()).data.processo_id;

    const doc = await api(
      "manager",
      "POST",
      `${TM_API}/processos/${processoId}/bpmn-document`,
      { xml: XML },
    );
    expect(doc.status(), `create bpmn-document: ${await doc.text()}`).toBe(201);
  });

  test("REPRO-EDITOR — /bpmn alcança estado terminal (ready/error)", async ({
    page,
  }) => {
    const probe = instrument(page);
    await gotoPage(page, `/apps/transformometro/processes/${processoId}/bpmn`);

    const canvas = page.getByLabel("Canvas do diagrama BPMN");
    const rendered = await canvas
      .waitFor({ state: "visible", timeout: 60_000 })
      .then(async () => {
        // espera elementos do vendor OU erro de página
        const ok = await page
          .locator(".bpmnm-canvas .djs-element, .bpmnm-error")
          .first()
          .waitFor({ state: "visible", timeout: 30_000 })
          .then(() => true)
          .catch(() => false);
        return ok;
      })
      .catch(() => false);

    const saveLabel = await page
      .locator(".bpmnm-save, [class*='save'], .bpmnm-editor__header")
      .first()
      .innerText()
      .catch(() => "(header indisponível)");
    console.log(`    [repro] editor rendered=${rendered} header="${saveLabel}"`);
    console.log(
      `    [repro] doc reqs=${probe.counts.doc} wc reqs=${probe.counts.wc}`,
    );
    expect(rendered, "editor nunca alcançou estado terminal — ver log").toBe(
      true,
    );
  });

  test("REPRO-HANG — working-copy pendurada deve terminar em erro (não LOADING)", async ({
    page,
  }) => {
    // Fault injection: a request de working-copy nunca resolve. Sem
    // timeout/abort o sintoma real do usuário se reproduz: LOADING eterno.
    // PASS = estado terminal ERROR + "Tentar novamente" dentro do budget.
    await page.route("**/bpmn-document/working-copy", (route) => {
      // nunca resolve — simula request travada na rede/proxy
    });
    const probe = instrument(page);
    await gotoPage(page, `/apps/transformometro/processes/${processoId}/bpmn`);

    const retry = page.getByRole("button", { name: "Tentar novamente" });
    const terminal = await Promise.race([
      retry
        .waitFor({ state: "visible", timeout: 40_000 })
        .then(() => "error-retry" as const),
      page
        .locator(".bpmnm-canvas .djs-element")
        .first()
        .waitFor({ state: "visible", timeout: 40_000 })
        .then(() => "ready" as const),
    ]).catch(() => "stuck");

    console.log(`    [repro] hang→terminal=${terminal} wc reqs=${probe.counts.wc}`);
    expect(terminal, "working-copy pendurada deixou editor em LOADING eterno").toBe(
      "error-retry",
    );
  });

  test("REPRO-PREVIEW — card alcança viewer ready/error", async ({ page }) => {
    const probe = instrument(page);
    await gotoPage(page, `/apps/transformometro/processes/${processoId}#diagrama`);

    const preview = page.getByTestId("bpmn-preview");
    await expect(preview).toBeVisible({ timeout: 60_000 });

    const viewer = page.getByTestId("bpmn-readonly-viewer");
    let status = "(ausente)";
    for (let i = 0; i < 30; i++) {
      status = await viewer.getAttribute("data-status").catch(() => "(ausente)");
      if (status && status !== "loading") break;
      await page.waitForTimeout(1_000);
    }
    console.log(`    [repro] preview viewer data-status final="${status}"`);
    console.log(
      `    [repro] doc reqs=${probe.counts.doc} wc reqs=${probe.counts.wc}`,
    );
    expect(
      status,
      "preview ficou em loading >30s — ver log de estágio",
    ).not.toBe("loading");
  });

  test("REPRO-NAV — processo → editor → processo → editor 3× sem travar", async ({
    page,
  }) => {
    const probe = instrument(page);
    const processUrl = `/apps/transformometro/processes/${processoId}#diagrama`;
    const editorUrl = `/apps/transformometro/processes/${processoId}/bpmn`;

    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(`${e.name}: ${e.message}`));

    for (let round = 1; round <= 3; round++) {
      await gotoPage(page, processUrl);
      const viewer = page.getByTestId("bpmn-readonly-viewer");
      await expect(viewer).toBeVisible({ timeout: 60_000 });
      const status = await viewer.getAttribute("data-status");
      expect(
        status,
        `round ${round}: preview não saiu de loading`,
      ).not.toBe("loading");

      await gotoPage(page, editorUrl);
      const terminal = await Promise.race([
        page
          .locator(".bpmnm-canvas .djs-element")
          .first()
          .waitFor({ state: "visible", timeout: 40_000 })
          .then(() => "ready" as const),
        page
          .getByRole("button", { name: "Tentar novamente" })
          .waitFor({ state: "visible", timeout: 40_000 })
          .then(() => "error" as const),
      ]).catch(() => "stuck");
      expect(
        terminal,
        `round ${round}: editor ficou em LOADING eterno`,
      ).not.toBe("stuck");

      // instâncias duplicadas de canvas = remount loop / adapter leak
      const canvases = await page.locator(".bpmnm-canvas .djs-viewport").count();
      expect(canvases, `round ${round}: ${canvases} viewports`).toBeLessThanOrEqual(1);
    }

    console.log(
      `    [repro] nav 3x: doc reqs=${probe.counts.doc} wc reqs=${probe.counts.wc} pageerrors=${errors.length}`,
    );
    expect(
      errors.filter(
        (e) => !e.includes("sandbox") && !e.includes("iframe"),
      ),
      "exceções de página durante a navegação",
    ).toEqual([]);
  });
});
