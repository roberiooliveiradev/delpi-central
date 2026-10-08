/**
 * G3 — PROD-CLIP-*: copy/cut/paste via interação real de usuário
 * (seleção → Ctrl+C/X/V → posicionamento), command stack (undo/redo),
 * autosave → read-back autoritativo → reload.
 *
 * Governança: PROD-CLIP-06/07 provam que preserve-only importado não vira
 * CREATE via clipboard (evento copyPaste.canCopyElements filtrado pelo
 * editingProfile — fail-closed, inclusive descendants/attachers).
 */
import {
  test,
  expect,
  createModelViaApi,
  importModelViaApi,
  waitSaved,
} from "../helpers";
import {
  openEditor,
  createFromPalette,
  clickEl,
  connectElements,
  selectedElementId,
  shapeIds,
  newConnectionId,
  saveReadbackReload,
  expectXmlHas,
  fetchWorkingCopyXml,
  canvasBox,
  selectViaDom,
} from "../ce-helpers";
import { readFixture } from "../rt-helpers";

const PRES_ACT = readFixture("pres-activities.bpmn");

/** posição absoluta → coordenada dentro do canvas (page.mouse usa viewport). */
async function canvasPoint(page: any, x: number, y: number) {
  const box = await canvasBox(page);
  return { x: box.x + x, y: box.y + y };
}

/** Move o mouse para o ponto do canvas, Ctrl+V e clica para posicionar. */
async function pasteAt(page: any, x: number, y: number) {
  const p = await canvasPoint(page, x, y);
  await page.mouse.move(p.x, p.y);
  await page.keyboard.press("Control+v");
  await page.locator(".bpmnm-canvas .djs-container").click({
    position: { x, y },
  });
}

test.describe("PROD-CLIP — clipboard productivity", () => {
  test.use({ actor: "editor" });

  test("PROD-CLIP-01: single copy/paste → novo id, original preservado, save/RB/reload", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-CLIP-01");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const t1 = await selectedElementId(page);

    await clickEl(page, t1);
    await page.keyboard.press("Control+c");
    await pasteAt(page, 480, 320);

    const ids = await shapeIds(page);
    const copied = ids.find((id) => id !== t1);
    expect(copied, "nenhum novo shape após paste").toBeTruthy();
    expect(ids).toContain(t1); // original permanece

    const xml = await saveReadbackReload(page, "editor", modelId, [
      t1,
      copied!,
    ]);
    expectXmlHas(xml, new RegExp(`id="${t1}"`), "task original");
    expectXmlHas(xml, new RegExp(`id="${copied}"`), "task copiada");
    const tasks = (xml.match(/<bpmn:task[\s>]/g) ?? []).length;
    expect(tasks).toBe(2);
  });

  test("PROD-CLIP-02: multi copy/paste com sequence flow interna → refs válidas", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-CLIP-02");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 180, 180);
    const a = await selectedElementId(page);
    await createFromPalette(page, "create.task", 400, 180);
    const b = await selectedElementId(page);
    const f1 = await newConnectionId(page, () =>
      connectElements(page, a, b),
    );

    // clique em área vazia primeiro: o properties panel pode focar o campo
    // "Nome" após seleção — Ctrl+A/C/V dentro de input não chegam ao vendor
    await page.locator(".bpmnm-canvas .djs-container").click({
      position: { x: 60, y: 480 },
    });
    // seleciona tudo (2 tasks + flow) → copia → cola em área livre
    await page.keyboard.press("Control+a");
    await expect(page.locator(".djs-element.selected")).toHaveCount(3);
    await page.keyboard.press("Control+c");
    const before = new Set(await shapeIds(page));
    await pasteAt(page, 300, 420);

    const newShapes = (await shapeIds(page)).filter((id) => !before.has(id));
    expect(newShapes, "multi paste não criou 2 shapes").toHaveLength(2);
    expect(before.has(a)).toBe(true);
    expect(before.has(b)).toBe(true);

    const xml = await saveReadbackReload(page, "editor", modelId, [
      a,
      b,
      ...newShapes,
    ]);
    const tasks = (xml.match(/<bpmn:task[\s>]/g) ?? []).length;
    expect(tasks).toBe(4);
    const flows = (xml.match(/<bpmn:sequenceFlow[\s>]/g) ?? []).length;
    expect(flows).toBe(2);
    // flow copiada referencia os NOVOS ids (sem referência quebrada/ao original)
    const copiedFlow = [...xml.matchAll(
      /<bpmn:sequenceFlow id="([^"]+)"[^>]*sourceRef="([^"]+)"[^>]*targetRef="([^"]+)"/g,
    )].find((m) => m[1] !== f1);
    expect(copiedFlow, "flow copiada ausente").toBeTruthy();
    expect(newShapes).toContain(copiedFlow![2]);
    expect(newShapes).toContain(copiedFlow![3]);
  });

  test("PROD-CLIP-03: cut → original removido → paste cria clone novo", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-CLIP-03");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 220, 220);
    const t1 = await selectedElementId(page);

    await clickEl(page, t1);
    await page.keyboard.press("Control+x");
    // cut remove do DOM imediatamente (vendor só corta o que copiou)
    await expect(
      page.locator(`.djs-element[data-element-id="${t1}"]`),
    ).toHaveCount(0);

    await pasteAt(page, 500, 300);
    const ids = await shapeIds(page);
    expect(ids).toHaveLength(1);
    const t2 = ids[0];
    // o vendor reutiliza o id do original removido (cut = move via
    // clipboard; unicidade preservada — nunca coexistem dois t1)

    const xml = await saveReadbackReload(page, "editor", modelId, [t2]);
    expectXmlHas(xml, new RegExp(`id="${t2}"`), "clone do cut");
    const tasks = (xml.match(/<bpmn:task[\s>]/g) ?? []).length;
    expect(tasks).toBe(1);
  });

  test("PROD-CLIP-04: undo/redo cobrem paste e cut", async ({ page }) => {
    const modelId = await createModelViaApi("editor", "PROD-CLIP-04");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 220, 220);
    const t1 = await selectedElementId(page);

    // paste → undo remove clone → redo recria
    await clickEl(page, t1);
    await page.keyboard.press("Control+c");
    const before = new Set(await shapeIds(page));
    await pasteAt(page, 500, 320);
    const clone = (await shapeIds(page)).find((id) => !before.has(id));
    expect(clone).toBeTruthy();

    await page.keyboard.press("Control+z");
    await expect(
      page.locator(`.djs-element[data-element-id="${clone}"]`),
    ).toHaveCount(0);
    await page.keyboard.press("Control+y");
    await expect(
      page.locator(`.djs-element[data-element-id="${clone}"]`),
    ).toBeAttached();

    // cut → undo restaura → redo remove de novo
    await clickEl(page, t1);
    await page.keyboard.press("Control+x");
    await expect(
      page.locator(`.djs-element[data-element-id="${t1}"]`),
    ).toHaveCount(0);
    await page.keyboard.press("Control+z");
    await expect(
      page.locator(`.djs-element[data-element-id="${t1}"]`),
    ).toBeAttached();
    await page.keyboard.press("Control+y");
    await expect(
      page.locator(`.djs-element[data-element-id="${t1}"]`),
    ).toHaveCount(0);
  });

  test("PROD-CLIP-05: duplicate (Ctrl+D) passa pelo mesmo gate de cópia", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-CLIP-05");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 220, 220);
    const t1 = await selectedElementId(page);

    await clickEl(page, t1);
    const before = new Set(await shapeIds(page));
    const p = await canvasPoint(page, 480, 340);
    await page.mouse.move(p.x, p.y);
    await page.keyboard.press("Control+d");
    await page.locator(".bpmnm-canvas .djs-container").click({
      position: { x: 480, y: 340 },
    });

    const dup = (await shapeIds(page)).find((id) => !before.has(id));
    expect(dup, "duplicate não criou clone").toBeTruthy();

    const xml = await saveReadbackReload(page, "editor", modelId, [t1, dup!]);
    const tasks = (xml.match(/<bpmn:task[\s>]/g) ?? []).length;
    expect(tasks).toBe(2);
  });
});

test.describe("PROD-CLIP — paste governance (PRESERVE_ONLY != CREATE)", () => {
  test.use({ actor: "editor" });

  test("PROD-CLIP-06: copy/paste de ComplexGateway preserve-only não cria clone", async ({
    page,
  }) => {
    const modelId = await importModelViaApi(
      "editor",
      "PROD-CLIP-06",
      PRES_ACT,
    );
    await openEditor(page, modelId);

    const nonLabelShapes = async () =>
      (await shapeIds(page)).filter((id) => !id.endsWith("_label"));

    await selectViaDom(page, "CG1");
    const baseline = await nonLabelShapes();
    await page.keyboard.press("Control+c");
    await page.keyboard.press("Control+v");
    await page.locator(".bpmnm-canvas .djs-container").click({
      position: { x: 600, y: 560 },
      force: true,
    });
    await page.waitForTimeout(400);

    // nada novo no canvas — complexGateway negado no canCopyElements
    await expect(
      page.locator('.djs-element[data-element-id="CG1"]'),
    ).toBeAttached();
    expect(await nonLabelShapes()).toEqual(baseline);

    // cut de preserve-only não remove (vendor só corta o que copiou)
    await selectViaDom(page, "CG1");
    await page.keyboard.press("Control+x");
    await expect(
      page.locator('.djs-element[data-element-id="CG1"]'),
    ).toBeAttached();

    // duplicate também bloqueado
    await selectViaDom(page, "CG1");
    const beforeDup = await nonLabelShapes();
    await page.keyboard.press("Control+d");
    await page.waitForTimeout(300);
    await page.locator(".bpmnm-canvas .djs-container").click({
      position: { x: 600, y: 560 },
      force: true,
    });
    expect(await nonLabelShapes()).toEqual(beforeDup);

    // read-back autoritativo: exatamente 1 complexGateway
    await waitSaved(page);
    const xml = await fetchWorkingCopyXml("editor", modelId);
    const cgs = (xml.match(/<bpmn:complexGateway[\s>]/g) ?? []).length;
    expect(cgs).toBe(1);
  });

  test("PROD-CLIP-07: seleção mista — paste cria só o elemento CREATE_EDIT", async ({
    page,
  }) => {
    const modelId = await importModelViaApi(
      "editor",
      "PROD-CLIP-07",
      PRES_ACT,
    );
    await openEditor(page, modelId);

    // seleção mista: T_NORM (task CREATE_EDIT) + CG1 (preserve-only)
    await selectViaDom(page, "T_NORM");
    await selectViaDom(page, "CG1", true);
    await expect(page.locator(".djs-element.selected")).toHaveCount(2);

    const before = new Set(
      (await shapeIds(page)).filter((id) => !id.endsWith("_label")),
    );
    await page.keyboard.press("Control+c");
    await pasteAt(page, 300, 560);

    let created: string[] = [];
    await expect
      .poll(
        async () => {
          created = (await shapeIds(page)).filter(
            (id) => !before.has(id) && !id.endsWith("_label"),
          );
          return created.length;
        },
        { timeout: 5_000 },
      )
      .toBe(1);
    // o clone é task, não gateway
    const xml = await saveReadbackReload(page, "editor", modelId, created);
    const cgs = (xml.match(/<bpmn:complexGateway[\s>]/g) ?? []).length;
    expect(cgs).toBe(1);
  });
});
