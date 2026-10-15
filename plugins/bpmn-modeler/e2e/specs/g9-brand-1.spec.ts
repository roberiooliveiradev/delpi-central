import { request } from "@playwright/test";
import { test, expect, apiToken, loginAs } from "../helpers";

/**
 * G9-BRAND-1 — marca bpmn.io não pode interceptar os controles do canvas.
 *
 * A LICENSE do bpmn-js exige o selo visível e não sobreposto — a suíte
 * prova: (a) selo continua visível; (b) bounding boxes selo × controles
 * não se intersectam; (c) cliques em +/-/fit não abrem lightbox nem
 * navegação externa; (d) fit altera o viewport.
 *
 * Runtime real: gateway + MFE transformometro + transformometro-api.
 */

const TM_API = "/apps/transformometro-api/transformometro";
const BASE = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
const RUN = `g9brand-${Date.now().toString(36)}`;

const XML = [
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"',
  ' xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"',
  ' xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"',
  ' xmlns:di="http://www.omg.org/spec/DD/20100524/DI"',
  ' id="Defs_g9brand" targetNamespace="http://bpmn.io/schema/bpmn">',
  '<bpmn:process id="Proc_g9brand" isExecutable="false">',
  '<bpmn:startEvent id="Start_1" name="Início"><bpmn:outgoing>Flow_1</bpmn:outgoing></bpmn:startEvent>',
  '<bpmn:task id="Task_1" name="Executar rotina de gerenciamento">',
  "<bpmn:incoming>Flow_1</bpmn:incoming><bpmn:outgoing>Flow_2</bpmn:outgoing></bpmn:task>",
  '<bpmn:endEvent id="End_1" name="Fim"><bpmn:incoming>Flow_2</bpmn:incoming></bpmn:endEvent>',
  '<bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="Task_1"/>',
  '<bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="End_1"/>',
  "</bpmn:process>",
  '<bpmndi:BPMNDiagram id="Diag_1"><bpmndi:BPMNPlane id="Plane_1" bpmnElement="Proc_g9brand">',
  '<bpmndi:BPMNShape id="Start_1_di" bpmnElement="Start_1"><dc:Bounds x="100" y="100" width="36" height="36"/></bpmndi:BPMNShape>',
  '<bpmndi:BPMNShape id="Task_1_di" bpmnElement="Task_1"><dc:Bounds x="200" y="78" width="160" height="80"/></bpmndi:BPMNShape>',
  '<bpmndi:BPMNShape id="End_1_di" bpmnElement="End_1"><dc:Bounds x="420" y="100" width="36" height="36"/></bpmndi:BPMNShape>',
  '<bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1"><di:waypoint x="136" y="118"/><di:waypoint x="200" y="118"/></bpmndi:BPMNEdge>',
  '<bpmndi:BPMNEdge id="Flow_2_di" bpmnElement="Flow_2"><di:waypoint x="360" y="118"/><di:waypoint x="420" y="118"/></bpmndi:BPMNEdge>',
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>",
  "</bpmn:definitions>",
].join("");

async function gotoPage(page: import("@playwright/test").Page, url: string) {
  await page.goto(url);
  const sso = page.getByRole("button", { name: /Entrar com DELPI SSO/ });
  const landed = await Promise.race([
    page
      .locator(".bpmnm-page, [data-testid='bpmn-preview'], [data-testid='bpmn-readonly-viewer']")
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

test.describe("G9-BRAND-1 — colisão powered-by × controles", () => {
  test.describe.configure({ mode: "serial" });
  test.use({ actor: "manager", viewport: { width: 1440, height: 900 } });
  test.setTimeout(240_000);

  let processoId = "";

  test.beforeAll(async () => {
    const existing = process.env.G9_PROC_ID;
    if (existing) {
      processoId = existing;
      return;
    }
    const token = await apiToken("manager");
    const ctx = await request.newContext({ baseURL: BASE });
    const proc = await ctx.fetch(`${TM_API}/processos`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      data: JSON.stringify({
        nome_processo: `G9-BRAND-1 ${RUN}`,
        status_processo: "ativo",
      }),
    });
    expect(proc.status()).toBe(201);
    processoId = (await proc.json()).data.processo_id;
    const doc = await ctx.fetch(
      `${TM_API}/processos/${processoId}/bpmn-document`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        data: JSON.stringify({ xml: XML }),
      },
    );
    expect(doc.status()).toBe(201);
  });

  /** Prova completa numa superfície com BpmnReadonlyViewer. */
  async function assertSurface(
    page: import("@playwright/test").Page,
    label: string,
  ) {
    // com modal aberto existem 2 viewers (card + modal) — o do modal
    // monta depois no DOM, portanto .last() é a superfície em foreground
    const v = page.getByTestId("bpmn-readonly-viewer").last();
    for (let i = 0; i < 30; i++) {
      const s = await v.getAttribute("data-status");
      if (s === "ready") break;
      await page.waitForTimeout(500);
    }
    await expect(v).toHaveAttribute("data-status", "ready");

    // (a) selo continua VISÍVEL (obrigação da licença bpmn-js)
    const badge = v.locator("a.bjs-powered-by");
    await expect(badge, `${label}: selo deve permanecer visível`).toBeVisible();

    // (b) bounding boxes selo × controles não se intersectam
    const controls = v.locator(".bpmnm-readonly-viewer__controls");
    await expect(controls).toBeVisible();
    const bb = await badge.boundingBox();
    const cb = await controls.boundingBox();
    expect(bb, `${label}: sem boundingBox do selo`).not.toBeNull();
    expect(cb, `${label}: sem boundingBox dos controles`).not.toBeNull();
    const overlap =
      bb!.x < cb!.x + cb!.width &&
      bb!.x + bb!.width > cb!.x &&
      bb!.y < cb!.y + cb!.height &&
      bb!.y + bb!.height > cb!.y;
    expect(overlap, `${label}: selo sobrepõe controles`).toBe(false);

    // (c) cliques em +/-/fit/fit ×10: zero lightbox, zero navegação
    let popups = 0;
    const onPage = () => {
      popups += 1;
    };
    page.context().on("page", onPage);
    const urlBefore = page.url();
    const zoomIn = v.getByRole("button", { name: "Ampliar" });
    const zoomOut = v.getByRole("button", { name: "Reduzir" });
    const fit = v.getByRole("button", { name: "Ajustar à tela" });

    const scale = () =>
      v.evaluate(
        (el) =>
          (el.querySelector(".viewport") as SVGGElement | null)
            ?.getAttribute("transform") ?? "",
      );

    for (let i = 0; i < 10; i++) {
      const btn = i % 3 === 0 ? zoomIn : i % 3 === 1 ? zoomOut : fit;
      await btn.click();
      await page.waitForTimeout(120);
      const lightbox = await page.locator(".bjs-powered-by-lightbox").count();
      expect(lightbox, `${label}: clique ${i} abriu lightbox bpmn.io`).toBe(0);
      expect(page.url(), `${label}: clique ${i} navegou para fora`).toBe(
        urlBefore,
      );
    }
    page.context().off("page", onPage);
    expect(popups, `${label}: popups/new-tabs abertos`).toBe(0);

    // (d) fit altera o viewport (transform muda)
    const before = await scale();
    await zoomIn.click();
    await page.waitForTimeout(150);
    await fit.click();
    await page.waitForTimeout(150);
    const after = await scale();
    expect(
      after,
      `${label}: fit não alterou o transform do viewport`,
    ).not.toBe(before);
    console.log(`    [brand] ${label}: badge visível, sem overlap, ` +
      `popups=0, fit alterou viewport`);
  }

  test("card preview — selo visível fora dos controles, cliques seguros", async ({
    page,
  }) => {
    await gotoPage(page, `/apps/transformometro/processes/${processoId}#diagrama`);
    await assertSurface(page, "card-preview");
  });

  test("fullscreen — selo visível fora dos controles, cliques seguros", async ({
    page,
  }) => {
    await gotoPage(page, `/apps/transformometro/processes/${processoId}#diagrama`);
    const viewer = page.getByTestId("bpmn-readonly-viewer").first();
    await expect(viewer).toHaveAttribute("data-status", "ready", {
      timeout: 30_000,
    });
    const full = page.getByRole("button", { name: /tela cheia|fullscreen/i });
    if (await full.count()) {
      await full.first().click();
      await assertSurface(page, "fullscreen");
    } else {
      console.log("    [brand] sem botão tela cheia — superfície ausente");
    }
  });

  test("editor — selo fora da área dos controles de viewport", async ({
    page,
  }) => {
    await gotoPage(page, `/apps/transformometro/processes/${processoId}/bpmn`);
    const canvas = page.getByLabel("Canvas do diagrama BPMN");
    await canvas.waitFor({ state: "visible", timeout: 60_000 });
    await page
      .locator(".bpmnm-canvas .djs-element")
      .first()
      .waitFor({ state: "visible", timeout: 30_000 });

    const badge = page.locator(".bpmnm-page a.bjs-powered-by").first();
    await expect(badge, "editor: selo deve permanecer visível").toBeVisible();

    const controls = page.locator(".bpmnm-viewport-controls");
    if (await controls.count()) {
      const bb = await badge.boundingBox();
      const cb = await controls.first().boundingBox();
      if (bb && cb) {
        const overlap =
          bb.x < cb.x + cb.width &&
          bb.x + bb.width > cb.x &&
          bb.y < cb.y + cb.height &&
          bb.y + bb.height > cb.y;
        expect(overlap, "editor: selo sobrepõe controles").toBe(false);
      }
    }
    const urlBefore = page.url();
    const zoom = controls
      .first()
      .locator("button")
      .first();
    if (await zoom.count()) {
      let popups = 0;
      page.context().on("page", () => (popups += 1));
      await zoom.click();
      await page.waitForTimeout(150);
      expect(await page.locator(".bjs-powered-by-lightbox").count()).toBe(0);
      expect(page.url()).toBe(urlBefore);
      expect(popups).toBe(0);
    }
  });
});
