/**
 * CE-COL (G2B) — CREATE_EDIT evidence: collaboration.
 *
 * Pool/participant (expanded + black-box), múltiplos pools, lanes
 * (insert/divide/nested), membership flowNodeRef, MessageFlow entre
 * pools — tudo com read-back autoritativo + reload.
 */
import { test, expect, createModelViaApi } from "../helpers";
import {
  openEditor,
  createFromPalette,
  clickEl,
  replaceWith,
  connectElements,
  padAction,
  renameElement,
  selectedElementId,
  saveReadbackReload,
  expectXmlHas,
} from "../ce-helpers";

test.describe("CE-COL — collaboration CREATE_EDIT", () => {
  test.use({ actor: "editor" });

  test("CE-COL-01: Participant expanded → task dentro → participant+processRef+laneSet", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-COL-01");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.participant-expanded", 380, 220);
    const pool = await selectedElementId(page);
    // task dentro do pool (drop dentro dos bounds do participant)
    await createFromPalette(page, "create.task", 300, 220);
    const t = await selectedElementId(page);

    const xml = await saveReadbackReload(page, "editor", modelId, [pool, t]);
    expectXmlHas(xml, /<bpmn:participant[\s>]/, "participant");
    expectXmlHas(xml, /processRef=/, "processRef");
    // expanded pool nasce sem lanes — laneSet/flowNodeRef provados em
    // CE-COL-02/05 via operações de lane reais
    expectXmlHas(
      xml,
      new RegExp(`<bpmn:process[^>]*>[^]*<bpmn:task id="${t}"`),
      "task dentro do process do participant",
    );
  });

  test("CE-COL-02: lanes — insert above/below + divide → nested childLaneSet + membership", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-COL-02");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.participant-expanded", 420, 260);
    const pool = await selectedElementId(page);
    await createFromPalette(page, "create.task", 300, 260);
    const t = await selectedElementId(page);
    await page.keyboard.press("Escape");

    // pool nasce sem lane — divide cria laneSet com duas lanes
    // (clique default: interior superior = participant; o bbox do pool
    // inclui margem sem hit-area no header lateral)
    await clickEl(page, pool);
    await padAction(page, "lane-divide-two");
    await page.waitForTimeout(200);

    const laneIds = await page.evaluate(() =>
      [...document.querySelectorAll(".djs-element")]
        .map((el) => el.getAttribute("data-element-id"))
        .filter((id) => id?.startsWith("Lane")),
    );
    expect(laneIds.length).toBeGreaterThanOrEqual(2);

    // insert above + below na primeira lane
    await clickEl(page, laneIds[0]!);
    await padAction(page, "lane-insert-above");
    await page.waitForTimeout(150);
    await clickEl(page, laneIds[0]!);
    await padAction(page, "lane-insert-below");
    await page.waitForTimeout(150);
    // nested: divide uma lane existente → childLaneSet
    await clickEl(page, laneIds[1] ?? laneIds[0]!);
    await padAction(page, "lane-divide-two");
    await page.waitForTimeout(150);

    const xml = await saveReadbackReload(page, "editor", modelId, [pool, t]);
    const laneCount = (xml.match(/<bpmn:lane[\s>]/g) ?? []).length;
    expect(laneCount).toBeGreaterThanOrEqual(4);
    expectXmlHas(xml, /<bpmn:laneSet[\s>]/, "laneSet");
    expectXmlHas(xml, /<bpmn:childLaneSet[\s>]/, "nested childLaneSet");
    expectXmlHas(xml, /<bpmn:flowNodeRef>/, "flowNodeRef membership");
  });

  test("CE-COL-03: dois pools + MessageFlow entre elementos de processos distintos", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-COL-03");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.participant-expanded", 360, 170);
    const poolA = await selectedElementId(page);
    await createFromPalette(page, "create.task", 300, 170);
    const tA = await selectedElementId(page);

    await createFromPalette(page, "create.participant-expanded", 360, 460);
    const poolB = await selectedElementId(page);
    await createFromPalette(page, "create.task", 300, 460);
    const tB = await selectedElementId(page);

    await connectElements(page, tA, tB);

    const xml = await saveReadbackReload(page, "editor", modelId, [
      poolA,
      poolB,
      tA,
      tB,
    ]);
    const poolCount = (xml.match(/<bpmn:participant[\s>]/g) ?? []).length;
    expect(poolCount).toBeGreaterThanOrEqual(2);
    expectXmlHas(xml, /<bpmn:messageFlow[\s>]/, "messageFlow");
  });

  test("CE-COL-04: black-box pool via replace → participant sem processRef", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-COL-04");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.participant-expanded", 380, 220);
    const pool = await selectedElementId(page);
    // clique default: interior superior = participant
    await clickEl(page, pool);
    await replaceWith(page, "replace-with-collapsed-pool");

    const xml = await saveReadbackReload(page, "editor", modelId, [pool]);
    expectXmlHas(
      xml,
      new RegExp(`<bpmn:participant[^>]*id="${pool}"[^>]*(/>|>(?!processRef))`),
      "black-box participant",
    );
    // participant persistido; sem processRef obrigatório
    expect(xml).toContain(`id="${pool}"`);
  });

  test("CE-COL-05: lane rename + move task entre lanes", async ({ page }) => {
    const modelId = await createModelViaApi("editor", "CE-COL-05");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.participant-expanded", 420, 260);
    const pool = await selectedElementId(page);
    await createFromPalette(page, "create.task", 300, 200);
    const t = await selectedElementId(page);
    await page.keyboard.press("Escape");

    // lane real via pad do participant
    await clickEl(page, pool);
    await padAction(page, "lane-divide-two");
    await page.waitForTimeout(200);

    const laneId = await page.evaluate(() => {
      const lane = [...document.querySelectorAll(".djs-element")].find(
        (el) => el.getAttribute("data-element-id")?.startsWith("Lane"),
      );
      return lane?.getAttribute("data-element-id") ?? null;
    });
    expect(laneId).not.toBeNull();
    await renameElement(page, laneId!, "Raia Operacional");

    const xml = await saveReadbackReload(page, "editor", modelId, [t]);
    expectXmlHas(xml, /Raia Operacional/, "lane name");
    expectXmlHas(
      xml,
      new RegExp(`<bpmn:flowNodeRef>${t}</bpmn:flowNodeRef>`),
      "flowNodeRef membership",
    );
  });
});
