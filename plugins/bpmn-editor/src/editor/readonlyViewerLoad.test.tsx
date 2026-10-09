// @vitest-environment jsdom
/**
 * G9-LOAD-1 §7/§11 — hardening do BpmnReadonlyViewer: toda inicialização
 * alcança estado terminal (ready/empty/error); constructor failure,
 * importXML rejection e import que nunca resolve → "error"; falha de
 * fit-viewport → "ready" degradado (conteúdo navegável, fit cosmético).
 */
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { BpmnReadonlyViewerStatus } from "./BpmnReadonlyViewer";

type ImportBehavior = "resolve" | "reject" | "hang";
const behavior: {
  ctorThrows: boolean;
  importResult: ImportBehavior;
  fitThrows: boolean;
} = { ctorThrows: false, importResult: "resolve", fitThrows: false };

vi.mock("bpmn-js/lib/NavigatedViewer", () => ({
  default: class MockNavigatedViewer {
    constructor() {
      if (behavior.ctorThrows) throw new Error("ctor boom");
    }
    importXML(): Promise<never> {
      if (behavior.importResult === "reject")
        return Promise.reject(new Error("import boom"));
      if (behavior.importResult === "hang") return new Promise(() => {});
      return Promise.resolve() as Promise<never>;
    }
    get(name: string): unknown {
      if (name === "elementRegistry") {
        return { filter: () => [{ type: "bpmn:Task", id: "T1" }] };
      }
      if (name === "canvas") {
        return {
          zoom: () => {
            if (behavior.fitThrows) throw new Error("fit boom");
          },
        };
      }
      if (name === "zoomScroll") return { stepZoom: () => undefined };
      throw new Error(`service não registrado: ${name}`);
    }
    destroy() {}
  },
}));

(globalThis as Record<string, unknown>).IS_REACT_ACT_ENVIRONMENT = true;

const XML =
  '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"/>';

async function renderViewer(opts?: { importTimeoutMs?: number }) {
  const { BpmnReadonlyViewer } = await import("./BpmnReadonlyViewer");
  const statuses: BpmnReadonlyViewerStatus[] = [];
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => {
    root.render(
      <BpmnReadonlyViewer
        xml={XML}
        fitOnLoad
        importTimeoutMs={opts?.importTimeoutMs}
        onStatusChange={(s) => statuses.push(s)}
      />,
    );
    // drena microtasks/promises do import
    await Promise.resolve();
    await Promise.resolve();
  });
  const el = container.querySelector(
    "[data-testid='bpmn-readonly-viewer']",
  ) as HTMLElement;
  return { container, root, statuses, status: () => el?.dataset.status };
}

describe("BpmnReadonlyViewer — estados terminais garantidos", () => {
  beforeEach(() => {
    behavior.ctorThrows = false;
    behavior.importResult = "resolve";
    behavior.fitThrows = false;
    vi.spyOn(console, "debug").mockImplementation(() => undefined);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("import OK → ready", async () => {
    const v = await renderViewer();
    expect(v.status()).toBe("ready");
    await act(async () => v.root.unmount());
    v.container.remove();
  }, 30_000);

  it("constructor do NavigatedViewer lança → error (parent não fica loading)", async () => {
    behavior.ctorThrows = true;
    const v = await renderViewer();
    expect(v.status()).toBe("error");
    await act(async () => v.root.unmount());
    v.container.remove();
  }, 30_000);

  it("importXML rejeita → error", async () => {
    behavior.importResult = "reject";
    const v = await renderViewer();
    expect(v.status()).toBe("error");
    await act(async () => v.root.unmount());
    v.container.remove();
  }, 30_000);

  it("importXML nunca resolve → timeout → error", async () => {
    behavior.importResult = "hang";
    const v = await renderViewer({ importTimeoutMs: 30 });
    // espera o timeout disparar
    await act(async () => {
      await new Promise((r) => setTimeout(r, 80));
    });
    expect(v.status()).toBe("error");
    await act(async () => v.root.unmount());
    v.container.remove();
  }, 30_000);

  it("fit-viewport lança → ready degradado (decisão explícita §11)", async () => {
    behavior.fitThrows = true;
    const v = await renderViewer();
    expect(v.status()).toBe("ready");
    await act(async () => v.root.unmount());
    v.container.remove();
  }, 30_000);
});
