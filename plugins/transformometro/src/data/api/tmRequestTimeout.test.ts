/**
 * G9-LOAD-1 §5/§11 — timeout governado das leituras BPMN:
 * request pendurada → abort → erro classificado (REQUEST_TIMEOUT),
 * nunca promise pendente para sempre. Abort externo do consumidor
 * propaga sem classificar como timeout.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// @delpi/bpmn-editor não resolve no env node do TM (ESM do vendor sem
// extensão) — basta a shape do erro de transporte para classificar.
vi.mock("@delpi/bpmn-editor", () => ({
  BpmnDocumentError: class extends Error {
    status: number;
    code: string;
    constructor(status: number, body: { error?: { code?: string; message?: string } } | null, fallback: string) {
      super(body?.error?.message ?? fallback);
      this.status = status;
      this.code = body?.error?.code ?? "INFRASTRUCTURE_FAILURE";
    }
  },
}));

import { TmRequestTimeoutError, tmRequest } from "./transformometroApiBase";
import {
  fetchProcessBpmnDocument,
  fetchProcessBpmnWorkingCopy,
} from "./bpmnDocumentApi";

/** fetch real rejeita com AbortError quando o signal aborta — o stub
 *  reproduz exatamente isso para exercitar a classificação de timeout. */
const hangingFetch = (_url: unknown, init?: RequestInit) =>
  new Promise<Response>((_, reject) => {
    init?.signal?.addEventListener("abort", () =>
      reject(new DOMException("aborted", "AbortError")),
    );
  });

const envelope = (data: unknown) =>
  new Response(JSON.stringify({ success: true, data }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });

describe("tmRequest — timeout governado", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("fetch que nunca resolve → TmRequestTimeoutError após o budget", async () => {
    vi.stubGlobal("fetch", vi.fn(hangingFetch));
    const pending = tmRequest("/x", undefined, async (r) => r.json());
    const assertion = expect(pending).rejects.toBeInstanceOf(
      TmRequestTimeoutError,
    );
    await vi.advanceTimersByTimeAsync(21_000);
    await assertion;
  });

  it("abort externo propaga AbortError (não classifica como timeout)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init?: RequestInit) =>
          new Promise<Response>((_, reject) => {
            init?.signal?.addEventListener("abort", () =>
              reject(new DOMException("aborted", "AbortError")),
            );
          }),
      ),
    );
    const controller = new AbortController();
    const pending = tmRequest(
      "/x",
      { signal: controller.signal },
      async (r) => r.json(),
    );
    const assertion = expect(pending).rejects.toMatchObject({
      name: "AbortError",
    });
    controller.abort();
    await assertion;
  });
});

describe("bpmnDocumentApi — leituras terminam em erro recuperável", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("working-copy pendurada → BpmnDocumentError REQUEST_TIMEOUT (408)", async () => {
    vi.stubGlobal("fetch", vi.fn(hangingFetch));
    const pending = fetchProcessBpmnWorkingCopy("proc-1", () => "t");
    const assertion = expect(pending).rejects.toMatchObject({
      status: 408,
      code: "REQUEST_TIMEOUT",
    });
    await vi.advanceTimersByTimeAsync(21_000);
    await assertion;
  });

  it("document metadata pendurada → BpmnDocumentError REQUEST_TIMEOUT", async () => {
    vi.stubGlobal("fetch", vi.fn(hangingFetch));
    const pending = fetchProcessBpmnDocument("proc-1", () => "t");
    const assertion = expect(pending).rejects.toMatchObject({
      status: 408,
      code: "REQUEST_TIMEOUT",
    });
    await vi.advanceTimersByTimeAsync(21_000);
    await assertion;
  });

  it("resposta 200 normal → parseia envelope (não regrediu o happy path)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          envelope({
            document: { document_id: "d1", processo_id: "proc-1" },
            version: 3,
          }),
        ),
      ),
    );
    const doc = await fetchProcessBpmnDocument("proc-1", () => "t");
    expect(doc?.document.document_id).toBe("d1");
    expect(doc?.version).toBe(3);
  });
});
