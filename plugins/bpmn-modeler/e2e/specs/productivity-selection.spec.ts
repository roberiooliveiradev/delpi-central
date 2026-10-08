/**
 * G3 — PROD-SEL-*: seleção real (Shift, lasso, select-all, deselect),
 * bulk move (DI + undo/redo + read-back), bulk delete (refs limpas) e
 * evidência de snap/grid (SPACING=10 do GridSnapping vendor).
 */
import { test, expect, createModelViaApi } from "../helpers";
import {
  openEditor,
  createFromPalette,
  clickEl,
  deselect,
  connectElements,
  selectedElementId,
  shapeIds,
  newConnectionId,
  saveReadbackReload,
  elBox,
  canvasBox,
} from "../ce-helpers";

async function selectedCount(page: any): Promise<number> {
  return page.locator(".djs-element.selected").count();
}

/** Bounds DI de um bpmnElement no XML autoritativo. */
function diBounds(xml: string, elementId: string) {
  const m = xml.match(
    new RegExp(
      `bpmnElement="${elementId}"[^>]*>[\\s\\S]*?<dc:Bounds x="([-\\d.]+)" y="([-\\d.]+)" width="([\\d.]+)" height="([\\d.]+)"`,
    ),
  );
  if (!m) return null;
  return {
    x: parseFloat(m[1]),
    y: parseFloat(m[2]),
    width: parseFloat(m[3]),
    height: parseFloat(m[4]),
  };
}

test.describe("PROD-SEL — selection & bulk operations", () => {
  test.use({ actor: "editor" });

  test("PROD-SEL-01: Shift+click adiciona à seleção (multi-select real)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-SEL-01");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const a = await selectedElementId(page);
    await createFromPalette(page, "create.task", 420, 200);
    const b = await selectedElementId(page);

    await clickEl(page, a);
    await page.keyboard.down("Shift");
    await page
      .locator(`.djs-element[data-element-id="${b}"]`)
      .click({ position: { x: 50, y: 40 }, force: true });
    await page.keyboard.up("Shift");

    await expect(
      page.locator(`.djs-element.selected[data-element-id="${a}"]`),
    ).toBeAttached();
    await expect(
      page.locator(`.djs-element.selected[data-element-id="${b}"]`),
    ).toBeAttached();
    expect(await selectedCount(page)).toBe(2);
  });

  test("PROD-SEL-02: lasso (tecla L + drag) seleciona shapes contidos", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-SEL-02");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const a = await selectedElementId(page);
    await createFromPalette(page, "create.task", 420, 200);
    const b = await selectedElementId(page);
    await createFromPalette(page, "create.task", 620, 330);
    const outside = await selectedElementId(page);

    // deselect em ponto vazio (retry tolerante — element.click é
    // time-dependent no vendor) + foco no svg para o keyboard
    await deselect(page, { x: 500, y: 60 });
    await page.keyboard.press("l");

    // retângulo do lasso (coords relativas ao container): cobre a e b
    // integralmente, exclui `outside` (começa em x=570 > 560)
    const c = await canvasBox(page);
    await page.mouse.move(c.x + 130, c.y + 130);
    await page.mouse.down();
    await page.mouse.move(c.x + 560, c.y + 300, { steps: 6 });
    await page.mouse.up();

    await expect(
      page.locator(`.djs-element.selected[data-element-id="${a}"]`),
    ).toBeAttached();
    await expect(
      page.locator(`.djs-element.selected[data-element-id="${b}"]`),
    ).toBeAttached();
    await expect(
      page.locator(`.djs-element.selected[data-element-id="${outside}"]`),
    ).toHaveCount(0);
  });

  test("PROD-SEL-03: select-all (Ctrl+A) seleciona tudo; clique vazio deseleciona", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-SEL-03");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const a = await selectedElementId(page);
    await createFromPalette(page, "create.task", 420, 200);
    const b = await selectedElementId(page);
    const flow = await newConnectionId(page, () =>
      connectElements(page, a, b),
    );

    await deselect(page, { x: 620, y: 320 });
    await page.keyboard.press("Control+a");
    const sel = await selectedCount(page);
    expect(sel).toBeGreaterThanOrEqual(3); // 2 tasks + flow
    for (const id of [a, b, flow]) {
      await expect(
        page.locator(`.djs-element.selected[data-element-id="${id}"]`),
      ).toBeAttached();
    }
  });

  test("PROD-SEL-04: bulk move — geometria relativa, DI, undo/redo, RB/reload", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-SEL-04");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const a = await selectedElementId(page);
    await createFromPalette(page, "create.task", 420, 200);
    const b = await selectedElementId(page);
    await connectElements(page, a, b);

    const boxA0 = await elBox(page, a);
    const boxB0 = await elBox(page, b);

    // deselect garante foco no svg do canvas (properties panel pode ter
    // focado "Nome" após connect) → Ctrl+A chega ao vendor
    await deselect(page, { x: 620, y: 320 });
    // seleciona os dois e arrasta A — vendor move a seleção inteira
    await page.keyboard.press("Control+a");
    await expect(page.locator(".djs-element.selected")).toHaveCount(3);
    const start = await elBox(page, a);
    await page.mouse.move(start.x + 50, start.y + 40);
    await page.mouse.down();
    await page.mouse.move(start.x + 170, start.y + 190, { steps: 8 });
    await page.mouse.up();

    const boxA1 = await elBox(page, a);
    const boxB1 = await elBox(page, b);
    const dxA = boxA1.x - boxA0.x;
    const dyA = boxA1.y - boxA0.y;
    const dxB = boxB1.x - boxB0.x;
    const dyB = boxB1.y - boxB0.y;
    // ambos moveram e a geometria relativa foi preservada (snap → tolerância)
    expect(Math.abs(dxA), "A não moveu em x").toBeGreaterThan(50);
    expect(Math.abs(dyA), "A não moveu em y").toBeGreaterThan(50);
    expect(Math.abs(dxA - dxB)).toBeLessThanOrEqual(10); // grid snap 10
    expect(Math.abs(dyA - dyB)).toBeLessThanOrEqual(10);

    // undo restaura posições, redo reaplica
    await page.keyboard.press("Control+z");
    const boxA2 = await elBox(page, a);
    expect(Math.abs(boxA2.x - boxA0.x)).toBeLessThanOrEqual(10);
    await page.keyboard.press("Control+y");
    const boxA3 = await elBox(page, a);
    expect(Math.abs(boxA3.x - boxA1.x)).toBeLessThanOrEqual(10);

    // persistência: DI read-back mostra bounds novos; reload preserva
    const xml = await saveReadbackReload(page, "editor", modelId, [a, b]);
    const diA = diBounds(xml, a);
    const diB = diBounds(xml, b);
    expect(diA, "DI bounds de A ausentes").toBeTruthy();
    expect(diB, "DI bounds de B ausentes").toBeTruthy();
    // geometria relativa preservada no XML persistido
    expect(Math.abs(diA!.x - diB!.x)).toBeCloseTo(
      Math.abs(boxA1.x - boxB1.x),
      -1,
    );
  });

  test("PROD-SEL-05: bulk delete — remove selecionados + flows, undo/redo, RB", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-SEL-05");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const a = await selectedElementId(page);
    await createFromPalette(page, "create.task", 420, 200);
    const b = await selectedElementId(page);
    const f1 = await newConnectionId(page, () =>
      connectElements(page, a, b),
    );
    await createFromPalette(page, "create.task", 200, 460);
    const keep = await selectedElementId(page);

    // seleciona a+b+flow via shift e deleta
    await clickEl(page, a);
    await page.keyboard.down("Shift");
    await page
      .locator(`.djs-element[data-element-id="${b}"]`)
      .click({ position: { x: 50, y: 40 }, force: true });
    await page.keyboard.up("Shift");
    await page.keyboard.press("Delete");

    for (const id of [a, b, f1]) {
      await expect(
        page.locator(`.djs-element[data-element-id="${id}"]`),
      ).toHaveCount(0);
    }
    await expect(
      page.locator(`.djs-element[data-element-id="${keep}"]`),
    ).toBeAttached();

    // undo restaura tudo, redo remove de novo
    await page.keyboard.press("Control+z");
    for (const id of [a, b, f1]) {
      await expect(
        page.locator(`.djs-element[data-element-id="${id}"]`),
      ).toBeAttached();
    }
    await page.keyboard.press("Control+y");
    for (const id of [a, b, f1]) {
      await expect(
        page.locator(`.djs-element[data-element-id="${id}"]`),
      ).toHaveCount(0);
    }

    // read-back: sem referências quebradas para os ids removidos
    const xml = await saveReadbackReload(page, "editor", modelId, [keep]);
    expect(xml).not.toContain(`id="${f1}"`);
    expect(xml).not.toContain(`"${a}"`);
    expect(xml).not.toContain(`"${b}"`);
    expect(xml).not.toMatch(new RegExp(`(sourceRef|targetRef)="${a}"`));
    expect(xml).not.toMatch(new RegExp(`(sourceRef|targetRef)="${b}"`));
  });

  test("PROD-SEL-06: snap/grid — movimento livre é quantizado no grid 10", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-SEL-06");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 220, 220);
    const a = await selectedElementId(page);

    // arrasta por delta não múltiplo de 10 — DI final deve seguir grid 10
    const start = await elBox(page, a);
    await page.mouse.move(start.x + 50, start.y + 40);
    await page.mouse.down();
    await page.mouse.move(start.x + 57, start.y + 43, { steps: 4 });
    await page.mouse.up();

    const xml = await saveReadbackReload(page, "editor", modelId, [a]);
    const di = diBounds(xml, a);
    expect(di, "DI bounds ausentes").toBeTruthy();
    expect(
      di!.x % 10 === 0 && di!.y % 10 === 0,
      `bounds (${di!.x},${di!.y}) fora do grid 10 — snapping inativo`,
    ).toBe(true);
  });
});
