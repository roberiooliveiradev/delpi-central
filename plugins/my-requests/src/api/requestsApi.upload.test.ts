import { describe, expect, it, vi } from "vitest";

import { API_BASE, uploadArtifact, uploadAttachment } from "./requestsApi";

describe("uploadAttachment", () => {
  it("envia multipart para POST /attachments com caller-app", async () => {
    let capturedUrl = "";
    let capturedInit: RequestInit | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        capturedUrl = url;
        capturedInit = init;
        return {
          ok: true,
          json: async () => ({
            success: true,
            data: { id: "att-1", original_name: "doc.pdf" },
          }),
        };
      }),
    );

    const file = new File(["conteudo"], "doc.pdf", { type: "application/pdf" });
    const result = await uploadAttachment("req-1", file, "idem-1");

    expect(result.id).toBe("att-1");
    expect(result.file_name).toBe("doc.pdf");
    expect(capturedUrl).toBe(`${API_BASE}/requests/req-1/attachments`);
    expect(capturedInit?.method).toBe("POST");
    const headers = capturedInit?.headers as Record<string, string>;
    expect(headers["X-Delpi-Caller-App"]).toBe("my-requests");
    expect(headers["Idempotency-Key"]).toBe("idem-1");
    expect(capturedInit?.body).toBeInstanceOf(FormData);
    expect((capturedInit?.body as FormData).get("file")).toBeInstanceOf(File);

    vi.unstubAllGlobals();
  });
});

describe("uploadArtifact", () => {
  it("envia multipart para POST /artifacts com artifact_kind", async () => {
    let capturedUrl = "";
    let capturedInit: RequestInit | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        capturedUrl = url;
        capturedInit = init;
        return {
          ok: true,
          json: async () => ({
            success: true,
            data: {
              id: "art-1",
              original_name: "nf.pdf",
              artifact_kind: "invoice_pdf",
            },
          }),
        };
      }),
    );

    const file = new File(["pdf"], "nf.pdf", { type: "application/pdf" });
    const result = await uploadArtifact("req-1", file, {
      artifactKind: "invoice_pdf",
      idempotencyKey: "idem-art",
    });

    expect(result.id).toBe("art-1");
    expect(result.file_name).toBe("nf.pdf");
    expect(result.kind).toBe("invoice_pdf");
    expect(capturedUrl).toBe(`${API_BASE}/requests/req-1/artifacts`);
    expect(capturedInit?.method).toBe("POST");
    const headers = capturedInit?.headers as Record<string, string>;
    expect(headers["X-Delpi-Caller-App"]).toBe("my-requests");
    expect(headers["Idempotency-Key"]).toBe("idem-art");
    const form = capturedInit?.body as FormData;
    expect(form.get("file")).toBeInstanceOf(File);
    expect(form.get("artifact_kind")).toBe("invoice_pdf");
    expect(capturedUrl).not.toContain("api-delpi");

    vi.unstubAllGlobals();
  });
});
