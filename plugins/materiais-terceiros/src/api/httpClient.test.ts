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

  it("envia Authorization e X-Delpi-Caller-App", async () => {
    configureHttpClient(() => "abc-token");
    const fetchSpy = mockFetch({ json: async () => ({ ok: true }) });

    await httpGet("/apps/api-delpi/supplies/third-party-materials/summary");

    const init = fetchSpy.mock.calls[0]?.[1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get("Authorization")).toBe("Bearer abc-token");
    expect(headers.get("X-Delpi-Caller-App")).toBe("materiais-terceiros");
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
      return true;
    });
  });
});
