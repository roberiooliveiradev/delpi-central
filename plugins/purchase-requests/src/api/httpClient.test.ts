import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, configureHttpClient, httpGet } from "./httpClient";

describe("httpClient", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    configureHttpClient(() => undefined);
  });

  it("sends Authorization and caller app headers", async () => {
    configureHttpClient(() => "token-abc");
    const fetchMock = vi.fn(async () =>
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await httpGet("/apps/purchase-requests-api/purchase-requests?branch=02");

    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer token-abc");
    expect(headers["X-Delpi-Caller-App"]).toBe("purchase-requests");
  });

  it("maps 403 to friendly message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ message: "Sem permissão" }), {
          status: 403,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(httpGet("/forbidden")).rejects.toEqual(
      expect.objectContaining<Partial<ApiClientError>>({
        status: 403,
        message: "Sem permissão",
      }),
    );
  });
});
