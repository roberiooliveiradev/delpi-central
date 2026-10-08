/**
 * PROP-EVT (WAVE E) — event definition references (evidence closure):
 * messageRef, signalRef, errorRef, escalationRef, linkName.
 *
 * Os entries são vendor (`bpmn` provider, já expostos/governados pelo
 * profile) — a wave fecha a evidência: select ref → root element BPMN
 * criado em definitions.rootElements → save → read-back → reload.
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
  attachBoundary,
  newShapeId,
  replaceWith,
  saveReadbackReload,
  expectXmlHas,
} from "../ce-helpers";
import { expandAllGroups, entry, entryInput } from "../prop-helpers";
import type { Page } from "@playwright/test";

/** Seleciona ref via dropdown do entry e prova root + referência. */
async function refCreateNew(page: Page, entryId: string) {
  const select = entry(page, entryId).locator("select").first();
  await expect(select).toBeVisible({ timeout: 10_000 });
  await select.selectOption("create-new");
  await page.waitForTimeout(300);
}

test.describe("PROP-EVT — event definition refs", () => {
  test.use({ actor: "editor" });

  test("PROP-EVT-01: message start → messageRef create-new → root bpmn:message + ref", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROP-EVT-01");
    await openEditor(page, modelId);

    const ev = await newShapeId(page, () =>
      createFromPalette(page, "create.start-event", 300, 200),
    );
    await clickEl(page, ev);
    await replaceWith(page, "replace-with-message-start");
    await clickEl(page, ev);
    await expandAllGroups(page);

    await refCreateNew(page, "messageRef");
    await fillNameIfVisible(page, "messageName", "PedidoRecebido");

    const xml = await saveReadbackReload(page, "editor", modelId, [ev]);
    expectXmlHas(xml, /<bpmn:message id="([^"]+)"/, "root bpmn:message");
    const msgId = /<bpmn:message id="([^"]+)"/.exec(xml)![1];
    expectXmlHas(
      xml,
      new RegExp(`messageRef="${msgId}"`),
      "messageRef → root",
    );
  });

  test("PROP-EVT-02: signal start → signalRef create-new → root bpmn:signal + ref", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROP-EVT-02");
    await openEditor(page, modelId);

    const ev = await newShapeId(page, () =>
      createFromPalette(page, "create.start-event", 300, 200),
    );
    await clickEl(page, ev);
    await replaceWith(page, "replace-with-signal-start");
    await clickEl(page, ev);
    await expandAllGroups(page);

    await refCreateNew(page, "signalRef");
    await fillNameIfVisible(page, "signalName", "SinalGlobal");

    const xml = await saveReadbackReload(page, "editor", modelId, [ev]);
    expectXmlHas(xml, /<bpmn:signal id="([^"]+)"/, "root bpmn:signal");
    const sigId = /<bpmn:signal id="([^"]+)"/.exec(xml)![1];
    expectXmlHas(xml, new RegExp(`signalRef="${sigId}"`), "signalRef → root");
  });

  test("PROP-EVT-03: error boundary → errorRef create-new → root bpmn:error + ref + code", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROP-EVT-03");
    await openEditor(page, modelId);

    const task = await newShapeId(page, () =>
      createFromPalette(page, "create.task", 300, 200),
    );
    const be = await attachBoundary(page, task);
    await clickEl(page, be);
    await replaceWith(page, "replace-with-error-boundary");
    await clickEl(page, be);
    await expandAllGroups(page);

    await refCreateNew(page, "errorRef");
    await fillNameIfVisible(page, "errorName", "FalhaPagamento");
    await fillNameIfVisible(page, "errorCode", "PAY-001");

    const xml = await saveReadbackReload(page, "editor", modelId, [be]);
    expectXmlHas(xml, /<bpmn:error id="([^"]+)"/, "root bpmn:error");
    const errId = /<bpmn:error id="([^"]+)"/.exec(xml)![1];
    expectXmlHas(xml, new RegExp(`errorRef="${errId}"`), "errorRef → root");
    expectXmlHas(xml, /errorCode="PAY-001"/, "errorCode");
  });

  test("PROP-EVT-04: escalation throw → escalationRef create-new → root bpmn:escalation + ref", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROP-EVT-04");
    await openEditor(page, modelId);

    const ev = await newShapeId(page, () =>
      createFromPalette(page, "create.intermediate-event", 300, 200),
    );
    await clickEl(page, ev);
    await replaceWith(page, "replace-with-escalation-intermediate-throw");
    await clickEl(page, ev);
    await expandAllGroups(page);

    await refCreateNew(page, "escalationRef");
    await fillNameIfVisible(page, "escalationName", "EscNivel1");
    await fillNameIfVisible(page, "escalationCode", "ESC-1");

    const xml = await saveReadbackReload(page, "editor", modelId, [ev]);
    expectXmlHas(xml, /<bpmn:escalation id="([^"]+)"/, "root bpmn:escalation");
    const escId = /<bpmn:escalation id="([^"]+)"/.exec(xml)![1];
    expectXmlHas(
      xml,
      new RegExp(`escalationRef="${escId}"`),
      "escalationRef → root",
    );
    expectXmlHas(xml, /escalationCode="ESC-1"/, "escalationCode");
  });

  test("PROP-EVT-05: link catch → linkName → save → read-back", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "PROP-EVT-05");
    await openEditor(page, modelId);

    const ev = await newShapeId(page, () =>
      createFromPalette(page, "create.intermediate-event", 300, 200),
    );
    await clickEl(page, ev);
    await replaceWith(page, "replace-with-link-intermediate-catch");
    await clickEl(page, ev);
    await expandAllGroups(page);

    const nameInput = entryInput(page, "linkName");
    await expect(nameInput).toBeVisible({ timeout: 10_000 });
    await nameInput.click();
    await nameInput.fill("LinkA");
    await nameInput.press("Tab");
    await page.waitForTimeout(400);

    const xml = await saveReadbackReload(page, "editor", modelId, [ev]);
    expectXmlHas(
      xml,
      /<bpmn:linkEventDefinition[\s>][^>]*name="LinkA"|name="LinkA"[\s\S]{0,200}linkEventDefinition/,
      "linkName",
    );
  });
});

/** Entry de nome só aparece após o ref existir — preenche quando visível. */
async function fillNameIfVisible(page: Page, entryId: string, value: string) {
  const input = entryInput(page, entryId);
  await expect(input).toBeVisible({ timeout: 10_000 });
  await input.click();
  await input.fill(value);
  await input.press("Tab");
  await page.waitForTimeout(400);
}
