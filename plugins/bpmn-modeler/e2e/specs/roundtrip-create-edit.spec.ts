/**
 * G4 — RT-CE-*: round-trip CREATE_EDIT (activities + gateways).
 * no-op: import → open → serialize (Validar=exportXml) → reimport → reserialize
 * safe-edit: import → rename não-relacionado → autosave → reimport → compare.
 */
import { test, expect, importModelViaApi, waitSaved } from "../helpers";
import { fetchWorkingCopyXml, openEditor } from "../ce-helpers";
import {
  expectEquivalent,
  readFixture,
  renameViaDirectEdit,
  roundTripNoEdit,
  serializeViaValidate,
  validateXmlApi,
  expectReportsEquivalent,
} from "../rt-helpers";

const CE_ACT = readFixture("ce-activities.bpmn");
const CE_GW = readFixture("ce-gateways.bpmn");

test("RT-CE-01 activities: todos os task types + callActivity(calledElement) + subprocesses", async ({
  page,
}) => {
  await roundTripNoEdit(page, "editor", CE_ACT, {
    name: "RT-CE-01",
    renderIds: ["T_PLAIN", "T_USER", "T_CALL", "SUB_EXP", "SUB_COL", "E1"],
    // EXPECTED_SERIALIZATION_DIFF: bpmn-js cria BPMNDiagram+BPMNPlane extra
    // (drill-down) para o subprocess colapsado SUB_COL — additive, sem perda.
    allowed: [{ kind: "EXTRA_ELEMENT", pathIncludes: "BPMNDiagram" }],
  });
});

test("RT-CE-02 gateways: exclusive+default/cond + parallel + inclusive + eventBased", async ({
  page,
}) => {
  await roundTripNoEdit(page, "editor", CE_GW, {
    name: "RT-CE-02",
    renderIds: ["GX", "GP", "GI", "GEB", "ICE_MSG", "E_GW"],
    // EXPECTED_SERIALIZATION_DIFF: vendor escreve isMarkerVisible="true" no
    // shape do exclusive gateway (marker X renderizado). Aditivo, DI enrich.
    allowed: [{ kind: "ATTR_DIFF", detailIncludes: "isMarkerVisible" }],
  });
});

test("RT-CE-03 safe-edit: rename unrelated task preserva todo o restante", async ({
  page,
}) => {
  const modelA = await importModelViaApi("editor", "RT-CE-03", CE_ACT);
  await openEditor(page, modelA);

  // safe edit — rename de task no meio do diagrama (longe de overlays)
  await renameViaDirectEdit(page, "T_MAN", "Manual Renomeada");
  await waitSaved(page);

  // persisted = serializado pelo editor + salvo (write path real)
  const savedA = await fetchWorkingCopyXml("editor", modelA);
  expect(savedA).toContain("Manual Renomeada");

  // diffs vs fixture: delta editado + drilldown plane do subprocess
  // colapsado (mesmo EXPECTED_SERIALIZATION_DIFF do RT-CE-01)
  expectEquivalent(CE_ACT, savedA, "RT-CE-03 fixture→saved", [
    { kind: "ATTR_DIFF", pathIncludes: "T_MAN", detailIncludes: "name" },
    { kind: "EXTRA_ELEMENT", pathIncludes: "BPMNDiagram" },
  ]);

  // reimport como novo model + re-serialize
  const modelB = await importModelViaApi("editor", "RT-CE-03-rt", savedA);
  const storedB = await fetchWorkingCopyXml("editor", modelB);
  expect(storedB).toBe(savedA); // opaque persistence TEXT_EQUAL

  await openEditor(page, modelB);
  await expect(
    page.locator('.djs-element[data-element-id="SUB_EXP"]'),
  ).toBeAttached();
  const { xml: serB, report: repB } = await serializeViaValidate(page, modelB);
  expectEquivalent(savedA, serB, "RT-CE-03 saved→reimport→serialize");

  const repA = await validateXmlApi("editor", modelA, savedA);
  expectReportsEquivalent(repA, repB, "RT-CE-03");
});
