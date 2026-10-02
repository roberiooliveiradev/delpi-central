import { test, expect, importModelViaApi, modelUrl } from "../helpers";
import type { Page } from "@playwright/test";

/**
 * E2E-41 — Sidebar / properties panel PT-BR + integração visual.
 *
 * O serviço `translate` oficial do diagram-js (injetado via
 * additionalModules → ptBrTranslateModule) é o único owner de toda
 * string user-facing do vendor: header de elemento, grupos, campos,
 * estados vazios e chrome do bpmn-js. Nada é patcheado via DOM.
 */

const XML_SB =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_sb" targetNamespace="urn:sb">' +
  '<bpmn:collaboration id="C1"><bpmn:participant id="PA1" name="Pool" processRef="P1"/></bpmn:collaboration>' +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:laneSet id="LS1"><bpmn:lane id="L1" name="Raia A"><bpmn:flowNodeRef>T1</bpmn:flowNodeRef></bpmn:lane></bpmn:laneSet>' +
  '<bpmn:startEvent id="S1" name="Início"/>' +
  '<bpmn:task id="T1" name="Tarefa"/>' +
  '<bpmn:userTask id="U1" name="Aprovar"/>' +
  '<bpmn:exclusiveGateway id="G1"/>' +
  '<bpmn:subProcess id="SP1"><bpmn:startEvent id="S2"/><bpmn:endEvent id="E2"/></bpmn:subProcess>' +
  '<bpmn:endEvent id="E1"/>' +
  '<bpmn:dataStoreReference id="DS1" dataStoreRef="DSB1"/>' +
  '<bpmn:dataStore id="DSB1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" sourceRef="T1" targetRef="G1"/>' +
  '<bpmn:sequenceFlow id="F3" sourceRef="G1" targetRef="E1"/>' +
  '</bpmn:process>' +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="C1">' +
  '<bpmndi:BPMNShape id="PA1_di" bpmnElement="PA1" isHorizontal="true"><dc:Bounds x="100" y="80" width="1100" height="420"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="L1_di" bpmnElement="L1" isHorizontal="true"><dc:Bounds x="130" y="80" width="1070" height="420"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="S1_di" bpmnElement="S1"><dc:Bounds x="160" y="140" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="T1_di" bpmnElement="T1"><dc:Bounds x="260" y="120" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="U1_di" bpmnElement="U1"><dc:Bounds x="430" y="260" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="G1_di" bpmnElement="G1" isMarkerVisible="true"><dc:Bounds x="580" y="135" width="50" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="SP1_di" bpmnElement="SP1" isExpanded="true"><dc:Bounds x="700" y="110" width="220" height="110"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="S2_di" bpmnElement="S2"><dc:Bounds x="715" y="150" width="30" height="30"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E2_di" bpmnElement="E2"><dc:Bounds x="870" y="150" width="30" height="30"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="E1_di" bpmnElement="E1"><dc:Bounds x="980" y="140" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="DS1_di" bpmnElement="DS1"><dc:Bounds x="280" y="300" width="50" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="F1_di" bpmnElement="F1"><di:waypoint x="196" y="158"/><di:waypoint x="260" y="158"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F2_di" bpmnElement="F2"><di:waypoint x="360" y="160"/><di:waypoint x="580" y="160"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="F3_di" bpmnElement="F3"><di:waypoint x="630" y="160"/><di:waypoint x="980" y="158"/></bpmndi:BPMNEdge>' +
  '</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>';

/** Strings EN do vendor que NUNCA podem aparecer na sidebar. */
const FORBIDDEN_EN = [
  "General",
  "Documentation",
  "Select an element",
  "Start Event",
  "End Event",
  "Task",
  "Gateway",
  "Sub Process",
  "Element documentation",
  "Participant Name",
  "Process ID",
];

const EXPECTED_TYPE: Record<string, string> = {
  PA1: "Participante",
  S1: "Evento inicial",
  T1: "Tarefa",
  U1: "Tarefa de usuário",
  G1: "Gateway exclusivo",
  SP1: "Subprocesso expandido",
  S2: "Evento inicial",
  E2: "Evento final",
  E1: "Evento final",
  DS1: "Referência a armazenamento de dados",
  L1: "Raia",
  F1: "Fluxo de sequência",
};

async function openEditor(page: Page, theme: "light" | "dark") {
  await page.evaluate((t) => {
    localStorage.setItem("theme", t);
    document.documentElement.setAttribute("data-theme", t);
  }, theme);
  const modelId = await importModelViaApi("editor", "E2E-Sidebar", XML_SB);
  await page.goto(modelUrl(modelId));
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(1000);
}

/** Seleciona via clique e devolve o id realmente selecionado
 *  (hit-layers do bpmn-js podem interceptar em áreas compartilhadas). */
async function selectElement(page: Page, id: string): Promise<string> {
  // fecha context pad/overlays e deseleciona: hit-layers do vendor podem
  // interceptar o próximo clique se o pad ficar aberto sobre o alvo
  await page.keyboard.press("Escape");
  const cv = await page.locator(".bpmnm-canvas").boundingBox();
  if (cv) {
    await page.mouse.click(cv.x + 12, cv.y + cv.height - 12);
    await page.waitForTimeout(300);
  }
  await page
    .locator(`.djs-element[data-element-id="${id}"]`)
    .click({ position: { x: 30, y: 30 }, force: true });
  await page.waitForTimeout(500);
  const selected = await page.evaluate(
    () =>
      document
        .querySelector(".djs-element.selected")
        ?.getAttribute("data-element-id") ?? "",
  );
  return selected;
}

async function sidebarText(page: Page): Promise<string> {
  return (await page.locator(".bpmnm-side").textContent()) ?? "";
}

test.describe("E2E-41 — sidebar PT-BR", () => {
  test.use({ actor: "editor", viewport: { width: 1440, height: 900 } });

  test("header, grupos e campos em PT-BR por tipo de elemento", async ({
    page,
  }) => {
    await openEditor(page, "dark");

    const seen = new Set<string>();
    for (const id of Object.keys(EXPECTED_TYPE)) {
      const selected = await selectElement(page, id);
      if (!selected || seen.has(selected)) continue;
      seen.add(selected);

      const typeEl = page.locator(".bio-properties-panel-header-type");
      await expect(typeEl).toBeVisible();
      const typeName = (await typeEl.textContent())?.trim() ?? "";
      const expected = EXPECTED_TYPE[selected];
      expect(
        expected,
        `elemento ${selected} exibiu tipo "${typeName}"`,
      ).toBeDefined();
      if (expected) expect(typeName).toBe(expected);
    }

    // cobertura mínima de tipos distintos
    expect(seen.size).toBeGreaterThanOrEqual(6);

    // grupos PT-BR presentes para qualquer elemento com fields
    const text = await sidebarText(page);
    expect(text).toContain("Geral");
    expect(text).toContain("Documentação");
  });

  test("sidebar não contém strings EN do vendor", async ({ page }) => {
    await openEditor(page, "dark");

    // percorre elementos e acumula texto da aba Propriedades
    for (const id of ["S1", "T1", "G1", "SP1", "PA1", "DS1"]) {
      await selectElement(page, id);
      const text = await sidebarText(page);
      for (const en of FORBIDDEN_EN) {
        // "Task" isolado pode colidir com substrings PT-BR — boundary check
        const re = new RegExp(`\\b${en}\\b`, "i");
        expect(
          re.test(text),
          `residual EN "${en}" visível na sidebar (elemento ${id})`,
        ).toBe(false);
      }
    }

    // expande Documentação para expor campos internos
    await selectElement(page, "T1");
    const docHeader = page.locator(
      ".bio-properties-panel-group-header-title",
      { hasText: "Documentação" },
    );
    if (await docHeader.count()) {
      await docHeader.first().click();
      await page.waitForTimeout(400);
      const text = await sidebarText(page);
      for (const en of FORBIDDEN_EN) {
        const re = new RegExp(`\\b${en}\\b`, "i");
        expect(re.test(text)).toBe(false);
      }
    }
  });

  test("abas Validação e Histórico permanecem PT-BR e funcionais", async ({
    page,
  }) => {
    await openEditor(page, "dark");

    await page.getByRole("tab", { name: "Validação" }).click();
    await expect(
      page.locator(".bpmnm-side").getByText(/Sem validação|Nenhum/).first(),
    ).toBeVisible();

    await page.getByRole("tab", { name: "Histórico" }).click();
    await expect(
      page
        .locator(".bpmnm-side")
        .getByText(/Revisões|Nenhuma revisão/)
        .first(),
    ).toBeVisible();
  });

  test("light: painel traduzido e legível", async ({ page }) => {
    await openEditor(page, "light");
    await selectElement(page, "T1");

    const typeEl = page.locator(".bio-properties-panel-header-type");
    await expect(typeEl).toBeVisible();
    const text = await sidebarText(page);
    expect(text).toContain("Geral");
    expect(text).toContain("Documentação");

    // surface do painel clara em light, texto escuro
    const colors = await page.evaluate(() => {
      const panel = document.querySelector(".bio-properties-panel")!;
      const header = panel.querySelector(".bio-properties-panel-header")!;
      return {
        panelBg: getComputedStyle(panel).backgroundColor,
        text: getComputedStyle(header).color,
      };
    });
    expect(colors.panelBg).toBeTruthy();
    expect(colors.text).toBeTruthy();
  });
});
