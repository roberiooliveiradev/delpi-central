import { describe, expect, it, vi } from "vitest";

import {
  API_BASE,
  downloadProductDrawingBlob,
  productDrawingUrl,
} from "./requestsApi";

describe("productDrawingUrl", () => {
  it("aponta para a rota vinculada à solicitação (sem código livre)", () => {
    expect(productDrawingUrl("req-abc")).toBe(
      `${API_BASE}/requests/req-abc/product-drawing`,
    );
    expect(productDrawingUrl("req-abc")).not.toContain("code=");
    expect(productDrawingUrl("req-abc")).not.toContain("api-delpi");
  });
});

describe("downloadProductDrawingBlob", () => {
  it("busca o PDF autenticado pelo request id", async () => {
    let capturedUrl = "";
    let capturedInit: RequestInit | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        capturedUrl = url;
        capturedInit = init;
        return {
          ok: true,
          blob: async () => new Blob(["%PDF-1.4"], { type: "application/pdf" }),
        };
      }),
    );

    const blob = await downloadProductDrawingBlob("req-42");

    expect(blob.type).toBe("application/pdf");
    expect(capturedUrl).toBe(`${API_BASE}/requests/req-42/product-drawing`);
    expect(capturedInit?.method).toBe("GET");
    const headers = capturedInit?.headers as Record<string, string>;
    expect(headers["X-Delpi-Caller-App"]).toBe("my-requests");

    vi.unstubAllGlobals();
  });

  it("propaga a mensagem do envelope de erro (desenho ausente)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 404,
        json: async () => ({
          success: false,
          message: "Desenho não encontrado para este produto.",
          data: { code: "drawing_not_found" },
        }),
      })),
    );

    await expect(downloadProductDrawingBlob("req-1")).rejects.toThrow(
      "Desenho não encontrado para este produto.",
    );

    vi.unstubAllGlobals();
  });

  it("propaga indisponibilidade da biblioteca", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 503,
        json: async () => ({
          success: false,
          message: "Não foi possível consultar o desenho neste momento.",
          data: { code: "drawing_source_unavailable" },
        }),
      })),
    );

    await expect(downloadProductDrawingBlob("req-1")).rejects.toThrow(
      "Não foi possível consultar o desenho neste momento.",
    );

    vi.unstubAllGlobals();
  });

  it("faz fallback para HTTP status quando a resposta não é JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 502,
        json: async () => {
          throw new Error("not json");
        },
      })),
    );

    await expect(downloadProductDrawingBlob("req-1")).rejects.toThrow(
      "Erro HTTP 502",
    );

    vi.unstubAllGlobals();
  });
});
