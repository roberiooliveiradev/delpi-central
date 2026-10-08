/**
 * PROP-CORE / PROP-DOC (WAVE E) — BPMN core properties breadth:
 * calledElement (CallActivity) e documentation (task + process).
 *
 * Toda evidência: UI → command stack → autosave → XML autoritativo
 * (GET working-copy) → reload → campo persistido. Nunca UI-only.
 */
import {
  test,
  expect,
  createModelViaApi,
  waitSaved,
} from "../helpers";
import {
  openEditor,
  createFromPalette,
  clickEl,
  deselect,
  replaceWith,
  newShapeId,
  focusCanvasSvg,
  saveReadbackReload,
  fetchWorkingCopyXml,
  expectXmlHas,
} from "../ce-helpers";
import {
  expandAllGroups,
  entry,
  entryInput,
  fillEntry,
} from "../prop-helpers";

test.describe("PROP-CORE — calledElement (CallActivity)", () => {
  test.use({ actor: "editor" });

  test("PROP-CORE-01: calledElement edit → save → read-back → undo/redo → reload (RT: RT-CE-01 fixture)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROP-CORE-01");
    await openEditor(page, modelId);

    const task = await newShapeId(page, () =>
      createFromPalette(page, "create.task", 300, 200),
    );
    await clickEl(page, task);
    await replaceWith(page, "replace-with-call-activity");
    await clickEl(page, task);
    await expandAllGroups(page);

    // entry do produto (grupo callActivity) — BPMN core, sem engine fields
    await expect(entry(page, "calledElement")).toBeAttached({
      timeout: 10_000,
    });
    // semântica engine NÃO exposta (binding/version/tenant ficam fora)
    await expect(entry(page, "calledElementBinding")).toHaveCount(0);
    await expect(entry(page, "calledElementVersionTag")).toHaveCount(0);

    await fillEntry(page, "calledElement", "Process_B");
    await waitSaved(page);

    let xml = await fetchWorkingCopyXml("editor", modelId);
    expectXmlHas(xml, /<bpmn:callActivity[\s>][^>]*calledElement="Process_B"/, "calledElement");

    // undo/redo via command stack
    await focusCanvasSvg(page);
    await page.keyboard.press("ControlOrMeta+z");
    await waitSaved(page);
    xml = await fetchWorkingCopyXml("editor", modelId);
    expect(xml).not.toMatch(/calledElement="Process_B"/);
    await page.keyboard.press("ControlOrMeta+y");
    await waitSaved(page);
    xml = await fetchWorkingCopyXml("editor", modelId);
    expectXmlHas(xml, /calledElement="Process_B"/, "calledElement redo");

    // reload → campo repopulado com valor persistido
    await page.reload();
    await expect(
      page.locator(".bpmnm-canvas .djs-container"),
    ).toBeVisible({ timeout: 20_000 });
    await waitSaved(page);
    await clickEl(page, task);
    await expandAllGroups(page);
    await expect(entryInput(page, "calledElement")).toHaveValue("Process_B");
  });
});

test.describe("PROP-DOC — documentation", () => {
  test.use({ actor: "editor" });

  test("PROP-DOC-01: task documentation → save → read-back → reload", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROP-DOC-01");
    await openEditor(page, modelId);

    const task = await newShapeId(page, () =>
      createFromPalette(page, "create.task", 300, 200),
    );
    await clickEl(page, task);
    await expandAllGroups(page);

    const docEntry = entry(page, "documentation");
    await expect(docEntry).toBeAttached({ timeout: 10_000 });
    const docInput = docEntry.locator("textarea, input").first();
    await docInput.click();
    await docInput.fill("Documentação BPMN core da tarefa");
    await docInput.press("Tab");
    await page.waitForTimeout(400);

    const xml = await saveReadbackReload(page, "editor", modelId, [task]);
    expectXmlHas(
      xml,
      /<bpmn:documentation[^>]*>Documentação BPMN core da tarefa<\/bpmn:documentation>/,
      "task documentation",
    );
  });

  test("PROP-DOC-02: process documentation → save → read-back", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROP-DOC-02");
    await openEditor(page, modelId);

    // canvas vazio seleciona o process root → painel mostra Process
    await deselect(page);
    await expandAllGroups(page);

    const docEntry = entry(page, "processDocumentation").or(
      entry(page, "documentation"),
    );
    await expect(docEntry.first()).toBeAttached({ timeout: 10_000 });
    const docInput = docEntry.first().locator("textarea, input").first();
    await docInput.click();
    await docInput.fill("Documentação do processo");
    await docInput.press("Tab");
    await page.waitForTimeout(400);

    await waitSaved(page);
    const xml = await fetchWorkingCopyXml("editor", modelId);
    expectXmlHas(
      xml,
      /<bpmn:documentation[^>]*>Documentação do processo<\/bpmn:documentation>/,
      "process documentation",
    );
  });
});
