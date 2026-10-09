/**
 * G9-LOAD-1 §3/§11 — identidade estável do host: title e token são
 * getters vivos resolvidos no momento de cada chamada — nunca o valor
 * congelado no construtor.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

// @delpi/bpmn-editor não resolve no env node do TM (ESM do vendor) —
// só a shape do erro de transporte é usada pelo host/API.
vi.mock("@delpi/bpmn-editor", () => ({
  BpmnDocumentError: class extends Error {
    status: number;
    constructor(status: number, body: { message?: string } | null, fallback: string) {
      super(body?.message ?? fallback);
      this.status = status;
    }
  },
}));

import { TmProcessDocumentHost } from "./TmProcessDocumentHost";

const envelope = (data: unknown) =>
  new Response(JSON.stringify({ success: true, data }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });

describe("TmProcessDocumentHost — getters vivos", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("title getter resolve o valor mais recente (não o congelado)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.endsWith("/revisions")) return Promise.resolve(envelope({ items: [] }));
        return Promise.resolve(
          envelope({ document: { document_id: "d1" }, version: 1 }),
        );
      }),
    );
    let title = "Documento BPMN";
    const host = new TmProcessDocumentHost("proc-1", () => title, () => "tok");
    title = "PROC-0067 — Gerenciamento de Rotina";
    const meta = await host.loadDocument();
    expect(meta.title).toBe("PROC-0067 — Gerenciamento de Rotina");
  });

  it("token getter resolve o token mais recente em cada request", async () => {
    const seen: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string, init?: RequestInit) => {
        seen.push(
          String(
            (init?.headers as Record<string, string>)?.Authorization ?? "",
          ),
        );
        if (url.endsWith("/revisions")) return Promise.resolve(envelope({ items: [] }));
        return Promise.resolve(
          envelope({ document: { document_id: "d1" }, version: 1 }),
        );
      }),
    );
    let token: string | undefined = "tok-A";
    const host = new TmProcessDocumentHost("proc-1", "t", () => token);
    token = "tok-B";
    await host.loadDocument();
    expect(seen.every((h) => h === "Bearer tok-B")).toBe(true);
  });
});
