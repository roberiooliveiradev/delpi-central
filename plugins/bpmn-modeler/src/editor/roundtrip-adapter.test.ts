// @vitest-environment jsdom
/**
 * G4 — adapter-level round-trip: BpmnEditorAdapter real (mount edit) →
 * importXml → exportXml → compareBpmnXml vs fixture.
 *
 * Evidência unit-level (sem stack) complementar aos specs E2E roundtrip-*.
 * Cada fixture declara seu inventário EXPECTED de diffs do serializer:
 *  - EXPECTED_VENDOR_TRANSFORM: BPMNDiagram extra = drilldown plane do
 *    subprocess colapsado; isMarkerVisible = enriquecimento DI do vendor.
 *  - KNOWN_DEFECT (ext-*): bpmn-moddle dropa `definition` de <bpmn:extension>
 *    e desqualifica attr namespaced vend:flag → flag. Defeito real de
 *    preservação registrado — NÃO normalizado no comparador.
 *  - no-di: adapter cru falha com EDITOR_CAPABILITY_FAILURE sem BPMN-DI;
 *    o path no-DI (elk layout → injectDiIntoXml) vive no ModelEditorPage,
 *    coberto pelo E2E RT-DI-02.
 */
import { describe, it, beforeAll, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { BpmnEditorAdapter } from "./BpmnEditorAdapter";
import { installCanvasDomStubs } from "./canvasTestSetup";
import {
  compareBpmnXml,
  checkIncomingOutgoingConsistency,
  formatDiffs,
  type Diff,
} from "../../e2e/rt-compare";

const DIR = join(__dirname, "../../e2e/fixtures/roundtrip");

type Allowed = Pick<Diff, "kind"> & {
  pathIncludes?: string;
  detailIncludes?: string;
};

function unexpected(diffs: Diff[], allowed: Allowed[]): Diff[] {
  return diffs.filter(
    (d) =>
      !allowed.some(
        (a) =>
          d.kind === a.kind &&
          (!a.pathIncludes || d.path.includes(a.pathIncludes)) &&
          (!a.detailIncludes || d.detail.includes(a.detailIncludes)),
      ),
  );
}

const CASES: Array<{ fixture: string; allowed: Allowed[] }> = [
  { fixture: "ce-activities.bpmn", allowed: [
    // drilldown plane do subprocess colapsado — additive vendor DI
    { kind: "EXTRA_ELEMENT", pathIncludes: "BPMNDiagram" },
  ] },
  { fixture: "ce-gateways.bpmn", allowed: [
    // enriquecimento DI do vendor no gateway exclusivo
    { kind: "ATTR_DIFF", pathIncludes: "SH_GX", detailIncludes: "isMarkerVisible" },
  ] },
  { fixture: "ce-events.bpmn", allowed: [] },
  { fixture: "ce-collaboration.bpmn", allowed: [] },
  { fixture: "ce-artifacts.bpmn", allowed: [] },
  { fixture: "pres-activities.bpmn", allowed: [] },
  { fixture: "pres-events.bpmn", allowed: [] },
  { fixture: "pres-data.bpmn", allowed: [] },
  { fixture: "ext-false.bpmn", allowed: [
    // KNOWN_DEFECT vendor preservation: definition drop + desqualificação de ns
    { kind: "ATTR_DIFF", pathIncludes: "MODEL}extension", detailIncludes: "definition" },
    { kind: "ATTR_DIFF", pathIncludes: "prop", detailIncludes: "flag" },
    { kind: "ATTR_DIFF", pathIncludes: "prop", detailIncludes: "flag" },
  ] },
  { fixture: "ext-true.bpmn", allowed: [
    // KNOWN_DEFECT vendor preservation: definition drop
    { kind: "ATTR_DIFF", pathIncludes: "MODEL}extension", detailIncludes: "definition" },
  ] },
  { fixture: "multi-diagram.bpmn", allowed: [] },
];

beforeAll(() => installCanvasDomStubs());

describe("G4 — adapter round-trip (importXml→exportXml)", () => {
  for (const { fixture, allowed } of CASES) {
    it(fixture, async () => {
      const xml = readFileSync(join(DIR, fixture), "utf-8");
      const host = document.createElement("div");
      const panel = document.createElement("div");
      panel.id = "bpmn-properties-panel";
      document.body.append(host, panel);
      const adapter = new BpmnEditorAdapter();
      adapter.mount(host, "edit");
      const res = await adapter.importXml(xml);
      expect(res.ok, `${fixture} import falhou: ${JSON.stringify(res)}`).toBe(true);
      const out = await adapter.exportXml();
      adapter.destroy();
      document.body.innerHTML = "";

      const diffs = [
        ...compareBpmnXml(xml, out),
        ...checkIncomingOutgoingConsistency(out),
      ];
      expect(
        unexpected(diffs, allowed),
        `${fixture} divergiu:\n${formatDiffs(unexpected(diffs, allowed))}`,
      ).toEqual([]);
      for (const a of allowed) {
        const hit = diffs.some(
          (d) =>
            d.kind === a.kind &&
            (!a.pathIncludes || d.path.includes(a.pathIncludes)) &&
            (!a.detailIncludes || d.detail.includes(a.detailIncludes)),
        );
        expect(hit, `${fixture}: diff esperado ausente: ${JSON.stringify(a)}`).toBe(true);
      }
    });
  }

  it("no-di.bpmn — adapter cru falha com capability failure (DI injetado no page)", async () => {
    const xml = readFileSync(join(DIR, "no-di.bpmn"), "utf-8");
    const host = document.createElement("div");
    const panel = document.createElement("div");
    panel.id = "bpmn-properties-panel";
    document.body.append(host, panel);
    const adapter = new BpmnEditorAdapter();
    adapter.mount(host, "edit");
    const res = await adapter.importXml(xml);
    adapter.destroy();
    document.body.innerHTML = "";
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.error.kind).toBe("EDITOR_CAPABILITY_FAILURE");
  });
});
