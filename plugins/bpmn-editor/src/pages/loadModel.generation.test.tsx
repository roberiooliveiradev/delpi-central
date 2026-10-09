// @vitest-environment jsdom
/**
 * G9-LOAD-1 §4/§11 — proteção de geração do loadModel:
 *  - load antigo completando depois do novo → resultado ignorado;
 *  - cada remount de host (recreation) gera geração nova; a anterior
 *    não pode sobrescrever model/state do load corrente.
 */
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { BpmnDocumentHost } from "../host/BpmnDocumentHost";
import { installCanvasDomStubs } from "../editor/canvasTestSetup";

(globalThis as Record<string, unknown>).IS_REACT_ACT_ENVIRONMENT = true;

const XML =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" ' +
  'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" ' +
  'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" ' +
  'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" ' +
  'id="Definitions_1" targetNamespace="urn:test">' +
  '<bpmn:process id="Process_1" isExecutable="false">' +
  '<bpmn:startEvent id="Start_1"/>' +
  "</bpmn:process>" +
  '<bpmndi:BPMNDiagram id="D1"><bpmndi:BPMNPlane id="P1" bpmnElement="Process_1">' +
  '<bpmndi:BPMNShape id="S1" bpmnElement="Start_1"><dc:Bounds x="10" y="10" width="36" height="36"/></bpmndi:BPMNShape>' +
  "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>" +
  "</bpmn:definitions>";

function makeHost(
  title: string,
  version: number,
  wc: Promise<{ xml: string; version: number; sha256: string }>,
): BpmnDocumentHost {
  return {
    loadDocument: () =>
      Promise.resolve({ id: "d1", title, version, archived_at: null }),
    loadWorkingCopy: () => wc,
    saveWorkingCopy: () =>
      Promise.resolve({
        document_id: "d1",
        version,
        changed: true,
        artifact_sha256: "x",
      }),
    validate: () =>
      Promise.resolve({
        evaluated_stages: [],
        not_evaluated_stages: [],
        issues: [],
      }),
    listRevisions: () => Promise.resolve([]),
    createRevision: () =>
      Promise.resolve({ revision_number: 1, version }),
    loadRevision: () =>
      Promise.resolve({
        revision_number: 1,
        artifact_sha256: "x",
        origin: "explicit",
        source_revision_number: null,
        created_at: "",
        created_by: "",
        created_by_name: null,
        name: null,
        description: null,
      }),
    loadRevisionXml: () => Promise.resolve(XML),
    exportWorkingCopy: () => Promise.resolve(XML),
  };
}

async function flush(times = 30) {
  for (let i = 0; i < times; i++) {
    await act(async () => {
      await Promise.resolve();
      await new Promise((r) => setTimeout(r, 0));
    });
  }
}

let DEBUG_CONTAINER: HTMLElement | null = null;
const DEBUG_LOG: string[] = [];
async function waitFor(cond: () => boolean, timeoutMs = 15_000) {
  const start = Date.now();
  for (;;) {
    if (cond()) return;
    if (Date.now() - start > timeoutMs)
      throw new Error(
        "waitFor timeout — condição nunca atingida.\nDOM: " +
          (DEBUG_CONTAINER?.innerHTML ?? "(null)").slice(0, 2000) +
          "\nLOG: " +
          DEBUG_LOG.slice(-12).join("\n"),
      );
    await flush(1);
  }
}

describe("BpmnDocumentEditorPage — geração de load (stale não vence)", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    installCanvasDomStubs();
    window.matchMedia =
      window.matchMedia ??
      ((q: string) => ({
        matches: false,
        media: q,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
        addListener: () => undefined,
        removeListener: () => undefined,
        onchange: null,
        dispatchEvent: () => false,
      }) as MediaQueryList);
    for (const m of ["debug", "error", "warn"] as const) {
      vi.spyOn(console, m).mockImplementation((...args: unknown[]) => {
        DEBUG_LOG.push(`[${m}] ` + args.map(String).join(" "));
      });
    }
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    DEBUG_CONTAINER = container;
  });
  afterEach(async () => {
    await act(async () => root.unmount());
    container.remove();
    vi.restoreAllMocks();
  });

  it("load antigo completando após o novo é ignorado (host recreate)", { timeout: 30_000 }, async () => {
    const { BpmnDocumentEditorPage } = await import(
      "./BpmnDocumentEditorPage"
    );

    let resolveWc1!: (v: { xml: string; version: number; sha256: string }) => void;
    const wc1 = new Promise<{ xml: string; version: number; sha256: string }>(
      (r) => {
        resolveWc1 = r;
      },
    );
    const hostA = makeHost("OLD-DOC", 1, wc1);
    const hostB = makeHost(
      "NEW-DOC",
      2,
      Promise.resolve({ xml: XML, version: 2, sha256: "b" }),
    );

    const render = (host: BpmnDocumentHost) =>
      act(async () => {
        root.render(
          <BpmnDocumentEditorPage
            host={host}
            capabilities={{ view: true, edit: false, manage: false }}
            backLabel="Voltar"
            backPath="/x"
            revisionPathFor={(n) => `/rev/${n}`}
            navigate={() => undefined}
          />,
        );
      });

    await render(hostA);
    await waitFor(() => container.querySelector(".bpmnm-editor__title") != null);

    // host recreate (ex.: chegada do título / nova identidade) → gen2
    await render(hostB);
    await waitFor(() =>
      Boolean(
        container
          .querySelector(".bpmnm-editor__title")
          ?.textContent?.includes("NEW-DOC"),
      ),
    );

    // o load #1 (stale) resolve tarde — não pode sobrescrever o #2
    await act(async () => {
      resolveWc1({ xml: XML, version: 1, sha256: "a" });
    });
    await flush(5);

    const title = container.querySelector(".bpmnm-editor__title");
    expect(title?.textContent).toContain("NEW-DOC");
    expect(title?.textContent).not.toContain("OLD-DOC");
    expect(container.querySelector(".bpmnm-error")).toBeNull();
  });
});
