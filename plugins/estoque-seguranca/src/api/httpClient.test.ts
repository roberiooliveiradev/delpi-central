import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiClientError } from "../types/api";
import { configureHttpClient, httpGet } from "./httpClient";

function mockFetch(response: Partial<Response>) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok: response.ok ?? true,
    status: response.status ?? 200,
    json: response.json ?? (async () => ({})),
  } as Response);
}

describe("httpClient", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureHttpClient(() => undefined);
  });

  it("converte 401 em ApiClientError tipado", async () => {
    configureHttpClient(() => "token");
    mockFetch({ ok: false, status: 401, json: async () => ({ message: "Unauthorized" }) });

    await expect(httpGet("/test")).rejects.toMatchObject({
      name: "ApiClientError",
      status: 401,
      kind: "auth",
      retryable: false,
    });
  });

  it("converte 403 em ApiClientError tipado", async () => {
    configureHttpClient(() => "token");
    mockFetch({
      ok: false,
      status: 403,
      json: async () => ({ message: "Sem permissão para a filial." }),
    });

    await expect(httpGet("/test")).rejects.toSatisfy((error: unknown) => {
      expect(error).toBeInstanceOf(ApiClientError);
      const clientError = error as ApiClientError;
      expect(clientError.status).toBe(403);
      expect(clientError.kind).toBe("forbidden");
      expect(clientError.retryable).toBe(false);
      return true;
    });
  });

  it("converte 400 em ApiClientError tipado", async () => {
    configureHttpClient(() => "token");
    mockFetch({
      ok: false,
      status: 400,
      json: async () => ({ message: "branch inválida" }),
    });

    await expect(httpGet("/test")).rejects.toMatchObject({
      status: 400,
      kind: "validation",
      message: "branch inválida",
    });
  });

  it("converte 503 em ApiClientError tipado", async () => {
    configureHttpClient(() => "token");
    mockFetch({ ok: false, status: 503, json: async () => ({}) });

    await expect(httpGet("/test")).rejects.toMatchObject({
      status: 503,
      kind: "unavailable",
      retryable: true,
    });
  });

  it("envia Authorization e X-Delpi-Caller-App", async () => {
    configureHttpClient(() => "abc-token");
    const fetchSpy = mockFetch({ json: async () => ({ ok: true }) });

    await httpGet("/apps/api-delpi/supplies/safety-stock/filters");

    expect(fetchSpy).toHaveBeenCalledWith(
      "/apps/api-delpi/supplies/safety-stock/filters",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer abc-token",
          "X-Delpi-Caller-App": "estoque-seguranca",
        }),
      }),
    );
  });
});
