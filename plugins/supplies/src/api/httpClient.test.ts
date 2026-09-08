import { afterEach, describe, expect, it, vi } from "vitest";

import { getCapabilities } from "./capabilities";
import { configureHttpClient, httpGet, httpPatch, suppliesApiUrl } from "./httpClient";

describe("httpClient", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    configureHttpClient(() => undefined);
  });

  it("points only to supplies-api and sends caller + bearer headers", async () => {
    configureHttpClient(() => "token-abc");
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const url = suppliesApiUrl("/me/capabilities");
    expect(url).toBe("/apps/supplies-api/me/capabilities");

    await httpGet(url);

    const [calledUrl, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(calledUrl).toBe("/apps/supplies-api/me/capabilities");
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer token-abc");
    expect(headers["X-Delpi-Caller-App"]).toBe("supplies");
  });

  it("patches preferences on the same BFF base", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify({ theme: "dark" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await httpPatch(suppliesApiUrl("/me/preferences"), { theme: "dark" });

    const [calledUrl, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(calledUrl).toBe("/apps/supplies-api/me/preferences");
    expect(init.method).toBe("PATCH");
  });

  it("parses supplies-api envelope on 403", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify({ detail: "Forbidden", code: "forbidden" }), {
            status: 403,
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );

    await expect(httpGet(suppliesApiUrl("/me/capabilities"))).rejects.toThrow("[forbidden] Forbidden");
  });

  it("loads capabilities from GET /me/capabilities", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              userId: "user-1",
              capabilities: { portal: true, analytics: false },
              allowedUnits: ["01"],
              aliasesDoNotGrantAppAccess: true,
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
      ),
    );

    const result = await getCapabilities();
    expect(result.userId).toBe("user-1");
    expect(result.allowedUnits).toEqual(["01"]);
    expect(result.capabilities.portal).toBe(true);
  });
});
