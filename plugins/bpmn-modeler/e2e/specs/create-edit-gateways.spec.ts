/**
 * CE-GW (G2B) — CREATE_EDIT evidence: gateways.
 *
 * Exclusive via palette (baseline já PROVEN), Parallel/Inclusive/
 * EventBased via replace (caminho aprovado). Cada um: create → connect
 * in/out → save → read-back QName → reload → render.
 */
import { test, expect, createModelViaApi } from "../helpers";
import {
  openEditor,
  createFromPalette,
  clickEl,
  replaceWith,
  connectElements,
  appendAndPlace,
  selectedElementId,
  saveReadbackReload,
  expectXmlHas,
} from "../ce-helpers";

test.describe("CE-GW — gateways CREATE_EDIT", () => {
  test.use({ actor: "editor" });

  test("CE-GW-01: Exclusive palette + connect in/out + bpmn:exclusiveGateway", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-GW-01");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 160, 200);
    const t1 = await selectedElementId(page);
    await createFromPalette(page, "create.exclusive-gateway", 340, 190);
    const gw = await selectedElementId(page);
    await createFromPalette(page, "create.end-event", 540, 190);
    const end = await selectedElementId(page);

    await connectElements(page, t1, gw);
    await connectElements(page, gw, end);

    const xml = await saveReadbackReload(page, "editor", modelId, [
      t1,
      gw,
      end,
    ]);
    expectXmlHas(xml, /<bpmn:exclusiveGateway[\s>]/, "exclusiveGateway");
    const flows = (xml.match(/<bpmn:sequenceFlow[\s>]/g) ?? []).length;
    expect(flows).toBeGreaterThanOrEqual(2);
  });

  for (const gw of [
    { entry: "replace-with-parallel-gateway", qname: /<bpmn:parallelGateway[\s>]/, label: "Parallel", n: "02" },
    { entry: "replace-with-inclusive-gateway", qname: /<bpmn:inclusiveGateway[\s>]/, label: "Inclusive", n: "03" },
  ]) {
    test(`CE-GW-${gw.n}: ${gw.label} via replace + connect + QName`, async ({
      page,
    }) => {
      const modelId = await createModelViaApi("editor", `CE-GW-${gw.n}`);
      await openEditor(page, modelId);

      await createFromPalette(page, "create.task", 160, 200);
      const t1 = await selectedElementId(page);
      await createFromPalette(page, "create.exclusive-gateway", 340, 190);
      const g = await selectedElementId(page);
      await clickEl(page, g);
      await replaceWith(page, gw.entry);
      await createFromPalette(page, "create.end-event", 540, 190);
      const end = await selectedElementId(page);
      await connectElements(page, t1, g);
      await connectElements(page, g, end);

      const xml = await saveReadbackReload(page, "editor", modelId, [
        t1,
        g,
        end,
      ]);
      expectXmlHas(xml, gw.qname, gw.label);
      expectXmlHas(
        xml,
        new RegExp(`<bpmn:sequenceFlow[^>]*sourceRef="${g}"`),
        `${gw.label} outgoing`,
      );
      expectXmlHas(
        xml,
        new RegExp(`<bpmn:sequenceFlow[^>]*targetRef="${g}"`),
        `${gw.label} incoming`,
      );
    });
  }

  // EventBasedGateway: outgoing válido é catch event (regra BPMN) — usar
  // append dedicado em vez de connect→endEvent (que o vendor corretamente
  // recusa).
  test("CE-GW-04: EventBased via replace + append catch + QName", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-GW-04");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 160, 200);
    const t1 = await selectedElementId(page);
    await createFromPalette(page, "create.exclusive-gateway", 340, 190);
    const g = await selectedElementId(page);
    await clickEl(page, g);
    await replaceWith(page, "replace-with-event-based-gateway");

    await connectElements(page, t1, g);
    await clickEl(page, g);
    await appendAndPlace(page, "append.timer-intermediate-event", 520, 190);
    const catchEv = await selectedElementId(page);

    const xml = await saveReadbackReload(page, "editor", modelId, [
      t1,
      g,
      catchEv,
    ]);
    expectXmlHas(xml, /<bpmn:eventBasedGateway[\s>]/, "eventBasedGateway");
    expectXmlHas(
      xml,
      new RegExp(`<bpmn:sequenceFlow[^>]*sourceRef="${g}"`),
      "EventBased outgoing",
    );
    expectXmlHas(
      xml,
      new RegExp(`<bpmn:sequenceFlow[^>]*targetRef="${g}"`),
      "EventBased incoming",
    );
  });

  test("CE-GW-05: EventBased — appends allowed; conditional append deny (regressão G2A)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-GW-05");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.exclusive-gateway", 300, 190);
    const g = await selectedElementId(page);
    await clickEl(page, g);
    await replaceWith(page, "replace-with-event-based-gateway");

    // outgoing válidos via context pad (timer/message catch)
    await clickEl(page, g);
    const pad = page.locator(".djs-context-pad.open");
    await expect(pad).toBeVisible();
    const entries = await page.evaluate(() =>
      [...document.querySelectorAll(".djs-context-pad.open .entry")].map((e) =>
        e.getAttribute("data-action"),
      ),
    );
    expect(entries).toContain("append.timer-intermediate-event");
    expect(entries).toContain("append.message-intermediate-event");
    expect(entries).not.toContain("append.condition-intermediate-event");

    const xml = await saveReadbackReload(page, "editor", modelId, [g]);
    expectXmlHas(xml, /<bpmn:eventBasedGateway[\s>]/, "eventBasedGateway");
  });
});
