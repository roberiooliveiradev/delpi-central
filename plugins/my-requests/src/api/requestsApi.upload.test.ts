import { describe, expect, it, vi } from "vitest";

import { API_BASE, uploadAttachment } from "./requestsApi";

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
