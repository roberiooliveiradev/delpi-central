/**
 * G3 — PROD-RSZ-*: resize funcional (não apenas handle visível) —
 * drag real no resizer, DI bounds mudam, semântica intacta,
 * undo/redo, save → read-back → reload.
 *
 * Classificação vendor (BpmnRules.canResize — fonte de verdade):
 *   SUPPORTED: SubProcess expandido, Participant, Lane, Group,
 *              TextAnnotation (e/w), Label (e/w)
 *   BLOCKED_AS_EXPECTED: Task, Event, Gateway, DataObject/Store
 *   (BPMN prescreve tamanho fixo — ausência de resizer é o comportamento
 *   normativo, não defeito).
 *
 * Geometria de teste (evidência medida no DOM real):
 *  - palette vendor ocupa a faixa esquerda do container (~x:22-116);
 *  - o auto-select pós-create deixa o elemento selecionado MAS sem
 *    resizers (o vendor emite selection.changed posterior que os limpa).
 *    Resizers = evidência de TRANSIÇÃO de seleção → deselect → reselect;
 *  - re-select em elemento já selecionado não re-emite o evento.
 */
import { test, expect, createModelViaApi } from "../helpers";
import {
  openEditor,
  createFromPalette,
  clickEl,
  deselect,
  selectViaDom,
  selectedElementId,
  saveReadbackReload,
  elBox,
} from "../ce-helpers";

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

/** Transição real de seleção → resizers renderizam (ou não, se fixed-size). */
async function selectFresh(
  page: any,
  elementId: string,
  position?: { x: number; y: number },
  deselectPos?: { x: number; y: number },
) {
  await deselect(page, deselectPos);
  await clickEl(page, elementId, position);
}

/** Arrasta o resizer `dir` do elemento selecionado por (dx,dy). */
async function dragResize(
  page: any,
  direction: "n" | "s" | "e" | "w" | "se" | "nw" | "ne" | "sw",
  dx: number,
  dy: number,
) {
  const handle = page.locator(`.djs-resizer-${direction}`).first();
  await expect(handle).toBeVisible({ timeout: 5_000 });
  const hb = await handle.boundingBox();
  if (!hb) throw new Error(`resizer ${direction} sem bbox`);
  await page.mouse.move(hb.x + hb.width / 2, hb.y + hb.height / 2);
  await page.mouse.down();
  await page.mouse.move(hb.x + hb.width / 2 + dx, hb.y + hb.height / 2 + dy, {
    steps: 8,
  });
  await page.mouse.up();
}

test.describe("PROD-RSZ — functional resize", () => {
  // viewport largo: participant (600px) precisa ficar à direita da palette
  test.use({ actor: "editor", viewport: { width: 1600, height: 900 } });

  test("PROD-RSZ-01: SubProcess expanded — resize muda DI, undo/redo, RB/reload", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-RSZ-01");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.subprocess-expanded", 450, 250);
    const sp = await selectedElementId(page);
    const box0 = await elBox(page, sp);

    await selectFresh(page, sp, { x: 300, y: 150 });
    await expect(page.locator(".djs-resizer")).toHaveCount(8);
    await dragResize(page, "se", 90, 70);

    const box1 = await elBox(page, sp);
    expect(box1.width).toBeGreaterThan(box0.width + 30);
    expect(box1.height).toBeGreaterThan(box0.height + 20);

    // undo → tamanho original; redo → novo tamanho
    await page.keyboard.press("Control+z");
    const boxU = await elBox(page, sp);
    expect(Math.abs(boxU.width - box0.width)).toBeLessThanOrEqual(10);
    await page.keyboard.press("Control+y");
    const boxR = await elBox(page, sp);
    expect(Math.abs(boxR.width - box1.width)).toBeLessThanOrEqual(10);

    const xml = await saveReadbackReload(page, "editor", modelId, [sp]);
    const di = diBounds(xml, sp);
    expect(di, "DI bounds ausentes").toBeTruthy();
    // semântica intacta: continua bpmn:subProcess com o mesmo id
    expect(xml).toMatch(new RegExp(`<bpmn:subProcess id="${sp}"`));
  });

  test("PROD-RSZ-02: Pool (Participant) — resize + RB", async ({ page }) => {
    const modelId = await createModelViaApi("editor", "PROD-RSZ-02");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.participant-expanded", 480, 240);
    const pool = await selectedElementId(page);
    const box0 = await elBox(page, pool);

    // header do participant (faixa esquerda do shape) seleciona o pool
    await selectFresh(page, pool, { x: 15, y: 150 });
    await expect(page.locator(".djs-resizer")).toHaveCount(8);
    await dragResize(page, "s", 0, 60);

    const box1 = await elBox(page, pool);
    expect(box1.height).toBeGreaterThan(box0.height + 30);
    const xml = await saveReadbackReload(page, "editor", modelId, [pool]);
    const di = diBounds(xml, pool);
    expect(di, "DI do participant ausente").toBeTruthy();
    expect(di!.height).toBeGreaterThan(box0.height + 30);
  });

  test("PROD-RSZ-03: Lane dentro do pool — resize funcional", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-RSZ-03");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.participant-expanded", 480, 240);
    const pool = await selectedElementId(page);

    // participant nasce sem lanes; dividir via context pad (governed).
    // Entries do pad são draggable — clique real não entrega o evento
    // 'click' ao delegate do vendor; usa o mesmo path de selectViaDom.
    await deselect(page);
    await selectViaDom(page, pool);
    await expect(page.locator(".djs-context-pad.open")).toBeVisible();
    await page.evaluate(() => {
      document
        .querySelector(
          '.djs-context-pad.open .entry[data-action="lane-divide-two"]',
        )
        ?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    // bpmn-js renderiza lanes no plane do root (irmãs do participant no
    // DOM, posicionadas dentro dos bounds do pool); ids gerados: Lane_*
    const lanes = page.locator('.djs-element[data-element-id^="Lane_"]');
    await expect(lanes).toHaveCount(2);
    const lane = await lanes.first().getAttribute("data-element-id");
    expect(lane, "lane não encontrada no pool").toBeTruthy();

    // clique no corpo da lane (não no header do pool) → seleciona a lane
    await selectFresh(page, lane!, { x: 300, y: 120 });
    const resizers = await page.locator(".djs-resizer").count();
    // canResize(bpmn:Lane)=true → lane expõe handles
    expect(resizers).toBeGreaterThan(0);

    const box0 = await elBox(page, lane!);
    await dragResize(page, "s", 0, 60);
    const box1 = await elBox(page, lane!);
    expect(
      box1.height !== box0.height || box1.width !== box0.width,
      "lane resize não produziu mudança de DI",
    ).toBe(true);

    await saveReadbackReload(page, "editor", modelId, [pool]);
  });

  test("PROD-RSZ-04: Group (artifact) — resize + RB", async ({ page }) => {
    const modelId = await createModelViaApi("editor", "PROD-RSZ-04");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.group", 450, 280);
    const g = await selectedElementId(page);
    const box0 = await elBox(page, g);

    // group é artifact com hit-area irregular — seleção via DOM após
    // deselect garante a transição real que recria os resizers
    await deselect(page);
    await selectViaDom(page, g);
    await expect(page.locator(".djs-resizer")).toHaveCount(8);
    await dragResize(page, "se", 70, 60);

    const box1 = await elBox(page, g);
    expect(box1.width).toBeGreaterThan(box0.width + 30);
    const xml = await saveReadbackReload(page, "editor", modelId, [g]);
    const di = diBounds(xml, g);
    expect(di, "DI do group ausente").toBeTruthy();
  });

  test("PROD-RSZ-05: fixed-size — task/event/gateway/data-object sem resizer (BLOCKED_AS_EXPECTED)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-RSZ-05");
    await openEditor(page, modelId);

    // posições fora da faixa da palette e sem sobreposição entre shapes
    await createFromPalette(page, "create.start-event", 350, 150);
    const start = await selectedElementId(page);
    await createFromPalette(page, "create.exclusive-gateway", 450, 150);
    const gw = await selectedElementId(page);
    await createFromPalette(page, "create.data-object", 570, 150);
    const dataObj = await selectedElementId(page);
    await createFromPalette(page, "create.task", 330, 320);
    const task = await selectedElementId(page);
    await createFromPalette(page, "create.subprocess-expanded", 580, 330);
    const sp = await selectedElementId(page); // controle positivo

    for (const id of [start, gw, dataObj, task]) {
      // transição real: deselect → click no elemento → resizers recriados
      await deselect(page, { x: 900, y: 520 });
      await page
        .locator(`.djs-element[data-element-id="${id}"]`)
        .click({ position: { x: 18, y: 18 }, force: true });
      await expect(
        page.locator(`.djs-element.selected[data-element-id="${id}"]`),
      ).toBeAttached({ timeout: 5_000 });
      expect(
        await page.locator(".djs-resizer").count(),
        `${id} (fixed-size) exibiu resizer`,
      ).toBe(0);
    }

    // controle positivo: subprocess recém-selecionado tem os 8 resizers
    await selectFresh(page, sp, { x: 300, y: 150 }, { x: 900, y: 520 });
    await expect(page.locator(".djs-resizer")).toHaveCount(8);
  });
});
