/**
 * G4 — RT-DI-*: multi-diagram + no-DI.
 * multi-diagram: 2 BPMNDiagram preservados (count, plane refs, shapes/edges).
 * no-di: import sem BPMNDI → semântica preservada; serialização do editor
 * ganha DI (expected transform, não no-op).
 */
import { test, expect, importModelViaApi } from "../helpers";
import { fetchWorkingCopyXml, openEditor } from "../ce-helpers";
import {
  expectEquivalent,
  readFixture,
  roundTripNoEdit,
  serializeViaValidate,
} from "../rt-helpers";
import { compareBpmnXml } from "../rt-compare";

const MULTI = readFixture("multi-diagram.bpmn");
const NODI = readFixture("no-di.bpmn");

test("RT-DI-01 multi-diagram: secondary BPMNDiagram não é descartado", async ({
  page,
}) => {
  await roundTripNoEdit(page, "editor", MULTI, {
    name: "RT-DI-01",
    renderIds: ["SA", "TA"],
  });

  // UI reconhece múltiplos diagramas (selector visível no modelB reaberto)
  await expect(page.locator(".bpmnm-diagram-selector")).toBeAttached();
});

test("RT-DI-02 no-DI: semântica preservada; serialização gera DI (transform esperado)", async ({
  page,
}) => {
  const modelA = await importModelViaApi("editor", "RT-DI-02", NODI);
  await openEditor(page, modelA);
  await expect(
    page.locator('.djs-element[data-element-id="NT1"]'),
  ).toBeAttached();

  const { xml: serialized } = await serializeViaValidate(page, modelA);

  // semântica preservada integralmente — diffs permitidos: apenas elementos
  // ADICIONADOS no domínio BPMN-DI (injeção transitória de layout no-DI).
  expectEquivalent(NODI, serialized, "RT-DI-02 semantics", [
    { kind: "EXTRA_ELEMENT", pathIncludes: "20100524/DI" },
  ]);

  // serialized ganhou DI → diffs são APENAS EXTRA_ELEMENT no domínio BPMN-DI
  const diffs = compareBpmnXml(NODI, serialized);
  expect(diffs.length).toBeGreaterThan(0);
  for (const d of diffs) {
    expect(d.kind, JSON.stringify(diffs)).toBe("EXTRA_ELEMENT");
    expect(
      d.path.includes("20100524/DI") ||
        d.path.includes("20100524/DC") ||
        d.detail.includes("20100524/DI"),
      JSON.stringify(d),
    ).toBeTruthy();
  }

  // reimport do serializado → reserialize → equivalente
  const modelB = await importModelViaApi("editor", "RT-DI-02-rt", serialized);
  const storedB = await fetchWorkingCopyXml("editor", modelB);
  expect(storedB).toBe(serialized);
  await openEditor(page, modelB);
  const { xml: serB } = await serializeViaValidate(page, modelB);
  expectEquivalent(serialized, serB, "RT-DI-02 serialized→reimport→serialize");
});
