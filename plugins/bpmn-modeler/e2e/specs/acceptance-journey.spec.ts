import fs from "node:fs";
import path from "node:path";
import { request, type Page } from "@playwright/test";
import {
  test,
  expect,
  apiToken,
  importModelViaApi,
  modelUrl,
  waitSaved,
} from "../helpers";

const SHOTS = path.resolve(import.meta.dirname, "../../.tmp-shots");

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`) });
}

/**
 * ACC — jornada de acceptance final no portal integrado (§19–§24).
 *
 * Fixture cobre toda a superfície corrigida: Pool/participant, 2 lanes,
 * start/task/gateway/end, SubProcess expandido, data object, data store,
 * label externa (BPMNLabel) e Group com enclosure visual.
 */

const XML =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="defs_acc" targetNamespace="urn:acc">' +
  '<bpmn:collaboration id="C1">' +
  '<bpmn:participant id="PA1" name="Pool Acceptance" processRef="P1"/>' +
  "</bpmn:collaboration>" +
  '<bpmn:process id="P1" isExecutable="false">' +
  '<bpmn:laneSet id="LS1">' +
  '<bpmn:lane id="L1" name="Raia A">' +
  "<bpmn:flowNodeRef>S1</bpmn:flowNodeRef><bpmn:flowNodeRef>T1</bpmn:flowNodeRef>" +
  "<bpmn:flowNodeRef>GW1</bpmn:flowNodeRef>" +
  "</bpmn:lane>" +
  '<bpmn:lane id="L2" name="Raia B">' +
  "<bpmn:flowNodeRef>SP1</bpmn:flowNodeRef><bpmn:flowNodeRef>E1</bpmn:flowNodeRef>" +
  "<bpmn:flowNodeRef>DO1</bpmn:flowNodeRef><bpmn:flowNodeRef>DS1</bpmn:flowNodeRef>" +
  "</bpmn:lane>" +
  "</bpmn:laneSet>" +
  '<bpmn:startEvent id="S1" name="Início"/>' +
  '<bpmn:task id="T1" name="Tarefa A"/>' +
  '<bpmn:exclusiveGateway id="GW1" name="Decisão"/>' +
  '<bpmn:subProcess id="SP1" name="Sub">' +
  '<bpmn:startEvent id="S2"/><bpmn:task id="T2"/><bpmn:endEvent id="E2"/>' +
  '<bpmn:sequenceFlow id="SF1" sourceRef="S2" targetRef="T2"/>' +
  '<bpmn:sequenceFlow id="SF2" sourceRef="T2" targetRef="E2"/>' +
  "</bpmn:subProcess>" +
  '<bpmn:endEvent id="E1"/>' +
  '<bpmn:dataObject id="DOB1" name="DocObj"/>' +
  '<bpmn:dataObjectReference id="DO1" name="Doc" dataObjectRef="DOB1"/>' +
  '<bpmn:dataStore id="DSB1" name="BaseDS"/>' +
  '<bpmn:dataStoreReference id="DS1" name="Base" dataStoreRef="DSB1"/>' +
  '<bpmn:group id="GRP1"/>' +
  '<bpmn:sequenceFlow id="F1" sourceRef="S1" targetRef="T1"/>' +
  '<bpmn:sequenceFlow id="F2" name="sim" sourceRef="T1" targetRef="GW1"/>' +
  '<bpmn:sequenceFlow id="F3" sourceRef="GW1" targetRef="SP1"/>' +
  '<bpmn:sequenceFlow id="F4" sourceRef="SP1" targetRef="E1"/>' +
  "</bpmn:process>" +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="PL1" bpmnElement="C1">' +
  '<bpmndi:BPMNShape id="sh_PA1" bpmnElement="PA1" isHorizontal="true"><dc:Bounds x="80" y="60" width="760" height="460"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_L1" bpmnElement="L1" isHorizontal="true"><dc:Bounds x="110" y="60" width="730" height="230"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_L2" bpmnElement="L2" isHorizontal="true"><dc:Bounds x="110" y="290" width="730" height="230"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_S1" bpmnElement="S1"><dc:Bounds x="150" y="150" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_T1" bpmnElement="T1"><dc:Bounds x="240" y="138" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_GW1" bpmnElement="GW1"><dc:Bounds x="400" y="143" width="50" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_SP1" bpmnElement="SP1" isExpanded="true"><dc:Bounds x="160" y="330" width="260" height="140"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_S2" bpmnElement="S2"><dc:Bounds x="180" y="380" width="30" height="30"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_T2" bpmnElement="T2"><dc:Bounds x="250" y="360" width="100" height="80"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_E2" bpmnElement="E2"><dc:Bounds x="370" y="382" width="30" height="30"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_E1" bpmnElement="E1"><dc:Bounds x="560" y="355" width="36" height="36"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_DO1" bpmnElement="DO1"><dc:Bounds x="470" y="340" width="36" height="50"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNShape id="sh_DS1" bpmnElement="DS1"><dc:Bounds x="470" y="420" width="36" height="50"/></bpmndi:BPMNShape>' +
  // GRP1 envolve T1 (240..340) e GW1 (400..450) completamente
  '<bpmndi:BPMNShape id="sh_GRP1" bpmnElement="GRP1"><dc:Bounds x="225" y="120" width="250" height="100"/></bpmndi:BPMNShape>' +
  '<bpmndi:BPMNEdge id="e_F1" bpmnElement="F1"><di:waypoint x="186" y="168"/><di:waypoint x="240" y="178"/></bpmndi:BPMNEdge>' +
  // label externa: BPMNLabel deslocada do path da edge F2
  '<bpmndi:BPMNEdge id="e_F2" bpmnElement="F2"><di:waypoint x="340" y="178"/><di:waypoint x="400" y="168"/>' +
  '<bpmndi:BPMNLabel><dc:Bounds x="345" y="230" width="24" height="14"/></bpmndi:BPMNLabel></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F3" bpmnElement="F3"><di:waypoint x="425" y="193"/><di:waypoint x="290" y="330"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_F4" bpmnElement="F4"><di:waypoint x="420" y="390"/><di:waypoint x="560" y="373"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_SF1" bpmnElement="SF1"><di:waypoint x="210" y="395"/><di:waypoint x="250" y="400"/></bpmndi:BPMNEdge>' +
  '<bpmndi:BPMNEdge id="e_SF2" bpmnElement="SF2"><di:waypoint x="350" y="400"/><di:waypoint x="370" y="397"/></bpmndi:BPMNEdge>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram></bpmn:definitions>";

type Bounds = { x: number; y: number; width: number; height: number };

const encloses = (outer: Bounds, inner: Bounds) =>
  inner.x >= outer.x &&
  inner.y >= outer.y &&
  inner.x + inner.width <= outer.x + outer.width &&
  inner.y + inner.height <= outer.y + outer.height;

async function domBounds(page: Page, id: string): Promise<Bounds> {
  return page.evaluate((elId) => {
    const g = document.querySelector(
      `[data-element-id="${elId}"]`,
    ) as SVGGElement | null;
    if (!g) return null;
    const tf = g.getAttribute("transform") ?? "";
    const m =
      /translate\(([-\d.e]+)[ ,]+([-\d.e]+)\)/.exec(tf) ??
      /matrix\([-\d.e]+[ ,]+[-\d.e]+[ ,]+[-\d.e]+[ ,]+[-\d.e]+[ ,]+([-\d.e]+)[ ,]+([-\d.e]+)\)/.exec(
        tf,
      );
    const visual = g.querySelector(".djs-visual") as SVGGElement | null;
    const bb = (visual ?? g).getBBox();
    return {
      x: Number(m?.[1] ?? NaN),
      y: Number(m?.[2] ?? NaN),
      width: bb.width,
      height: bb.height,
    };
  }, id) as Promise<Bounds>;
}

async function apiXml(modelId: string): Promise<string> {
  const base = process.env.BPMN_E2E_BASE_URL ?? "http://localhost";
  const token = await apiToken("manager");
  const ctx = await request.newContext({ baseURL: base });
  const resp = await ctx.get(
    `/apps/bpmn-modeler-api/models/${modelId}/working-copy`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  return resp.text();
}

async function openModel(page: Page, modelId: string) {
  await page.goto(modelUrl(modelId));
  await expect(page.locator(".bpmnm-save-status")).toHaveText("Salvo", {
    timeout: 20_000,
  });
  await expect(
    page.locator('.djs-element[data-element-id="T1"]'),
  ).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(600);
}

test.describe("ACC — jornada de acceptance no portal", () => {
  test.use({ actor: "manager", viewport: { width: 1440, height: 900 } });
  test.setTimeout(300_000);

  test("edição, popup, undo/redo, sidebar e autosave", async ({ page }) => {
    const modelId = await importModelViaApi("manager", "ACC-Acceptance", XML);
    await openModel(page, modelId);

    // --- edit: rename via properties panel (campo Nome) ---
    await page.locator('.djs-element[data-element-id="T1"]').click({
      position: { x: 20, y: 20 },
      force: true,
    });
    const nameInput = page.getByLabel("Nome", { exact: true });
    await expect(nameInput).toBeVisible({ timeout: 10_000 });
    await nameInput.fill("Tarefa A Editada");
    await page.locator(".bpmnm-canvas").click({
      position: { x: 700, y: 40 },
      force: true,
    });
    await waitSaved(page);
    expect(await apiXml(modelId)).toContain("Tarefa A Editada");

    // --- popup do editor ampliado (documentação) ---
    await page.locator('.djs-element[data-element-id="T1"]').click({
      position: { x: 20, y: 20 },
      force: true,
    });
    await page.waitForTimeout(500);
    const launcher = page
      .locator(".bio-properties-panel-open-feel-popup")
      .first();
    await expect(launcher).toHaveAttribute("title", "Abrir editor ampliado");
    await launcher.locator("xpath=..").hover();
    await launcher.click({ force: true });
    const popup = page.locator(".bio-properties-panel-popup");
    await expect(popup).toBeVisible({ timeout: 8000 });
    // popup renderiza dentro do escopo de tema do MFE (feelPopupContainer),
    // não no body do portal
    const inScope = await popup.evaluate((el) =>
      Boolean(el.closest(".dashboard-bpmn-modeler")),
    );
    expect(inScope).toBe(true);
    // título PT-BR sem raw bpmn: e tooltip traduzido
    const titleText = await popup
      .locator(".bio-properties-panel-popup__title")
      .innerText();
    expect(titleText).not.toMatch(/bpmn:/);
    await expect(
      popup.locator(".bio-properties-panel-popup__close"),
    ).toHaveAttribute("title", "Salvar e fechar");
    // textarea do popup usa o título como accessible name
    await expect(popup.locator("textarea")).toHaveAttribute(
      "aria-label",
      /\//,
    );
    // placeholder do campo in-panel enquanto o popup está aberto
    await expect(
      page
        .locator(
          ".bio-properties-panel-textarea__open-popup-placeholder, " +
            ".bio-properties-panel-feel-editor__open-popup-placeholder",
        )
        .first(),
    ).toHaveText("Aberto no editor");
    await popup.locator("textarea").fill("Documentação de aceite");
    await shot(page, "acc-popup-editor-expanded");
    await page.keyboard.press("Escape");
    await expect(popup).toHaveCount(0, { timeout: 5000 });
    await waitSaved(page);

    // --- undo / redo (command stack intacto) ---
    await page.getByRole("button", { name: "Desfazer" }).click();
    await waitSaved(page);
    await page.getByRole("button", { name: "Refazer" }).click();
    await waitSaved(page);

    // --- sidebar collapse/expand ---
    await page
      .locator('button[aria-label="Recolher painel lateral"]')
      .click();
    await expect(page.locator(".bpmnm-side__rail")).toBeVisible();
    await shot(page, "acc-sidebar-collapsed");
    await page
      .locator('.bpmnm-side__rail button[aria-label="Propriedades"]')
      .click();
    await page.waitForTimeout(400);
    await expect(
      page.locator('button[aria-label="Recolher painel lateral"]'),
    ).toBeVisible();
  });

  test("organizar: preview, cancel, accept, containment e read-back", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("manager", "ACC-Acceptance", XML);
    await openModel(page, modelId);
    const xmlBefore = await apiXml(modelId);

    // --- Preview: enclosure já vale na proposta ---
    await shot(page, "acc-group-before-organizar");
    await page.getByRole("button", { name: "Organizar" }).click();
    const preview = page.locator('[data-testid="layout-preview"]');
    await expect(preview).toBeVisible({ timeout: 20_000 });
    await page.waitForTimeout(500);
    await shot(page, "acc-group-preview-enclosure");
    const grpPreview = await domBounds(page, "GRP1");
    for (const id of ["T1", "GW1"]) {
      expect(
        encloses(grpPreview, await domBounds(page, id)),
        `preview: GRP1 deve envolver ${id}`,
      ).toBe(true);
    }

    // --- Cancel: canonical e DI permanecem idênticos ---
    await preview.getByRole("button", { name: "Cancelar" }).click();
    await page.waitForTimeout(500);
    expect(await apiXml(modelId)).toBe(xmlBefore);

    // --- Accept: autosave + read-back ---
    await page.getByRole("button", { name: "Organizar" }).click();
    await expect(preview).toBeVisible({ timeout: 20_000 });
    await preview.getByRole("button", { name: "Aceitar" }).click();
    await waitSaved(page);
    await shot(page, "acc-group-after-accept");

    const xml = await apiXml(modelId);
    // lane containment: T1 continua flowNodeRef de L1
    const lane1 = /<bpmn:lane id="L1"[\s\S]*?<\/bpmn:lane>/.exec(xml)?.[0] ?? "";
    expect(lane1).toContain("flowNodeRef>T1<");
    // subprocess containment: filhos continuam dentro do subProcess
    const sub = /<bpmn:subProcess id="SP1"[\s\S]*?<\/bpmn:subProcess>/.exec(
      xml,
    )?.[0] ?? "";
    expect(sub).toContain('id="S2"');
    expect(sub).toContain('id="T2"');
    // BPMNLabel externa preservada no DI
    expect(xml).toContain("bpmndi:BPMNLabel");
    // group DI existe
    expect(xml).toContain('bpmnElement="GRP1"');

    // --- reload: estado persistido idêntico ---
    await page.reload();
    await waitSaved(page);
    const grp = await domBounds(page, "GRP1");
    for (const id of ["T1", "GW1"]) {
      expect(
        encloses(grp, await domBounds(page, id)),
        `pós-reload: GRP1 deve envolver ${id}`,
      ).toBe(true);
    }
  });

  test("revisions: create, view, restore e histórico append-only", async ({
    page,
  }) => {
    const modelId = await importModelViaApi("manager", "ACC-Acceptance", XML);
    await openModel(page, modelId);

    // --- edit inicial: rev1 captura estado "Tarefa A Editada" ---
    await page.locator('.djs-element[data-element-id="T1"]').click({
      position: { x: 20, y: 20 },
      force: true,
    });
    const nameInput = page.getByLabel("Nome", { exact: true });
    await expect(nameInput).toBeVisible({ timeout: 10_000 });
    await nameInput.fill("Tarefa A Editada");
    await page.locator(".bpmnm-canvas").click({
      position: { x: 700, y: 40 },
      force: true,
    });
    await waitSaved(page);

    // --- create rev 1 com metadata ---
    await page.getByRole("tab", { name: "Histórico" }).click();
    await page.getByRole("button", { name: "Criar revisão" }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await dialog.getByLabel("Nome da revisão").fill("Baseline aceite");
    await dialog.getByLabel("Observação").fill("Estado aprovado.");
    await dialog.getByRole("button", { name: "Criar revisão" }).click();
    const card1 = page.locator(".bpmnm-revision-item", {
      hasText: "Baseline aceite",
    });
    await expect(card1).toBeVisible({ timeout: 15_000 });
    await expect(card1.getByText("Rev. 1")).toBeVisible();
    await expect(
      card1.getByText(/\d{2}\/\d{2}\/\d{4}/),
    ).toBeVisible();

    // --- edit + autosave + rev 2: autosave não cria revisão ---
    await page.locator('.djs-element[data-element-id="T1"]').click({
      position: { x: 20, y: 20 },
      force: true,
    });
    await page.getByRole("tab", { name: "Propriedades" }).click();
    const nameV2 = page.getByLabel("Nome", { exact: true });
    await expect(nameV2).toBeVisible({ timeout: 10_000 });
    await nameV2.fill("Tarefa A v2");
    await page.locator(".bpmnm-canvas").click({
      position: { x: 700, y: 40 },
      force: true,
    });
    await waitSaved(page);
    await page.getByRole("tab", { name: "Histórico" }).click();
    await page.getByRole("button", { name: "Criar revisão" }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Criar revisão" })
      .click();
    await expect(page.getByText("Revisão 2")).toBeVisible({ timeout: 15_000 });
    // autosave não gerou checkpoints extras: exatamente 2 cards
    await expect(page.locator(".bpmnm-revision-item")).toHaveCount(2);

    // --- view rev 1: viewer read-only dedicado ---
    await card1.getByRole("button", { name: "Ver revisão 1" }).click();
    await expect(
      page.locator('.bpmnm-canvas[aria-label="Diagrama da revisão"]'),
    ).toBeVisible({ timeout: 20_000 });
    await page.getByRole("button", { name: "Voltar ao modelo" }).click();
    await waitSaved(page);

    // --- restore rev 1 → rev 3 (append-only) ---
    await page.getByRole("tab", { name: "Histórico" }).click();
    await page
      .locator(".bpmnm-revision-item", { hasText: "Baseline aceite" })
      .getByRole("button", { name: "Restaurar" })
      .click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Restaurar" })
      .click();
    // restore é append-only: cria "Revisão 3" com marcador de origem
    const card3 = page.locator(".bpmnm-revision-item", {
      hasText: "Revisão 3",
    });
    await expect(card3).toBeVisible({ timeout: 15_000 });
    await expect(card3.getByText("Restauração")).toBeVisible();
    await shot(page, "acc-revision-history-append-only");
    await waitSaved(page);

    // read-back autoritativo: working copy voltou ao conteúdo de rev1
    const xml = await apiXml(modelId);
    expect(xml).toContain("Tarefa A Editada");
    expect(xml).not.toContain("Tarefa A v2");

    // reload: restore persistido
    await page.reload();
    await waitSaved(page);
    await page.getByRole("tab", { name: "Histórico" }).click();
    await expect(
      page.locator(".bpmnm-revision-item", { hasText: "Revisão 3" }),
    ).toBeVisible();
    await expect(page.getByText("Baseline aceite")).toBeVisible();
  });
});
