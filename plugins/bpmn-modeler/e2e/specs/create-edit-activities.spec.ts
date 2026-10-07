/**
 * CE-ACT (G2B) — CREATE_EDIT evidence: activities.
 *
 * Cada typed task é criada via Task → Replace (caminho aprovado pelo
 * freeze), configurada (rename), conectada, persistida e provada por
 * read-back autoritativo (GET working-copy XML) + reload. QName correto
 * é verificado no XML — nunca apenas ícone visual.
 */
import { test, expect, createModelViaApi } from "../helpers";
import {
  openEditor,
  createFromPalette,
  clickEl,
  replaceWith,
  renameElement,
  connectElements,
  selectedElementId,
  saveReadbackReload,
  expectXmlHas,
} from "../ce-helpers";

const TYPED_TASKS: { entry: string; qname: RegExp; label: string }[] = [
  { entry: "replace-with-user-task", qname: /<bpmn:userTask[\s>]/, label: "UserTask" },
  { entry: "replace-with-service-task", qname: /<bpmn:serviceTask[\s>]/, label: "ServiceTask" },
  { entry: "replace-with-manual-task", qname: /<bpmn:manualTask[\s>]/, label: "ManualTask" },
  { entry: "replace-with-rule-task", qname: /<bpmn:businessRuleTask[\s>]/, label: "BusinessRuleTask" },
  { entry: "replace-with-script-task", qname: /<bpmn:scriptTask[\s>]/, label: "ScriptTask" },
  { entry: "replace-with-send-task", qname: /<bpmn:sendTask[\s>]/, label: "SendTask" },
  { entry: "replace-with-receive-task", qname: /<bpmn:receiveTask[\s>]/, label: "ReceiveTask" },
];

test.describe("CE-ACT — activities CREATE_EDIT", () => {
  test.use({ actor: "editor" });

  test("CE-ACT-01: Task → rename → connect → save/read-back/reload → bpmn:task; delete+undo", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-ACT-01");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const t1 = await selectedElementId(page);
    await createFromPalette(page, "create.task", 420, 200);
    const t2 = await selectedElementId(page);

    await renameElement(page, t1, "Atividade Um");
    await connectElements(page, t1, t2);

    const xml = await saveReadbackReload(page, "editor", modelId, [
      t1,
      t2,
    ]);
    expectXmlHas(xml, /<bpmn:task[\s>][^]*name="Atividade Um"/, "task renomeada");
    expectXmlHas(xml, /<bpmn:sequenceFlow[\s>][^]*sourceRef=/, "sequenceFlow");

    // delete + undo (command stack)
    await clickEl(page, t2);
    await page
      .locator('.djs-context-pad.open .entry[data-action="delete"]')
      .click();
    await expect(
      page.locator(`.djs-element[data-element-id="${t2}"]`),
    ).toHaveCount(0);
    await page.locator('button[aria-label="Desfazer"]').click();
    await expect(
      page.locator(`.djs-element[data-element-id="${t2}"]`),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("CE-ACT-02: Task → Replace → 7 typed tasks com QName correto", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-ACT-02");
    await openEditor(page, modelId);

    const created: string[] = [];
    for (let i = 0; i < TYPED_TASKS.length; i++) {
      await page.keyboard.press("Escape");
      // grid 4×2 dentro da área útil do canvas (panel aside à direita)
      await createFromPalette(
        page,
        "create.task",
        170 + (i % 4) * 120,
        140 + Math.floor(i / 4) * 170,
      );
      const id = await selectedElementId(page);
      created.push(id);
      await clickEl(page, id);
      await replaceWith(page, TYPED_TASKS[i].entry);
      await page.waitForTimeout(150);
    }

    const xml = await saveReadbackReload(page, "editor", modelId, created);
    for (const t of TYPED_TASKS) {
      expectXmlHas(xml, t.qname, t.label);
    }
  });

  test("CE-ACT-03: Task → Replace → CallActivity → bpmn:callActivity", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-ACT-03");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 300, 200);
    const id = await selectedElementId(page);
    await clickEl(page, id);
    await replaceWith(page, "replace-with-call-activity");

    const xml = await saveReadbackReload(page, "editor", modelId, [id]);
    expectXmlHas(xml, /<bpmn:callActivity[\s>]/, "callActivity");
    // PROP-GAP: calledElement não tem UI no provider bpmn carregado
    // (grupo vive nos providers Zeebe/Camunda não registrados) —
    // registrado no relatório G2B, não bloqueia o construct.
  });

  test("CE-ACT-04: SubProcess expanded (palette) + collapsed (replace)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-ACT-04");
    await openEditor(page, modelId);

    // expanded via palette
    await createFromPalette(page, "create.subprocess-expanded", 320, 260);
    const spExpanded = await selectedElementId(page);

    // collapsed via replace em task
    await createFromPalette(page, "create.task", 120, 480);
    const t = await selectedElementId(page);
    await clickEl(page, t);
    await replaceWith(page, "replace-with-collapsed-subprocess");

    // containment: task criada dentro do subprocess expandido
    await createFromPalette(page, "create.task", 300, 260);
    const child = await selectedElementId(page);

    const xml = await saveReadbackReload(page, "editor", modelId, [
      spExpanded,
      t,
      child,
    ]);
    // dois subProcesses no XML; expanded tem plane/filho, collapsed é shape simples
    const count = (xml.match(/<bpmn:subProcess[\s>]/g) ?? []).length;
    expect(count).toBeGreaterThanOrEqual(2);
    // collapsed: shape sem isExpanded="true" + sem filhos semânticos
    expectXmlHas(xml, /isExpanded="true"/, "expanded subprocess DI");
    expectXmlHas(
      xml,
      new RegExp(`<bpmn:subProcess id="${t}"\\s*/>`),
      "collapsed subprocess semântico",
    );
    expectXmlHas(
      xml,
      new RegExp(`<bpmn:subProcess[^>]*id="${spExpanded}"[^]*${child}`),
      "child dentro do subprocess expandido",
    );
  });
});
