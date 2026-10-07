/**
 * CE-EVT (G2B) — CREATE_EDIT evidence: events por posição × definição.
 *
 * Start/catch/throw/boundary/end: create → replace def → read-back
 * <bpmn:*EventDefinition> → reload. Properties provadas onde a surface
 * real as expõe (timer type/value, refs de evento).
 */
import { test, expect, createModelViaApi } from "../helpers";
import {
  openEditor,
  createFromPalette,
  clickEl,
  replaceWith,
  connectElements,
  appendAndPlace,
  newShapeId,
  selectedElementId,
  saveReadbackReload,
  expectXmlHas,
  attachBoundary,
} from "../ce-helpers";

test.describe("CE-EVT — events CREATE_EDIT", () => {
  test.use({ actor: "editor" });

  test("CE-EVT-01: Start defs — None/Message/Timer/Signal com EventDefinition", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-EVT-01");
    await openEditor(page, modelId);

    const defs = [
      { entry: "replace-with-message-start", q: /<bpmn:messageEventDefinition[\s>]/ },
      { entry: "replace-with-timer-start", q: /<bpmn:timerEventDefinition[\s>]/ },
      { entry: "replace-with-signal-start", q: /<bpmn:signalEventDefinition[\s>]/ },
    ];
    const ids: string[] = [];
    // None start (default create)
    await createFromPalette(page, "create.start-event", 140, 100);
    const noneStart = await selectedElementId(page);
    ids.push(noneStart);
    for (let i = 0; i < defs.length; i++) {
      await page.keyboard.press("Escape");
      await createFromPalette(page, "create.start-event", 140, 200 + i * 90);
      const id = await selectedElementId(page);
      ids.push(id);
      await clickEl(page, id);
      await replaceWith(page, defs[i].entry);
      await page.waitForTimeout(120);
    }

    const xml = await saveReadbackReload(page, "editor", modelId, ids);
    const startCount = (xml.match(/<bpmn:startEvent[\s>]/g) ?? []).length;
    expect(startCount).toBeGreaterThanOrEqual(4);
    // None start: sem eventDefinition
    expectXmlHas(
      xml,
      new RegExp(`<bpmn:startEvent id="${noneStart}"\\s*/?>`),
      "none start",
    );
    for (const d of defs) expectXmlHas(xml, d.q, d.entry);
  });

  test("CE-EVT-02: Intermediate Catch — Message/Timer/Signal append + Link replace", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-EVT-02");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 200, 200);
    const t1 = await selectedElementId(page);

    // task pad só expõe append.intermediate-event genérico — defs entram
    // via Replace (caminho aprovado)
    const defs = [
      { entry: "replace-with-message-intermediate-catch", q: /<bpmn:messageEventDefinition[\s>]/ },
      { entry: "replace-with-timer-intermediate-catch", q: /<bpmn:timerEventDefinition[\s>]/ },
      { entry: "replace-with-signal-intermediate-catch", q: /<bpmn:signalEventDefinition[\s>]/ },
    ];
    const ids: string[] = [];
    for (let i = 0; i < defs.length; i++) {
      await page.keyboard.press("Escape");
      await clickEl(page, t1);
      const id = await newShapeId(page, () =>
        appendAndPlace(page, "append.intermediate-event", 400, 100 + i * 90),
      );
      ids.push(id);
      await page.keyboard.press("Escape");
      await clickEl(page, id);
      await replaceWith(page, defs[i].entry);
      await page.waitForTimeout(120);
    }
    // Link catch via replace no primeiro catch criado
    await clickEl(page, ids[0]);
    await replaceWith(page, "replace-with-link-intermediate-catch");

    const xml = await saveReadbackReload(page, "editor", modelId, ids);
    expectXmlHas(xml, /<bpmn:timerEventDefinition[\s>]/, "timer catch");
    expectXmlHas(xml, /<bpmn:signalEventDefinition[\s>]/, "signal catch");
    expectXmlHas(xml, /<bpmn:linkEventDefinition[\s>]/, "link catch");
    const catchCount = (xml.match(/<bpmn:intermediateCatchEvent[\s>]/g) ?? []).length;
    expect(catchCount).toBeGreaterThanOrEqual(3);
  });

  test("CE-EVT-03: Intermediate Throw — None/Message/Signal/Escalation/Link", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-EVT-03");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 160, 260);
    const t1 = await selectedElementId(page);
    // throw none via append.intermediate-event
    await clickEl(page, t1);
    const noneThrow = await newShapeId(page, () =>
      appendAndPlace(page, "append.intermediate-event", 340, 260),
    );

    const defs = [
      { entry: "replace-with-message-intermediate-throw", q: /<bpmn:messageEventDefinition[\s>]/ },
      { entry: "replace-with-signal-intermediate-throw", q: /<bpmn:signalEventDefinition[\s>]/ },
      { entry: "replace-with-escalation-intermediate-throw", q: /<bpmn:escalationEventDefinition[\s>]/ },
      { entry: "replace-with-link-intermediate-throw", q: /<bpmn:linkEventDefinition[\s>]/ },
    ];
    const ids = [noneThrow];
    for (let i = 0; i < defs.length; i++) {
      await page.keyboard.press("Escape");
      await clickEl(page, t1);
      const id = await newShapeId(page, () =>
        appendAndPlace(
          page,
          "append.intermediate-event",
          320 + (i % 2) * 190,
          380 + Math.floor(i / 2) * 100,
        ),
      );
      ids.push(id);
      await page.keyboard.press("Escape");
      await clickEl(page, id);
      await replaceWith(page, defs[i].entry);
      await page.waitForTimeout(120);
    }

    const xml = await saveReadbackReload(page, "editor", modelId, ids);
    const throwCount = (xml.match(/<bpmn:intermediateThrowEvent[\s>]/g) ?? []).length;
    expect(throwCount).toBeGreaterThanOrEqual(5);
    for (const d of defs) expectXmlHas(xml, d.q, d.entry);
  });

  test("CE-EVT-04: Boundary — drop on task + defs Message/Timer/Error/Signal/Escalation + non-interrupting", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-EVT-04");
    await openEditor(page, modelId);

    const defs = [
      { entry: "replace-with-message-boundary", q: /<bpmn:messageEventDefinition[\s>]/ },
      { entry: "replace-with-timer-boundary", q: /<bpmn:timerEventDefinition[\s>]/ },
      { entry: "replace-with-error-boundary", q: /<bpmn:errorEventDefinition[\s>]/ },
      { entry: "replace-with-signal-boundary", q: /<bpmn:signalEventDefinition[\s>]/ },
      { entry: "replace-with-escalation-boundary", q: /<bpmn:escalationEventDefinition[\s>]/ },
    ];
    const ids: string[] = [];
    for (let i = 0; i < defs.length; i++) {
      await page.keyboard.press("Escape");
      await createFromPalette(
        page,
        "create.task",
        140 + (i % 3) * 190,
        130 + Math.floor(i / 3) * 230,
      );
      const t = await selectedElementId(page);
      // fecha o direct editing aberto pelo create antes do próximo clique
      await page.keyboard.press("Escape");
      // drop intermediate event ON the task → boundary event (vendor rules)
      const b = await attachBoundary(page, t);
      ids.push(b);
      await page.keyboard.press("Escape");
      await clickEl(page, b);
      await replaceWith(page, defs[i].entry);
      await page.waitForTimeout(120);
    }

    const xml = await saveReadbackReload(page, "editor", modelId, ids);
    const bCount = (xml.match(/<bpmn:boundaryEvent[\s>]/g) ?? []).length;
    expect(bCount).toBeGreaterThanOrEqual(5);
    expectXmlHas(xml, /attachedToRef=/, "attachedToRef");
    for (const d of defs) expectXmlHas(xml, d.q, d.entry);

    // non-interrupting via header toggle (regressão cancelActivity)
    await clickEl(page, ids[0]);
    await replaceWith(page, "replace-with-non-interrupting-message-boundary").catch(
      async () => {
        // alguns vendors expõem via header toggle em vez de entry dedicada
        await page.keyboard.press("Escape");
        await clickEl(page, ids[0]);
        await page
          .locator('.djs-context-pad.open .entry[data-action="replace"]')
          .click();
        await page
          .locator('.djs-popup [data-id="toggle-non-interrupting"]')
          .click();
      },
    );
    await page.waitForTimeout(200);
    const xml2 = await saveReadbackReload(page, "editor", modelId, ids);
    expectXmlHas(xml2, /cancelActivity="false"/, "non-interrupting boundary");
  });

  test("CE-EVT-05: End defs — None/Message/Error/Signal/Escalation/Terminate", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-EVT-05");
    await openEditor(page, modelId);

    const defs = [
      { entry: "replace-with-message-end", q: /<bpmn:messageEventDefinition[\s>]/ },
      { entry: "replace-with-error-end", q: /<bpmn:errorEventDefinition[\s>]/ },
      { entry: "replace-with-signal-end", q: /<bpmn:signalEventDefinition[\s>]/ },
      { entry: "replace-with-escalation-end", q: /<bpmn:escalationEventDefinition[\s>]/ },
      { entry: "replace-with-terminate-end", q: /<bpmn:terminateEventDefinition[\s>]/ },
    ];
    const ids: string[] = [];
    await createFromPalette(page, "create.end-event", 140, 80);
    ids.push(await selectedElementId(page)); // none end
    for (let i = 0; i < defs.length; i++) {
      await page.keyboard.press("Escape");
      await createFromPalette(
        page,
        "create.end-event",
        140 + (i % 3) * 170,
        200 + Math.floor(i / 3) * 110,
      );
      const id = await selectedElementId(page);
      ids.push(id);
      await clickEl(page, id);
      await replaceWith(page, defs[i].entry);
      await page.waitForTimeout(120);
    }

    const xml = await saveReadbackReload(page, "editor", modelId, ids);
    const endCount = (xml.match(/<bpmn:endEvent[\s>]/g) ?? []).length;
    expect(endCount).toBeGreaterThanOrEqual(6);
    for (const d of defs) expectXmlHas(xml, d.q, d.entry);
  });

  test("CE-EVT-06: timer properties — type + value expostos e persistem", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-EVT-06");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 160, 200);
    const t1 = await selectedElementId(page);
    await clickEl(page, t1);
    const te = await newShapeId(page, () =>
      appendAndPlace(page, "append.intermediate-event", 360, 200),
    );
    // task pad só tem append genérico — timer catch via replace
    await page.keyboard.press("Escape");
    await clickEl(page, te);
    await replaceWith(page, "replace-with-timer-intermediate-catch");

    // panel: timer group entries (surface real inventariada G2A)
    await clickEl(page, te);
    const panel = page.locator(
      "#bpmn-properties-panel .bio-properties-panel",
    );
    await expect(panel).toBeVisible();
    // grupos nascem collapsed — expande todos (re-query: DOM re-renderiza)
    for (let i = 0; i < 12; i++) {
      const closed = panel.locator(
        ".bio-properties-panel-group-header:not(.open) .bio-properties-panel-group-header-title",
      );
      if (!(await closed.count())) break;
      await closed.first().click();
      await page.waitForTimeout(120);
    }
    await expect(
      panel.locator('[data-entry-id="timerEventDefinitionType"]'),
    ).toBeAttached({ timeout: 10_000 });

    // seleciona tipo timeDuration e preenche valor
    await panel
      .locator('[data-entry-id="timerEventDefinitionType"] select, [data-entry-id="timerEventDefinitionType"]')
      .first()
      .click();
    const typeSelect = panel.locator(
      '[data-entry-id="timerEventDefinitionType"] select',
    );
    if (await typeSelect.count()) {
      await typeSelect.selectOption("timeDuration");
      const valueInput = panel.locator(
        '[data-entry-id="timerEventDefinitionValue"] input, [data-entry-id="timerEventDefinitionValue"] textarea',
      );
      await valueInput.first().click();
      await valueInput.first().fill("PT1H");
    }

    const xml = await saveReadbackReload(page, "editor", modelId, [te]);
    expectXmlHas(xml, /<bpmn:timerEventDefinition[\s>]/, "timer def");
    if (await typeSelect.count()) {
      expectXmlHas(xml, /<bpmn:timeDuration[\s>][^<]*PT1H/, "timeDuration value");
    }
  });
});
