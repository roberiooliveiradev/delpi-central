import { describe, expect, it, vi } from "vitest";

import { API_BASE, uploadAttachment } from "./requestsApi";

describe("uploadAttachment", () => {
  it("envia multipart para POST /attachments com caller-app", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        success: true,
        data: { id: "att-1", original_name: "doc.pdf" },
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const file = new File(["conteudo"], "doc.pdf", { type: "application/pdf" });
    const result = await uploadAttachment("req-1", file, "idem-1");

    expect(result.id).toBe("att-1");
    expect(result.file_name).toBe("doc.pdf");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const call = fetchMock.mock.calls[0];
    expect(call).toBeTruthy();
    const url = call![0] as string;
    const init = call![1] as RequestInit;
    expect(url).toBe(`${API_BASE}/requests/req-1/attachments`);
    expect(init.method).toBe("POST");
    expect((init.headers as Record<string, string>)["X-Delpi-Caller-App"]).toBe(
      "my-requests",
    );
    expect((init.headers as Record<string, string>)["Idempotency-Key"]).toBe("idem-1");
    expect(init.body).toBeInstanceOf(FormData);
    const form = init.body as FormData;
    expect(form.get("file")).toBeInstanceOf(File);

    vi.unstubAllGlobals();
  });
});
