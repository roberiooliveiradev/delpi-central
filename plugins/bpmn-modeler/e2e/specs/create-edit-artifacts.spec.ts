/**
 * CE-ART (G2B) — CREATE_EDIT evidence: data/artifacts + conectores.
 *
 * DataObject(Reference), DataStoreReference, TextAnnotation, Group,
 * Association, DataAssociation — create via palette/pad → connect →
 * read-back QName → reload.
 */
import { test, expect, createModelViaApi } from "../helpers";
import {
  openEditor,
  createFromPalette,
  clickEl,
  appendAndPlace,
  connectElements,
  newShapeId,
  newConnectionId,
  renameElement,
  selectedElementId,
  saveReadbackReload,
  expectXmlHas,
} from "../ce-helpers";

test.describe("CE-ART — artifacts/data CREATE_EDIT", () => {
  test.use({ actor: "editor" });

  test("CE-ART-01: DataObject + DataStore via palette", async ({ page }) => {
    const modelId = await createModelViaApi("editor", "CE-ART-01");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.data-object", 200, 300);
    const dataObj = await selectedElementId(page);
    await createFromPalette(page, "create.data-store", 200, 420);
    const dataStore = await selectedElementId(page);

    const xml = await saveReadbackReload(page, "editor", modelId, [
      dataObj,
      dataStore,
    ]);
    expectXmlHas(xml, /<bpmn:dataObjectReference[\s>]/, "dataObjectReference");
    expectXmlHas(xml, /<bpmn:dataStoreReference[\s>]/, "dataStoreReference");
  });

  test("CE-ART-02: DataAssociation — connect task ↔ dataObject", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-ART-02");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 320, 200);
    const t = await selectedElementId(page);
    // dois dataObjects — caminhos distintos evitam overlap dos connects
    await createFromPalette(page, "create.data-object", 200, 400);
    const dOut = await selectedElementId(page);
    await createFromPalette(page, "create.data-object", 440, 400);
    const dIn = await selectedElementId(page);

    // task → dataObject = dataOutputAssociation (vendor rules);
    // dataObject → task = dataInputAssociation — ambas num ciclo de save
    const out = await newConnectionId(page, () =>
      connectElements(page, t, dOut),
    );
    const inp = await newConnectionId(page, () =>
      connectElements(page, dIn, t),
    );

    const xml = await saveReadbackReload(page, "editor", modelId, [
      t,
      dOut,
      dIn,
      out,
      inp,
    ]);
    expectXmlHas(xml, /<bpmn:dataOutputAssociation[\s>]/, "dataOutput");
    expectXmlHas(xml, /<bpmn:dataInputAssociation[\s>]/, "dataInput");
  });

  test("CE-ART-03: TextAnnotation + texto editado + Association", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-ART-03");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 320, 200);
    const t = await selectedElementId(page);
    await clickEl(page, t);
    const ann = await newShapeId(page, () =>
      appendAndPlace(page, "append.text-annotation", 320, 360),
    );

    await renameElement(page, ann, "Nota operacional");

    // association: connect task → textAnnotation (única conexão válida;
    // fallback annotation → task se o vendor exigir a direção inversa)
    const assoc = await newConnectionId(page, () =>
      connectElements(page, t, ann),
    ).catch(() => newConnectionId(page, () => connectElements(page, ann, t)));

    const xml = await saveReadbackReload(page, "editor", modelId, [
      t,
      ann,
      assoc,
    ]);
    expectXmlHas(xml, /<bpmn:textAnnotation[\s>]/, "textAnnotation");
    expectXmlHas(xml, /Nota operacional/, "annotation text");
    expectXmlHas(xml, /<bpmn:association[\s>]/, "association");
  });

  test("CE-ART-04: Group via palette (artifact visual, não container)", async ({
    page,
  }) => {
    const modelId = await createModelViaApi("editor", "CE-ART-04");
    await openEditor(page, modelId);

    await createFromPalette(page, "create.task", 320, 200);
    const t = await selectedElementId(page);
    await page.keyboard.press("Escape");
    await createFromPalette(page, "create.group", 300, 180);
    const g = await selectedElementId(page);

    const xml = await saveReadbackReload(page, "editor", modelId, [t, g]);
    expectXmlHas(xml, /<bpmn:group[\s>]/, "group");
    // group é artifact visual — task não vira filho semântico
    expect(xml).not.toMatch(
      new RegExp(`<bpmn:group[^>]*>[^]*<bpmn:task`),
    );
  });
});
