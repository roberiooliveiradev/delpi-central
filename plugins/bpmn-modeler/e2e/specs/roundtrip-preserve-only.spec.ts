/**
 * G4 — RT-PRES-*: round-trip RENDER_PRESERVE_ONLY.
 * Corpus: ComplexGateway, Transaction(+cancel boundary), AdHocSubProcess,
 * EventSubProcess, MultiInstance(seq+par), StandardLoop, isForCompensation,
 * boundary/catch/throw/end conditional/multiple/parallelMultiple/compensate/
 * cancel, DataInput/DataOutput(ioSpecification).
 * Critério: NÃO criar via UI — import → render → (safe edit elsewhere) →
 * save → read-back → reimport → compare.
 */
import { test, expect, importModelViaApi, waitSaved } from "../helpers";
import { fetchWorkingCopyXml, openEditor } from "../ce-helpers";
import {
  expectEquivalent,
  readFixture,
  renameViaDirectEdit,
  roundTripNoEdit,
  serializeViaValidate,
} from "../rt-helpers";

const PRES_ACT = readFixture("pres-activities.bpmn");
const PRES_EVT = readFixture("pres-events.bpmn");
const PRES_DATA = readFixture("pres-data.bpmn");

test("RT-PRES-01 preserve-only activities: complex gw, transaction, adhoc, eventsubprocess, MI, loop, compensation", async ({
  page,
}) => {
  await roundTripNoEdit(page, "editor", PRES_ACT, {
    name: "RT-PRES-01",
    renderIds: [
      "T_NORM",
      "TR1",
      "AH1",
      "CG1",
      "T_MIP",
      "T_MIS",
      "T_LOOP",
      "T_COMP",
      "BND_CANCEL",
      "ESP1",
    ],
  });
});

test("RT-PRES-02 safe-edit elsewhere: rename task não altera constructs preserve-only", async ({
  page,
}) => {
  const modelA = await importModelViaApi("editor", "RT-PRES-02", PRES_ACT);
  await openEditor(page, modelA);

  // edição segura em elemento totalmente diferente (meio do diagrama)
  await renameViaDirectEdit(page, "T_MIP", "MI Renomeada");
  await waitSaved(page);

  const savedA = await fetchWorkingCopyXml("editor", modelA);
  expect(savedA).toContain("MI Renomeada");
  expect(savedA).toContain("complexGateway");
  expect(savedA).toContain("adHocSubProcess");
  expect(savedA).toContain("multiInstanceLoopCharacteristics");

  // único delta = name de T_MIP + BPMNLabel adicionado ao shape editado
  // (EXPECTED_EDIT_DIFF — rename legítimo gera label bounds)
  expectEquivalent(PRES_ACT, savedA, "RT-PRES-02 fixture→saved", [
    { kind: "ATTR_DIFF", pathIncludes: "T_MIP", detailIncludes: "name" },
    { kind: "EXTRA_ELEMENT", pathIncludes: "SH_T_MIP" },
  ]);

  // reimport + reserialize
  const modelB = await importModelViaApi("editor", "RT-PRES-02-rt", savedA);
  await openEditor(page, modelB);
  await expect(
    page.locator('.djs-element[data-element-id="CG1"]'),
  ).toBeAttached();
  const { xml: serB } = await serializeViaValidate(page, modelB);
  expectEquivalent(savedA, serB, "RT-PRES-02 saved→reimport→serialize");
});

test("RT-PRES-03 preserve-only events: conditional/multiple/parallelMultiple/compensate em todas as posições", async ({
  page,
}) => {
  await roundTripNoEdit(page, "editor", PRES_EVT, {
    name: "RT-PRES-03",
    renderIds: ["S_COND", "S_MULT", "S_PMULT", "BD_COND", "TH_COMP", "E_COMP", "E_MULT"],
  });
});

test("RT-PRES-04 preserve-only data: DataInput/DataOutput via ioSpecification", async ({
  page,
}) => {
  await roundTripNoEdit(page, "editor", PRES_DATA, {
    name: "RT-PRES-04",
    renderIds: ["T_IO", "DIN1", "DOUT1", "DOR_IN", "DOR_OUT"],
  });
});
