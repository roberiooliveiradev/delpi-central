/**
 * G3 — PROD-KEY-*: matriz de atalhos executada (não documentada por
 * leitura de código) + usabilidade de context pad/replace (§24).
 * Cada atalho tem um efeito observável assertado.
 */
import { test, expect, createModelViaApi, waitSaved, PENDING_SAVE_RE } from "../helpers";
import {
  openEditor,
  createFromPalette,
  clickEl,
  deselect,
  selectedElementId,
  shapeIds,
  expectXmlHas,
  saveReadbackReload,
} from "../ce-helpers";

test.describe("PROD-KEY — keyboard shortcuts & context pad", () => {
  test.use({ actor: "editor" });

  test("PROD-KEY-01: Ctrl+S salva edição pendente (dirty → Salvo)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-KEY-01");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 220, 220);
    // após o create o autosave pode já ter drenado; força dirty via undo
    // e confirma que Ctrl+S enfileira write
    await page.keyboard.press("Control+z");
    await page.keyboard.press("Control+s");
    await waitSaved(page);
    // estado final autoritativo: task desfeita não volta
    const xml = await saveReadbackReload(page, "editor", modelId, []);
    expect(xml).not.toContain("<bpmn:task");
  });

  test("PROD-KEY-02: 'E' abre direct editing no elemento selecionado", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-KEY-02");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 220, 220);
    const t = await selectedElementId(page);
    await clickEl(page, t);

    await page.keyboard.press("e");
    await expect(
      page.locator(".djs-direct-editing-content"),
    ).toBeVisible();
    // digita renomeando
    await page.keyboard.type("Nome Via E");
    await page.keyboard.press("Enter");

    const xml = await saveReadbackReload(page, "editor", modelId, [t]);
    expectXmlHas(xml, /Nome Via E/, "rename via E");
  });

  test("PROD-KEY-03: 'R' abre replace menu; Escape fecha sem mutação", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-KEY-03");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 220, 220);
    const t = await selectedElementId(page);
    await clickEl(page, t);

    await page.keyboard.press("r");
    const popup = page.locator(".djs-popup");
    await expect(popup).toBeVisible({ timeout: 5_000 });

    // Escape fecha o popup sem trocar o tipo
    await page.keyboard.press("Escape");
    await expect(popup).not.toBeVisible();

    const xml = await saveReadbackReload(page, "editor", modelId, [t]);
    expectXmlHas(xml, new RegExp(`<bpmn:task id="${t}"`), "task intacta");
  });

  test("PROD-KEY-04: replace via context pad executa morph (task → userTask)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-KEY-04");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 220, 220);
    const t = await selectedElementId(page);
    await clickEl(page, t);

    // context pad aberto (clickEl já prova) → replace → user-task
    await page
      .locator('.djs-context-pad.open .entry[data-action="replace"]')
      .click();
    const popup = page.locator(".djs-popup");
    await expect(popup).toBeVisible({ timeout: 5_000 });
    await page
      .locator('.djs-popup [data-id="replace-with-user-task"]')
      .first()
      .click();
    await expect(popup).not.toBeVisible();

    const xml = await saveReadbackReload(page, "editor", modelId, [t]);
    expectXmlHas(
      xml,
      new RegExp(`<bpmn:userTask id="${t}"`),
      "morph para userTask (mesmo id)",
    );
  });

  test("PROD-KEY-05: Backspace remove seleção (par de Delete)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-KEY-05");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 220, 220);
    const t = await selectedElementId(page);
    await clickEl(page, t);

    await page.keyboard.press("Backspace");
    await expect(
      page.locator(`.djs-element[data-element-id="${t}"]`),
    ).toHaveCount(0);

    const xml = await saveReadbackReload(page, "editor", modelId, []);
    expect(xml).not.toContain(`id="${t}"`);
  });

  test("PROD-KEY-06: context pad abre com clique e oferece actions governadas", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROD-KEY-06");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 220, 220);
    const t = await selectedElementId(page);
    await clickEl(page, t);

    const pad = page.locator(".djs-context-pad.open");
    await expect(pad).toBeVisible();
    // actions esperadas para task (já governadas — G2A provou allowlist)
    for (const action of ["append.append-task", "connect", "replace"]) {
      await expect(
        pad.locator(`.entry[data-action="${action}"]`),
        `pad sem ${action}`,
      ).toBeVisible();
    }
    // foco não fica preso: Escape/clique em vazio deseleciona e pad fecha
    await page.keyboard.press("Escape");
    await deselect(page, { x: 60, y: 520 });
  });
});
