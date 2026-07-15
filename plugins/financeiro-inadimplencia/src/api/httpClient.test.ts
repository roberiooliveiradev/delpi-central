import { afterEach, describe, expect, it, vi } from "vitest";

import { configureHttpClient, httpGet } from "./httpClient";

afterEach(() => {
  vi.unstubAllGlobals();
  configureHttpClient(() => undefined);
});

function mockJsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("httpClient", () => {
  it("desembrulha resposta 200 JSON", async () => {
    configureHttpClient(() => "token-test");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: string, init?: RequestInit) => {
        const headers = new Headers(init?.headers);
        expect(headers.get("Authorization")).toBe("Bearer token-test");
        expect(headers.get("X-Delpi-Caller-App")).toBe("financeiro-inadimplencia");
        return mockJsonResponse(200, { success: true, data: { ok: 1 } });
      }),
    );

    await expect(httpGet<{ success: boolean }>("/apps/api-delpi/x")).resolves.toEqual({
      success: true,
      data: { ok: 1 },
    });
  });

  it("mapeia 401 para mensagem de sessão", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => mockJsonResponse(401, { message: "Unauthorized" })));
    await expect(httpGet("/x")).rejects.toThrow(/Sessão expirada/);
  });

  it("mapeia 403 para mensagem de permissão", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => mockJsonResponse(403, { message: "Forbidden" })));
    await expect(httpGet("/x")).rejects.toThrow(/permissão/);
  });

  it("mapeia 400 preservando mensagem do envelope", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        mockJsonResponse(400, {
          message: "O período máximo permitido é de 60 meses.",
          error: { code: "INVALID_PERIOD" },
        }),
      ),
    );
    await expect(httpGet("/x")).rejects.toThrow(/\[INVALID_PERIOD\].*60 meses/);
  });
});
